#!/usr/bin/env python

from __future__ import print_function
import argparse
from math import log10, floor, fabs
import re
import sys

from .cow import ColumnObjectWriter
from .dist import Lightyears
from . import env
from . import ship
from . import util

app_name = "fuel_usage"

log = util.get_logger(app_name)


class Application(object):
  refuel_re = re.compile(r'^([+=])?([\d.]+)([%T])?$')

  def __init__(self, arg, hosted, state = {}):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Plot jump distance matrix", fromfile_prefix_chars="@", parents = ap_parents, prog = app_name)
    ap.add_argument(      "--ship", metavar="filename", type=str, required=False, help="Load ship data from export file")
    ap.add_argument("-f", "--fsd", type=str, required=False, help="The ship's frame shift drive in the form 'A6 or '6A'")
    ap.add_argument("-b", "--boost", type=str.upper, choices=['0', '1', '2', '3', 'D', 'N'], help="FSD boost level (0 for none, D for white dwarf, N for neutron")
    ap.add_argument("-m", "--mass", type=float, required=False, help="The ship's unladen mass excluding fuel")
    ap.add_argument("-t", "--tank", type=float, required=False, help="The ship's fuel tank size")
    ap.add_argument("-T", "--reserve-tank", type=float, required=False, help="The ship's reserve tank size")
    ap.add_argument("-s", "--starting-fuel", type=float, required=False, help="The starting fuel quantity (default: tank size)")
    ap.add_argument("-c", "--cargo", type=int, default=0, help="Cargo on board the ship")
    ap.add_argument(      "--fsd-optmass", type=str, help="The optimal mass of your FSD, either as a number in T or modified percentage value (including % sign)")
    ap.add_argument(      "--fsd-mass", type=str, help="The mass of your FSD, either as a number in T or modified percentage value (including % sign)")
    ap.add_argument(      "--fsd-maxfuel", type=str, help="The max fuel per jump of your FSD, either as a number in T or modified percentage value (including % sign)")
    ap.add_argument("-r", "--refuel", action='store_true', default=False, help="Assume that the ship can be refueled as needed, e.g. by fuel scooping")
    ap.add_argument("systems", metavar="system", nargs='+', help="Systems")

    self.args = ap.parse_args(arg)

    if self.args.fsd is not None and self.args.mass is not None and self.args.tank is not None:
      self.ship = ship.Ship(self.args.fsd, self.args.mass, self.args.tank, reserve_tank = self.args.reserve_tank)
    elif self.args.ship:
      loaded = ship.Ship.from_file(self.args.ship)
      fsd = self.args.fsd if self.args.fsd is not None else loaded.fsd
      mass = self.args.mass if self.args.mass is not None else loaded.mass
      tank = self.args.tank if self.args.tank is not None else loaded.tank_size
      reserve_tank = self.args.reserve_tank if self.args.reserve_tank is not None else loaded.reserve_tank
      self.ship = ship.Ship(fsd, mass, tank, reserve_tank = reserve_tank)
    elif 'ship' in state:
      fsd = self.args.fsd if self.args.fsd is not None else state['ship'].fsd
      mass = self.args.mass if self.args.mass is not None else state['ship'].mass
      tank = self.args.tank if self.args.tank is not None else state['ship'].tank_size
      reserve_tank = self.args.reserve_tank if self.args.reserve_tank is not None else state['ship'].reserve_tank
      self.ship = ship.Ship(fsd, mass, tank, reserve_tank = reserve_tank)
    else:
      log.error("Error: You must specify --ship, all of --fsd, --mass and --tank, or have previously set a ship")
      sys.exit(1)

    if self.args.fsd_optmass is not None or self.args.fsd_mass is not None or self.args.fsd_maxfuel is not None:
      fsd_optmass = util.parse_number_or_add_percentage(self.args.fsd_optmass, self.ship.fsd.stock_optmass)
      fsd_mass = util.parse_number_or_add_percentage(self.args.fsd_mass, self.ship.fsd.stock_mass)
      fsd_maxfuel = util.parse_number_or_add_percentage(self.args.fsd_maxfuel, self.ship.fsd.stock_maxfuel)
      self.ship = self.ship.get_modified(optmass=fsd_optmass, fsdmass=fsd_mass, maxfuel=fsd_maxfuel)

    if self.args.boost:
      self.ship.supercharge(self.args.boost)

    if self.args.starting_fuel is None:
      self.args.starting_fuel = self.ship.tank_size

  def refuel(self, amount, cur_fuel = None):
    m = self.refuel_re.match(amount)
    if m is not None:
      if cur_fuel is None:
        return True
      try:
        absolute = (m.group(1) == '=')
        if m.group(3) == '%':
          extra_fuel = self.ship.refuel(cur_fuel, percent = float(m.group(2)), absolute = absolute)
        else:
          extra_fuel = self.ship.refuel(cur_fuel, amount = float(m.group(2)), absolute = absolute)
        return extra_fuel
      except:
        log.exception("Can't parse refuel amount.")
        return None
    else:
      return None

  def run(self):
    headings = ['  ', 'Distance', 'System']
    padding = ['>', '>', '<', '>']
    intra = [' ', '  ', '  ', '  ']

    refueling = False
    with env.use() as envdata:
      systems = envdata.parse_systems([arg for arg in self.args.systems if self.refuel(arg) is None])
      for y in self.args.systems:
        if self.refuel(y) is not None:
          refueling = True
          continue
        if y not in systems or systems[y] is None:
          log.error("Could not find system \"{0}\"!", y)
          return

    if refueling:
      headings += ['Refuel', 'Percent']
    headings += ['Fuel cost', 'Remaining']

    cur_fuel = self.args.starting_fuel

    cow = ColumnObjectWriter(len(headings), padding, intra)
    cow.add(headings)

    prev = None
    for y in self.args.systems:
      extra_fuel = self.refuel(y, cur_fuel)
      if extra_fuel is not None:
        used_fuel = self.ship.tank_size - cur_fuel
        if extra_fuel > used_fuel:
          extra_fuel = used_fuel
        cur_fuel += extra_fuel
        row = ['', '', '']
        if refueling:
          row += ['{:.2f}T'.format(extra_fuel), '{:.2f}%'.format(self.ship.refuel_percent(extra_fuel))]
        row += ['', '{:.2f}T'.format(cur_fuel)]
        cow.add(row)
        continue
      else:
        s = systems[y]
      if prev is None:
        # First iteration
        prev = s
        row = ['', '', s]
        if refueling:
          row += ['', '']
        row += ['', '{:.2f}T'.format(cur_fuel), '']
        cow.add(row)
        continue
      distance = prev.distance_to(s)
      is_ok = True
      fmax = self.ship.max_fuel_weight(distance, allow_invalid=True)
      # Fudge factor to prevent cost coming out at exactly maxfuel (stupid floating point!)
      cur_fuel = min(fmax - 0.000001, self.ship.tank_size)
      is_long = (fmax >= 0.0 and fmax < self.ship.tank_size)
      if self.args.refuel:
        is_ok = (is_ok and fmax >= 0.0)

      fuel_cost = self.ship.cost(distance, cur_fuel, self.args.cargo)
      cur_fuel -= fuel_cost
      is_ok = (is_ok and fuel_cost <= self.ship.fsd.maxfuel and cur_fuel >= 0.0)
      row = ['!' if not is_ok else '*' if is_long else '', Lightyears(distance).to_string(True), s]
      if refueling:
        row += ['', '']
      row += ['{:.2f}T'.format(fuel_cost), '{:.2f}T'.format(cur_fuel)]
      cow.add(row)
      prev = s

    print('')
    cow.out()
    print('')


def _get_leg_char(leg):
  if leg['ok']:
    if leg['long']:
      return '~'
    else:
      return '='
  else:
    return '!'
