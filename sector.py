import math
import vector3

cube_size = 1280.0
# Sector at (0,0,0) is Wregoe, the sector containing Sol
base_coords = vector3.Vector3(-65.0, -25.0, 215.0 - 1280.0)
base_sector_coords = [39, 8, 18]
# Galaxy actually goes from [-49985, -40985, -24105] = [-39, -32, -18]

class Sector(object):
  def __init__(self, name):
    self.name = name

  def contains(self, other):
    raise NotImplementedError("Invalid call to base Sector contains method")


class HASector(Sector):
  def __init__(self, centre, radius, name = None):
    super(HASector, self).__init__(name)
    self._centre = centre
    self._radius = radius

  def origin(self, cube_width):
    sector_origin = self.centre - vector3.Vector3(self.radius, self.radius, self.radius)
    sox = math.floor(sector_origin.x)
    soy = math.floor(sector_origin.y)
    soz = math.floor(sector_origin.z)
    sox -= (sox - int(base_coords.x)) % cube_width
    soy -= (soy - int(base_coords.y)) % cube_width
    soz -= (soz - int(base_coords.z)) % cube_width
    return vector3.Vector3(float(sox), float(soy), float(soz))

  @property
  def centre(self):
    return self._centre

  @property
  def radius(self):
    return self._radius

  def contains(self, pos):
    return ((self.centre - pos).length <= self.radius)
  
  def __str__(self):
    return "HASector({})".format(self.name)

  def __repr__(self):
    return self.__str__()

  def __eq__(self, rhs):
    return (self.centre == rhs.centre and self.radius == other.radius)

  def __ne__(self, rhs):
    return not self.__eq__(rhs)


class PGSector(Sector):
  __slots__ = ('_v','name')

  def __init__(self, x, y, z, name = None):
    super(PGSector, self).__init__(name)
    self._v = [int(x), int(y), int(z)]

  @property
  def x(self):
    return self._v[0]

  @property
  def y(self):
    return self._v[1]

  @property
  def z(self):
    return self._v[2]

  def __str__(self):
    x, y, z = self._v
    if self.name is not None:
      return "PGSector({} @ {}, {}, {})".format(self.name, x, y, z)
    else:
      return "PGSector({}, {}, {})".format(x, y, z)

  def __repr__(self):
    return self.__str__()

  def __len__(self):
    return 3

  def __iter__(self):
    return iter(self._v)

  def __getitem__(self, index):
    try:
      return self._v[index]
    except IndexError:
      raise IndexError("There are 3 values in this object, index should be 0, 1 or 2!")
    
  def __eq__(self, rhs):
    x, y, z = self._v
    xx, yy, zz = rhs
    return (x == xx and y == yy and z == zz)

  def __ne__(self, rhs):
    return not self.__eq__(rhs)

  @property
  def origin(self):
    ox = base_coords.x + (cube_size * self.x)
    oy = base_coords.y + (cube_size * self.y)
    oz = base_coords.z + (cube_size * self.z)
    return vector3.Vector3(ox, oy, oz)
  
  @property
  def index(self):
    return [self.x + base_sector_coords[0], self.y + base_sector_coords[1], self.z + base_sector_coords[2]]

  def contains(self, pos):
    o = self.origin
    return (pos[0] >= o.x and pos[0] < (o.x + cube_size)
        and pos[1] >= o.y and pos[1] < (o.y + cube_size)
        and pos[2] >= o.z and pos[2] < (o.z + cube_size))

