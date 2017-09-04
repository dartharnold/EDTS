#!/usr/bin/env python

from __future__ import print_function
from edtslib import env
from edtslib import vsc

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  env.start()
  a = vsc.Application(env.local_args, False)
  a.run()
  env.stop()
