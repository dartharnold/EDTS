#!/usr/bin/env python

from __future__ import print_function
import argparse
from edtslib.cow import ColumnObjectWriter
from edtslib.dist import Lightseconds, Lightyears
from edtslib import close_to
from edtslib import env

class ApplicationAction(argparse.Action):
  def __call__(self, parser, namespace, value, option_strings=None):
    n = vars(namespace)
    system_list = n['systems'] if n['systems'] is not None else []
    need_new = True
    i = 0
    while i < len(system_list):
      if self.dest not in system_list[i]:
        need_new = False
        break
      i += 1
    if need_new:
      system_list.append({})
    d = system_list[i]
    if self.dest == 'systems':
      d['system'] = value[0]
    else:
      d[self.dest] = value
      setattr(namespace, self.dest, value)
    setattr(namespace, 'systems', system_list)

def parse_args(arg, hosted, state):
  ap_parents = [env.arg_parser] if not hosted else []
  ap = argparse.ArgumentParser(description = "Find Nearby Systems", fromfile_prefix_chars="@", parents = ap_parents, prog = close_to.app_name)
  ap.add_argument("-n", "--num", type=int, required=False, default=close_to.default_num, help="Show the specified number of nearby systems")
  ap.add_argument("-d", "--min-dist", type=float, required=False, action=ApplicationAction, help="Exclude systems less than this distance from reference")
  ap.add_argument("-m", "--max-dist", type=float, required=False, action=ApplicationAction, help="Exclude systems further this distance from reference")
  ap.add_argument("-S", "--arrival-star", type=str, required=False, help="Only show systems with arrival star of the given class(es)")
  ap.add_argument("-a", "--allegiance", type=str, required=False, default=None, help="Only show systems with the specified allegiance")
  ap.add_argument("-s", "--max-sc-distance", type=float, required=False, help="Only show systems with a starport less than this distance from entry point")
  ap.add_argument("-p", "--pad-size", required=False, type=str.upper, choices=['S','M','L'], help="Only show systems with stations matching the specified pad size")
  ap.add_argument("-l", "--list-stations", default=False, action='store_true', help="List stations in returned systems")
  ap.add_argument("--direction", type=str, required=False, help="A system or set of coordinates that returned systems must be in the same direction as")
  ap.add_argument("--direction-angle", type=float, required=False, default=close_to.default_max_angle, help="The maximum angle, in degrees, allowed for the direction check")

  ap.add_argument("systems", metavar="system", nargs=1, action=ApplicationAction, help="The system to find other systems near")

  parsed = None
  remaining = arg
  args = argparse.Namespace()
  while remaining:
    args, remaining = ap.parse_known_args(remaining, namespace=args)
    parsed = args
  if parsed is None:
    parsed = ap.parse_args(arg)
  return parsed

def run(args, hosted = False, state = {}):
  parsed = parse_args(args, hosted, state)
  results = list(close_to.Application(**vars(parsed)).run())
  if not len(results):
    print("")
    print("No matching systems")
    print("")
    return

  indent = 8
  cow = ColumnObjectWriter(3, ['<', '>', '<'])
  print("")
  print("Matching systems close to {0}:".format(', '.join([d["sysobj"].name for d in parsed.systems])))
  print("")
  for entry in results:
    cow.add([
      '    {}'.format(entry.system.name),
      '{} '.format(entry.distances[parsed.systems[0]['sysobj'].name].to_string(True)) if len(entry.distances) == 1 else '',
      entry.system.arrival_star.to_string(True)
    ])
    for stn in entry.stations:
      cow.add([
        '{}{}'.format(' ' * indent, stn.name),
        '({})'.format(str(Lightseconds(stn.distance)) if stn.distance is not None else '???'),
        stn.station_type if stn.station_type is not None else '???'
      ])
  cow.add(['', '', ''])
  if len(parsed.systems) > 1:
    for d in parsed.systems:
      cow.add(["  Distance from {0}:".format(d['system']), '', ''])
      cow.add(['', '', ''])
      results.sort(key=lambda t: t.distances[d['sysobj'].name])
      for entry in results:
        # Print distance from the current candidate system to the current start system
        cow.add([
          '    {}'.format(entry.system.name),
          '{} '.format(entry.distances[d['sysobj'].name].to_string(True)),
          entry.system.arrival_star.to_string(True)
        ])
      cow.add(['', '' ,''])
  cow.out()

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  env.start()
  run(env.local_args)
  env.stop()
