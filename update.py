#!/usr/bin/env python

from __future__ import print_function, division
import argparse
import gc
import json
import logging
import os
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
if args.batch or args.batch_size:
  try:
    import ijson.backends.yajl2_cffi as ijson
  except ImportError:
    try:
      import ijson.backends.yajl2 as ijson
    except ImportError:
      try:
        import ijson
      except ImportError:
        log.error("Can't use ijson on this system!")
        sys.exit(1)

def import_json(url, description, fn, key, batch_size):
  if batch_size is None:
    batch_size = 131072
  if 'ijson' in sys.modules:
    log.info("Parsing {0} list from {1} ... ".format(description, url))
    batch = []
    for obj in ijson.items(util.open_url(url), key):
      batch.append(obj)
      if len(batch) >= batch_size:
        log.info("Loading {0} data of size {1} to DB...".format(description, len(batch)))
        fn(batch)
        log.info("Resuming parsing...")
        batch = []
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
  gc.collect()

def import_coriolis_data(entries):
  if 'fsd' in entries:
    # Not ijson parsed.
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

import_json(edsm_systems_url, 'EDSM Systems', dbc.populate_table_systems, 'item', args.batch_size)
import_json(eddb_systems_url, 'EDDB Systems', dbc.update_table_systems, 'item', args.batch_size)
import_json(eddb_stations_url, 'EDDB Stations', dbc.populate_table_stations, 'item', args.batch_size)
import_json(coriolis_fsds_url, 'Coriolis FSD', import_coriolis_data, 'fsd.item', args.batch_size)

dbc.close()

if os.path.isfile(db.default_db_file):
  os.unlink(db.default_db_file)
os.rename(db_tmp_filename, db.default_db_file)

log.info("All done.")
