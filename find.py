#!/usr/bin/env python

from __future__ import print_function
import argparse
from edtslib.cow import ColumnObjectWriter
from edtslib import env
from edtslib import find

def parse_args(arg, hosted, state):
  ap_parents = [env.arg_parser] if not hosted else []
  ap = argparse.ArgumentParser(description = "Find System or Station", fromfile_prefix_chars="@", parents=ap_parents, prog = find.app_name)
  ap.add_argument("-s", "--systems", default=False, action='store_true', help="Limit the search to system names")
  ap.add_argument("-t", "--stations", default=False, action='store_true', help="Limit the search to station names")
  ap.add_argument("-i", "--show-ids", default=False, action='store_true', help="Show system and station IDs in output")
  ap.add_argument("-l", "--list-stations", default=False, action='store_true', help="List stations in returned systems")
  ap.add_argument("-r", "--regex", default=False, action='store_true', help="Takes input as a regex rather than a glob")
  ap.add_argument("--id64", required=False, type=str.upper, choices=['INT', 'HEX', 'VSC'], help="Show system ID64 in output")
  ap.add_argument("--filters", required=False, metavar='filter', nargs='*')
  ap.add_argument("pattern", metavar="system/station", type=str, nargs='?', help="The system or station to find")
  return ap.parse_args(arg)

def run(args, hosted = False, state = {}):
  parsed = parse_args(args, hosted, state)
  indent = 8

  stn_matches = []
  sys_matches = []

  for entry in find.Application(**vars(parsed)).run():
    if entry.station is not None:
      stn_matches.append(entry)
    elif entry.system is not None:
      sys_matches.append(entry)

  if len(sys_matches) > 0:
    print("")
    print("Matching systems:")
    print("")
    cow = ColumnObjectWriter(3, ['<', '>', '<'])
    for entry in sorted(sys_matches, key=lambda t: t.system.name):
      if parsed.show_ids or parsed.id64:
        id = " ({})".format(entry.system.pretty_id64(parsed.id64) if parsed.id64 else entry.system.id)
      else:
        id = ""
      cow.add([
        '{}{}'.format(entry.system.name, id),
        '',
        entry.system.arrival_star.to_string(True)
      ])

      for stn in entry.stations:
        cow.add([
          '{}{}'.format(' ' * indent, stn.name),
          '({})'.format(stn.distance.to_string() if stn.distance is not None else '???'),
          stn.station_type if stn.station_type is not None else '???'
        ])
    cow.out()
    print("")

  if len(stn_matches) > 0:
    print("")
    print("Matching stations:")
    print("")
    cow = ColumnObjectWriter(5, ['<', '<', '<', '>', '<'], ['  ', '   '])
    for entry in sorted(stn_matches, key=lambda t: t.station.name):
      if parsed.show_ids or parsed.id64:
        id = " ({})".format(entry.station.id)
      else:
        id = ""
      cow.add([
        '',
        entry.station.system.name,
        '{}{}'.format(entry.station.name, id),
        entry.station.distance.to_string() if entry.station.distance is not None else '???',
        entry.station.station_type if entry.station.station_type is not None else '???'
      ])
    cow.out()
    print("")

  if len(sys_matches) == 0 and len(stn_matches) == 0:
    print("")
    print("No matches")
    print("")

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  env.start()
  run(env.local_args)
  env.stop()
