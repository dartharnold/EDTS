#!/usr/bin/env python

from __future__ import print_function
import io
import json
import logging
import sys

import eddb
import coriolis

log = logging.getLogger("update")

if __name__ == '__main__':
  logging.basicConfig(level = logging.INFO, format="[%(asctime)-15s] [%(name)-6s] %(message)s")
  
  eddb.download_eddb_files(eddb.default_systems_file, eddb.default_stations_file)
  
  syresult = eddb.check_systems(eddb.default_systems_file)
  if syresult != False:
    log.info("Systems file exists and loads OK ({0} systems)".format(syresult))
  else:
    log.error("!! Systems file does not exist or could not be loaded")
  stresult = eddb.check_stations(eddb.default_stations_file)
  if stresult != False:
    log.info("Stations file exists and loads OK ({0} stations)".format(stresult))
  else:
    log.error("!! Stations file does not exist or could not be loaded")
    
  coriolis.download_coriolis_files(coriolis.default_frame_shift_drive_file)
  
  syresult = coriolis.check_frame_shift_drives(coriolis.default_frame_shift_drive_file)
  if syresult != False:
    log.info("FSD file exists and loads OK ({0} drives)".format(syresult))
  else:
    log.error("!! FSD file does not exist or could not be loaded")
