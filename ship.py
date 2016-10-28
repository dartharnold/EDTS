import logging
from fsd import FSD

log = logging.getLogger("ship")


class Ship(object):
  def __init__(self, fsd_info, mass, tank, cargo = 0):
    # If we already have an FSD object, just use it as-is; otherwise assume a string and create a FSD object
    self.fsd = fsd_info if isinstance(fsd_info, FSD) else FSD(fsd_info)
    self.mass = mass
    self.tank_size = tank
    self.cargo_capacity = cargo

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
    if (optmass is not None and optmass_percent is not None):
      raise ValueError("A maximum of one of optmass and optmass_percent must be provided")
    if (fsdmass is not None and fsdmass_percent is not None):
      raise ValueError("A maximum of one of fsdmass and fsdmass_percent must be provided")
    if (maxfuel is not None and maxfuel_percent is not None):
      raise ValueError("A maximum of one of maxfuel and maxfuel_percent must be provided")
    s = Ship(self.fsd.drive, self.mass, self.tank_size, self.cargo_capacity)
    if optmass is not None:
      s.fsd.optmass = optmass
    elif optmass_percent is not None:
      s.fsd.optmass *= (1.0 + optmass_percent/100.0)
    if fsdmass is not None:
      s.mass += (fsdmass - s.fsd.mass)
    elif fsdmass_percent is not None:
      s.mass += s.fsd.mass * (fsdmass_percent/100.0)
    if maxfuel is not None:
      s.fsd.maxfuel = maxfuel
    elif maxfuel_percent is not None:
      s.fsd.maxfuel *= (1.0 + maxfuel_percent/100.0)
    return s