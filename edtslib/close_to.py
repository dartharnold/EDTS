#!/usr/bin/env python

from __future__ import print_function
import math

from .dist import Lightyears
from .opaque_types import Opaq
from . import env
from . import filtering
from . import util

app_name = "close_to"

log = util.get_logger(app_name)

default_num = 10
default_max_angle = 15.0

class Result(Opaq):
  def __init__(self, **args):
    self.system = args.get('system')
    self.distances = args.get('distances', {})
    self.stations = args.get('stations', [])

class Application(object):

  def __init__(self, **args):
    self._allegiance = args.get('allegiance')
    self._arrival_star = args.get('arrival_star')
    self._direction = args.get('direction')
    self._direction_angle = args.get('direction_angle')
    self._list_stations = args.get('list_stations')
    self._max_sc_distance = args.get('max_sc_distance')
    self._num = args.get('num', default_num)
    self._pad_size = args.get('pad_size')
    self._systems = args.get('systems')

  def run(self):
    with env.use() as envdata:
      # Add the system object to each system arg
      tmpsystems = envdata.parse_systems([d['system'] for d in self._systems])
      for d in self._systems:
        d['sysobj'] = tmpsystems.get(d['system'], None)
        if d['sysobj'] is None:
          log.error("Could not find start system \"{0}\"!", d['system'])
          return

      if self._direction is not None:
        direction_obj = envdata.parse_system(self._direction)
        if direction_obj is None:
          log.error("Could not find direction system \"{0}\"!", self._direction)
          return

    asys = []

    close_to_list = []
    for s in self._systems:
      min_dist = [filtering.Operator('>=', s['min_dist'])] if 'min_dist' in s else []
      max_dist = [filtering.Operator('<',  s['max_dist'])] if 'max_dist' in s else []
      close_to_list.append({filtering.PosArgs: [filtering.Operator('=', s['sysobj'])], 'distance': min_dist + max_dist})
    if not any([('max_dist' in s) for s in self._systems]):
      log.warning("database query will be slow unless at least one reference system has a max distance specified with --max-dist")

    filters = {}
    filters['close_to'] = close_to_list
    if self._pad_size is not None:
      # Retain previous behaviour: 'M' counts as 'any'
      filters['pad'] = [{filtering.PosArgs: [filtering.Operator('>=', filtering.PadSize('L') if self._pad_size == 'L' else filtering.Any)]}]
    if self._max_sc_distance is not None:
      filters['sc_distance'] = [{filtering.PosArgs: [filtering.Operator('<', self._max_sc_distance)]}]
    if self._allegiance is not None:
      filters['allegiance'] = [{filtering.PosArgs: [filtering.Operator('=', self._allegiance)]}]
    if self._num is not None:
      # Get extras, in case we get our reference systems as a result
      filters['limit'] = [{filtering.PosArgs: [filtering.Operator('=', self._num + len(self._systems))]}]
    if self._direction is not None:
      for entry in filters['close_to']:
        entry['direction'] = [filtering.Operator('=', direction_obj)]
        entry['angle'] = [filtering.Operator('<', self._direction_angle)]
    if self._arrival_star is not None:
      filters['arrival_star'] = self._arrival_star

    with env.use() as envdata:
      # Filter out our reference systems from the results
      names = [d['sysobj'].name for d in self._systems]
      asys = [s for s in envdata.find_all_systems(filters=envdata.convert_filter_object(filters)) if s.name not in names]
      if self._num:
        asys = asys[0:self._num]

        stations = {}
        if self._list_stations:
          stations = envdata.find_stations(asys)

        for i in range(0, len(asys)):
          stnlist = stations.get(asys[i], [])
          stnlist.sort(key=lambda t: t.distance if t.distance else 0.0)
          yield Result(system = asys[i], distances = { d['sysobj'].name: Lightyears(asys[i].distance_to(d['sysobj'])) for d in self._systems }, stations = stnlist)

  def all_angles_within(self, starts, dest1, dest2, max_angle):
    for d in starts:
      cur_dir = (dest1.position - d['sysobj'].position)
      test_dir = (dest2.position - d['sysobj'].position)
      if cur_dir.angle_to(test_dir) > max_angle:
        return False
    return True
