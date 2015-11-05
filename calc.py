import logging
import math
from station import Station
  
log = logging.getLogger("calc")

class Calc:
  def __init__(self, args, fsd):
    self.args = args
    self.fsd = fsd
    self.sc_constant = 65
    self.sc_multiplier = 1.8
    self.sc_power = 0.5
    self.jump_spool_time = 20
    self.jump_witchspace_time = 15
    self.jump_cooldown_time = 10
    self.stop_outpost_time = 75
    self.stop_station_time = 90

  def jump_count(self, a, b, route, allow_long = False):
    if self.fsd is not None:
      if allow_long:
        jumpdist = self.fsd.max_range(self.args.mass, self.args.cargo * (len(route)-1))
      else:
        jumpdist = self.fsd.range(self.args.mass, self.args.tank, self.args.cargo * (len(route)-1))
    else:
      jumpdist = self.args.jump_range - (self.args.jump_decay * (len(route)-1))
    hopdist = (a.position - b.position).length
    # If we're doing multiple jumps, apply the SLF
    if hopdist > jumpdist:
      jumpdist = jumpdist * self.args.slf
    return int(math.ceil(hopdist / jumpdist))

  def sc_cost(self, distance):
    return self.sc_constant + (math.pow(distance, self.sc_power) * self.sc_multiplier)
	
  def solve_cost(self, a, b, route):
    hs_jumps = self.time_for_jumps(self.jump_count(a, b, route))
    hs_jdist = (a.position - b.position).length
    sc = self.sc_cost(b.distance) if b.uses_sc else 0.0
    return (hs_jumps + hs_jdist + sc)

  def solve_route_cost(self, route):
    cost = 0.0
    for i in xrange(0, len(route)-1):
      cost += self.solve_cost(route[i], route[i+1], route)
    return cost

  def route_cost(self, route):
    if self.args.route_strategy == "trundle":
      return self.trundle_cost(route)
    elif self.args.route_strategy == "astar":
      return self.astar_cost(route[0], route[-1], route)
    else:
      log.error("Invalid route strategy {0} provided".format(self.args.route_strategy))
      return None

  def trundle_cost(self, route):
    jump_count = (len(route)-1) * 1000
    dist = self.route_dist(route)
    var = self.route_stdev(route, dist)
    return jump_count + dist + var

  def route_dist(self, route):
    dist = 0.0
    for i in xrange(0, len(route)-1):
      dist += (route[i+1].position - route[i].position).length
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
    for i in xrange(0, len(route)-1):
      jdist = (route[i+1].position - route[i].position).length
      cvar += math.pow((jdist - meanjump), power)
    return cvar

  def astar_cost(self, a, b, route, dist_threshold = None):
    jcount = self.jump_count(a, b, route, (dist_threshold is not None))
    hs_jumps = self.time_for_jumps(jcount)
    hs_jdist = (a.position - b.position).length
    var = self.route_variance(route, self.route_dist(route))

    penalty = 0.0
    if jcount == 1 and dist_threshold is not None and (a.position - b.position).length > dist_threshold:
      penalty += 20

    for i in xrange(0, len(route)-1):
      cdist = (route[i+1].position - route[i].position).length
      if dist_threshold is not None and cdist > dist_threshold:
        penalty += 20

    total = (hs_jumps + hs_jdist + var + penalty)
    return total

  def sc_time(self, stn):
    if isinstance(stn, Station) and stn.name != None:
      return self.sc_cost(stn.distance if stn.distance != None else 0.0)
    else:
      return 0.0

  def station_time(self, stn):
    if isinstance(stn, Station) and stn.name != None:
      if stn.max_pad_size == 'L':
        return self.stop_station_time
      else:
        return self.stop_outpost_time
    else:
      return 0.0

  def time_for_jumps(self, jump_count):
    jump_witchspace_time = self.args.witchspace_time if self.args.witchspace_time is not None else self.jump_witchspace_time
    return max(0.0, ((self.jump_spool_time + jump_witchspace_time) * jump_count) + (self.jump_cooldown_time * (jump_count - 1)))

  def route_time(self, route, jump_count):
    hs_t = self.time_for_jumps(jump_count)
    sc_t = sum(self.sc_time(stn) for stn in route[1:])
    stn_t = sum(self.station_time(stn) for stn in route)

    log.debug("hs_time = {0:.2f}, sc_time = {1:.2f}, stn_time = {2:.2f}".format(hs_t, sc_t, stn_t))

    return hs_t + sc_t + stn_t
