#!/usr/bin/env python

from __future__ import print_function
import io
import json
import logging
import os
import sys
import util

default_systems_file = "eddb/systems.json"
default_stations_file = "eddb/stations.json"

eddb_systems_url = "http://eddb.io/archive/v4/systems.json"
eddb_stations_url = "http://eddb.io/archive/v4/stations.json"

eddb_systems_file_size_limit = 400 * 1048576
eddb_stations_file_size_limit = 400 * 1048576

log = logging.getLogger("eddb")

def download_eddb_files(sys_file, station_file):
  # If the systems.json's directory doesn't exist, make it
  if not os.path.exists(os.path.dirname(sys_file)):
    os.makedirs(os.path.dirname(sys_file))
  # If the stations.json's directory doesn't exist, make it
  if not os.path.exists(os.path.dirname(station_file)):
    os.makedirs(os.path.dirname(station_file))

  # Download the systems.json
  log.info("Downloading EDDB Systems list from {0} ... ".format(eddb_systems_url))
  sys.stdout.flush()
  util.download_file(eddb_systems_url, sys_file)
  log.info("Done.")
  log.info("Downloading EDDB Stations list from {0} ... ".format(eddb_stations_url))
  sys.stdout.flush()
  util.download_file(eddb_stations_url, station_file)
  log.info("Done.")


def check_systems(filename):
  if os.path.isfile(filename):
    try:
      s = load_systems(filename)
      return len(s)
    except:
      return False
  else:
    return False

def check_stations(filename):
  if os.path.isfile(filename):
    try:
      s = load_stations(filename)
      return len(s)
    except:
      return False
  else:
    return False

def load_systems(filename):
  return load_json(filename, eddb_systems_file_size_limit)

def load_stations(filename):
  return load_json(filename, eddb_stations_file_size_limit)

def load_json(filename, size_limit):
  f = io.open(filename, "r")
  return json.loads(f.read(size_limit))


if __name__ == '__main__':
  logging.basicConfig(level = logging.INFO, format="[%(asctime)-15s] [%(name)-6s] %(message)s")
  
  if len(sys.argv) > 1 and sys.argv[1] == "--download":
    download_eddb_files(default_systems_file, default_stations_file)
  
  syresult = check_systems(default_systems_file)
  if syresult != False:
    log.info("Systems file exists and loads OK ({0} systems)".format(syresult))
  else:
    log.error("!! Systems file does not exist or could not be loaded")
  stresult = check_stations(default_stations_file)
  if stresult != False:
    log.info("Stations file exists and loads OK ({0} stations)".format(stresult))
  else:
    log.error("!! Stations file does not exist or could not be loaded")
  
