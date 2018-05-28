#!/usr/bin/env python

from __future__ import print_function
import argparse
from edtslib.cow import ColumnObjectWriter
from edtslib import coords
from edtslib import env
from edtslib import util

def parse_args(arg, hosted, state):
  ap_parents = [env.arg_parser] if not hosted else []
  ap = argparse.ArgumentParser(description = "Display System Coordinates", fromfile_prefix_chars="@", parents=ap_parents, prog = coords.app_name)
  ap.add_argument("-f", "--full-width", default=False, action='store_true', help="Do not restrict number of significant figures")
  ap.add_argument("systems", metavar="systems", type=str, nargs="*", help="The system(s) to print the coordinates for")

  return ap.parse_args(arg)

def run(args, hosted = False, state = {}):
  parsed = parse_args(args, hosted, state)
  results = coords.Application(**vars(parsed)).run()
  if env.global_args.json:
    print(util.to_json(list(results)))
    return
  fmt = '8g' if parsed.full_width else '8.2f'
  cow = ColumnObjectWriter(5, ['<', '>'], ['  ', ''])
  for entry in results:
    position = [('{:' + fmt + '}').format(coord) for coord in entry.system.position]
    cow.add([
      '',
      entry.system.name,
      ': [',
      position[0],
      ', ',
      position[1],
      ', ',
      position[2],
      ']',
      " +/- {0:.0f}LY in each axis".format(entry.system.uncertainty) if entry.system.uncertainty != 0.0 else ""
    ])
  print("")
  cow.out()
  print("")


if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  env.start()
  run(env.local_args)
  env.stop()
