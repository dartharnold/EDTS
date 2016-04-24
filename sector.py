import vector3

base_coords = vector3.Vector3(-65.0, -25.0, 215.0)
cube_size = 1280.0
base_sector_coords   = [39, 8, 19]
# Galaxy actually goes from [-49985, -40985, -24105] = [-39, -32, -19]

class Sector(object):
  __slots__ = ('_v','name')

  def __init__(self, x, y, z, name = None):
    self._v = [int(x), int(y), int(z)]
    self.name = name

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
    return "Sector({0}, {1}, {2})".format(x, y, z)

  def __repr__(self):
    x, y, z = self._v
    return "Sector({0}, {1}, {2})".format(x, y, z)

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
    x, y, z = self._v
    xx, yy, zz = rhs

  @property
  def origin(self):
    ox = base_coords.x + (cube_size * self.x)
    oy = base_coords.y + (cube_size * self.y)
    oz = base_coords.z + (cube_size * self.z)
    return vector3.Vector3(ox, oy, oz)

  def contains(self, pos):
    o = self.origin
    return (pos[0] >= o.x and pos[0] < (o.x + cube_size)
        and pos[1] >= o.y and pos[1] < (o.y + cube_size)
        and pos[2] >= o.z and pos[2] < (o.z + cube_size))

