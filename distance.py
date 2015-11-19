#!/usr/bin/env python

from __future__ import print_function
import argparse
import calc
import env
import logging
import math
import sys
from vector3 import Vector3

app_name = "distance"

log = logging.getLogger(app_name)

class Application:

  def __init__(self, arg, hosted):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Plot jump distance matrix", fromfile_prefix_chars="@", parents = ap_parents, prog = app_name)
    ap.add_argument("-c", "--csv", action='store_true', default=False, help="Output in CSV")
    ap.add_argument("-o", "--ordered", action='store_true', default=False, help="List is ordered (do not sort alphabetically)")
    ap.add_argument("-f", "--full-width", action='store_true', default=False, help="Do not truncate heading names for readability")
    ap.add_argument("systems", metavar="system", nargs='+', help="Systems")

    self.args = ap.parse_args(arg)
    self.longest = 6
    self._max_heading = 1000 if self.args.full_width else 10
    self._padding_width = 2

    self._calc = calc.Calc(self.args, None)


  def print_system(self, name, is_line_start, max_len = None):
    if self.args.csv:
      sys.stdout.write('%s%s' % ('' if is_line_start else ',', name))
    else:
      # If name length is > max, truncate name and append ".."
      tname = name if (max_len is None or len(name) <= max_len) else (name[0:max_len-2] + '..')
      # If we have a max length, account for it when working out padding
      pad = (min(self.longest, max_len) if max_len is not None else self.longest) + self._padding_width - len(tname)
      sys.stdout.write('%s%s' % (' ' * pad, tname))

  def distance(self, a, b):
    start = env.data.eddb_systems_by_name[a]
    end = env.data.eddb_systems_by_name[b]
    return (end.position - start.position).length

  def format_distance(self, dist):
    fmt = '{0:.2f}' if self.args.csv else '{0: >7.2f}'
    return fmt.format(dist)

  def run(self):
    if not self.args.csv:
      self.longest = max([len(s) for s in self.args.systems])

    for y in self.args.systems:
      if not y.lower() in env.data.eddb_systems_by_name:
        log.error("Could not find system \"{0}\"!".format(y))
        return

    print('')

    # If we have many systems, generate a Raikogram
    if len(self.args.systems) > 2 or self.args.csv:

      if not self.args.ordered:
        # Remove duplicates
        seen = set()
        seen_add = seen.add
        self.args.systems = [x for x in self.args.systems if not (x in seen or seen_add(x))]
        # Sort alphabetically
        self.args.systems.sort()

      if not self.args.csv:
        self.print_system('', True)

      for y in self.args.systems:
        self.print_system(y, False, self._max_heading)
      print('')

      for x in self.args.systems:
        self.print_system(x, True)
        for y in self.args.systems:
          self.print_system('-' if y == x else self.format_distance(self.distance(x.lower(), y.lower())), False, self._max_heading)
        print('')

      if self.args.ordered:
        print('')
        self.print_system('Total:', True)
        total_dist = self._calc.route_dist([env.data.eddb_systems_by_name[x.lower()] for x in self.args.systems])
        self.print_system(self.format_distance(total_dist), False, self._max_heading)

      print('')

    # Otherwise, just return the simple output
    else:
      
      start = env.data.eddb_systems_by_name[self.args.systems[0].lower()]
      end = env.data.eddb_systems_by_name[self.args.systems[1].lower()]

      print(start.to_string())
      print('    === {0: >7.2f}Ly ===> {1}'.format((end.position - start.position).length, end.to_string()))

    print('')

if __name__ == '__main__':
  a = Application(env.local_args, False)
  a.run()

