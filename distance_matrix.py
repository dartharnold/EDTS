#!/usr/bin/env python

from __future__ import print_function
import argparse
import env
import logging
import math
import sys
from vector3 import Vector3

app_name = "distance_matrix"

log = logging.getLogger(app_name)

class Application:

  def __init__(self, arg, hosted):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Plot jump distance matrix", fromfile_prefix_chars="@", parents = ap_parents, prog = app_name)
    ap.add_argument("-c", "--csv", action='store_true', default=False, help="Output in CSV")
    ap.add_argument("systems", metavar="system", nargs='+', help="Systems")

    self.args = ap.parse_args(arg)
    self.longest = 6

  def print_system(self, name, is_line_start):
    if self.args.csv:
      sys.stdout.write('%s%s' % ('' if is_line_start else ',', name))
    else:
      pad = 2 + self.longest - len(name)
      sys.stdout.write('%s%s' % (' ' * pad, name))

  def distance(self, a, b):
    start = env.data.eddb_systems_by_name[a]
    end = env.data.eddb_systems_by_name[b]
    fmt = '{0:.2f}' if self.args.csv else '{0: >7.2f}'
    return fmt.format((end.position - start.position).length)

  def run(self):
    if not self.args.csv:
      self.longest = max([len(s) for s in self.args.systems])

    for y in self.args.systems:
      if not y.lower() in env.data.eddb_systems_by_name:
        log.error("Could not find system \"{0}\"!".format(y))
        return

    self.args.systems.sort()

    print('')

    if not self.args.csv:
      self.print_system('', True)

    for y in self.args.systems:
      self.print_system(y, False)
    print('')

    for x in self.args.systems:
      self.print_system(x, True)
      for y in self.args.systems:
        self.print_system('-' if y == x else self.distance(x.lower(), y.lower()), False)
      print('')

    print('')

if __name__ == '__main__':
  a = Application(env.local_args, False)
  a.run()

