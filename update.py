#!/usr/bin/env python

from __future__ import print_function, division
from edtslib import env
from edtslib import update

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  a = update.Application(env.local_args, False)
  a.run()