#!/usr/bin/env python

from __future__ import print_function
from edtslib import env
from edtslib import fuel_usage

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  env.start()
  a = fuel_usage.Application(env.local_args, False)
  a.run()
  env.stop()
