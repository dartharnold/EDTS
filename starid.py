import pgnames
import sector
import system
import util
import vector3

# mask, e.g. 000002937DFC92DA
_mask_xb = 0x0000003FFC000000
_mask_yb = 0x0000000003FF8000
_mask_zb = 0x0000000000007FF8
_mask_n2 = 0x003FFFC000000000
_mask_mc = 0x0000000000000007


def _calculate(input):
  # If input is a string, assume hex
  if util.is_str(input):
    input = int(input, 16)
  xb = (input & _mask_xb) >> (64-38)
  yb = (input & _mask_yb) >> (64-49)
  zb = (input & _mask_zb) >> (64-61)
  n2 = (input & _mask_n2) >> (64-26)
  mc = (input & _mask_mc) >> (64-64)
  
  mcode = chr(mc + ord('a'))
  cw = sector.get_mcode_cube_width(mcode)
  coords_internal = vector3.Vector3(xb * cw, yb * cw, zb * cw)
  print(coords_internal)
  # Shift the coords to be the origin we know and love
  coords = coords_internal + sector.internal_origin_coords
  
  return (coords, mcode, n2)


def get_system_from_starid(id):
  coords, mcode, n2 = _calculate(id)
  sys_proto = pgnames.get_system(coords, mcode)
  name = sys_proto.name + str(n2)
  x, y, z = sys_proto.position
  return system.PGSystem(x, y, z, name, sys_proto.sector, sys_proto.uncertainty)
