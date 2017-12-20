#!/usr/bin/env python

from __future__ import print_function
import argparse
from edtslib import env
from edtslib import galmath

def parse_args(arg, hosted, state):
  ap = argparse.ArgumentParser(description = "Magic Number plotting for the Galactic Core", fromfile_prefix_chars="@", prog = galmath.app_name)
  ap.add_argument("-j", "--jump-range", required=('ship' not in state), type=float, help="The full jump range of the ship")
  ap.add_argument("-c", "--core-distance", required=True, type=float, help="Current distance from the centre of the core (Sagittarius A*) in kLY")
  ap.add_argument("-d", "--distance", required=False, type=float, default=galmath.default_distance, help="The distance to travel")

  parsed = ap.parse_args(arg)

  if parsed.jump_range is None:
    if 'ship' in state:
      parsed.jump_range = state['ship'].range()
    else:
      raise Exception("Jump range not provided and no ship previously set")

  return parsed

def run(args, hosted = False, state = {}):
  for entry in galmath.Application(**vars(parse_args(args, hosted, state))).run():
    print("")
    print("Travelling {} with a {} jump range, at around {} from the core centre:".format(entry.distance.to_string(True), entry.jump_range.to_string(True), entry.core_distance.to_string(True)))
    print("")
    print("  Maximum jump in range: {}".format(entry.low_max_dist.to_string(True)))
    print("  Plot between {} and {}".format(entry.plot_min.to_string(True), entry.plot_max.to_string(True)))
    print("")


if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  run(env.local_args)
