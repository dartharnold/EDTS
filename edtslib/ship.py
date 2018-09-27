import json
import sys
from . import util
from .fsd import FSD, InfiniteImprobabilityDrive

log = util.get_logger("ship")


class Ship(object):
  def __init__(self, fsd_info, mass, tank, max_cargo = 0, reserve_tank = 0, range_boost = 0):
    # If we already have an FSD object, just use it as-is; otherwise assume a string and create a FSD object
    self.fsd = fsd_info if isinstance(fsd_info, FSD) else FSD(fsd_info)
    self.mass = mass
    self.tank_size = tank
    self.reserve_tank = reserve_tank if reserve_tank is not None else 0
    self.range_boost = range_boost if range_boost is not None else 0
    self.cargo_capacity = max_cargo

  def clone(self):
    return Ship(self.fsd.clone(), self.mass, self.tank_size, self.cargo_capacity, self.reserve_tank)

  @classmethod
  def from_dict(self, data):
    fsd_info = FSD.from_dict(data)
    if fsd_info is not None:
      try:
        log.debug("Reading ship from Coriolis dump")
        stats = data['stats']
        mass = stats['unladenMass']
        log.debug("Dumped unladenMass: {}", mass)
        tank = stats['fuelCapacity']
        log.debug("Dumped fuelCapacity: {}", tank)
        max_cargo = stats['cargoCapacity']
        log.debug("Dumped cargoCapacity: {}", max_cargo)
        return Ship(fsd_info, mass, tank, max_cargo)
      except KeyError:
        pass
      log.error("Don't understand dump file!")

  @classmethod
  def from_file(self, filename):
    try:
      with open(filename, 'r') as f:
        ship = self.from_dict(json.load(f))
        if ship is None:
          sys.exit(1)
        return ship
    except IOError:
      log.error("Error reading file {}!", filename)

  @classmethod
  def from_args(self, fsd = None, mass = None, tank = None, max_cargo = None, reserve_tank = None, fsd_optmass = None, fsd_mass = None, fsd_maxfuel = None, range_boost = None):
    if fsd is None or mass is None or tank is None:
      log.error("Must pass fsd, mass and tank to ship.from_args()!")
      return None

    ship = Ship(fsd, mass, tank, max_cargo = max_cargo, reserve_tank = reserve_tank, range_boost = range_boost)
    if fsd_optmass is not None or fsd_mass is not None or fsd_maxfuel is not None:
      fsd_optmass = util.parse_number_or_add_percentage(fsd_optmass, ship.fsd.stock_optmass)
      fsd_mass = util.parse_number_or_add_percentage(fsd_mass, ship.fsd.stock_mass)
      fsd_maxfuel = util.parse_number_or_add_percentage(fsd_maxfuel, ship.fsd.stock_maxfuel)
      return ship.get_modified(optmass=fsd_optmass, fsdmass=fsd_mass, maxfuel=fsd_maxfuel)
    return ship

  @property
  def unladen_mass(self):
    return self.mass + self.reserve_tank

  def __str__(self):
    return "Ship [FSD: {0}, mass: {1:.1f}T, fuel: {2:.0f}T]:{3} jump range {4:.2f}LY ({5:.2f}LY)".format(str(self.fsd), self.mass, self.tank_size, ' reserve {:d}kg'.format(int(self.reserve_tank * 1000)) if self.reserve_tank else '', self.range(), self.max_range())

  def __repr__(self):
    return "Ship({}, {}T, {}T)".format(str(self.fsd), self.mass, self.tank_size)

  def supercharge(self, boost):
    self.fsd.supercharge(boost)

  @property
  def range_boost(self):
    return self.fsd.range_boost

  @range_boost.setter
  def range_boost(self, dist):
    self.fsd.range_boost = dist

  def refuel(self, cur_fuel, amount = None, percent = 0, absolute = False):
    if absolute:
      if amount is None:
        amount = self.tank_size * (percent / 100)
      return max(0.0, amount - cur_fuel)
    else:
      amount = amount if amount is not None else ((self.tank_size / 100.0) + (self.reserve_tank / 10.0)) * percent
      return min(amount, self.tank_size - cur_fuel)

  def refuel_percent(self, amount):
    if amount < self.tank_size:
      return 100 * amount / (self.tank_size + (self.reserve_tank * 10.0))
    else:
      return 100.0

  def max_range(self, cargo = 0):
    return self.fsd.max_range(self.unladen_mass, cargo)

  def range(self, fuel = None, cargo = 0):
    return self.fsd.range(self.unladen_mass, fuel if fuel is not None else self.tank_size, cargo)

  def cost(self, dist, fuel = None, cargo = 0):
    return self.fsd.cost(dist, self.unladen_mass, fuel if fuel is not None else self.tank_size, cargo)

  def min_fuel_weight(self, dist, cargo = 0, allow_invalid = False):
    return self.fsd.min_fuel_weight(dist, self.unladen_mass, cargo, allow_invalid)

  def max_fuel_weight(self, dist, cargo = 0, allow_invalid = False):
    return self.fsd.max_fuel_weight(dist, self.unladen_mass, cargo, allow_invalid)

  def fuel_weight_range(self, dist, cargo = 0, allow_invalid = False):
    return self.fsd.fuel_weight_range(dist, self.unladen_mass, cargo, allow_invalid)

  def to_arrive_with(self, target, dist, cargo = 0, allow_invalid = False):
    return self.fsd.fuel_weight_range(dist, self.unladen_mass + target, cargo, allow_invalid)[0]

  def get_modified(self, optmass = None, optmass_percent = None, maxfuel = None, maxfuel_percent = None, fsdmass = None, fsdmass_percent = None):
    fsd = self.fsd.get_modified(optmass, optmass_percent, maxfuel, maxfuel_percent, fsdmass, fsdmass_percent)
    s = Ship(fsd, self.mass, self.tank_size, self.cargo_capacity, self.reserve_tank)
    if fsdmass is not None:
      s.mass += (fsdmass - s.fsd.stock_mass)
    elif fsdmass_percent is not None:
      s.mass += s.fsd.stock_mass * (fsdmass_percent/100.0)
    return s

class HeartOfGold(Ship):
  def __init__(self):
    super(HeartOfGold, self).__init__(InfiniteImprobabilityDrive(), 0, 0, max_cargo = 0, reserve_tank = 0)
