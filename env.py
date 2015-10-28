import argparse
import os
import sys
import eddb
import coriolis

arg_parser = argparse.ArgumentParser(description = "Elite: Dangerous Tools", fromfile_prefix_chars="@", add_help=False)
arg_parser.add_argument("--eddb-systems-file", type=str, default=eddb.default_systems_file, help="Path to EDDB systems.json")
arg_parser.add_argument("--eddb-stations-file", type=str, default=eddb.default_stations_file, help="Path to EDDB stations.json")
arg_parser.add_argument("--coriolis-fsd-file", type=str, default=coriolis.default_frame_shift_drive_file, help="Path to Coriolis frame_shift_drive.json")
global_args, unknown_args = arg_parser.parse_known_args(sys.argv[1:])

if not os.path.isfile(global_args.eddb_systems_file) or not os.path.isfile(global_args.eddb_stations_file):
  log.error("Error: EDDB system/station files not found. Run the eddb.py script with the --download flag to auto-download these.")
  sys.exit(1)

if not os.path.isfile(global_args.coriolis_fsd_file):
  log.error("Error: Coriolis FSD file not found. Run the coriolis.py script with the --download flag to auto-download this.")
  sys.exit(1)

eddb_systems = eddb.load_systems(global_args.eddb_systems_file)
eddb_stations = eddb.load_stations(global_args.eddb_stations_file)
coriolis_fsd_list = coriolis.load_frame_shift_drives(global_args.coriolis_fsd_file)

