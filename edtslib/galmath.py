#!/usr/bin/env python

from __future__ import print_function
import math
import sys

from .dist import Lightyears
from .opaque_types import Opaq
from . import util

app_name = "galmath"

log = util.get_logger(app_name)

default_distance = 1000.0

class Result(Opaq):
  def __init__(self, **args):
    self.core_distance = args.get('core_distance')
    self.distance = args.get('distance')
    self.inaccuracy = args.get('inaccuracy')
    self.low_max_dist = args.get('low_max_dist')
    self.jump_range = args.get('jump_range')
    self.plot_min = args.get('plot_min')
    self.plot_max = args.get('plot_max')

class Application(object):

  def __init__(self, **args):
    self._core_distance = args.get('core_distance')
    self._distance = args.get('distance', default_distance)
    self._jump_range = args.get('jump_range')

    if self._jump_range is None:
      raise RuntimeError('Jump range not provided')

  def run(self):
    num_jumps = int(math.floor(self._distance / self._jump_range))
    low_max_dist = num_jumps * self._jump_range

    ans = low_max_dist - ((num_jumps / 4.0) + ((self._core_distance + 1) * 2.0))
    inaccuracy = low_max_dist * 0.0025

    log.debug("M = {0:.2f}, N = {1}, D = {2:.2f}", low_max_dist, num_jumps, self._core_distance)

    yield Result(core_distance = Lightyears(self._core_distance * 1000), distance = Lightyears(self._jump_range), inaccuracy = Lightyears(inaccuracy), low_max_dist = Lightyears(low_max_dist), jump_range = Lightyears(self._jump_range), plot_min = Lightyears(ans - inaccuracy), plot_max = Lightyears(ans + inaccuracy))
