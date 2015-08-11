from __future__ import print_function
import io
import json
import os
import sys
import urllib

eddb_systems_url = "http://eddb.io/archive/v3/systems.json"
eddb_stations_url = "http://eddb.io/archive/v3/stations_lite.json"

eddb_systems_file_size_limit = 100 * 1048576
eddb_stations_file_size_limit = 500 * 1048576

def download_eddb_files(sys_file, station_file):
  # If the systems.json's directory doesn't exist, make it
  if not os.path.exists(os.path.dirname(sys_file)):
    os.makedirs(os.path.dirname(sys_file))
  # If the stations.json's directory doesn't exist, make it
  if not os.path.exists(os.path.dirname(station_file)):
    os.makedirs(os.path.dirname(station_file))

  # Download the systems.json
  print("-- Downloading EDDB Systems list from {0} ... ".format(eddb_systems_url), end="")
  sys.stdout.flush()
  urllib.urlretrieve(eddb_systems_url, sys_file)
  print("done.")
  print("-- Downloading EDDB Stations list from {0} ... ".format(eddb_stations_url), end="")
  sys.stdout.flush()
  urllib.urlretrieve(eddb_stations_url, station_file)
  print("done.")
  print("")


def load_systems(filename):
  eddb_systems_file = io.open(filename, "r")
  return json.loads(eddb_systems_file.read(eddb_systems_file_size_limit))

def load_stations(filename):
  eddb_stations_file = io.open(filename, "r")
  return json.loads(eddb_stations_file.read(eddb_stations_file_size_limit))
