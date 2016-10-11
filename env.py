import logging
logging.basicConfig(level = logging.INFO, format="[%(asctime)-15s] [%(name)-6s] %(message)s")

import argparse
import collections
import defs
import logging
import os
import sys
import threading
import time
import util
import system_internal as system
import station
import db_sqlite3

log = logging.getLogger("env")

default_path = '.'
default_backend_name = 'db_sqlite3'

def _make_known_system(s, keep_data=False):
  sysobj = system.KnownSystem(s)
  if keep_data:
    sysobj.data = s.copy()
  return sysobj

def _make_station(sy, st, keep_data = False):
  sysobj = _make_known_system(sy, keep_data) if not isinstance(sy, system.KnownSystem) else sy
  stnobj = station.Station(st, sysobj)
  if keep_data:
    stnobj.data = st
  return stnobj


_registered_backends = {}

def register_backend(name, fn):
  _registered_backends[name] = fn

def unregister_backend(name):
  del _registered_backends[name]

def _get_default_backend(path):
  db_path = os.path.join(os.path.normpath(path), os.path.normpath(global_args.db_file))
  if not os.path.isfile(db_path):
    log.error("Error: EDDB/Coriolis data not found. Please run update.py to download this data and create the local database.")
    return None
  return db_sqlite3.open_db(db_path)

register_backend(default_backend_name, _get_default_backend)



class Env(object):
  def __init__(self, backend):
    self.is_data_loaded = False
    self._backend = backend
    self._load_data()

  def close(self):
    if self._backend is not None:
      self._backend.close()

  @property
  def backend_name(self):
    return (self._backend.backend_name if self._backend else None)

  def parse_station(self, statstr):
    parts = statstr.split("/", 1)
    sysname = parts[0]
    statname = parts[1] if len(parts) > 1 else None
    return self.get_station(sysname, statname)

  def parse_system(self, sysstr):
    return self.get_system(sysstr)

  def get_station(self, sysname, statname = None, keep_data = False):
    if statname is not None:
      (sysdata, stndata) = self._backend.get_station_by_names(sysname, statname)
      if sysdata is not None and stndata is not None:
        return _make_station(sysdata, stndata, keep_data)
    else:
      sys = self.get_system(sysname, keep_data)
      if sys is not None:
        return station.Station.none(sys)
    return None

  def get_system(self, sysname, keep_data = False):
    # Check the input against the "fake" system format of "[123.4,56.7,-89.0]"...
    coords_data = util.parse_coords(sysname)
    if coords_data is not None:
      cx, cy, cz, name = coords_data
      return system.System(cx, cy, cz, name)
    else:
      result = self._backend.get_system_by_name(sysname)
      if result is not None:
        return _make_known_system(result, keep_data)
      else:
        return None

  def find_stations(self, args, filters = None, keep_station_data = False):
    sysobjs = args if isinstance(args, collections.Iterable) else [args]
    sysobjs = { s.id: s for s in sysobjs if s.id is not None }
    return [_make_station(sysobjs[stndata['eddb_system_id']], stndata, keep_data=keep_station_data) for stndata in self._backend.find_stations_by_system_id(list(sysobjs.keys()), filters=filters)]

  def find_systems_by_aabb(self, vec_from, vec_to, buffer_from = 0.0, buffer_to = 0.0, filters = None):
    min_x = min(vec_from.x, vec_to.x) - buffer_from
    min_y = min(vec_from.y, vec_to.y) - buffer_from
    min_z = min(vec_from.z, vec_to.z) - buffer_from
    max_x = max(vec_from.x, vec_to.x) + buffer_to
    max_y = max(vec_from.y, vec_to.y) + buffer_to
    max_z = max(vec_from.z, vec_to.z) + buffer_to
    return [KnownSystem(s) for s in self._backend.find_systems_by_aabb(min_x, min_y, min_z, max_x, max_y, max_z, filters=filters)]
 
  def find_all_systems(self, filters = None, keep_data = False):
    for s in self._backend.find_all_systems(filters=filters):
      yield _make_known_system(s, keep_data=keep_data)

  def find_all_stations(self, filters = None, keep_data = False):
    for sy,st in self._backend.find_all_stations(filters=filters):
      yield _make_station(sy, st, keep_data=keep_data)

  def find_systems_by_glob(self, name, filters = None, keep_data=False):
    for s in self._backend.find_systems_by_name_unsafe(name, mode=db.FIND_GLOB, filters=filters):
      yield _make_known_system(s, keep_data)

  def find_systems_by_regex(self, name, filters = None, keep_data=False):
    for s in self._backend.find_systems_by_name_unsafe(name, mode=db.FIND_REGEX, filters=filters):
      yield _make_known_system(s, keep_data)

  def find_stations_by_glob(self, name, filters = None, keep_data=False):
    for (sy, st) in self._backend.find_stations_by_name_unsafe(name, mode=db.FIND_GLOB, filters=filters):
      yield _make_station(sy, st, keep_data)

  def find_stations_by_regex(self, name, filters = None, keep_data=False):
    for (sy, st) in self._backend.find_stations_by_name_unsafe(name, mode=db.FIND_REGEX, filters=filters):
      yield _make_station(sy, st, keep_data)

  def _load_data(self):
    try:
      self._load_coriolis_data()
      self.is_data_loaded = True
      log.debug("Data loaded")
    except Exception as ex:
      self.is_data_loaded = False
      log.error("Failed to load environment data: {}".format(ex))

  def _load_coriolis_data(self):
    self._coriolis_fsd_list = self._backend.retrieve_fsd_list()
    self.is_coriolis_data_loaded = True
    log.debug("Coriolis data loaded")

  @property
  def coriolis_fsd_list(self):
    return self._coriolis_fsd_list


class EnvWrapper(object):
  def __init__(self, path = default_path, backend = default_backend_name):
    self._backend = backend
    self._path = path

  def __enter__(self):
    self._close_env = False
    if not is_started(self._path, self._backend):
      start(self._path, self._backend)
      self._close_env = True
    if is_started(self._path, self._backend):
      return _open_backends[(self._backend, self._path)]
    else:
      raise RuntimeError("Failed to load environment")

  def __exit__(self, typ, value, traceback):
    if self._close_env:
      stop(self._path, self._backend)



_open_backends = {}

def start(path = default_path, backend = default_backend_name):
  if backend not in _registered_backends:
    raise ValueError("Specified backend name '{}' is not registered".format(backend))
  if not is_started(path, backend):
    backend_obj = _registered_backends[backend](path)
    if backend_obj is None:
      log.error("Failed to start environment: backend name '{}' failed to create object".format(backend))
      return False
    newdata = Env(backend_obj)
    if newdata.is_data_loaded:
      _open_backends[(backend, path)] = newdata
      return True
    else:
      return False
  else:
    return True


def is_started(path = default_path, backend = default_backend_name):
  return ((backend, path) in _open_backends and _open_backends[(backend, path)].is_data_loaded)


def stop(path = default_path, backend = default_backend_name):
  if (backend, path) in _open_backends:
    _open_backends[(backend, path)].close()
    del _open_backends[(backend, path)]
  return True


def use(path = default_path, backend = default_backend_name):
  return EnvWrapper(path, backend)


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
arg_parser.add_argument("--db-file", type=str, default=defs.default_db_file, help="Specifies the database file to use")
global_args, local_args = arg_parser.parse_known_args(sys.argv[1:])    

# Only try to parse args/set verbosity in non-interactive mode
if not util.is_interactive():
  set_verbosity(global_args.verbose)
