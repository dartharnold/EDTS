import logging
import math
import sys
from system import System
from vector3 import Vector3

log = logging.getLogger("route")


class Routing:

  def __init__(self, calc, eddb_systems, bufroute, bufhop, route_strategy):
    self._calc = calc
    self._systems = eddb_systems
    self._buffer_ly_route = bufroute
    self._buffer_ly_hop = bufhop
    self._route_strategy = route_strategy


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
    if self._route_strategy == "trundle":
      # My algorithm - slower but pinpoint
      return self.plot_trundle(sys_from, sys_to, jump_range)
    elif self._route_strategy == "astar":
      # A* search - faster but worse fuel efficiency
      return self.plot_astar(sys_from, sys_to, jump_range)
    else:
      log.error("Tried to use invalid route strategy {0}".format(self._route_strategy))
      return None


  def plot_astar(self, sys_from, sys_to, jump_range):
    stars = self.cylinder(self._systems, sys_from.position, sys_to.position, self._buffer_ly_route)

    closedset = []          # The set of nodes already evaluated.
    openset = [sys_from]    # The set of tentative nodes to be evaluated, initially containing the start node
    came_from = dict()
 
    g_score = dict()
    g_score[sys_from] = 0    # Cost from sys_from along best known path.
    f_score = dict()
    f_score[sys_from] = self._calc.astar_cost(sys_from, sys_to, [sys_from])
    
    while len(openset) > 0:
      current = min(openset, key=f_score.get) # the node in openset having the lowest f_score[] value
      if current == sys_to:
        return self.astar_reconstruct_path(came_from, sys_to)
      
      openset.remove(current)
      closedset.append(current)

      neighbor_nodes = [n for n in stars if n != current and (n.position - current.position).length < jump_range]

      for neighbor in neighbor_nodes:
        if neighbor in closedset:
          continue
 
        tentative_g_score = g_score[current] + (current.position - neighbor.position).length

        if neighbor not in g_score:
          g_score[neighbor] = sys.float_info.max

        if neighbor not in openset or tentative_g_score < g_score[neighbor]:
          came_from[neighbor] = current
          g_score[neighbor] = tentative_g_score
          f_score[neighbor] = self._calc.astar_cost(neighbor, sys_to, self.astar_reconstruct_path(came_from, neighbor))
          if neighbor not in openset:
            openset.append(neighbor)
 
    return None


  def astar_reconstruct_path(self, came_from, current):
    total_path = [current]
    while current in came_from:
        current = came_from[current]
        total_path.append(current)
    return list(reversed(total_path))


  def plot_trundle(self, sys_from, sys_to, jump_range):
    stars = self.cylinder(self._systems, sys_from.position, sys_to.position, self._buffer_ly_route)
   
    log.debug("{0} --> {1}: systems to search from: {2}".format(sys_from.name, sys_to.name, len(stars)))

    add_jumps = 0
    best_jump_count = int(math.ceil((sys_from.position - sys_to.position).length / jump_range))

    best = None
    bestcost = None
    while best == None:
      log.debug("Attempt %d, jump count: %d, calculating...", add_jumps, best_jump_count + add_jumps)
      vr = self.trundle_get_viable_routes([sys_from], stars, sys_to, jump_range, add_jumps)
      log.debug("Attempt %d, jump count: %d, viable routes: %d", add_jumps, best_jump_count + add_jumps, len(vr))
      for route in vr:
        cost = self._calc.trundle_cost(route)
        if bestcost == None or cost < bestcost:
          best = route
          bestcost = cost
      add_jumps += 1

    log.debug("Route, length = %d, cost = %.2f: %s", len(best)-1, bestcost, " --> ".join([p.name for p in best]))
    return best

  def trundle_get_viable_routes(self, route, stars, sys_to, jump_range, add_jumps):
    cur_dist = (route[-1].position - sys_to.position).length
    if cur_dist > jump_range:
      # Multiple jumps to go
      best_jump_count = int(math.ceil((route[0].position - sys_to.position).length / jump_range)) + add_jumps

      # current_pos + (dir(current_pos --> sys_to) * jump_range)
      dir_vec = route[-1].position + ((sys_to.position - route[-1].position).normalise() * jump_range)
      # Start looking halfway down the route, since we shouldn't really ever be jumping <50% of our range, especially + buffer
      start_vec = route[-1].position + ((sys_to.position - route[-1].position).normalise() * jump_range / 2)
      # Get viable stars; if we're adding jumps, use a smaller buffer cylinder to prevent excessive searching
      mystars = self.cylinder(stars, start_vec, dir_vec, self._buffer_ly_hop)

      # Get valid next hops
      vsnext = []
      for s in mystars:
        next_dist = (s.position - route[-1].position).length
        if next_dist < jump_range:
          dist_jumpN = (s.position - sys_to.position).length
          maxd = (best_jump_count - len(route)) * jump_range
#          log.debug("[%d] [%d] cur_dist = %.2f, next_dist = %.2f, dist_jumpN = %.2f, maxd = %.2f", best_jump_count, len(route)-1, cur_dist, next_dist, dist_jumpN, maxd)
          if dist_jumpN < maxd:
            vsnext.append(s)

      vrnext = []
      for s in vsnext:
        vrnext = vrnext + self.trundle_get_viable_routes(route + [s], stars, sys_to, jump_range, add_jumps)
      return vrnext

    else:
      route.append(sys_to)
      return [route]

