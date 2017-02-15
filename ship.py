import logging
from fsd import FSD

log = logging.getLogger("ship")


class Ship(object):
  def __init__(self, fsd_info, mass, tank, max_cargo = 0):
    # If we already have an FSD object, just use it as-is; otherwise assume a string and create a FSD object
    self.fsd = fsd_info if isinstance(fsd_info, FSD) else FSD(fsd_info)
    self.mass = mass
    self.tank_size = tank
    self.cargo_capacity = max_cargo

  def __str__(self):
    return "Ship [FSD: {0}, mass: {1:.1f}T, fuel: {2:.0f}T]: jump range {3:.2f}Ly ({4:.2f}Ly)".format(str(self.fsd), self.mass, self.tank_size, self.range(), self.max_range())

  def max_range(self, cargo = 0):
    return self.fsd.max_range(self.mass, cargo)

  def range(self, fuel = None, cargo = 0):
    return self.fsd.range(self.mass, fuel if fuel is not None else self.tank_size, cargo)

  def cost(self, dist, fuel = None, cargo = 0):
    return self.fsd.cost(dist, self.mass, fuel if fuel is not None else self.tank_size, cargo)

  def max_fuel_weight(self, dist, cargo = 0):
    return self.fsd.max_fuel_weight(dist, self.mass, cargo)

  def fuel_weight_range(self, dist, cargo = 0):
    return self.fsd.fuel_weight_range(dist, self.mass, cargo)

  def get_modified(self, optmass = None, optmass_percent = None, maxfuel = None, maxfuel_percent = None, fsdmass = None, fsdmass_percent = None):
    fsd = self.fsd.get_modified(optmass, optmass_percent, maxfuel, maxfuel_percent, fsdmass, fsdmass_percent)
    s = Ship(fsd, self.mass, self.tank_size, self.cargo_capacity)
    if fsdmass is not None:
      s.mass += (fsdmass - s.fsd.stock_mass)
    elif fsdmass_percent is not None:
      s.mass += s.fsd.stock_mass * (fsdmass_percent/100.0)
    return s
