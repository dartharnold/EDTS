import logging
import math

log = logging.getLogger("solver")

class Solver:
  def __init__(self, args, calc):
    self._calc = calc
    self.diff_limit = args.diff_limit

  def solve(self, stations, start, end, maxstops):
    vr = self.get_viable_routes([start], stations, end, maxstops)
    log.debug("Viable routes: {0}".format(len(vr)))
    
    mincost = None
    minroute = None
    
    for route in vr:
      cost = 0
      for i in xrange(0, len(route)-1):
        cost += self._calc.solve_cost(route[i], route[i+1], route)
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

        dist = self._calc.solve_cost(route[-1], stn, route)
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
    


