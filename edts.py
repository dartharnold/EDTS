#!/usr/bin/env python

from __future__ import print_function
import argparse
import logging
import math
import sys
import env
from calc import Calc
from route import Routing
from solver import Solver
from station import Station
from system import System
from fsd import FSD

app_name = "edts"

log = logging.getLogger(app_name)

class Application:

  def __init__(self, arg, hosted):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Elite: Dangerous TSP Solver", fromfile_prefix_chars="@", parents=ap_parents, prog = app_name)
    ap.add_argument("-f", "--fsd", type=str, required=False, help="The ship's frame shift drive in the form 'A6 or '6A'")
    ap.add_argument("-m", "--mass", type=float, required=False, help="The ship's unladen mass excluding fuel")
    ap.add_argument("-t", "--tank", type=float, required=False, help="The ship's fuel tank size")
    ap.add_argument("-c", "--cargo", type=int, default=0, help="Cargo to collect at each station")
    ap.add_argument("-j", "--jump-range", type=float, required=False, help="The ship's max jump range with full fuel and empty cargo")
    ap.add_argument("-w", "--witchspace-time", type=int, required=False, help="Time in seconds spent in hyperspace jump")
    ap.add_argument("-s", "--start", type=str, required=True, help="The starting station, in the form 'system/station' or 'system'")
    ap.add_argument("-e", "--end", type=str, required=True, help="The end station, in the form 'system/station' or 'system'")
    ap.add_argument("-n", "--num-jumps", default=None, type=int, help="The number of stations to visit, not including the start/end")
    ap.add_argument("-p", "--pad-size", default="M", type=str.upper, choices=['S','M','L'], help="The landing pad size of the ship (S/M/L)")
    ap.add_argument("-d", "--jump-decay", type=float, default=0.0, help="An estimate of the range decay per jump in Ly (e.g. due to taking on cargo)")
    ap.add_argument("-r", "--route", default=False, action='store_true', help="Whether to try to produce a full route rather than just hops")
    ap.add_argument("-o", "--ordered", default=False, action='store_true', help="Whether the stations are already in a set order")
    ap.add_argument("-l", "--long-jumps", default=False, action='store_true', help="Whether to allow for jumps only possible at low fuel when routing")
    ap.add_argument("--format", default='long', type=str.lower, choices=['long','short','csv'], help="The format to display the output in")
    ap.add_argument("--reverse", default=False, action='store_true', help="Whether to reverse the generated route")
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
        self.fsd = FSD(self.args.fsd)
        if self.fsd is None:
          sys.exit(1)
      else:
        log.error("Error: You must specify either --jump-range or all of --fsd, --mass and --tank.")
        sys.exit(1)
    else:
      self.fsd = None


  def run(self):

    start = env.data.get_station_from_string(self.args.start)
    end = env.data.get_station_from_string(self.args.end)

    if start == None:
      log.error("Error: start system/station {0} could not be found. Stopping.".format(self.args.start))
      return
    if end == None:
      log.error("Error: end system/station {0} could not be found. Stopping.".format(self.args.end))
      return

    stations = []
    for st in self.args.stations:
      sobj = env.data.get_station_from_string(st)
      if sobj != None:
        log.debug("Adding system/station: {0} ({1}, {2}Ls)".format(sobj.name, sobj.system_name, sobj.distance if sobj.distance != None else "???"))

        if self.args.pad_size == "L" and sobj.max_pad_size != "L":
          log.warning("Warning: station {0} ({1}) is not usable by the specified ship size.".format(sobj.name, sobj.system_name))
        stations.append(sobj)

      else:
        log.warning("Error: system/station {0} could not be found.".format(st))
        return

    if self.fsd is not None:
      full_jump_range = self.fsd.range(self.unladen_mass, self.fuel)
      jump_range = self.fsd.max_range(self.unladen_mass) if self.args.long_jumps else full_jump_range
    else:
      full_jump_range = self.args.jump_range
      jump_range = self.args.jump_range

    calc = Calc(self.args, self.fsd)
    r = Routing(calc, env.data.eddb_systems, self.args.rbuffer_base, self.args.rbuffer_mult, self.args.hbuffer_base, self.args.hbuffer_mult, self.args.route_strategy)
    s = Solver(calc, r, jump_range, self.args.diff_limit, self.args.solve_full)

    if self.args.ordered:
      route = [start] + stations + [end]
    else:
      # Add 2 to the jump count for start + end
      route = s.solve(stations, start, end, self.args.num_jumps + 2)

    if self.args.reverse:
      route = [route[0]] + list(reversed(route[1:-1])) + [route[-1]]

    totaldist = 0.0
    totaljumps_min = 0
    totaljumps_max = 0
    totalsc = 0
    totalsc_accurate = True

    output_data = []

    if route != None and len(route) > 0:
      output_data.append({'src': route[0].to_string()})

      for i in range(1, len(route)):
        cur_data = {'dst': route[i]}

        if self.fsd is None:
          full_max_jump = self.args.jump_range - (self.args.jump_decay * (i-1))
          cur_max_jump = full_max_jump
        else:
          full_max_jump = self.fsd.range(self.args.mass, self.args.tank, self.args.cargo * (i-1))
          cur_max_jump = self.fsd.max_range(self.args.mass, self.args.cargo * (i-1)) if self.args.long_jumps else full_max_jump

        cur_data['jumpcount_min'], cur_data['jumpcount_max'] = calc.jump_count_range(route[i-1], route[i], route[0:i-1], self.args.long_jumps)
        if self.args.route:
          log.debug("Doing route plot for {0} --> {1}".format(route[i-1].system.name, route[i].system.name))
          hop_route = r.plot(route[i-1].system, route[i].system, cur_max_jump, full_max_jump)
          if hop_route != None:
            route_jcount = len(hop_route)-1
            # For hoppy routes, always use stats for the jumps reported (less confusing)
            cur_data['jumpcount_min'] = route_jcount
            cur_data['jumpcount_max'] = route_jcount
            # cur_data['jumpcount_min'] = min(cur_data['jumpcount_min'], route_jcount)
            # cur_data['jumpcount_max'] = min(cur_data['jumpcount_max'], route_jcount)
          else:
            log.warning("No valid route found for hop: {0} --> {1}".format(route[i-1].system_name, route[i].system_name))

        cur_data['hopsldist'] = (route[i-1].position - route[i].position).length
        totaldist += cur_data['hopsldist']
        totaljumps_min += cur_data['jumpcount_min']
        totaljumps_max += cur_data['jumpcount_max']
        if route[i].distance != None and route[i].distance != 0:
          totalsc += route[i].distance
        elif route[i].name != None:
          # Only say the SC time is inaccurate if it's actually a *station* we don't have the distance for
          totalsc_accurate = False

        if self.args.route and hop_route != None:
          cur_data['hop_route'] = []
          if len(hop_route) > 2:
            cur_data['hopdist'] = 0.0
            for j in range(1, len(hop_route)):
              hdist = (hop_route[j-1].position - hop_route[j].position).length
              cur_data['hopdist'] += hdist
              is_long = (hdist > full_max_jump)
              cur_data['hop_route'].append({'is_long': is_long, 'hdist': hdist, 'dst': hop_route[j]})
          else:
            cur_data['hopdist'] = cur_data['hopsldist']
            hdist = (hop_route[0].position - hop_route[1].position).length
            cur_data['hop_route'].append({'is_long': is_long, 'hdist': hdist, 'dst': hop_route[1]})

        if route[i].name is not None:
          cur_data['sc_time'] = "{0:.0f}".format(calc.sc_cost(route[i].distance)) if (route[i].distance != None and route[i].distance != 0) else "???"
        # Add current route to list
        output_data.append(cur_data)

      # Get suitably formatted ETA string
      est_time_min = calc.route_time(route, totaljumps_min)
      est_time_min_m = math.floor(est_time_min / 60)
      est_time_min_s = int(est_time_min) % 60
      est_time_str = "{0:.0f}:{1:02.0f}".format(est_time_min_m, est_time_min_s)
      if totaljumps_min != totaljumps_max:
        est_time_max = calc.route_time(route, totaljumps_max)
        est_time_max_m = math.floor(est_time_max / 60)
        est_time_max_s = int(est_time_max) % 60
        est_time_str += " - {0:.0f}:{1:02.0f}".format(est_time_max_m, est_time_max_s)

      totaljumps_str = "{0:d}".format(totaljumps_max) if totaljumps_min == totaljumps_max else "{0:d} - {1:d}".format(totaljumps_min, totaljumps_max)

      # Work out the max length of the jump distances and jump counts to be printed
      d_max_len = 0
      jmin_max_len = 0
      jmax_max_len = 0
      has_var_jcounts = False
      for i in range(1, len(output_data)):
        od = output_data[i]
        # If we have a hoppy route, we'll only be printing single-jump ranges. If not, we'll be using full leg distances.
        if 'hop_route' in od:
          if len(od['hop_route']) > 0:
            d_max_len = max(d_max_len, max([h['hdist'] for h in od['hop_route']]))
        else:
          d_max_len = max(d_max_len, max(1, od['hopsldist']))
        # If we have estimated jump counts, work out how long the strings will be
        if 'jumpcount_min' in od:
          jmin_max_len = max(jmin_max_len, od['jumpcount_min'])
          jmax_max_len = max(jmax_max_len, od['jumpcount_max'])
          has_var_jcounts = has_var_jcounts or (od['jumpcount_min'] != od['jumpcount_max'])

      # Length = "NNN.nn", so length = len(NNN) + 3 = log10(NNN) + 4
      d_max_len = str(int(math.floor(math.log10(d_max_len))) + 4)
      # Work out max length of jump counts, ensuring >= 1 char
      jmin_max_len = int(math.floor(max(1, math.log10(jmin_max_len)+1)))
      jmax_max_len = int(math.floor(max(1, math.log10(jmax_max_len)+1)))
      # If we have the form "N - M" anywhere, pad appropriately. If not, just use the normal length
      jall_max_len = str(jmin_max_len + jmax_max_len + 3) if has_var_jcounts else str(jmin_max_len)
      jmin_max_len = str(jmin_max_len)
      jmax_max_len = str(jmax_max_len)

      print_summary = True

      if self.args.format == 'long':
        print("")
        print(route[0].to_string())

        # For each hop (not including start point)
        for i in range(1, len(route)):
          od = output_data[i]
          if 'hop_route' in od:
            # For every jump except the last...
            for j in range(0, len(od['hop_route'])-1):
              hd = od['hop_route'][j]
              print(("    -{0}- {1: >"+d_max_len+".2f}Ly -{0}-> {2}").format("!" if hd['is_long'] else "-", hd['hdist'], hd['dst'].to_string()))
            # For the last jump...
            hd = od['hop_route'][-1]
            print(("    ={0}= {1: >"+d_max_len+".2f}Ly ={0}=> {2} -- hop of {3:.2f}Ly for {4:.2f}Ly").format("!" if hd['is_long'] else "=", hd['hdist'], od['dst'].to_string(), od['hopdist'], od['hopsldist']))
          else:
            # If we don't have "N - M", just print simple result
            if od['jumpcount_min'] == od['jumpcount_max']:
              jumps_str = ("{0:>"+jall_max_len+"d} jump{1}").format(od['jumpcount_max'], "s" if od['jumpcount_max'] != 1 else " ")
            else:
              jumps_str = ("{0:>"+jmin_max_len+"d} - {1:>"+jmax_max_len+"d} jumps").format(od['jumpcount_min'], od['jumpcount_max'])
            route_str = od['dst'].to_string()
            # If the destination is a station, include estimated SC time
            if 'sc_time' in od:
              route_str += ", SC: ~{0}s".format(od['sc_time'])
            print(("    === {0: >"+d_max_len+".2f}Ly ({1}) ===> {2}").format(od['hopsldist'], jumps_str, route_str))

      elif self.args.format == 'short':
        print("")
        sys.stdout.write(str(route[0]))
        for i in range(1, len(route)):
          od = output_data[i]
          if 'hop_route' in od:
            for j in range(0, len(od['hop_route'])):
              hd = od['hop_route'][j]
              sys.stdout.write(", {0}".format(str(hd['dst'])))
          else:
            sys.stdout.write(", {0}".format(str(od['dst'])))
        print("")

      elif self.args.format == 'csv':
        print("{0},{1},{2},{3}".format(route[0].system.name, route[0].name if route[0].name is not None else '', 0.0, 0))
        for i in range(1, len(route)):
          od = output_data[i]
          if 'hop_route' in od:
            for j in range(0, len(od['hop_route'])):
              hd = od['hop_route'][j]
              print("{0},{1},{2},{3}".format(hd['dst'].system.name, hd['dst'].name if hd['dst'].name is not None else '', hd['hdist'], hd['dst'].distance if hd['dst'].distance is not None else 0))
          else:
            print("{0},{1},{2},{3}".format(od['dst'].system.name, od['dst'].name if od['dst'].name is not None else '', od['hopsldist'], od['dst'].distance if od['dst'].distance is not None else 0))
        print_summary = False

      if print_summary:
        print("")
        print("Total distance: {0:.2f}Ly; total jumps: {1}; total SC distance: {2:d}Ls{3}; ETT: {4}".format(totaldist, totaljumps_str, totalsc, "+" if not totalsc_accurate else "", est_time_str))
        print("")

    else:
      print("")
      print("No viable route found :(")
      print("")


if __name__ == '__main__':
  a = Application(env.local_args, False)
  a.run()


