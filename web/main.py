#!/usr/bin/env python

import sys
import bottle
import json
import collections

sys.path.insert(0, '..')
import pgnames
import pgdata
import sector
import vector3
del sys.path[0]


def vec3_to_dict(v):
  return collections.OrderedDict([('x', v.x), ('y', v.y), ('z', v.z)])


@bottle.hook('before_request')
def strip_path():
  bottle.request.environ['PATH_INFO'] = bottle.request.environ['PATH_INFO'].rstrip('/')


@bottle.route('/')
def index():
  return '<html><head><title>EDTSweb</title></head><body><a href="/api">API docs</a></body></html>'


@bottle.route('/api')
def api_index():
  return bottle.template('api_index')


@bottle.route('/api/system_name/<x:float>,<y:float>,<z:float>/<mcode:re:[a-h]>')
def api_system_name(x, y, z, mcode):
  sect = api_sector_name(x, y, z)
  pos = vector3.Vector3(x, y, z)

  psect = pgnames.get_sector(pos, allow_ha=True)
  psorig = psect.get_origin(pgnames.get_mcode_cube_width(mcode))
  relpos = vector3.Vector3(x - psorig.x, y - psorig.y, z - psorig.z)
  sysid = pgnames.get_sysid_from_relpos(relpos, mcode, format_output=True)

  if sect['result'] is not None and any(sect['result']['names']):
    for n in sect['result']['names']:
      n['name'] = '{} {}'.format(n['name'], sysid)
    result = sect
  else:
    bottle.response.status = 400
    result = None
  bottle.response.content_type = 'application/json'
  return {'result': result}


@bottle.route('/api/sector_name/<x:float>,<y:float>,<z:float>')
def api_sector_name(x, y, z):
  v = vector3.Vector3(x, y, z)
  result = None
  ha_name = pgnames.ha_get_name(v)
  if ha_name is not None:
    result = {'names': [{'name': ha_name, 'type': 'ha'}], 'position': vec3_to_dict(vector3.Vector3(x, y, z))}
  else:
    c1_name = pgnames.format_name(pgnames.c1_get_name(v))
    c2_name = pgnames.format_name(pgnames.c2_get_name(v))
    if c1_name is not None and c2_name is not None:
      result = {'names': [{'name': c1_name, 'type': 'c1'}, {'name': c2_name, 'type': 'c2'}], 'position': vec3_to_dict(vector3.Vector3(x, y, z))}
    else:
      bottle.response.status = 400
      result = None
  bottle.response.content_type = 'application/json'
  return {'result': result}


@bottle.route('/api/system_position/<name>')
def api_system_position(name):
  pos, err = pgnames.get_coords_from_name(name)
  if pos is not None and err is not None:
    result = {'name': name, 'position': vec3_to_dict(pos), 'uncertainty': err}
  else:
    bottle.response.status = 400
    result = None
  bottle.response.content_type = 'application/json'
  return {'result': result}


@bottle.route('/api/sector_position/<name>')
def api_sector_position(name):
  sect = pgnames.get_sector_from_name(name)
  if sect is not None:
    if isinstance(sect, sector.HASector):
      result = {'name': name, 'type': 'ha', 'centre': vec3_to_dict(sect.centre), 'radius': sect.radius}
    else:
      result = {'name': name, 'type': 'pg', 'origin': vec3_to_dict(sect.origin), 'centre': vec3_to_dict(sect.centre), 'size': sect.size}
  else:
    bottle.response.status = 400
    result = None
  bottle.response.content_type = 'application/json'
  return {'result': result}


if __name__ == '__main__':
  bottle.run(host='localhost', port=8080)
