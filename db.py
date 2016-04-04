import json
import logging
import os
import re
import sqlite3
import time

log = logging.getLogger("db")

default_db_file = 'data/edts.db'
schema_version = 3

def _regexp(expr, item):
  rgx = re.compile(expr)
  return rgx.search(item) is not None


def open_db(filename = default_db_file):
  conn = sqlite3.connect(filename)
  conn.create_function("REGEXP", 2, _regexp)
  
  c = conn.cursor()
  c.execute('SELECT db_version FROM edts_info')
  (db_version, ) = c.fetchone()
  if db_version != schema_version:
    log.warning("DB file's schema version {0} does not match the expected version {1}.".format(db_version, schema_version))
    log.warning("This may cause errors; you may wish to rebuild the database by running update.py")
  return conn


def initialise_db(filename = default_db_file):
  conn = open_db(filename)
  c = conn.cursor()
  c.execute('CREATE TABLE edts_info (db_version INTEGER, db_mtime INTEGER)')
  c.execute('INSERT INTO edts_info VALUES (?, ?)', (schema_version, int(time.time())))
  
  c.execute('CREATE TABLE eddb_systems (id INTEGER, name TEXT, pos_x REAL, pos_y REAL, pos_z REAL, needs_permit BOOLEAN, allegiance TEXT, data TEXT)')
  c.execute('CREATE TABLE eddb_stations (id INTEGER, system_id INTEGER, name TEXT, sc_distance INTEGER, station_type TEXT, max_pad_size TEXT, data TEXT)')
  c.execute('CREATE TABLE coriolis_fsds (id TEXT, data TEXT)')
  
  c.execute('CREATE INDEX idx_eddb_systems_name ON eddb_systems (name)')
  c.execute('CREATE INDEX idx_eddb_systems_pos ON eddb_systems (pos_x, pos_y, pos_z)')
  c.execute('CREATE INDEX idx_eddb_stations_name ON eddb_stations (name)')
  
  conn.commit()
  return conn


def populate_table_eddb_systems(conn, systems):
 sysdata = [(int(s['id']), s['name'], float(s['x']), float(s['y']), float(s['z']), bool(s['needs_permit']), s['allegiance'], json.dumps(s)) for s in systems]
 c = conn.cursor()
 c.executemany('INSERT INTO eddb_systems VALUES (?, ?, ?, ?, ?, ?, ?, ?)', sysdata)
 conn.commit()


def populate_table_eddb_stations(conn, stations):
  stndata = [(int(s['id']), int(s['system_id']), s['name'], int(s['distance_to_star']) if s['distance_to_star'] is not None else None, s['type'], s['max_landing_pad_size'], json.dumps(s)) for s in stations]
  c = conn.cursor()
  c.executemany('INSERT INTO eddb_stations VALUES (?, ?, ?, ?, ?, ?, ?)', stndata)
  conn.commit()


def populate_table_coriolis_fsds(conn, fsds):
  fsddata = [(k, json.dumps(v)) for (k, v) in fsds.items()]
  c = conn.cursor()
  c.executemany('INSERT INTO coriolis_fsds VALUES (?, ?)', fsddata)
  conn.commit()