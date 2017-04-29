import collections
import decimal
import defs
import env_backend as eb
import filter
import json
import math
import os
import pgnames
import re
import sqlite3
import time
import util
import vector3

log = util.get_logger("db_sqlite3")

schema_version = 8

_find_operators = ['=','LIKE','REGEXP']
# This is nasty, and it may well not be used up in the main code
_bad_char_regex = re.compile("[^a-zA-Z0-9'&+:*^%_?.,/#@!=`() -|\[\]]")


_find_method_systems_entries = [
  'systems.name AS name',
  'systems.pos_x AS pos_x',
  'systems.pos_y AS pos_y',
  'systems.pos_z AS pos_z',
  'systems.id64 AS id64',
  'systems.data AS data',
  'systems.needs_permit AS needs_permit',
  'systems.arrival_star_class AS arrival_star_class'
]


def _regexp(expr, item):
  rgx = re.compile(expr)
  return rgx.search(item) is not None


def _vec3_len(x1, y1, z1, x2, y2, z2):
  xdiff = (x2-x1)
  ydiff = (y2-y1)
  zdiff = (z2-z1)
  return math.sqrt(xdiff*xdiff + ydiff*ydiff + zdiff*zdiff)

def _list_clause(field, mode, names):
  if mode in [eb.FIND_GLOB, eb.FIND_REGEX]:
    operator = _find_operators[mode]
    return "({})".format(' OR '.join(["{} {} ?".format(field, operator)] * len(names)))
  else:
    return "{} IN ({})".format(field, ','.join(['?'] * len(names)))

def _vec3_angle(x1, y1, z1, x2, y2, z2):
  return vector3.Vector3(x1, y1, z1).angle_to(vector3.Vector3(x2, y2, z2))


def log_versions():
  log.debug("SQLite3: {} / PySQLite: {}", sqlite3.sqlite_version, sqlite3.version)


def open_db(filename = defs.default_db_path, check_version = True):
  conn = sqlite3.connect(filename)
  conn.row_factory = sqlite3.Row
  conn.create_function("REGEXP", 2, _regexp)
  conn.create_function("vec3_len", 6, _vec3_len)
  conn.create_function("vec3_angle", 6, _vec3_angle)
 
  if check_version:
    c = conn.cursor()
    c.execute('SELECT db_version FROM edts_info')
    (db_version, ) = c.fetchone()
    if db_version != schema_version:
      log.warning("DB file's schema version {0} does not match the expected version {1}.", db_version, schema_version)
      log.warning("This is likely to cause errors; you may wish to rebuild the database by running update.py")
    log.debug("DB connection opened")
  return SQLite3DBConnection(conn, schema_version)


def initialise_db(filename = defs.default_db_path):
  dbc = open_db(filename, check_version=False)
  dbc._create_tables()
  return dbc


class SQLite3DBConnection(eb.EnvBackend):
  def __init__(self, conn, schema_version):
    super(SQLite3DBConnection, self).__init__("db_sqlite3")
    self._conn = conn
    self._schema_version = schema_version
    self._is_closed = False

  @property
  def schema_version(self):
    return self._schema_version

  @property
  def closed(self):
    return self._is_closed

  def close(self):
    self._conn.close()
    self._is_closed = True
    log.debug("DB connection closed")

  def compress(self, s):
    if self.schema_version >= 8:
      return util.zlib_compress(s)
    else:
      return s

  def decompress(self, b):
    if self.schema_version >= 8:
      return util.zlib_decompress(b)
    else:
      return b


  # ###
  # Creation/update methods
  # ###

  def _create_tables(self):
    log.debug("Creating tables...")
    c = self._conn.cursor()
    c.execute('CREATE TABLE edts_info (db_version INTEGER NOT NULL, db_mtime INTEGER NOT NULL, systems_source TEXT)')
    c.execute('INSERT INTO edts_info VALUES (?, ?, NULL)', (schema_version, int(time.time())))

    c.execute('CREATE TABLE systems (id INTEGER NOT NULL, name TEXT COLLATE NOCASE NOT NULL, pos_x REAL NOT NULL, pos_y REAL NOT NULL, pos_z REAL NOT NULL, edsm_id INTEGER, eddb_id INTEGER, id64 INTEGER, needs_permit BOOLEAN, allegiance TEXT, arrival_star_class TEXT, data BLOB)')
    c.execute('CREATE TABLE stations (eddb_id INTEGER NOT NULL, eddb_system_id INTEGER NOT NULL, name TEXT COLLATE NOCASE NOT NULL, eddb_body_id INTEGER, sc_distance INTEGER, station_type TEXT, max_pad_size TEXT, data BLOB)')
#   c.execute('CREATE TABLE bodies (eddb_id INTEGER NOT NULL, eddb_system_id INTEGER NOT NULL, id64 INTEGER, ...)
    c.execute('CREATE TABLE coriolis_fsds (id TEXT NOT NULL, data BLOB NOT NULL)')

    self._conn.commit()
    log.debug("Done.")

  def _generate_systems_eddb(self, systems):
    import id64data
    for s in systems:
      s_id64 = id64data.known_systems.get(s['name'].lower(), None)
      yield (int(s['id']), s['name'], float(s['x']), float(s['y']), float(s['z']), int(s['edsm_id']) if 'edsm_id' in s and s['edsm_id'] else None, int(s['id']), s_id64, bool(s['needs_permit']), s['allegiance'])

  def _generate_systems_edsm(self, systems):
    import id64data
    for s in systems:
      s_id64 = id64data.known_systems.get(s['name'].lower(), None)
      yield (int(s['id']), s['name'], float(s['coords']['x']), float(s['coords']['y']), float(s['coords']['z']), int(s['id']), s_id64)

  def _generate_systems_update_eddb(self, systems, id_column):
    for s in systems:
      yield (int(s['id']), bool(s['needs_permit']), s['allegiance'], self.compress(json.dumps(s)), s[id_column])

  def _generate_systems_arrival_star_update(self, bodies):
    tmp = {1: 'XBH', 2: 'XBH', 3: 'XNS'}
    for b in bodies:
      # Only update for arrival stars
      if bool(b['is_main_star']) is True:
        if int(b['group_id']) == 1:  # Compact star
          starcls = tmp.get(int(b['type_id']), 'X')
        else:
          starcls = b['spectral_class']
        yield (starcls, int(b['system_id']))

  def _generate_stations(self, stations):
    for s in stations:
      yield (int(s['id']), int(s['system_id']), s['name'], int(s['body_id']) if s['body_id'] is not None else None, int(s['distance_to_star']) if s['distance_to_star'] is not None else None, s['type'], s['max_landing_pad_size'], self.compress(json.dumps(s)))

  def _generate_coriolis_fsds(self, fsds):
    for fsd in fsds:
      yield ('{0}{1}'.format(fsd['class'], fsd['rating']), self.compress(json.dumps(fsd)))

  def populate_table_systems(self, many, systems_source):
    c = self._conn.cursor()
    c.execute('UPDATE edts_info SET systems_source=?', (systems_source,))
    log.debug("Going for INSERT INTO systems...")
    if systems_source == 'eddb':
      c.executemany('INSERT INTO systems VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)', self._generate_systems_eddb(many))
    elif systems_source == 'edsm':
      c.executemany('INSERT INTO systems VALUES (?, ?, ?, ?, ?, ?, NULL, ?, NULL, NULL, NULL, NULL)', self._generate_systems_edsm(many))
    else:
      raise ValueError("Invalid systems_source provided to populate_table_systems")
    self._conn.commit()
    log.debug("Done, {} rows inserted.", c.rowcount)
    log.debug("Going to add indexes to systems for name, pos_x/pos_y/pos_z, id...")
    c.execute('CREATE INDEX idx_systems_name ON systems (name COLLATE NOCASE)')
    c.execute('CREATE INDEX idx_systems_pos ON systems (pos_x, pos_y, pos_z)')
    c.execute('CREATE INDEX idx_systems_id ON systems (id)')
    c.execute('CREATE INDEX idx_systems_edsm_id ON systems (edsm_id)')
    if systems_source == 'eddb':
      c.execute('CREATE INDEX idx_systems_eddb_id ON systems (eddb_id)')
    c.execute('CREATE INDEX idx_systems_id64 ON systems (id64)')
    self._conn.commit()
    log.debug("Indexes added.")

  def update_table_systems(self, many, systems_source):
    c = self._conn.cursor()
    log.debug("Going for UPDATE systems...")
    id_column = 'id' if systems_source == 'eddb' else 'edsm_id'
    c.executemany('UPDATE systems SET eddb_id=?, needs_permit=?, allegiance=?, data=? WHERE id=?', self._generate_systems_update_eddb(many, id_column))
    self._conn.commit()
    log.debug("Done, {} rows affected.", c.rowcount)
    if systems_source != 'eddb':
      log.debug("Going to add indexes to systems for eddb_id...")
      c.execute('CREATE INDEX idx_systems_eddb_id ON systems (eddb_id)')
    self._conn.commit()
    log.debug("Indexes added.")

  def update_table_systems_with_id64(self):
    import id64data
    get_id64 = lambda s: id64data.known_systems.get(s.lower(), None)
    self._conn.create_function('get_id64', 1, get_id64)
    c = self._conn.cursor()
    log.debug("Going for UPDATE systems for ID64 data...")
    c.execute('UPDATE systems SET id64=get_id64(systems.name)')
    self._conn.commit()
    log.debug("Done, {} rows affected.", c.rowcount)

  def populate_table_stations(self, many):
    c = self._conn.cursor()
    log.debug("Going for INSERT INTO stations...")
    c.executemany('INSERT INTO stations VALUES (?, ?, ?, ?, ?, ?, ?, ?)', self._generate_stations(many))
    self._conn.commit()
    log.debug("Done, {} rows inserted.", c.rowcount)
    log.debug("Going to add indexes to stations for name, eddb_system_id...")
    c.execute('CREATE INDEX idx_stations_name ON stations (name COLLATE NOCASE)')
    c.execute('CREATE INDEX idx_stations_sysid ON stations (eddb_system_id)')
    self._conn.commit()
    log.debug("Indexes added.")

  def populate_table_bodies(self, many):
    c = self._conn.cursor()
    log.debug("Going for UPDATE systems for body data...")
    c.executemany('UPDATE systems SET arrival_star_class=? WHERE eddb_id=?', self._generate_systems_arrival_star_update(many))
    # log.debug("Going for INSERT into bodies...")
    # c.executemany('INSERT INTO bodies VALUES (...)', self._generate_bodies(many))
    self._conn.commit()

  def populate_table_coriolis_fsds(self, many):
    log.debug("Going for INSERT INTO coriolis_fsds...")
    c = self._conn.cursor()
    c.executemany('INSERT INTO coriolis_fsds VALUES (?, ?)', self._generate_coriolis_fsds(many))
    self._conn.commit()
    log.debug("Done, {} rows inserted.", c.rowcount)
    log.debug("Going to add indexes to coriolis_fsds for id...")
    c.execute('CREATE INDEX idx_coriolis_fsds_id ON coriolis_fsds (id)')
    self._conn.commit()
    log.debug("Indexes added.")

  
  # ###
  # Retrieval methods
  # ###

  def retrieve_fsd_list(self):
    c = self._conn.cursor()
    cmd = 'SELECT id, data FROM coriolis_fsds'
    log.debug("Executing: {}", cmd)
    c.execute(cmd)
    results = c.fetchall()
    log.debug("Done.")
    return dict([(k, json.loads(self.decompress(v))) for (k, v) in results])

  def get_system_by_id64(self, id64, fallback_name = None):
    c = self._conn.cursor()
    cmd, params = _construct_query(
      ['systems'],
      _find_method_systems_entries,
      ["systems.id64 = ? OR systems.name = ?"] if fallback_name else ["systems.id64 = ?"],
      [],
      [id64, fallback_name] if fallback_name else [id64])
    log.debug("Executing: {}; params = {}", cmd, params)
    c.execute(cmd, params)
    result = c.fetchone()
    log.debug("Done.")
    if result is not None:
      return self._process_system_result(result)
    else:
      return None

  def get_system_by_name(self, name):
    c = self._conn.cursor()
    cmd, params = _construct_query(
      ['systems'],
      _find_method_systems_entries,
      ["systems.name = ?"],
      [],
      [name])
    log.debug("Executing: {}; params = {}", cmd, params)
    c.execute(cmd, params)
    result = c.fetchone()
    log.debug("Done.")
    if result is not None:
      return self._process_system_result(result)
    else:
      return None

  def get_systems_by_name(self, names):
    c = self._conn.cursor()
    cmd, params = _construct_query(
      ['systems'],
      _find_method_systems_entries,
      ["systems.name IN ({})".format(','.join(['?'] * len(names)))],
      [],
      names)
    log.debug("Executing: {}; params = {}", cmd, params)
    c.execute(cmd, params)
    result = c.fetchall()
    log.debug("Done.")
    if result is not None:
      return [self._process_system_result(r) for r in result]
    else:
      return None

  def get_station_by_names(self, sysname, stnname):
    c = self._conn.cursor()
    cmd, params = _construct_query(
      ['systems', 'stations'],
      _find_method_systems_entries + ["stations.data AS stndata"],
      ["systems.name = ?", "stations.name = ?"],
      [],
      [sysname, stnname])
    log.debug("Executing: {}; params = {}", cmd, params)
    c.execute(cmd, params)
    result = c.fetchone()
    log.debug("Done.")
    if result is not None:
      return (self._process_system_result(result), self._process_station_result(result))
    else:
      return (None, None)

  def get_stations_by_names(self, names):
    c = self._conn.cursor()
    cmd, params = _construct_query(
      ['systems', 'stations'],
      _find_method_systems_entries + ["stations.data AS stndata"],
      [' OR '.join(['(systems.name = ? AND stations.name = ?)'] * len(names))],
      [],
      [n for sublist in names for n in sublist])
    log.debug("Executing: {}; params = {}", cmd, params)
    c.execute(cmd, params)
    result = c.fetchall()
    log.debug("Done.")
    if result is not None:
      return [(self._process_system_result(r), self._process_station_result(r)) for r in result]
    else:
      return (None, None)

  def find_stations_by_system_id(self, args, filters = None):
    sysids = args if isinstance(args, collections.Iterable) else [args]
    c = self._conn.cursor()
    cmd, params = _construct_query(
      ['stations'],
      ['stations.eddb_system_id AS system_id', 'stations.data AS stndata'],
      ['stations.eddb_system_id IN ({})'.format(','.join(['?'] * len(sysids)))],
      [],
      sysids,
      filters)
    log.debug("Executing: {}; params = {}", cmd, params)
    c.execute(cmd, params)
    results = c.fetchall()
    log.debug("Done, {} results.", len(results))
    return [{ k: v for d in [{ 'eddb_system_id': r['system_id'] }, self._process_station_result(r)] for k, v in d.items()} for r in results]

  def find_systems_by_aabb(self, min_x, min_y, min_z, max_x, max_y, max_z, filters = None):
    c = self._conn.cursor()
    cmd, params = _construct_query(
      ['systems'],
      _find_method_systems_entries,
      ['? <= systems.pos_x', 'systems.pos_x < ?', '? <= systems.pos_y', 'systems.pos_y < ?', '? <= systems.pos_z', 'systems.pos_z < ?'],
      [],
      [min_x, max_x, min_y, max_y, min_z, max_z],
      filters)
    log.debug("Executing: {}; params = {}", cmd, params)
    c.execute(cmd, params)
    results = c.fetchall()
    log.debug("Done, {} results.", len(results))
    return [self._process_system_result(r) for r in results]
    
  def find_systems_by_name(self, namelist, mode = eb.FIND_EXACT, filters = None):
    # return self.find_systems_by_name_safe(namelist, mode, filters)
    return self.find_systems_by_name_unsafe(namelist, mode, filters)

  def find_systems_by_id64(self, id64list, filters = None):
    return self.find_systems_by_id64_safe(id64list, filters)

  def find_stations_by_name(self, name, mode = eb.FIND_EXACT, filters = None):
    # return self.find_stations_by_name_safe(name, mode, filters)
    return self.find_stations_by_name_unsafe(name, mode, filters)

  def find_systems_by_name_safe(self, namelist, mode = eb.FIND_EXACT, filters = None):
    names = util.flatten(namelist)
    if mode == eb.FIND_GLOB and _find_operators[mode] == 'LIKE':
      names = map(lambda name: name.replace('*','%').replace('?','_'), names)
    c = self._conn.cursor()
    cmd, params = _construct_query(
      ['systems'],
      _find_method_systems_entries,
      [_list_clause('systems.name', mode, names)],
      [],
      names,
      filters)
    log.debug("Executing: {}; params = {}", cmd, params)
    c.execute(cmd, params)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield self._process_system_result(result)
      result = c.fetchone()

  def find_stations_by_name_safe(self, name, mode = eb.FIND_EXACT, filters = None):
    if mode == eb.FIND_GLOB and _find_operators[mode] == 'LIKE':
      name = name.replace('*','%').replace('?','_')
    c = self._conn.cursor()
    cmd, params = _construct_query(
      ['systems', 'stations'],
      _find_method_systems_entries + ['stations.data AS stndata'],
      ['stations.name {} ?'.format(_find_operators[mode])],
      [],
      [name],
      filters)
    log.debug("Executing: {}; params = {}", cmd, params)
    c.execute(cmd, params)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield (self._process_system_result(result), self._process_station_result(result))
      result = c.fetchone()

  def find_systems_by_id64_safe(self, id64list, filters = None):
    c = self._conn.cursor()
    cmd, params = _construct_query(
      ['systems'],
      _find_method_systems_entries,
      ["systems.id64 IN ({})".format(','.join(['?'] * len(id64list)))],
      [],
      id64list,
      filters)
    log.debug("Executing: {}; params = {}", cmd, params)
    c.execute(cmd, params)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield self._process_system_result(result)
      result = c.fetchone()

  # WARNING: VERY UNSAFE, USE WITH CARE
  # These methods exist due to a bug in the Python sqlite3 module
  # Using bound parameters as the safe versions do results in indexes being ignored
  # This significantly slows down searches (~500x at time of writing) due to doing full table scans
  # So, these methods are fast but vulnerable to SQL injection due to use of string literals
  # This will hopefully be unnecessary in Python 2.7.11+ / 3.6.0+ if porting of a newer pysqlite2 version is completed
  def find_systems_by_name_unsafe(self, namelist, mode=eb.FIND_EXACT, filters = None):
    names = util.flatten(namelist)
    if mode == eb.FIND_GLOB and _find_operators[mode] == 'LIKE':
      names = map(lambda name: name.replace('*','%').replace('?','_'), names)
    names = map(lambda name: _bad_char_regex.sub("", name), names)
    names = map(lambda name: name.replace("'", r"''"), names)
    c = self._conn.cursor()
    cmd, params = _construct_query(
      ['systems'],
      _find_method_systems_entries,
      [_list_clause('systems.name', mode, names)],
      [],
      names,
      filters)
    log.debug("Executing (U): {}; params = {}", cmd, params)
    c.execute(cmd, params)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield self._process_system_result(result)
      result = c.fetchone()

  def find_stations_by_name_unsafe(self, name, mode=eb.FIND_EXACT, filters = None):
    if mode == eb.FIND_GLOB and _find_operators[mode] == 'LIKE':
      name = name.replace('*','%').replace('?','_')
    name = _bad_char_regex.sub("", name)
    name = name.replace("'", r"''")
    cmd, params = _construct_query(
      ['systems', 'stations'],
      _find_method_systems_entries + ['stations.data AS stndata'],
      ["stations.name {} '{}'".format(_find_operators[mode], name)],
      [],
      [],
      filters)
    c = self._conn.cursor()
    log.debug("Executing (U): {}; params = {}", cmd, params)
    c.execute(cmd, params)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield (self._process_system_result(result), self._process_station_result(result))
      result = c.fetchone()

  # Slow as sin; avoid if at all possible
  def find_all_systems(self, filters = None):
    c = self._conn.cursor()
    cmd, params = _construct_query(
      ['systems'],
      _find_method_systems_entries,
      [],
      [],
      [],
      filters)
    log.debug("Executing: {}; params = {}", cmd, params)
    c.execute(cmd, params)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield self._process_system_result(result)
      result = c.fetchone()

  # Slow as sin; avoid if at all possible
  def find_all_stations(self, filters = None):
    c = self._conn.cursor()
    cmd, params = _construct_query(
      ['systems', 'stations'],
      _find_method_systems_entries + ['stations.data AS stndata'],
      [],
      [],
      [],
      filters) 
    log.debug("Executing: {}; params = {}", cmd, params)
    c.execute(cmd, params)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield (self._process_system_result(result), self._process_station_result(result))
      result = c.fetchone()

  def get_populated_systems(self):
    c = self._conn.cursor()
    cmd = 'SELECT name, pos_x, pos_y, pos_z, data, id64, needs_permit, arrival_star_class FROM systems WHERE allegiance IS NOT NULL'
    log.debug("Executing: {}", cmd)
    c.execute(cmd)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield self._process_system_result(result)
      result = c.fetchone()


  # ###
  # Result processing
  # ###

  def _process_system_result(self, result):
    if 'data' in result.keys() and result['data'] is not None:
      data = json.loads(self.decompress(result['data']))
    else:
      data = {'name': result['name'], 'x': result['pos_x'], 'y': result['pos_y'], 'z': result['pos_z']}
    # If our data source is EDDB, much of this is likely to be populated even if we don't have a data JSON
    for key in ('id64','needs_permit','arrival_star_class'):
      data[key] = result[key]
    return data

  def _process_station_result(self, result):
    return json.loads(self.decompress(result['stndata']))


def _construct_query(qtables, select, qfilter, select_params = [], filter_params = [], filters = None):
  tables = qtables
  qmodifier = []
  qmodifier_params = []
  # Apply any user-defined filters
  if filters:
    fsql = filter.generate_sql(filters)
    tables = set(qtables + fsql['tables'])
    select = select + fsql['select'][0]
    qfilter = qfilter + fsql['filter'][0]
    select_params += fsql['select'][1]
    filter_params += fsql['filter'][1]
    group = fsql['group'][0]
    group_params = fsql['group'][1]
    # Hack, since we can't really know this before here :(
    if 'stations' in tables and 'systems' in tables:
      qfilter.append("systems.eddb_id=stations.eddb_system_id")
      # More hack: if we weren't originally joining on stations, group results by system
      if 'stations' not in qtables:
        group.append('systems.eddb_id')
    # If we have any groups/ordering/limiting, set it up
    if any(group):
      qmodifier.append('GROUP BY {}'.format(', '.join(group)))
      qmodifier_params += group_params
    if any(fsql['order'][0]):
      qmodifier.append('ORDER BY {}'.format(', '.join(fsql['order'][0])))
      qmodifier_params += fsql['order'][1]
    if fsql['limit']:
      qmodifier.append('LIMIT {}'.format(fsql['limit']))
  else:
    # Still need to check this
    if 'stations' in tables and 'systems' in tables:
      qfilter.append("systems.eddb_id=stations.eddb_system_id")

  q1 = 'SELECT {} FROM {}'.format(','.join(select), ','.join(tables))
  q2 = 'WHERE {}'.format(' AND '.join(qfilter)) if any(qfilter) else ''
  q3 = ' '.join(qmodifier)
  query = '{} {} {}'.format(q1, q2, q3)
  params = select_params + filter_params + qmodifier_params
  return (query, params)
