#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ObsPi DSO visibility tool
#
"""
===================================================================
Solveigh's customized DSO observation planning based on

https://docs.astropy.org/en/stable/generated/examples/coordinates/plot_obs-planning.html

Some DSOs found in catalogues like
- the classical Messier catalogue
- Orphaned Beauties: https://www.astrobin.com/in2ev8/
- Faint Giants: https://www.astrobin.com/0unmpq/

Determining and plotting the altitude/azimuth of a celestial object per day.
The results will be fixed in a json-file per day for quick reference.
Supplying a favorite direction (N, E, S, W) and a minimal altitude will 
result in a list of matching DSOs from the internal catalogue.
===================================================================
*Based on developments by: Erik Tollerud, Kelle Cruz*
*License: BSD*
"""

import os, sys, platform
import optparse
import json
import matplotlib.pyplot as plt
import numpy as np
import datetime

from astropy.visualization import astropy_mpl_style, quantity_support
import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time
from astroquery.simbad import Simbad # https://github.com/astropy/astroquery

import config

debug = False #True

parser = optparse.OptionParser()

parser.add_option('-a', '--latitude',
    action="store", dest="latitude",
    help="Latitude", default=config.coordinates['latitude'])
parser.add_option('-o', '--longitude',
    action="store", dest="longitude",
    help="Longitude", default=config.coordinates['longitude'])
parser.add_option('-e', '--elevation',
    action="store", dest="elevation",
    help="Elevation (height)", default=config.coordinates['elevation'])
parser.add_option('-l', '--location',
    action="store", dest="location",
    help="Location", default=config.coordinates['location'])
parser.add_option('-d', '--dso',
    action="store", dest="dso",
    help="Deep space object to check (M1, ...)", default="M31")
parser.add_option('-t', '--date',
    action="store", dest="date",
    help="Date of observation night in format %d.%m.%Y")
parser.add_option('-c', '--catalogue',
    action="store_true", dest="catalogue",
    help="Prepare visibility graphs/descriptions for the whole catalogue", default=False)
parser.add_option('-p', '--plot',
    action="store_true", dest="plot",
    help="Create visibility plots", default=False)

parser.add_option('-r', '--direction',
    action="store", dest="direction",
    help="Consider direction for today's suggestion", default="S") # N / E / W / S
parser.add_option('-i', '--min_altitude',
    action="store", dest="min_altitude",
    help="Consider minimal altitude for today's suggestion", default="10.0")

parser.add_option('-f', '--debug',
    action="store_true", dest="debug",
    help="Debug mode", default=False)
parser.add_option('-m', '--message',
    action="store_true", dest="message",
    help="Send info message", default=False)
parser.add_option('-n', '--sendplots',
    action="store_true", dest="sendplots",
    help="Send plots for suggested DSOs", default=False)

options, args = parser.parse_args()

if options.latitude:
  latitude = options.latitude
else:
  latitude = float(49.878708)

if options.longitude:
  longitude = float(options.longitude)
else:
  longitude = float(8.646927)

if options.elevation:
  elevation = int(options.elevation)

if options.location:
  location = options.location
else:
  location = "Darmstadt"

if options.dso:
  the_object_name = options.dso

if options.date:
  the_date = options.date

if options.debug:
  debug = True

my_DSO_list = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10", "M11", "M12", "M13", "M14", "M15", "M16", "M17", "M18", "M19", "M20", "M21", "M22", "M23", "M24", "M25", "M26", "M27", "M28", "M29", "M30", "M31", "M32", "M33", "M34", "M35", "M36", "M37", "M38", "M39", "M40", "M41", "M42", "M43", "M44", "M45", "M46", "M47", "M48", "M49", "M50", "M51", "M52", "M53", "M54", "M55", "M56", "M57", "M58", "M59", "M60", "M61", "M62", "M63", "M64", "M65", "M66", "M67", "M68", "M69", "M70", "M71", "M72", "M73", "M74", "M75", "M76", "M77", "M78", "M79", "M80", "M81", "M82", "M83", "M84", "M85", "M86", "M87", "M88", "M89", "M90", "M91", "M92", "M93", "M94", "M95", "M96", "M97", "M98", "M99", "M100", "M101", "M102", "M103", "M104", "M105", "M106", "M107", "M108", "M109", "M110", "NGC7822", "SH2-173", "NGC210", "IC63", "SH2-188", "NGC613", "NGC660", "NGC672", "NGC918", "IC1795", "IC1805", "NGC1055", "IC1848", "SH2-200", "NGC1350", "NGC1499", "LBN777", "NGC1532", "LDN1495", "NGC1555", "NGC1530", "NGC1624", "NGC1664", "Melotte15", "vdb31", "NGC1721", "IC2118", "IC410", "SH2-223", "SH2-224", "IC434", "SH2-240", "LDN1622", "SH2-261", "SH2-254", "NGC2202", "IC443", "NGC2146", "NGC2217", "NGC2245", "SH2-308", "NGC2327", "SH2-301", "Abell21", "NGC2835", "Abell33", "NGC2976","Arp316", "NGC3359", "Arp214", "NGC4395", "NGC4535", "Abell35", "NGC5068", "NGC5297", "NGC5371", "NGC5364", "NGC5634", "NGC5701", "NGC5963", "NGC5982", "IC4592", "IC4628", "Barnard59", "SH2-003", "Barnard252", "NGC6334", "NGC6357", "Barnard75", "NGC6384", "SH2-54", "vdb126", "SH2-82", "NGC6820", "SH2-101", "WR134", "LBN331", "LBN325", "SH2-112", "SH2-115", "LBN468", "IC5070", "vdb141", "SH2-114", "vdb152", "SH2-132", "Arp319", "NGC7497", "SH2-157", "NGC7606", "Abell85", "LBN 564", "SH2-170", "LBN603", "LBN639", "LBN640", "LDN1333", "NGC1097", "LBN762", "SH2-202", "vdb14", "vdb15", "LDN1455", "vdb13", "vdb16", "IC348", "SH2-205", "SH2-204", "Barnard208", "Barnard7", "vdb27", "Barnard8", "Barnard18", "SH2-216", "Abell7", "SH2-263", "SH2-265", "SH2-232", "Barnard35", "SH2-249", "IC447", "SH2-280", "SH2-282", "SH2-304", "SH2-284", "LBN1036", "NGC2353", "SH2-310", "SH2-302", "Gum14", "Gum15", "Gum17", "Abell31", "SH2-1", "SH2-273", "SH2-46", "SH2-34", "IC4685", "SH2-91", "Barnard147", "IC1318b", "LBN380", "Barnard150", "LBN552", "SH2-119", "SH2-124", "Barnard169", "LBN420", "SH2-134", "SH2-150", "LDN1251", "LBN438", "SH2-154", "LDN1218", "SH2-160", "SH2-122", "LBN575", "LDN1262", "LBN534", "vdb158", "IC4703"]

class DSO:

  def __init__(self, the_object_name, today, tomorrow):
    self.the_object_name = the_object_name
    self.theDate = today.strftime("%Y-%m-%d")
    self.today = today
    self.tomorrow = tomorrow

    ##############################################################################
    # `astropy.coordinates.SkyCoord.from_name` uses Simbad to resolve object
    # names and retrieve coordinates.
    #
    # Get the coordinates of the desired DSO:
    self.the_object = SkyCoord.from_name(self.the_object_name)

    # http://vizier.u-strasbg.fr/cgi-bin/OType?$1
    result_table = Simbad.query_tap("SELECT main_id, otype FROM basic WHERE main_id IN ('" + str(self.the_object_name) + "')")
    if debug:
      print(result_table)
    if result_table:
      self.object_type = result_table["otype"].pformat()[2].strip()
    else:
      self.object_type = ""
    if debug:
      print("Object type: " + str(self.object_type))

    if self.object_type == "AGN":
      self.object_type_string = "Active galaxy nucleus"
    elif self.object_type == "SNR":
      self.object_type_string = "SuperNova remnant"
    elif self.object_type == "SFR":
      self.object_type_string = "Star forming region"
    elif self.object_type == "SFR":
      self.object_type_string = "Star forming region"
    elif self.object_type == "GNe":
      self.object_type_string = "Nebula"
    elif self.object_type == "RNe":
      self.object_type_string = "Reflection nebula"
    elif self.object_type == "GDNe":
      self.object_type_string = "Dark cloud (nebula)"
    elif self.object_type == "MoC":
      self.object_type_string = "Molecular cloud"
    elif self.object_type == "IG":
      self.object_type_string = "Interacting galaxies"
    elif self.object_type == "PaG":
      self.object_type_string = "Pair of galaxies"
    elif self.object_type == "GiP":
      self.object_type_string = "Galaxy in pair of galaxies"
    elif self.object_type == "CGG":
      self.object_type_string = "Compact group of galaxies"
    elif self.object_type == "CIG":
      self.object_type_string = "Cluster of galaxies"
    elif self.object_type == "BH":
      self.object_type_string = "Black hole"
    elif self.object_type == "LSB":
      self.object_type_string = "Low surface brightness galaxy"
    elif self.object_type == "SBG":
      self.object_type_string = "Starburst galaxy"
    elif self.object_type == "H2G":
      self.object_type_string = "HII galaxy"
    elif self.object_type == "GGG":
      self.object_type_string = "Galaxy"
    elif self.object_type == "Cl":
      self.object_type_string = "Cluster of stars"
    elif self.object_type == "GlC":
      self.object_type_string = "Globular cluster"
    elif self.object_type == "OpC":
      self.object_type_string = "Open cluster"
    elif self.object_type == "Cl*":
      self.object_type_string = "Open cluster"
    elif self.object_type == "LIN":
      self.object_type_string = "LINER-type active galaxy nucleus"
    elif self.object_type == "SyG":
      self.object_type_string = "Seyfert galaxy"
    elif self.object_type == "Sy1":
      self.object_type_string = "Seyfert 1 galaxy"
    elif self.object_type == "Sy2":
      self.object_type_string = "Seyfert 2 galaxy"
    elif self.object_type == "GiG":
      self.object_type_string = "Galaxy towards a group of galaxies"
    elif self.object_type == "As*":
      self.object_type_string = "Association of stars"
    elif self.object_type == "PN":
      self.object_type_string = "Planetary nebula"
    else:
      self.object_type_string = ""

    time = Time(str(self.theDate) + " 23:59:00") + utcoffset
    if debug:
      print(time)

    ##############################################################################
    # `astropy.coordinates.EarthLocation.get_site_names` and
    # `~astropy.coordinates.EarthLocation.get_site_names` can be used to get
    # locations of major observatories.
    #
    # Use `astropy.coordinates` to find the Alt, Az coordinates of the DSO at as
    # observed from the current location today
    self.the_object_altaz = self.the_object.transform_to(AltAz(obstime=time, location=the_location))
    to_alt = self.the_object_altaz.alt
    to_az = self.the_object_altaz.az
    if debug:
      print(str(self.the_object_name) + "'s altitude = " + str(to_alt) + ", azimut = " + str(to_az))

    direction = self.get_compass_direction(to_az.value)
    if debug:
      print(str(time) + ": " + str(direction))


    ##############################################################################
    # This is helpful since it turns out M33 is barely above the horizon at this
    # time. It's more informative to find M33's airmass over the course of
    # the night.
    #
    # Find the alt,az coordinates of the object at 100 times evenly spaced between 10pm
    # and 7am EDT:
    # +1: otherwise the dso graph does not match the x-axis ticks
    self.midnight = Time(str(self.theDate) + " 00:00:00") + 1 #utcoffset
    self.delta_midnight = np.linspace(-2, 10, 100) * u.hour
    self.frame_night = AltAz(obstime=self.midnight + self.delta_midnight, location=the_location)
    self.the_objectaltazs_night = self.the_object.transform_to(self.frame_night)

    ##############################################################################
    # convert alt, az to airmass with `~astropy.coordinates.AltAz.secz` attribute:
    #the_objectairmasss_night = the_objectaltazs_night.secz
    ##############################################################################
    # Plot the airmass as a function of time:
    '''
    plt.plot(delta_midnight, the_objectairmasss_night)
    plt.xlim(-2, 10)
    plt.ylim(1, 4)
    plt.xlabel("Hours from EDT Midnight")
    plt.ylabel("Airmass [Sec(z)]")
    plt.show()
    '''

    ##############################################################################
    # Use  `~astropy.coordinates.get_sun` to find the location of the Sun at 1000
    # evenly spaced times between noon on July 12 and noon on July 13:
    from astropy.coordinates import get_sun
    self.delta_midnight = np.linspace(-12, 12, 1000) * u.hour
    self.times_overnight = self.midnight + self.delta_midnight
    self.frame_over_night = AltAz(obstime=self.times_overnight, location=the_location)
    self.sunaltazs_over_night = get_sun(self.times_overnight).transform_to(self.frame_over_night)


    ##############################################################################
    # Do the same with `~astropy.coordinates.get_body` to find when the moon is
    # up. Be aware that this will need to download a 10MB file from the internet
    # to get a precise location of the moon.
    from astropy.coordinates import get_body
    self.moon_over_night = get_body("moon", self.times_overnight)
    self.moonaltazs_over_night = self.moon_over_night.transform_to(self.frame_over_night)

    ##############################################################################
    # Find the alt,az coordinates of the object at those same times:
    self.the_astro_night_start, self.the_astro_night_end = self.astro_night_time(today, tomorrow)
    self.the_objectaltazs_over_night = self.the_object.transform_to(self.frame_over_night)
    #self.dso_in_the_dark_alt_max, self.direction_max_alt, self.dso_in_the_dark_ot, self.alt_max_total, self.direction_max_total, self.max_total_obstime = self.max_altitudes(frame_over_night, the_objectaltazs_over_night)
    self.max_alt, self.max_alt_direction, self.max_alt_time, self.max_alt_during_night, self.max_alt_during_night_direction, self.max_alt_during_night_obstime = self.max_altitudes(self.frame_over_night, self.the_objectaltazs_over_night)

  def astro_night_time(self, today, tomorrow):
    t_22 = datetime.time(hour=22, minute=0)
    self.the_astro_night_start = datetime.datetime.combine(today, t_22)
    t_4 = datetime.time(hour=4, minute=0)
    self.the_astro_night_end = datetime.datetime.combine(tomorrow, t_4)
    if debug:
      print("AN start: " + str(self.the_astro_night_start))
      print("AN end: " + str(self.the_astro_night_end))
    return self.the_astro_night_start, self.the_astro_night_end

  def max_altitudes(self, frame_over_night, the_objectaltazs_over_night):
    try:
      if debug:
        print("Check object alt az during night time")
      dso_in_the_dark_ot = []
      dso_in_the_dark_alt = []
      dso_in_the_dark_az = []
      for o in the_objectaltazs_over_night:
        dt = o.obstime.tt.datetime
        if dt > self.the_astro_night_start and dt < self.the_astro_night_end:
          #print(str(o.obstime) + ": " + str(o.alt) + ", " + str(o.az))
          dso_in_the_dark_alt.append(o.alt.value)
          dso_in_the_dark_az.append(o.az.value)
          dso_in_the_dark_ot.append(o.obstime.tt.datetime)
      dso_in_the_dark_alt_max = max(dso_in_the_dark_alt)
      index_alt_max = np.argmax(dso_in_the_dark_alt)
      #print(dso_in_the_dark_alt_max)
      #print(index_alt_max)
      if debug:
        print("DSO night max alt: " + str(dso_in_the_dark_alt_max) + " at " + str(dso_in_the_dark_ot[index_alt_max]))
      dso_in_the_dark_alt_max_az = dso_in_the_dark_az[index_alt_max]
      #print(dso_in_the_dark_alt_max_az)
      direction_max_alt = self.get_compass_direction(dso_in_the_dark_alt_max_az)
      if debug:
        print("DSO night max alt direction: " + str(direction_max_alt))
      # Direction of total max. altitude
      alt_max_total = max(the_objectaltazs_over_night.alt.value)
      index_alt_max_total = np.argmax(the_objectaltazs_over_night.alt)
      direction_max_alt_total = self.get_compass_direction(the_objectaltazs_over_night.az[index_alt_max_total].value)
      alt_max_total_obstime = frame_over_night.obstime[index_alt_max_total]
      if debug:
        max_alt_txt = "Max. Alt. " + str(round(alt_max_total,2)) + "deg at: " + str(alt_max_total_obstime) + " in " + str(direction_max_alt_total)
        print(max_alt_txt)
      return dso_in_the_dark_alt_max, direction_max_alt, dso_in_the_dark_ot[index_alt_max], alt_max_total, direction_max_alt_total, alt_max_total_obstime
    except Exception as e:
      print(str(e))

  def observation_night_directions(self):
    try:
      # observation directions 20 pm .. 4 am
      theDate_today = self.today.strftime("%Y-%m-%d")
      theDate_tomorrow = self.tomorrow.strftime("%Y-%m-%d")

      # 20 pm
      time = Time(str(theDate_today) + " 18:59:00") + utcoffset
      if debug:
        print(time)
      the_object_altaz = self.the_object.transform_to(AltAz(obstime=time, location=the_location))
      to_alt = the_object_altaz.alt
      to_az = the_object_altaz.az
      if debug:
        print(str(self.the_object_name) + "'s altitude = " + str(to_alt) + ", azimut = " + str(to_az))
      direction_20 = self.get_compass_direction(to_az.value)
      if debug:
        print(str(time) + ": " + str(direction_20))

      # 22 pm
      time = Time(str(theDate_today) + " 20:59:00") + utcoffset
      if debug:
        print(time)
      the_object_altaz = self.the_object.transform_to(AltAz(obstime=time, location=the_location))
      to_alt = the_object_altaz.alt
      to_az = the_object_altaz.az
      if debug:
        print(str(self.the_object_name) + "'s altitude = " + str(to_alt) + ", azimut = " + str(to_az))
      direction_22 = self.get_compass_direction(to_az.value)
      if debug:
        print(str(time) + ": " + str(direction_22))

      # 24 pm
      time = Time(str(theDate_today) + " 21:59:00") + utcoffset
      if debug:
        print(time)
      the_object_altaz = self.the_object.transform_to(AltAz(obstime=time, location=the_location))
      to_alt = the_object_altaz.alt
      to_az = the_object_altaz.az
      if debug:
        print(str(self.the_object_name) + "'s altitude = " + str(to_alt) + ", azimut = " + str(to_az))
      direction_0 = self.get_compass_direction(to_az.value)
      if debug:
        print(str(time) + ": " + str(direction_0))

      # 2 am
      time = Time(str(theDate_tomorrow) + " 00:00:00") + utcoffset
      if debug:
        print(time)
      the_object_altaz = self.the_object.transform_to(AltAz(obstime=time, location=the_location))
      to_alt = the_object_altaz.alt
      to_az = the_object_altaz.az
      if debug:
        print(str(self.the_object_name) + "'s altitude = " + str(to_alt) + ", azimut = " + str(to_az))
      direction_2 = self.get_compass_direction(to_az.value)
      if debug:
        print(str(time) + ": " + str(direction_2))

      # 4 am
      time = Time(str(theDate_tomorrow) + " 01:59:00") + utcoffset
      if debug:
        print(time)
      the_object_altaz = self.the_object.transform_to(AltAz(obstime=time, location=the_location))
      to_alt = the_object_altaz.alt
      to_az = the_object_altaz.az
      if debug:
        print(str(self.the_object_name) + "'s altitude = " + str(to_alt) + ", azimut = " + str(to_az))
      direction_4 = self.get_compass_direction(to_az.value)
      if debug:
        print(str(time) + ": " + str(direction_4))

      # 6 am
      time = Time(str(theDate_tomorrow) + " 03:59:00") + utcoffset
      if debug:
        print(time)
      the_object_altaz = self.the_object.transform_to(AltAz(obstime=time, location=the_location))
      to_alt = the_object_altaz.alt
      to_az = the_object_altaz.az
      if debug:
        print(str(self.the_object_name) + "'s altitude = " + str(to_alt) + ", azimut = " + str(to_az))
      direction_6 = self.get_compass_direction(to_az.value)
      if debug:
        print(str(time) + ": " + str(direction_6))

      return direction_20, direction_22, direction_0, direction_2, direction_4, direction_6
    except Exception as e:
      print(str(e))

  def plot(self):
    try:
      plt.clf()
      plt.cla()
      plt.close()
      #ax = plt.axes()
      # Setting the background color of the plot 
      # using set_facecolor() method
      #ax.set_facecolor("lightgrey")
      #plt.figure(facecolor='lightgrey')
      plt.figure(facecolor='lightgrey')
      plt.style.use(astropy_mpl_style)
      quantity_support()

      direction_20, direction_22, direction_0, direction_2, direction_4, direction_6 = self.observation_night_directions()

      ##############################################################################
      # Make a beautiful figure illustrating nighttime and the altitudes of the DSO and
      # the Sun over that time:
      plt.plot(self.delta_midnight, self.sunaltazs_over_night.alt, color="orange", label="Sun")
      plt.plot(self.delta_midnight, self.moonaltazs_over_night.alt, color=[0.75] * 3, ls="--", label="Moon")
      # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.scatter.html
      plt.scatter(
          self.delta_midnight,
          self.the_objectaltazs_over_night.alt,
          c=self.the_objectaltazs_over_night.az.value,
          label=str(self.the_object_name),
          linewidths=0,
          s=8,
          cmap="viridis",)
      plt.fill_between(
          self.delta_midnight,
          0 * u.deg,
          90 * u.deg,
          self.sunaltazs_over_night.alt < 3 * u.deg,
          color="0.55",
          zorder=0,)  # twilight time
      plt.fill_between(
          self.delta_midnight,
          0 * u.deg,
          90 * u.deg,
          self.sunaltazs_over_night.alt < -3 * u.deg,
          color="0.35",
          zorder=0,)  # night time
      plt.fill_between(
          self.delta_midnight,
          0 * u.deg,
          90 * u.deg,
          self.sunaltazs_over_night.alt < -18 * u.deg,
          color="k",
          zorder=0,)
      plt.colorbar().set_label("Azimuth [deg]")
      plt.legend(loc="upper left")
      plt.xlim(-12 * u.hour, 12 * u.hour)
      plt.xticks((np.arange(13) * 2 - 12) * u.hour)

      plt.ylim(0 * u.deg, 90 * u.deg)
      plt.xlabel("Hours from Midnight") # EDT: Eastern Daylight Time
      plt.ylabel("Altitude [deg]")
     
      today_tomorrow = self.today.strftime("%d") + "." + self.today.strftime("%m") + "." + self.today.strftime("%y") + "-" +  self.tomorrow.strftime("%d") + "." + self.tomorrow.strftime("%m") + "." + self.tomorrow.strftime("%y")

      plt.title(str(self.the_object_name) + " " + str(today_tomorrow) + ": " + str(direction_20) + "-" + str(direction_22) + "-" + str(direction_0) + "-" + str(direction_2) + "-" + str(direction_4) + "-" + str(direction_6))

      theDate_format = self.today.strftime("%d.%m.%Y")

      imageName = "/home/pi/sky/dso/DSO_" + str(self.the_object_name) + "_" + str(theDate_format) + ".png"
      if platform.system() == "Windows":
        imageName = "E:\\DEV\\RaspberryPi3\\theServer\\sky\\dso\\DSO_" + str(self.the_object_name) + "_" + str(theDate_format) + ".png"
      plt.savefig(imageName)
      if debug:
        print("Saved: " + str(imageName))

    except Exception as e:
      print("DSO observation night plotting error " + str(self.the_object_name) + ": " + str(e))

  def get_compass_direction(self, azimuth):
    direction = ""
    '''
    N: 0
    NE: 45
    E: 90
    ES: 135
    S: 180
    SW: 225
    W: 270
    WN: 315
    '''
    if azimuth >= 0 and azimuth < 15:
      direction = "N"
    if azimuth >= 15 and azimuth < 30:
      direction = "NNE"
    if azimuth >= 30 and azimuth < 60:
      direction = "NE"
    if azimuth >= 60 and azimuth < 75:
      direction = "ENE"
    if azimuth >= 75 and azimuth < 105:
      direction = "E"
    if azimuth >= 105 and azimuth < 135:
      direction = "ESE"
    if azimuth >= 135 and azimuth < 150:
      direction = "SE"
    if azimuth >= 150 and azimuth < 165:
      direction = "SSE"
    if azimuth >= 165 and azimuth < 195:
      direction = "S"
    if azimuth >= 195 and azimuth < 225:
      direction = "SSW"
    if azimuth >= 225 and azimuth < 240:
      direction = "SW"
    if azimuth >= 240 and azimuth < 255:
      direction = "WSW"
    if azimuth >= 255 and azimuth < 285:
      direction = "W"
    if azimuth >= 285 and azimuth < 300:
      direction = "WNW"
    if azimuth >= 300 and azimuth < 330:
      direction = "NW"
    if azimuth >= 330 and azimuth < 345:
      direction = "NWN"
    if azimuth >= 345 and azimuth <= 360:
      direction = "N"
    if debug:
      print("Direction: " + str(direction))
    return direction

  def score_altitude(self, alt):
    score_total = 0
    if self.max_alt == self.max_alt_during_night:
      # bingo
      score_total += 7
    elif self.max_alt <= 0:
      score_total = 0
    elif self.max_alt < 10.0:
      score_total += 0.5
    elif self.max_alt <= 10.0:
      score_total += 1
    elif self.max_alt <= 20.0:
      score_total += 2
    elif self.max_alt <= 30.0:
      score_total += 3
    elif self.max_alt <= 40.0:
      score_total += 4
    elif self.max_alt <= 50.0:
      score_total += 5
    else:
      score_total += 6
    return score_total

  def score(self):
    # check visibility over horizon and direction during night time, search max altitude
    # evaluate whether its worth to look at the object

    score_total = 0
    msg = str(self.the_object_name) + " is barely visible."
    if debug:
      print("Max. alt during astronimical night: " + str(self.max_alt) + " at " + str(self.max_alt_time))
      print("Max. alt: " + str(self.max_alt_during_night) + " at " + str(self.max_alt_during_night_obstime))
    if self.max_alt >= self.max_alt_during_night:
      score_total += 2
      # altitude maximum during astronomical night
      msg = str(self.the_object_name) + " max. altitude " + str(round(self.max_alt,0)) + " deg reached during night time at " + str(self.max_alt_time) + " in " + str(self.max_alt_direction)
      if debug:
        print(msg)
      score_total += self.score_altitude(self.max_alt)
      if score_total == 0:
        msg += "\n"
        msg += str(self.the_object_name) + " is invisible."
        return 0, msg
      msg += "\n"
      msg += str(self.the_object_name) + " is best observed at " + str(self.max_alt_time) + " in " + str(self.max_alt_direction)

    else:
      score_total += 1
      msg = str(self.the_object_name) + " max. altitude " + str(round(self.max_alt_during_night,0)) + " deg reached at " + str(self.max_alt_during_night_obstime) + " in " + str(self.max_alt_during_night_direction) + "\n"
      msg += str(self.the_object_name) + " max. altitude " + str(round(self.max_alt,0)) + " deg reached during night time at " + str(self.max_alt_time) + " in " + str(self.max_alt_direction)
      score_total += self.score_altitude(self.max_alt)
      if score_total == 0:
        msg += "\n"
        msg += str(self.the_object_name) + " is invisible."
        return 0, msg
      msg += "\n"
      msg += str(self.the_object_name) + " is best observed before " + str(self.max_alt_time) + " in " + str(self.max_alt_direction)

    # score = 0 : object is invisible
    # score > 1 : object is visible at all close to the horizon
    # score > 2 : object is visible
    # score > 3 : very good visibility
    return score_total, msg

def store_DSO_data_in_file(DSOs, dso_data_file):
  try:
    if debug:
      #print(DSOs)
      print("Store dso data in file " + str(dso_data_file))
    if not os.path.isfile(dso_data_file):
      with open(dso_data_file, 'w', encoding='utf-8') as f:
        json.dump(DSOs, f, ensure_ascii=False, default=serialize_datetime)
        if debug:
          print("DSO file written: " + str(dso_data_file))
  except Exception as e:
    print("DSO write json file error: " + str(e))

def DSOs_tonight(today, tomorrow, plot):
  # check DSO list for good visible objects in the desired directions

  theDate = today.strftime("%d.%m.%Y")
  if platform.system() == "Linux":
    dso_data_file = "/home/pi/sky/dso/dsos_" + str(theDate) + ".json"

  DSOs = {}
  # load DSO data from file if available
  if os.path.isfile(dso_data_file):
    if debug:
      print("File exists: " + str(dso_data_file))
    with open(dso_data_file, 'r', encoding='utf-8') as f:
      DSOs = json.load(f)
      if debug:
        print("Loaded DSOs: " + str(DSOs))
  else:
    if debug:
      print(str(dso_data_file) + " does not exist yet. Create it...")


  if len(DSOs) == 0:
    if debug:
      print("Check the DSO list...this will take a while...")
    for dso in ( my_DSO_list ):
      if debug:
        print("")
        print("DSO: " + str(dso))
      dsoo = DSO(dso, today, tomorrow)
      if plot:
        dsoo.plot()
      max_alt, max_alt_direction, max_alt_time, max_alt_during_whole_night, max_alt_during_whole_night_direction, max_alt_during_whole_night_obstime = dsoo.max_altitudes(dsoo.frame_over_night, dsoo.the_objectaltazs_over_night)
      direction_20, direction_22, direction_0, direction_2, direction_4, direction_6 = dsoo.observation_night_directions()
      main_directions = direction_20 + direction_22 + direction_0 + direction_2 + direction_4 + direction_6

      # investigate main directions
      num_N = main_directions.count('N')
      num_E = main_directions.count('E')
      num_S = main_directions.count('S')
      num_W = main_directions.count('W')
      mdl = []
      mdl.append(num_N)
      mdl.append(num_E)
      mdl.append(num_S)
      mdl.append(num_W)
      if debug:
        print(main_directions)
        print("N: " + str(num_N))
        print("E: " + str(num_E))
        print("S: " + str(num_S))
        print("W: " + str(num_W))
      main_direction_idx1 = np.argmax(mdl) # top max
      main_dirs = ''
      if main_direction_idx1 == 0:
        main_dirs += 'N'
      elif main_direction_idx1 == 1:
        main_dirs += 'E'
      elif main_direction_idx1 == 2:
        main_dirs += 'S'
      elif main_direction_idx1 == 3:
        main_dirs += 'W'

      mdl[main_direction_idx1] = 0 # remove top max from list to keep indices
      main_direction_idx2 = np.argmax(mdl) # second max
      if main_direction_idx2 == 0:
        main_dirs += 'N'
      elif main_direction_idx2 == 1:
        main_dirs += 'E'
      elif main_direction_idx2 == 2:
        main_dirs += 'S'
      elif main_direction_idx2 == 3:
        main_dirs += 'W'

      if debug:
        print(str(dso) + " main directions: " + str(main_dirs))

      # try to evaluate DSO visibility by its altitude during night time
      score, msg = dsoo.score()
      if debug:
        print("Max. alt: " + str(max_alt) + " at " + str(max_alt_time))

      dsodata = {
        'date' : theDate,
        'max_alt' : max_alt,
        'max_alt_direction' : max_alt_direction,
        'max_alt_time' : max_alt_time,
        'max_alt_during_night' : max_alt_during_whole_night,
        'max_alt_during_night_direction' : max_alt_during_whole_night_direction,
        'max_alt_during_night_obstime' : max_alt_during_whole_night_obstime,
        'direction_20' : direction_20,
        'direction_22' : direction_22,
        'direction_0' : direction_0,
        'direction_2' : direction_2,
        'direction_4' : direction_4,
        'direction_6' : direction_6,
        'main_directions' : main_dirs,
        'score' : score
        }
      DSOs[dso] = dsodata

    # serialize DSO data into json file for quick reference
    store_DSO_data_in_file(DSOs, dso_data_file)

    '''
    if debug:
      #print(DSOs)
      print("Store dso data in file " + str(dso_data_file))
    if not os.path.isfile(dso_data_file):
      with open(dso_data_file, 'w', encoding='utf-8') as f:
        json.dump(DSOs, f, ensure_ascii=False, default=serialize_datetime)
        if debug:
          print("DSO file written: " + str(dso_data_file))
    '''
  return DSOs

# Define a custom function to serialize datetime objects 
def serialize_datetime(obj): 
  if isinstance(obj, datetime.datetime): 
    return obj.strftime("%Y-%m-%d %H:%M:%S") #obj.isoformat() 

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
      print(dsoname)
  return DSOs_in_direction


if __name__ == '__main__':

  try:
    ##############################################################################
    # Use `astropy.coordinates.EarthLocation` to provide the location of the
    # desired time
    #the_location = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg, height=elevation * u.m)
    the_location = EarthLocation(lat=latitude, lon=longitude, height=elevation)
    utcoffset = 0 * u.hour  # +2 +1?
    now = datetime.datetime.now()
    just_now = now.strftime("%Y-%m-%d %H:%M:%S")
    theDate = now.strftime("%d.%m.%Y")
    theDate_today = now.strftime("%Y-%m-%d")

    today = datetime.date.today()
    if options.date:
      if debug:
        print("The desired date: " + str(options.date))
      theDay = options.date.split(".")[0]
      theMonth = options.date.split(".")[1]
      theYear = options.date.split(".")[2]
      today = today.replace(day=int(theDay), month=int(theMonth), year=int(theYear))

    tomorrow = today + datetime.timedelta(days=1)
    if debug:
      print("Now: " + str(now))
      print("The day: " + str(today))
      print("The day after: " + str(tomorrow))

    if options.catalogue:
      DSOs = DSOs_tonight(today, tomorrow, options.plot)

      if options.direction and options.min_altitude:
        DSOs_in_direction = filter_DSOs_direction(DSOs, str(options.min_altitude), str(options.direction[0]))
        if len(DSOs_in_direction) > 0:
          msg = str(theDate) + ": DSOs matching direction " + str(options.direction) + " and min altitude " + str(options.min_altitude) + " found:"
          if debug:  
            print(msg)
          msg = ""

          # sort by max altitude time
          DSOs_in_direction_sorted = {k: v for k, v in sorted(DSOs_in_direction.items(), key=lambda item: item[1]['max_alt_time'])}
          if debug:
            print(DSOs_in_direction_sorted)

          for dsoname, dsodata in DSOs_in_direction_sorted.items():
            if debug:
              print(dsoname)
            msg += dsoname + " (" + str(round(dsodata['max_alt'],1)) + " at " + str(dsodata['max_alt_time']) + " in " + str(dsodata['max_alt_direction']) + ")\n"

          # send plots optionally
          if options.sendplots:
            for dsoname, dsodata in DSOs_in_direction_sorted.items():
              if debug:
                print(dsoname)
              if platform.system() == "Linux":
                plotname = "/home/pi/sky/dso/DSO_" + str(dsoname) + "_" + str(theDate) + ".png"
        else:
          msg = "No DSOs matching direction " + str(options.direction) + " and min altitude " + str(options.min_altitude) + " found."
          if debug:
            print(msg)
    else:
      dso = DSO(the_object_name, today, tomorrow)
      if options.plot:
        dso.plot()

      score, msg = dso.score()
      print("Score: " + str(score))
      print(msg)

  except Exception as e:
    print("DSO observation planning error " + str(the_object_name) + ": " + str(e))
  sys.exit(0)

