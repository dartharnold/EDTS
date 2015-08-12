from vector3 import Vector3

class System:
  def __init__(self, x, y, z, sysname, permit):
    self.position = Vector3(x, y, z)
    self.name = sysname
    self.needs_permit = permit

  def to_string(self):
    return "%s (%.2f, %.2f, %.2f)" % (self.name, self.position.x, self.position.y, self.position.z)

  def __eq__(self, other):
    if isinstance(other, System):
      return (self.name == other.name and self.position == other.position)
    else:
      return NotImplemented

  def __hash__(self):
    return "{0}/{1},{2},{3}".format(self.name,self.x,self.y,self.z).__hash__()

