import sys

if __name__ == '__main__':
  print "Loading environment..."
import env

import cmd
import edts

class EDI(cmd.Cmd):

  def __init__(self):
    # super (EDI, self).__init__()
    cmd.Cmd.__init__(self)
    self.prompt = "EDI> "

  def do_edts(self, args):
    app = edts.Application(args.split())
    app.run()
    return True

  def do_close_to(self, args):
    print "close-to"
    return True


  def do_quit(self, args):
    return False

  def do_exit(self, args):
    return False

  def postcmd(self, retval, line):
    if retval == False:
      return True

if __name__ == '__main__':
  EDI().cmdloop()
