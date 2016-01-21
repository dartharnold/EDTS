import logging
import math
import ship
from station import Station

log = logging.getLogger("calc")

default_slf = 0.9
default_strategy = "astar"

default_ws_time = 15
jump_spool_time = 20
jump_cooldown_time = 10
default_jump_time = default_ws_time + jump_spool_time + jump_cooldown_time


class Calc(object):
  def __init__(self, ship = None, jump_range = None, witchspace_time = default_ws_time, route_strategy = default_strategy, slf = default_slf):
    self.ship = ship
    self.jump_range = jump_range
    self.sc_constant = 65
    self.sc_multiplier = 1.8
    self.sc_power = 0.5
    self.jump_witchspace_time = witchspace_time
    self.stop_outpost_time = 75
    self.stop_station_time = 90
    self.slf = slf
    self.route_strategy = route_strategy

  def jump_count(self, a, b, route, allow_long = False, cargo = 0, jump_decay = 0.0):
    _, maxjumps = self.jump_count_range(a, b, route, allow_long, cargo, jump_decay)
    return maxjumps

  # Gets an estimated range of number of jumps required to jump from a to b
  def jump_count_range(self, a, b, route, allow_long = False, cargo = 0, jump_decay = 0.0):
    if self.jump_range is not None:
      jumpdist = self.jump_range - (jump_decay * (len(route)-1))
    elif self.ship is not None:
      if allow_long:
        jumpdist = self.ship.max_range(cargo = cargo * (len(route)-1))
      else:
        jumpdist = self.ship.range(cargo = cargo * (len(route)-1))
    else:
      raise Exception("Tried to calculate jump counts without either valid ship or jump range")

    hopdist = a.distance_to(b)

    minjumps = int(math.ceil(hopdist / jumpdist))
    # If we're doing multiple jumps, apply the straight-line factor
    if hopdist > jumpdist:
      jumpdist = jumpdist * self.slf
    maxjumps = int(math.ceil(hopdist / jumpdist))
    return minjumps, maxjumps

  # Calculate the fuel cost for a route, optionally taking lowered fuel usage into account
  # Note that this method has no guards against routes beyond the tank size (i.e. negative fuel amounts)
  def route_fuel_cost(self, route, track_usage, starting_fuel = None):
    if self.ship is not None:
      cost = 0.0
      cur_fuel = starting_fuel if starting_fuel is not None else self.ship.tank_size
      for i in range(1, len(route)):
        cost += self.ship.cost(route[i-1].distance_to(route[i]), cur_fuel)
        if track_usage:
          cur_fuel -= cost
      return cost
    else:
      raise Exception("Tried to calculate route fuel cost without a valid ship")

  # An approximation of the cost (currently time taken in seconds) of doing an SC journey
  def sc_cost(self, distance):
    return self.sc_constant + (math.pow(distance, self.sc_power) * self.sc_multiplier)

  # The cost to go from a to b, as used in simple (non-routed) solving
  def solve_cost(self, a, b, route):
    hs_jumps = self.time_for_jumps(self.jump_count(a, b, route))
    hs_jdist = a.distance_to(b)
    sc = self.sc_cost(b.distance if b.uses_sc else 0.0)
    return (hs_jumps + hs_jdist + sc)

  # Gets the cumulative solve cost for a set of hops
  def solve_route_cost(self, route):
    cost = 0.0
    for i in range(0, len(route)-1):
      cost += self.solve_cost(route[i], route[i+1], route)
    return cost

  # Gets the route cost using the current route strategy
  def route_cost(self, route):
    if self.route_strategy in ["trundle", "trunkle"]:
      return self.trundle_cost(route)
    elif self.route_strategy == "astar":
      return self.astar_cost(route[0], route[-1], route)
    else:
      log.error("Invalid route strategy {0} provided".format(self.route_strategy))
      return None

  # Gets the route cost for a trundle/trunkle route
  def trundle_cost(self, route):
    # Prioritise jump count: we should always be returning the shortest route
    jump_count = (len(route)-1) * 1000
    dist = self.route_dist(route)
    if self.ship is not None:
      # If we have ship info, use the real fuel calcs to generate the cost
      # Scale the result by the FSD's maxfuel to try and keep the magnitude consistent
      var = self.ship.range() * (self.route_fuel_cost(route, False) / self.ship.fsd.maxfuel)
    else:
      # Without ship info, use the hops' standard deviation to try and generate a balanced route
      var = self.route_stdev(route, dist)
    return (jump_count + dist + var)

  # Get the cumulative actual distance of a set of jumps
  def route_dist(self, route):
    dist = 0.0
    for i in range(0, len(route)-1):
      dist += route[i+1].distance_to(route[i])
    return dist

  def route_variance(self, route, dist):
    return self._route_sd_or_var(route, dist, 2)

  def route_stdev(self, route, dist):
    return self._route_sd_or_var(route, dist, 1)

  def _route_sd_or_var(self, route, dist, power):
    if len(route) <= 1:
      return 0.0

    meanjump = dist / (len(route)-1)
    cvar = 0.0
    for i in range(0, len(route)-1):
      jdist = route[i+1].distance_to(route[i])
      cvar += math.pow((jdist - meanjump), power)
    return cvar

  # Gets the route cost for an A* route
  def astar_cost(self, a, b, route, dist_threshold = None):
    jcount = self.jump_count(a, b, route, (dist_threshold is not None))
    hs_jumps = self.time_for_jumps(jcount)
    hs_jdist = a.distance_to(b)
    var = self.route_variance(route, route[0].distance_to(route[-1]))

    penalty = 0.0
    # If we're allowing long jumps, we need to check whether to add an extra penalty
    # This is to disincentivise doing long jumps unless it's actually necessary
    if dist_threshold is not None:
      if jcount == 1 and a.distance_to(b) > dist_threshold:
        penalty += 20

      for i in range(0, len(route)-1):
        cdist = route[i+1].distance_to(route[i])
        if cdist > dist_threshold:
          penalty += 20

    return (hs_jumps + hs_jdist + var + penalty)

  # Gets the time taken to do an SC journey (defaulting to 0.0 for non-stations)
  def sc_time(self, stn):
    if isinstance(stn, Station) and stn.name is not None:
      return self.sc_cost(stn.distance if stn.distance is not None else 0.0)
    else:
      return 0.0

  # Gets a very rough approximation of the time taken to stop at a starport/outpost
  def station_time(self, stn):
    if isinstance(stn, Station) and stn.name is not None:
      if stn.max_pad_size == 'L':
        return self.stop_station_time
      else:
        return self.stop_outpost_time
    else:
      return 0.0

  def time_for_jumps(self, jump_count):
    return max(0.0, ((jump_spool_time + self.jump_witchspace_time) * jump_count) + (jump_cooldown_time * (jump_count - 1)))

  # Gets the full time taken to traverse a route
  def route_time(self, route, jump_count):
    hs_t = self.time_for_jumps(jump_count)
    sc_t = sum(self.sc_time(stn) for stn in route[1:])
    stn_t = sum(self.station_time(stn) for stn in route)

    log.debug("hs_time = {0:.2f}, sc_time = {1:.2f}, stn_time = {2:.2f}".format(hs_t, sc_t, stn_t))

    return (hs_t + sc_t + stn_t)
