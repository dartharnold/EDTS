from vector3 import Vector3

class Station:
  def __init__(self, x, y, z, ls, sysname, stationname, stationtype, permit, fuel, padsize):
    self.position = Vector3(x, y, z)
    self.distance = ls
    self.system = sysname
    self.name = stationname
    self.station_type = stationtype
    self.needs_permit = permit
    self.has_fuel = fuel
    self.max_pad_size = padsize

  def to_string(self):
    return "%s, %s (%dLs, %s)" % (self.system, self.name, self.distance, self.station_type)

  def __eq__(self, other):
    if isinstance(other, Station):
      return (self.system == other.system and self.name == other.name)
    else:
      return NotImplemented

  def __hash__(self):
    return "{0}/{1}".format(self.system, self.name).__hash__()

