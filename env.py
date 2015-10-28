import argparse
import logging
import os
import sys
import eddb
import coriolis
from itertools import izip

def get_stations_by_system(stations):
  sbs = {}
  for st in stations:
    sid = st["system_id"]
    if not sid in sbs:
      sbs[sid] = []
    sbs[sid].append(st)
  return sbs

def get_systems_by_name(stations):
  return {el['name'].lower() : el for el in stations}

logging.basicConfig(level = logging.INFO, format="[%(asctime)-15s] [%(name)-6s] %(message)s")

arg_parser = argparse.ArgumentParser(description = "Elite: Dangerous Tools", fromfile_prefix_chars="@", add_help=False)
arg_parser.add_argument("-v", "--verbose", type=int, default=1, help="Increases the logging output")
arg_parser.add_argument("--eddb-systems-file", type=str, default=eddb.default_systems_file, help="Path to EDDB systems.json")
arg_parser.add_argument("--eddb-stations-file", type=str, default=eddb.default_stations_file, help="Path to EDDB stations.json")
arg_parser.add_argument("--coriolis-fsd-file", type=str, default=coriolis.default_frame_shift_drive_file, help="Path to Coriolis frame_shift_drive.json")
global_args, unknown_args = arg_parser.parse_known_args(sys.argv[1:])

if global_args.verbose > 1:
  logging.getLogger().setLevel(logging.DEBUG)

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
eddb_systems_by_name = get_systems_by_name(eddb_systems)
