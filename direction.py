#!/usr/bin/env python

from __future__ import print_function
import argparse
import env
import logging
import vector3

app_name = "direction"

log = logging.getLogger(app_name)

class Application(object):

  def __init__(self, arg, hosted, state = {}):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Calculate direction between two systems", fromfile_prefix_chars="@", parents = ap_parents, prog = app_name)
    ap.add_argument("-a", "--angle", default=False, action='store_true', help="Return angle not vector")
    ap.add_argument("-n", "--normal", default=False, action='store_true', help="Return normalised direction vector")
    ap.add_argument("-r", "--reference", metavar="system", nargs='?', default="Sol", help="Reference system for angle calculation")
    ap.add_argument("systems", metavar="system", nargs=2, help="Systems")

    self.args = ap.parse_args(arg)

  def run(self):
    with env.use() as envdata:
      systems = envdata.parse_systems(self.args.systems)
      for y in self.args.systems:
        if y not in systems or systems[y] is None:
          log.error("Could not find system \"{0}\"!".format(y))
          return

      if self.args.reference:
        reference = envdata.parse_system(self.args.reference)
        if reference is None:
          log.error("Could not find reference system \"{0}\"!".format(self.args.reference))
          return

      a, b = [systems[y].position for y in self.args.systems]
      v = b - a
      log.debug("From {} to {}".format(a, b))

      if self.args.angle:
        print(v.angle_to(a - reference.position))
      elif self.args.normal:
        log.debug("Normalising {}".format(v))
        print(v.get_normalised())
      else:
        print(v)

if __name__ == '__main__':
  env.start()
  a = Application(env.local_args, False)
  a.run()
