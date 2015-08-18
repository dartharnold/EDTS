import logging
import math
  
log = logging.getLogger("calc")

class Calc:
  def __init__(self, args):
    self.args = args
    self.sc_constant = 65
    self.sc_multiplier = 1.8
    self.sc_power = 0.5

  def jump_count(self, a, b, route):
    jumpdist = self.args.jump_range - (self.args.jump_decay * (len(route) - 1))
    hopdist = (a.position - b.position).length
    # If we're doing multiple jumps, apply the SLF
    if hopdist > jumpdist:
      jumpdist = jumpdist * self.args.slf
    return int(math.ceil(hopdist / jumpdist))

  def sc_cost(self, distance):
    return self.sc_constant + (math.pow(distance, self.sc_power) * self.sc_multiplier)
	
  def solve_cost(self, a, b, route):
    hs_jumps = self.jump_count(a, b, route) * self.args.jump_time
    hs_jdist = (a.position - b.position).length
    sc = self.sc_cost(b.distance) if b.uses_sc else 0.0
    return (hs_jumps + hs_jdist + sc)

  def route_cost(self, route):
    if self.args.route_strategy == "trundle":
      return self.trundle_cost(route)
    elif self.args.route_strategy == "astar":
      return self.astar_cost(route)
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

  def astar_cost(self, a, b, route):
    hs_jumps = self.jump_count(a, b, route) * self.args.jump_time
    hs_jdist = (a.position - b.position).length
    var = self.route_variance(route, self.route_dist(route))
    return (hs_jumps + hs_jdist + var)


