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

