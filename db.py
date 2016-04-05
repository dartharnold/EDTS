import json
import logging
import os
import re
import sqlite3
import time

log = logging.getLogger("db")

default_db_file = 'data/edts.db'
schema_version = 4

FIND_EXACT = 0
FIND_GLOB = 1
FIND_REGEX = 2

_find_operators = ['=','LIKE','REGEXP']

def _regexp(expr, item):
  rgx = re.compile(expr)
  return rgx.search(item) is not None


def open_db(filename = default_db_file, check_version = True):
  conn = sqlite3.connect(filename)
  conn.create_function("REGEXP", 2, _regexp)
 
  if check_version:
    c = conn.cursor()
    c.execute('SELECT db_version FROM edts_info')
    (db_version, ) = c.fetchone()
    if db_version != schema_version:
      log.warning("DB file's schema version {0} does not match the expected version {1}.".format(db_version, schema_version))
      log.warning("This may cause errors; you may wish to rebuild the database by running update.py")
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
  
  def _create_tables(self):
    c = self._conn.cursor()
    c.execute('CREATE TABLE edts_info (db_version INTEGER, db_mtime INTEGER)')
    c.execute('INSERT INTO edts_info VALUES (?, ?)', (schema_version, int(time.time())))

    c.execute('CREATE TABLE eddb_systems (id INTEGER, name TEXT COLLATE NOCASE, pos_x REAL, pos_y REAL, pos_z REAL, needs_permit BOOLEAN, allegiance TEXT, data TEXT)')
    c.execute('CREATE TABLE eddb_stations (id INTEGER, system_id INTEGER, name TEXT COLLATE NOCASE, sc_distance INTEGER, station_type TEXT, max_pad_size TEXT, data TEXT)')
    c.execute('CREATE TABLE coriolis_fsds (id TEXT, data TEXT)')

    c.execute('CREATE INDEX idx_eddb_systems_name ON eddb_systems (name COLLATE NOCASE)')
    c.execute('CREATE INDEX idx_eddb_systems_pos ON eddb_systems (pos_x, pos_y, pos_z)')
    c.execute('CREATE INDEX idx_eddb_stations_name ON eddb_stations (name COLLATE NOCASE)')
    c.execute('CREATE INDEX idx_eddb_stations_sysid ON eddb_stations (system_id)')

    self._conn.commit()

  def populate_table_eddb_systems(self, systems):
    sysdata = [(int(s['id']), s['name'], float(s['x']), float(s['y']), float(s['z']), bool(s['needs_permit']), s['allegiance'], json.dumps(s)) for s in systems]
    c = self._conn.cursor()
    c.executemany('INSERT INTO eddb_systems VALUES (?, ?, ?, ?, ?, ?, ?, ?)', sysdata)
    self._conn.commit()

  def populate_table_eddb_stations(self, stations):
    stndata = [(int(s['id']), int(s['system_id']), s['name'], int(s['distance_to_star']) if s['distance_to_star'] is not None else None, s['type'], s['max_landing_pad_size'], json.dumps(s)) for s in stations]
    c = self._conn.cursor()
    c.executemany('INSERT INTO eddb_stations VALUES (?, ?, ?, ?, ?, ?, ?)', stndata)
    self._conn.commit()

  def populate_table_coriolis_fsds(self, fsds):
    fsddata = [(k, json.dumps(v)) for (k, v) in fsds.items()]
    c = self._conn.cursor()
    c.executemany('INSERT INTO coriolis_fsds VALUES (?, ?)', fsddata)
    self._conn.commit()

  def retrieve_fsd_list(self):
    c = self._conn.cursor()
    c.execute('SELECT id, data FROM coriolis_fsds')
    results = c.fetchall()
    return dict([(k, json.loads(v)) for (k, v) in results])

  def get_system_by_name(self, name):
    c = self._conn.cursor()
    c.execute('SELECT data FROM eddb_systems WHERE name = ?', (name, ))
    result = c.fetchone()
    if result != None:
      return json.loads(result[0])
    else:
      return None

  def get_station_by_names(self, sysname, stnname):
    c = self._conn.cursor()
    c.execute('SELECT sy.data AS sysdata, st.data AS stndata FROM eddb_systems sy, eddb_stations st WHERE sy.name = ? AND st.name = ? AND sy.id = st.system_id', (sysname, stnname))
    result = c.fetchone()
    if result != None:
      return (json.loads(result[0]), json.loads(result[1]))
    else:
      return (None, None)

  def get_stations_by_system_id(self, sysid):
    c = self._conn.cursor()
    c.execute('SELECT data FROM eddb_stations WHERE system_id = ?', (sysid, ))
    results = c.fetchall()
    return [json.loads(r[0]) for r in results]

  def get_systems_by_aabb(self, min_x, min_y, min_z, max_x, max_y, max_z):
    c = self._conn.cursor()
    c.execute('SELECT data FROM eddb_systems WHERE ? <= pos_x AND pos_x < ? AND ? <= pos_y AND pos_y < ? AND ? <= pos_z AND pos_z < ?', (min_x, max_x, min_y, max_y, min_z, max_z))
    results = c.fetchall()
    return [json.loads(r[0]) for r in results]
    
  def find_systems_by_name(self, name, mode=FIND_EXACT):
    if mode == FIND_GLOB:
      name = name.replace('*','%').replace('?','_')
    c = self._conn.cursor()
    c.execute('SELECT data FROM eddb_systems WHERE name {0} ?'.format(_find_operators[mode]), (name, ))
    result = c.fetchone()
    while result is not None:
      yield json.loads(result[0])
      result = c.fetchone()

  def find_stations_by_name(self, name, mode=FIND_EXACT):
    if mode == FIND_GLOB:
      name = name.replace('*','%').replace('?','_')
    c = self._conn.cursor()
    c.execute('SELECT sy.data AS sysdata, st.data AS stndata FROM eddb_systems sy, eddb_stations st WHERE st.name {0} ? AND sy.id = st.system_id'.format(_find_operators[mode]), (name, ))
    result = c.fetchone()
    while result is not None:
      yield (json.loads(result[0]), json.loads(result[1]))
      result = c.fetchone()
  
  # Slow as sin; avoid if at all possible
  def get_all_systems(self):
    c = self._conn.cursor()
    c.execute('SELECT data FROM eddb_systems')
    result = c.fetchone()
    while result is not None:
      yield json.loads(result[0])
      result = c.fetchone()