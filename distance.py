#!/usr/bin/env python

from __future__ import print_function
import argparse
from edtslib.cow import ColumnObjectWriter
from edtslib.dist import Lightyears
from edtslib import distance
from edtslib import env

def parse_args(arg, hosted, state):
  ap_parents = [env.arg_parser] if not hosted else []
  ap = argparse.ArgumentParser(description = "Plot jump distance matrix", fromfile_prefix_chars="@", parents = ap_parents, prog = distance.app_name)
  ap.add_argument("-c", "--csv", action='store_true', default=False, help="Output in CSV")
  ap.add_argument("-o", "--ordered", action='store_true', default=False, help="List is ordered (do not sort alphabetically)")
  ap.add_argument("-f", "--full-width", action='store_true', default=False, help="Do not truncate heading names for readability")
  ap.add_argument("-s", "--start", type=str, required=False, help="Defines a start system to calculate all other distances from")
  ap.add_argument("-r", "--route", action='store_true', default=False, help="List of systems is a sequential list to visit and get distances between")
  ap.add_argument("systems", metavar="systems", nargs='+', help="Systems")

  return ap.parse_args(arg)

def run(args, hosted = False, state = {}):
  parsed = parse_args(args, hosted, state)
  cow = ColumnObjectWriter()
  raikogram_mode = False
  last_origin = None
  if parsed.route:
    # Route mode.
    cow.expand(4, ['<', '>', '<', '<'], ['   ', ' ', ' ', '   '])
  elif parsed.start is not None:
    # Reference mode.
    cow.expand(6, ['<', '<', '>', '>', '<'], ['   ', ' '])
  else:
    # Raikogram.
    raikogram_mode = True
    header = ['']
    row = []
    total = 0.0
    shown_header = False
    cow.expand(len(parsed.systems) + (1 if not parsed.csv else 0), ['>'], [',' if parsed.csv else '   '])

  for entry in distance.Application(**vars(parsed)).run():
    if raikogram_mode:
      if entry.origin.system != last_origin:
        if len(row):
          if not shown_header:
            if parsed.csv:
              print(','.join(header))
            else:
              cow.add(header)
            shown_header = True
          if parsed.csv:
            print(','.join(row))
          else:
            cow.add(row)
        row = [entry.origin.system]
        total += entry.distance.lightyears
      if not shown_header:
        header.append(entry.destination.system)
      row.append(entry.distance.to_string(parsed.full_width) if entry.origin.system != entry.destination.system else '-')
    elif parsed.route:
      if last_origin is None:
        cow.add([
          '', # Padding
          '', # Distance
          '', # >
          entry.origin.system.to_string(),
          '', # Extra
        ])
      cow.add([
        '',
        entry.distance.to_string(parsed.full_width),
        '>',
        entry.destination.system.to_string(),
        '+/- {}'.format(Lightyears(entry.origin.system.uncertainty3d + entry.destination.system.uncertainty3d).to_string(parsed.full_width)) if entry.origin.system.uncertainty3d != 0.0 or entry.destination.system.uncertainty3d != 0.0 else ''
      ])
    else:
      cow.add([
        '', # Padding
        entry.origin.system.to_string(),
        '>',
        entry.distance.to_string(parsed.full_width),
        '>',
        entry.destination.system.to_string(),
        '+/- {}'.format(Lightyears(entry.origin.system.uncertainty3d + entry.destination.system.uncertainty3d).to_string(parsed.full_width)) if entry.origin.system.uncertainty3d != 0.0 or entry.destination.system.uncertainty3d != 0.0 else ''
      ])
    last_origin = entry.origin.system

  if raikogram_mode:
    if parsed.csv:
      print(','.join(row))
    else:
      cow.add(row)
    if parsed.ordered:
      row = ['Total:', Lightyears(total).to_string(parsed.full_width)]
      if parsed.csv:
        print(','.join(row))
      else:
        cow.add([])
        cow.add(row)

  print('')
  cow.out()
  print('')

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  env.start()
  run(env.local_args)
  env.stop()
