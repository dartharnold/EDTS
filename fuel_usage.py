#!/usr/bin/env python

from __future__ import print_function
import argparse
from edtslib.cow import ColumnObjectWriter
from edtslib import env
from edtslib import fuel_usage
from edtslib import ship
from edtslib import util

def parse_args(arg, hosted, state):
  ap_parents = [env.arg_parser] if not hosted else []
  ap = argparse.ArgumentParser(description = "Plot jump distance matrix", fromfile_prefix_chars="@", parents = ap_parents, prog = fuel_usage.app_name)
  ap.add_argument(      "--ship", metavar="filename", type=str, required=False, help="Load ship data from export file")
  ap.add_argument("-f", "--fsd", type=str, required=False, help="The ship's frame shift drive in the form 'A6 or '6A'")
  ap.add_argument("-b", "--boost", type=str.upper, choices=['0', '1', '2', '3', 'D', 'N'], help="FSD boost level (0 for none, D for white dwarf, N for neutron)")
  ap.add_argument("-B", "--range-boost", type=float, help="The bonus from the ship's Guardian FSD booster")
  ap.add_argument("-m", "--mass", type=float, required=False, help="The ship's unladen mass excluding fuel")
  ap.add_argument("-t", "--tank", type=float, required=False, help="The ship's fuel tank size")
  ap.add_argument("-T", "--reserve-tank", type=float, required=False, help="The ship's reserve tank size")
  ap.add_argument("-s", "--starting-fuel", type=float, required=False, help="The starting fuel quantity (default: tank size)")
  ap.add_argument("-c", "--cargo", type=int, default=fuel_usage.default_cargo, help="Cargo on board the ship")
  ap.add_argument(      "--fsd-optmass", type=str, help="The optimal mass of your FSD, either as a number in T or modified percentage value (including % sign)")
  ap.add_argument(      "--fsd-mass", type=str, help="The mass of your FSD, either as a number in T or modified percentage value (including % sign)")
  ap.add_argument(      "--fsd-maxfuel", type=str, help="The max fuel per jump of your FSD, either as a number in T or modified percentage value (including % sign)")
  ap.add_argument("-r", "--refuel", action='store_true', default=False, help="Assume that the ship can be refueled as needed, e.g. by fuel scooping")
  ap.add_argument("systems", metavar="system", nargs='+', help="Systems")

  parsed = ap.parse_args(arg)

  if parsed.fsd is not None and parsed.mass is not None and parsed.tank is not None:
    parsed.ship = ship.Ship.from_args(fsd = parsed.fsd, mass = parsed.mass, tank = parsed.tank, reserve_tank = parsed.reserve_tank, range_boost = parsed.range_boost, fsd_optmass = parsed.fsd_optmass, fsd_mass = parsed.fsd_mass, fsd_maxfuel = parsed.fsd_maxfuel)
  elif parsed.ship:
    loaded = ship.Ship.from_file(parsed.ship)
    fsd = parsed.fsd if parsed.fsd is not None else loaded.fsd
    mass = parsed.mass if parsed.mass is not None else loaded.mass
    tank = parsed.tank if parsed.tank is not None else loaded.tank_size
    reserve_tank = parsed.reserve_tank if parsed.reserve_tank is not None else loaded.reserve_tank
    range_boost = parsed.range_boost if parsed.range_boost is not None else loaded.range_boost
    parsed.ship = ship.Ship(fsd, mass, tank, reserve_tank = reserve_tank, range_boost = range_boost)
  elif 'ship' in state:
    fsd = parsed.fsd if parsed.fsd is not None else state['ship'].fsd
    mass = parsed.mass if parsed.mass is not None else state['ship'].mass
    tank = parsed.tank if parsed.tank is not None else state['ship'].tank_size
    reserve_tank = parsed.reserve_tank if parsed.reserve_tank is not None else state['ship'].reserve_tank
    range_boost = parsed.range_boost if parsed.range_boost is not None else state['ship'].range_boost
    parsed.ship = ship.Ship(fsd, mass, tank, reserve_tank = reserve_tank, range_boost = range_boost)
  else:
    parsed.ship = None

  if parsed.fsd_optmass is not None or parsed.fsd_mass is not None or parsed.fsd_maxfuel is not None:
    fsd_optmass = util.parse_number_or_add_percentage(parsed.fsd_optmass, parsed.ship.fsd.stock_optmass)
    fsd_mass = util.parse_number_or_add_percentage(parsed.fsd_mass, parsed.ship.fsd.stock_mass)
    fsd_maxfuel = util.parse_number_or_add_percentage(parsed.fsd_maxfuel, parsed.ship.fsd.stock_maxfuel)
    parsed.ship = parsed.ship.get_modified(optmass=fsd_optmass, fsdmass=fsd_mass, maxfuel=fsd_maxfuel)

  return parsed

def run(args, hosted = False, state = {}):
  parsed = parse_args(args, hosted, state)
  results = list(fuel_usage.Application(**vars(parsed)).run())
  if env.global_args.json:
    print(util.to_json(results))
    return

  headings = ['  ', 'Distance', 'System']
  padding = ['>', '>', '<', '>']
  intra = [' ', '  ', '  ', '  ']
  refueling = False

  for entry in results:
    if entry.refuel is not None:
      refueling = True
      break

  if refueling:
    headings += ['Refuel', 'Percent']
  headings += ['Fuel cost', 'Remaining']

  cow = ColumnObjectWriter(len(headings), padding, intra)
  cow.add(headings)

  last_origin = None
  for entry in results:
    if entry.refuel is not None:
      row = ['', '', '']
      if refueling:
        row += ['{:.2f}T'.format(entry.refuel.amount), '{:.2f}%'.format(entry.refuel.percent)]
      row += ['', '{:.2f}T'.format(entry.fuel.final)]
      cow.add(row)
    else:
      if last_origin is None:
        row = ['', '', entry.origin.system]
        if refueling:
          row += ['', '']
        # This is the first row, so use the initial fuel available, not at the destination
        row += ['', '{:.2f}T'.format(entry.fuel.initial), '']
        cow.add(row)
      row = ['!' if not entry.ok else '*' if entry.is_long else '', entry.distance.to_string(True), entry.destination.system]
      if refueling:
        row += ['', '']
      row += ['{:.2f}T'.format(entry.fuel.cost), '{:.2f}T'.format(entry.fuel.final)]
      cow.add(row)

      last_origin = entry.origin.system

  print('')
  cow.out()
  print('')

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  env.start()
  run(env.local_args)
  env.stop()
