import argparse
import logging
import os
import sys
import threading
import time
import util
import db
from system import System, KnownSystem
from station import Station

logging.basicConfig(level = logging.INFO, format="[%(asctime)-15s] [%(name)-6s] %(message)s")
log = logging.getLogger("env")


class Env(object):
  def __init__(self, path = '.'):
    self.is_data_loaded = False
    self._db_conn = None
    self._data_path = os.path.normpath(path)

    if not os.path.isfile(os.path.join(self._data_path, os.path.normpath(global_args.db_file))):
      log.error("Error: EDDB/Coriolis data not found. Please run update.py to download this data and create the local database.")
      return

    self._load_lock = threading.RLock()
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

  def _make_known_system(self, s, keep_data=False):
    sysobj = KnownSystem(s)
    if keep_data:
      sysobj.data = s.copy()
    return sysobj

  def _make_station(self, sy, st, keep_data=False):
    sysobj = self._make_known_system(sy, keep_data) if not isinstance(sy, KnownSystem) else sy
    stnobj = Station(st, sysobj)
    if keep_data:
      stnobj.data = st
    return stnobj

  def get_station(self, sysname, statname = None, keep_data=False):
    if statname is not None:
      (sysdata, stndata) = self._db_conn.get_station_by_names(sysname, statname)
      if sysdata is not None and stndata is not None:
        return self._make_station(sysdata, stndata, keep_data)
    else:
      sys = self.get_system(sysname, keep_data)
      if sys is not None:
        return Station.none(sys)
    return None

  def get_stations(self, sysobj, keep_station_data=False):
    if hasattr(sysobj, 'id') and sysobj.id is not None:
      return [self._make_station(sysobj, stndata, keep_data=keep_station_data) for stndata in self._db_conn.get_stations_by_system_id(sysobj.id)]
    else:
      return []

  def get_system(self, sysname, keep_data=False):
    # Check the input against the "fake" system format of "[123.4,56.7,-89.0]"...
    coords_data = util.parse_coords(sysname)
    if coords_data is not None:
      cx, cy, cz, name = coords_data
      return System(cx, cy, cz, name)
    else:
      result = self._db_conn.get_system_by_name(sysname)
      if result is not None:
        return self._make_known_system(result, keep_data)
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
 
  def get_all_systems(self, keep_data=False):
    for s in self._db_conn.get_all_systems():
      yield self._make_known_system(s, keep_data)

  def get_all_stations(self, keep_data=False):
    for st,sy in self._db_conn.get_all_stations():
      yield self._make_station(sy, st, keep_data)

  def find_systems_by_glob(self, name, keep_data=False):
    for s in self._db_conn.find_systems_by_name_unsafe(name, mode=db.FIND_GLOB):
      yield self._make_known_system(s, keep_data)

  def find_systems_by_regex(self, name, keep_data=False):
    for s in self._db_conn.find_systems_by_name_unsafe(name, mode=db.FIND_REGEX):
      yield self._make_known_system(s, keep_data)

  def find_stations_by_glob(self, name, keep_data=False):
    for (sy, st) in self._db_conn.find_stations_by_name_unsafe(name, mode=db.FIND_GLOB):
      yield self._make_station(sy, st, keep_data)

  def find_stations_by_regex(self, name, keep_data=False):
    for (sy, st) in self._db_conn.find_stations_by_name_unsafe(name, mode=db.FIND_REGEX):
      yield self._make_station(sy, st, keep_data)

  def find_systems_close_to(self, refs, keep_data=False):
    for s in self._db_conn.find_systems_close_to(refs):
      yield self._make_known_system(s, keep_data)

  def _load_data(self):
    with self._load_lock:
      try:
        self._db_conn = db.open_db(os.path.join(self._data_path, os.path.normpath(global_args.db_file)))
        self._load_coriolis_data()
        self.is_data_loaded = True
        log.debug("Data loaded")
      except Exception as ex:
        self.is_data_loaded = False
        log.error("Failed to open database: {}".format(ex))

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

  @property
  def coriolis_fsd_list(self):
    self._ensure_data_loaded()
    return self._coriolis_fsd_list


data = None


def start(path = '.'):
  global data
  if data is None or not data.is_data_loaded:
    newdata = Env(path)
    if newdata.is_data_loaded:
      data = newdata


def is_started():
  global data
  return (data is not None and data.is_data_loaded)


def stop():
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

# Only try to parse args/set verbosity in non-interactive mode
if not util.is_interactive():
  set_verbosity(global_args.verbose)
