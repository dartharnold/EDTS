#!/usr/bin/env python

from __future__ import print_function
import argparse
import math
import sys

from . import calc
from . import env
from . import pgnames
from . import util
from .cow import ColumnObjectWriter
from .dist import Lightyears

app_name = "distance"

log = util.get_logger(app_name)


class Application(object):

  def __init__(self, arg, hosted, state = {}):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Plot jump distance matrix", fromfile_prefix_chars="@", parents = ap_parents, prog = app_name)
    ap.add_argument("-c", "--csv", action='store_true', default=False, help="Output in CSV")
    ap.add_argument("-o", "--ordered", action='store_true', default=False, help="List is ordered (do not sort alphabetically)")
    ap.add_argument("-f", "--full-width", action='store_true', default=False, help="Do not truncate heading names for readability")
    ap.add_argument("-s", "--start", type=str, required=False, help="Defines a start system to calculate all other distances from")
    ap.add_argument("-r", "--route", action='store_true', default=False, help="List of systems is a sequential list to visit and get distances between")
    ap.add_argument("systems", metavar="system", nargs='+', help="Systems")

    self.args = ap.parse_args(arg)
    self.longest = 6
    self._max_heading = 1000 if self.args.full_width else 10
    self._padding_width = 2

  def print_system(self, name, is_line_start, max_len = None):
    if self.args.csv:
      sys.stdout.write('%s%s' % ('' if is_line_start else ',', name))
    else:
      # If name length is > max, truncate name and append ".."
      tname = name if (max_len is None or len(name) <= max_len) else (name[0:max_len-2] + '..')
      # If we have a max length, account for it when working out padding
      pad = (min(self.longest, max_len) if max_len is not None else self.longest) + self._padding_width - len(tname)
      sys.stdout.write('%s%s' % (' ' * pad, tname))

  def format_distance(self, dist):
    fmt = '{0:.2f}' if self.args.csv else '{0: >7.2f}'
    return fmt.format(dist)

  def run(self):
    if not self.args.csv:
      self.longest = max([len(s) for s in self.args.systems])

    with env.use() as envdata:
      start_obj = None
      if self.args.start is not None:
        start_obj = envdata.parse_system(self.args.start)
        if start_obj is None:
          log.error("Could not find start system \"{0}\"!", self.args.start)
          return

      systems = envdata.parse_systems(self.args.systems)
      for y in self.args.systems:
        if y not in systems or systems[y] is None:
          pgsys = pgnames.get_system(y)
          if pgsys is not None:
            systems[y] = pgsys
          else:
            log.error("Could not find system \"{0}\"!", y)
            return

      if start_obj is None and not self.args.route and not self.args.csv and len(self.args.systems) == 2:
        self.args.start = self.args.systems[0]
        start_obj = systems[self.args.start]
        self.args.systems = [self.args.systems[1]]

    cow = ColumnObjectWriter()
    if self.args.route:
      cow.expand(4, ['<', '>', '<', '<'], ['   ', ' ', ' ', '   '])
      cow.add([
        '', # Padding
        '', # Distance
        '', # >
        systems[self.args.systems[0]].to_string(),
        '', # Extra
      ])
      for i in range(1, len(self.args.systems)):
        sobj1 = systems[self.args.systems[i-1]]
        sobj2 = systems[self.args.systems[i]]
        cow.add([
          '',
          Lightyears(sobj1.distance_to(sobj2)).to_string(self.args.full_width),
          '>',
          sobj2.to_string(),
          '+/- {}'.format(Lightyears(sobj1.uncertainty3d + sobj2.uncertainty3d).to_string(self.args.full_width)) if sobj1.uncertainty3d != 0.0 or sobj2.uncertainty3d != 0.0 else ''
        ])

    elif self.args.start is not None and start_obj is not None:
      distances = {}
      for s in self.args.systems:
        distances[s] = systems[s].distance_to(start_obj)

      if not self.args.ordered:
        self.args.systems.sort(key=distances.get)

      cow.expand(6, ['<', '<', '>', '>', '<'], ['   ', ' '])
      for s in self.args.systems:
        sobj = systems[s]
        cow.add([
          '', # Padding
          start_obj.to_string(),
          '>',
          Lightyears(sobj.distance_to(start_obj)).to_string(self.args.full_width),
          '>',
          sobj.to_string(),
          '+/- {}'.format(Lightyears(start_obj.uncertainty3d + sobj.uncertainty3d).to_string(self.args.full_width)) if start_obj.uncertainty3d != 0.0 or sobj.uncertainty3d != 0.0 else ''
        ])

    else:
      # If we have many systems, generate a Raikogram
      if len(self.args.systems) > 2 or self.args.csv:
        cow.expand(len(self.args.systems) + (1 if not self.args.csv else 0), ['>'], [',' if self.args.csv else '   '])

        if not self.args.ordered:
          # Remove duplicates
          seen = set()
          seen_add = seen.add
          self.args.systems = [x for x in self.args.systems if not (x in seen or seen_add(x))]
          # Sort alphabetically
          self.args.systems.sort()

        row = [''] + self.args.systems
        if self.args.csv:
          print(','.join(row))
        else:
          cow.add(row)

        for x in self.args.systems:
          row = [x]
          for y in self.args.systems:
            row.append('-' if y == x else Lightyears(systems[x].distance_to(systems[y])).to_string(self.args.full_width))
          if self.args.csv:
            print(','.join(row))
          else:
            cow.add(row)

        if self.args.ordered:
          row = ['Total:', Lightyears(calc.route_dist([systems[x] for x in self.args.systems])).to_string(self.args.full_width)]
          if self.args.csv:
            print(','.join(row))
          else:
            cow.add([])
            cow.add(row)

      else:
        log.error("For a simple distance calculation, at least two system names must be provided!")
        return
    print('')
    cow.out()
    print('')
