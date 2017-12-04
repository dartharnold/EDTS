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

  def __init__(self, args):
    self.args = args

    if self.args.system is None:
      if self.args.filters is None:
        raise ArgumentError('Supply at least one system or filter!')
      # Find only by filter, defaulting to system-only search.
      self.args.system = ['.*' if self.args.regex else '*']
      if not self.args.stations:
        self.args.systems = True
    else:
      self.args.system = [self.args.system]

  def run(self):
    sys_matches = []
    stn_matches = []

    with env.use() as envdata:
      filters = filtering.entry_separator.join(self.args.filters) if self.args.filters is not None else None
      if self.args.regex:
        if self.args.systems or not self.args.stations:
          sys_matches = list(envdata.find_systems_by_regex(self.args.system[0], filters=filters))
        if self.args.stations or not self.args.systems:
          stn_matches = list(envdata.find_stations_by_regex(self.args.system[0], filters=filters))
      elif re.match(r'^\d+$', self.args.system[0]):
        id64 = int(self.args.system[0], 10)
        if self.args.systems or not self.args.stations:
          id64_match = system.from_id64(id64)
          sys_matches = [id64_match] if id64_match else []
      else:
        if self.args.systems or not self.args.stations:
          sys_matches = list(envdata.find_systems_by_glob(self.args.system[0], filters=filters))
        if self.args.stations or not self.args.systems:
          stn_matches = list(envdata.find_stations_by_glob(self.args.system[0], filters=filters))

      for system in sys_matches:
        if self.args.list_stations:
          stations = envdata.find_stations(sys_matches).get(system)
          stations.sort(key=lambda t: (t.distance if t.distance else sys.maxsize))
        else:
          stations = []
        yield Result(system = system, stations = stations)

      for station in stn_matches:
        yield Result(station = station)
