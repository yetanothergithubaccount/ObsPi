#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ObsPi DSO server
#
import bottle
from bottle import route, run, template, BaseTemplate, get, post, request, static_file # https://bottlepy.org/docs/dev/
from datetime import datetime # for time difference checks
import json, socket
import os, sys
import time

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
imageFilePath = '/home/pi/sky/dso/'
staticImageRoot = '/home/pi/sky/dso/'
######################END#CONFIG##########################

# Target links: https://simbad.cds.unistra.fr/simbad/sim-basic?Ident=M1

# build dynamically based on files in /sky/dso directory
def createHTMLcode(theDate):

  html = '''<html>
         <head>
         <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
         <title>
        '''
  html += str(theDate) + ': Tonight\'s DSO\'s</title>'
  html += '''</head>
          <body>'''

  try:
    '''
    # TODO evaluate json list,
    # sort by max altitude time
    DSOs_in_direction_sorted = {k: v for k, v in sorted(DSOs_filtered.items(), key=lambda item: item[1]['max_alt_time'])}
    if debug:
      print(DSOs_in_direction_sorted)
    '''
    files = os.listdir(staticImageRoot)
    images = [name for name in files if (name[-4:] in [".png"]) and (name[0] == "D") and (name[1] == "S") and (name[2] == "O") and (str(name.split("_")[2]) == (str(theDate) + ".png"))]
    for i in images:
      if debug:
        print(i)
      name = i.split("_")[1]
      if debug:
        print(name)
      html += '<a href="https://simbad.cds.unistra.fr/simbad/sim-basic?Ident=' + str(name) + '"  target="_blank"><img src="{{ get_url(\'static\', filename=\'' + str(i) + '\') }}" alt="static ' + str(i) + '"/></a>'
  except Exception as e:
    print(str(e))

  html += '''</body>
          </html>'''
  return html

def createHTMLcode_list(theDate):

  html = '''<html>
              <head>
              <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
              <title>'''
  html += str(theDate)
  html += ": Tonight's DSO's</title>"
  html += '''</head>
            <body>
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
      print(dsoname + " (" + str(round(dsodata[max_alt],0)) + " degrees)")
  return DSOs_in_direction

def createHTMLcode_filtered(theDate, direction, min_altitude_limit):
  # build dynamically filtered by direction and altitude
  # read list if it exists
  dso_data_file = "/home/pi/sky/dso/dsos_" + str(theDate) + ".json"

  html = '''<html>
        <head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title>'''
  html += str(theDate) + ': Tonight\'s best DSO\'s in the ' + str(direction) + ' above ' + str(min_altitude_limit) + ' degrees'
  html += '''</title>
        </head>
        <body>'''

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
        print("DSOs in direction " + str(direction) + " above " + str(altitude_low_limit) + " deg")
      for dsoname, dsodata in DSOs_in_direction_sorted.items():
        if debug:
          print(dsoname + " (" + str(round(dsodata[max_alt],0)) + " degrees)")
        html += '<a href="https://simbad.cds.unistra.fr/simbad/sim-basic?Ident=' + str(dsoname) + '"  target="_blank"><img src="{{ get_url(\'static\', filename=\'DSO_' + str(dsoname) + '_' + str(theDate) + '.png\') }}" alt="static DSO_' + str(dsoname) + '_' + str(theDate) + '.png" /></a>'

  else:
    html += '<p><bold>DSO list for ' + str(theDate) + ' not available.</bold></p>'

  html += '''</body>
          </html>'''
  return html

def createHTMLcode_filtered_list(theDate, direction, min_altitude_limit):
  # build dynamically filtered by direction and altitude
  # read list if it exists
  dso_data_file = "/home/pi/sky/dso/dsos_" + str(theDate) + ".json"

  html = '''<html>
        <head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title>'''
  html += str(theDate) + ': Tonight\'s best DSO\'s in the ' + str(direction) + ' above ' + str(min_altitude_limit) + ' degrees'
  html += '''</title>
        </head>
        <body>
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
        print("DSOs in direction " + str(direction) + " above " + str(altitude_low_limit) + " deg")
      for dsoname, dsodata in DSOs_in_direction_sorted.items():
        if debug:
          print(dsoname + " (" + str(round(dsodata[max_alt],0)) + " degrees)")
        html += '<tr><td><a href="https://simbad.cds.unistra.fr/simbad/sim-basic?Ident=' + str(dsoname) + '"  target="_blank">' + str(dsoname) + '</a></td></tr>'

  else:
    html += '<p><bold>DSO list for ' + str(theDate) + ' not available.</bold></p>'
  html += '''</table>
          </body>
          </html>'''
  return html

app = bottle.default_app()
BaseTemplate.defaults['get_url'] = app.get_url  # reference to function


@route('/')
def index():
  theDate = time.strftime("%d.%m.%Y")
  #html = HTML_TONIGHT.replace('{theDate}', theDate)
  html = createHTMLcode(theDate)
  return template(html)

@route('/static/<filename:path>', name='static')
def serve_static(filename):
  response = static_file(filename, root=staticImageRoot)
  response.set_header("Cache-Control", "public, max-age=3600")
  return response

# All DSO's tonight
@get('/tonight')
def tonight():
  if debug:
    print(str('DSOs TONIGHT'))
  theDate = time.strftime("%d.%m.%Y")
  html = createHTMLcode(theDate)
  return template(html)

@get('/tonight/list')
def tonight_list():
  if debug:
    print(str('DSOs TONIGHT'))
  theDate = time.strftime("%d.%m.%Y")
  html = createHTMLcode_list(theDate)
  return template(html)


# The best DSO's tonight in desired direction above x degrees
@get('/best/<direction>/<min_altitude_limit>')
def tonights_best(direction, min_altitude_limit):
  if debug:
    print(str('DSOs TONIGHT'))
  theDate = time.strftime("%d.%m.%Y")
  html = createHTMLcode_filtered(theDate, direction, min_altitude_limit)
  return template(html)

@get('/best/<direction>/<min_altitude_limit>/list')
def tonights_best_list(direction, min_altitude_limit):
  if debug:
    print(str('DSOs TONIGHT'))
  theDate = time.strftime("%d.%m.%Y")
  html = createHTMLcode_filtered_list(theDate, direction, min_altitude_limit)
  return template(html)

# The best DSO's tonight in desired direction above x degrees
@get('/<dd>.<mm>.<yyyy>/best/<direction>/<min_altitude_limit>')
def that_nights_best(dd, mm, yyyy, direction, min_altitude_limit):
  theDate = str(dd) + "." + str(mm) + "." + str(yyyy)
  if debug:
    print("DSOs tonight " + str(theDate) + "...")
  html = createHTMLcode_filtered(theDate, direction, min_altitude_limit)
  return template(html)

@get('/<dd>.<mm>.<yyyy>')
def night(dd, mm, yyyy):
  if debug:
    print("DSOs at " + str(dd) + "." + str(mm) + "." + str(yyyy))
  theDate = str(dd) + "." + str(mm) + "." + str(yyyy)
  html = createHTMLcode(theDate)
  return template(html)

@get('/<dd>.<mm>.<yyyy>/list')
def night(dd, mm, yyyy):
  theDate = str(dd) + "." + str(mm) + "." + str(yyyy)
  if debug:
    print("DSOs at " + str(theDate) + "...")
  html = createHTMLcode_list(theDate)
  return template(html)


# create catalogue for today
@get('/c')
def createCatalogue():
  if debug:
    print("Create catalogue...")
  os.system("python3 /home/pi/sky/dso/DSO_observation_planning.py --catalogue")
  html = HTML_CALCULATING.replace('{theDate}', theDate)
  return template(html)

# create plots and catalogue for today
@get('/p')
def createCatalogueAndPlots():
  if debug:
    print("Create catalogue...")
  os.system("python3 /home/pi/sky/dso/DSO_observation_planning.py --catalogue --plot")
  html = HTML_CALCULATING.replace('{theDate}', theDate)
  return template(html)

# create catalogue for today
@get('/c/<dd>.<mm>.<yyyy>')
def createCatalogueDate(dd, mm, yyyy):
  theDate = str(dd) + "." + str(mm) + "." + str(yyyy)
  if debug:
    print("Create catalogue for " + str(theDate) + "...")
  os.system("python3 /home/pi/sky/dso/DSO_observation_planning.py --catalogue --date " + str(theDate))
  html = HTML_CALCULATING.replace('{theDate}', theDate)
  return template(html)

# create plots and catalogue for today
@get('/p/<dd>.<mm>.<yyyy>')
def createCatalogueAndPlotsDate(dd, mm, yyyy):
  theDate = str(dd) + "." + str(mm) + "." + str(yyyy)
  if debug:
    print("Create catalogue for " + str(theDate) + "...")
  os.system("python3 /home/pi/sky/dso/DSO_observation_planning.py --catalogue --plot --date " + str(theDate))
  html = HTML_CALCULATING.replace('{theDate}', theDate)
  return template(html)

HTML_CALCULATING = '''<html>
        <head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title>DSO calculation ongoing for {theDate}...</title>
        </head>
        <body>
            <p><bold>DSO calculation ongoing for {theDate}...</bold></p>
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


