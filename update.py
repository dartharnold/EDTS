#!/usr/bin/env python

from __future__ import print_function, division
from time import time
import argparse
import gc
import json
import logging
import os
import re
import sys
import db
import util

log = logging.getLogger("update")
logging.basicConfig(level = logging.INFO, format="[%(asctime)-15s] [%(name)-6s] %(message)s")

edsm_systems_url = "https://www.edsm.net/dump/systemsWithCoordinates.json"
eddb_systems_url = "https://eddb.io/archive/v4/systems_populated.json{}"
eddb_stations_url = "https://eddb.io/archive/v4/stations.json{}"

coriolis_fsds_url = "https://raw.githubusercontent.com/cmmcleod/coriolis-data/master/modules/standard/frame_shift_drive.json"

_re_json_line = re.compile(r'\s*(\{.*\})[\s,]*')

ap = argparse.ArgumentParser(description = 'Update local database')
ap.add_argument_group("Processing options")
bex = ap.add_mutually_exclusive_group()
bex.add_argument('-b', '--batch', dest='batch', action='store_true', default=True, help='Import data in batches')
bex.add_argument('-n', '--no-batch', dest='batch', action='store_false', help='Import data in one load - this will use massive amounts of RAM and may fail!')
ap.add_argument('-s', '--batch-size', required=False, type=int, help='Batch size; higher sizes are faster but consume more memory')
args = ap.parse_args(sys.argv[1:])
batch_size = None
if args.batch or args.batch_size:
  batch_size = args.batch_size if args.batch_size is not None else 1024
  if not batch_size > 0:
    log.error("Batch size must be a natural number!")
    sys.exit(1)

def import_json_from_url(urlfmt, jsonl, description, batch_size, key = None):
  url = urlfmt.format('l' if jsonl and batch_size else '')
  try:
    if batch_size is not None:
      log.info("Batch downloading {0} list from {1} ... ".format(description, url))
      sys.stdout.flush()

      start = int(time())
      done = 0
      failed = 0
      last_elapsed = 0

      batch = []
      encoded = ''
      stream = util.open_url(url)
      if stream is None:
        return
      while True:
        line = util.read_stream_line(stream)
        if not line:
          break
        m = _re_json_line.match(line)
        if m is None:
          continue
        try:
          obj = json.loads(m.group(1))
        except ValueError:
          log.debug("Line failed JSON parse: {0}".format(line))
          failed += 1
          continue
        batch.append(obj)
        if len(batch) >= batch_size:
          for obj in batch:
            yield obj
          done += len(batch)
          elapsed = int(time()) - start
          if elapsed - last_elapsed >= 30:
            log.info("Loaded {0} row(s) of {1} data to DB...".format(done, description))
            last_elapsed = elapsed
          batch = []
        if len(batch) >= batch_size:
          for obj in batch:
            yield obj
          done += len(batch)
          log.info("Loaded {0} row(s) of {1} data to DB...".format(done, description))
      done += len(batch)
      for obj in batch:
        yield obj
      if failed:
        log.info("Lines failing JSON parse: {0}".format(failed))
      log.info("Loaded {0} row(s) of {1} data to DB...".format(done, description))
      log.info("Done.")
    else:
      log.info("Downloading {0} list from {1} ... ".format(description, url))
      sys.stdout.flush()
      encoded = util.read_from_url(url)
      log.info("Done.")
      log.info("Loading {0} data...".format(description))
      sys.stdout.flush()
      obj = json.loads(encoded)
      log.info("Done.")
      log.info("Adding {0} data to DB...".format(description))
      sys.stdout.flush()
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
  except MemoryError:
    encoded = None
    obj = None
    batch = None
    gc.collect()
    raise

def import_jsonl(urlfmt, description, batch_size, key = None):
  return import_json_from_url(urlfmt, True, description, batch_size, key)

def import_json(urlfmt, description, batch_size, key = None):
  return import_json_from_url(urlfmt, False, description, batch_size, key)

# If the data directory doesn't exist, make it
if not os.path.exists(os.path.dirname(db.default_db_file)):
  os.makedirs(os.path.dirname(db.default_db_file))

db_tmp_filename = "{0}.tmp".format(db.default_db_file)

log.info("Initialising database...")
sys.stdout.flush()
if os.path.isfile(db_tmp_filename):
  os.unlink(db_tmp_filename)
dbc = db.initialise_db(db_tmp_filename)
log.info("Done.")

try:
  dbc.populate_table_systems(import_json(edsm_systems_url, 'EDSM systems', batch_size))
  dbc.update_table_systems(import_jsonl(eddb_systems_url, 'EDDB systems', batch_size))
  dbc.populate_table_stations(import_jsonl(eddb_stations_url, 'EDDB stations', batch_size))
  dbc.populate_table_coriolis_fsds(import_json(coriolis_fsds_url, 'Coriolis FSDs', None, 'fsd'))
except MemoryError:
  log.error("Out of memory!")
  if batch_size is None:
    log.error("Try the --batch flag for a slower but more memory-efficient method!")
  elif batch_size > 64:
    log.error("Try --batch-size %d" % (batch_size / 2))
  dbc.close()
  sys.exit(1)

dbc.close()

if os.path.isfile(db.default_db_file):
  os.unlink(db.default_db_file)
os.rename(db_tmp_filename, db.default_db_file)

log.info("All done.")
