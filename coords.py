#!/usr/bin/env python

from __future__ import print_function
from edtslib import coords
from edtslib import env

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  env.start()
  a = coords.Application(env.local_args, False)
  a.run()
  env.stop()
