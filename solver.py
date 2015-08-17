import logging
import math

class Solver:
  def __init__(self, args):
    self.jump_range = args.jump_range
    self.jump_time = args.jump_time
    self.diff_limit = args.diff_limit
    self.jump_decay = args.jump_decay
    self.straight_line_factor = args.slf
    self.sc_power = 0.5
    self.sc_multiplier = 1.8
    self.sc_constant = 70


  def jump_count(self, a, b, route):
    jumpdist = self.jump_range - (self.jump_decay * (len(route) - 1))
    hopdist = (a.position - b.position).length
    # If we're doing multiple jumps, apply the SLF
    if hopdist > jumpdist:
      jumpdist = jumpdist * self.straight_line_factor
    return int(math.ceil(hopdist / jumpdist))

  def sc_cost(self, distance):
    return self.sc_constant + (math.pow(distance, self.sc_power) * self.sc_multiplier)
	
  def cost(self, a, b, route):
    # Now calculate
    hs_jumps = self.jump_count(a, b, route) * self.jump_time
    hs_jdist = (a.position - b.position).length
    sc = self.sc_cost(b.distance) if b.uses_sc else 0.0
    return (hs_jumps + hs_jdist + sc)

  def solve(self, stations, start, end, maxstops):
    vr = self.get_viable_routes([start], stations, end, maxstops)

    mincost = None
    minroute = None

    for route in vr:
      cost = 0
      for i in xrange(0, len(route)-1):
        cost += self.cost(route[i], route[i+1], route)
      if mincost == None or cost < mincost:
        mincost = cost
        minroute = route

    return minroute

  def get_viable_routes(self, route, stations, end, maxstops):
    # If we have more non-end stops to go...
    if len(route) + 1 < maxstops:
      nexts = {}

      for stn in stations:
        # Can't visit the same station twice
        if stn in route or stn == end:
          continue

        dist = self.cost(route[-1], stn, route)
        nexts[stn] = dist

      mindist = min(nexts.itervalues())

      vsnext = []
      for stn, dist in nexts.iteritems():
        if dist < (mindist * self.diff_limit):
          vsnext.append(stn)

      vrnext = []
      for stn in vsnext:
        vrnext = vrnext + self.get_viable_routes(route + [stn], stations, end, maxstops)
      
      return vrnext

    # We're at the end
    else:
      route.append(end)
      return [route]
    


