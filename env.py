import argparse
import logging
import os
import sys
import threading
import eddb
import coriolis
from system import System
from station import Station

logging.basicConfig(level = logging.INFO, format="[%(asctime)-15s] [%(name)-6s] %(message)s")
log = logging.getLogger("env")

class Env(object):
  def __init__(self):
    self._coriolis_load_lock = threading.RLock()
    self._eddb_load_lock = threading.RLock()
    
    self.is_coriolis_data_loaded = False
    self.is_eddb_data_loaded = False
    
    self.load_coriolis_data(False)
    self.load_eddb_data(True)

  def _get_stations_by_system(self, stations):
    sbs = {}
    for st in stations:
      sid = st.system.id
      if not sid in sbs:
        sbs[sid] = []
      sbs[sid].append(st)
    return sbs
  
  def _get_systems_by_id(self, systems):
    return {el.id : el for el in systems}
  
  def _get_systems_by_name(self, systems):
    return {el.name.lower() : el for el in systems}
  
  def _get_stations_by_name(self, stations):
    sbn = {}
    for st in stations:
      name = st.name.lower()
      if not name in sbn:
        sbn[name] = []
      sbn[name].append(st)
    return sbn
  
  def get_station_from_string(self, statstr):
    parts = statstr.split("/", 1)
    sysname = parts[0]
    statname = parts[1] if len(parts) > 1 else None
    return self.get_station(sysname, statname)
  
  def get_station(self, sysname, statname = None):
    if statname is not None and statname.lower() in self.eddb_stations_by_name:
      for stn in self.eddb_stations_by_name[statname.lower()]:
        if sysname.lower() == stn.system.name.lower():
          return stn
    else:
      if sysname.lower() in self.eddb_systems_by_name:
        return Station.none(self.eddb_systems_by_name[sysname.lower()])
    return None
  
  def _load_eddb_data(self):
    with self._eddb_load_lock:
      self._eddb_systems = [System(s) for s in eddb.load_systems(global_args.eddb_systems_file)]
      self._eddb_systems_by_id = self._get_systems_by_id(self._eddb_systems)
      self._eddb_systems_by_name = self._get_systems_by_name(self._eddb_systems)
      
      self._eddb_stations = [Station(t, self._eddb_systems_by_id[t["system_id"]]) for t in eddb.load_stations(global_args.eddb_stations_file)]
      self._eddb_stations_by_name = self._get_stations_by_name(self._eddb_stations)
      self._eddb_stations_by_system = self._get_stations_by_system(self._eddb_stations)

      self.is_eddb_data_loaded = True
      log.debug("EDDB data loaded")
  
  def load_eddb_data(self, async):
    if async:
      self._eddb_load_thread = threading.Thread(name = "eddb_load", target = self._load_eddb_data)
      self._eddb_load_thread.start()
    else:
      self._load_eddb_data()
      
  def _load_coriolis_data(self):
    with self._coriolis_load_lock:
      self._coriolis_fsd_list = coriolis.load_frame_shift_drives(global_args.coriolis_fsd_file)
      self.is_coriolis_data_loaded = True
      log.debug("Coriolis data loaded")
    
  def load_coriolis_data(self, async):
    if async:
      self._coriolis_load_thread = threading.Thread(name = "coriolis_load", target = self._load_coriolis_data)
      self._coriolis_load_thread.start()
    else:
      self._load_coriolis_data()
  
  def _ensure_eddb_data_loaded(self):
    if not self.is_eddb_data_loaded:
      log.debug("Waiting for EDDB data to be loaded...")
      self._eddb_load_lock.acquire()
      self._eddb_load_lock.release()
      log.debug("Finished waiting")
  
  def _ensure_coriolis_data_loaded(self):
    if not self.is_coriolis_data_loaded:
      log.debug("Waiting for Coriolis data to be loaded...")
      self._coriolis_load_lock.acquire()
      self._coriolis_load_lock.release()
      log.debug("Finished waiting")
  
  #
  # Public EDDB properties
  #
  @property
  def eddb_systems(self):
    self._ensure_eddb_data_loaded()
    return self._eddb_systems
  
  @property
  def eddb_stations(self):
    self._ensure_eddb_data_loaded()
    return self._eddb_stations
    
  @property
  def eddb_stations_by_system(self):
    self._ensure_eddb_data_loaded()
    return self._eddb_stations_by_system
    
  @property
  def eddb_systems_by_id(self):
    self._ensure_eddb_data_loaded()
    return self._eddb_systems_by_id
    
  @property
  def eddb_systems_by_name(self):
    self._ensure_eddb_data_loaded()
    return self._eddb_systems_by_name
    
  @property
  def eddb_stations_by_name(self):
    self._ensure_eddb_data_loaded()
    return self._eddb_stations_by_name
    
  #
  # Public Coriolis properties
  #
  @property
  def coriolis_fsd_list(self):
    self._ensure_coriolis_data_loaded()
    return self._coriolis_fsd_list



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
arg_parser.add_argument("--eddb-systems-file", type=str, default=eddb.default_systems_file, help="Path to EDDB systems.json")
arg_parser.add_argument("--eddb-stations-file", type=str, default=eddb.default_stations_file, help="Path to EDDB stations.json")
arg_parser.add_argument("--coriolis-fsd-file", type=str, default=coriolis.default_frame_shift_drive_file, help="Path to Coriolis frame_shift_drive.json")
global_args, local_args = arg_parser.parse_known_args(sys.argv[1:])

set_verbosity(global_args.verbose)

if not os.path.isfile(global_args.eddb_systems_file) or not os.path.isfile(global_args.eddb_stations_file):
  log.error("Error: EDDB system/station files not found. Run the eddb.py script with the --download flag to auto-download these.")
  sys.exit(1)

if not os.path.isfile(global_args.coriolis_fsd_file):
  log.error("Error: Coriolis FSD file not found. Run the coriolis.py script with the --download flag to auto-download this.")
  sys.exit(1)

# Create the object
data = Env()
