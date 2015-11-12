from vector3 import Vector3

class System:
  def __init__(self, x, y, z, sysname, permit):
    self.position = Vector3(x, y, z)
    self.uses_sc = False
    self.name = sysname
    self.needs_permit = permit

  def to_string(self, use_long = False):
    if use_long:
      return u"%s (%.2f, %.2f, %.2f)" % (self.name, self.position.x, self.position.y, self.position.z)
    else:
      return u"%s" % self.name

  def __eq__(self, other):
    if isinstance(other, System):
      return (self.name == other.name and self.position == other.position)
    else:
      return NotImplemented

  def __hash__(self):
    return u"{0}/{1},{2},{3}".format(self.name,self.position.x,self.position.y,self.position.z).__hash__()

