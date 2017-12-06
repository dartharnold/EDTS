#!/usr/bin/env python

from __future__ import print_function

from . import env
from . import pgnames
from . import util

app_name = "coords"

log = util.get_logger(app_name)


class Result(object):
  def __init__(self, **args):
    self.system = args.get('system')

class Application(object):

  def __init__(self, args):
    self.args = args

  def run(self):
    with env.use() as envdata:
      systems = envdata.parse_systems(self.args.system)
      for name in self.args.system:
        if name not in systems or systems[name] is None:
          pgsys = pgnames.get_system(name)
          if pgsys is not None:
            systems[name] = pgsys
          else:
            log.error("Could not find system \"{0}\"!", name)
            return

    for name in self.args.system:
      yield Result(system = systems[name])
