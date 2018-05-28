import json

from .dist import Lightyears

class OpaqEncoder(json.JSONEncoder):
  def default(self, obj):
    try:
      return obj.to_opaq()
    except Exception as e:
      return "Don't know how to serialise {}: {}".format(type(obj), e)

class Opaq(object):
  def __repr__(self):
    return str(vars(self))

  def to_opaq(self):
    return vars(self)

class Fuel(Opaq):
  def __init__(self, **args):
    for attr in ['min', 'max', 'initial', 'cost', 'final']:
      setattr(self, attr, args.get(attr, 0.0))

class Refuel(Opaq):
  def __init__(self, **args):
    self.amount = args.get('amount', 0.0)
    self.percent = args.get('percent', 0)

class Jumps(Opaq):
  def __init__(self, **args):
    self.min = args.get('min', 1)
    self.max = args.get('max', 1)

class Location(Opaq):
  def __init__(self, **args):
    self.system = args.get('system')
    self.station = args.get('station')

class WaypointTime(Opaq):
  def __init__(self, **args):
    self.accurate = args.get('accurate', True)
    self.cruise = args.get('cruise', 0)
    self.jumps = args.get('jumps', Jumps(min = 0, max = 0))

class Waypoint(Opaq):
  def __init__(self, **args):
    self.distance = args.get('distance', Lightyears(0))
    self.direct = args.get('direct', self.distance)
    self.jumps = args.get('jumps', Jumps())
    self.time = args.get('time', WaypointTime())

  def to_opaq(self):
    return vars(self)
