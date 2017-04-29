#!/usr/bin/env python

from __future__ import print_function, division
from time import time
import argparse
import collections
import csv
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
  def close(): pass

edsm_systems_url  = "https://www.edsm.net/dump/systemsWithCoordinates.json"
eddb_systems_url  = "https://eddb.io/archive/v5/systems.csv"
eddb_systems_populated_url  = "https://eddb.io/archive/v5/systems_populated.jsonl"
eddb_stations_url = "https://eddb.io/archive/v5/stations.jsonl"
eddb_bodies_url   = "https://eddb.io/archive/v5/bodies.jsonl"
coriolis_fsds_url = "https://raw.githubusercontent.com/edcd/coriolis-data/master/modules/standard/frame_shift_drive.json"

edsm_systems_local_path  = "data/systemsWithCoordinates.json"
eddb_systems_local_path  = "data/systems.csv"
eddb_systems_populated_local_path = "data/systems_populated.jsonl"
eddb_stations_local_path = "data/stations.jsonl"
eddb_bodies_local_path   = "data/bodies.jsonl"
coriolis_fsds_local_path = "data/frame_shift_drive.json"

_re_json_line = re.compile(r'^\s*(\{.*\})[\s,]*$')

default_steps = ['clean', 'systems', 'systems_populated', 'stations', 'fsds']
valid_steps = ['clean', 'systems', 'systems_populated', 'stations', 'fsds', 'id64', 'bodies']


def cleanup_local(f, scratch):
  if f is not None and not f.closed:
    try:
      f.close()
    except:
      log.error("Error closing temporary file{}", ' {}'.format(scratch) if scratch is not None else '')
  if scratch is not None:
    try:
      unlink(scratch)
    except:
      log.error("Error cleaning up temporary file {}", scratch)


class StreamingStringIO(object):
  def __init__(self): self.data = collections.deque()
  def add(self, data): self.data.appendleft(data)
  def __iter__(self): return self
  def next(self):
    if any(self.data):
      return self.data.pop()
    else:
      raise StopIteration
  __next__ = next

def read_header_csv(line):
  sio = StreamingStringIO()
  sio.add(line)
  csvr = csv.DictReader(sio)
  return (sio, csvr)

def read_line_csv(line, header):
  if len(line) == 0:
    return False
  header[0].add(line)
  return next(header[1])

def read_all_csv(data):
  return [row for row in csv.DictReader(data)]

def read_line_json(line, header):
  m = _re_json_line.match(line)
  if m is None:
    return False
  try:
    return json.loads(m.group(1))
  except ValueError:
    log.debug("Line failed JSON parse: {0}", line)
    return None

def read_all_json(data):
  return json.loads(data)

def import_csv_from_url(url, filename, description, batch_size, is_url_local = False, key = None):
  return import_data_from_url(read_header_csv, read_line_csv, read_all_csv, url, filename, description, batch_size, is_url_local, key)

def import_json_from_url(url, filename, description, batch_size, is_url_local = False, key = None):
  return import_data_from_url(None, read_line_json, read_all_json, url, filename, description, batch_size, is_url_local, key)

def import_data_from_url(fn_read_header, fn_read_line, fn_read_all, url, filename, description, batch_size, is_url_local, key):
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
      
      header = None

      batch = []
      encoded = ''
      stream = util.open_url(url, allow_no_ssl=is_url_local)
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
        # Check if this is the first line and we should read a header
        if fn_read_header is not None and header is None:
          header = fn_read_header(line)
          if header is None:
            raise Exception("Failed to read header")
          continue
        # OK, read a normal line
        obj = fn_read_line(line, header)
        if obj in [None, False]:
          if obj is None:
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
      encoded = util.read_from_url(url, allow_no_ssl=is_url_local)
      log.info("Done.")
      if copy_local:
        log.info("Writing {0} local data...", description)
        util.write_stream(f, encoded)
        log.info("Done.")
      if not download_only:
        log.info("Loading {0} data...", description)
        sys.stdout.flush()
        obj = fn_read_all(encoded)
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

    
if __name__ == '__main__':
  env.log_versions()
  db.log_versions()

  ap = argparse.ArgumentParser(description = 'Update local database', parents = [env.arg_parser], prog = "update")
  ap.add_argument_group("Processing options")
  bex = ap.add_mutually_exclusive_group()
  bex.add_argument('-b', '--batch', dest='batch', action='store_true', default=True, help='Import data in batches')
  bex.add_argument('-n', '--no-batch', dest='batch', action='store_false', help='Import data in one load - this will use massive amounts of RAM and may fail!')
  ap.add_argument('-c', '--copy-local', required=False, action='store_true', help='Keep local copy of downloaded files')
  ap.add_argument('-d', '--download-only', required=False, action='store_true', help='Do not import, just download files - implies --copy-local')
  ap.add_argument('-s', '--batch-size', required=False, type=int, help='Batch size; higher sizes are faster but consume more memory')
  ap.add_argument('-l', '--local', required=False, action='store_true', help='Instead of downloading, update from local files in the data directory')
  ap.add_argument(      '--step', required=False, type=str, help='Manually perform/re-perform a single step of the update process.')
  ap.add_argument(      '--systems-source', required=False, type=str.lower, default='edsm', choices=['edsm','eddb'], help='The source to get main system data from.')
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

  if args.print_urls:
    if args.local:
      if args.systems_source == 'edsm':
        print(edsm_systems_local_path)
      elif args.systems_source == 'eddb':
        print(eddb_systems_local_path)
      print(eddb_systems_populated_local_path)
      print(eddb_stations_local_path)
      print(coriolis_fsds_local_path)
    else:
      if args.systems_source == 'edsm':
        print(edsm_systems_url)
      elif args.systems_source == 'eddb':
        print(eddb_systems_url)
      print(eddb_systems_populated_url)
      print(eddb_stations_url)
      print(coriolis_fsds_url)
    sys.exit(0)

  steps = [args.step] if args.step else default_steps

  if download_only:
    log.info("Downloading files locally...")
    dbc = DownloadOnly()
  else:
    db_file = os.path.join(defs.default_path, env.global_args.db_file)
    db_dir = os.path.dirname(db_file)

    # If the data directory doesn't exist, make it
    if db_dir and not os.path.exists(db_dir):
      os.makedirs(db_dir)

    if 'clean' in steps:
      # Open then close a temporary file, essentially reserving the name.
      fd, db_tmp_filename = tempfile.mkstemp('.tmp', os.path.basename(db_file), db_dir if db_dir else '.')
      os.close(fd)

      log.info("Initialising database...")
      sys.stdout.flush()
      dbc = db.initialise_db(db_tmp_filename)
      db_open_filename = db_tmp_filename
      log.info("Done.")
    else:
      log.info("Opening existing database...")
      dbc = db.open_db(db_file)
      db_open_filename = db_file
      if dbc:
        log.info("Done.")
      else:
        log.error("Failed to open existing DB!")
        sys.exit(2)

  try:
    edsm_systems_path  = util.path_to_url(edsm_systems_local_path)  if args.local else edsm_systems_url
    eddb_systems_path  = util.path_to_url(eddb_systems_local_path)  if args.local else eddb_systems_url
    eddb_systems_populated_path  = util.path_to_url(eddb_systems_populated_local_path)  if args.local else eddb_systems_populated_url
    eddb_stations_path = util.path_to_url(eddb_stations_local_path) if args.local else eddb_stations_url
    eddb_bodies_path   = util.path_to_url(eddb_bodies_local_path)   if args.local else eddb_bodies_url
    coriolis_fsds_path = util.path_to_url(coriolis_fsds_local_path) if args.local else coriolis_fsds_url

    if 'systems' in steps:
      if args.systems_source == 'edsm':
        dbc.populate_table_systems(import_json_from_url(edsm_systems_path, edsm_systems_local_path, 'EDSM systems', batch_size, is_url_local=args.local), args.systems_source)
      elif args.systems_source == 'eddb':
        dbc.populate_table_systems(import_csv_from_url(eddb_systems_path, eddb_systems_local_path, 'EDDB systems', batch_size, is_url_local=args.local), args.systems_source)
      else:
        raise Exception("Invalid systems source option provided!")
    if 'systems_populated' in steps:
      dbc.update_table_systems(import_json_from_url(eddb_systems_populated_path, eddb_systems_populated_local_path, 'EDDB populated systems', batch_size, is_url_local=args.local), args.systems_source)
    if 'stations' in steps:
      dbc.populate_table_stations(import_json_from_url(eddb_stations_path, eddb_stations_local_path, 'EDDB stations', batch_size, is_url_local=args.local))
    if 'fsds' in steps:
      dbc.populate_table_coriolis_fsds(import_json_from_url(coriolis_fsds_path, coriolis_fsds_local_path, 'Coriolis FSDs', batch_size=None, is_url_local=args.local, key='fsd'))
    if 'id64' in steps:
      dbc.update_table_systems_with_id64()
    if 'bodies' in steps:
      dbc.populate_table_bodies(import_json_from_url(eddb_bodies_path, eddb_bodies_local_path, 'EDDB bodies', batch_size, is_url_local=args.local))
  except MemoryError:
    log.error("Out of memory!")
    if batch_size is None:
      log.error("Try the --batch flag for a slower but more memory-efficient method!")
    elif batch_size > 64:
      log.error("Try --batch-size {0}", batch_size / 2)
    if not download_only:
      cleanup_local(None, db_open_filename)
    sys.exit(1)
  except:
    if not download_only:
      cleanup_local(None, db_open_filename)
    raise

  if not download_only:
    dbc.close()

    if 'clean' in steps:
      if os.path.isfile(db_file):
        os.unlink(db_file)
      shutil.move(db_tmp_filename, db_file)

  log.info("All done.")
