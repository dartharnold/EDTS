import argparse
import json
import logging
import os
import re
import sys
import threading
import db
from system import System, KnownSystem
from station import Station

logging.basicConfig(level = logging.INFO, format="[%(asctime)-15s] [%(name)-6s] %(message)s")
log = logging.getLogger("env")


class Env(object):
  def __init__(self):
    # Match a float such as "33", "-33", "-33.1"
    rgx_float = r'[-+]?\d+(?:\.\d+)?'
    # Match a set of coords such as "[33, -45.6, 78.910]"
    rgx_coords = r'\[\s*({0})\s*,\s*({0})\s*,\s*({0})\s*\]'.format(rgx_float)
    # Compile the regex for faster execution later
    self._regex_coords = re.compile(rgx_coords)

    self._db_conn = None

    self._load_lock = threading.RLock()
    self.is_data_loaded = False
    self.load_data(False)

  def close(self):
    self._db_conn.close()

  def parse_station(self, statstr):
    parts = statstr.split("/", 1)
    sysname = parts[0]
    statname = parts[1] if len(parts) > 1 else None
    return self.get_station(sysname, statname)

  def parse_system(self, sysstr):
    return self.get_system(sysstr)

  def get_station(self, sysname, statname = None):
    if statname is not None:
      (sysdata, stndata) = self._db_conn.get_station_by_names(sysname, statname)
      if sysdata is not None and stndata is not None:
        return Station(stndata, KnownSystem(sysdata))
    else:
      sys = self.get_system(sysname)
      if sys is not None:
        return Station.none(sys)
    return None

  def get_stations(self, sysobj):
    return [Station(stndata, sysobj) for stndata in self._db_conn.get_stations_by_system_id(sysobj.id)]

  def get_system(self, sysname):
    # Check the input against the "fake" system format of "[123.4,56.7,-89.0]"...
    rx_match = self._regex_coords.match(sysname)
    if rx_match is not None:
      # If it matches, make a fake system and station at those coordinates
      try:
        cx = float(rx_match.group(1))
        cy = float(rx_match.group(2))
        cz = float(rx_match.group(3))
        return System(cx, cy, cz, sysname)
      except:
        pass
    else:
      result = self._db_conn.get_system_by_name(sysname)
      if result is not None:
        return KnownSystem(result)
      else:
        return None

  def get_systems_by_aabb(self, vec_from, vec_to, buffer_from, buffer_to):
    min_x = min(vec_from.x, vec_to.x) - buffer_from
    min_y = min(vec_from.y, vec_to.y) - buffer_from
    min_z = min(vec_from.z, vec_to.z) - buffer_from
    max_x = max(vec_from.x, vec_to.x) + buffer_to
    max_y = max(vec_from.y, vec_to.y) + buffer_to
    max_z = max(vec_from.z, vec_to.z) + buffer_to
    return [KnownSystem(s) for s in self._db_conn.get_systems_by_aabb(min_x, min_y, min_z, max_x, max_y, max_z)]

  def _load_data(self):
    with self._load_lock:
      self._db_conn = db.open_db()

      self._load_coriolis_data()

      self.is_data_loaded = True
      log.debug("Data loaded")

  def load_data(self, async):
    if async:
      self._load_thread = threading.Thread(name = "data_load", target = self._load_data)
      self._load_thread.start()
    else:
      self._load_data()

  def _load_coriolis_data(self):
    with self._load_lock:
      
      self._coriolis_fsd_list = self._db_conn.retrieve_fsd_list()
      self.is_coriolis_data_loaded = True
      log.debug("Coriolis data loaded")

  def _ensure_data_loaded(self):
    if not self.is_data_loaded:
      log.debug("Waiting for data to be loaded...")
      self._load_lock.acquire()
      self._load_lock.release()
      log.debug("Finished waiting")

  #
  # Public Coriolis properties
  #
  @property
  def coriolis_fsd_list(self):
    self._ensure_data_loaded()
    return self._coriolis_fsd_list


data = None


def open():
  global data
  if data is None:
    data = Env()


def close():
  global data
  data.close()
  data = None


def set_verbosity(level):
  if level >= 3:
    logging.getLogger().setLevel(logging.DEBUG)
  elif level >= 2:
    logging.getLogger().setLevel(logging.INFO)
  elif level >= 1:
    logging.getLogger().setLevel(logging.WARN)
  else:
    logging.getLogger().setLevel(logging.ERROR)


arg_parser = argparse.ArgumentParser(description = "Elite: Dangerous Tools", fromfile_prefix_chars="@", add_help=False)
arg_parser.add_argument("-v", "--verbose", type=int, default=1, help="Increases the logging output")
arg_parser.add_argument("--db-file", type=str, default=db.default_db_file, help="Specifies the database file to use")
global_args, local_args = arg_parser.parse_known_args(sys.argv[1:])

set_verbosity(global_args.verbose)

if not os.path.isfile(global_args.db_file):
  log.error("Error: EDDB/Coriolis data not found. Please run update.py to obtain these.")
  sys.exit(1)
