#!/usr/bin/env python

from __future__ import print_function

from . import env
from . import pgnames
from . import util
from .opaque_types import Opaq

app_name = "coords"

log = util.get_logger(app_name)


class Result(Opaq):
  def __init__(self, **args):
    self.system = args.get('system')

class Application(object):

  def __init__(self, **args):
    self._systems = args.get('systems')

  def run(self):
    with env.use() as envdata:
      systems = envdata.parse_systems(self._systems)
      for name in self._systems:
        if name not in systems or systems[name] is None:
          pgsys = pgnames.get_system(name)
          if pgsys is not None:
            systems[name] = pgsys
          else:
            log.error("Could not find system \"{0}\"!", name)
            return

    for name in self._systems:
      yield Result(system = systems[name])
