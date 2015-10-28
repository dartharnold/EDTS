#!/usr/bin/env python

import argparse
import json
import logging
import math
import os
import sys
import env
import eddb
import coriolis
from calc import Calc
from route import Routing
from solver import Solver
from station import Station
from system import System
from fsd import FSD

log = logging.getLogger("edts")

class Application:

  def __init__(self, arg):
    ap = argparse.ArgumentParser(description = "Elite: Dangerous TSP Solver", fromfile_prefix_chars="@", parents=[env.arg_parser])
    ap.add_argument("-f", "--fsd", type=str, required=False, help="The ship's frame shift drive in the form 'A6 or '6A'")
    ap.add_argument("-m", "--mass", type=float, required=False, help="The ship's unladen mass excluding fuel")
    ap.add_argument("-t", "--tank", type=float, required=False, help="The ship's fuel tank size")
    ap.add_argument("-c", "--cargo", type=int, default=0, help="Cargo to collect at each station")
    ap.add_argument("-j", "--jump-range", type=float, required=False, help="The ship's max jump range with full fuel and empty cargo")
    ap.add_argument("-s", "--start", type=str, required=True, help="The starting station, in the form 'system/station' or 'system'")
    ap.add_argument("-e", "--end", type=str, required=True, help="The end station, in the form 'system/station' or 'system'")
    ap.add_argument("-n", "--num-jumps", default=None, type=int, help="The number of stations to visit, not including the start/end")
    ap.add_argument("-p", "--pad-size", default="M", type=str, help="The landing pad size of the ship (S/M/L)")
    ap.add_argument("-d", "--jump-decay", type=float, default=0.0, help="An estimate of the range decay per jump in Ly (e.g. due to taking on cargo)")
    ap.add_argument("-r", "--route", default=False, action='store_true', help="Whether to try to produce a full route rather than just hops")
    ap.add_argument("-o", "--ordered", default=False, action='store_true', help="Whether the stations are already in a set order")
    ap.add_argument("--jump-time", type=float, default=45.0, help="Seconds taken per hyperspace jump")
    ap.add_argument("--diff-limit", type=float, default=1.5, help="The multiplier of the fastest route which a route must be over to be discounted")
    ap.add_argument("--slf", type=float, default=0.9, help="The multiplier to apply to multi-jump hops to account for imperfect system positions")
    ap.add_argument("--route-strategy", default="astar", help="The strategy to use for route plotting. Valid options are 'trundle' and 'astar'")
    ap.add_argument("--solve-full", default=False, action='store_true', help="Uses full route plotting to find an optimal route solution (slow)")
    ap.add_argument("--rbuffer-base", type=float, default=10.0, help="A minimum buffer distance, in Ly, used to search for valid stars for routing")
    ap.add_argument("--rbuffer-mult", type=float, default=0.15, help="A multiple of hop straight-line distance to add to rbuffer_base")
    ap.add_argument("--hbuffer-base", type=float, default=5.0, help="A minimum buffer distance, in Ly, used to search for valid next hops. Only used by the 'trundle' strategy.")
    ap.add_argument("--hbuffer-mult", type=float, default=0.3, help="A multiple of jump range to add to hbuffer_base. Only used by the 'trundle' strategy.")
    ap.add_argument("stations", metavar="system[/station]", nargs="*", help="A station to travel via, in the form 'system/station' or 'system'")
    self.args = ap.parse_args(arg)

    if self.args.num_jumps == None:
      self.args.num_jumps = len(self.args.stations)

    if self.args.jump_range is None:
      if self.args.fsd is not None and self.args.mass is not None and self.args.tank is not None:
        self.unladen_mass = self.args.mass
        self.fuel = self.args.tank
        self.fsd = FSD(self.args.fsd, env.coriolis_fsd_list)
        if self.fsd is None:
          sys.exit(1)
      else:
        log.error("Error: You must specify either --jump-range or all of --fsd, --mass and --tank.")
        sys.exit(1)
    else:
      self.fsd = None
    

  def run(self):

    start = env.get_station_from_string(self.args.start)
    end = env.get_station_from_string(self.args.end)

    if start == None:
      log.error("Error: start system/station {0} could not be found. Stopping.".format(self.args.start))
      return
    if end == None:
      log.error("Error: end system/station {0} could not be found. Stopping.".format(self.args.end))
      return

    stations = []
    for st in self.args.stations:
      sobj = env.get_station_from_string(st)
      if sobj != None:      
        log.debug("Adding system/station: {0} ({1}, {2}Ls)".format(sobj.name, sobj.system_name, sobj.distance))
        
        if self.args.pad_size == "L" and sobj.max_pad_size != "L":
          log.warning("Warning: station {0} ({1}) is not usable by the specified ship size.".format(sobj.name, sobj.system_name))
        stations.append(sobj)
          
      else:
        log.warning("Error: system/station {0} could not be found.".format(st))
        return

    if self.fsd is not None:
      jump_range = self.fsd.range(self.unladen_mass, self.fuel)
    else:
      jump_range = self.args.jump_range

    calc = Calc(self.args, self.fsd)
    r = Routing(calc, env.eddb_systems, self.args.rbuffer_base, self.args.rbuffer_mult, self.args.hbuffer_base, self.args.hbuffer_mult, self.args.route_strategy)
    s = Solver(calc, r, jump_range, self.args.diff_limit, self.args.solve_full)

    if self.args.ordered:
      route = [start] + stations + [end]
    else:
      # Add 2 to the jump count for start + end
      route = s.solve(stations, start, end, self.args.num_jumps + 2)

    totaldist = 0.0
    totaljumps = 0
    totalsc = 0
    totalsc_accurate = True

    print ""
    print route[0].to_string()
    for i in xrange(1, len(route)):
      if self.fsd is None:
        cur_max_jump = self.args.jump_range - (self.args.jump_decay * (i-1))
      else:
        cur_max_jump = self.fsd.range(self.args.mass, self.args.tank, self.args.cargo * (i-1))

      jumpcount = calc.jump_count(route[i-1], route[i], route[0:i-1])
      if self.args.route:
        hop_route = r.plot(route[i-1].system, route[i].system, cur_max_jump)
        if hop_route != None:
          jumpcount = len(hop_route)-1
        else:
          log.warning("No valid route found for hop: {0} --> {1}".format(route[i-1].system_name, route[i].system_name))

      hopsldist = (route[i-1].position - route[i].position).length
      totaldist += hopsldist
      totaljumps += jumpcount
      if route[i].distance != None and route[i].distance != 0:
        totalsc += route[i].distance
      elif route[i].name != None:
        # Only say the SC time is inaccurate if it's actually a *station* we don't have the distance for
        totalsc_accurate = False

      if self.args.route and hop_route != None:
        lastdist = (hop_route[-1].position - hop_route[-2].position).length
        if len(hop_route) > 2:
          hopdist = 0.0
          for j in xrange(1, len(hop_route)-1):
            hdist = (hop_route[j-1].position - hop_route[j].position).length
            hopdist += hdist
            print "    --- {0: >6.2f}Ly ---> {1}".format(hdist, hop_route[j].name)
          hopdist += lastdist
        else:
          hopdist = hopsldist
    
      route_str = route[i].to_string()
      if route[i].name is not None:
        route_str += ", SC: ~{0}s".format("{0:.0f}".format(calc.sc_cost(route[i].distance)) if route[i].distance != None and route[i].distance != 0 else "???")
      if self.args.route and hop_route != None:
        print "    === {0: >6.2f}Ly ===> {1} -- hop of {2:.2f}Ly for {3:.2f}Ly".format(lastdist, route_str, hopdist, hopsldist)
      else:
        print "    === {0: >6.2f}Ly ({1:2d} jump{2}) ===> {3}".format(hopsldist, jumpcount, "s" if jumpcount != 1 else " ", route_str)

    est_time = calc.route_time(route, totaljumps)
    est_time_m = math.floor(est_time / 60)
    est_time_s = int(est_time) % 60

    print ""
    print "Total distance: {0:.2f}Ly; total jumps: {1:d}; total SC distance: {2:d}Ls{3}; ETT: {4:.0f}:{5:02.0f}".format(totaldist, totaljumps, totalsc, "+" if not totalsc_accurate else "", est_time_m, est_time_s)
    print ""



if __name__ == '__main__':
  a = Application(sys.argv[1:])
  a.run()


