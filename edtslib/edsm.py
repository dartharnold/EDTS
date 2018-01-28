from __future__ import print_function
import datetime
import json
import re
import time

from . import util
from . import vector3

log = util.get_logger("edsm")

class EDSMCacheHit(Exception):
  pass

class EDSMCache(object):
  HOST = 'https://www.edsm.net'
  STANDARD_ARGS = [
    'showId=1',
    'showCoordinates=1',
    'showInformation=1',
    'showPermit=1',
    'showPrimaryStar=1'
    ]

  def __init__(self, cache_time = 604800, conn = None):
    self.cache_time = cache_time
    self.conn = conn

  def _name_params(self, names):
    return '({})'.format(','.join(['?'] * len(names)))

  def _cached(self, api, endpoint, names):
    if not self.cache_time or self.conn is None:
      return
    cutoff = int(time.time()) - self.cache_time
    log.debug('Checking {} in cache since {}'.format((api, endpoint, str(names)), cutoff))
    c = self.conn.cursor()
    c.execute('SELECT name FROM edsm_cache WHERE api=? AND endpoint=? AND timestamp >= ? AND name in {}'.format(self._name_params(names)), [api, endpoint, cutoff] + names)
    for row in c.fetchall():
      yield row[0]

  def _generate_cache_names(self, api, endpoint, names):
    now = int(time.time())
    for name in names:
      yield (api, endpoint, name, now)

  def filter_names(self, names):
    return [name.lower() for name in names if name not in [None, '*']]

  def cache(self, api, endpoint, names):
    if self.conn is None:
      return
    log.debug('Caching result of {}'.format((api, endpoint, str(names))))
    c = self.conn.cursor()
    c.executemany('REPLACE INTO edsm_cache VALUES (NULL, ?, ?, ?, ?)', self._generate_cache_names(api, endpoint, names))
    self.conn.commit()

  def excluding_cached(self, api, endpoint, names):
    cached = set(self._cached(api, endpoint, names))
    log.debug('Requested: {}', ', '.join(names))
    log.debug('Found in cache: {}', ', '.join(cached))
    return list(set(names) - set(cached))

  def get(self, api, endpoint, args = None):
    try:
      uri = '/'.join(['', api, endpoint])
      url = self.HOST + uri
      if args is not None:
        url += '?' + '&'.join(args)
      log.debug('EDSM query: {}'.format(url))
      return json.loads(util.read_from_url(url, allow_gzip = True))
    except Exception:
      log.exception(url)
      return None

  def get_systems(self, names, **kwargs):
    api, endpoint = ('api-v1', 'systems')
    uncached = self.excluding_cached(api, endpoint, names)
    if len(names) and not len(uncached):
      raise EDSMCacheHit
    args = map(lambda name: util.urlencode({ 'systemName[]': name }), uncached)
    args += ['onlyKnownCoordinates=1'] + self.STANDARD_ARGS
    result = self.get(api, endpoint, args)
    if result is not None:
      self.cache(api, endpoint, uncached)
    return result

  def get_system(self, name, **kwargs):
    return self.get_systems([name], **kwargs)

  def sphere_systems(self, system, **kwargs):
    api, endpoint = ('api-v1', 'sphere-systems')
    args = self.STANDARD_ARGS
    if type(system) == vector3.Vector3:
      args += [
        'x={}'.format(system.x),
        'y={}'.format(system.y),
        'z={}'.format(system.z)
      ]
    else:
      args += [util.urlencode({ 'systemName': system })]
    if kwargs.get('radius'):
      args += ['radius={}'.format(kwargs['radius'])]
    if kwargs.get('inner'):
      args += ['minRadius={}'.format(kwargs['inner'])]
    uncached = ['&'.join(sorted(args))]
    if not len(self.excluding_cached(api, endpoint, uncached)):
      raise EDSMCacheHit
    result = self.get(api, endpoint, args)
    if result is not None:
      self.cache(api, endpoint, uncached)
    return result

  def get_stations_in_system(self, system, names = None, id = None):
    api, endpoint = ('api-system-v1', 'stations')
    uncached = self.excluding_cached(api, endpoint, [system])
    if not len(uncached):
      raise EDSMCacheHit
    args = [util.urlencode({ 'systemName': system })]
    if id is not None:
      args.append(util.urlencode({ 'systemId': id }))
    result = self.get(api, endpoint, args)
    if result is not None:
      self.cache(api, endpoint, args)
    stations = [station for station in result.get('stations', []) if names is None or station.get('name') in names]
    for station in stations:
      station['system'] = { k: result.get(k) for k in result.keys() if k != 'stations' }
    return stations

  def get_station_in_system(self, system, name, id = None):
    return self.get_stations_in_system(system, [name], id)
