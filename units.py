#!/usr/bin/env python

from __future__ import print_function
import argparse
from edtslib import env
from edtslib import units
from edtslib.dist import *

class CaseInsensitiveList(list):
  def __init__(self, elements):
    super(CaseInsensitiveList, self).__init__([element.lower() for element in elements])

  def __contains__(self, other):
    return super(CaseInsensitiveList, self).__contains__(other.lower())

def parse_args(arg, hosted, state):
  choices = CaseInsensitiveList(Dist.SUFFICES)
  ap_parents = [env.arg_parser] if not hosted else []
  ap = argparse.ArgumentParser(description = "Convert distance scales", fromfile_prefix_chars="@", parents=ap_parents, prog = units.app_name)
  ap.add_argument("-s", "--short", default=False, action='store_true', help="Restrict number of significant figures")
  ap.add_argument("distance", metavar="distance", type=str, help="Distance to convert")
  ap.add_argument("suffix", metavar="from_scale", type=str, nargs='?', choices=choices, help="Source scale")
  ap.add_argument("result", metavar="scale", type=str, choices=choices, help="Resultant scale")
  return ap.parse_args(arg)

def run(args, hosted = False, state = {}):
  parsed = parse_args(args, hosted, state)
  for entry in units.Application(**vars(parsed)).run():
    print("")
    print(entry.distance.to_string(long = not parsed.short))
    print("")

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  run(env.local_args)
