#!/usr/bin/env python

from __future__ import print_function
import argparse
import env
import fnmatch
import logging

app_name = "find"

log = logging.getLogger(app_name)


class Application(object):

  def __init__(self, arg, hosted, state = {}):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Find System or Station", fromfile_prefix_chars="@", parents=ap_parents, prog = app_name)
    ap.add_argument("-a", "--anagram", default=False, action='store_true', help="Find names matching an anagram of the provided string")
    ap.add_argument("-s", "--systems", default=False, action='store_true', help="Limit the search to system names")
    ap.add_argument("-t", "--stations", default=False, action='store_true', help="Limit the search to station names")
    ap.add_argument("-i", "--show-ids", default=False, action='store_true', help="Show system and station IDs in output")
    ap.add_argument("-l", "--list-stations", default=False, action='store_true', help="List stations in returned systems")
    ap.add_argument("system", metavar="system", type=str, nargs=1, help="The system or station to find")
    self.args = ap.parse_args(arg)

  def run(self):
    searchname = self.args.system[0].lower()

    sys_matches = []
    stn_matches = []

    if not self.args.anagram:
      if self.args.systems or not self.args.stations:
        sys_matches = fnmatch.filter(list(env.data.eddb_systems_by_name.keys()), searchname)
      if self.args.stations or not self.args.systems:
        stn_matches = fnmatch.filter(list(env.data.eddb_stations_by_name.keys()), searchname)

    else:
      if self.args.systems or not self.args.stations:
        sys_matches = self.anagram_find_matches(list(env.data.eddb_systems_by_name.keys()), searchname)
      if self.args.stations or not self.args.systems:
        stn_matches = self.anagram_find_matches(list(env.data.eddb_stations_by_name.keys()), searchname)

    if (self.args.systems or not self.args.stations) and len(sys_matches) > 0:
      print("")
      print("Matching systems:")
      print("")
      for sys in sorted(sys_matches):
        sysobj = env.data.get_system(sys)
        print("  {0}{1}".format(sysobj.to_string(), " ({0})".format(sysobj.id) if self.args.show_ids else ""))
        if self.args.list_stations:
          stlist = env.data.get_stations(sysobj)
          stlist.sort(key=lambda t: t.distance)
          for stn in stlist:
            print("        {0}".format(stn.to_string(False)))
      print("")

    if (self.args.stations or not self.args.systems) and len(stn_matches) > 0:
      print("")
      print("Matching stations:")
      print("")
      for stn_name in sorted(stn_matches):
        stns = env.data.eddb_stations_by_name[stn_name]
        for stnobj in stns:
          print("  {0}{1}".format(stnobj.to_string(), " ({0})".format(stnobj.id) if self.args.show_ids else ""))
      print("")

    if len(sys_matches) == 0 and len(stn_matches) == 0:
      print("")
      print("No matches")
      print("")

    return True

  def anagram_find_matches(self, keys, query):
    results = []
    for sys_name in keys:
      cur_query = query
      for key in sys_name.split(' '):
        passed = True
        for ch in key:
          if ch >= 'a' and ch <= 'z' and ch not in cur_query:
            passed = False
            break
          cur_query = cur_query.replace(str(ch), '', 1)
        if passed and len(cur_query) == 0:
          results.append(sys_name)
    return results


if __name__ == '__main__':
  a = Application(env.local_args, False)
  a.run()
