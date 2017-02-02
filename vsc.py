#!/usr/bin/env python

from __future__ import print_function
import argparse
import env
import filter
import logging
import starcache
import vector3

app_name = "vsc"

log = logging.getLogger(app_name)

class Application(object):

  def __init__(self, arg, hosted, state = {}):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Read and write the visited stars cache", fromfile_prefix_chars="@", parents = ap_parents, prog = app_name)
    subparsers = ap.add_subparsers()
    rp = subparsers.add_parser("read", help="Read from star cache")
    rp.add_argument("readfile", metavar="filename")
    rp.set_defaults(func=self.run_read)
    wp = subparsers.add_parser("write", help="Write to star cache")
    wp.add_argument("writefile", metavar="filename")
    wp.add_argument("-r", "--recent", default=False, action="store_true", help="Create int RecentlyVisitedStars format")
    wp.add_argument("filters", metavar="filters", nargs='*')
    wp.set_defaults(func=self.run_write)

    self.args = ap.parse_args(arg)

  def run(self):
    with env.use() as envdata:
      self.args.func(envdata, self.args)

  def batch_read(self, envdata, id64list):
    missing = { str(id64): True for id64 in id64list }
    for s in envdata.find_systems_by_id64(id64list):
      print(s.name)
      id64 = str(s.id64)
      if id64 in missing:
        del(missing[id64])
    for id64 in missing.keys():
      print(id64)

  def run_read(self, envdata, args):
    id64list = []
    batch_size = 512
    for id64 in starcache.parse_visited_stars_cache(args.readfile):
      id64list.append(id64)
      if len(id64list) >= batch_size:
        self.batch_read(envdata, id64list)
        id64list = []
    if len(id64list):
      self.batch_read(envdata, id64list)

  def run_write(self, envdata, args):
    starcache.write_visited_stars_cache(args.writefile, envdata.find_all_systems(filter.entry_separator.join(args.filters) if len(args.filters) else None), self.args.recent)

if __name__ == '__main__':
  env.start()
  a = Application(env.local_args, False)
  a.run()
