from vector3 import Vector3

class Station:
  def __init__(self, obj, sysobj):
    self.distance = obj['distance_to_star'] if obj is not None else None
    self.uses_sc = True if obj is not None else False
    self.system = sysobj
    self.name = obj['name'] if obj is not None else None
    self.station_type = obj['type'] if obj is not None else None
    self.has_fuel = bool(obj['has_refuel']) if obj is not None else False
    self.max_pad_size = obj['max_landing_pad_size'] if obj is not None else 'L'

  @classmethod
  def none(self, sysobj):
    return self(None, sysobj)

  @property
  def position(self):
    return self.system.position

  @property
  def needs_permit(self):
    return self.system.needs_permit
    
  @property
  def system_name(self):
    return self.system.name

  def to_string(self, inc_sys = True):
    if self.name is None:
      return self.system_name
    return u"{0}{1} ({2}Ls, {3})".format((self.system_name + ", ") if inc_sys else "", self.name, self.distance if self.distance != None else "???", self.station_type if self.station_type != None else "???")

  def __eq__(self, other):
    if isinstance(other, Station):
      return (self.system == other.system and self.name == other.name)
    else:
      return NotImplemented

  def __hash__(self):
    return u"{0}/{1}".format(self.system_name, self.name).__hash__()

