import logging
import math
from system import System
from vector3 import Vector3

log = logging.getLogger("route")


class Routing:

  def __init__(self, args, eddbSystems):
    self._systems = eddbSystems
    self._buffer_ly = args.buffer_ly


  def aabb(self, stars, vec_from, vec_to, buffer_from, buffer_to):
    min_x = min(vec_from.x, vec_to.x) - buffer_from
    min_y = min(vec_from.y, vec_to.y) - buffer_from
    min_z = min(vec_from.z, vec_to.z) - buffer_from
    max_x = max(vec_from.x, vec_to.x) + buffer_to
    max_y = max(vec_from.y, vec_to.y) + buffer_to
    max_z = max(vec_from.z, vec_to.z) + buffer_to

    candidates = []
    for s in stars:
      x = s.position.x if isinstance(s, System) else s["x"]
      y = s.position.y if isinstance(s, System) else s["y"]
      z = s.position.z if isinstance(s, System) else s["z"]
      if min_x < x < max_x and min_y < y < max_y and min_z < z < max_z:
        if isinstance(s, System):
          candidates.append(s)
        else:
          candidates.append(System(s["x"], s["y"], s["z"], s["name"], s["needs_permit"]))

    return candidates


  def cylinder(self, stars, vec_from, vec_to, buffer_both):
    candidates = []
    for s in stars:
      x = s.position.x if isinstance(s, System) else s["x"]
      y = s.position.y if isinstance(s, System) else s["y"]
      z = s.position.z if isinstance(s, System) else s["z"]
      sv = Vector3(x, y, z)
      
      numerator = ((sv - vec_from).cross(sv - vec_to)).length
      denominator = (vec_to - vec_from).length
      dist = numerator / denominator
      if dist < buffer_both:
        if isinstance(s, System):
          candidates.append(s)
        else:
          candidates.append(System(s["x"], s["y"], s["z"], s["name"], s["needs_permit"]))

    return candidates


  def plot(self, sys_from, sys_to, jump_range):
    # stars = self.aabb(self._systems, sys_from.position, sys_to.position, self._buffer_ly, self._buffer_ly)
    stars = self.cylinder(self._systems, sys_from.position, sys_to.position, self._buffer_ly)
   
    log.debug("Systems to search from: {0}".format(len(stars)))

    add_jumps = 0
    best_jump_count = int(math.ceil((sys_from.position - sys_to.position).length / jump_range))

    best = None
    bestcost = None
    while best == None:
      vr = self.get_viable_routes([sys_from], stars, sys_to, jump_range, add_jumps)
      log.debug("Attempt %d, jump count: %d, viable routes: %d", add_jumps, best_jump_count + add_jumps, len(vr))
      for route in vr:
        cost = self.route_cost(route)
        if bestcost == None or cost < bestcost:
          best = route
          bestcost = cost
      add_jumps += 1

    log.debug("Route, length = %d, cost = %.2f: %s", len(best)-1, bestcost, " --> ".join([p.name for p in best]))
    return best


  def route_cost(self, route):
    jump_count = (len(route)-1) * 1000
    dist = self.route_dist(route)
    var = self.route_variance(route, dist)
    return jump_count + dist + var

  def route_dist(self, route):
    dist = 0.0
    for i in xrange(0, len(route)-1):
      dist += (route[i+1].position - route[i].position).length
    return dist

  def route_variance(self, route, dist):
    meanjump = dist / (len(route)-1)
    cvar = 0.0
    for i in xrange(0, len(route)-1):
      jdist = (route[i+1].position - route[i].position).length
      cvar += (jdist - meanjump) * (jdist - meanjump)
    return cvar
    

  def get_viable_routes(self, route, stars, sys_to, jump_range, add_jumps):
    cur_dist = (route[-1].position - sys_to.position).length
    if cur_dist > jump_range:
      # Multiple jumps to go
      best_jump_count = int(math.ceil((route[0].position - sys_to.position).length / jump_range)) + add_jumps

      # current_pos + (dir(current_pos --> sys_to) * jump_range)
      dir_vec = route[-1].position + ((sys_to.position - route[-1].position).normalise() * jump_range)
      # mystars = self.aabb(stars, route[-1].position, dir_vec, 0.0, self._buffer_ly)
      mystars = self.cylinder(stars, route[-1].position, dir_vec, self._buffer_ly)

      # Get valid next hops
      vsnext = []
      for s in mystars:
        next_dist = (s.position - route[-1].position).length
        dist_jumpN = (s.position - sys_to.position).length
        if next_dist < jump_range:
          maxd = (best_jump_count - (len(route)-1)) * jump_range
          if dist_jumpN < maxd:
            vsnext.append(s)

      vrnext = []
      for s in vsnext:
        vrnext = vrnext + self.get_viable_routes(route + [s], stars, sys_to, jump_range, add_jumps)
      return vrnext

    else:
      route.append(sys_to)
      return [route]

