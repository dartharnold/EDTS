#!/usr/bin/env python

from __future__ import print_function
from edtslib import edts
from edtslib import env

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  env.start()
  a = edts.Application(env.local_args, False)
  a.run()
  env.stop()
