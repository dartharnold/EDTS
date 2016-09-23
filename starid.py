import pgnames
import sector
import system
import util
import vector3


_max_int64  = 0xFFFFFFFFFFFFFFFF
_mask_mcode = 0x0000000000000007


def _calculate(input):
  # If input is a string, assume hex
  if util.is_str(input):
    input = int(input, 16)
  # Get the mass code from the end of the ID
  mc = (input & _mask_mcode)  # a-h = 0-7
  cube_width = 10 * (2**mc)
  # Calculate the shifts we need to do to get the individual fields out
  # Can't tell how long N2 field is (or if the start moves!), assuming ~16 for now
  shn2 = ( 4 + 3*mc, 20 + 3*mc)
  shxb = (20 + 3*mc, 34 + 2*mc)
  shyb = (34 + 2*mc, 47 +   mc)
  shzb = (47 +   mc, 61       )
  # Perform the shifts (clamping to 64-bit)
  xb = ((input << shxb[0]) & _max_int64) >> (64 + shxb[0] - shxb[1])
  yb = ((input << shyb[0]) & _max_int64) >> (64 + shyb[0] - shyb[1])
  zb = ((input << shzb[0]) & _max_int64) >> (64 + shzb[0] - shzb[1])
  n2 = ((input << shn2[0]) & _max_int64) >> (64 + shn2[0] - shn2[1])
  # Multiply each X/Y/Z value by the cube width to get actual coords
  coords_internal = vector3.Vector3(xb * cube_width, yb * cube_width, zb * cube_width)
  # Shift the coords to be the origin we know and love
  coords = coords_internal + sector.internal_origin_coords
  return (coords, cube_width, n2)


def get_system_from_starid(id, allow_ha = True):
  coords, cube_width, n2 = _calculate(id)
  # Get a system prototype to steal its name
  sys_proto = pgnames.get_system(coords, cube_width, allow_ha)
  name = sys_proto.name + str(n2)
  x, y, z = sys_proto.position
  return system.PGSystem(x, y, z, name, sys_proto.sector, sys_proto.uncertainty)
