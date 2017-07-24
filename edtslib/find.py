#!/usr/bin/env python

from __future__ import print_function
import argparse
import filtering
import fnmatch
import re
import sys

from . import env
from . import util

app_name = "find"

log = util.get_logger(app_name)


class Application(object):

  def __init__(self, arg, hosted, state = {}):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Find System or Station", fromfile_prefix_chars="@", parents=ap_parents, prog = app_name)
    ap.add_argument("-s", "--systems", default=False, action='store_true', help="Limit the search to system names")
    ap.add_argument("-t", "--stations", default=False, action='store_true', help="Limit the search to station names")
    ap.add_argument("-i", "--show-ids", default=False, action='store_true', help="Show system and station IDs in output")
    ap.add_argument("-l", "--list-stations", default=False, action='store_true', help="List stations in returned systems")
    ap.add_argument("-r", "--regex", default=False, action='store_true', help="Takes input as a regex rather than a glob")
    ap.add_argument("--id64", required=False, type=str.upper, choices=['INT', 'HEX', 'VSC'], help="Show system ID64 in output")
    ap.add_argument("--filters", required=False, metavar='filter', nargs='*')
    ap.add_argument("system", metavar="system", type=str, nargs='?', help="The system or station to find")
    self.args = ap.parse_args(arg)

    if self.args.system is None:
      if self.args.filters is None:
        raise ArgumentError('Supply at least one system or filter!')
      # Find only by filter, defaulting to system-only search.
      self.args.system = ['.*' if self.args.regex else '*']
      if not self.args.stations:
        self.args.systems = True
    else:
      self.args.system = [self.args.system]

  def run(self):
    sys_matches = []
    stn_matches = []

    with env.use() as envdata:
      filters = filtering.entry_separator.join(self.args.filters) if self.args.filters is not None else None
      if self.args.regex:
        if self.args.systems or not self.args.stations:
          sys_matches = list(envdata.find_systems_by_regex(self.args.system[0], filters=filters))
        if self.args.stations or not self.args.systems:
          stn_matches = list(envdata.find_stations_by_regex(self.args.system[0], filters=filters))
      else:
        if self.args.systems or not self.args.stations:
          sys_matches = list(envdata.find_systems_by_glob(self.args.system[0], filters=filters))
        if self.args.stations or not self.args.systems:
          stn_matches = list(envdata.find_stations_by_glob(self.args.system[0], filters=filters))

      if (self.args.systems or not self.args.stations) and len(sys_matches) > 0:
        print("")
        print("Matching systems:")
        print("")
        stations = envdata.find_stations(sys_matches) if self.args.list_stations else None
        for sysobj in sorted(sys_matches, key=lambda t: t.name):
          if self.args.show_ids or self.args.id64:
            id = " ({0})".format(sysobj.pretty_id64(self.args.id64) if self.args.id64 else sysobj.id)
          else:
            id = ""
          print("  {0}{1}".format(sysobj.to_string(), id))
          if self.args.list_stations:
            stlist = stations.get(sysobj)
            if stlist is None:
              continue
            stlist.sort(key=lambda t: (t.distance if t.distance else sys.maxsize))
            for stn in stlist:
              print("        {0}".format(stn.to_string(False)))
        print("")

    if (self.args.stations or not self.args.systems) and len(stn_matches) > 0:
      print("")
      print("Matching stations:")
      print("")
      for stnobj in sorted(stn_matches, key=lambda t: t.name):
        print("  {0}{1}".format(stnobj.to_string(), " ({0})".format(stnobj.id) if self.args.show_ids else ""))
      print("")

    if len(sys_matches) == 0 and len(stn_matches) == 0:
      print("")
      print("No matches")
      print("")

    return True
