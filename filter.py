import argparse
import collections
import env
import logging
import math
import random
import vector3
from station import Station
from system import System

log = logging.getLogger("filter")

default_direction_angle = 15.0

entry_separator = ';'
entry_subseparator = ','
entry_kvseparator = '='


class AnyType(object):
  def __str__(self):
    return "Any"
  def __repr__(self):
    return "Any"
Any = AnyType()

class Not(object):
  def __init__(self, val):
    self.value = val
  def __str__(self):
    return "Not({})".format(self.value)
  def __repr__(self):
    return "Not({})".format(self.value)


def _parse_system(s):
  with env.use() as data:
    return data.parse_system(s)


_conversions = {
  'min_sc_distance': {'max': 1,    'special': [Any],            'fn': int},
  'max_sc_distance': {'max': 1,    'special': [Any],            'fn': int},
  'pad':             {'max': 1,    'special': [Any, None, Not], 'fn': str.upper},
  'direction':       {'max': None, 'special': [],               'fn': {0: _parse_system, 'angle': float}},
  'close_to':        {'max': None, 'special': [],               'fn': {0: _parse_system, 'min': float, 'max': float}},
  'allegiance':      {'max': 1,    'special': [Any, None, Not], 'fn': str},
  'limit':           {'max': 1,    'special': [],               'fn': int},
}


def _global_conv(val, specials = []):
  if val.lower() == "any" and Any in specials:
    return (Any, False, None)
  elif val.lower() == "none" and None in specials:
    return (None, False, None)
  elif len(val) > 0 and val[0] == '!' and Not in specials:
    return (_global_conv(val[1:]), True, Not)
  else:
    return (val, True, None)


def parse_filter_string(s):
  entries = s.split(entry_separator)
  output = {}
  # For each separate filter entry...
  for entry in entries:
    kv = entry.split(entry_kvseparator, 1)
    key = kv[0].strip()
    if key in _conversions:
      multiple = (_conversions[key]['max'] != 1)
    else:
      raise KeyError("Unexpected filter key provided: {0}".format(k))
    kvlist = kv[1].strip().split(entry_subseparator)
    # Do we have sub-entries, or just a simple key=value ?
    if multiple or len(kvlist) > 1:
      idx = 0
      value = {}
      # For each sub-entry...
      for e in kvlist:
        ekv = [s.strip() for s in e.split(entry_kvseparator)]
        # Is this sub-part a subkey=value?
        if len(ekv) > 1:
          value[ekv[0].strip()] = ekv[1].strip()
        else:
          # If not, give it a position-based index
          value[idx] = ekv[0].strip()
          idx += 1
    else:
      value = kvlist[0].strip()
    # Set the value and move on
    if multiple:
      if key not in output:
        output[key] = []
      output[key].append(value)
    else:
      output[key] = value

  # For each result
  for k in output.keys():
    # Do we know about it?
    if k in _conversions:
      if _conversions[k]['max'] not in [None, 1] and len(output[k]) > _conversions[k]['max']:
        raise KeyError("Filter key {} provided more than its maximum {} times".format(k, _conversions[k]['max']))
      # Is it a complicated one, or a simple key=value?
      if isinstance(_conversions[k]['fn'], collections.Iterable):
        # For each present subkey, check if we know about it and convert it if so
        outlist = output[k] if _conversions[k]['max'] != 1 else [output[k]]
        for outentry in outlist:
          for ek in outentry:
            if ek in _conversions[k]['fn']:
              outentry[ek], continue_conv, post_conv = _global_conv(outentry[ek], []) # TODO: Support specials in inner args?
              if continue_conv:
                outentry[ek] = _conversions[k]['fn'][ek](outentry[ek])
              if post_conv:
                outentry[ek] = post_conv(outentry[ek])
            else:
              raise KeyError("Unexpected filter subkey provided: {0}".format(ek))
      else:
        output[k], continue_conv, post_conv = _global_conv(output[k], _conversions[k]['special'])
        if continue_conv:
          output[k] = _conversions[k]['fn'](output[k])
        if post_conv:
          output[k] = post_conv(output[k])
    else:
      raise KeyError("Unexpected filter key provided: {0}".format(k))

  return output


def generate_filter_sql(filters):
  select_str = []
  filter_str = []
  group_str = []
  order_str = []
  limit = None
  select_params = []
  filter_params = []
  group_params = []
  order_params = []
  req_tables = set()
  idx = 0

  if 'close_to' in filters:
    start_idx = idx
    req_tables.add('systems')
    for entry in filters['close_to']:
      pos = entry[0].position
      select_str.append("(((? - systems.pos_x) * (? - systems.pos_x)) + ((? - systems.pos_y) * (? - systems.pos_y)) + ((? - systems.pos_z) * (? - systems.pos_z))) AS diff{0}".format(idx))
      select_params += [pos.x, pos.x, pos.y, pos.y, pos.z, pos.z]
      if 'min' in entry and entry['min']:
        filter_str.append("diff{0} >= ? * ?".format(idx))
        filter_params += [entry['min'], entry['min']]
      if 'max' in entry and entry['max']:
        filter_str.append("diff{0} <= ? * ?".format(idx))
        filter_params += [entry['max'], entry['max']]
      idx += 1
    order_str.append("+".join(["diff{}".format(i) for i in range(start_idx, idx)]))
  if 'direction' in filters:
    start_idx = idx
    req_tables.add('systems')
    for entry in filters['direction']:
      angle = entry.get('angle', 15.0) * math.pi / 180.0
      select_str.append("vec3_angle(systems.pos_x,systems.pos_y,systems.pos_z,?,?,?) AS diff{}".format(idx))
      select_params += [entry[0].position.x, entry[0].position.y, entry[0].position.z]
      filter_str.append("diff{} < ?".format(idx))
      filter_params.append(angle)
      idx += 1
    order_str.append("+".join(["diff{}".format(i) for i in range(start_idx, idx)]))
  if 'allegiance' in filters:
    req_tables.add('systems')
    if filters['allegiance'] is Any or (isinstance(filters['allegiance'], Not) and filters['allegiance'].value is None):
      filter_str.append("systems.allegiance IS NOT NULL AND systems.allegiance != 'None'")
    elif filters['allegiance'] is None or (isinstance(filters['allegiance'], Not) and filters['allegiance'].value is Any):
      filter_str.append("systems.allegiance IS NULL OR systems.allegiance == 'None'")
    elif isinstance(filters['allegiance'], Not):
      filter_str.append("systems.allegiance != ?")
      filter_params.append(filters['allegiance'].value)
    else:
      filter_str.append("systems.allegiance = ?")
      filter_params.append(filters['allegiance'])
  if 'pad' in filters:
    req_tables.add('stations')
    if filters['pad'] is None:
      filter_str.append("stations.max_pad_size IS NULL") # Should never hit, resulting in no matches for this system
    elif filters['pad'] is Any:
      filter_str.append("stations.max_pad_size IS NOT NULL")
    else:
      filter_str.append("stations.max_pad_size = ?")
      filter_params.append(filters['pad'])
  if 'max_sc_distance' in filters and filters['max_sc_distance'] is not Any:
    req_tables.add('stations')
    filter_str.append("stations.sc_distance < ?")
    filter_params.append(filters['max_sc_distance'])
    order_str.append("stations.sc_distance")
  if 'min_sc_distance' in filters and filters['min_sc_distance'] is not Any:
    req_tables.add('stations')
    filter_str.append("stations.sc_distance >= ?")
    filter_params.append(filters['min_sc_distance'])
    order_str.append("stations.sc_distance")
  if 'limit' in filters:
    limit = int(filters['limit'])

  return {
    'select': (select_str, select_params),
    'filter': (filter_str, filter_params),
    'order': (order_str, order_params),
    'group': (group_str, group_params),
    'limit': limit,
    'tables': list(req_tables)
  }


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
    elif isinstance(s, KnownSystem):
      st = Station.none(s)
      sy = s
    else:
      st = env.data.parse_station(s)
      if st is not None:
        sy = st.system
      else:
        log.error("Could not find system in list: \"{0}\"!".format(s))
        continue

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
