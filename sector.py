import math
import vector3

cube_size = 1280.0
# Sector at (0,0,0) is Wregoe, the sector containing Sol
# Galaxy actually goes from [-49985, -40985, -24105] = [-39, -32, -18]
base_coords = vector3.Vector3(-65.0, -25.0, 215.0 - 1280.0)
base_sector_coords = [39, 8, 18]
named_origin_coords = base_coords - vector3.Vector3(cube_size * base_sector_coords[0], cube_size*base_sector_coords[1], cube_size*base_sector_coords[2])
internal_origin_coords = vector3.Vector3(-49985, -40985, -24105)


def get_mcode_cube_width(mcode):
  return cube_size / pow(2, ord('h') - ord(mcode.lower()))


class Sector(object):
  def __init__(self, name):
    self.name = name

  @property
  def centre(self):
    raise NotImplementedError("Invalid call to base Sector centre property")

  @property
  def size(self):
    raise NotImplementedError("Invalid call to base Sector size property")

  @property
  def sector_class(self):
    raise NotImplementedError("Invalid call to base Sector sector_class property")

  def contains(self, other):
    raise NotImplementedError("Invalid call to base Sector contains method")

  def get_origin(self, cube_width):
    raise NotImplementedError("Invalid call to base Sector get_origin method")


class HASector(Sector):
  def __init__(self, centre, radius, name = None):
    super(HASector, self).__init__(name)
    self._centre = centre
    self._radius = radius
    self._size = radius

  def get_origin(self, cube_width):
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

  @property
  def size(self):
    return self._size

  @property
  def sector_class(self):
    return 'ha'

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


class HASectorCluster(HASector):
  def __init__(self, centre, radius, size, name, sectors):
    super(HASectorCluster, self).__init__(centre, radius, name)
    self._size = size
    self.sectors = sectors

  def contains(self, pos):
    return any([s.contains(pos) for s in self.sectors])

  def __str__(self):
    return "HASectorCluster({})".format(self.name)

  def __repr__(self):
    return self.__str__()


class PGSector(Sector):
  __slots__ = ('_v','name')

  def __init__(self, x, y, z, name = None, sc = None):
    super(PGSector, self).__init__(name)
    self._v = [int(x), int(y), int(z)]
    self._class = 'c{}'.format(sc)

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
    return self.get_origin()

  def get_origin(self, cube_width = None):
    ox = base_coords.x + (cube_size * self.x)
    oy = base_coords.y + (cube_size * self.y)
    oz = base_coords.z + (cube_size * self.z)
    return vector3.Vector3(ox, oy, oz)
  
  @property
  def centre(self):
    return self.origin + vector3.Vector3(cube_size / 2, cube_size / 2, cube_size / 2)

  @property
  def size(self):
    return cube_size

  @property
  def index(self):
    return [self.x + base_sector_coords[0], self.y + base_sector_coords[1], self.z + base_sector_coords[2]]

  @property
  def sector_class(self):
    return self._class

  def contains(self, pos):
    o = self.origin
    return (pos[0] >= o.x and pos[0] < (o.x + cube_size)
        and pos[1] >= o.y and pos[1] < (o.y + cube_size)
        and pos[2] >= o.z and pos[2] < (o.z + cube_size))

