from __future__ import print_function, division
import json
import logging
import os
import sys
import db
import util

log = logging.getLogger("update")
logging.basicConfig(level = logging.INFO, format="[%(asctime)-15s] [%(name)-6s] %(message)s")

eddb_systems_url = "http://eddb.io/archive/v4/systems.json"
eddb_stations_url = "http://eddb.io/archive/v4/stations.json"

coriolis_fsds_url = "https://raw.githubusercontent.com/cmmcleod/coriolis-data/master/modules/standard/frame_shift_drive.json"

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

# Download the systems.json
log.info("Downloading EDDB Systems list from {0} ... ".format(eddb_systems_url))
sys.stdout.flush()
eddb_systems_json = util.read_from_url(eddb_systems_url)
log.info("Done.")
log.info("Loading EDDB Systems data...")
sys.stdout.flush()
eddb_systems_obj = json.loads(eddb_systems_json)
log.info("Done.")
log.info("Adding EDDB Systems data to DB...")
sys.stdout.flush()
dbc.populate_table_eddb_systems(eddb_systems_obj)
log.info("Done.")

log.info("Downloading EDDB Stations list from {0} ... ".format(eddb_stations_url))
sys.stdout.flush()
eddb_stations_json = util.read_from_url(eddb_stations_url)
log.info("Done.")
log.info("Loading EDDB Stations data...")
sys.stdout.flush()
eddb_stations_obj = json.loads(eddb_stations_json)
log.info("Done.")
log.info("Adding EDDB Stations data to DB...")
sys.stdout.flush()
dbc.populate_table_eddb_stations(eddb_stations_obj)
log.info("Done.")

log.info("Downloading Coriolis FSD list from {0} ... ".format(coriolis_fsds_url))
sys.stdout.flush()
coriolis_fsds_json = util.read_from_url(coriolis_fsds_url)
log.info("Done.")
log.info("Loading Coriolis FSD data...")
sys.stdout.flush()
coriolis_fsds_obj = json.loads(coriolis_fsds_json)
log.info("Done.")
log.info("Adding Coriolis FSD data to DB...")
sys.stdout.flush()
fsddata = {}
for entry in coriolis_fsds_obj['fsd']:
  fsddata['{0}{1}'.format(entry['class'], entry['rating'])] = entry
dbc.populate_table_coriolis_fsds(fsddata)
log.info("Done.")

dbc.close()

if os.path.isfile(db.default_db_file):
  os.unlink(db.default_db_file)
os.rename(db_tmp_filename, db.default_db_file)

log.info("All done.")
