#!/usr/bin/env python

from __future__ import print_function
import math
import sys

from .dist import Lightyears, Metres
from .opaque_types import Opaq
from . import env
from . import filtering
from . import ship
from . import util

app_name = "obscured"

log = util.get_logger(app_name)

default_num = 10
default_min_deviation = 15

DISTANCE_FROM = 'DISTANCE-FROM'
DISTANCE_TO = 'DISTANCE-TO'
DEVIATION = 'DEVIATION'
default_sort = DEVIATION

class Result(Opaq):
  def __init__(self, **args):
    self.system = args.get('system')
    self.deviation = args.get('deviation')
    self.distances = args.get('distances', {})

class Application(object):

  def __init__(self, **args):
    self._end = args.get('end')
    self._jump_range = args.get('jump_range')
    self._min_deviation = args.get('min_deviation')
    self._num = args.get('num')
    self._obscured = args.get('obscured')
    self._ship = args.get('ship')
    self._sort = args.get('sort')
    self._start = args.get('start')

    if self._ship is not None:
      if not isinstance(self._ship, ship.Ship):
        self._ship = ship.Ship.from_args(**self._ship)
        if self._ship is None:
          raise RuntimeError("Can't instantiate Ship from provided 'ship' parameter!")
      log.debug(str(self._ship))

  def deviation(self, a, b, r):
    v = (a.position - r.position).get_normalised()
    w = (b.position - r.position).get_normalised()
    d = v.dot(w)
    return 100 * (1 - d)

  def run(self):
    with env.use() as envdata:
      snames = [name for name in [self._start, self._end, self._obscured] if name is not None]
      envdata.find_systems_from_edsm(snames)
      systems = envdata.parse_systems(snames)
      for name in snames:
        if systems.get(name) is None:
          log.error("Could not find system \"{0}\"!", name)
          return
      start = systems.get(self._start)
      obscured = systems.get(self._obscured)
      end = systems.get(self._end, obscured)
      if self._ship is not None:
        jump_range = self._ship.range()
      elif self._jump_range is not None:
        jump_range = self._jump_range
      else:
        jump_range = start.distance_to(end)

      # Candidates must be within one jump of the start system.
      filters = {'close_to': [{filtering.PosArgs: [filtering.Operator('=', start)], 'distance': [filtering.Operator('<=', jump_range)]}]}
      if self._jump_range is not None:
        # Restrict search radius to distance to end system plus one jump.
        filters['close_to'].append({filtering.PosArgs: [filtering.Operator('=', start)], 'distance': [filtering.Operator('<=', start.distance_to(end))]})
      envdata.find_filtered_systems_from_edsm(filters)
      names = [start.name, obscured.name, end.name]
      asys = [s for s in envdata.find_all_systems(filters = envdata.convert_filter_object(filters)) if s.name not in names and self.deviation(s, obscured, start) >= self._min_deviation]
      if self._sort == DISTANCE_TO:
        asys.sort(key = lambda s: s.distance_to(end))
      elif self._sort == DISTANCE_FROM:
        asys.sort(key = lambda s: s.distance_to(end))
      else:
        asys.sort(key = lambda s: self.deviation(s, obscured, start), reverse = True)
      if self._num:
        asys = asys[0:self._num]

        for i in range(0, len(asys)):
          yield Result(system = asys[i], deviation = self.deviation(asys[i], obscured, start), distances = { start.name: Lightyears(asys[i].distance_to(start)), end.name: Lightyears(asys[i].distance_to(end)) })
