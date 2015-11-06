import argparse
import logging
import os
import sys
import eddb
import coriolis
from system import System
from station import Station

logging.basicConfig(level = logging.INFO, format="[%(asctime)-15s] [%(name)-6s] %(message)s")
log = logging.getLogger("env")


def get_stations_by_system(stations):
  sbs = {}
  for st in stations:
    sid = st["system_id"]
    if not sid in sbs:
      sbs[sid] = []
    sbs[sid].append(st)
  return sbs

def get_systems_by_id(systems):
  return {el['id'] : el for el in systems}

def get_systems_by_name(systems):
  return {el['name'].lower() : el for el in systems}

def get_stations_by_name(stations):
  sbn = {}
  for st in stations:
    name = st["name"].lower()
    if not name in sbn:
      sbn[name] = []
    sbn[name].append(st)
  return sbn

def get_station_from_string(statstr):
  parts = statstr.split("/", 1)
  sysname = parts[0]
  statname = parts[1] if len(parts) > 1 else None

  return get_station(sysname, statname)

def get_station(sysname, statname = None, allow_none_distance = False):
  if sysname.lower() in eddb_systems_by_name:
    # Found system
    sy = eddb_systems_by_name[sysname.lower()]
    sysid = sy["id"]
    sysobj = System(sy["x"], sy["y"], sy["z"], sy["name"], bool(sy["needs_permit"]))

    if statname is None:
      return Station.none(sysobj)
    else:
      for st in eddb_stations_by_system[sysid]:
        if st["name"].lower() == statname.lower():
          # Found station
          stobj = Station(sysobj, st["distance_to_star"], st["name"], st["type"], bool(st["has_refuel"]), st["max_landing_pad_size"])
          
          if stobj.distance == None and not allow_none_distance:
            log.warning("Warning: station {0} ({1}) is missing SC distance in EDDB. Assuming 0.".format(stobj.name, stobj.system_name))
            stobj.distance = 0
          
          return stobj
  return None
  
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

eddb_systems = eddb.load_systems(global_args.eddb_systems_file)
eddb_stations = eddb.load_stations(global_args.eddb_stations_file)
coriolis_fsd_list = coriolis.load_frame_shift_drives(global_args.coriolis_fsd_file)

eddb_stations_by_system = get_stations_by_system(eddb_stations)
eddb_systems_by_id = get_systems_by_id(eddb_systems)
eddb_systems_by_name = get_systems_by_name(eddb_systems)
eddb_stations_by_name = get_stations_by_name(eddb_stations)
