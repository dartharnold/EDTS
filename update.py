#!/usr/bin/env python

from __future__ import print_function, division
from time import time
import argparse
import defs
import gc
import json
import os
import shutil
import platform
import re
import sys
import db_sqlite3 as db
import util
import tempfile
import env

log = util.get_logger("update")

class DownloadOnly(object):
  def ignore(self, many):
    for one in many:
      continue

  populate_table_systems = ignore
  populate_table_stations = ignore
  populate_table_coriolis_fsds = ignore
  update_table_systems = ignore

edsm_systems_url  = "https://www.edsm.net/dump/systemsWithCoordinates.json"
eddb_systems_url  = "https://eddb.io/archive/v5/systems_populated.jsonl"
eddb_stations_url = "https://eddb.io/archive/v5/stations.jsonl"
coriolis_fsds_url = "https://raw.githubusercontent.com/cmmcleod/coriolis-data/master/modules/standard/frame_shift_drive.json"

edsm_systems_local_path  = "data/systemsWithCoordinates.json"
eddb_systems_local_path  = "data/systems_populated.jsonl"
eddb_stations_local_path = "data/stations.jsonl"
coriolis_fsds_local_path = "data/frame_shift_drive.json"

_re_json_line = re.compile(r'^\s*(\{.*\})[\s,]*$')

ap = argparse.ArgumentParser(description = 'Update local database', parents = [env.arg_parser], prog = "update")
ap.add_argument_group("Processing options")
bex = ap.add_mutually_exclusive_group()
bex.add_argument('-b', '--batch', dest='batch', action='store_true', default=True, help='Import data in batches')
bex.add_argument('-n', '--no-batch', dest='batch', action='store_false', help='Import data in one load - this will use massive amounts of RAM and may fail!')
ap.add_argument('-c', '--copy-local', required=False, action='store_true', help='Keep local copy of downloaded files')
ap.add_argument('-d', '--download-only', required=False, action='store_true', help='Do not import, just download files - implies --copy-local')
ap.add_argument('-s', '--batch-size', required=False, type=int, help='Batch size; higher sizes are faster but consume more memory')
ap.add_argument('-l', '--local', required=False, action='store_true', help='Instead of downloading, update from local files in the data directory')
ap.add_argument('--print-urls', required=False, action='store_true', help='Do not download anything, just print the URLs which we would fetch from')
args = ap.parse_args(sys.argv[1:])
batch_size = None
if args.batch or args.batch_size:
  batch_size = args.batch_size if args.batch_size is not None else 1024
  if not batch_size > 0:
    log.error("Batch size must be a natural number!")
    sys.exit(1)
download_only = args.download_only
copy_local = download_only or args.copy_local
if copy_local and args.local:
  log.error("Invalid use of --local and --{}!", "download-only" if download_only else "copy-local")
  sys.exit(1)

def cleanup_local(f, scratch):
  try:
    if f is not None:
      f.close()
    if scratch is not None:
      unlink(scratch)
  except:
    log.error("Error cleanup up temporary file {}", scratch)

def import_json_from_url(url, filename, description, batch_size, key = None):
  if copy_local:
    try:
      dirname = os.path.dirname(filename)
      fd, scratch = tempfile.mkstemp('.tmp', os.path.basename(filename), dirname if dirname else '.')
      f = os.fdopen(fd, 'wb')
    except:
      log.error("Failed to create a temporary file")
      raise
  try:
    if batch_size is not None:
      log.info("Batch downloading {0} list from {1} ... ", description, url)
      sys.stdout.flush()

      start = int(time())
      done = 0
      failed = 0
      last_elapsed = 0

      batch = []
      encoded = ''
      stream = util.open_url(url)
      if stream is None:
        if copy_local:
          cleanup_local(f, scratch)
        return
      while True:
        line = util.read_stream_line(stream)
        if not line:
          break
        if copy_local:
          util.write_stream(f, line)
        if download_only:
          continue
        m = _re_json_line.match(line)
        if m is None:
          continue
        try:
          obj = json.loads(m.group(1))
        except ValueError:
          log.debug("Line failed JSON parse: {0}", line)
          failed += 1
          continue
        batch.append(obj)
        if len(batch) >= batch_size:
          for obj in batch:
            yield obj
          done += len(batch)
          elapsed = int(time()) - start
          if elapsed - last_elapsed >= 30:
            log.info("Loaded {0} row(s) of {1} data to DB...", done, description)
            last_elapsed = elapsed
          batch = []
        if len(batch) >= batch_size:
          for obj in batch:
            yield obj
          done += len(batch)
          log.info("Loaded {0} row(s) of {1} data to DB...", done, description)
      done += len(batch)
      if not download_only:
        for obj in batch:
          yield obj
        if failed:
          log.info("Lines failing JSON parse: {0}", failed)
        log.info("Loaded {0} row(s) of {1} data to DB...", done, description)
        log.info("Done.")
    else:
      log.info("Downloading {0} list from {1} ... ", description, url)
      sys.stdout.flush()
      encoded = util.read_from_url(url)
      log.info("Done.")
      if copy_local:
        log.info("Writing {0} local data...", description)
        util.write_stream(f, encoded)
        log.info("Done.")
      if not download_only:
        log.info("Loading {0} data...", description)
        sys.stdout.flush()
        obj = json.loads(encoded)
        log.info("Done.")
        log.info("Adding {0} data to DB...", description)
        if key is not None:
          obj = obj[key]
        for o in obj:
          yield o
        log.info("Done.")
    # Force GC collection to try to avoid memory errors
    encoded = None
    obj = None
    batch = None
    gc.collect()
    if copy_local:
      f.close()
      f = None
      shutil.move(scratch, filename)
  except MemoryError:
    encoded = None
    obj = None
    batch = None
    gc.collect()
    raise
  except:
    if copy_local:
      cleanup_local(f, scratch)
    raise

def import_jsonl(url, filename, description, batch_size, key = None):
  return import_json_from_url(url, filename, description, batch_size, key)

def import_json(url, filename, description, batch_size, key = None):
  return import_json_from_url(url, filename, description, batch_size, key)

if __name__ == '__main__':
  env.log_versions()
  db.log_versions()

  if args.print_urls:
    if args.local:
      print(edsm_systems_local_path)
      print(eddb_systems_local_path)
      print(eddb_stations_local_path)
      print(coriolis_fsds_local_path)
    else:
      print(edsm_systems_url)
      print(eddb_systems_url)
      print(eddb_stations_url)
      print(coriolis_fsds_url)
    sys.exit(0)

  if download_only:
    log.info("Downloading files locally...")
    dbc = DownloadOnly()
  else:
    db_file = os.path.join(defs.default_path, env.global_args.db_file)
    db_dir = os.path.dirname(db_file)

    # If the data directory doesn't exist, make it
    if db_dir and not os.path.exists(db_dir):
      os.makedirs(db_dir)

    fd, db_tmp_filename = tempfile.mkstemp('.tmp', os.path.basename(db_file), db_dir if db_dir else '.')

    log.info("Initialising database...")
    sys.stdout.flush()
    if os.path.isfile(db_tmp_filename):
      os.unlink(db_tmp_filename)
    dbc = db.initialise_db(db_tmp_filename)
    log.info("Done.")

  try:
    edsm_systems_path  = util.path_to_url(edsm_systems_local_path)  if args.local else edsm_systems_url
    eddb_systems_path  = util.path_to_url(eddb_systems_local_path)  if args.local else eddb_systems_url
    eddb_stations_path = util.path_to_url(eddb_stations_local_path) if args.local else eddb_stations_url
    coriolis_fsds_path = util.path_to_url(coriolis_fsds_local_path) if args.local else coriolis_fsds_url

    dbc.populate_table_systems(import_json(edsm_systems_path, edsm_systems_local_path, 'EDSM systems', batch_size))
    dbc.update_table_systems(import_jsonl(eddb_systems_path, eddb_systems_local_path, 'EDDB systems', batch_size))
    dbc.populate_table_stations(import_jsonl(eddb_stations_path, eddb_stations_local_path, 'EDDB stations', batch_size))
    dbc.populate_table_coriolis_fsds(import_json(coriolis_fsds_url, coriolis_fsds_local_path, 'Coriolis FSDs', None, 'fsd'))
  except MemoryError:
    log.error("Out of memory!")
    if batch_size is None:
      log.error("Try the --batch flag for a slower but more memory-efficient method!")
    elif batch_size > 64:
      log.error("Try --batch-size {0}", batch_size / 2)
    if not download_only:
      cleanup_local(None, db_tmp_filename)
    sys.exit(1)
  except:
    if not download_only:
      cleanup_local(None, db_tmp_filename)
    raise

  if not download_only:
    dbc.close()

    if os.path.isfile(db_file):
      os.unlink(db_file)
    shutil.move(db_tmp_filename, db_file)

  log.info("All done.")
