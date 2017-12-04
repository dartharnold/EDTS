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

  def __init__(self, args):
    self.args = args

    if self.args.suffix is None:
      m = re.match(r'^([0-9.]+)(.*)?', self.args.dist)
      if m is not None:
        if len(m.groups()) > 1:
          suffix = m.group(2).lower()
          for choice in Dist.SUFFICES:
            if choice.lower() == suffix:
              self.args.suffix = choice
          if self.args.suffix is None:
            log.error('Invalid suffix: {}', suffix)
            return False
          self.args.dist = m.group(1)
    self.args.dist = float(self.args.dist)

  def run(self):
    yield Result(distance = Dist(self.args.dist, self.args.suffix, self.args.result), source = self.args.dist, scale = self.args.result)
