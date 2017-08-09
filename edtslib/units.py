#!/usr/bin/env python

from __future__ import print_function
import argparse
import re

from .dist import *
from . import env
from . import util

app_name = "units"

log = util.get_logger(app_name)


class CaseInsensitiveList(list):
  def __init__(self, elements):
    super(CaseInsensitiveList, self).__init__([element.lower() for element in elements])

  def __contains__(self, other):
    return super(CaseInsensitiveList, self).__contains__(other.lower())

class Application(object):

  def __init__(self, arg, hosted, state = {}):
    choices = CaseInsensitiveList(Dist.SUFFICES)
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Convert distance scales", fromfile_prefix_chars="@", parents=ap_parents, prog = app_name)
    ap.add_argument("dist", metavar="distance", type=str, help="Distance to convert")
    ap.add_argument("suffix", metavar="from_scale", type=str, nargs='?', choices=choices, help="Source scale scale")
    ap.add_argument("result", metavar="scale", type=str, choices=choices, help="Resultant scale")
    self.args = ap.parse_args(arg)

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
    print("")
    print(Dist(self.args.dist, self.args.suffix, self.args.result))
    print("")

    return True
