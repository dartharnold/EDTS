#!/usr/bin/env python

from __future__ import print_function
import argparse

from .cow import ColumnObjectWriter
from . import env
from . import pgnames
from . import util

app_name = "coords"

log = util.get_logger(app_name)


class Application(object):

  def __init__(self, arg, hosted, state = {}):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Display System Coordinates", fromfile_prefix_chars="@", parents=ap_parents, prog = app_name)
    ap.add_argument("-f", "--full-width", default=False, action='store_true', help="Do not restrict number of significant figures")
    ap.add_argument("system", metavar="system", type=str, nargs="*", help="The system to print the coordinates for")
    self.args = ap.parse_args(arg)

  def run(self):
    maxlen = 0
    with env.use() as envdata:
      systems = envdata.parse_systems(self.args.system)
      for name in self.args.system:
        maxlen = max(maxlen, len(name))
        if name not in systems or systems[name] is None:
          pgsys = pgnames.get_system(name)
          if pgsys is not None:
            systems[name] = pgsys
          else:
            log.error("Could not find system \"{0}\"!", name)
            return

    fmt = '8g' if self.args.full_width else '8.2f'

    cow = ColumnObjectWriter(4, '>', '')
    for name in self.args.system:
      s = systems[name]
      coords = [('{:' + fmt + '}').format(coord) for coord in s.position]
      cow.add([
        s,
        ': [',
        coords[0],
        ', ',
        coords[1],
        ', ',
        coords[2],
        ']',
        " +/- {0:.0f}LY in each axis".format(s.uncertainty) if s.uncertainty != 0.0 else ""
      ])
    print("")
    cow.out()
    print("")

    return True
