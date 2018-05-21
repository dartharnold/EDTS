#!/usr/bin/env python

from __future__ import print_function
import argparse
import sys
from edtslib import direction
from edtslib import env
from edtslib import util

def parse_args(arg, hosted, state):
  ap_parents = [env.arg_parser] if not hosted else []
  ap = argparse.ArgumentParser(description = "Calculate direction between two systems", fromfile_prefix_chars="@", parents = ap_parents, prog = direction.app_name)
  ap.add_argument("-a", "--angle", default=False, action='store_true', help="Return angle not vector")
  ap.add_argument("-c", "--check", default=False, action='store_true', help="Check if second system is in the same direction as the first from the reference")
  ap.add_argument("-n", "--normal", default=False, action='store_true', help="Return normalised direction vector")
  ap.add_argument("-r", "--reference", metavar="system", nargs='?', default=direction.default_reference, help="Reference system for angle calculation")
  ap.add_argument("-t", "--tolerance", type=float, default=direction.default_tolerance, help="Tolerance in percent for --check")
  ap.add_argument("systems", metavar="system", nargs=2, help="Systems")

  return ap.parse_args(arg)

def run(args, hosted = False, state = {}):
  parsed = parse_args(args, hosted, state)
  results = direction.Application(**vars(parsed)).run()
  if env.global_args.json:
    print(util.to_json(list(results)))
    return
  for entry in results:
    if parsed.check:
      if entry.check:
        print('OK {:0.2f}% deviation'.format(entry.deviation))
        sys.exit(0)
      elif entry.opposite:
        print('NO opposite')
      else:
        print('NO {:0.2f}% deviation'.format(entry.deviation))
      sys.exit(100)
    else:
      if entry.angle is not None:
        print(entry.angle)
      else:
        print(entry.direction)

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  env.start()
  run(env.local_args)
  env.stop()
