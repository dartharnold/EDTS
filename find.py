import argparse
import env
import fnmatch
import logging
import os
import sys
from vector3 import Vector3

log = logging.getLogger("find")


class Application:

  def __init__(self, arg):
    ap = argparse.ArgumentParser(description = "Find System or Station", fromfile_prefix_chars="@", parents=[env.arg_parser])
    ap.add_argument("system", metavar="system", type=str, nargs=1, help="The system or station to find")
    self.args = ap.parse_args(arg)

  def run(self):

    searchname = self.args.system[0].lower()

    sys_matches = fnmatch.filter(env.eddb_systems_by_name.keys(), searchname)
    stn_matches = fnmatch.filter(env.eddb_stations_by_name.keys(), searchname)

    if len(sys_matches) > 0:
      print ""
      print "Matching systems:"
      print ""
      for sys in sys_matches:
        stn = env.get_station(sys, None, True)
        print "  " + stn.to_string()
      print ""

    if len(stn_matches) > 0:
      print ""
      print "Matching stations:"
      print ""
      for stn_name in stn_matches:
        stns = env.eddb_stations_by_name[stn_name]
        for stn in stns:
          stn_obj = env.get_station(env.eddb_systems_by_id[stn["system_id"]]["name"], stn["name"], True)
          print "  " + stn_obj.to_string()
      print ""

    if len(sys_matches) == 0 and len(stn_matches) == 0:
      print ""
      print "No matches"
      print ""

    return True


if __name__ == '__main__':
  a = Application(sys.argv[1:])
  a.run()

