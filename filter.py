import argparse
import env
import logging
import math
import random
import vector3
from station import Station
from system import System

log = logging.getLogger("filter")

default_direction_angle = 15.0

def parse_filter_string(s):
  entries = s.split(",")
  output = {}
  for e in entries:
    kv = e.split("=")
    output[kv[0].strip()] = kv[1].strip()

  for k in output.keys():
    # -> system
    if k in ['direction']:
      output[k] = env.data.parse_system(output[k])
    # -> int
    if k in ['sc_distance']:
      output[k] = int(output[k])
    # -> string.upper
    if k in ['pad']:
      output[k] = output[k].upper()
    # -> float
    if k in ['direction_angle']:
      output[k] = float(output[k])

  return output


def filter_list(s_list, filters, limit = None, p_src_list = None):
  if p_src_list is not None:
    src_list = [s if isinstance(s, Station) else Station.none(s) for s in p_src_list]

  if (src is not None and 'direction' in filters):
    direction_obj = filters['direction']
    direction_angle = filters['direction_angle'] if 'direction_angle' in filters else default_direction_angle
    max_angle = direction_angle * math.pi / 180.0
    if direction_obj is None:
      log.error("Could not find direction target \"{0}\"!".format(self.args.direction))
      return

  asys = []
  maxdist = 0.0

  for s in sys_list:
    if isinstance(s, Station):
      st = s
      sy = s.system
    elif isinstance(s, KnownSystem):
      st = Station.none(s)
      sy = s
    else:
      st = env.data.parse_station(s)
      if st is not None:
        sy = st.system
      else:
        log.error("Could not find system in list: \"{0}\"!".format(s))

    if ('allegiance' in filters and filters['allegiance'] != sy.allegiance):
      continue

    has_stns = (sy.allegiance is not None)
    
    if ('pad' in filters and not has_stns):
      continue

    if ('direction' in filters and not self.all_angles_within(src_list, sy, direction_obj, max_angle)):
      continue

    if ('pad' in filters and filters['pad'] != 'L' and st.max_pad_size == 'L'):
      continue

    if ('sc_distance' in filters and st.distance is not None and st.distance > filters['sc_distance']):
      continue

    dist = math.fsum([s.distance_to(start) for start in src_list])

    if limit is None or len(asys) < limit or dist < maxdist:
      # We have a new contender; add it, sort by distance, chop to length and set the new max distance
      asys.append(s)
      # Sort the list by distance to ALL start systems
      asys.sort(key=lambda t: math.fsum([t.distance_to(start) for start in src_list]))

      asys = asys[0:self.args.num]
      maxdist = max(dist, maxdist)

    return asys


def all_angles_within(starts, dest1, dest2, max_angle):
  for d in starts:
    cur_dir = (dest1.position - d.system.position)
    test_dir = (dest2.position - d.system.position)
    if cur_dir.angle_to(test_dir) > max_angle:
      return False
  return True
