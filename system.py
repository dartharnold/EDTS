from vector3 import Vector3

class System:
  def __init__(self, obj):
    self.id = obj['id']
    self.position = Vector3(float(obj['x']), float(obj['y']), float(obj['z']))
    self.name = obj['name']
    self.needs_permit = obj['needs_permit']
    self.allegiance = obj['allegiance']
    self.uses_sc = False

  def to_string(self, use_long = False):
    if use_long:
      return u"%s (%.2f, %.2f, %.2f)" % (self.name, self.position.x, self.position.y, self.position.z)
    else:
      return u"%s" % self.name

  def __eq__(self, other):
    if isinstance(other, System):
      return (self.id == other.id and self.name == other.name and self.position == other.position)
    else:
      return NotImplemented

  def __hash__(self):
    return u"{0}/{1},{2},{3}".format(self.name,self.position.x,self.position.y,self.position.z).__hash__()

