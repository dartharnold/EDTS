import logging

log = logging.getLogger("ship")

class Ship:
  def __init__(self, fsd, mass, tank, cargo = 0):
    self.fsd = fsd
    self.mass = mass
    self.tank_size = tank
    self.cargo_capacity = cargo

  def max_range(self, cargo = 0):
    return self.fsd.max_range(self.mass, cargo)

  def range(self, fuel = None, cargo = 0):
    return self.fsd.range(self.mass, fuel if fuel is not None else self.tank_size, cargo)

  def cost(self, dist, mass, fuel = None, cargo = 0):
    return self.fsd.cost(dist, self.mass, fuel if fuel is not None else self.tank_size, cargo)

  def max_fuel_weight(self, dist, cargo = 0):
    return self.fsd.max_fuel_weight(dist, self.mass, cargo)

  def fuel_weight_range(self, dist, cargo = 0):
    return self.fsd.fuel_weight_range(dist, self.mass, cargo)

