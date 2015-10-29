#!/usr/bin/env python

from __future__ import print_function
import io
import json
import logging
import os
import sys
import urllib

default_frame_shift_drive_file = "coriolis/frame_shift_drive.json"

coriolis_frame_shift_drive_url = "https://raw.githubusercontent.com/cmmcleod/coriolis-data/master/components/standard/frame_shift_drive.json"

coriolis_frame_shift_drive_file_size_limit = 1 * 1048576

log = logging.getLogger("coriolis")

def download_coriolis_files(frame_shift_drive_file):
  # If the frame_shift_drive.json's directory doesn't exist, make it
  if not os.path.exists(os.path.dirname(frame_shift_drive_file)):
    os.makedirs(os.path.dirname(frame_shift_drive_file))

  # Download the frame_shift_drive.json
  log.info("Downloading Coriolis FSD list from {0} ... ".format(coriolis_frame_shift_drive_url))
  sys.stdout.flush()
  urllib.urlretrieve(coriolis_frame_shift_drive_url, frame_shift_drive_file)
  log.info("Done.")


def check_frame_shift_drives(filename):
  if os.path.isfile(filename):
    try:
      s = load_frame_shift_drives(filename)
      return len(s)
    except:
      return False
  else:
    return False

def load_frame_shift_drives(filename):
  return load_json(filename, coriolis_frame_shift_drive_file_size_limit)

def load_json(filename, size_limit):
  f = io.open(filename, "r")
  return json.loads(f.read(size_limit))


if __name__ == '__main__':
  logging.basicConfig(level = logging.INFO, format="[%(asctime)-15s] [%(name)-6s] %(message)s")
  
  if len(sys.argv) > 1 and sys.argv[1] == "--download":
    download_coriolis_files(default_frame_shift_drive_file)
  
  syresult = check_frame_shift_drives(default_frame_shift_drive_file)
  if syresult != False:
    log.info("FSD file exists and loads OK ({0} drives)".format(syresult))
  else:
    log.error("!! FSD file does not exist or could not be loaded")
  
