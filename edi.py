#!/usr/bin/env python

from __future__ import print_function
import sys
import shlex
import logging
import time
import cmd
import argparse

if __name__ == '__main__':
  print("Loading environment...")
import env

log = logging.getLogger("edi")

import fsd
import ship

import edts
import close_to
import coords
import distance
import find
import galmath

class EDI(cmd.Cmd):

  def __init__(self):
    # super (EDI, self).__init__()
    cmd.Cmd.__init__(self)
    self.prompt = "EDI> "
    self.state = {}

  def do_application(self, ns, args):
    try:
      args = shlex.split(args)
      app = ns.Application(args, True, self.state)
      app.run()
    except KeyboardInterrupt:
      log.debug("Interrupt detected")
      pass
    except SystemExit:
      pass
    except Exception, e:
      log.error("Error in application: {}".format(e))
      pass
    return True

  def help_application(self, ns):
    try:
      ns.Application(['-h'], True, self.state).run()
    except SystemExit:
      pass
    return True

  #
  # Begin commands
  #

  def help_edts(self):
    return self.help_application(edts)

  def do_edts(self, args):
    return self.do_application(edts, args)

  def help_distance(self):
    return self.help_application(distance)

  def do_distance(self, args):
    return self.do_application(distance, args)

  def help_raikogram(self):
    return self.help_distance()

  def do_raikogram(self, args):
    return self.do_distance(args)

  def help_close_to(self):
    return self.help_application(close_to)

  def do_close_to(self, args):
    return self.do_application(close_to, args)

  def help_coords(self):
    return self.help_application(coords)

  def do_coords(self, args):
    return self.do_application(coords, args)

  def help_find(self):
    return self.help_application(find)

  def do_find(self, args):
    return self.do_application(find, args)

  def help_galmath(self):
    return self.help_application(galmath)

  def do_galmath(self, args):
    return self.do_application(galmath, args)

  def help_set_verbosity(self):
    print("usage: set_verbosity N")
    print("")
    print("Set log level (0-3)")
    return True

  def do_set_verbosity(self, args):
    env.set_verbosity(int(args))
    return True

  def help_set_ship(self):
    print("usage: set_ship -m N -t N -f NC [-c N]")
    print("")
    print("Set the current ship to be used in other commands")
    return True

  def do_set_ship(self, args):
    ap = argparse.ArgumentParser(fromfile_prefix_chars="@", prog = "set_ship")
    ap.add_argument("-f", "--fsd", type=str, required=True, help="The ship's frame shift drive in the form 'A6 or '6A'")
    ap.add_argument("-m", "--mass", type=float, required=True, help="The ship's unladen mass excluding fuel")
    ap.add_argument("-t", "--tank", type=float, required=True, help="The ship's fuel tank size")
    ap.add_argument("-c", "--cargo", type=int, default=0, help="The ship's cargo capacity")
    argobj = ap.parse_args(shlex.split(args))
    self.state['ship'] = ship.Ship(fsd.FSD(argobj.fsd), argobj.mass, argobj.tank, argobj.cargo)
    return True

  def help_quit(self):
    print("Exit this shell by typing \"exit\", \"quit\" or Control-D.")
    return True

  def do_quit(self, args):
    return False

  def help_exit(self):
    return self.help_quit()

  def do_exit(self, args):
    return False

  #
  # End commands
  #

  def help_EOF(self):
    return self.help_quit()

  def do_EOF(self, args):
    print()
    return False

  def precmd(self, line):
    self.start_time = time.time()
    return line

  def postcmd(self, retval, line):
    if retval == False:
      return True
    log.debug("Command complete, time taken: {0:.4f}s".format(time.time() - self.start_time))

if __name__ == '__main__':
  EDI().cmdloop()
