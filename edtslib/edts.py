#!/usr/bin/env python

from __future__ import print_function
from .opaque_types import Opaq
from . import env
from . import calc
from . import filtering
from . import ship
from . import routing as rx
from . import util
from . import solver
from .cow import ColumnObjectWriter
from .dist import Lightseconds, Lightyears
from .station import Station
from .system_internal import System
from .opaque_types import Fuel, Jumps, Location, WaypointTime, Waypoint

app_name = "edts"

log = util.get_logger(app_name)

default_cargo = 0
default_diff_limit = 1.5
default_fuel_strategy = rx.default_fuel_strategy
default_hbuffer = rx.default_hbuffer_ly
default_initial_cargo = 0
default_jump_decay = 0.0
default_pad_size = 'M'
default_rbuffer = rx.default_rbuffer_ly
default_route_strategy = rx.default_route_strategy
default_slf = calc.default_slf
default_solve_mode = solver.CLUSTERED
default_tolerance = 5
default_ws_time = calc.default_ws_time

class Result(Opaq):
  def __init__(self, **args):
    self.destination = args.get('destination')
    self.origin = args.get('origin', self.destination)
    self.distance = args.get('distance', Lightyears(0))
    self.obscured = args.get('obscured', False)
    self.behind = args.get('behind', False)
    self.fuel = args.get('fuel', Fuel())
    self.fuel_percent = args.get('fuel_percent', Fuel())
    self.jumps = args.get('jumps', Jumps())
    self.is_long = args.get('is_long', False)
    self.ok = args.get('ok', True)
    self.summary = args.get('summary', False)
    self.waypoint = args.get('waypoint', False)

class Application(object):

  def __init__(self, **args):
    self._avoid = args.get('avoid')
    self._boost = args.get('boost')
    self._cargo = args.get('cargo', default_cargo)
    self._diff_limit = args.get('diff_limit', default_diff_limit)
    self._end = args.get('end')
    self._fuel_strategy = args.get('fuel_strategy', default_fuel_strategy)
    self._hbuffer = args.get('hbuffer', default_hbuffer)
    self._initial_cargo = args.get('initial_cargo', default_initial_cargo)
    self._jump_decay = args.get('jump_decay', default_jump_decay)
    self._jump_range = args.get('jump_range')
    self._long_jumps = args.get('long_jumps')
    self._num_jumps = args.get('num_jumps')
    self._ordered = args.get('ordered')
    self._pad_size = args.get('pad_size', default_pad_size)
    self._rbuffer = args.get('rbuffer', default_rbuffer)
    self._reverse = args.get('reverse')
    self._route = args.get('route')
    self._route_filters = args.get('route_filters')
    self._route_set = args.get('route_set')
    self._route_strategy = args.get('route_strategy', default_route_strategy)
    self._slf = args.get('slf', default_slf)
    self._solve_mode = args.get('solve_mode', default_solve_mode)
    self._ship = args.get('ship')
    self._tank = args.get('tank')
    self._start = args.get('start')
    self._starting_fuel = args.get('starting_fuel')
    self._stations = args.get('stations', [])
    self._tour = args.get('tour')
    self._tolerance = args.get('tolerance', default_tolerance)
    self._witchspace_time = args.get('witchspace_time', default_ws_time)

    if self._tolerance is not None:
      if self._tolerance < 0 or self._tolerance > 100:
        raise RuntimeError("Tolerance must be in range 0 to 100 (percent)!")

    if self._ship is not None:
      if self._boost:
        self._ship.supercharge(self._boost)
      log.debug(str(self._ship))
    else:
      # No ship is fine as long as we have a static jump range set
      if self._jump_range is None:
        if self._route:
          raise RuntimeError("Error: You must specify --ship or all of --fsd, --mass and --tank and/or --jump-range.")
        else:
          self._ship = ship.HeartOfGold()
      else:
        self._ship = None
        if self._tank is not None:
          log.info('Ignoring tank with explicit jump range.')
          self._tank = None

      if self._boost:
        raise RuntimeError("Error: FSD boost requires --ship or all of --fsd, --mass and --tank.")
      log.debug("Static jump range {0:.2f}LY", self._jump_range)

    self.starting_fuel = self._starting_fuel

    # stations will always be parsed before any tours, because -O is greedy.
    if self._ordered:
      self.tours = [self._stations]
      if self._tour:
        for tour in self._tour:
          self.tours[0] += tour
    else:
      self.tours = [[station] for station in self._stations]
      if self._tour:
        self.tours += self._tour
    self.stations = []
    for stations in self.tours:
      self.stations += stations

    # Route sets.
    if self._route_set is not None:
      for route_set in self._route_set:
        self.stations += route_set['destinations']

    # If the user hasn't provided a number of stops to use, assume we're stopping at all provided
    if self._num_jumps is None:
      self._num_jumps = len(self.stations)
      if self._route_set is not None:
        self._num_jumps += sum([route_set.get('min', 1) for route_set in self._route_set]) - sum([len(route_set['destinations']) for route_set in self._route_set])

    # Systems to route around.
    self.avoid = self._avoid if self._avoid else []

  def run(self):
    timer = util.start_timer()
    with env.use() as envdata:
      envdata.find_filtered_systems_from_edsm(self._route_filters)
      route_filters = filtering.entry_separator.join(self._route_filters) if self._route_filters is not None else None
      sysstats = [envdata.parse_station(name, True) for name in ([self._start, self._end] + self.stations + self.avoid) if name is not None]
      envdata.find_systems_from_edsm(sysstat[0] for sysstat in sysstats)
      envdata.find_stations_in_systems_from_edsm(sysstat[0] for sysstat in sysstats if sysstat[1] is not None)
      anywhere = Station.none(System(float('inf'), float('inf'), float('inf'), 'Anywhere'))
      start = envdata.parse_station(self._start) if self._start is not None else anywhere
      end = envdata.parse_station(self._end) if self._end is not None else anywhere

      if start is None:
        log.error("Error: start system/station {0} could not be found. Stopping.", self._start)
        return
      if end is None:
        log.error("Error: end system/station {0} could not be found. Stopping.", self._end)
        return

      # Locate all the systems/stations provided and ensure they're valid for our ship
      stations = envdata.parse_stations(self.stations)
      for sname in self.stations:
        if sname in stations and stations[sname] is not None:
          sobj = stations[sname]
          log.debug("Adding system/station: {0}", sobj.to_string())
          if self._pad_size == "L" and sobj.max_pad_size != "L":
            log.warning("Warning: station {0} ({1}) is not usable by the specified ship size.", sobj.name, sobj.system_name)
        else:
          log.warning("Error: system/station {0} could not be found.", sname)
          return
      route_sets = [solver.RouteSet(stations = [stations[sname] for sname in route_set['destinations']], min = route_set.get('min'), max = route_set.get('max')) for route_set in self._route_set] if self._route_set is not None else []
      avoid = []
      if len(self.avoid):
        avoid_stations = envdata.parse_stations(self.avoid)
        for sname in self.avoid:
          if sname in avoid_stations and avoid_stations[sname] is not None:
            avoid_system = avoid_stations[sname].system
            if avoid_system in [sobj.system for sobj in stations.values()] + [stn.system for stn in [start, end]] + [sobj.system for sobj in route_set.stations for route_set in route_sets]:
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

    if len(list(filter(lambda stn: stn != anywhere, [start, end] + stations))) < 2:
      log.error('Not enough stations to form a route!')
      return

    # Prefer a static jump range if provided, to allow user to override ship's range
    if self._jump_range is not None:
      full_jump_range = self._jump_range
      jump_range = self._jump_range
    else:
      full_jump_range = self._ship.range()
      jump_range = self._ship.max_range() if self._long_jumps else full_jump_range

    r = rx.Routing(self._ship, self._rbuffer, self._hbuffer, self._route_strategy, self._fuel_strategy, witchspace_time=self._witchspace_time, starting_fuel = self.starting_fuel, jump_range = self._jump_range)
    s = solver.Solver(jump_range, self._diff_limit, witchspace_time=self._witchspace_time)

    if len(tours) == 1:
      route = [start] + stations + [end]
    else:
      # Add 2 to the jump count for start + end
      route, is_definitive = s.solve(stations, start, end, self._num_jumps + 2, preferred_mode = self._solve_mode, route_sets = route_sets, tours = tours)

    if route is not None:
      route = [stn for stn in route if stn != anywhere]

      if self._reverse:
        route = [route[0]] + list(reversed(route[1:-1])) + [route[-1]]

    output_data = []
    total_fuel_cost = 0.0

    if route is not None and len(route) > 0:
      output_data.append({'src': route[0].to_string()})

      for i in range(1, len(route)):
        cur_data = {'src': route[i-1], 'dst': route[i]}
        cargo = self._initial_cargo + self._cargo * (i-1)

        if self._jump_range is not None:
          full_max_jump = self._jump_range - (self._jump_decay * (i-1))
          cur_max_jump = full_max_jump
        else:
          full_max_jump = self._ship.range(cargo = cargo)
          cur_max_jump = self._ship.max_range(cargo = cargo) if self._long_jumps else full_max_jump

        cur_data['jumpcount_min'], cur_data['jumpcount_max'] = calc.jump_count_range(route[i-1], route[i], cur_max_jump, slf=self._slf)
        if self._route:
          envdata.find_intermediate_systems_from_edsm(route[i-1].system.position, route[i].system.position)
          log.debug("Doing route plot for {0} --> {1}", route[i-1].system_name, route[i].system_name)
          if route[i-1].system != route[i].system and cur_data['jumpcount_max'] > 1:
            leg_route = r.plot(route[i-1].system, route[i].system, avoid, cur_max_jump, full_max_jump, cargo, route_filters)
          else:
            leg_route = [route[i-1].system, route[i].system]

          if leg_route is not None:
            route_jcount = len(leg_route)-1
            # For hoppy routes, always use stats for the jumps reported (less confusing)
            cur_data['jumpcount_min'] = route_jcount
            cur_data['jumpcount_max'] = route_jcount
          else:
            log.warning("No valid route found for leg: {0} --> {1}", route[i-1].system_name, route[i].system_name)

        cur_data['legsldist'] = route[i-1].distance_to(route[i])

        cur_fuel = self._ship.tank_size if self._ship is not None else self._tank
        if self._route and leg_route is not None:
          cur_data['leg_route'] = []
          cur_data['legdist'] = 0.0
          for j in range(1, len(leg_route)):
            ldist = leg_route[j-1].distance_to(leg_route[j])
            cur_data['legdist'] += ldist
            is_long = (ldist > full_max_jump)
            fuel_cost = None
            min_tank = None
            max_tank = None
            initial_fuel = None
            final_fuel = None
            if cur_fuel is not None:
              fuel_cost = min(self._ship.cost(ldist, cur_fuel), self._ship.fsd.maxfuel)
              min_tank, max_tank = self._ship.fuel_weight_range(ldist, self._initial_cargo + self._cargo * (i-1))
              if max_tank is not None and max_tank >= self._ship.tank_size:
                max_tank = None
              total_fuel_cost += fuel_cost
              initial_fuel = cur_fuel
              cur_fuel -= fuel_cost
              final_fuel = cur_fuel
              # TODO: Something less arbitrary than this?
              if cur_fuel < 0:
                cur_fuel = self._ship.tank_size if self._ship is not None else self._tank
            # Write all data about this jump to the current leg info
            cur_data['leg_route'].append({
                'is_long': is_long, 'ldist': ldist,
                'src': Station.none(leg_route[j-1]), 'dst': Station.none(leg_route[j]),
                'fuel_cost': fuel_cost, 'min_tank': min_tank, 'max_tank': max_tank,
                'initial_fuel': initial_fuel, 'final_fuel': final_fuel,
                'fuel_cost_percent': self._ship.refuel_percent(fuel_cost) if self._ship is not None else None,
                'min_tank_percent': self._ship.refuel_percent(min_tank) if self._ship is not None else None,
                'max_tank_percent': self._ship.refuel_percent(max_tank) if self._ship is not None and max_tank is not None else None,
                'initial_fuel_percent': self._ship.refuel_percent(initial_fuel) if self._ship is not None else None,
                'final_fuel_percent': self._ship.refuel_percent(final_fuel) if self._ship is not None else None,
            })

        if route[i].name is not None:
          cur_data['sc_time'] = calc.sc_time(route[i].distance.lightseconds) if (route[i].distance.lightseconds is not None and route[i].distance.lightseconds != 0) else None
          cur_data['sc_time_accurate'] = (cur_data['sc_time'] is not None)
        else:
          cur_data['sc_time'] = None
          cur_data['sc_time_accurate'] = True
        cur_data['jump_time_min'] = calc.route_time([Station.none(route[i-1]), Station.none(route[i])], cur_data['jumpcount_min'], witchspace_time = self._witchspace_time)
        cur_data['jump_time_max'] = cur_data['jump_time_min'] if cur_data['jumpcount_max'] == cur_data['jumpcount_min'] else calc.route_time([Station.none(route[i-1]), Station.none(route[i])], cur_data['jumpcount_max'], witchspace_time = self._witchspace_time)
        # Add current route to list
        output_data.append(cur_data)

      log.debug("All solving/routing finished after {}", util.format_timer(timer))

      summary = not self._route
      directions = [None, output_data[1]['src'].system, output_data[1]['dst'].system]
      for i in range(1, len(route)):
        od = output_data[i]
        wp = Waypoint(direct = Lightyears(od['legsldist']), distance = Lightyears(od['legsldist']), jumps = Jumps(min = od['jumpcount_min'], max = od['jumpcount_max']), time = WaypointTime(accurate = od['sc_time_accurate'], cruise = od['sc_time'], jumps = Jumps(min = od['jump_time_min'], max = od['jump_time_max'])))
        if i == 1:
          yield Result(
            origin = Location(system = od['src'].system, station = od['src'] if od['src'].name is not None else None),
            destination = Location(system = od['src'].system, station = od['src'] if od['src'].name is not None else None),
            summary = summary,
            waypoint = Waypoint()
          )
        if 'leg_route' in od:
          last_leg = len(od['leg_route']) - 1
          for j in range(0, len(od['leg_route'])):
            ld = od['leg_route'][j]
            if j == last_leg:
              waypoint = wp
              waypoint.distance = Lightyears(od['legdist'])
              destination_station = od['dst']
            else:
              waypoint = None
              destination_station = ld['dst']
            if j == 0:
              origin_station = od['src']
            else:
              origin_station = ld['src']
            if j < last_leg - 1:
              nd = od['leg_route'][j + 1]
              directions = [directions[1], nd['src'].system, nd['dst'].system]
            else:
              directions = [directions[1], ld['dst'].system, route[i].system]
            direction = self.direction_hint(*directions) if all(directions) else ''
            yield Result(
              origin = Location(system = ld['src'].system, station = origin_station if origin_station.name is not None else None),
              destination = Location(system = ld['dst'].system, station = destination_station if destination_station.name is not None else None),
              distance = Lightyears(ld['ldist']),
              direct = ldist,
              fuel = Fuel(min = ld['min_tank'], max = ld['max_tank'], cost = ld['fuel_cost'], initial = ld['initial_fuel'], final = ld['final_fuel']),
              fuel_percent = Fuel(min = ld['min_tank_percent'], max = ld['max_tank_percent'], cost = ld['fuel_cost_percent'], initial = ld['initial_fuel_percent'], final = ld['final_fuel_percent']),
              is_long = ld['is_long'],
              waypoint = waypoint,
              obscured = (direction == 'X'),
              behind = (direction == 'o')
            )
        else:
          yield Result(origin = Location(system = od['src'].system, station = od['src'] if od['src'].name is not None else None), destination = Location(system = od['dst'].system, station = od['dst'] if od['dst'].name is not None else None), distance = wp.direct, fuel = None, summary = summary, waypoint = wp)

  def direction_hint(self, reference, src, dst):
    v = (src.position - reference.position).get_normalised()
    w = (dst.position - reference.position).get_normalised()
    d = v.dot(w)
    if d >= 1.0 - float(self._tolerance) / 100:
      # Probably obscured!
      return 'X'
    elif d <= 0.0:
      # Behind.
      return 'o'
    else:
      return ''
