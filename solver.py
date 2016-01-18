import logging
import math
import random
import vector3

log = logging.getLogger("solver")

max_single_solve_size = 20
cluster_size_max = 12
cluster_size_min = 5
cluster_divisor = 10

class Solver:
  def __init__(self, calc, route, jump_range, diff_limit):
    self._calc = calc
    self._route = route
    self._diff_limit = diff_limit
    self._jump_range = jump_range

  def solve(self, stations, start, end, maxstops, allow_clustering = True):
    if allow_clustering and len(stations) > max_single_solve_size:
      return self.solve_clustered(stations, start, end, maxstops), False
    else:
      return self.solve_basic(stations, start, end, maxstops), True
    
  def solve_basic(self, stations, start, end, maxstops):
    log.debug("Calculating viable routes...")
    vr = self.get_viable_routes([start], set(stations), end, maxstops)
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

    return minroute


  def solve_clustered(self, stations, start, end, maxstops):
    cluster_count = int(math.ceil(float(len(stations) + 2) / cluster_divisor))
    log.debug("Splitting problem into {0} clusters...".format(cluster_count))
    iterations = 0
    while iterations < 100:
      iterations += 1
      means, clusters = find_centers(stations, cluster_count)
      lengths = [len(clusters[i]) for i in clusters]
      if min(lengths) >= cluster_size_min and max(lengths) <= cluster_size_max:
        break
    log.debug("Using clusters of sizes {0} after {1} iterations".format(", ".join([str(len(clusters[i])) for i in clusters]), iterations))

    indices,_ = self.get_best_cluster_route(means, start, end)

    route = [start]
    r_maxstops = maxstops - 2

    # Get the closest points in the first/last clusters to the start/end
    _, from_start = self.get_closest_points([start], clusters[indices[0]])
    to_end, _ = self.get_closest_points(clusters[indices[-1]], [end])
    # For each cluster...
    for i in range(1, len(indices)):
      from_cluster = clusters[indices[i-1]]
      to_cluster = clusters[indices[i]]
      # Get the closest points, disallowing using from_start or to_end
      from_end, to_start = self.get_closest_points(from_cluster, to_cluster, [from_start, to_end])
      # Work out how many of the stops we should be doing in this cluster
      cur_maxstops = min(len(from_cluster), int(round(float(maxstops) * len(from_cluster) / len(stations))))
      r_maxstops -= cur_maxstops
      # Solve and add to the route. DO NOT allow nested clustering, that makes it all go wrong :)
      route += self.solve_basic(from_cluster, from_start, from_end, cur_maxstops)
      from_start = to_start
    route += self.solve_basic(clusters[indices[-1]], from_start, to_end, r_maxstops)
    route += [end]
    return route

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


  def get_best_cluster_route(self, means, start, end, route = []):
    best = None
    bestcost = 0.0
    if len(route) < len(means):
      for i,m in enumerate(means):
        if i in route:
          continue
        c_route, c_cost = self.get_best_cluster_route(means, start, end, route + [i])
        if best == None or c_cost < bestcost:
          best = c_route
          bestcost = c_cost
      return best, bestcost
    else:
      cur_cost = (start.position - means[route[0]]).length
      for i in range(1, len(route)):
        cur_cost += (means[route[i-1]] - means[route[i]]).length
      cur_cost += (means[route[-1]] - end.position).length
      return route, cur_cost

  def get_closest_points(self, cluster1, cluster2, disallowed = []):
    best = None
    bestcost = None
    for n1 in cluster1:
      if n1 in disallowed:
        continue
      for n2 in cluster2:
        if n2 in disallowed:
          continue
        cost = self._calc.solve_cost(n1, n2, [])
        if best == None or cost < bestcost:
          best = (n1, n2)
          bestcost = cost
    return best

#
# K-means clustering
#
def _cluster_points(X, mu):
  clusters = {}
  for x in X:
    bestmukey = min([(i[0], (x.position - mu[i[0]]).length) for i in enumerate(mu)], key=lambda t:t[1])[0]
    if bestmukey not in clusters:
      clusters[bestmukey] = []
    clusters[bestmukey].append(x)
  return clusters

def _reevaluate_centers(mu, clusters):
  newmu = []
  keys = sorted(clusters.keys())
  for k in keys:
    newmu.append(vector3.mean([x.position for x in clusters[k]]))
  return newmu

def _has_converged(mu, oldmu):
  return (set(mu) == set(oldmu))

def find_centers(X, K):
  # Initialize to K random centers
  oldmu = random.sample([x.position for x in X], K)
  mu = random.sample([x.position for x in X], K)
  clusters = None
  while not _has_converged(mu, oldmu):
    oldmu = mu
    # Assign all points in X to clusters
    clusters = _cluster_points(X, mu)
    # Reevaluate centers
    mu = _reevaluate_centers(oldmu, clusters)
  return(mu, clusters)
