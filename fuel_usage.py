#!/usr/bin/env python

from __future__ import print_function
import argparse
import calc
import env
import logging
from math import log10, floor, fabs
import sys
from vector3 import Vector3
import ship

app_name = "fuel_usage"

log = logging.getLogger(app_name)

class Application:

  def __init__(self, arg, hosted, state = {}):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Plot jump distance matrix", fromfile_prefix_chars="@", parents = ap_parents, prog = app_name)
    ap.add_argument("-f", "--fsd", type=str, required=('ship' not in state), help="The ship's frame shift drive in the form 'A6 or '6A'")
    ap.add_argument("-m", "--mass", type=float, required=('ship' not in state), help="The ship's unladen mass excluding fuel")
    ap.add_argument("-t", "--tank", type=float, required=('ship' not in state), help="The ship's fuel tank size")
    ap.add_argument("-s", "--starting-fuel", type=float, required=False, help="The starting fuel quantity (default: tank size)")
    ap.add_argument("-c", "--cargo", type=int, default=0, help="Cargo on board the ship")
    ap.add_argument("systems", metavar="system", nargs='+', help="Systems")
    
    self.args = ap.parse_args(arg)

    if self.args.fsd is not None and self.args.mass is not None and self.args.tank is not None:
      self.ship = ship.Ship(self.args.fsd, self.args.mass, self.args.tank)
    elif 'ship' in state:
      self.ship = state['ship']
    else:
      log.error("Error: You must specify all of --fsd, --mass and --tank, or have previously set these")
      sys.exit(1)

    if self.args.starting_fuel == None:
      self.args.starting_fuel = self.ship.tank_size


  def run(self):
    systems = []
    for y in self.args.systems:
      s = env.data.parse_system(y)
      if s == None:
        log.error("Could not find system \"{0}\"!".format(y))
        return
      systems.append(s)

    print('')

    cur_fuel = self.args.starting_fuel

    output_data = [{'src': systems[0]}]

    for i in range(1, len(systems)):
      distance = systems[i-1].distance_to(systems[i])
      fuel_cost = self.ship.cost(distance, cur_fuel, self.args.cargo)
      cur_fuel -= fuel_cost
      is_ok = (fuel_cost < self.ship.fsd.maxfuel and cur_fuel >= 0.0)
      output_data.append({'src': systems[i-1], 'dst': systems[i], 'distance': distance, 'cost': fuel_cost, 'remaining': cur_fuel, 'ok': is_ok})

    d_max_len = 1.0
    c_max_len = 1.0
    f_max_len = 1.0
    f_min_len = 1.0
    for i in range(1, len(output_data)):
      od = output_data[i]
      d_max_len = max(d_max_len, od['distance'])
      c_max_len = max(c_max_len, od['cost'])
      f_max_len = max(f_max_len, od['remaining'])
      f_min_len = min(f_min_len, od['remaining'])
    # Length = "NNN.nn", so length = len(NNN) + 3 = log10(NNN) + 4
    d_max_len = str(int(floor(log10(fabs(d_max_len)))) + 4)
    c_max_len = str(int(floor(log10(fabs(c_max_len)))) + 4)
    f_max_len = int(floor(log10(fabs(f_max_len)))) + 4
    f_min_len = int(floor(abs(log10(fabs(f_min_len))))) + 5
    f_len = str(max(f_max_len, f_min_len))

    print(output_data[0]['src'].to_string())
    for i in range(1, len(output_data)):
      hop = output_data[i]
      dist = hop['src'].distance_to(hop['dst'])
      print(('    ={4}= {0: >'+d_max_len+'.2f}Ly / {1:>'+c_max_len+'.2f}T / {2:>'+f_len+'.2f}T ={4}=> {3}').format(dist, hop['cost'], hop['remaining'], hop['dst'].to_string(), '=' if hop['ok'] else '!'))

    print('')

if __name__ == '__main__':
  a = Application(env.local_args, False)
  a.run()

