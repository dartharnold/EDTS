#!/usr/bin/env python

import sys
import shlex
import logging
import time

if __name__ == '__main__':
  print "Loading environment..."
import env

log = logging.getLogger("edi")

import cmd
import edts
import close_to
import coords
import distance
import find

class EDI(cmd.Cmd):

  def __init__(self):
    # super (EDI, self).__init__()
    cmd.Cmd.__init__(self)
    self.prompt = "EDI> "

  def do_edts(self, args):
    try:
      app = edts.Application(shlex.split(args), True)
      app.run()
    except SystemExit:
      pass
    return True

  def do_distance(self, args):
    try:
      app = distance.Application(shlex.split(args), True)
      app.run()
    except SystemExit:
      pass
    return True

  def do_close_to(self, args):
    try:
      app = close_to.Application(shlex.split(args), True)
      app.run()
    except SystemExit:
      pass
    return True

  def do_coords(self, args):
    try:
      app = coords.Application(shlex.split(args), True)
      app.run()
    except SystemExit:
      return True

  def do_find(self, args):
    try:
      app = find.Application(shlex.split(args), True)
      app.run()
    except SystemExit:
      return True

  def do_set_verbosity(self, args):
    env.set_verbosity(int(args))
    return True

  def do_quit(self, args):
    return False

  def do_exit(self, args):
    return False

  def do_EOF(self, args):
    print
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
