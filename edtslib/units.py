#!/usr/bin/env python

from __future__ import print_function
import re

from .dist import *
from . import env
from . import util

app_name = "units"

log = util.get_logger(app_name)

class Result(object):
  def __init__(self, **args):
    self.distance = args.get('distance')
    self.scale = args.get('scale')
    self.source = args.get('source')

class Application(object):

  def __init__(self, **args):
    self._distance = args.get('distance')
    self._result = args.get('result')
    self._suffix = args.get('suffix')

    if self._suffix is None:
      m = re.match(r'^([0-9.]+)(.*)?', str(self._distance))
      if m is not None:
        if len(m.groups()) > 1:
          suffix = m.group(2).lower()
          if suffix:
              for choice in Dist.SUFFICES:
                if choice.lower() == suffix:
                  self._suffix = choice
              if self._suffix is None:
                raise RuntimeError('Invalid suffix: {}', suffix)
          self._distance = m.group(1)
    self._distance = float(self._distance)

  def run(self):
    yield Result(distance = Dist(self._distance, self._suffix, self._result), source = self._distance, scale = self._result)
