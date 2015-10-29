import argparse
import env
import logging
import os
import sys
from vector3 import Vector3

log = logging.getLogger("distance")


class Application:

  def __init__(self, arg):
    ap = argparse.ArgumentParser(description = "Calculate Distance Between Systems", fromfile_prefix_chars="@", parents=[env.arg_parser])
    ap.add_argument("system", metavar="start end", type=str, nargs=2, help="The systems to find the distance between")
    self.args = ap.parse_args(arg)

  def run(self):

    start = env.get_station_from_string(self.args.system[0].lower())
    end = env.get_station_from_string(self.args.system[1].lower())
    
    if start == None:
      log.error("Could not find start system \"{0}\"!".format(self.args.system[0]))
      return
    if end == None:
      log.error("Could not find end system \"{0}\"!".format(self.args.system[1]))
      return

    
    print ""
    print start.to_string()
    print "    === {0: >6.2f}Ly ===> {1}".format((end.position - start.position).length, end.to_string())
    print ""

if __name__ == '__main__':
  a = Application(sys.argv[1:])
  a.run()

