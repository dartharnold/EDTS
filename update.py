#!/usr/bin/env python

from __future__ import print_function, division
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

def import_json(url, description, fn):
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

def import_coriolis_data(coriolis_fsds_obj):
  fsddata = {}
  for entry in coriolis_fsds_obj['fsd']:
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

import_json(edsm_systems_url, 'EDSM Systems', dbc.populate_table_systems)
import_json(eddb_systems_url, 'EDDB Systems', dbc.update_table_systems)
import_json(eddb_stations_url, 'EDDB Stations', dbc.populate_table_stations)
import_json(coriolis_fsds_url, 'Coriolis FSD', import_coriolis_data)

dbc.close()

if os.path.isfile(db.default_db_file):
  os.unlink(db.default_db_file)
os.rename(db_tmp_filename, db.default_db_file)

log.info("All done.")
