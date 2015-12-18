#!/usr/bin/env python

from __future__ import print_function
import argparse
import env
import logging
import math
import sys
from vector3 import Vector3

app_name = "close_to"

log = logging.getLogger(app_name)

default_max_angle = 15.0

class ApplicationAction(argparse.Action):
  def __call__(self, parser, namespace, value, option_strings=None):
    n = vars(namespace)
    system_list = n['system'] if n['system'] is not None else []
    need_new = True
    i = 0
    while i < len(system_list):
      if self.dest not in system_list[i]:
        need_new = False
        break
      i += 1
    if need_new:
      system_list.append({})
    d = system_list[i]
    if self.dest == 'system':
      d['system'] = value[0]
    else:
      d[self.dest] = value
      setattr(namespace, self.dest, value)
    setattr(namespace, 'system', system_list)


class Application:

  def __init__(self, arg, hosted, state = {}):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Find Nearby Systems", fromfile_prefix_chars="@", parents = ap_parents, prog = app_name)
    ap.add_argument("-n", "--num", type=int, required=False, default=10, help="Show the specified number of nearby systems")
    ap.add_argument("-d", "--min-dist", type=int, required=False, action=ApplicationAction, help="Exclude systems less than this distance from reference")
    ap.add_argument("-m", "--max-dist", type=int, required=False, action=ApplicationAction, help="Exclude systems further this distance from reference")
    ap.add_argument("-a", "--allegiance", type=str, required=False, default=None, help="Only show systems with the specified allegiance")
    ap.add_argument("-s", "--max-sc-distance", type=float, required=False, help="Only show systems with a starport less than this distance from entry point")
    ap.add_argument("-p", "--pad-size", required=False, type=str.upper, choices=['S','M','L'], help="Only show systems with stations matching the specified pad size")
    ap.add_argument("-l", "--list-stations", default=False, action='store_true', help="List stations in returned systems")
    ap.add_argument("--direction", type=str, required=False, help="A system or set of coordinates that returned systems must be in the same direction as")
    ap.add_argument("--direction-angle", type=float, required=False, default=default_max_angle, help="The maximum angle, in degrees, allowed for the direction check")
    
    ap.add_argument("system", metavar="system", nargs=1, action=ApplicationAction, help="The system to find other systems near")

    remaining = arg
    args = argparse.Namespace()
    while remaining:
      args, remaining = ap.parse_known_args(remaining, namespace=args)
      self.args = args
    if not hasattr(self, 'args'):
      self.args = ap.parse_args(arg)

    if self.args.pad_size is not None:
      self.args.stations = True

    self.allow_outposts = (self.args.pad_size != "L")

  def run(self):
    # Add the system object to each system arg
    for d in self.args.system:
      d['sysobj'] = env.data.parse_system(d['system'])
      if d['sysobj'] == None:
        log.error("Could not find start system \"{0}\"!".format(d['system']))
        return
    # Create a list of names for quick checking in the main loop
    start_names = [d['system'].lower() for d in self.args.system]

    if self.args.direction != None:
      direction_obj = env.data.parse_system(self.args.direction)
      max_angle = self.args.direction_angle * math.pi / 180.0
      if direction_obj == None:
        log.error("Could not find direction system \"{0}\"!".format(self.args.direction))
        return

    asys = []
    
    maxdist = 0.0

    for s in env.data.eddb_systems:
      # If we don't care about allegiance, or we do and it matches...
      if s.name.lower() not in start_names and (self.args.allegiance == None or s.allegiance == self.args.allegiance):
        has_stns = (s.allegiance != None)
        # If we have stations, or we don't care...
        if has_stns or self.args.pad_size == None:
          # Check if the direction matches, if we care
          if self.args.direction == None or self.all_angles_within(self.args.system, s, direction_obj, max_angle):
            # If we *don't* have stations (because we don't care), or the stations match the requirements...
            matching_stns = env.data.get_stations(s)
            if not self.allow_outposts:
              matching_stns = [st for st in matching_stns if st.max_pad_size == "L"]
            if self.args.max_sc_distance != None:
              matching_stns = [st for st in matching_stns if (st.distance != None and st.distance < self.args.max_sc_distance)]
            if not has_stns or len(matching_stns) > 0:
              dist = 0.0 # The total distance from this system to ALL start systems
              is_ok = True
              for d in self.args.system:
                start = d['sysobj']
                this_dist = s.distance_to(start)
                if 'min_dist' in d and this_dist < d['min_dist']:
                  is_ok = False
                  break
                if 'max_dist' in d and this_dist > d['max_dist']:
                  is_ok = False
                  break
                dist += this_dist

              if not is_ok:
                continue
                
              if len(asys) < self.args.num or dist < maxdist:
                # We have a new contender; add it, sort by distance, chop to length and set the new max distance
                asys.append(s)
                # Sort the list by distance to ALL start systems
                asys.sort(key=lambda t: math.fsum([t.distance_to(e['sysobj']) for e in self.args.system]))

                asys = asys[0:self.args.num]
                maxdist = max(dist, maxdist)


    if not len(asys):
      print("")
      print("No matching systems")
      print("")
    else:
      print("")
      print("Matching systems close to {0}:".format(', '.join([d["system"] for d in self.args.system])))
      print("")
      for i in range(0, len(asys)):
        if len(self.args.system) == 1:
          print("    {0} ({1:.2f}Ly)".format(asys[i].name, asys[i].distance_to(self.args.system[0]['sysobj'])))
        else:
          print("    {0}".format(asys[i].name, " ({0:.2f}Ly)".format(asys[i].distance_to(self.args.system[0]['sysobj']))))
        if self.args.list_stations and asys[i].id in env.data.eddb_stations_by_system:
          stlist = env.data.eddb_stations_by_system[asys[i].id]
          stlist.sort(key=lambda t: t.distance)
          for stn in stlist:
            print("        {0}".format(stn.to_string(False)))
      print("")
      if len(self.args.system) > 1:
        for d in self.args.system:
          print("  Distance from {0}:".format(d['system']))
          print("")
          asys.sort(key=lambda t: t.distance_to(d['sysobj']))
          for i in range(0, len(asys)):
            # Print distance from the current candidate system to the current start system
            print("    {0} ({1:.2f}Ly)".format(asys[i].name, asys[i].distance_to(d['sysobj'])))
          print("")


  def all_angles_within(self, starts, dest1, dest2, max_angle):
    for d in starts:
      cur_dir = (dest1.position - d['sysobj'].position)
      test_dir = (dest2.position - d['sysobj'].position)
      if cur_dir.angle_to(test_dir) > max_angle:
        return False
    return True


if __name__ == '__main__':
  a = Application(env.local_args, False)
  a.run()

