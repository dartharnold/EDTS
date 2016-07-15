import json
import logging
import math
import os
import re
import sqlite3
import time

log = logging.getLogger("db")

default_db_file = 'data/edts.db'
schema_version = 5

FIND_EXACT = 0
FIND_GLOB = 1
FIND_REGEX = 2

_find_operators = ['=','LIKE','REGEXP']
# This is nasty, and it may well not be used up in the main code
_bad_char_regex = re.compile("[^a-zA-Z0-9'&+:*^%_?.,/#@!=`() -]")

def _regexp(expr, item):
  rgx = re.compile(expr)
  return rgx.search(item) is not None

def _vec3_len(x1, y1, z1, x2, y2, z2):
  xdiff = (x2-x1)
  ydiff = (y2-y1)
  zdiff = (z2-z1)
  return math.sqrt(xdiff*xdiff + ydiff*ydiff + zdiff*zdiff)


def open_db(filename = default_db_file, check_version = True):
  conn = sqlite3.connect(filename)
  conn.create_function("REGEXP", 2, _regexp)
  conn.create_function("vec3_len", 6, _vec3_len)
 
  if check_version:
    c = conn.cursor()
    c.execute('SELECT db_version FROM edts_info')
    (db_version, ) = c.fetchone()
    if db_version != schema_version:
      log.warning("DB file's schema version {0} does not match the expected version {1}.".format(db_version, schema_version))
      log.warning("This is likely to cause errors; you may wish to rebuild the database by running update.py")
    log.debug("DB connection opened")
  return DBConnection(conn)

def initialise_db(filename = default_db_file):
  dbc = open_db(filename, check_version=False)
  dbc._create_tables()
  return dbc

class DBConnection(object):
  def __init__(self, conn):
    self._conn = conn

  def close(self):
    self._conn.close()
    log.debug("DB connection closed")

  def _create_tables(self):
    log.debug("Creating tables...")
    c = self._conn.cursor()
    c.execute('CREATE TABLE edts_info (db_version INTEGER, db_mtime INTEGER)')
    c.execute('INSERT INTO edts_info VALUES (?, ?)', (schema_version, int(time.time())))

    c.execute('CREATE TABLE systems (edsm_id INTEGER, eddb_id INTEGER, name TEXT COLLATE NOCASE, pos_x REAL, pos_y REAL, pos_z REAL, needs_permit BOOLEAN, allegiance TEXT, data TEXT)')
    c.execute('CREATE TABLE stations (eddb_id INTEGER, eddb_system_id INTEGER, name TEXT COLLATE NOCASE, sc_distance INTEGER, station_type TEXT, max_pad_size TEXT, data TEXT)')
    c.execute('CREATE TABLE coriolis_fsds (id TEXT, data TEXT)')

    c.execute('CREATE INDEX idx_systems_name ON systems (name COLLATE NOCASE)')
    c.execute('CREATE INDEX idx_systems_pos ON systems (pos_x, pos_y, pos_z)')
    c.execute('CREATE INDEX idx_stations_name ON stations (name COLLATE NOCASE)')
    c.execute('CREATE INDEX idx_stations_sysid ON stations (eddb_system_id)')

    self._conn.commit()
    log.debug("Done.")

  def populate_table_systems(self, edsm_systems):
    sysdata = [(int(s['id']), s['name'], float(s['coords']['x']), float(s['coords']['y']), float(s['coords']['z'])) for s in edsm_systems]
    # sysdata = [(int(s['id']), s['name'], float(s['coords']['x']), float(s['coords']['y']), float(s['coords']['z']), bool(s['needs_permit']), s['allegiance'], json.dumps(s)) for s in systems]
    c = self._conn.cursor()
    log.debug("Going for INSERT INTO systems for {} systems".format(len(sysdata)))
    c.executemany('INSERT INTO systems VALUES (?, NULL, ?, ?, ?, ?, NULL, NULL, NULL)', sysdata)
    self._conn.commit()
    log.debug("Done.")

  def update_table_systems(self, eddb_systems):
    sysdata = [(int(s['id']), bool(s['needs_permit']), s['allegiance'], json.dumps(s), s['name']) for s in eddb_systems]
    c = self._conn.cursor()
    log.debug("Going for UPDATE systems for {} systems".format(len(sysdata)))
    c.executemany('UPDATE systems SET eddb_id=?, needs_permit=?, allegiance=?, data=? WHERE name=? AND eddb_id IS NULL', sysdata)
    self._conn.commit()
    log.debug("Done.")
  
  def trim_table_systems(self):
    c = self._conn.cursor()
    cmd = 'DELETE FROM systems WHERE eddb_id IS NULL'
    log.debug("Executing: {}".format(cmd))
    c.execute(cmd)
    self._conn.commit()
    log.debug("Done.")

  def populate_table_stations(self, eddb_stations):
    stndata = [(int(s['id']), int(s['system_id']), s['name'], int(s['distance_to_star']) if s['distance_to_star'] is not None else None, s['type'], s['max_landing_pad_size'], json.dumps(s)) for s in eddb_stations]
    c = self._conn.cursor()
    log.debug("Going for INSERT INTO stations for {} stations".format(len(stndata)))
    c.executemany('INSERT INTO stations VALUES (?, ?, ?, ?, ?, ?, ?)', stndata)
    self._conn.commit()
    log.debug("Done.")

  def populate_table_coriolis_fsds(self, fsds):
    fsddata = [(k, json.dumps(v)) for (k, v) in fsds.items()]
    c = self._conn.cursor()
    log.debug("Going for INSERT INTO coriolis_fsds for {} entries".format(len(fsddata)))
    c.executemany('INSERT INTO coriolis_fsds VALUES (?, ?)', fsddata)
    self._conn.commit()
    log.debug("Done.")

  def retrieve_fsd_list(self):
    c = self._conn.cursor()
    cmd = 'SELECT id, data FROM coriolis_fsds'
    log.debug("Executing: {}".format(cmd))
    c.execute(cmd)
    results = c.fetchall()
    log.debug("Done.")
    return dict([(k, json.loads(v)) for (k, v) in results])

  def get_system_by_name(self, name):
    c = self._conn.cursor()
    cmd = 'SELECT data FROM systems WHERE name = ?'
    log.debug("Executing: {}; name = {}".format(cmd, name))
    c.execute(cmd, (name, ))
    result = c.fetchone()
    log.debug("Done.")
    if result != None:
      return json.loads(result[0])
    else:
      return None

  def get_station_by_names(self, sysname, stnname):
    c = self._conn.cursor()
    cmd = 'SELECT sy.data AS sysdata, st.data AS stndata FROM systems sy, stations st WHERE sy.name = ? AND st.name = ? AND sy.eddb_id = st.eddb_system_id'
    log.debug("Executing: {}; sysname = {}, stnname = {}".format(cmd, sysname, stnname))
    c.execute(cmd, (sysname, stnname))
    result = c.fetchone()
    log.debug("Done.")
    if result != None:
      return (json.loads(result[0]), json.loads(result[1]))
    else:
      return (None, None)

  def get_stations_by_system_id(self, sysid):
    c = self._conn.cursor()
    cmd = 'SELECT data FROM stations WHERE eddb_system_id = ?'
    log.debug("Executing: {}; sysid = {}".format(cmd, sysid))
    c.execute(cmd, (sysid, ))
    results = c.fetchall()
    log.debug("Done.")
    return [json.loads(r[0]) for r in results]

  def get_systems_by_aabb(self, min_x, min_y, min_z, max_x, max_y, max_z):
    c = self._conn.cursor()
    cmd = 'SELECT data FROM systems WHERE ? <= pos_x AND pos_x < ? AND ? <= pos_y AND pos_y < ? AND ? <= pos_z AND pos_z < ?'
    log.debug("Executing: {}; min_x = {}, max_x = {}, min_y = {}, max_y = {}, min_z = {}, max_z = {}".format(cmd, min_x, max_x, min_y, max_y, min_z, max_z))
    c.execute(cmd, (min_x, max_x, min_y, max_y, min_z, max_z))
    results = c.fetchall()
    log.debug("Done.")
    return [json.loads(r[0]) for r in results]
    
  def find_systems_by_name(self, name, mode=FIND_EXACT):
    if mode == FIND_GLOB and _find_operators[mode] == 'LIKE':
      name = name.replace('*','%').replace('?','_')
    c = self._conn.cursor()
    cmd = 'SELECT data FROM systems WHERE name {0} ?'.format(_find_operators[mode])
    log.debug("Executing: {}; name = {}".format(cmd, name))
    c.execute(cmd, (name, ))
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield json.loads(result[0])
      result = c.fetchone()

  def find_stations_by_name(self, name, mode=FIND_EXACT):
    if mode == FIND_GLOB and _find_operators[mode] == 'LIKE':
      name = name.replace('*','%').replace('?','_')
    c = self._conn.cursor()
    cmd = 'SELECT sy.data AS sysdata, st.data AS stndata FROM systems sy, stations st WHERE st.name {0} ? AND sy.eddb_id = st.eddb_system_id'.format(_find_operators[mode])
    log.debug("Executing: {}; name = {}".format(cmd, name))
    c.execute(cmd, (name, ))
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield (json.loads(result[0]), json.loads(result[1]))
      result = c.fetchone()
  
  # WARNING: VERY UNSAFE, USE WITH CARE
  # These methods exist due to a bug in the Python sqlite3 module
  # Using bound parameters as the safe versions do results in indexes being ignored
  # This significantly slows down searches (~500x at time of writing) due to doing full table scans
  # So, these methods are fast but vulnerable to SQL injection due to use of string literals
  # This will hopefully be unnecessary in Python 2.7.11+ / 3.6.0+ if porting of a newer pysqlite2 version is completed
  def find_systems_by_name_unsafe(self, name, mode=FIND_EXACT):
    if mode == FIND_GLOB and _find_operators[mode] == 'LIKE':
      name = name.replace('*','%').replace('?','_')
    name = _bad_char_regex.sub("", name)
    name = name.replace("'", r"''")
    c = self._conn.cursor()
    cmd = "SELECT data FROM systems WHERE name {0} '{1}'".format(_find_operators[mode], name)
    log.debug("Executing (U): {}".format(cmd))
    c.execute(cmd)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield json.loads(result[0])
      result = c.fetchone()

  def find_stations_by_name_unsafe(self, name, mode=FIND_EXACT):
    if mode == FIND_GLOB and _find_operators[mode] == 'LIKE':
      name = name.replace('*','%').replace('?','_')
    name = _bad_char_regex.sub("", name)
    name = name.replace("'", r"''")
    c = self._conn.cursor()
    cmd = "SELECT sy.data AS sysdata, st.data AS stndata FROM systems sy, stations st WHERE st.name {0} '{1}' AND sy.eddb_id = st.eddb_system_id".format(_find_operators[mode], name)
    log.debug("Executing (U): {}".format(cmd))
    c.execute(cmd)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield (json.loads(result[0]), json.loads(result[1]))
      result = c.fetchone()

  # Slow as sin; avoid if at all possible
  def get_all_systems(self):
    c = self._conn.cursor()
    cmd = 'SELECT data FROM systems'
    log.debug("Executing: {}".format(cmd))
    c.execute(cmd)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield json.loads(result[0])
      result = c.fetchone()

  # Slow as sin; avoid if at all possible
  def get_all_stations(self):
    c = self._conn.cursor()
    cmd = 'SELECT stations.data, systems.data FROM stations, systems WHERE stations.eddb_system_id = systems.eddb_id'
    log.debug("Executing: {}".format(cmd))
    c.execute(cmd)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield (json.loads(result[0]), json.loads(result[1]))
      result = c.fetchone()
