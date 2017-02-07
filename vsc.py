#!/usr/bin/env python

from __future__ import print_function
import argparse
import env
import filter
import logging
import os
import shutil
import starcache
import sys
import time
import vector3

app_name = "vsc"

log = logging.getLogger(app_name)

class Application(object):

  def __init__(self, arg, hosted, state = {}):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Read and write the visited stars cache", fromfile_prefix_chars="@", parents = ap_parents, prog = app_name)
    subparsers = ap.add_subparsers()
    bp = subparsers.add_parser("batch", help="Batch import jobs")
    bp.add_argument("-d", "--directory", help="Directory where Elite looks for ImportStars.txt")
    bp.add_argument("starfile", metavar="filename")
    bp.set_defaults(func=self.run_batch)
    ip = subparsers.add_parser("import", help="Use Elite client to run import job")
    ip.add_argument("-d", "--directory", help="Directory where Elite looks for ImportStars.txt")
    ip.add_argument("importfile", metavar="filename")
    ip.add_argument("cachefile")
    ip.set_defaults(func=self.run_import)
    rp = subparsers.add_parser("read", help="Read from star cache")
    rp.add_argument("readfile", metavar="filename")
    rp.set_defaults(func=self.run_read)
    wp = subparsers.add_parser("write", help="Write to star cache")
    wp.add_argument("writefile", metavar="filename")
    wp.add_argument("-r", "--recent", default=False, action="store_true", help="Create int RecentlyVisitedStars format")
    wp.add_argument("filters", metavar="filters", nargs='*')
    wp.set_defaults(func=self.run_write)

    self.args = ap.parse_args(arg)

  def run(self):
    with env.use() as envdata:
      self.args.func(envdata, self.args)

  def batch_read(self, envdata, id64list):
    missing = { str(id64): True for id64 in id64list }
    for s in envdata.find_systems_by_id64(id64list):
      print(s.name)
      id64 = str(s.id64)
      if id64 in missing:
        del(missing[id64])
    for id64 in missing.keys():
      print(id64)

  def run_batch(self, envdata, args):
    data = []
    with open(args.starfile, 'r') as f:
      for d in f:
        data.append(d.strip())

    if not len(data):
      log.warning("No stars in {}...".format(args.starfile))
      return

    cacheformat = 'VisitedStarsCache{}.dat'
    importformat = starcache.IMPORTFORMAT
    names = starcache.create_import_list_files(data, importformat)
    for name in names:
      cachefile = cacheformat.format(name)
      importfile = importformat.format(name)
      log.info("Importing from {}".format(importfile))
      self.game_import({
        'cachefile': cachefile,
        'directory': args.directory,
        'importfile': importfile
      })

    id64s = starcache.calculate_id64s_from_list_files(args.starfile, cacheformat.format('Full'), [cacheformat.format(n) for n in names if n != 'Full'])
    print(id64s)

  def client_import(self, importsrc, importdst, imported, recent):
    try:
      log.debug("Writing {}...".format(importdst))
      shutil.copyfile(importsrc, importdst)
      spoke = False
      while os.path.isfile(importdst):
        time.sleep(1)
        if not spoke:
          log.info("Waiting for game client to log in...")
          spoke = True
      spoke = False
      while os.path.isfile(recent):
        time.sleep(1)
        if not spoke:
          log.info("Waiting for game client to log out...")
          spoke = True
    except IOError:
      log.error("Failed to copy {} to {}".format(importsrc, importdst))
    except KeyboardInterrupt:
      os.unlink(importdst)
      log.warning("Interrupted!")

  def game_import(self, args):
    if not os.path.isfile(args['importfile']):
      log.error("Import list {} doesn't exist!".format(args['importfile']))
      sys.exit(1)

    if not os.path.isdir(args['directory']):
      log.error("Client directory {0} doesn't exist!".format(args['directory']))
      sys.exit(1)

    importfile = os.path.sep.join([args['directory'], starcache.IMPORTFILE])
    importedfile = os.path.sep.join([args['directory'], starcache.IMPORTEDFILE])
    cachefile = os.path.sep.join([args['directory'], starcache.CACHEFILE])
    recentfile = os.path.sep.join([args['directory'], starcache.RECENTFILE])
    backup = cachefile + '.backup' if os.path.isfile(cachefile) else None
    if backup is not None and os.path.isfile(backup):
      log.error("Previous backup file {} exists!".format(backup))
      sys.exit(1)

    # Backup VisitedStarsCache.dat.
    if backup is not None:
      try:
        log.debug("Backing up {}...".format(cachefile))
        shutil.move(cachefile, backup)
      except IOError:
        log.error("Failed to back up {} as {}!".format(cachefile, backup))
        sys.exit(1)

    # Create ImportStars.txt.
    self.client_import(args['importfile'], importfile, importedfile, recentfile)

    # Delete old ImportStars.text.imported so it can be overridden.
    if os.path.isfile(importedfile):
      os.unlink(importedfile)

    # Extract VisitedStarsCache.dat.
    if os.path.isfile(cachefile):
      try:
        shutil.copyfile(cachefile, args['cachefile'])
      except IOError:
        log.error("Failed to copy {} to {}".format(cachefile, args['cachefile']))

    # Restore backed up VisitedStarsCache.dat.
    if backup is not None:
      try:
        log.debug("Restoring {}...".format(cachefile))
        shutil.move(backup, cachefile)
      except IOError:
        log.error("Failed to restore {} from {}!".format(cachefile, backup))
        sys.exit(1)

  def run_import(self, envdata, args):
    return self.game_import({
      'cachefile': args.cachefile,
      'directory': args.directory,
      'importfile': args.importfile
    })

  def run_read(self, envdata, args):
    id64list = []
    batch_size = 512
    for id64 in starcache.parse_visited_stars_cache(args.readfile):
      id64list.append(id64)
      if len(id64list) >= batch_size:
        self.batch_read(envdata, id64list)
        id64list = []
    if len(id64list):
      self.batch_read(envdata, id64list)

  def run_write(self, envdata, args):
    starcache.write_visited_stars_cache(args.writefile, envdata.find_all_systems(filter.entry_separator.join(args.filters) if len(args.filters) else None), self.args.recent)

if __name__ == '__main__':
  env.start()
  a = Application(env.local_args, False)
  a.run()
