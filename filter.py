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
    elif k in ['min_sc_distance', 'max_sc_distance']:
      output[k] = int(output[k])
    # -> string.upper
    elif k in ['pad']:
      output[k] = output[k].upper()
    # -> float
    elif k in ['direction_angle', 'min_distance', 'max_distance']:
      output[k] = float(output[k])
    else:
      raise KeyError("Unexpected filter key provided: {0}".format(k))

  return output


def filter_list(s_list, filters, limit = None, p_src_list = None):
  src_list = None
  if p_src_list is not None:
    src_list = [s if isinstance(s, Station) else Station.none(s) for s in p_src_list]

  if (src_list is not None and 'direction' in filters):
    direction_obj = filters['direction']
    direction_angle = filters['direction_angle'] if 'direction_angle' in filters else default_direction_angle
    max_angle = direction_angle * math.pi / 180.0
    if direction_obj is None:
      log.error("Could not find direction target \"{0}\"!".format(self.args.direction))
      return

  asys = []
  maxdist = 0.0

  for s in s_list:
    if isinstance(s, Station):
      st = s
      sy = s.system
    elif isinstance(s, System):
      st = Station.none(s)
      sy = s
    else:
      st = env.data.parse_station(s)
      if st is not None:
        sy = st.system
      else:
        log.error("Could not find system in list: \"{0}\"!".format(s))

    if ('allegiance' in filters and ((not hasattr(sy, 'allegiance')) or filters['allegiance'] != sy.allegiance)):
      continue

    has_stns = (hasattr(sy, 'allegiance') and sy.allegiance is not None)
    
    if ('pad' in filters and not has_stns):
      continue

    if ('direction' in filters and src_list is not None and not self.all_angles_within(src_list, sy, direction_obj, max_angle)):
      continue

    if ('pad' in filters and filters['pad'] != 'L' and st.max_pad_size == 'L'):
      continue

    if ('min_sc_distance' in filters and (st.distance is None or st.distance < filters['min_sc_distance'])):
      continue
    if ('max_sc_distance' in filters and (st.distance is None or st.distance > filters['max_sc_distance'])):
      continue

    dist = None
    if src_list is not None:
      dist = math.fsum([s.distance_to(start) for start in src_list])

      if ('min_distance' in filters and any([s.distance_to(start) < filters['min_distance'] for start in src_list])):
        continue
      if ('max_distance' in filters and any([s.distance_to(start) > filters['max_distance'] for start in src_list])):
        continue

    if limit is None or len(asys) < limit or (dist is None or dist < maxdist):
      # We have a new contender; add it, sort by distance, chop to length and set the new max distance
      asys.append(s)
      # Sort the list by distance to ALL start systems
      if src_list is not None:
        asys.sort(key=lambda t: math.fsum([t.distance_to(start) for start in src_list]))

      if limit is not None:
        asys = asys[0:limit]
      maxdist = max(dist, maxdist)

  return asys


def all_angles_within(starts, dest1, dest2, max_angle):
  for d in starts:
    cur_dir = (dest1.position - d.position)
    test_dir = (dest2.position - d.position)
    if cur_dir.angle_to(test_dir) > max_angle:
      return False
  return True
