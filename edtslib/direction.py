#!/usr/bin/env python

from __future__ import print_function

from .opaque_types import Location
from . import env
from . import util
from . import vector3

app_name = "direction"

log = util.get_logger(app_name)

class Result(object):
  def __init__(self, **args):
    self.angle = args.get('angle')
    self.direction = args.get('direction')
    self.check = args.get('check')
    self.opposite = args.get('opposite')
    self.deviation = args.get('deviation')
    self.tolerance = args.get('tolerance', 0)
    self.normalised = args.get('normalised', False)
    self.origin = args.get('origin')
    self.destination = args.get('destination')
    self.reference = args.get('reference')

class Application(object):

  def __init__(self, **args):
    self._check = args.get('check')
    self._normal = args.get('normal')
    self._tolerance = args.get('tolerance')
    self._reference = args.get('reference')
    self._systems = args.get('systems')

    if self._tolerance is not None:
      if self._tolerance < 0 or self._tolerance > 100:
        raise RuntimeError("Tolerance must be in range 0 to 100 (percent)!")

  def run(self):
    with env.use() as envdata:
      systems = envdata.parse_systems(self._systems)
      for y in self._systems:
        if y not in systems or systems[y] is None:
          log.error("Could not find system \"{0}\"!", y)
          return

      if self._reference:
        reference = envdata.parse_system(self._reference)
        if reference is None:
          log.error("Could not find reference system \"{0}\"!", self._reference)
          return
      else:
        reference = None

      a, b = [systems[y].position for y in self._systems]
      entry = Result(origin = Location(system = a), destination = Location(system = b), reference = Location(system = reference))
      if self._check:
        v = (a - reference.position).get_normalised()
        w = (b - reference.position).get_normalised()
        d = v.dot(w)
        log.debug('{0} vs {1} dot {2}', v, w, d)
        entry.deviation = 100 * (1 - d)
        entry.normalised = True
        if d >= 1.0 - float(self._tolerance) / 100:
          entry.check = True
        elif d < 0.0:
          entry.check = False
          entry.opposite = True
        else:
          entry.check = False
      else:
        v = b - a
        log.debug("From {0} to {1}", a, b)

        entry.direction = v
        if self._normal:
          log.debug("Normalising {0}", v)
          entry.direction = v.get_normalised()
          entry.normalised = True
        elif reference is not None:
          entry.angle = v.angle_to(a - reference.position)
      yield entry
