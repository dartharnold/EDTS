#!/usr/bin/env python

from __future__ import print_function
import argparse
from edtslib import env
from edtslib import vsc

def parse_args(arg, hosted, state):
  ap_parents = [env.arg_parser] if not hosted else []
  ap = argparse.ArgumentParser(description = "Read and write the visited stars cache", fromfile_prefix_chars="@", parents = ap_parents, prog = vsc.app_name)
  subparsers = ap.add_subparsers()
  bp = subparsers.add_parser("batch", help="Batch import jobs")
  bp.add_argument("-c", "--clean", default=False, action="store_true", help="Delete any existing cache rather than back it up")
  bp.add_argument("-d", "--directory", help="Directory where Elite looks for ImportStars.txt")
  bp.add_argument("-n", "--no-import", default=False, action="store_true", help="Only create ImportStars files, don't copy to game client")
  bp.add_argument("starfile", metavar="filename")
  bp.add_argument("dictfile", nargs='?', help="Destination file")
  bp.set_defaults(func=vsc.Application.run_batch)
  ip = subparsers.add_parser("import", help="Use Elite client to run import job")
  ip.add_argument("-c", "--clean", default=False, action="store_true", help="Delete any existing cache rather than back it up")
  ip.add_argument("-d", "--directory", help="Directory where Elite looks for ImportStars.txt")
  ip.add_argument("importfile", metavar="filename")
  ip.add_argument("cachefile")
  ip.set_defaults(func=vsc.Application.run_import)
  rp = subparsers.add_parser("read", help="Read from star cache")
  rp.add_argument("readfile", metavar="filename")
  rp.set_defaults(func=vsc.Application.run_read)
  wp = subparsers.add_parser("write", help="Write to star cache")
  wp.add_argument("writefile", metavar="filename")
  wp.add_argument("-i", "--importfile", metavar="filename", nargs='?', help="File with list of stars")
  wp.add_argument("-r", "--recent", default=False, action="store_true", help="Create in RecentlyVisitedStars format")
  wp.add_argument("-v", "--version", type=int, required=False, help="File version to write")
  wp.add_argument("filters", metavar="filters", nargs='*')
  wp.set_defaults(func=vsc.Application.run_write)

  return ap.parse_args(arg)

def run(args, hosted = False, state = {}):
  vsc.Application(parse_args(args, hosted, state)).run()

if __name__ == '__main__':
  env.configure_logging(env.global_args.log_level)
  env.start()
  run(env.local_args)
  env.stop()
