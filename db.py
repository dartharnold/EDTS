import json
import os
import sqlite3
import eddb

schema_version = 1

def initialise_db(filename):
  sys_mtime = int(os.path.getmtime(eddb.default_systems_file))
  stn_mtime = int(os.path.getmtime(eddb.default_stations_file))

  conn = sqlite3.connect(filename)
  c = conn.cursor()
  c.execute('CREATE TABLE edts_info (db_version INTEGER, systems_file_mtime INTEGER, stations_file_mtime INTEGER)')
  c.execute('INSERT INTO edts_info VALUES (?, ?, ?)', (schema_version, sys_mtime, stn_mtime))
  c.execute('CREATE TABLE eddb_systems (id INTEGER, name TEXT, pos_x REAL, pos_y REAL, pos_z REAL, needs_permit BOOLEAN, allegiance TEXT, data TEXT)')
  c.execute('CREATE TABLE eddb_stations (id INTEGER, system_id INTEGER, name TEXT, sc_distance INTEGER, station_type TEXT, max_pad_size TEXT, data TEXT)')
  conn.commit()

  _populate_table_eddb_systems(conn, eddb.default_systems_file)
  _populate_table_eddb_stations(conn, eddb.default_stations_file)

  conn.close()


def _populate_table_eddb_systems(conn, systems_file):
 systems = eddb.load_systems(systems_file)
 sysdata = [(int(s['id']), s['name'], float(s['x']), float(s['y']), float(s['z']), bool(s['needs_permit']), s['allegiance'], json.dumps(s)) for s in systems]
 c = conn.cursor()
 c.executemany('INSERT INTO eddb_systems VALUES (?, ?, ?, ?, ?, ?, ?, ?)', sysdata)
 conn.commit()


def _populate_table_eddb_stations(conn, stations_file):
  stations = eddb.load_stations(stations_file)
  stndata = [(int(s['id']), int(s['system_id']), s['name'], int(s['distance_to_star']) if s['distance_to_star'] is not None else None, s['type'], s['max_landing_pad_size'], json.dumps(s)) for s in stations]
  c = conn.cursor()
  c.executemany('INSERT INTO eddb_stations VALUES (?, ?, ?, ?, ?, ?, ?)', stndata)
  conn.commit()


