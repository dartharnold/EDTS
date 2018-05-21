#!/usr/bin/env python

from __future__ import print_function
import argparse
from edtslib.cow import ColumnObjectWriter
from edtslib import calc
from edtslib import edts
from edtslib import env
from edtslib import routing as rx
from edtslib import ship
from edtslib import solver
from edtslib import util
import math
import sys

class ApplicationAction(argparse.Action):
  def __call__(self, parser, namespace, value, option_strings=None):
    n = vars(namespace)
    route_set = n['route_set'] if n['route_set'] is not None else []
    need_new = True
    i = 0
    while i < len(route_set):
      if ('destinations' if self.dest == 'route_set' else self.dest) not in route_set[i]:
        need_new = False
        break
      i += 1
    if need_new:
      route_set.append({})
    d = route_set[i]
    if self.dest == 'route_set':
      if 'destinations' not in d:
        d['destinations'] = value
      else:
        d['destinations'] += value
    else:
      if self.dest == 'route_set_min':
        key = 'min'
      elif self.dest == 'route_set_max':
        key = 'max'
      d[key] = value
      setattr(namespace, self.dest, value)
    setattr(namespace, 'route_set', route_set)

def parse_args(arg, hosted, state):
  ap_parents = [env.arg_parser] if not hosted else []
  ap = argparse.ArgumentParser(description = "Elite: Dangerous TSP Solver", fromfile_prefix_chars="@", parents=ap_parents, prog = edts.app_name)
  ap.add_argument(      "--ship", metavar="filename", type=str, required=False, help="Load ship data from export file")
  ap.add_argument("-f", "--fsd", type=str, required=False, help="The ship's frame shift drive in the form 'A6 or '6A'")
  ap.add_argument("-b", "--boost", type=str.upper, choices=['0', '1', '2', '3', 'D', 'N'], help="FSD boost level (0 for none, D for white dwarf, N for neutron")
  ap.add_argument("-m", "--mass", type=float, required=False, help="The ship's unladen mass excluding fuel")
  ap.add_argument("-t", "--tank", type=float, required=False, help="The ship's fuel tank size")
  ap.add_argument("-T", "--reserve-tank", type=float, required=False, help="The ship's reserve tank size")
  ap.add_argument(      "--starting-fuel", type=float, required=False, help="The starting fuel quantity (default: tank size)")
  ap.add_argument("-c", "--cargo", type=int, default=edts.default_cargo, help="Cargo to collect at each station")
  ap.add_argument("-C", "--initial-cargo", type=int, default=edts.default_initial_cargo, help="Cargo already carried at the start of the journey")
  ap.add_argument(      "--fsd-optmass", type=str, help="The optimal mass of your FSD, either as a number in T or modified percentage value (including %% sign)")
  ap.add_argument(      "--fsd-mass", type=str, help="The mass of your FSD, either as a number in T or modified percentage value (including %% sign)")
  ap.add_argument(      "--fsd-maxfuel", type=str, help="The max fuel per jump of your FSD, either as a number in T or modified percentage value (including %% sign)")
  ap.add_argument("-j", "--jump-range", type=float, required=False, help="The ship's max jump range with full fuel and empty cargo")
  ap.add_argument("-w", "--witchspace-time", type=int, default=edts.default_ws_time, help="Time in seconds spent in hyperspace jump")
  ap.add_argument("-s", "--start", type=str, required=False, help="The starting station, in the form 'system/station' or 'system'")
  ap.add_argument("-e", "--end", type=str, required=False, help="The end station, in the form 'system/station' or 'system'")
  ap.add_argument("-n", "--num-jumps", default=None, type=int, help="The number of stations to visit, not including the start/end")
  ap.add_argument("-p", "--pad-size", default=edts.default_pad_size, type=str.upper, choices=['S','M','L'], help="The landing pad size of the ship (S/M/L)")
  ap.add_argument("-d", "--jump-decay", type=float, default=edts.default_jump_decay, help="An estimate of the range decay per jump in LY (e.g. due to taking on cargo)")
  ap.add_argument("-r", "--route", default=False, action='store_true', help="Whether to try to produce a full route rather than just legs")
  ap.add_argument("--route-filters", required=False, metavar='filter', nargs='*', help="Only travel via systems that match the filters")
  ap.add_argument("-o", "--ordered", default=False, action='store_true', help="Whether the stations are already in a set order")
  ap.add_argument("-O", "--tour", metavar="system[/station]", action='append', type=str, nargs='*', help="Following stations must be visited in order")
  ap.add_argument("-R", "--route-set", metavar="system[/station]", nargs='+', action=ApplicationAction, help="Choose a subset of the following stations")
  ap.add_argument(      "--route-set-min", type=int, default=1, action=ApplicationAction, help="Minimum number of stations to visit in the --route-set.")
  ap.add_argument(      "--route-set-max", type=int, default=1, action=ApplicationAction, help="Maximum number of stations to visit in the --route-set.")
  ap.add_argument("-l", "--long-jumps", default=False, action='store_true', help="Whether to allow for jumps only possible at low fuel when routing")
  ap.add_argument("-a", "--accurate", dest='route_strategy', action='store_const', const='trunkle', default=edts.default_route_strategy, help="Use a more accurate but slower routing method (equivalent to --route-strategy=trunkle)")
  ap.add_argument("-x", "--avoid", metavar='system', action='append', type=str, nargs='?', help="Reject routes that pass through named system(s)")
  ap.add_argument("--format", default='long', type=str.lower, choices=['long','summary','short','csv'], help="The format to display the output in")
  ap.add_argument("--reverse", default=False, action='store_true', help="Whether to reverse the generated route")
  ap.add_argument("--diff-limit", type=float, default=edts.default_diff_limit, help="The multiplier of the fastest route which a route must be over to be discounted")
  ap.add_argument("--slf", type=float, default=edts.default_slf, help="The multiplier to apply to multi-jump legs to account for imperfect system positions")
  ap.add_argument("--route-strategy", default=edts.default_route_strategy, choices=rx.route_strategies, help="The strategy to use for route plotting")
  ap.add_argument("--fuel-strategy", default=edts.default_fuel_strategy, choices=rx.fuel_strategies, help="The strategy to use for refueling")
  ap.add_argument("--rbuffer", type=float, default=edts.default_rbuffer, help="A minimum buffer distance, in LY, used to search for valid stars for routing")
  ap.add_argument("--hbuffer", type=float, default=edts.default_hbuffer, help="A minimum buffer distance, in LY, used to search for valid next legs. Not used by the 'astar' strategy.")
  ap.add_argument("--solve-mode", type=str, default=edts.default_solve_mode, choices=solver.modes, help="The mode used by the travelling salesman solver")
  ap.add_argument("--tolerance", type=float, default=edts.default_tolerance, help="Tolerance checking for obscured jumps")
  ap.add_argument("stations", metavar="system[/station]", nargs="*", help="A station to travel via, in the form 'system/station' or 'system'")

  parsed = ap.parse_args(arg)

  if parsed.fsd is not None and parsed.mass is not None and parsed.tank is not None:
    # If user has provided full ship data in this invocation, use it
    # TODO: support cargo capacity?
    parsed.ship = ship.Ship.from_args(fsd = parsed.fsd, mass = parsed.mass, tank = parsed.tank, reserve_tank = parsed.reserve_tank, fsd_optmass = parsed.fsd_optmass, fsd_mass = parsed.fsd_mass, fsd_maxfuel = parsed.fsd_maxfuel)
  elif parsed.ship:
    loaded = ship.Ship.from_file(parsed.ship)
    fsd = parsed.fsd if parsed.fsd is not None else loaded.fsd
    mass = parsed.mass if parsed.mass is not None else loaded.mass
    tank = parsed.tank if parsed.tank is not None else loaded.tank_size
    reserve_tank = parsed.reserve_tank if parsed.reserve_tank is not None else loaded.reserve_tank
    parsed.ship = ship.Ship(fsd, mass, tank, reserve_tank = reserve_tank)
  elif 'ship' in state:
    # If we have a cached ship, use that (with any overrides provided as part of this invocation)
    fsd = parsed.fsd if parsed.fsd is not None else state['ship'].fsd
    mass = parsed.mass if parsed.mass is not None else state['ship'].mass
    tank = parsed.tank if parsed.tank is not None else state['ship'].tank_size
    reserve_tank = parsed.reserve_tank if parsed.reserve_tank is not None else state['ship'].reserve_tank
    parsed.ship = ship.Ship(fsd, mass, tank, reserve_tank = reserve_tank)
  else:
    parsed.ship = None

  return parsed

def direction_hint(entry):
  hint = ''
  if entry.behind is not None:
    if entry.behind:
      hint = 'o'
  if entry.obscured is not None:
    if entry.obscured:
      hint = 'X'
  return hint

def format_leg(entry, show_cruise = False, show_route = False, show_jumps = True, show_fuel = False):
  row = [
    direction_hint(entry),
    '!' if entry.is_long else '',
    entry.distance.to_string(True),
    '>' if entry.waypoint is not None else '',
    entry.destination.system.name
  ]

  if show_cruise:
    if entry.destination.station is not None:
      row += [
        entry.destination.station.distance.to_string() if entry.destination.station.distance is not None else '???',
        '~{}s'.format(int(entry.waypoint.time.cruise)) if entry.waypoint is not None else '',
        entry.destination.station.name,
        entry.destination.station.station_type if entry.destination.station.station_type is not None else ''
      ]
    else:
      row += ['', '', '', '']
  row += ['<' if entry.waypoint is not None else '']

  if show_fuel:
    if entry.fuel is not None:
      row += ['{:.2f}T'.format(entry.fuel.cost) if entry.fuel.cost is not None else '']
      if entry.fuel.max is not None:
        row += [
          '{:.2f}-{:.2f}T'.format(
            entry.fuel.min,
            entry.fuel.max
          ),
          '({:d}-{:d}%)'.format(
            int(entry.fuel_percent.min),
            int(entry.fuel_percent.max),
          )
        ]
      elif entry.fuel.min is not None:
        row += [
          '{:.2f}T'.format(entry.fuel.min),
          '({:d}%) +'.format(int(entry.fuel_percent.min))
        ]
      else:
        row += ['', '']

  if show_jumps:
    if entry.waypoint is not None:
      row += [
        entry.waypoint.distance.to_string(True),
        'for ' + entry.waypoint.direct.to_string(True)
      ]
      if entry.waypoint.jumps.min == entry.waypoint.jumps.max:
        row += [entry.waypoint.jumps.min]
      else:
        row += ['{} - {}'.format(
          entry.waypoint.jumps.min,
          entry.waypoint.jumps.max
        )]
    else:
      row += ['', '', '']

  return row

def run(args, hosted = False, state = {}):
  parsed = parse_args(args, hosted, state)
  results = list(edts.Application(**vars(parsed)).run())
  if env.global_args.json:
    print(util.to_json(results))
    return
  if not len(results):
    print("")
    print("No viable route found :(")
    print("")
    return

  print_summary = True
  show_cruise = False
  show_route = False
  show_jumps = parsed.ship is not None or parsed.jump_range is not None

  for entry in results:
    if entry.origin.station is not None or entry.destination.station is not None:
      show_cruise = True
    if not entry.summary:
      show_route = True
    if show_cruise and show_route:
      break

  origin = results[0].origin
  cow = None

  if parsed.format in ['long','summary']:
    headings = ['', '', 'Distance', '', 'System']
    padding = ['<', '<', '>', '<', '<']
    intra = [' ', ' ', ' ', ' ']
    if show_cruise:
      headings += ['Cruise', '', '', '']
      padding += ['>', '>', '<', '<']
      intra += ['   ', '   ', ' ', '  ', ' ']
    else:
      intra += [' ']
    headings += ['']
    padding += ['<']
    intra += ['   ']
    if parsed.ship is not None and show_route:
      headings += ['Fuel', 'Fuel', 'range']
      padding += ['<', '>', '<']
      intra += ['   ', ' ', '   ']
    if show_jumps:
      headings += ['Hop', 'dist.', 'Jumps']
      padding += ['>', '<', '>']
      intra += [' ', '  ']
    cow = ColumnObjectWriter(len(headings), padding, intra)
    cow.add(headings)
    cow.add([])
    row = [
      '', # Obscured
      '', # Long
      '', # Distance
      '>',
      origin.system.name
    ]
    if show_cruise:
      row += [
        origin.station.distance.to_string() if origin.station is not None and origin.station.distance is not None else '',
        '', # Cruise time
        origin.station.name if origin.station is not None else '',
        origin.station.station_type if origin.station is not None and origin.station.station_type is not None else ''
      ]
    row += ['<']
    cow.add(row)
  elif parsed.format == 'short':
    print("")
    sys.stdout.write(str(origin.station) if origin.station is not None else origin.system.name)
  elif parsed.format == 'csv':
    print(','.join([
      origin.system.name,
      origin.station.name if origin.station is not None else '',
      str(0.0),
      origin.station.distance.to_string() if origin.station is not None and origin.station.distance is not None else '',
      ''
    ]))
    print_summary = False

  totaldist = 0.0
  totaldist_sl = 0.0
  totaljumps_min = 0
  totaljumps_max = 0
  total_fuel_cost = 0.0
  totalsc = 0
  totalsc_accurate = True
  est_time_min = 0
  est_time_max = 0
  for entry in results[1:]:
    if entry.waypoint is not None:
      totaldist += entry.waypoint.distance.lightyears
      totaldist_sl += entry.waypoint.direct.lightyears
      totaljumps_min += entry.waypoint.jumps.min
      totaljumps_max += entry.waypoint.jumps.max
      totalsc_accurate &= entry.waypoint.time.accurate
      if entry.destination.station is not None:
        if entry.destination.station.distance is not None:
          totalsc += entry.destination.station.distance.lightseconds
      if entry.waypoint.time.jumps is not None:
        est_time_min += entry.waypoint.time.jumps.min
        est_time_max += entry.waypoint.time.jumps.max
      if entry.waypoint.time.cruise is not None:
        est_time_min += entry.waypoint.time.cruise
        est_time_max += entry.waypoint.time.cruise
    if entry.fuel is not None and entry.fuel.cost is not None:
      total_fuel_cost += entry.fuel.cost
    if cow is not None:
      cow.add(format_leg(entry, show_cruise, show_route, show_jumps, parsed.ship is not None))
    elif parsed.format == 'short':
      sys.stdout.write(', {}'.format(str(entry.destination.station) if entry.destination.station is not None else str(entry.destination.system)))
    elif parsed.format == 'csv':
      print(','.join([
        entry.destination.system.name,
        entry.destination.station.name if entry.destination.station is not None else '',
        str(entry.distance.lightyears),
        str(entry.destination.station.distance) if entry.destination.station is not None and entry.destination.station.distance is not None else '',
        direction_hint(entry)
      ]))

  if cow is not None:
    cow.out()
  elif parsed.format == 'short':
    print("")

  if print_summary:
    totaldist_str = "{:.2f}LY ({:.2f}LY)".format(totaldist, totaldist_sl) if totaldist >= totaldist_sl else "{:.2f}LY".format(totaldist_sl)
    totaljumps_str = "{:d}".format(totaljumps_max) if totaljumps_min == totaljumps_max else "{:d} - {:d}".format(totaljumps_min, totaljumps_max)
    fuel_str = "; fuel cost: {:.2f}T".format(total_fuel_cost) if total_fuel_cost else ''
    est_time_min_m = math.floor(est_time_min / 60)
    est_time_min_s = int(est_time_min) % 60
    est_time_str = "{:.0f}:{:02.0f}".format(est_time_min_m, est_time_min_s)
    if totaljumps_min != totaljumps_max:
      est_time_max_m = math.floor(est_time_max / 60)
      est_time_max_s = int(est_time_max) % 60
      est_time_str += " - {:.0f}:{:02.0f}".format(est_time_max_m, est_time_max_s)
    print("")
    if show_jumps:
      print("Total distance: {}; total jumps: {}".format(totaldist_str, totaljumps_str))
      print("Total SC distance: {:d}Ls{}; ETT: {}{}".format(int(totalsc), "+" if not totalsc_accurate else "", est_time_str, fuel_str))
    else:
      print("Total distance: {}".format(totaldist_str))
  print("")

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  env.start()
  run(env.local_args)
  env.stop()
