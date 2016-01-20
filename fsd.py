import logging
import math
import re
import env

log = logging.getLogger("fsd")

class FSD(object):
  def __init__(self, classrating):
    drive_class = None
    drive_rating = None

    result = re.search('([A-E])', classrating.upper())
    if result is not None:
      drive_rating = result.group(1)

    result = re.search('(\d+)', classrating)
    if result is not None:
      drive_class = result.group(1)

    if drive_class is None or drive_rating is None:
      log.error("Error: Invalid FSD specification '{0}'.  Try, eg, '2A'".format(classrating))
      return None

    classrating = "{0}{1}".format(drive_class, drive_rating)
    if not classrating in env.data.coriolis_fsd_list:
      log.error("Error: No definition available for '{0}' drive.".format(classrating))
      return None

    self.drive = classrating
    fsdobj = env.data.coriolis_fsd_list[self.drive]
    self.optmass = float(fsdobj['optmass'])
    self.maxfuel = float(fsdobj['maxfuel'])
    self.fuelmul = float(fsdobj['fuelmul'])
    self.fuelpower = float(fsdobj['fuelpower'])

  def range(self, mass, fuel, cargo = 0):
    cur_maxfuel = min(self.maxfuel, fuel)
    return (self.optmass / (mass + fuel + cargo)) * math.pow((cur_maxfuel / self.fuelmul), (1 / self.fuelpower))

  def cost(self, dist, mass, fuel, cargo = 0):
    return self.fuelmul * math.pow(dist * ((mass + fuel + cargo) / self.optmass), self.fuelpower)
  
  def max_range(self, mass, cargo = 0):
    return self.range(mass, self.maxfuel, cargo)

  def max_fuel_weight(self, dist, mass, cargo = 0):
    _, wmax = self.fuel_weight_range(dist, mass, cargo)
    return wmax

  def fuel_weight_range(self, dist, mass, cargo = 0):
    # self.maxfuel == self.fuelmul * math.pow(dist * ((mass + fuel + cargo) / self.optmass), self.fuelpower)
    # self.maxfuel / self.fuelmul == math.pow(dist * ((mass + fuel + cargo) / self.optmass), self.fuelpower)
    # math.pow(self.maxfuel / self.fuelmul, 1 / self.fuelpower) * self.optmass / dist == (mass + fuel + cargo)
    wmax = (math.pow(self.maxfuel / self.fuelmul, 1 / self.fuelpower) * self.optmass / dist) - (mass + cargo)

    # Iterative check to narrow down the minimum fuel requirement
    clast = self.maxfuel
    c = clast
    # 15 iterations seems to result in at least 6 decimal places accuracy
    for i in range(0, 15):
      c = self.cost(dist, mass, clast, cargo)
      clast = c + (clast - c) / 4.0
    wmin = c

    return wmin, wmax
