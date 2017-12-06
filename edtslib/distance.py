#!/usr/bin/env python

from __future__ import print_function
import math
import sys

from . import calc
from . import env
from . import pgnames
from . import util
from .dist import Lightyears
from .opaque_types import Location, Opaq

app_name = "distance"

log = util.get_logger(app_name)

class Result(Opaq):
  def __init__(self, **args):
    self.origin = args.get('origin')
    self.destination = args.get('destination')
    self.distance = args.get('distance', Lightyears(0))

class Application(object):

  def __init__(self, **args):
    self._csv = args.get('csv')
    self._start = args.get('start')
    self._ordered = args.get('ordered')
    self._route = args.get('route')
    self._systems = args.get('systems')

  def run(self):
    with env.use() as envdata:
      start_obj = None
      if self._start is not None:
        start_obj = envdata.parse_system(self._start)
        if start_obj is None:
          log.error("Could not find start system \"{0}\"!", self._start)
          return

      systems = envdata.parse_systems(self._systems)
      for y in self._systems:
        if y not in systems or systems[y] is None:
          pgsys = pgnames.get_system(y)
          if pgsys is not None:
            systems[y] = pgsys
          else:
            log.error("Could not find system \"{0}\"!", y)
            return

      if start_obj is None and not self._route and not self._csv and len(self._systems) == 2:
        self._start = self._systems[0]
        start_obj = systems[self._start]
        self._systems = [self._systems[1]]

    if self._route:
      for i in range(1, len(self._systems)):
        sobj1 = systems[self._systems[i-1]]
        sobj2 = systems[self._systems[i]]
        yield Result(origin = Location(system = sobj1), destination = Location(system = sobj2), distance = Lightyears(sobj1.distance_to(sobj2)))

    elif self._start is not None and start_obj is not None:
      distances = {}
      for s in self._systems:
        distances[s] = systems[s].distance_to(start_obj)

      if not self._ordered:
        self._systems.sort(key=distances.get)

      for s in self._systems:
        sobj = systems[s]
        yield Result(origin = Location(system = start_obj), destination = Location(system = systems[s]), distance = Lightyears(systems[s].distance_to(start_obj)))

    else:
      # If we have many systems, generate a Raikogram
      if len(self._systems) > 2 or self._csv:

        if not self._ordered:
          # Remove duplicates
          seen = set()
          seen_add = seen.add
          self._systems = [x for x in self._systems if not (x in seen or seen_add(x))]
          # Sort alphabetically
          self._systems.sort()

        for x in self._systems:
          for y in self._systems:
            yield Result(origin = Location(system = x), destination = Location(system = y), distance = Lightyears(systems[x].distance_to(systems[y])))

      else:
        raise RuntimeError("For a simple distance calculation, at least two system names must be provided!")
