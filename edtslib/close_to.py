#!/usr/bin/env python

from __future__ import print_function
import math

from .dist import Lightyears
from . import env
from . import filtering
from . import util

app_name = "close_to"

log = util.get_logger(app_name)

default_max_angle = 15.0

class Result(object):
  def __init__(self, **args):
    self.system = args.get('system')
    self.distances = args.get('distances', {})
    self.stations = args.get('stations', [])

class Application(object):

  def __init__(self, args = {}):
    self.args = args

  def run(self):
    with env.use() as envdata:
      # Add the system object to each system arg
      tmpsystems = envdata.parse_systems([d['system'] for d in self.args.system])
      for d in self.args.system:
        d['sysobj'] = tmpsystems.get(d['system'], None)
        if d['sysobj'] is None:
          log.error("Could not find start system \"{0}\"!", d['system'])
          return

      if self.args.direction is not None:
        direction_obj = envdata.parse_system(self.args.direction)
        if direction_obj is None:
          log.error("Could not find direction system \"{0}\"!", self.args.direction)
          return

    asys = []

    close_to_list = []
    for s in self.args.system:
      min_dist = [filtering.Operator('>=', s['min_dist'])] if 'min_dist' in s else []
      max_dist = [filtering.Operator('<',  s['max_dist'])] if 'max_dist' in s else []
      close_to_list.append({filtering.PosArgs: [filtering.Operator('=', s['sysobj'])], 'distance': min_dist + max_dist})
    if not any([('max_dist' in s) for s in self.args.system]):
      log.warning("database query will be slow unless at least one reference system has a max distance specified with --max-dist")

    filters = {}
    filters['close_to'] = close_to_list
    if self.args.pad_size is not None:
      # Retain previous behaviour: 'M' counts as 'any'
      filters['pad'] = [{filtering.PosArgs: [filtering.Operator('>=', filtering.PadSize('L') if self.args.pad_size == 'L' else filtering.Any)]}]
    if self.args.max_sc_distance is not None:
      filters['sc_distance'] = [{filtering.PosArgs: [filtering.Operator('<', self.args.max_sc_distance)]}]
    if self.args.allegiance is not None:
      filters['allegiance'] = [{filtering.PosArgs: [filtering.Operator('=', self.args.allegiance)]}]
    if self.args.num is not None:
      # Get extras, in case we get our reference systems as a result
      filters['limit'] = [{filtering.PosArgs: [filtering.Operator('=', self.args.num + len(self.args.system))]}]
    if self.args.direction is not None:
      for entry in filters['close_to']:
        entry['direction'] = [filtering.Operator('=', direction_obj)]
        entry['angle'] = [filtering.Operator('<', self.args.direction_angle)]
    if self.args.arrival_star is not None:
      filters['arrival_star'] = self.args.arrival_star

    with env.use() as envdata:
      # Filter out our reference systems from the results
      names = [d['sysobj'].name for d in self.args.system]
      asys = [s for s in envdata.find_all_systems(filters=envdata.convert_filter_object(filters)) if s.name not in names]
      if self.args.num:
        asys = asys[0:self.args.num]

        stations = {}
        if self.args.list_stations:
          stations = envdata.find_stations(asys)

        for i in range(0, len(asys)):
          stnlist = stations.get(asys[i], [])
          stnlist.sort(key=lambda t: t.distance if t.distance else 0.0)
          yield Result(system = asys[i], distances = { d['sysobj'].name: Lightyears(asys[i].distance_to(d['sysobj'])) for d in self.args.system }, stations = stnlist)

  def all_angles_within(self, starts, dest1, dest2, max_angle):
    for d in starts:
      cur_dir = (dest1.position - d['sysobj'].position)
      test_dir = (dest2.position - d['sysobj'].position)
      if cur_dir.angle_to(test_dir) > max_angle:
        return False
    return True
