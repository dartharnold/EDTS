#!/usr/bin/env python

from __future__ import print_function
import argparse
import env
import logging
from vector3 import Vector3

app_name = "coords"

log = logging.getLogger(app_name)


class Application:

  def __init__(self, arg, hosted):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Display System Coordinates", fromfile_prefix_chars="@", parents=ap_parents, prog = app_name)
    ap.add_argument("system", metavar="system", type=str, nargs="*", help="The system to print the coordinates for")
    self.args = ap.parse_args(arg)

  def run(self):
    maxlen = 0
    for name in self.args.system:
      maxlen = max(maxlen, len(name))
      if not name.lower() in env.data.eddb_systems_by_name:
        log.error("Could not find system \"{0}\"!".format(self.args.system))
        return

    print("")
    for name in self.args.system:
      s = env.data.eddb_systems_by_name[name.lower()]
      fmtstr = "  {0:>" + str(maxlen) + "s}: [{1:>8.2f}, {2:>8.2f}, {3:>8.2f}]"
      print(fmtstr.format(name, s.position.x, s.position.y, s.position.z))
    print("")

    return True


if __name__ == '__main__':
  a = Application(env.local_args, False)
  a.run()

