import pgnames
import sector
import util
import vector3


class System(object):
  def __init__(self, x, y, z, name = None):
    self.position = vector3.Vector3(float(x), float(y), float(z))
    self.name = name
    self.uses_sc = False
    self.id = None

  @property
  def system_name(self):
    return self.name

  def to_string(self, use_long = False):
    if use_long:
      return u"{0} ({1:.2f}, {2:.2f}, {3:.2f})".format(self.name, self.position.x, self.position.y, self.position.z)
    else:
      return u"{0}".format(self.name)

  def __str__(self):
    return self.to_string()

  def __repr__(self):
    return u"System({})".format(self.name)

  def distance_to(self, other):
    return (self.position - other.position).length

  def __eq__(self, other):
    if isinstance(other, System):
      return (self.name == other.name and self.position == other.position)
    else:
      return NotImplemented

  def __hash__(self):
    return u"{}/{},{},{}".format(self.name, self.position.x, self.position.y, self.position.z).__hash__()


class PGSystemPrototype(System):
  def __init__(self, x, y, z, name, sector, uncertainty):
    super(PGSystemPrototype, self).__init__(x, y, z, name)
    self.uncertainty = uncertainty
    self.sector = sector

  def __repr__(self):
    return u"PGSystemPrototype({})".format(self.name if self.name is not None else '{},{},{}'.format(self.position.x, self.position.y, self.position.z))


class PGSystem(PGSystemPrototype):
  def __init__(self, x, y, z, name, sector, uncertainty):
    super(PGSystem, self).__init__(x, y, z, name, sector, uncertainty)
    self.uncertainty = uncertainty
    self.sector = sector

  def __repr__(self):
    return u"PGSystem({})".format(self.name if self.name is not None else '{},{},{}'.format(self.position.x, self.position.y, self.position.z))


class KnownSystem(System):
  def __init__(self, obj):
    super(KnownSystem, self).__init__(float(obj['x']), float(obj['y']), float(obj['z']), obj['name'])
    self.id = obj['id'] if 'id' in obj else None
    self.needs_permit = obj['needs_permit'] if 'needs_permit' in obj else False
    self.allegiance = obj['allegiance'] if 'allegiance' in obj else None
    self.uses_sc = False

  def __repr__(self):
    return u"KnownSystem({0})".format(self.name)

  def __eq__(self, other):
    if isinstance(other, KnownSystem):
      return ((self.id is None or other.id is None or self.id == other.id) and self.name == other.name and self.position == other.position)
    elif isinstance(other, System):
      return super(KnownSystem, self).__eq__(other)
    else:
      return NotImplemented
  
  def __hash__(self):
    return u"{0}/{1},{2},{3}".format(self.name, self.position.x, self.position.y, self.position.z).__hash__()


    
#
# System ID calculations
#
_max_int64  = 0xFFFFFFFFFFFFFFFF
_mask_mcode = 0x0000000000000007


def _calculate_from_id(input):
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


def from_id(id, allow_ha = True):
  coords, cube_width, n2 = _calculate_from_id(id)
  # Get a system prototype to steal its name
  sys_proto = pgnames.get_system(coords, cube_width, allow_ha)
  name = sys_proto.name + str(n2)
  x, y, z = sys_proto.position
  return PGSystem(x, y, z, name, sys_proto.sector, sys_proto.uncertainty)