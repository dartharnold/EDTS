#!/usr/bin/env python

from __future__ import print_function
import argparse
from edtslib.cow import ColumnObjectWriter
from edtslib.dist import Lightyears
from edtslib import obscured
from edtslib import env
from edtslib import ship
from edtslib import util

def parse_args(arg, hosted, state):
  ap_parents = [env.arg_parser] if not hosted else []
  ap = argparse.ArgumentParser(description = "Recalculate next hop if jump is obscured", fromfile_prefix_chars="@", parents = ap_parents, prog = obscured.app_name)
  ap.add_argument("-d", "--min-deviation", type=int, required=False, default=obscured.default_min_deviation, help="Minimum required deviation in angle")
  ap.add_argument("-e", "--end", type=str, required=False, help="The ultimate destination system")
  ap.add_argument("-j", "--jump-range", type=float, required=False, help="The ship's max jump range with full fuel and empty cargo")
  ap.add_argument("-n", "--num", type=int, required=False, default=obscured.default_num, help="Show the specified number of candidate systems")
  ap.add_argument("-s", "--start", type=str, required=True, help="The starting system")
  ap.add_argument(      "--sort", type=str.upper, choices=[obscured.DEVIATION, obscured.DISTANCE_FROM, obscured.DISTANCE_TO], default=obscured.default_sort, help='Sort results by distance or deviation')
  ap.add_argument(      "--ship", metavar="filename", type=str, required=False, help="Load ship data from export file")
  ap.add_argument("-f", "--fsd", type=str, required=False, help="The ship's frame shift drive in the form 'A6 or '6A'")
  ap.add_argument("-m", "--mass", type=float, required=False, help="The ship's unladen mass excluding fuel")
  ap.add_argument("-t", "--tank", type=float, required=False, help="The ship's fuel tank size")
  ap.add_argument("-T", "--reserve-tank", type=float, required=False, help="The ship's reserve tank size")
  ap.add_argument(      "--fsd-optmass", type=str, help="The optimal mass of your FSD, either as a number in T or modified percentage value (including % sign)")
  ap.add_argument(      "--fsd-mass", type=str, help="The mass of your FSD, either as a number in T or modified percentage value (including % sign)")
  ap.add_argument(      "--fsd-maxfuel", type=str, help="The max fuel per jump of your FSD, either as a number in T or modified percentage value (including % sign)")
  ap.add_argument("obscured", type=str, help="The obscured system")

  parsed = ap.parse_args(arg)

  if parsed.fsd is not None and parsed.mass is not None and parsed.tank is not None:
    parsed.ship = ship.Ship.from_args(fsd = parsed.fsd, mass = parsed.mass, tank = parsed.tank, reserve_tank = parsed.reserve_tank, fsd_optmass = parsed.fsd_optmass, fsd_mass = parsed.fsd_mass, fsd_maxfuel = parsed.fsd_maxfuel)
  elif parsed.ship:
    loaded = ship.Ship.from_file(parsed.ship)
    fsd = parsed.fsd if parsed.fsd is not None else loaded.fsd
    mass = parsed.mass if parsed.mass is not None else loaded.mass
    tank = parsed.tank if parsed.tank is not None else loaded.tank_size
    reserve_tank = parsed.reserve_tank if parsed.reserve_tank is not None else loaded.reserve_tank
    parsed.ship = ship.Ship(fsd, mass, tank, reserve_tank = reserve_tank)
  elif 'ship' in state:
    fsd = parsed.fsd if parsed.fsd is not None else state['ship'].fsd
    mass = parsed.mass if parsed.mass is not None else state['ship'].mass
    tank = parsed.tank if parsed.tank is not None else state['ship'].tank_size
    reserve_tank = parsed.reserve_tank if parsed.reserve_tank is not None else state['ship'].reserve_tank
    parsed.ship = ship.Ship(fsd, mass, tank, reserve_tank = reserve_tank)
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
  results = list(obscured.Application(**vars(parsed)).run())
  if env.global_args.json:
    print(util.to_json(results))
    return
  if not len(results):
    print("")
    print("No suitable systems")
    print("")
    return

  cow = ColumnObjectWriter(6, ['<', '<', '>', '>', '>'])
  print("")
  print("Alternative systems for route from {} to {}:".format(parsed.start, parsed.end))
  print("")
  cow.add([
    '',
    'System',
    'Dev.',
    'Dist. from',
    'Dist. to'
  ])
  cow.add(['', '', ''])
  for entry in results:
    cow.add([
      ''.format(entry.system.name),
      '{}'.format(entry.system.name),
      '{:d}%'.format(min(100, int(entry.deviation))),
      '{}'.format(entry.distances.values()[0].to_string(True)),
      '{}'.format(entry.distances.values()[1].to_string(True))
    ])
  cow.add(['', '', ''])
  cow.out()

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  env.start()
  run(env.local_args)
  env.stop()
