import logging
import math
import sys
from system import System
from vector3 import Vector3

log = logging.getLogger("route")

class Routing:

  def __init__(self, calc, eddb_systems, rbuf_base, rbuf_mult, hbuf_base, hbuf_mult, route_strategy):
    self._calc = calc
    self._systems = eddb_systems
    self._rbuffer_base = rbuf_base
    self._rbuffer_mult = rbuf_mult
    self._hbuffer_base = hbuf_base
    self._hbuffer_mult = hbuf_mult
    self._route_strategy = route_strategy
    self._trundle_max_addjumps = 4
    self._trunkle_max_addjumps = 6.1
    self._ocount_initial_boost = 1.0
    self._ocount_relax_inc = 0.2
    self._ocount_reset_dec = 2.0
    self._ocount_reset_full = True
    self._trunkle_hop_size = 5.0
    self._trunkle_search_radius = 10.0

  def aabb(self, stars, vec_from, vec_to, buffer_from, buffer_to):
    min_x = min(vec_from.x, vec_to.x) - buffer_from
    min_y = min(vec_from.y, vec_to.y) - buffer_from
    min_z = min(vec_from.z, vec_to.z) - buffer_from
    max_x = max(vec_from.x, vec_to.x) + buffer_to
    max_y = max(vec_from.y, vec_to.y) + buffer_to
    max_z = max(vec_from.z, vec_to.z) + buffer_to

    candidates = []
    for s in stars:
      x = s.position.x
      y = s.position.y
      z = s.position.z
      if min_x < x < max_x and min_y < y < max_y and min_z < z < max_z:
        candidates.append(s)

    return candidates

  def cylinder(self, stars, vec_from, vec_to, buffer_both):
    candidates = []
    for s in stars:
      numerator = ((s.position - vec_from).cross(s.position - vec_to)).length
      denominator = (vec_to - vec_from).length
      dist = numerator / denominator
      if dist < buffer_both:
        candidates.append(s)

    return candidates

  def circle(self, stars, vec, radius):
    candidates = []
    for s in stars:
      dist = (s.position - vec).length
      if dist < radius:
        candidates.append(s)

    return candidates

  def plot(self, sys_from, sys_to, jump_range, full_range = None):
    if full_range is None:
      full_range = jump_range

    if self._route_strategy == "trundle":
      # My algorithm - slower but pinpoint
      return self.plot_trundle(sys_from, sys_to, jump_range, full_range)
    elif self._route_strategy == "trunkle":
      return self.plot_trunkle(sys_from, sys_to, jump_range, full_range)
    elif self._route_strategy == "astar":
      # A* search - faster but worse fuel efficiency
      return self.plot_astar(sys_from, sys_to, jump_range, full_range)
    else:
      log.error("Tried to use invalid route strategy {0}".format(self._route_strategy))
      return None

  def plot_astar(self, sys_from, sys_to, jump_range, full_range):
    rbuffer_ly = self._rbuffer_base + (sys_from.distance_to(sys_to) * self._rbuffer_mult)
    stars = self.cylinder(self._systems, sys_from.position, sys_to.position, rbuffer_ly)
    # Ensure the target system is present, in case it's a "fake" system not in the main list
    if sys_to not in stars:
      stars.append(sys_to)

    closedset = set()         # The set of nodes already evaluated.
    openset = set([sys_from]) # The set of tentative nodes to be evaluated, initially containing the start node
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
      closedset.add(current)

      neighbor_nodes = [n for n in stars if n != current and n.distance_to(current) < jump_range]

      path = self.astar_reconstruct_path(came_from, current)

      for neighbor in neighbor_nodes:
        if neighbor in closedset:
          continue

        # tentative_g_score = g_score[current] + (current.position - neighbor.position).length     
        tentative_g_score = g_score[current] + self._calc.astar_cost(current, neighbor, path, full_range)

        if neighbor not in g_score:
          g_score[neighbor] = sys.float_info.max

        if neighbor not in openset or tentative_g_score < g_score[neighbor]:
          came_from[neighbor] = current
          g_score[neighbor] = tentative_g_score
          f_score[neighbor] = self._calc.astar_cost(neighbor, sys_to, self.astar_reconstruct_path(came_from, neighbor), full_range)
          if neighbor not in openset:
            openset.add(neighbor)

    return None

  def astar_reconstruct_path(self, came_from, current):
    total_path = [current]
    while current in came_from:
        current = came_from[current]
        total_path.append(current)
    return list(reversed(total_path))

  def plot_trunkle(self, sys_from, sys_to, jump_range, full_range):
    rbuffer_ly = self._rbuffer_base + (sys_from.distance_to(sys_to) * self._rbuffer_mult)
    hbuffer_ly = self._hbuffer_base + (jump_range * self._hbuffer_mult)
    # Get full cylinder to work from
    stars = self.cylinder(self._systems, sys_from.position, sys_to.position, rbuffer_ly)

    best_jump_count = int(math.ceil(sys_from.distance_to(sys_to) / jump_range))

    sldistance = sys_from.distance_to(sys_to)
    # Current estimate of furthest ahead to look, as the estimated total number of jumps in this hop
    optimistic_count = best_jump_count - self._ocount_initial_boost
    # How many jumps to perform in each leg
    trunc_jcount = self._trunkle_hop_size

    sys_cur = sys_from
    next_star = None

    log.debug("Attempting to plot from {0} --> {1}".format(sys_from.to_string(), sys_to.to_string()))

    route = [sys_from]
    # While we haven't hit our limit to bomb out...
    while optimistic_count - best_jump_count <= self._trunkle_max_addjumps:
      # If this isn't our final leg...
      if self.best_jump_count(sys_cur, sys_to, jump_range) > trunc_jcount:
        factor = sldistance * (trunc_jcount / optimistic_count)
        # Work out the next position to get a circle of stars from
        next_pos = sys_cur.position + (sys_to.position - sys_cur.position).normalise() * factor
        log.debug("factor = {0}, optimistic_count = {1}, next_pos = {2}".format(factor, optimistic_count, next_pos))
        # Get a circle of stars around the estimate
        next_stars = self.circle(stars, next_pos, self._trunkle_search_radius)
        # Limit them to only ones where it's possible we'll get a valid route
        next_stars = [s for s in next_stars if self.best_jump_count(sys_cur, s, jump_range) <= trunc_jcount]
        # Now find the star closest to the centre line (TODO: improve this somehow, check multiple stars)
        c_next_star = min(next_stars, key=lambda s: (s.position - next_pos).length) if len(next_stars) > 0 else None
        # Check we got a valid star that isn't the one we've already been checking against
        # If not, bump the count up a bit and start the loop again
        if c_next_star == None or c_next_star == next_star:
          optimistic_count += self._ocount_relax_inc
          continue
        next_star = c_next_star
      else:
        next_star = sys_to

      best_jcount = self.best_jump_count(sys_cur, next_star, jump_range)
      # Use trundle to try and calculate a route
      next_route = self.plot_trundle(sys_cur, next_star, jump_range, full_range, max(0, trunc_jcount-best_jcount))
      # If our route was invalid or too long, increment the ocount and start the loop again
      if next_route == None or (next_star != sys_to and len(next_route)-1 > trunc_jcount):
        optimistic_count += self._ocount_relax_inc
        log.debug("Attempt failed, bumping oc to {0}".format(optimistic_count))
        continue

      # We have a valid route of the correct length, add it to the main route
      route += next_route[1:]
      sys_cur = next_star
      # If we're setting the ocount all the way back to its initial value, do that; otherwise just drop it a bit
      # This ensures that we don't miss any good legs just because the previous leg was a dud
      if self._ocount_reset_full == True:
        optimistic_count = best_jump_count - self._ocount_initial_boost
      else:
        optimistic_count = math.max(1.0, self._ocount_reset_dec)
      # If we've hit the destination, return with successful route
      if sys_cur == sys_to:
        log.debug("Arrived at {0}".format(sys_to.to_string()))
        return route

      log.debug("Plotted {0} jumps to {1}, continuing".format(len(next_route)-1, next_star.to_string()))

    log.debug("No route found")
    return None

  def plot_trundle(self, sys_from, sys_to, jump_range, full_range, addj_limit = None):
    rbuffer_ly = self._rbuffer_base + (sys_from.distance_to(sys_to) * self._rbuffer_mult)
    stars = self.cylinder(self._systems, sys_from.position, sys_to.position, rbuffer_ly)

    log.debug("{0} --> {1}: systems to search from: {2}".format(sys_from.name, sys_to.name, len(stars)))

    add_jumps = 0
    best_jump_count = self.best_jump_count(sys_from, sys_to, jump_range)

    best = None
    bestcost = None
    while best == None and add_jumps <= self._trundle_max_addjumps and (addj_limit is None or add_jumps <= addj_limit):
      log.debug("Attempt %d, jump count: %d, calculating...", add_jumps, best_jump_count + add_jumps)
      vr = self.trundle_get_viable_routes([sys_from], stars, sys_to, jump_range, add_jumps)
      log.debug("Attempt %d, jump count: %d, viable routes: %d", add_jumps, best_jump_count + add_jumps, len(vr))
      for route in vr:
        cost = self._calc.trundle_cost(route)
        if bestcost == None or cost < bestcost:
          best = route
          bestcost = cost
      add_jumps += 1

    if best != None:
      log.debug("Route, length = %d, cost = %.2f: %s", len(best)-1, bestcost, " --> ".join([p.name for p in best]))
    else:
      log.debug("No route found")
    return best

  def best_jump_count(self, sys_from, sys_to, jump_range):
    return int(math.ceil(sys_from.distance_to(sys_to) / jump_range))

  def trundle_get_viable_routes(self, route, stars, sys_to, jump_range, add_jumps):
    best_jcount = int(math.ceil(route[0].distance_to(sys_to) / jump_range)) + add_jumps
    vec_mult = 1.0 - max(1.0 / best_jcount, 0.1)
    hbuf_ly = self._hbuffer_base + (jump_range * self._hbuffer_mult)

    return self._trundle_gvr_internal(route, stars, sys_to, jump_range, add_jumps, best_jcount, vec_mult, hbuf_ly)

  def _trundle_gvr_internal(self, route, stars, sys_to, jump_range, add_jumps, best_jcount, vec_mult, hbuffer_ly):
    cur_dist = route[-1].distance_to(sys_to)
    if cur_dist > jump_range:
      # dir(current_pos --> sys_to) * jump_range
      dir_vec = ((sys_to.position - route[-1].position).normalise() * jump_range)
      # Start looking some way down the route, determined by jump count
      start_vec = route[-1].position + (dir_vec * vec_mult)
      end_vec = route[-1].position + dir_vec
      # Get viable stars; if we're adding jumps, use a smaller buffer cylinder to prevent excessive searching
      mystars = self.cylinder(stars, start_vec, end_vec, hbuffer_ly)

      # Get valid next hops
      vsnext = []
      for s in mystars:
        # distance(last_hop, candidate)
        next_dist = route[-1].distance_to(s)
        if next_dist < jump_range:
          dist_jumpN = s.distance_to(sys_to)
          # Is it possible for us to still hit the current total jump count with this jump?
          maxd = (best_jcount - len(route)) * jump_range
          if dist_jumpN < maxd:
            vsnext.append(s)

      vrnext = []
      for s in vsnext:
        vrnext = vrnext + self._trundle_gvr_internal(route + [s], stars, sys_to, jump_range, add_jumps, best_jcount, vec_mult, hbuffer_ly)
      return vrnext

    else:
      route.append(sys_to)
      return [route]
