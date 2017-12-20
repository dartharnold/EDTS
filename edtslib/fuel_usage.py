#!/usr/bin/env python

from __future__ import print_function
from math import log10, floor, fabs
import re
import sys

from .dist import Lightyears
from .opaque_types import Fuel, Refuel, Location, Opaq
from . import env
from . import ship
from . import util

app_name = "fuel_usage"

log = util.get_logger(app_name)

default_cargo = 0

class Result(Opaq):
  def __init__(self, **args):
    self.origin = args.get('origin')
    self.destination = args.get('destination')
    self.distance = args.get('distance', Lightyears(0))
    self.cargo = args.get('cargo', 0)
    self.fuel = args.get('fuel', Fuel())
    self.is_long = args.get('is_long', False)
    self.ok = args.get('ok', True)
    self.refuel = args.get('refuel')

class Application(object):
  refuel_re = re.compile(r'^([+=])?([\d.]+)([%T])?$')

  def __init__(self, **args):
    self._boost = args.get('boost')
    self._cargo = args.get('cargo', default_cargo)
    self._refuel = args.get('refuel')
    self._ship = args.get('ship')
    self._starting_fuel = args.get('starting_fuel')
    self._systems = args.get('systems')

    if self._ship is None:
      raise RuntimeError("Error: You must specify a ship")

    if self._boost:
      self._ship.supercharge(self._boost)

    if self._starting_fuel is None:
      self._starting_fuel = self._ship.tank_size

  def refuel(self, amount, cur_fuel = None):
    m = self.refuel_re.match(amount)
    if m is not None:
      if cur_fuel is None:
        return True
      try:
        absolute = (m.group(1) == '=')
        if m.group(3) == '%':
          extra_fuel = self._ship.refuel(cur_fuel, percent = float(m.group(2)), absolute = absolute)
        else:
          extra_fuel = self._ship.refuel(cur_fuel, amount = float(m.group(2)), absolute = absolute)
        return extra_fuel
      except:
        log.exception("Can't parse refuel amount.")
        return None
    else:
      return None

  def run(self):
    refueling = False
    with env.use() as envdata:
      systems = envdata.parse_systems([arg for arg in self._systems if self.refuel(arg) is None])
      for y in self._systems:
        if self.refuel(y) is not None:
          refueling = True
          continue
        if y not in systems or systems[y] is None:
          raise RuntimeError("Could not find system \"{0}\"!", y)

    cur_fuel = self._starting_fuel

    prev = None
    for y in self._systems:
      extra_fuel = self.refuel(y, cur_fuel)
      if extra_fuel is not None:
        used_fuel = self._ship.tank_size - cur_fuel
        if extra_fuel > used_fuel:
          extra_fuel = used_fuel
        yield Result(fuel = Fuel(initial = cur_fuel, final = cur_fuel + extra_fuel), refuel = Refuel(amount = extra_fuel, percent = self._ship.refuel_percent(extra_fuel)))
        cur_fuel += extra_fuel
        continue
      else:
        s = systems[y]
      if prev is not None:
        distance = prev.distance_to(s)
        is_ok = True
        fmin, fmax = self._ship.fuel_weight_range(distance, allow_invalid=True)
        # Fudge factor to prevent cost coming out at exactly maxfuel (stupid floating point!)
        cur_fuel = min(fmax - 0.000001, self._ship.tank_size)
        is_long = (fmax >= 0.0 and fmax < self._ship.tank_size)
        if self._refuel:
          is_ok = (is_ok and fmax >= 0.0)
        fuel_cost = self._ship.cost(distance, cur_fuel, self._cargo)
        is_ok = (is_ok and fuel_cost <= self._ship.fsd.maxfuel and cur_fuel >= fuel_cost)
        yield Result(origin = Location(system = prev), destination = Location(system = s), distance = Lightyears(distance), cargo = self._cargo, ok = is_ok, is_long = is_long, fuel = Fuel(initial = cur_fuel, cost = fuel_cost, final = cur_fuel - fuel_cost, min = fmin, max = fmax))
        cur_fuel -= fuel_cost
      prev = s
