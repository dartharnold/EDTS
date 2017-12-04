#!/usr/bin/env python

from __future__ import print_function
import math
import sys

from . import calc
from . import env
from . import pgnames
from . import util
from .dist import Lightyears
from .opaque_types import Location

app_name = "distance"

log = util.get_logger(app_name)

class Result(object):
  def __init__(self, **args):
    self.origin = args.get('origin')
    self.destination = args.get('destination')
    self.distance = args.get('distance', Lightyears(0))

class Application(object):

  def __init__(self, args):
    self.args = args

  def format_distance(self, dist):
    fmt = '{0:.2f}' if self.args.csv else '{0: >7.2f}'
    return fmt.format(dist)

  def run(self):
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

    if self.args.route:
      for i in range(1, len(self.args.systems)):
        sobj1 = systems[self.args.systems[i-1]]
        sobj2 = systems[self.args.systems[i]]
        yield Result(origin = Location(system = sobj1), destination = Location(system = sobj2), distance = Lightyears(sobj1.distance_to(sobj2)))

    elif self.args.start is not None and start_obj is not None:
      distances = {}
      for s in self.args.systems:
        distances[s] = systems[s].distance_to(start_obj)

      if not self.args.ordered:
        self.args.systems.sort(key=distances.get)

      for s in self.args.systems:
        sobj = systems[s]
        yield Result(origin = Location(system = start_obj), destination = Location(system = systems[s]), distance = Lightyears(systems[s].distance_to(start_obj)))

    else:
      # If we have many systems, generate a Raikogram
      if len(self.args.systems) > 2 or self.args.csv:

        if not self.args.ordered:
          # Remove duplicates
          seen = set()
          seen_add = seen.add
          self.args.systems = [x for x in self.args.systems if not (x in seen or seen_add(x))]
          # Sort alphabetically
          self.args.systems.sort()

        for x in self.args.systems:
          for y in self.args.systems:
            yield Result(origin = Location(system = x), destination = Location(system = y), distance = Lightyears(systems[x].distance_to(systems[y])))

      else:
        raise RuntimeError("For a simple distance calculation, at least two system names must be provided!")
