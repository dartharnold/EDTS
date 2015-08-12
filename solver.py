import logging
import math

class Solver:
  def __init__(self, args):
    self.jump_distance = args.jump_distance
    self.jump_time = args.jump_time
    self.sc_multiplier = args.sc_multiplier
    self.diff_limit = args.diff_limit
    self.jump_decay = args.jump_decay
    self.straight_line_factor = args.slf


  def jump_count(self, a, b, route):
    jumpdist = self.jump_distance - (self.jump_decay * (len(route) - 1))
    hopdist = (a.position - b.position).length
    # If we're doing multiple jumps, apply the SLF
    if hopdist > jumpdist:
      jumpdist = jumpdist * self.straight_line_factor
    return int(math.ceil(hopdist / jumpdist))

  def cost(self, a, b, route):
    # Now calculate
    hs_jumps = self.jump_count(a, b, route) * self.jump_time
    hs_jdist = (a.position - b.position).length
    sc = b.distance * self.sc_multiplier
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
    


