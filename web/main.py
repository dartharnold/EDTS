#!/usr/bin/env python
from __future__ import print_function, division
from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image
from wand.display import display
import io

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


@bottle.route('/img')
def img_index():
  return bottle.template('img')


_default_centre = vector3.Vector3(0, 0, 25000)
_px_scale = 1.0
_width_ly = 90000
_height_ly = 90000
_circle_radius = 7
_font_size = 16
_font_name = 'DejaVu Sans Mono'
_color = 'rgb(0,64,255)'

@bottle.route('/mkimg/<systems>')
def img_make(systems):
  sl = list(systems.split(','))
  with env.use() as data:
    syslist = data.get_systems_by_name(sl)
  for i,s in syslist.items():
    if s is None:
      syslist[i] = system.from_name(i)

  cnt = 0
  output = io.BytesIO()
  with Drawing() as draw:
    with Image(filename='edgalaxy_1500.png') as img:
      width_px = img.width
      height_px = img.height
      color = Color(_color)
      black = Color('#000')
      white = Color('#fff')
      # Draw lines - make this optional/different one day?
      draw.fill_color = Color('#888')
      draw.fill_opacity = 0.5
      draw.line((0,img.size[1]/2), (img.size[0], img.size[1]/2))
      draw.line((img.size[0]/2,0), (img.size[0]/2, img.size[1]))
      draw(img)
      draw.fill_color = color
      draw.font_size = _font_size
      draw.font_family = _font_name
      draw.font_weight = 900
      draw.stroke_color = Color('#000')
      draw.stroke_opacity = 0.75
      draw.stroke_width = 1.0
      text_offset_x = _circle_radius * 1.5
      text_offset_y = _circle_radius * 0.8
      for s in sorted([t for t in syslist.values() if t is not None], key=lambda t: t.position.x):
        draw.text_alignment = 'left' if (cnt % 2) == 0 else 'right'
        pos = s.position
        coord_x = int( (pos.x - _default_centre.x) * (width_px // _px_scale) / _width_ly + ((width_px / 2) // _px_scale))
        coord_y = int(-(pos.z - _default_centre.z) * (height_px // _px_scale) / _height_ly + ((height_px / 2) // _px_scale))
        draw.stroke_opacity = 1.0
        draw.stroke_color = color
        draw.stroke_width = int(_circle_radius // 2.0)
        draw.fill_opacity = 0.0
        draw.fill_color = color
        draw.circle((coord_x, coord_y), (coord_x + _circle_radius, coord_y))
        draw.stroke_width = 1.0
        draw.stroke_opacity = 0.75
        draw.stroke_color = black
        draw.fill_opacity = 1.0
        draw.fill_color = white
        draw.text(int(coord_x + text_offset_x), int(coord_y + text_offset_y), s.name)
        text_offset_x = -text_offset_x
        cnt += 1
      draw(img)
      img.save(file=output)
      bottle.response.content_type = 'image/png'
      output.seek(0)
      output_data = output.read()
      return output_data


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
  env.start(data_path)
  bottle.run(host='localhost', port=8099)
  env.stop(data_path)
