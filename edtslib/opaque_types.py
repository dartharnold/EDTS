from .dist import Lightyears

class Fuel(object):
  def __init__(self, **args):
    for attr in ['min', 'max', 'initial', 'cost', 'final']:
      setattr(self, attr, args.get(attr, 0.0))

class Refuel(object):
  def __init__(self, **args):
    self.amount = args.get('amount', 0.0)
    self.percent = args.get('percent', 0)

class Jumps(object):
  def __init__(self, **args):
    self.min = args.get('min', 1)
    self.max = args.get('max', 1)

class Location(object):
  def __init__(self, **args):
    self.system = args.get('system')
    self.station = args.get('station')

class WaypointTime(object):
  def __init__(self, **args):
    self.accurate = args.get('accurate', True)
    self.cruise = args.get('cruise', 0)
    self.jumps = args.get('jumps', Jumps(min = 0, max = 0))

class Waypoint(object):
  def __init__(self, **args):
    self.distance = args.get('distance', Lightyears(0))
    self.direct = args.get('direct', self.distance)
    self.jumps = args.get('jumps', Jumps())
    self.time = args.get('time', WaypointTime())
