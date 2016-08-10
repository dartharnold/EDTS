#!/usr/bin/env python

from __future__ import print_function, division
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
eddb_systems_url = "https://eddb.io/archive/v4/systems_populated.json"
eddb_stations_url = "https://eddb.io/archive/v4/stations.json"

coriolis_fsds_url = "https://raw.githubusercontent.com/cmmcleod/coriolis-data/master/modules/standard/frame_shift_drive.json"

ap = argparse.ArgumentParser(description = 'Update local database')
ap.add_argument('-b', '--batch', default=False, action='store_true', help='Import data in batches')
ap.add_argument('-s', '--batch-size', required=False, type=int, help='Batch size; higher sizes are faster but consume more memory')
args = ap.parse_args(sys.argv[1:])
batch_size = None
if args.batch or args.batch_size:
  batch_size = args.batch_size if args.batch_size is not None else 131072
  if not batch_size > 0:
    log.error("Batch size must be a natural number!")
    sys.exit(1)

def import_json(url, description, fn, batch_size):
  try:
    if batch_size is not None:
      log.info("Downloading {0} list from {1} ... ".format(description, url))
      sys.stdout.flush()

      batch = []
      encoded = ''
      bufsize = 256
      bytes_read = 0
      stream = util.open_url(url)
      while True:
        read = util.read_stream(stream, bufsize)
        if not read:
          break
        encoded += read
        if not bytes_read:
          # Handle leading [.
          encoded = re.sub(r'^\s*\[\s*', r'[\n', encoded, re.MULTILINE)
        bytes_read += len(read)
        if len(read) < bufsize:
          # Handle trailing ].
          encoded = re.sub(r'\s*\]\s*$', r'\n]', encoded, re.MULTILINE)
        encoded = re.sub(r'\s*\}\s*,\s*\{', '}\n{', encoded)
        lines = encoded.split('\n')
        if len(lines) == 1:
          continue
        last = len(lines) - 1
        encoded = ''
        for i in range(0, len(lines)):
          line = lines[i]
          m = re.match(r'\s*(\{.*\})(?:\s*,?\s*)?', line)
          if m is not None:
            try:
              obj = json.loads(m.group(1))
            except ValueError:
              encoded = '\n'.join(lines[i:])
              break
            batch.append(obj)
            if len(batch) >= batch_size:
              log.info("Loading {0} data of size {1} to DB...".format(description, len(batch)))
              fn(batch)
              log.info("Resuming parsing...")
              batch = []
          elif i == last:
            encoded = line
      if len(batch):
        log.info("Loading {0} data of size {1} to DB...".format(description, len(batch)))
        fn(batch)
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
      fn(obj)
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

def import_coriolis_data(entries):
  if 'fsd' in entries:
    entries = entries['fsd']
  fsddata = {}
  for entry in entries:
    fsddata['{0}{1}'.format(entry['class'], entry['rating'])] = entry
  dbc.populate_table_coriolis_fsds(fsddata)

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
  import_json(edsm_systems_url, 'EDSM Systems', dbc.populate_table_systems, batch_size)
  import_json(eddb_systems_url, 'EDDB Systems', dbc.update_table_systems, batch_size)
  import_json(eddb_stations_url, 'EDDB Stations', dbc.populate_table_stations, batch_size)
  import_json(coriolis_fsds_url, 'Coriolis FSD', import_coriolis_data, batch_size)
except MemoryError:
  log.error("Out of memory!")
  if batch_size is None:
    log.error("Try the --batch flag for a slower but more memory-efficient method!")
  elif batch_size > 1:
    log.error("Try --batch-size %d" % (batch_size / 2))
  dbc.close()
  sys.exit(1)

dbc.close()

if os.path.isfile(db.default_db_file):
  os.unlink(db.default_db_file)
os.rename(db_tmp_filename, db.default_db_file)

log.info("All done.")
