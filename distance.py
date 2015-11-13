#!/usr/bin/env python

from __future__ import print_function
import argparse
import env
import logging
from vector3 import Vector3

app_name = "distance"

log = logging.getLogger(app_name)


class Application:

  def __init__(self, arg, hosted):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Calculate Distance Between Systems", fromfile_prefix_chars="@", parents=ap_parents, prog = app_name)
    ap.add_argument("system", metavar="start end", type=str, nargs=2, help="The systems to find the distance between")
    self.args = ap.parse_args(arg)

  def run(self):

    start = env.data.get_station_from_string(self.args.system[0].lower())
    end = env.data.get_station_from_string(self.args.system[1].lower())
    
    if start == None:
      log.error("Could not find start system \"{0}\"!".format(self.args.system[0]))
      return
    if end == None:
      log.error("Could not find end system \"{0}\"!".format(self.args.system[1]))
      return

    
    print("")
    print(start.to_string())
    print("    === {0: >6.2f}Ly ===> {1}".format((end.position - start.position).length, end.to_string()))
    print("")

if __name__ == '__main__':
  a = Application(env.local_args, False)
  a.run()

