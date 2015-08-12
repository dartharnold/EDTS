from vector3 import Vector3

class Station:
  def __init__(self, sysobj, ls, stationname, stationtype, fuel, padsize):
    self.distance = ls
    self.system = sysobj
    self.name = stationname
    self.station_type = stationtype
    self.has_fuel = fuel
    self.max_pad_size = padsize

  @property
  def position(self):
    return self.system.position

  @property
  def needs_permit(self):
    return self.system.needs_permit

  @property
  def system_name(self):
    return self.system.name

  def to_string(self):
    return "%s, %s (%dLs, %s)" % (self.system_name, self.name, self.distance, self.station_type)

  def __eq__(self, other):
    if isinstance(other, Station):
      return (self.system == other.system and self.name == other.name)
    else:
      return NotImplemented

  def __hash__(self):
    return "{0}/{1}".format(self.system_name, self.name).__hash__()

