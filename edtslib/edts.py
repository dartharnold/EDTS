#!/usr/bin/env python

from __future__ import print_function
import argparse
import math
import sys
from . import env
from . import calc
from . import ship
from . import routing as rx
from . import util
from . import solver
from .cow import ColumnObjectWriter
from .dist import Lightseconds, Lightyears
from .station import Station

app_name = "edts"

log = util.get_logger(app_name)


class Application(object):

  def __init__(self, arg, hosted, state = {}):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Elite: Dangerous TSP Solver", fromfile_prefix_chars="@", parents=ap_parents, prog = app_name)
    ap.add_argument(      "--ship", metavar="filename", type=str, required=False, help="Load ship data from export file")
    ap.add_argument("-f", "--fsd", type=str, required=False, help="The ship's frame shift drive in the form 'A6 or '6A'")
    ap.add_argument("-b", "--boost", type=str.upper, choices=['0', '1', '2', '3', 'D', 'N'], help="FSD boost level (0 for none, D for white dwarf, N for neutron")
    ap.add_argument("-m", "--mass", type=float, required=False, help="The ship's unladen mass excluding fuel")
    ap.add_argument("-t", "--tank", type=float, required=False, help="The ship's fuel tank size")
    ap.add_argument("-T", "--reserve-tank", type=float, required=False, help="The ship's reserve tank size")
    ap.add_argument(      "--starting-fuel", type=float, required=False, help="The starting fuel quantity (default: tank size)")
    ap.add_argument("-c", "--cargo", type=int, default=0, help="Cargo to collect at each station")
    ap.add_argument("-C", "--initial-cargo", type=int, default=0, help="Cargo already carried at the start of the journey")
    ap.add_argument(      "--fsd-optmass", type=str, help="The optimal mass of your FSD, either as a number in T or modified percentage value (including %% sign)")
    ap.add_argument(      "--fsd-mass", type=str, help="The mass of your FSD, either as a number in T or modified percentage value (including %% sign)")
    ap.add_argument(      "--fsd-maxfuel", type=str, help="The max fuel per jump of your FSD, either as a number in T or modified percentage value (including %% sign)")
    ap.add_argument("-j", "--jump-range", type=float, required=False, help="The ship's max jump range with full fuel and empty cargo")
    ap.add_argument("-w", "--witchspace-time", type=int, default=calc.default_ws_time, help="Time in seconds spent in hyperspace jump")
    ap.add_argument("-s", "--start", type=str, required=True, help="The starting station, in the form 'system/station' or 'system'")
    ap.add_argument("-e", "--end", type=str, required=True, help="The end station, in the form 'system/station' or 'system'")
    ap.add_argument("-n", "--num-jumps", default=None, type=int, help="The number of stations to visit, not including the start/end")
    ap.add_argument("-p", "--pad-size", default="M", type=str.upper, choices=['S','M','L'], help="The landing pad size of the ship (S/M/L)")
    ap.add_argument("-d", "--jump-decay", type=float, default=0.0, help="An estimate of the range decay per jump in LY (e.g. due to taking on cargo)")
    ap.add_argument("-r", "--route", default=False, action='store_true', help="Whether to try to produce a full route rather than just legs")
    ap.add_argument("-o", "--ordered", default=False, action='store_true', help="Whether the stations are already in a set order")
    ap.add_argument("-O", "--tour", metavar="system[/station]", action='append', type=str, nargs='*', help="Following stations must be visited in order")
    ap.add_argument("-l", "--long-jumps", default=False, action='store_true', help="Whether to allow for jumps only possible at low fuel when routing")
    ap.add_argument("-a", "--accurate", dest='route_strategy', action='store_const', const='trunkle', default=rx.default_route_strategy, help="Use a more accurate but slower routing method (equivalent to --route-strategy=trunkle)")
    ap.add_argument("-x", "--avoid", metavar='system', action='append', type=str, nargs='?', help="Reject routes that pass through named system(s)")
    ap.add_argument("--format", default='long', type=str.lower, choices=['long','summary','short','csv'], help="The format to display the output in")
    ap.add_argument("--reverse", default=False, action='store_true', help="Whether to reverse the generated route")
    ap.add_argument("--jump-time", type=float, default=calc.default_jump_time, help="Seconds taken per hyperspace jump")
    ap.add_argument("--diff-limit", type=float, default=1.5, help="The multiplier of the fastest route which a route must be over to be discounted")
    ap.add_argument("--slf", type=float, default=calc.default_slf, help="The multiplier to apply to multi-jump legs to account for imperfect system positions")
    ap.add_argument("--route-strategy", default=rx.default_route_strategy, choices=rx.route_strategies, help="The strategy to use for route plotting")
    ap.add_argument("--fuel-strategy", default=rx.default_fuel_strategy, choices=rx.fuel_strategies, help="The strategy to use for refueling")
    ap.add_argument("--rbuffer", type=float, default=rx.default_rbuffer_ly, help="A minimum buffer distance, in LY, used to search for valid stars for routing")
    ap.add_argument("--hbuffer", type=float, default=rx.default_hbuffer_ly, help="A minimum buffer distance, in LY, used to search for valid next legs. Not used by the 'astar' strategy.")
    ap.add_argument("--solve-mode", type=str, default=solver.CLUSTERED, choices=solver.modes, help="The mode used by the travelling salesman solver")
    ap.add_argument("--tolerance", type=float, default=5, help="Tolerance checking for obscured jumps")
    ap.add_argument("stations", metavar="system[/station]", nargs="*", help="A station to travel via, in the form 'system/station' or 'system'")
    self.args = ap.parse_args(arg)

    if self.args.tolerance is not None:
      if self.args.tolerance < 0 or self.args.tolerance > 100:
        log.error("Tolerance must be in range 0 to 100 (percent)!")
        sys.exit(1)

    if self.args.fsd is not None and self.args.mass is not None and self.args.tank is not None:
      # If user has provided full ship data in this invocation, use it
      # TODO: support cargo capacity?
      self.ship = ship.Ship(self.args.fsd, self.args.mass, self.args.tank)
      if self.args.fsd_optmass is not None or self.args.fsd_mass is not None or self.args.fsd_maxfuel is not None:
        fsd_optmass = util.parse_number_or_add_percentage(self.args.fsd_optmass, self.ship.fsd.stock_optmass)
        fsd_mass = util.parse_number_or_add_percentage(self.args.fsd_mass, self.ship.fsd.stock_mass)
        fsd_maxfuel = util.parse_number_or_add_percentage(self.args.fsd_maxfuel, self.ship.fsd.stock_maxfuel)
        self.ship = self.ship.get_modified(optmass=fsd_optmass, fsdmass=fsd_mass, maxfuel=fsd_maxfuel)
    elif self.args.ship:
      loaded = ship.Ship.from_file(self.args.ship)
      fsd = self.args.fsd if self.args.fsd is not None else loaded.fsd
      mass = self.args.mass if self.args.mass is not None else loaded.mass
      tank = self.args.tank if self.args.tank is not None else loaded.tank_size
      reserve_tank = self.args.reserve_tank if self.args.reserve_tank is not None else loaded.reserve_tank
      self.ship = ship.Ship(fsd, mass, tank, reserve_tank = reserve_tank)
    elif 'ship' in state:
      # If we have a cached ship, use that (with any overrides provided as part of this invocation)
      fsd = self.args.fsd if self.args.fsd is not None else state['ship'].fsd
      mass = self.args.mass if self.args.mass is not None else state['ship'].mass
      tank = self.args.tank if self.args.tank is not None else state['ship'].tank_size
      reserve_tank = self.args.reserve_tank if self.args.reserve_tank is not None else state['ship'].reserve_tank
      self.ship = ship.Ship(fsd, mass, tank, reserve_tank = reserve_tank)
    else:
      # No ship is fine as long as we have a static jump range set
      if self.args.jump_range is None:
        log.error("Error: You must specify --ship or all of --fsd, --mass and --tank and/or --jump-range.")
        sys.exit(1)
      else:
        self.ship = None
    if self.ship is not None:
      if self.args.boost:
        self.ship.supercharge(self.args.boost)
      log.debug(str(self.ship))
    else:
      if self.args.boost:
        log.error("Error: FSD boost requires --ship or all of --fsd, --mass and --tank.")
        sys.exit(1)
      log.debug("Static jump range {0:.2f}LY", self.args.jump_range)

    self.starting_fuel = self.args.starting_fuel

    # stations will always be parsed before any tours, because -O is greedy.
    if self.args.ordered:
      self.tours = [self.args.stations]
      if self.args.tour:
        for tour in self.args.tour:
          self.tours[0] += tour
    else:
      self.tours = [[station] for station in self.args.stations]
      if self.args.tour:
        self.tours += self.args.tour
    self.stations = []
    for stations in self.tours:
      self.stations += stations

    # If the user hasn't provided a number of stops to use, assume we're stopping at all provided
    if self.args.num_jumps is None:
      self.args.num_jumps = len(self.stations)

    # Systems to route around.
    self.avoid = self.args.avoid if self.args.avoid else []

  def run(self):
    timer = util.start_timer()
    with env.use() as envdata:
      start = envdata.parse_station(self.args.start)
      end = envdata.parse_station(self.args.end)

      if start is None:
        log.error("Error: start system/station {0} could not be found. Stopping.", self.args.start)
        return
      if end is None:
        log.error("Error: end system/station {0} could not be found. Stopping.", self.args.end)
        return

      # Locate all the systems/stations provided and ensure they're valid for our ship
      stations = envdata.parse_stations(self.stations)
      for sname in self.stations:
        if sname in stations and stations[sname] is not None:
          sobj = stations[sname]
          log.debug("Adding system/station: {0}", sobj.to_string())
          if self.args.pad_size == "L" and sobj.max_pad_size != "L":
            log.warning("Warning: station {0} ({1}) is not usable by the specified ship size.", sobj.name, sobj.system_name)
        else:
          log.warning("Error: system/station {0} could not be found.", sname)
          return
      avoid = []
      if len(self.avoid):
        avoid_stations = envdata.parse_stations(self.avoid)
        for sname in self.avoid:
          if sname in avoid_stations and avoid_stations[sname] is not None:
            avoid_system = avoid_stations[sname].system
            if avoid_system in [sobj.system for sobj in stations.values()] + [stn.system for stn in [start, end]]:
              log.warning("Error: Can't avoid system {0} we are supposed to visit.", sname)
              return
            avoid.append(avoid_system)
          else:
            log.warning("Warning: Blacklisted system {0} could not be found.", sname)
    # Don't just take stations.values() in case a system/station was specified multiple times
    tours = []
    for tour in self.tours:
      tours.append([stations[sname] for sname in tour])
    stations = [stations[sname] for sname in self.stations]

    # Prefer a static jump range if provided, to allow user to override ship's range
    if self.args.jump_range is not None:
      full_jump_range = self.args.jump_range
      jump_range = self.args.jump_range
    else:
      full_jump_range = self.ship.range()
      jump_range = self.ship.max_range() if self.args.long_jumps else full_jump_range

    r = rx.Routing(self.ship, self.args.rbuffer, self.args.hbuffer, self.args.route_strategy, self.args.fuel_strategy, witchspace_time=self.args.witchspace_time, starting_fuel = self.starting_fuel, jump_range = self.args.jump_range)
    s = solver.Solver(jump_range, self.args.diff_limit, witchspace_time=self.args.witchspace_time)

    if len(tours) == 1:
      route = [start] + stations + [end]
    else:
      # Add 2 to the jump count for start + end
      route, is_definitive = s.solve(tours, stations, start, end, self.args.num_jumps + 2, self.args.solve_mode)

    if self.args.reverse:
      route = [route[0]] + list(reversed(route[1:-1])) + [route[-1]]

    totaldist = 0.0
    totaldist_sl = 0.0
    totaljumps_min = 0
    totaljumps_max = 0
    totalsc = 0
    totalsc_accurate = True

    output_data = []
    total_fuel_cost = 0.0
    total_fuel_cost_exact = True

    if route is not None and len(route) > 0:
      output_data.append({'src': route[0].to_string()})

      for i in range(1, len(route)):
        cur_data = {'src': route[i-1], 'dst': route[i]}

        if self.args.jump_range is not None:
          full_max_jump = self.args.jump_range - (self.args.jump_decay * (i-1))
          cur_max_jump = full_max_jump
        else:
          full_max_jump = self.ship.range(cargo = self.args.initial_cargo + self.args.cargo * (i-1))
          cur_max_jump = self.ship.max_range(cargo = self.args.initial_cargo + self.args.cargo * (i-1)) if self.args.long_jumps else full_max_jump

        cur_data['jumpcount_min'], cur_data['jumpcount_max'] = calc.jump_count_range(route[i-1], route[i], cur_max_jump, slf=self.args.slf)
        if self.args.route:
          log.debug("Doing route plot for {0} --> {1}", route[i-1].system_name, route[i].system_name)
          if route[i-1].system != route[i].system and cur_data['jumpcount_max'] > 1:
            leg_route = r.plot(route[i-1].system, route[i].system, avoid, cur_max_jump, full_max_jump)
          else:
            leg_route = [route[i-1].system, route[i].system]

          if leg_route is not None:
            route_jcount = len(leg_route)-1
            # For hoppy routes, always use stats for the jumps reported (less confusing)
            cur_data['jumpcount_min'] = route_jcount
            cur_data['jumpcount_max'] = route_jcount
          else:
            log.warning("No valid route found for leg: {0} --> {1}", route[i-1].system_name, route[i].system_name)
            total_fuel_cost_exact = False
        else:
          total_fuel_cost_exact = False

        cur_data['legsldist'] = route[i-1].distance_to(route[i])
        totaldist_sl += cur_data['legsldist']
        totaljumps_min += cur_data['jumpcount_min']
        totaljumps_max += cur_data['jumpcount_max']
        if route[i].distance is not None and route[i].distance != 0:
          totalsc += route[i].distance
        elif route[i].name is not None:
          # Only say the SC time is inaccurate if it's actually a *station* we don't have the distance for
          totalsc_accurate = False

        cur_fuel = self.ship.tank_size if self.ship is not None else self.args.tank
        if self.args.route and leg_route is not None:
          cur_data['leg_route'] = []
          cur_data['legdist'] = 0.0
          for j in range(1, len(leg_route)):
            ldist = leg_route[j-1].distance_to(leg_route[j])
            cur_data['legdist'] += ldist
            is_long = (ldist > full_max_jump)
            fuel_cost = None
            min_tank = None
            max_tank = None
            if cur_fuel is not None:
              fuel_cost = min(self.ship.cost(ldist, cur_fuel), self.ship.fsd.maxfuel)
              min_tank, max_tank = self.ship.fuel_weight_range(ldist, self.args.initial_cargo + self.args.cargo * (i-1))
              if max_tank is not None and max_tank >= self.ship.tank_size:
                max_tank = None
              total_fuel_cost += fuel_cost
              cur_fuel -= fuel_cost
              # TODO: Something less arbitrary than this?
              if cur_fuel < 0:
                cur_fuel = self.ship.tank_size if self.ship is not None else self.args.tank
            # Write all data about this jump to the current leg info
            cur_data['leg_route'].append({
                'is_long': is_long, 'ldist': ldist,
                'src': Station.none(leg_route[j-1]), 'dst': Station.none(leg_route[j]),
                'fuel_cost': fuel_cost, 'min_tank': min_tank, 'max_tank': max_tank
            })
          totaldist += cur_data['legdist']

        if route[i].name is not None:
          cur_data['sc_time'] = "{0:.0f}".format(calc.sc_time(route[i].distance)) if (route[i].distance is not None and route[i].distance != 0) else "???"
        # Add current route to list
        output_data.append(cur_data)

      log.debug("All solving/routing finished after {}", util.format_timer(timer))

      # Get suitably formatted ETA string
      est_time_min = calc.route_time(route, totaljumps_min, witchspace_time=self.args.witchspace_time)
      est_time_min_m = math.floor(est_time_min / 60)
      est_time_min_s = int(est_time_min) % 60
      est_time_str = "{0:.0f}:{1:02.0f}".format(est_time_min_m, est_time_min_s)
      if totaljumps_min != totaljumps_max:
        est_time_max = calc.route_time(route, totaljumps_max, witchspace_time=self.args.witchspace_time)
        est_time_max_m = math.floor(est_time_max / 60)
        est_time_max_s = int(est_time_max) % 60
        est_time_str += " - {0:.0f}:{1:02.0f}".format(est_time_max_m, est_time_max_s)

      totaljumps_str = "{0:d}".format(totaljumps_max) if totaljumps_min == totaljumps_max else "{0:d} - {1:d}".format(totaljumps_min, totaljumps_max)

      print_summary = True

      if self.args.format in ['long','summary']:
        show_cruise = any([hop.name for hop in route])
        headings = ['', '', 'Distance', '', 'System']
        padding = ['<', '<', '>', '<', '<']
        intra = [' ', ' ', ' ', ' ']
        if show_cruise:
          headings += ['Cruise', '', '']
          padding += ['>', '>', '<']
          intra += ['   ', '   ', ' ', ' ']
        else:
          intra += [' ']
        headings += ['']
        padding += ['<']
        intra += ['   ']
        if self.ship is not None and self.args.route:
          headings += ['Fuel', 'Fuel', 'range']
          padding += ['<', '>', '<']
          intra += ['   ', ' ', '   ']
        headings += ['Hop', 'dist.']
        padding += ['>', '<']
        intra += [' ']
        cow = ColumnObjectWriter(len(headings), padding, intra)
        cow.add(headings)
        cow.add([])
        row = [
          '', # Obscured
          '', # Long
          '', # Distance
          '>',
          route[0].system_name
        ]
        if show_cruise:
          row += [
            Lightseconds(route[0].distance).to_string() if route[0].distance is not None else '',
            '', # Cruise time
            '{}{}'.format(route[0].name if route[0].name is not None else '', ' ({})'.format(route[0].station_type) if route[0].station_type is not None else '')
          ]
        row += ['<']
        cow.add(row)
        directions = [None, output_data[1]['src'].system, output_data[1]['dst'].system]

        # For each leg (not including start point)
        for i in range(1, len(route)):
          od = output_data[i]
          if self.args.format == 'long' and 'leg_route' in od:
            # For every jump except the last...
            for j in range(0, len(od['leg_route'])-1):
              ld = od['leg_route'][j]
              if j < len(od['leg_route']) - 2:
                nd = od['leg_route'][j + 1]
                directions = [directions[1], nd['src'].system, nd['dst'].system]
              else:
                directions = [directions[1], ld['dst'].system, route[i].system]
              cow.add([self.direction_hint(*directions) if all(directions) else ''] + self.format_leg(ld, None, show_cruise))
            # For the last jump...
            ld = od['leg_route'][-1]
            if i < len(route) - 1:
              nd = output_data[i + 1]
              if len(nd['leg_route']) > 1:
                directions = [directions[1], directions[2], nd['leg_route'][0]['dst'].system]
              else:
                directions = [directions[1], directions[2], route[i + 1].system]
            else:
              directions = [None, None, None]
            cow.add([self.direction_hint(*directions) if all(directions) else ''] + self.format_leg(ld, od, show_cruise))
          else:
            fuel_fewest = None
            fuel_most = None
            if self.ship is not None:
              # Estimate fuel cost assuming average jump size and full tank.
              fuel_fewest = self.ship.cost(od['legsldist'] / max(0.001, float(od['jumpcount_min']))) * int(od['jumpcount_min'])
              fuel_most = self.ship.cost(od['legsldist'] / max(0.001, float(od['jumpcount_max']))) * int(od['jumpcount_max'])
              total_fuel_cost += max(fuel_fewest, fuel_most)
            row = ['', '', Lightyears(od['legsldist']).to_string(True), '>', od['dst'].system_name]
            if show_cruise:
              row += self.format_cruise(od)
            else:
              row += ['<']
            fuel_str = ""
            if self.ship is not None:
              if od['jumpcount_min'] == od['jumpcount_max']:
                fuel_str = " [{0:.2f}T{1}]".format(fuel_fewest, '+' if od['jumpcount_min'] > 1 else '')
              else:
                fuel_str = " [{0:.2f}T+ - {1:.2f}T+]".format(min(fuel_fewest, fuel_most), max(fuel_fewest, fuel_most))
            if od['jumpcount_min'] == od['jumpcount_max']:
              row += [od['jumpcount_min'], 'jump{}'.format('' if od['jumpcount_min'] == 1 else 's')]
            else:
              row += ['{} - {}'.format(od['jumpcount_min'], od['jumpcount_max']), 'jumps']
            cow.add(row)
        print("")
        cow.out()

      elif self.args.format == 'short':
        print("")
        sys.stdout.write(str(route[0]))
        for i in range(1, len(route)):
          od = output_data[i]
          if 'leg_route' in od:
            for j in range(0, len(od['leg_route'])):
              ld = od['leg_route'][j]
              sys.stdout.write(", {0}".format(str(ld['dst'])))
          else:
            sys.stdout.write(", {0}".format(str(od['dst'])))
        print("")

      elif self.args.format == 'csv':
        print("{0},{1},{2},{3},".format(
              route[0].system_name,
              route[0].name if route[0].name is not None else '',
              0.0,
              route[0].distance if route[0].uses_sc and route[0].distance is not None else 0))
        directions = [None, output_data[1]['src'].system, output_data[1]['dst'].system]
        for i in range(1, len(route)):
          od = output_data[i]
          if 'leg_route' in od:
            for j in range(0, len(od['leg_route'])-1):
              ld = od['leg_route'][j]
              if j < len(od['leg_route']) - 2:
                nd = od['leg_route'][j + 1]
                directions = [directions[1], nd['src'].system, nd['dst'].system]
              else:
                directions = [directions[1], ld['dst'].system, route[i].system]
              print("{0},{1},{2},{3},{4}".format(
                    ld['dst'].system_name,
                    ld['dst'].name if ld['dst'].name is not None else '',
                    ld['ldist'],
                    ld['dst'].distance if ld['dst'].uses_sc and ld['dst'].distance is not None else 0,
                    self.direction_hint(*directions) if all(directions) else ''))
            ld = od['leg_route'][-1]
            if i < len(route) - 1:
              nd = output_data[i + 1]
              if len(nd['leg_route']) > 1:
                directions = [directions[1], directions[2], nd['leg_route'][0]['dst'].system]
              else:
                directions = [directions[1], directions[2], route[i + 1].system]
            else:
              directions = [None, None, None]
            print("{0},{1},{2},{3},{4}".format(
                  od['dst'].system_name,
                  od['dst'].name if od['dst'].name is not None else '',
                  ld['ldist'],
                  od['dst'].distance if od['dst'].uses_sc and od['dst'].distance is not None else 0,
                  self.direction_hint(*directions) if all(directions) else ''))
          else:
            print("{0},{1},{2},{3},".format(
                  od['dst'].system_name,
                  od['dst'].name if od['dst'].name is not None else '',
                  od['legsldist'],
                  od['dst'].distance if od['dst'].uses_sc and od['dst'].distance is not None else 0))
        print_summary = False

      if print_summary:
        totaldist_str = "{0:.2f}LY ({1:.2f}LY)".format(totaldist, totaldist_sl) if totaldist >= totaldist_sl else "{0:.2f}LY".format(totaldist_sl)
        fuel_str = "; fuel cost: {0:.2f}T{1}".format(total_fuel_cost, '+' if not total_fuel_cost_exact else '') if total_fuel_cost else ''
        print("")
        print("Total distance: {0}; total jumps: {1}".format(totaldist_str, totaljumps_str))
        print("Total SC distance: {0:d}Ls{1}; ETT: {2}{3}".format(totalsc, "+" if not totalsc_accurate else "", est_time_str, fuel_str))
        print("")

    else:
      print("")
      print("No viable route found :(")
      print("")

  def format_cruise(self, od):
    if od['dst'].name is not None:
      return [
        '{}'.format(Lightseconds(od['dst'].distance).to_string(True) if od['dst'].distance is not None else '???'),
        '~{}s'.format(od['sc_time'] if 'sc_time' in od else ''),
        '{}{}'.format(od['dst'].name, ' ({})'.format(od['dst'].station_type) if od['dst'].station_type is not None else ''),
        '<'
      ]
    else:
      return ['', '', '', '<']

  def format_leg(self, ld, od = None, show_cruise = True):
    row = [
      '!' if ld['is_long'] else '',
      Lightyears(ld['ldist']).to_string(True),
      '>' if od is not None else '',
      ld['dst'].system_name
    ]
    if od is not None:
      if show_cruise:
        row += self.format_cruise(od)
      else:
        row += ['<']
    else:
      if show_cruise:
        row += ['', '', '', '']
      else:
        row += ['']
    if self.ship is not None:
      row.append('{:.2f}T'.format(ld['fuel_cost']))
      if ld['max_tank'] is not None:
        row += [
        '{:.2f}-{:.2f}T'.format(
          ld['min_tank'],
          ld['max_tank']
        ),
        '({:d}-{:d}%)'.format(
          int(100.0*ld['min_tank']/self.ship.tank_size),
          int(100.0*ld['max_tank']/self.ship.tank_size)
        )
      ]
      elif ld['min_tank'] is not None:
        row += [
          '{:.2f}T'.format(ld['min_tank']),
          '({:d}%) +'.format(int(100.0*ld['min_tank']/self.ship.tank_size))
        ]
      else:
        row += ['', '']
    if od is not None:
      row += [
        Lightyears(od['legdist']).to_string(True),
        'for ' + Lightyears(od['legsldist']).to_string(True),
      ]
    else:
      row += ['', '']
    return row

  def direction_hint(self, reference, src, dst):
    v = (src.position - reference.position).get_normalised()
    w = (dst.position - reference.position).get_normalised()
    d = v.dot(w)
    if d >= 1.0 - float(self.args.tolerance) / 100:
      # Probably obscured!
      return 'X'
    elif d <= 0.0:
      # Behind.
      return 'o'
    else:
      return ''
