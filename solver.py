import logging
import math

log = logging.getLogger("solver")

class Solver:
  def __init__(self, calc, route, jump_range, diff_limit, solve_full):
    self._calc = calc
    self._route = route
    self._diff_limit = diff_limit
    self._jump_range = jump_range
    self._solve_full = solve_full

  def solve(self, stations, start, end, maxstops):
    vr = self.get_viable_routes([start], stations, end, maxstops)
    log.debug("Viable routes: {0}".format(len(vr)))

    count = 0
    costs = []
    mincost = None
    minroute = None

    for route in vr:
      count += 1
      cost_normal = self._calc.solve_route_cost(route)
      route_reversed = [route[0]] + list(reversed(route[1:-1])) + [route[-1]]
      cost_reversed = self._calc.solve_route_cost(route_reversed)

      cost = cost_normal if (cost_normal <= cost_reversed) else cost_reversed
      route = route if (cost_normal <= cost_reversed) else route_reversed

      costs.append(cost)
      if mincost == None or cost < mincost:
        log.debug("New minimum cost: {0} on route {1}".format(cost, count))
        mincost = cost
        minroute = route

    if self._solve_full:
      minrcost = None
      minrroute = None

      # Get accurate stats for each hop
      hops = self.get_route_hops(stations + [start, end])
      idx = 0
      for route in vr:
        # If the route is viable...
        if costs[idx] < (mincost * self._diff_limit):
          # For each hop...
          rcost = 0.0
          for i in range(0, len(route)-1):
            hop = hops[route[i]][route[i+1]]
            rcost += self._calc.route_cost(hop)

          if minrcost == None or rcost < minrcost:
            minrcost = rcost
            minrroute = route

        idx += 1

      return minrroute

    else:
      return minroute


  def get_route_hops(self, stations):
    hops = {}

    for h in stations:
      hops[h] = {}

    for s in stations:
      for t in stations:
        if s.to_string() != t.to_string() and t not in hops[s]:
          log.debug("Calculating hop: {0} -> {1}".format(s.name, t.name))
          hop = self._route.plot(s, t, self._jump_range)
          if hop == None:
            log.warning("Hop route could not be calculated: {0} -> {1}".format(s.name, t.name))
          hops[s][t] = hop
          hops[t][s] = hop

    return hops


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

      mindist = min(nexts.values())

      vsnext = []
      for stn, dist in nexts.items():
        if dist < (mindist * self._diff_limit):
          vsnext.append(stn)

      vrnext = []
      for stn in vsnext:
        vrnext = vrnext + self.get_viable_routes(route + [stn], stations, end, maxstops)
      
      return vrnext

    # We're at the end
    else:
      route.append(end)
      return [route]
    


