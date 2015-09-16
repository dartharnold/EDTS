from vector3 import Vector3

class Station:
  def __init__(self, sysobj, ls, stationname, stationtype, fuel, padsize):
    self.distance = ls
    self.uses_sc = True
    self.system = sysobj
    self.name = stationname
    self.station_type = stationtype
    self.has_fuel = fuel
    self.max_pad_size = padsize

  @classmethod
  def none(self, sysobj):
    return self(sysobj, 0, None, None, False, 'L')

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
    if self.name is None:
      return self.system_name
    return u"{0}, {1} ({2}Ls, {3})".format(self.system_name, self.name, self.distance if self.distance != None else "???", self.station_type if self.station_type != None else "???")

  def __eq__(self, other):
    if isinstance(other, Station):
      return (self.system == other.system and self.name == other.name)
    else:
      return NotImplemented

  def __hash__(self):
    return u"{0}/{1}".format(self.system_name, self.name).__hash__()

