#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ObsPi DSO server
#

import os, sys
import time
from datetime import date, datetime
import bottle
from bottle import route, run, template, BaseTemplate, get, post, request, static_file # https://bottlepy.org/docs/dev/
import json, socket
import pytz
import ephem
from math import degrees as deg
import math, decimal
dec = decimal.Decimal
from skyfield.api import load
from skyfield.framelib import ecliptic_frame
import spaceweather as sw #https://pypi.org/project/spaceweather/
import config

debug = False # True

def get_IP_adress():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(("8.8.8.8", 80))
  ip = s.getsockname()[0]
  if debug:
    print("IP: " + ip)
  s.close()
  return ip

########################CONFIG############################
PORT = 44444
HOST = get_IP_adress()
path = '/home/pi'
staticImageRoot = path + '/sky/dso/'
######################END#CONFIG##########################

theDate = time.strftime("%d.%m.%Y")
dso_data_file = staticImageRoot + "dsos_" + str(theDate) + ".json"

eph = load('de421.bsp') # will be downloaded at first load

# Target links: https://simbad.cds.unistra.fr/simbad/sim-basic?Ident=M1

###sun/moon/night###
def sun_data(theDate):
  for_date = theDate.split(".")
  for_date = date(int(for_date[2]), int(for_date[1]), int(for_date[0]))

  home = ephem.Observer()
  home.lat, home.lon = str(config.coordinates['latitude']), str(config.coordinates['longitude'])
  home.date = for_date #datetime.now()

  tz_germany = pytz.timezone(config.coordinates['timezone'])
  sun = ephem.Sun()
  sun.compute(home)
  sun_rise = ephem.localtime(home.next_rising(sun)).astimezone(tz_germany).strftime("%d.%m.%Y %H:%M")
  sun_set  = ephem.localtime(home.next_setting(sun)).astimezone(tz_germany).strftime("%d.%m.%Y %H:%M")
  if debug:
    print("Sunrise: " + str(sun_rise))
    print("Sunset: " + str(sun_set))

  return sun_rise, sun_set

def moon_data(theDate):
  for_date = theDate.split(".")
  for_date = date(int(for_date[2]), int(for_date[1]), int(for_date[0]))

  home = ephem.Observer()
  home.lat, home.lon = str(config.coordinates['latitude']), str(config.coordinates['longitude'])
  home.date = for_date #datetime.now()

  moon = ephem.Moon()
  moon.compute(home)

  tz_germany = pytz.timezone(config.coordinates['timezone'])
  moon_rise = ephem.localtime(home.next_rising(moon)).astimezone(tz_germany).strftime("%d.%m.%Y %H:%M")
  moon_set  = ephem.localtime(home.next_setting(moon)).astimezone(tz_germany).strftime("%d.%m.%Y %H:%M")
  full_moon = ephem.localtime(ephem.next_full_moon(home.date)).strftime("%d.%m.%Y")

  ts = load.timescale()
  t = ts.utc(int(theDate.split(".")[2]), int(theDate.split(".")[1]), int(theDate.split(".")[0]), 21, 0)

  sun, moon, earth = eph['sun'], eph['moon'], eph['earth']
  e = earth.at(t)
  s = e.observe(sun).apparent()
  m = e.observe(moon).apparent()

  _, slon, _ = s.frame_latlon(ecliptic_frame)
  _, mlon, _ = m.frame_latlon(ecliptic_frame)
  moon_phase = (mlon.degrees - slon.degrees) % 360.0
  moon_phase_percent = 100.0 * m.fraction_illuminated(sun)

  if debug:
    print("Moonrise: " + moon_rise)
    print("Moonset: " + moon_set)
    print("Next full moon: " + str(full_moon))
    print('Phase (0°–360°): {0:.1f}'.format(moon_phase))
    print('Percent illuminated: {0:.1f}%'.format(moon_phase_percent))

  return moon_rise, moon_set, full_moon, moon_phase, moon_phase_percent

def position(now=None): 
  if now is None: 
    now = datetime.now()
  diff = now - datetime(2001, 1, 1)
  days = dec(diff.days) + (dec(diff.seconds) / dec(86400))
  lunations = dec("0.20439731") + (days * dec("0.03386319269"))
  return lunations % dec(1)

def phase(pos): 
  index = (pos * dec(8)) + dec("0.5")
  index = math.floor(index)
  return {
    0: "New Moon",
    1: "Waxing Crescent", # zunehmender Mond
    2: "First Quarter",
    3: "Waxing Gibbous",  # zunehmender gewoelbter Mond
    4: "Full Moon",
    5: "Waning Gibbous",  # abnehmender gewoelbter Mond
    6: "Last Quarter",
    7: "Waning Crescent"  # abnehmender Mond
  }[int(index) & 7]

def astro_night_times(theDate):
  civil_night_start = None
  civil_night_end = None
  nautical_night_start = None
  nautical_night_end = None
  astronomical_night_start = None
  astronomical_night_end = None

  earth = ephem.Observer()
  earth.lat = str(config.coordinates['latitude'])
  earth.lon = str(config.coordinates['longitude'])
  earth.date = datetime.strptime(theDate, "%d.%m.%Y")
  sun = ephem.Sun()
  sun.compute()

  try:
    earth.horizon = "0"
    sunset = ephem.localtime(earth.next_setting(sun))
    sunrise = ephem.localtime(earth.next_rising(sun))

    earth.horizon = "-6"
    civil_night_start = ephem.localtime(earth.next_setting(sun))
    civil_night_end = ephem.localtime(earth.next_rising(sun))

    earth.horizon = "-12"
    nautical_night_start = ephem.localtime(earth.next_setting(sun))
    nautical_night_end = ephem.localtime(earth.next_rising(sun))

    earth.horizon = "-18"
    astronomical_night_start = ephem.localtime(earth.next_setting(sun))
    astronomical_night_end = ephem.localtime(earth.next_rising(sun))

  # ephem throws an "AlwaysUpError" when there is no astronomical twilight (which occurs in summer in nordic countries)
  except ephem.AlwaysUpError:
    if debug:
      print("No astronomical night at the moment: " + str(theDate))

  if debug:
    print("Civil night start: " + str(civil_night_start))
    print("Civil night end: " + str(civil_night_end))
    print("Nautical night start: " + str(nautical_night_start))
    print("Nautical night end: " + str(nautical_night_end))
    print("Astronomical night start: " + str(astronomical_night_start))
    print("Astronomical night end: " + str(astronomical_night_end))

  return civil_night_start, civil_night_end, nautical_night_start, nautical_night_end, astronomical_night_start, astronomical_night_end

def apkp():
  try:
    # geomagnetic index
    df_d = sw.sw_daily(update=True)
    df_3h = sw.ap_kp_3h(update=True)
    apkp = df_3h.loc[time.strftime("%Y-%m-%d")] # for one day
    if debug:
      print(apkp)
      print(type(apkp))
    return apkp
  except Exception as e:
    print(str(e))
###sun/moon/night###

# build dynamically based on files in /sky/dso directory
def createHTMLcode_DSO(theDate):

  html = '''<!DOCTYPE html><html>
         <head>
         <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
         <title>
        '''
  html += str(theDate) + ': Tonight\'s DSO\'s</title>'
  html += '''<style>
          figcaption {
          background-color: black;
          color: white;
          font-style: italic;
          padding: 2px;
          text-align: left;
        }
        div.gallery {
          border: 1px solid #ccc;
        }
        div.gallery:hover {
          border: 1px solid #777;
        }
        div.gallery img {
          width: 100%;
          height: auto;
        }
        div.desc {
          padding: 15px;
          text-align: center;
        }
        * {
          box-sizing: border-box;
        }
        .responsive {
          padding: 0 6px;
          float: left;
          width: 49.99999%;
        }
        @media only screen and (max-width: 700px) {
          .responsive {
            width: 49.99999%;
            margin: 6px 0;
          }
        }
        @media only screen and (max-width: 500px) {
          .responsive {
            width: 100%;
          }
        }
        .clearfix:after {
          content: "";
          display: table;
          clear: both;
        }
        </style>
        </head>
        <body style="background-color:black;">'''

  try:
    DSOs = {}
    # load DSO data from file if available
    if os.path.isfile(dso_data_file):
      if debug:
        print("File exists: " + str(dso_data_file))
      with open(dso_data_file, 'r', encoding='utf-8') as f:
        DSOs = json.load(f)
        #print("Loaded DSOs: " + str(DSOs))
        #print(len(DSOs))

    if len(DSOs)>0:
      # sort by max altitude during night time
      sorted_DSOs = dict(sorted(DSOs.items(), key=lambda item: item[1]['max_alt_time']))
      #sorted_DSOs = OrderedDict(reversed(list(sorted_DSOs.items())))
    
      for dso_name, dso_data in sorted_DSOs.items():
        if debug:
          print(dso_name)
          #print(dso_data)
        if dso_data["max_alt"] > 0:
          image_name = "DSO_" + str(dso_name) + "_" + str(theDate) + ".png"
          if debug:
            print(image_name)
          htmlline = '<div class="responsive"><div class="gallery"><figure><a href="https://simbad.cds.unistra.fr/simbad/sim-basic?Ident=' + str(dso_name) + '"  target="_blank"><img src="{{ get_url(\'static\', filename=\'' + str(image_name) + '\') }}" alt="' + str(image_name) + '" title="' + str(dso_data["object_type_string"]) + '"/></a><figcaption>' + str(dso_name) + ': ' + str(dso_data["object_type_string"]) + '</figcaption></figure></div></div>'
        else:
          if debug:
            print(dso_name + " is below the horizon.")
        if debug:
          print(htmlline)
        html += htmlline
    else:
      files = os.listdir(staticImageRoot)
      images = [name for name in files if (name[-4:] in [".png"]) and (name[0] == "D") and (name[1] == "S") and (name[2] == "O") and (str(name.split("_")[2]) == (str(theDate) + ".png"))]
      for i in images:
        if debug:
          print(i)
        name = i.split("_")[1]
        if debug:
          print(name)
          print(DSOs[name])
        htmlline = '<div class="responsive"><div class="gallery"><figure><a href="https://simbad.cds.unistra.fr/simbad/sim-basic?Ident=' + str(name) + '"  target="_blank"><img src="{{ get_url(\'static\', filename=\'' + str(i) + '\') }}" alt="' + str(i) + '" title="' + str(name) + '"/></a><figcaption>' + str(name) + '</figcaption></figure></div></div>'
        if debug:
          print(htmlline)
        html += htmlline
  except Exception as e:
    print(str(e))
    html += '<p style="color:red;"><bold>DSO list for ' + str(theDate) + ' not available.</bold></p>'

  html += '''</body>
          </html>'''
  return html

def createHTMLcode_DSO_list(theDate):

  html = '''<!DOCTYPE html><html>
              <head>
              <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
              <title>'''
  html += str(theDate)
  html += ": Tonight's DSO's</title>"
  html += '''</head>
            <body style="background-color:black;">
            <table>'''

  try:
    files = os.listdir(staticImageRoot)
    images = [name for name in files if (name[-4:] in [".png"]) and (name[0] == "D") and (name[1] == "S") and (name[2] == "O") and (str(name.split("_")[2]) == (str(theDate) + ".png"))]
    for i in images:
      if debug:
        print(i)
      name = i.split("_")[1]
      if debug:
        print(name)
      html += '<tr><td>'
      html += '<a href=\"https://simbad.cds.unistra.fr/simbad/sim-basic?Ident=' + str(name)
      html += '\" target=\"_blank\">' + str(name) + '</a></td></tr>'

  except Exception as e:
    print(str(e))

  html += '''</table>
          </body>
          </html>'''

  if debug:
    print(html)
  return html

def filter_DSOs_direction(DSOs, min_altitude_limit, direction):
  # find objects in desired direction with altitude above xx deg during the night
  #print(DSOs)
  DSOs_in_direction = {}
  for dsoname, dsodata in DSOs.items():
    if debug:
      print(dsoname)
      #print(dsodata)
      #print(dsodata["date"])
      print("Max. altitude during AN: " + str(dsodata["max_alt"]))
      print("Main direction: " + str(dsodata["main_directions"][0]))
    if float(dsodata["max_alt"]) >= float(min_altitude_limit):
      if str(dsodata["main_directions"][0]) == str(direction):
        DSOs_in_direction[dsoname] = dsodata

  if debug:
    print("")
    print("DSOs in direction " + str(direction) + " above " + str(min_altitude_limit) + " deg")
    for dsoname, dsodata in DSOs_in_direction.items():
      print(dsoname + " (" + str(round(dsodata["max_alt"],0)) + " degrees)")
  return DSOs_in_direction

def createHTMLcode_DSO_filtered(theDate, direction, min_altitude_limit, object_type): #object_type: all | cluster | galaxy | nebula
  # build dynamically filtered by direction and altitude
  # read list if it exists
  dso_data_file = path + "/sky/dso/dsos_" + str(theDate) + ".json"

  html = '''<!DOCTYPE html><html>
        <head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title>'''
  html += str(theDate) + ': Tonight\'s best DSO\'s in the ' + str(direction) + ' above ' + str(min_altitude_limit) + ' degrees'
  html += '''</title>
        <style>
          figcaption {
          background-color: black;
          color: white;
          font-style: italic;
          padding: 2px;
          text-align: left;
        }
        div.gallery {
          border: 1px solid #ccc;
        }
        div.gallery:hover {
          border: 1px solid #777;
        }
        div.gallery img {
          width: 100%;
          height: auto;
        }
        div.desc {
          padding: 15px;
          text-align: center;
        }
        * {
          box-sizing: border-box;
        }
        .responsive {
          padding: 0 6px;
          float: left;
          width: 49.99999%;
        }
        @media only screen and (max-width: 700px) {
          .responsive {
            width: 49.99999%;
            margin: 6px 0;
          }
        }
        @media only screen and (max-width: 500px) {
          .responsive {
            width: 100%;
          }
        }
        .clearfix:after {
          content: "";
          display: table;
          clear: both;
        }
        </style>
        </head>
        <body style="background-color:black;">'''

  DSOs = {}
  # load DSO data from file if available
  if os.path.isfile(dso_data_file):
    if debug:
      print("File exists: " + str(dso_data_file))
    with open(dso_data_file, 'r', encoding='utf-8') as f:
      DSOs = json.load(f)
      #print("Loaded DSOs: " + str(DSOs))

    if len(DSOs)>0:
      DSOs_filtered = filter_DSOs_direction(DSOs, min_altitude_limit, direction)
      # sort by max altitude during night time
      #sorted_DSOs = dict(sorted(DSOs_filtered.items(), key=lambda item: item[1]['max_alt_during_night']))
      #sorted_DSOs = OrderedDict(reversed(list(sorted_DSOs.items())))
      DSOs_in_direction_sorted = {k: v for k, v in sorted(DSOs_filtered.items(), key=lambda item: item[1]['max_alt_time'])}
      
      for dso_name, dso_data in DSOs_in_direction_sorted.items():
        if debug:
          print(dso_name)
          #print(dso_data)
        if dso_data["max_alt"]>0:
          image_name = "DSO_" + str(dso_name) + "_" + str(theDate) + ".png"
          if debug:
            print(image_name)
            print(dso_name + " (" + str(round(dso_data["max_alt"],0)) + " degrees)")
          if object_type == "all":
            htmlline = '<div class="responsive"><div class="gallery"><figure><a href="https://simbad.cds.unistra.fr/simbad/sim-basic?Ident=' + str(dso_name) + '"  target="_blank"><img src="{{ get_url(\'static\', filename=\'DSO_' + str(dso_name) + '_' + str(theDate) + '.png\') }}" alt="static DSO_' + str(dso_name) + '_' + str(theDate) + '.png" title="' + str(dso_data["object_type_string"]) + '"/></a><figcaption>' + str(dso_name) + ': ' + str(dso_data["object_type_string"]) + '</figcaption></figure></div></div>'
          elif object_type in str(dso_data["object_type_string"]):
            htmlline = '<div class="responsive"><div class="gallery"><figure><a href="https://simbad.cds.unistra.fr/simbad/sim-basic?Ident=' + str(dso_name) + '"  target="_blank"><img src="{{ get_url(\'static\', filename=\'DSO_' + str(dso_name) + '_' + str(theDate) + '.png\') }}" alt="static DSO_' + str(dso_name) + '_' + str(theDate) + '.png" title="' + str(dso_data["object_type_string"]) + '"/></a><figcaption>' + str(dso_name) + ': ' + str(dso_data["object_type_string"]) + '</figcaption></figure></div></div>'
        else:
          if debug:
            print(dso_name + " is below the horizon.")
        html += htmlline
    else:
      html += '<p><bold>DSO list for ' + str(theDate) + ' not available.</bold></p>'
  else:
    html += '<p><bold>DSO file for ' + str(theDate) + ' not available.</bold></p>'

  html += '''</body>
          </html>'''
  return html

def createHTMLcode_DSO_filtered_list(theDate, direction, min_altitude_limit, object_type): #object_type: all | cluster | galaxy | nebula
  # build dynamically filtered by direction and altitude
  # read list if it exists
  dso_data_file = path + "/sky/dso/dsos_" + str(theDate) + ".json"

  html = '''<!DOCTYPE html><html>
        <head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title>'''
  html += str(theDate) + ': Tonight\'s best DSO\'s in the ' + str(direction) + ' above ' + str(min_altitude_limit) + ' degrees'
  html += '''</title>
        </head>
        <body style="background-color:black;">
        <table>'''

  DSOs = {}
  # load DSO data from file if available
  if os.path.isfile(dso_data_file):
    if debug:
      print("File exists: " + str(dso_data_file))
    with open(dso_data_file, 'r', encoding='utf-8') as f:
      DSOs = json.load(f)
      #print("Loaded DSOs: " + str(DSOs))

    if len(DSOs) > 0:
      for dsoname, dsodata in DSOs.items():
        if debug:
          print(dsoname)
      DSOs_filtered = filter_DSOs_direction(DSOs, min_altitude_limit, direction)
      # sort by max altitude time
      DSOs_in_direction_sorted = {k: v for k, v in sorted(DSOs_filtered.items(), key=lambda item: item[1]['max_alt_time'])}
      if debug:
        print(DSOs_in_direction_sorted)

      if debug:
        print("")
        print("DSOs in direction " + str(direction) + " above " + str(min_altitude_limit) + " deg")
      for dsoname, dsodata in DSOs_in_direction_sorted.items():
        if debug:
          print(dsoname + " (" + str(round(dsodata["max_alt"],0)) + " degrees) type = " + str(dsodata["object_type_string"]) )
        if object_type == "all":
          html += '<tr><td><a href="https://simbad.cds.unistra.fr/simbad/sim-basic?Ident=' + str(dsoname) + '"  target="_blank">' + str(dsoname) + ": " + str(dsodata["object_type_string"]) + '</a></td></tr>'
        elif object_type in str(dsodata["object_type_string"]):
          html += '<tr><td><a href="https://simbad.cds.unistra.fr/simbad/sim-basic?Ident=' + str(dsoname) + '"  target="_blank">' + str(dsoname) + ": " + str(dsodata["object_type_string"]) + '</a></td></tr>'
  else:
    html += '<p style="color:red;"><bold>DSO list for ' + str(theDate) + ' not available.</bold></p>'
  html += '''</table>
          </body>
          </html>'''
  return html

app = bottle.default_app()
BaseTemplate.defaults['get_url'] = app.get_url  # reference to function

@route('/static/<filename:path>', name='static')
def serve_static(filename):
  response = static_file(filename, root=staticImageRoot)
  response.set_header("Cache-Control", "public, max-age=3600")
  return response

@route('/')
@get('/tonight')
def allDSOsEctTonight():
  theDate = time.strftime("%d.%m.%Y")
  theMonthAndYear = time.strftime("%m.%Y")
  theHour = time.strftime("%h")

  with open(str(path) + "/sky/dso/FRAMESET_navigation.html", "w") as text_file:
    html = HTML_NAVIGATION.replace('{theDate}', theDate)

    civil_night_start, civil_night_end, nautical_night_start, nautical_night_end, astronomical_night_start, astronomical_night_end  = astro_night_times(theDate)
    if astronomical_night_start != None and astronomical_night_end != None:
      html = html.replace('{astronight}', "Astro night: " + str(astronomical_night_start.strftime("%H:%M")) + "-" + str(astronomical_night_end.strftime("%H:%M")))
    else:
      html = html.replace('{astronight}', "Nautical night: " + str(nautical_night_start.strftime("%H:%M")) + "-" + str(nautical_night_end.strftime("%H:%M")) + " (no astro night)")

    sunrise, sunset = sun_data(theDate)
    suntime = "Sun: " + str(sunrise) + " - " + str(sunset)
    if debug:
      print(suntime)
    html = html.replace('{suntimes}', suntime)

    moonrise, moonset, full_moon, moon_phase, percent = moon_data(theDate)
    moontime = "Moon: " + str(moonrise) + " - " + str(moonset)
    if debug:
      print(moontime)
    html = html.replace('{moontimes}', moontime)
    html = html.replace('{full_moon}', "Full moon: " + str(full_moon))

    pos = position(datetime.strptime(theDate, "%d.%m.%Y"))
    phasename = phase(pos)

    if debug:
      print("Moon illumination: " + str(percent) + " %")
      print("Phasename: " + str(phase))
    html = html.replace('{moon_phase}', "Moon phase: " + str(phasename) + " (" + str(int(percent)) + " %)")

    try:
      ak = apkp()
      ap = ak.to_dict()['Ap']
      kp = ak.to_dict()['Kp']
      apkp_data = "Kp indices:</br>"
      for t, k in kp.items():
        ki = round(k,1)
        if debug:
          print(ki)
        #apkp_data.append(t.strftime("%H:%M") + ": " + str(ki))
        apkp_data += t.strftime("%H:%M") + ": " + str(ki) + "</br>"
      print(apkp_data)
      html = html.replace('{apkp}', str(apkp_data))
    except Exception as e:
      print(str(e))

    text_file.write("%s" % template(html))

  with open(str(path) + "/sky/dso/FRAMESET_tonight.html", "w") as text_file:
    text_file.write("%s" % template(createHTMLcode_DSO(theDate)))
  with open(str(path) + "/sky/dso/FRAMESET_S10.html", "w") as text_file:
    text_file.write("%s" % template(createHTMLcode_DSO_filtered(theDate, "S", 10.0, "all")))
  with open(str(path) + "/sky/dso/FRAMESET_W10.html", "w") as text_file:
    text_file.write("%s" % template(createHTMLcode_DSO_filtered(theDate, "W", 10.0, "all")))
  with open(str(path) + "/sky/dso/FRAMESET_N10.html", "w") as text_file:
    text_file.write("%s" % template(createHTMLcode_DSO_filtered(theDate, "N", 10.0, "all")))
  with open(str(path) + "/sky/dso/FRAMESET_E10.html", "w") as text_file:
    text_file.write("%s" % template(createHTMLcode_DSO_filtered(theDate, "E", 10.0, "all")))

  html = HTML_FRAMESET.replace('{theDate}', theDate)
  return template(html)

# All DSO's tonight
@get('/alldsos')
def tonight():
  if debug:
    print(str('DSOs TONIGHT'))
  theDate = time.strftime("%d.%m.%Y")
  html = createHTMLcode_DSO(theDate)
  return template(html)

@get('/alldsos/list')
def tonight_list():
  if debug:
    print(str('DSOs TONIGHT'))
  theDate = time.strftime("%d.%m.%Y")
  html = createHTMLcode_DSO_list(theDate)
  return template(html)


# The best DSO's tonight in desired direction above x degrees
@get('/best/<direction>/<min_altitude_limit>')
def tonights_best(direction, min_altitude_limit):
  if debug:
    print(str('DSOs TONIGHT'))
  theDate = time.strftime("%d.%m.%Y")
  html = createHTMLcode_DSO_filtered(theDate, direction, min_altitude_limit, "all")
  return template(html)

@get('/best/<direction>/<min_altitude_limit>/list')
def tonights_best_list(direction, min_altitude_limit):
  if debug:
    print(str('DSOs TONIGHT'))
  theDate = time.strftime("%d.%m.%Y")
  html = createHTMLcode_DSO_filtered_list(theDate, direction, min_altitude_limit, "all")
  return template(html)

# The best DSO's tonight in desired direction above x degrees
@get('/<dd>.<mm>.<yyyy>/best/<direction>/<min_altitude_limit>')
def that_nights_best(dd, mm, yyyy, direction, min_altitude_limit):
  theDate = str(dd) + "." + str(mm) + "." + str(yyyy)
  if debug:
    print("DSOs tonight " + str(theDate) + "...")
  html = createHTMLcode_DSO_filtered(theDate, direction, min_altitude_limit, "all")
  return template(html)

@get('/<dd>.<mm>.<yyyy>')
def night(dd, mm, yyyy):
  if debug:
    print("DSOs at " + str(dd) + "." + str(mm) + "." + str(yyyy))
  theDate = str(dd) + "." + str(mm) + "." + str(yyyy)
  html = createHTMLcode_DSO(theDate)
  return template(html)

@get('/<dd>.<mm>.<yyyy>/list')
def night(dd, mm, yyyy):
  theDate = str(dd) + "." + str(mm) + "." + str(yyyy)
  if debug:
    print("DSOs at " + str(theDate) + "...")
  html = createHTMLcode_DSO_list(theDate)
  return template(html)


# create catalogue for today
@get('/c')
def createCatalogue():
  if debug:
    print("Create catalogue...")
  os.system("python3 " + path + "/sky/dso/DSO_observation_planning.py --catalogue")
  html = HTML_CALCULATING.replace('{theDate}', theDate)
  return template(html)

# create plots and catalogue for today
@get('/p')
def createCatalogueAndPlots():
  if debug:
    print("Create catalogue...")
  os.system("python3 " + path + "/sky/dso/DSO_observation_planning.py --catalogue --plot")
  html = HTML_CALCULATING.replace('{theDate}', theDate)
  return template(html)

# create catalogue for today
@get('/c/<dd>.<mm>.<yyyy>')
def createCatalogueDate(dd, mm, yyyy):
  theDate = str(dd) + "." + str(mm) + "." + str(yyyy)
  if debug:
    print("Create catalogue for " + str(theDate) + "...")
  os.system("python3 " + path + "/sky/dso/DSO_observation_planning.py --catalogue --date " + str(theDate))
  html = HTML_CALCULATING.replace('{theDate}', theDate)
  return template(html)

# create plots and catalogue for today
@get('/p/<dd>.<mm>.<yyyy>')
def createCatalogueAndPlotsDate(dd, mm, yyyy):
  theDate = str(dd) + "." + str(mm) + "." + str(yyyy)
  if debug:
    print("Create catalogue for " + str(theDate) + "...")
  os.system("python3 " + path + "/sky/dso/DSO_observation_planning.py --catalogue --plot --date " + str(theDate))
  html = HTML_CALCULATING.replace('{theDate}', theDate)
  return template(html)

HTML_CALCULATING = '''<!DOCTYPE html><html>
        <head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title>DSO calculation ongoing for {theDate}...</title>
        </head>
        <body>
            <p><bold>DSO calculation ongoing for {theDate}...</bold></p>
        </body>
        </html>
'''

HTML_FRAMESET = '''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Frameset//EN" "http://www.w3.org/TR/html4/frameset.dtd">
<html>
  <head><title>Tonight</title></head>
  <frameset cols="150, *">
    <frame src="static/FRAMESET_navigation.html" name="navigation">
    <frame src="static/FRAMESET_tonight.html" name="in">
  </frameset>
</html>
'''

HTML_NAVIGATION = '''<!DOCTYPE html><html><head>
<link href='https://fonts.googleapis.com/css?family=Open Sans' rel='stylesheet'>
<style>
body {
    font-family: 'Open Sans';
}
</style> <!--font-size: 18px;-->
</head>
<body style="background-color:black;" text="#ffffff">
<h2>{theDate}</h2>
<p>{astronight}</p>
<p>{suntimes}</p>
<p>{moontimes}</p>
<p>{moon_phase}</p>
<p>{full_moon}</p>
<p><a href="FRAMESET_tonight.html" target="in">The Sky Tonight</a></p>
<p><a href="FRAMESET_S10.html" target="in">DSOs S/10 deg</a></p>
<p><a href="FRAMESET_W10.html" target="in">DSOs W/10 deg</a></p>
<p><a href="FRAMESET_N10.html" target="in">DSOs N/10 deg</a></p>
<p><a href="FRAMESET_E10.html" target="in">DSOs E/10 deg</a></p>
<p>{apkp}</p>
</body>
</html>
'''

# run REST server
try:
  if debug:
    print('Launch REST server for DSO visibility')

  print("http://" + str(HOST) + ":" + str(PORT) + "/tonight")
  print("http://" + str(HOST) + ":" + str(PORT) + "/tonight/list")
  print("http://" + str(HOST) + ":" + str(PORT) + "/best/S/10.0")
  print("http://" + str(HOST) + ":" + str(PORT) + "/best/S/10.0/list")
  print("http://" + str(HOST) + ":" + str(PORT) + "/<dd.mm.yyyy>")
  print("http://" + str(HOST) + ":" + str(PORT) + "/<dd.mm.yyyy>/list")
  print("http://" + str(HOST) + ":" + str(PORT) + "/c")
  print("http://" + str(HOST) + ":" + str(PORT) + "/p")
  print("http://" + str(HOST) + ":" + str(PORT) + "/c/<dd.mm.yyyy>")
  print("http://" + str(HOST) + ":" + str(PORT) + "/p/<dd.mm.yyyy>")
  run(host=HOST, port=PORT)

except KeyboardInterrupt:
  exit()


