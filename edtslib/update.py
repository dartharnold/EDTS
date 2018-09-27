#!/usr/bin/env python

from __future__ import print_function, division
from time import time
import argparse
import collections
import csv
import gc
import json
import os
import shutil
import re
import sys
import tempfile

from . import db_sqlite3 as db
from . import defs
from . import env
from . import util

log = util.get_logger("update")


class DownloadOnly(object):
  def ignore(self, many, drop_indices = False):
    for _ in many:
      continue
  populate_table_systems = ignore
  populate_table_stations = ignore
  populate_table_coriolis_fsds = ignore
  def close(self): pass

edsm_systems_url  = "https://www.edsm.net/dump/systemsWithCoordinates.json"
edsm_syspop_url   = "https://www.edsm.net/dump/systemsPopulated.json"
edsm_stations_url = "https://www.edsm.net/dump/stations.json"
coriolis_fsds_url = "https://raw.githubusercontent.com/cmmcleod/coriolis-data/master/modules/standard/frame_shift_drive.json"

local_path = 'data'
edsm_systems_local_path  = os.path.join(local_path, "systemsWithCoordinates.json")
edsm_syspop_local_path   = os.path.join(local_path, "systemsPopulated.json")
edsm_stations_local_path = os.path.join(local_path, "stations.json")
coriolis_fsds_local_path = os.path.join(local_path, "frame_shift_drive.json")

_re_json_line = re.compile(r'^\s*(\{.*\})[\s,]*$')

default_steps = ['clean', 'systems', 'stations', 'fsds']
extra_steps   = ['systems_populated', 'id64']
valid_steps   = default_steps + extra_steps
all_steps     = valid_steps + ['default', 'extra', 'all']

def steps_type(s):
  step_names = s.lower().split(',') if s else []
  steps = []
  for step in step_names:
    if step not in all_steps:
      raise ValueError('Invalid step "{}".  Valid steps are: {}', step, ','.join(all_steps))
    if step == 'default':
      steps += default_steps
    elif step == 'extra':
      steps += extra_steps
    elif step == 'default':
      steps += default_steps
    elif step == 'all':
      return valid_steps
    else:
      steps.append(step)
  return steps


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


def cleanup_local(f, scratch):
  if f is not None and not f.closed:
    try:
      f.close()
    except:
      log.error("Error closing temporary file{}", ' {}'.format(scratch) if scratch is not None else '')
  if scratch is not None:
    try:
      os.unlink(scratch)
    except:
      log.error("Error cleaning up temporary file {}", scratch)


class Application(object):

  def __init__(self, arg, hosted, state = {}):
    ap = argparse.ArgumentParser(description = 'Update local database', parents = [env.arg_parser], prog = "update", epilog='Valid choices for --steps: {}'.format(','.join(all_steps)))
    ap.add_argument_group("Processing options")
    bex = ap.add_mutually_exclusive_group()
    bex.add_argument('-b', '--batch', dest='batch', action='store_true', default=True, help='Import data in batches')
    bex.add_argument('-n', '--no-batch', dest='batch', action='store_false', help='Import data in one load - this will use massive amounts of RAM and may fail!')
    ap.add_argument('-c', '--copy-local', required=False, action='store_true', help='Keep local copy of downloaded files')
    ap.add_argument('-d', '--download-only', required=False, action='store_true', help='Do not import, just download files - implies --copy-local')
    ap.add_argument('-s', '--batch-size', required=False, type=int, help='Batch size; higher sizes are faster but consume more memory')
    ap.add_argument('-l', '--local', required=False, action='store_true', help='Instead of downloading, update from local files in the data directory')
    ap.add_argument(      '--steps', required=False, type=steps_type, default=default_steps, help='Manually (re-)perform comma-separated steps of the update process.')
    ap.add_argument(      '--print-urls', required=False, action='store_true', help='Do not download anything, just print the URLs which we would fetch from')
    args = ap.parse_args(sys.argv[1:])
    if args.batch or args.batch_size:
      args.batch_size = args.batch_size if args.batch_size is not None else 1024
      if not args.batch_size > 0:
        raise ValueError("Batch size must be a natural number!")
    args.copy_local = args.download_only or args.copy_local
    if args.copy_local and args.local:
      raise ValueError("Invalid use of --local and --{}!", "download-only" if args.download_only else "copy-local")
    self.args = args

  def run(self):
    env.log_versions()
    db.log_versions()

    # Get the relative path to the "edtslib" base directory from the current directory
    relpath = util.get_relative_path(os.getcwd(), os.path.dirname(__file__))

    if self.args.print_urls:
      if self.args.local:
        for path in [edsm_systems_local_path, edsm_stations_local_path, coriolis_fsds_local_path]:
          print(path)
      else:
        for path in [edsm_systems_url, edsm_stations_url, coriolis_fsds_url]:
          print(path)
      return

    g = util.start_timer()

    if self.args.download_only:
      log.info("Downloading files locally...")
      dbc = DownloadOnly()
    else:
      db_file = os.path.join(defs.default_path, env.global_args.db_file)
      db_dir = os.path.dirname(db_file)

      # If the data directory doesn't exist, make it
      if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

      if 'clean' in self.args.steps:
        # Open then close a temporary file, essentially reserving the name.
        fd, db_tmp_filename = tempfile.mkstemp('.tmp', os.path.basename(db_file), db_dir if db_dir else '.')
        os.close(fd)

        log.info("Initialising database...")
        sys.stdout.flush()
        t = util.start_timer()
        dbc = db.initialise_db(db_tmp_filename)
        db_open_filename = db_tmp_filename
        log.info("Done in {}.", util.format_timer(t))
      else:
        log.info("Opening existing database...")
        sys.stdout.flush()
        t = util.start_timer()
        dbc = db.open_db(db_file)
        db_open_filename = db_file
        if dbc:
          log.info("Done in {}.", util.format_timer(t))
        else:
          log.error("Failed to open existing DB!")
          sys.exit(2)

    try:
      # Repoint local paths to use the right relative path
      cur_edsm_systems_local_path  = os.path.join(relpath, edsm_systems_local_path)
      cur_edsm_syspop_local_path   = os.path.join(relpath, edsm_syspop_local_path)
      cur_edsm_stations_local_path = os.path.join(relpath, edsm_stations_local_path)
      cur_coriolis_fsds_local_path = os.path.join(relpath, coriolis_fsds_local_path)
      # Decide whether to source data from local paths or remote URLs
      edsm_systems_path  = util.path_to_url(cur_edsm_systems_local_path)  if self.args.local else edsm_systems_url
      edsm_syspop_path   = util.path_to_url(cur_edsm_syspop_local_path)   if self.args.local else edsm_syspop_url
      edsm_stations_path = util.path_to_url(cur_edsm_stations_local_path) if self.args.local else edsm_stations_url
      coriolis_fsds_path = util.path_to_url(cur_coriolis_fsds_local_path) if self.args.local else coriolis_fsds_url

      if self.args.copy_local:
        download_dir = os.path.sep.join([relpath, local_path])
        if not os.path.exists(download_dir):
          os.makedirs(download_dir)

      if 'systems' in self.args.steps:
        dbc.populate_table_systems(self.import_json_from_url(edsm_systems_path, cur_edsm_systems_local_path, 'EDSM systems', self.args.batch_size, is_url_local=self.args.local), True)
        log.info("Done.")
      if 'systems_populated' in self.args.steps:
        dbc.populate_table_systems(self.import_json_from_url(edsm_syspop_path, cur_edsm_syspop_local_path, 'EDSM populated systems', self.args.batch_size, is_url_local=self.args.local))
        log.info("Done.")
      if 'stations' in self.args.steps:
        dbc.populate_table_stations(self.import_json_from_url(edsm_stations_path, cur_edsm_stations_local_path, 'EDSM stations', self.args.batch_size, is_url_local=self.args.local))
        log.info("Done.")
      if 'fsds' in self.args.steps:
        dbc.populate_table_coriolis_fsds(self.import_json_from_url(coriolis_fsds_path, cur_coriolis_fsds_local_path, 'Coriolis FSDs', None, is_url_local=self.args.local, key='fsd'))
        log.info("Done.")
      if 'id64' in self.args.steps:
        log.info("Setting known system ID64s...")
        sys.stdout.flush()
        t = util.start_timer()
        dbc.update_table_systems_with_id64()
        log.info("Done in {}.".format(util.format_timer(t)))
    except MemoryError:
      log.error("Out of memory!")
      if self.args.batch_size is None:
        log.error("Try the --batch flag for a slower but more memory-efficient method!")
      elif self.args.batch_size > 64:
        log.error("Try --batch-size {0}", self.args.batch_size / 2)
      if not self.args.download_only:
        if 'clean' in self.args.steps:
          cleanup_local(None, db_open_filename)
        else:
          log.warning("Update operation on existing database cancelled - database state could be invalid")
      return
    except:
      if not self.args.download_only:
        if 'clean' in self.args.steps:
          cleanup_local(None, db_open_filename)
        else:
          log.warning("Update operation on existing database cancelled - database state could be invalid")
      raise

    if not self.args.download_only:
      dbc.close()

      # If we just made a new DB...
      if 'clean' in self.args.steps:
        if os.path.isfile(db_file):
          os.unlink(db_file)
        shutil.move(db_open_filename, db_file)
      else:
        log.debug("Existing database updated")

    log.info("All done in {}.".format(util.format_timer(g)))

  def import_csv_from_url(self, url, filename, description, batch_size, is_url_local = False, key = None):
    return self.import_data_from_url(read_header_csv, read_line_csv, read_all_csv, url, filename, description, batch_size, is_url_local, key)

  def import_json_from_url(self, url, filename, description, batch_size, is_url_local = False, key = None):
    return self.import_data_from_url(None, read_line_json, read_all_json, url, filename, description, batch_size, is_url_local, key)

  def import_data_from_url(self, fn_read_header, fn_read_line, fn_read_all, url, filename, description, batch_size, is_url_local, key):
    if self.args.copy_local:
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

        start = int(util.start_timer())
        done = 0
        failed = 0
        last_elapsed = 0

        header = None

        batch = []
        encoded = ''
        stream = util.open_url(url, allow_no_ssl=is_url_local)
        if stream is None:
          if self.args.copy_local:
            cleanup_local(f, scratch)
          return
        while True:
          line = util.read_stream_line(stream)
          if not line:
            break
          if self.args.copy_local:
            util.write_stream(f, line)
          if self.args.download_only:
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
          # Add to batch and check if we're now full
          batch.append(obj)
          if len(batch) >= batch_size:
            for obj in batch:
              yield obj
            done += len(batch)
            elapsed = int(util.get_timer(start))
            if elapsed - last_elapsed >= 30:
              log.info("Loaded {0} row(s) of {1} data to DB...", done, description)
              last_elapsed = elapsed
            batch = []
        done += len(batch)
        if not self.args.download_only:
          for obj in batch:
            yield obj
          if failed:
            log.info("Lines failing JSON parse: {0}", failed)
          log.info("Loaded {0} row(s) of {1} data to DB...", done, description)
          log.info("Imported data in {}, generating relevant indexes...".format(util.format_timer(start)))
      else:
        log.info("Downloading {0} list from {1} ... ", description, url)
        sys.stdout.flush()
        t = util.start_timer()
        encoded = util.read_from_url(url, allow_no_ssl=is_url_local)
        log.info("Done in {}.".format(util.format_timer(t)))
        if self.args.copy_local:
          log.info("Writing {0} local data...", description)
          sys.stdout.flush()
          t = util.start_timer()
          util.write_stream(f, encoded)
          log.info("Done in {}.".format(util.format_timer(t)))
        if not self.args.download_only:
          log.info("Loading {0} data...", description)
          sys.stdout.flush()
          t = util.start_timer()
          obj = fn_read_all(encoded)
          log.info("Done in {}.".format(util.format_timer(t)))
          log.info("Adding {0} data to DB...", description)
          sys.stdout.flush()
          t = util.start_timer()
          if key is not None:
            obj = obj[key]
          for o in obj:
            yield o
          log.info("Imported data in {}, generating relevant indexes...".format(util.format_timer(t)))
      # Force GC collection to try to avoid memory errors
      encoded = None
      obj = None
      batch = None
      gc.collect()
      if self.args.copy_local:
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
      if self.args.copy_local:
        cleanup_local(f, scratch)
      raise
