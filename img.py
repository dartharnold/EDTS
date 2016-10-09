#!/usr/bin/env python

from __future__ import print_function, division
from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image
from wand.display import display
import env
import os
import pgdata
import pgnames
import sys
import vector3 as v3


def convcolour(tup):
  return 'rgb({0},{1},{2})'.format(*[int(t) for t in tup[0:3]])

def lerpn(tup1, tup2, pos):
  output = []
  for i in range(0, min(len(tup1), len(tup2))):
    output.append(tup1[i] + (tup2[i] - tup1[i])*pos)
  return output

_default_centre = v3.Vector3(0, 0, 25000)
_default_width_ly = 90000
_default_height_ly = 90000
_default_min_ly_per_px = 50.0

permit_sectors = ["Bleia1", "Bleia2", "Bleia3", "Bleia4", "Bleia5",
                  "Praei1", "Praei2", "Praei3", "Praei4", "Praei5", "Praei6",
                  "Bovomit", "Hyponia", "Froadik", "Dryman", "Sidgoir", 
                  "Col 70 Sector", "IC 4673 Sector", "Regor Sector", "Barnard's Loop Sector",
                  "Horsehead Dark Sector", "Col 121 Sector", "M41 Sector", "NGC 2264 Sector", 
                  "Col 97 Sector", "NGC 1647 Sector", "NGC 2286 Sector", "NGC 3603 Sector", 
                  ]


class Context(object):
  def __init__(self, width_px, height_px, min_ly_per_px = _default_min_ly_per_px):
    self.width_px = width_px
    self.height_px = height_px
    self.width_ly = _default_width_ly
    self.height_ly = _default_height_ly
    self.min_ly_per_px = min_ly_per_px
    self.colour_pt0    = [195, 105,   0, 1.0]
    self.colour_pt1    = [255, 165,   0, 1.0]
    self.colour_max    = [255, 255, 255, 1.0]
    self.colour_hasect = [ 64, 224, 160, 0.5]
    self.colour_permit = [224,   0,   0, 0.5]
    self.ec_opacity = 0.1
    self.ec_opacity_divisor = 4
    self.ec_opacity_limit = 0.5
    self.ylimit = 1000
    self.centre = _default_centre

  @property
  def px_scale(self):
    px = 1
    while min(px * ctx.width_ly/ctx.width_px, px * ctx.height_ly/ctx.height_px) < ctx.min_ly_per_px:
      px *= 2
    return px
    

def get_image(filename):
  if filename is None:
    return Image(width=1, height=1, background=Color('black'))
  else:
    return Image(filename=filename)
    

def mean(a):
    return sum(a) / len(a)

def count_around(imgdata, x, y):
  ec = 0
  cpos = []
  if x > 0:
    if y > 0 and imgdata[y-1][x-1]:
      ec += imgdata[y-1][x-1][1]
      cpos.append(imgdata[y-1][x-1][0])
    if imgdata[y][x-1]:
      ec += imgdata[y][x-1][1]
      cpos.append(imgdata[y][x-1][0])
    if y+1 < len(imgdata) and imgdata[y+1][x-1]:
      ec += imgdata[y+1][x-1][1]
      cpos.append(imgdata[y+1][x-1][0])
  if y > 0 and imgdata[y-1][x]:
    ec += imgdata[y-1][x][1]
    cpos.append(imgdata[y-1][x][0])
  if y+1 < len(imgdata) and imgdata[y+1][x]:
    ec += imgdata[y+1][x][1]
    cpos.append(imgdata[y+1][x][0])
  if x+1 < len(imgdata[y]):
    if y > 0 and imgdata[y-1][x+1]:
      ec += imgdata[y-1][x+1][1]
      cpos.append(imgdata[y-1][x+1][0])
    if imgdata[y][x+1]:
      ec += imgdata[y][x+1][1]
      cpos.append(imgdata[y][x+1][0])
    if y+1 < len(imgdata) and imgdata[y+1][x+1]:
      ec += imgdata[y+1][x+1][1]
      cpos.append(imgdata[y+1][x+1][0])
  cp = sum(cpos) / len(cpos) if any(cpos) else 0.5
  return (cp, ec)

def make_colour_data(ctx):
  ecdata  = [[None] * (ctx.width_px // ctx.px_scale) for i in range(0, (ctx.height_px // ctx.px_scale))]
  imgdata = [[None] * (ctx.width_px // ctx.px_scale) for i in range(0, (ctx.height_px // ctx.px_scale))]
  with env.use() as data:
    for s in data.get_all_systems():
      pos = s.position
      yrel = (max(-1.0, min((pos.y / ctx.ylimit) + 1.0, 1.0)) + 1.0) / 2.0
      coord_x = int( (pos.x - ctx.centre.x) * (ctx.width_px // ctx.px_scale) / ctx.width_ly + ((ctx.width_px / 2) // ctx.px_scale))
      coord_y = int(-(pos.z - ctx.centre.z) * (ctx.height_px // ctx.px_scale) / ctx.height_ly + ((ctx.height_px / 2) // ctx.px_scale))
      if imgdata[coord_y][coord_x] is None:
        imgdata[coord_y][coord_x] = [yrel, 0]
      elif imgdata[coord_y][coord_x][0] < yrel:
        imgdata[coord_y][coord_x][0] = yrel
      imgdata[coord_y][coord_x][1] += 1
  for y in range(0, (ctx.height_px // ctx.px_scale)):
    for x in range(0, (ctx.width_px // ctx.px_scale)):
      if imgdata[y][x] is None:
        ec_cpos, ec = count_around(imgdata, x, y)
        if ec > 0:
          ec_cval = lerpn(ctx.colour_pt0, ctx.colour_pt1, abs(ec_cpos))
          ecdata[y][x] = [min(255, c) for c in ec_cval[0:3]] + [min(ctx.ec_opacity_limit, ctx.ec_opacity * ec / ctx.ec_opacity_divisor)]
  for y in range(0, (ctx.height_px // ctx.px_scale)):
    for x in range(0, (ctx.width_px // ctx.px_scale)):
      if imgdata[y][x] is not None:
        yrel, count = imgdata[y][x]
        cval = lerpn(ctx.colour_pt0, ctx.colour_pt1, abs(yrel))
        imgdata[y][x] = [min(255, c + (count-1)) for c in cval]
  return (imgdata, ecdata)

def make_ha_data(ctx):
  hadata = []
  for s in pgdata.ha_sectors.values():
    cval = ctx.colour_permit if s.name in permit_sectors else ctx.colour_hasect
    # Don't care about px scale here, this should be image-space coords
    coord_x = int( (s.centre.x - ctx.centre.x) * ctx.width_px / ctx.width_ly + (ctx.width_px / 2))
    coord_y = int(-(s.centre.z - ctx.centre.z) * ctx.height_px / ctx.height_ly + (ctx.height_px / 2))
    radius = s.radius * ctx.width_px / ctx.width_ly
    hadata.append((coord_x, coord_y, radius, cval))
  return hadata

def make_image(ctx, imgdata, filename, bg_img=None, ha_data=None, ec_data=None):
  with Drawing() as draw:
    with get_image(bg_img) as img:
      img.resize(ctx.width_px, ctx.height_px)
      # Draw lines - make this optional/different one day?
      draw.fill_color = Color('#888')
      draw.fill_opacity = 0.5
      draw.line((0,img.size[1]/2), (img.size[0], img.size[1]/2))
      draw.line((img.size[0]/2,0), (img.size[0]/2, img.size[1]))
      draw(img)
      if ha_data and len(ha_data):
        for d in ha_data:
          draw.fill_color = Color(convcolour(d[3]))
          draw.fill_opacity = d[3][3]
          draw.circle((d[0], d[1]), (d[0] + d[2], d[1]))
      for y in range(0, ctx.height_px // ctx.px_scale):
        for x in range(0, ctx.width_px // ctx.px_scale):
          if imgdata[y][x] is not None:
            draw.fill_color = Color(convcolour(imgdata[y][x]))
            draw.fill_opacity = 1.0
            for dy in range(0, ctx.px_scale):
              for dx in range(0, ctx.px_scale):
                draw.point(x * ctx.px_scale + dx, y * ctx.px_scale + dy)
          elif ec_data and ec_data[y][x]:
            draw.fill_color = Color(convcolour(ec_data[y][x]))
            draw.fill_opacity = ec_data[y][x][3]
            for dy in range(0, ctx.px_scale):
              for dx in range(0, ctx.px_scale):
                draw.point(x * ctx.px_scale + dx, y * ctx.px_scale + dy)
      draw(img)
      img.save(filename=filename)

if __name__ == '__main__':
  width_px = int(sys.argv[1]) if len(sys.argv) >= 2 else 1500
  height_px = int(sys.argv[2]) if len(sys.argv) >= 3 else width_px
  ctx = Context(width_px, height_px)
  print("Output at {0}x{1}, {2}px = {3:.1f}Ly".format(ctx.width_px, ctx.height_px, ctx.px_scale, ctx.px_scale * ctx.width_ly/ctx.width_px))
  print("Getting colour data")
  imgdata, ecdata = make_colour_data(ctx)
  print("Getting HA data")
  hadata = make_ha_data(ctx)
  print("Writing map to map-b0.png")
  make_image(ctx, imgdata, 'map-b0.png', None, ha_data=hadata, ec_data=ecdata)
  if os.path.isfile('edgalaxy.png'):
    print("Writing map to map-b1.png")
    make_image(ctx, imgdata, 'map-b1.png', 'edgalaxy.png', ha_data=hadata, ec_data=ecdata)
  else:
    print("No edgalaxy.png found, skipping map with background")
  print("Done")
