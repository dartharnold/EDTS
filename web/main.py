#!/usr/bin/env python

import sys
import json
import collections

data_path = '..'

sys.path.insert(1, data_path)
import thirdparty.bottle as bottle
import env
import fsd
import pgnames
import pgdata
import sector
import system
import vector3
del sys.path[1]


def vec3_to_dict(v):
  return collections.OrderedDict([('x', v.x), ('y', v.y), ('z', v.z)])


@bottle.hook('before_request')
def strip_path():
  bottle.request.environ['PATH_INFO'] = bottle.request.environ['PATH_INFO'].rstrip('/')


@bottle.route('/')
def index():
  return bottle.template('index')


@bottle.route('/jump_range')
def jump_range():
  return bottle.template('jump_range')


@bottle.route('/api/v1')
def api_index():
  return bottle.template('api_v1_index')


@bottle.route('/static/<path:path>')
def static(path):
  return bottle.static_file(path, root='static')


@bottle.route('/api/v1/jump_range/<fsdcls:re:[0-9][A-E]>,<mass:float>,<fuel:float>,<cargo:int>,<optmod:re:[-+0-9.]+%?>,<maxfmod:re:[-+0-9.]+%?>,<massmod:re:[-+0-9.]+%?>')
def api_jump_range(fsdcls, mass, fuel, cargo, optmod, maxfmod, massmod):
  f = fsd.FSD(fsdcls)
  # Check values make sense
  f.optmass = (f.optmass * (1.0+float(optmod[:-1])/100.0) if '%' in optmod else float(optmod))
  f.maxfuel = (f.maxfuel * (1.0+float(maxfmod[:-1])/100.0) if '%' in maxfmod else float(maxfmod))
  
  fsdmass = (f.mass * (1.0+float(massmod[:-1])/100.0) if '%' in massmod else float(massmod))
  shipmass = mass + (fsdmass - f.mass)
  
  max_range = f.max_range(shipmass)
  full_range = f.range(shipmass, fuel)
  cargo_range = f.range(shipmass, fuel, cargo)

  result = {'max': max_range, 'full': full_range, 'laden': cargo_range}

  bottle.response.content_type = 'application/json'
  return {'result': result}

@bottle.route('/api/v1/system_name/<x:float>,<y:float>,<z:float>/<mcode:re:[a-h]>')
def api_system_name(x, y, z, mcode):
  pos = vector3.Vector3(x, y, z)
  syst = pgnames.get_system(pos, mcode)
  result = {'position': vec3_to_dict(pos), 'names': []}

  if syst is not None:
    result['names'] += [{'name': syst.name, 'type': syst.sector.sector_class}]
  else:
    bottle.response.status = 400
    result = None
  bottle.response.content_type = 'application/json'
  return {'result': result}


@bottle.route('/api/v1/sector_name/<x:float>,<y:float>,<z:float>')
def api_sector_name(x, y, z):
  v = vector3.Vector3(x, y, z)
  result = {'names': [], 'position': vec3_to_dict(v)}
  sect = pgnames.get_sector(v, allow_ha=True)
  if sect is not None and isinstance(sect, sector.HASector):
    result['names'].append({'name': sect.name, 'type': sect.sector_class})
    sect = pgnames.get_sector(v, allow_ha=False)
  if sect is not None:
    result['names'] += [{'name': sect.name, 'type': sect.sector_class}]
  if not any(result['names']):
    bottle.response.status = 400
    result = None
  bottle.response.content_type = 'application/json'
  return {'result': result}


@bottle.route('/api/v1/system_position/<name>')
def api_system_position(name):
  syst = pgnames.get_system(name)
  if syst is not None:
    result = {'name': pgnames.get_canonical_name(name), 'position': vec3_to_dict(syst.position), 'uncertainty': syst.uncertainty}
  else:
    bottle.response.status = 400
    result = None
  bottle.response.content_type = 'application/json'
  return {'result': result}


@bottle.route('/api/v1/sector_position/<name>')
def api_sector_position(name):
  sect = pgnames.get_sector(name)
  if sect is not None:
    if isinstance(sect, sector.HASector):
      result = {'name': pgnames.get_canonical_name(name), 'type': 'ha', 'centre': vec3_to_dict(sect.centre), 'radius': sect.radius}
    else:
      result = {'name': pgnames.get_canonical_name(name), 'type': 'pg', 'origin': vec3_to_dict(sect.origin), 'centre': vec3_to_dict(sect.centre), 'size': sect.size}
  else:
    bottle.response.status = 400
    result = None
  bottle.response.content_type = 'application/json'
  return {'result': result}

@bottle.route('/api/v1/system/<name>')
def api_system(name):
  with env.use(data_path) as data:
    syst = data.get_system(name, keep_data=True)
    if syst is not None:
      result = syst.data
    else:
      bottle.response.status = 400
      result = None
  bottle.response.content_type = 'application/json'
  return {'result': result}

@bottle.route('/api/v2/system/<id64:int>')
def api_v2_system_id64(id64):
  syst = system.from_id64(id64)
  return api_v2_system_name(syst.name)

@bottle.route('/api/v2/system/<name>')
def api_v2_system_name(name):
  syst = system.from_name(name)
  if syst is not None:
    result = collections.OrderedDict([('name', syst.name), ('x', syst.position.x), ('y', syst.position.y), ('z', syst.position.z),
              ('uncertainty', syst.uncertainty), ('pg_name', syst.pg_name), ('id64', syst.id64)])
  else:
    bottle.response.status = 400
    result = None
  bottle.response.content_type = 'application/json'
  return {'result': result}

@bottle.route('/api/v1/system/<name>/stations')
def api_system_stations(name):
  result = []
  with env.use(data_path) as data:
    syst = data.get_system(name, keep_data=True)
    if syst is not None:
      for stat in data.get_stations(syst, keep_station_data=True):
        if stat is not None:
          result.append(stat.data)
  if not len(result):
    result = None
  bottle.response.content_type = 'application/json'
  return {'result': result}

@bottle.route('/api/v1/system/<system_name>/station/<station_name>')
def api_system_station(system_name, station_name):
  with env.use(data_path) as data:
    stat = data.get_station(system_name, station_name, keep_data=True)
    if stat is not None:
      result = stat.data
      result['system'] = stat.system.data
    else:
      result = None
    bottle.response.content_type = 'application/json'
    return {'result': result}

@bottle.route('/api/v1/find_system/<glob>')
def api_find_system(glob):
  result = []
  with env.use(data_path) as data:
    for syst in data.find_systems_by_glob(glob, keep_data=True):
      if syst is not None:
        result.append(syst.data)
  if not len(result):
    result = None
  bottle.response.content_type = 'application/json'
  return {'result': result}

@bottle.route('/api/v1/find_station/<glob>')
def api_find_station(glob):
  result = []
  with env.use(data_path) as data:
    for stat in data.find_stations_by_glob(glob, keep_data=True):
      if stat is not None:
        stndata = stat.data
        stndata['system'] = stat.system.data
        result.append(stndata)
  if not len(result):
    result = None
  bottle.response.content_type = 'application/json'
  return {'result': result}

if __name__ == '__main__':
  port = 8080
  if len(sys.argv) > 1:
    port = int(sys.argv[1])

  env.start(data_path)
  bottle.run(host='localhost', port=port)
  env.stop(data_path)
