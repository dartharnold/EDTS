#!/usr/bin/env python

from __future__ import print_function
import fnmatch
import re
import sys

from . import env
from . import filtering
from . import system
from . import util

app_name = "find"

log = util.get_logger(app_name)

class Result(object):
  def __init__(self, **args):
    self.station = args.get('station')
    self.stations = args.get('stations', [])
    self.system = args.get('system')

class Application(object):

  def __init__(self, **args):
    self._filters = args.get('filters')
    self._pattern = args.get('pattern')
    self._stations = args.get('stations')
    self._systems = args.get('systems')
    self._regex = args.get('_regex')

    if self._pattern is None:
      if self._filters is None:
        raise RuntimeError('Supply at least one pattern or filter!')
      # Find only by filter, defaulting to system-only search.
      self._pattern = ['.*' if self._regex else '*']
      if not self._stations:
        self._systems = True
    else:
      self._pattern = [self._pattern]

  def run(self):
    sys_matches = []
    stn_matches = []

    with env.use() as envdata:
      filters = filtering.entry_separator.join(self._filters) if self._filters is not None else None
      if self._regex:
        if self._systems or not self._stations:
          sys_matches = list(envdata.find_systems_by_regex(self._pattern[0], filters=filters))
        if self._stations or not self._systems:
          stn_matches = list(envdata.find_stations_by_regex(self._pattern[0], filters=filters))
      elif re.match(r'^\d+$', self._pattern[0]):
        id64 = int(self._pattern[0], 10)
        if self._systems or not self._stations:
          id64_match = system.from_id64(id64)
          sys_matches = [id64_match] if id64_match else []
      else:
        if self._systems or not self._stations:
          sys_matches = list(envdata.find_systems_by_glob(self._pattern[0], filters=filters))
        if self._stations or not self._systems:
          stn_matches = list(envdata.find_stations_by_glob(self._pattern[0], filters=filters))

      for system in sys_matches:
        if self._list_stations:
          stations = envdata.find_stations(sys_matches).get(system)
          stations.sort(key=lambda t: (t.distance if t.distance else sys.maxsize))
        else:
          stations = []
        yield Result(system = system, stations = stations)

      for station in stn_matches:
        yield Result(station = station)
