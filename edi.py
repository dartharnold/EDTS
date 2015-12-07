#!/usr/bin/env python

from __future__ import print_function
import sys
import shlex
import logging
import time
import cmd

if __name__ == '__main__':
  print("Loading environment...")
import env

log = logging.getLogger("edi")

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

  def help_edts(self):
    try:
      edts.Application(['-h'], True).run()
    except SystemExit:
      pass
    return True

  def do_edts(self, args):
    try:
      app = edts.Application(shlex.split(args), True)
      app.run()
    except KeyboardInterrupt:
      log.debug("Interrupt detected")
      pass
    except SystemExit:
      pass
    return True

  def help_distance(self):
    try:
      distance.Application(['-h'], True).run()
    except SystemExit:
      pass
    return True

  def do_distance(self, args):
    try:
      app = distance.Application(shlex.split(args), True)
      app.run()
    except KeyboardInterrupt:
      log.debug("Interrupt detected")
      pass
    except SystemExit:
      pass
    return True

  def help_raikogram(self):
    return self.help_distance()

  def do_raikogram(self, args):
    return self.do_distance(args)

  def help_close_to(self):
    try:
      close_to.Application(['-h'], True).run()
    except SystemExit:
      pass
    return True

  def do_close_to(self, args):
    try:
      app = close_to.Application(shlex.split(args), True)
      app.run()
    except KeyboardInterrupt:
      log.debug("Interrupt detected")
      pass
    except SystemExit:
      pass
    return True

  def help_coords(self):
    try:
      coords.Application(['-h'], True).run()
    except SystemExit:
      pass
    return True

  def do_coords(self, args):
    try:
      app = coords.Application(shlex.split(args), True)
      app.run()
    except KeyboardInterrupt:
      log.debug("Interrupt detected")
      pass
    except SystemExit:
      return True

  def help_find(self):
    try:
      find.Application(['-h'], True).run()
    except SystemExit:
      pass
    return True

  def do_find(self, args):
    try:
      app = find.Application(shlex.split(args), True)
      app.run()
    except KeyboardInterrupt:
      log.debug("Interrupt detected")
      pass
    except SystemExit:
      return True

  def help_galmath(self):
    try:
      find.Application(['-h'], True).run()
    except SystemExit:
      pass
    return True

  def do_galmath(self, args):
    try:
      app = galmath.Application(shlex.split(args), True)
      app.run()
    except KeyboardInterrupt:
      log.debug("Interrupt detected")
      pass
    except SystemExit:
      return True

  def help_set_verbosity(self):
    print("usage: set_verbosity N")
    print("")
    print("Set log level (0-3)")
    return True

  def do_set_verbosity(self, args):
    env.set_verbosity(int(args))
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
