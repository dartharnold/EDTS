import math
import re

from . import env
from . import util

log = util.get_logger("fsd")


class FSD(object):
  def __init__(self, classrating):
    drive_class = None
    drive_rating = None

    result = re.search('([A-E])', classrating.upper())
    if result is not None:
      drive_rating = result.group(1)

    result = re.search(r'(\d+)', classrating)
    if result is not None:
      drive_class = result.group(1)

    if drive_class is None or drive_rating is None:
      log.error("Error: Invalid FSD specification '{0}'.  Try, eg, '2A'", classrating)
      return None

    classrating = "{0}{1}".format(drive_class, drive_rating)
    # Ensure we have an environment to query
    with env.use() as data:
      if classrating not in data.coriolis_fsd_list:
        log.error("Error: No definition available for '{0}' drive.", classrating)
        return None
      self.drive = classrating
      fsdobj = data.coriolis_fsd_list[self.drive]

    self.optmass         = float(fsdobj['optmass'])
    self.maxfuel         = float(fsdobj['maxfuel'])
    self.fuelmul         = float(fsdobj['fuelmul'])
    self.fuelpower       = float(fsdobj['fuelpower'])
    self.mass            = float(fsdobj['mass'])
    self.boost           = 1.0
    self.range_boost     = 0.0
    self.stock_mass      = self.mass
    self.stock_optmass   = self.optmass
    self.stock_maxfuel   = self.maxfuel
    self.stock_fuelmul   = self.fuelmul
    self.stock_fuelpower = self.fuelpower

  def clone(self):
    f = FSD(self.drive)
    f.optmass = self.optmass
    f.maxfuel = self.maxfuel
    f.fuelmul = self.fuelmul
    f.fuelpower = self.fuelpower
    f.mass = self.mass
    f.boost = self.boost
    f.range_boost = self.range_boost
    return f

  @classmethod
  def from_dict(self, data):
    if '$schema' in data and re.match(r'https://coriolis.*schemas/ship-loadout', data['$schema']):
      try:
        log.debug("Reading FSD from Coriolis dump")
        drive = data['components']['standard']['frameShiftDrive']
        classrating = '{}{}'.format(drive['class'], drive['rating'])
        log.debug("Dumped FSD is {}", classrating)
        fsd_info = FSD(classrating)
        if 'modifications' in drive:
          mods = drive['modifications']
          # Coriolis dump reports, eg, a 28.7910% bonus as 2879.10.
          if 'mass' in mods:
            fsd_info.mass *= 1.0 + mods['mass'] / 10000.0
            log.debug("Dumped FSD modified mass is {}", fsd_info.mass)
          if 'maxfuel' in mods:
            fsd_info.maxfuel *= 1.0 + mods['maxfuel'] / 10000.0
            log.debug("Dumped FSD modified maxfuel is {}", fsd_info.maxfuel)
          if 'optmass' in mods:
            fsd_info.optmass *= 1.0 + mods['optmass'] / 10000.0
            log.debug("Dumped FSD modified optmass is {}", fsd_info.optmass)
        return fsd_info
      except KeyError:
        pass
    log.error("Don't understand dump file!")

  def __str__(self):
    return "{}{}".format(self.drive, " (modified)" if self.is_modified else "")

  def __repr__(self):
    return "FSD({}{})".format(self.drive, ", modified" if self.is_modified else "")

  @property
  def is_modified(self):
    return (self.optmass != self.stock_optmass
         or self.maxfuel != self.stock_maxfuel
         or self.fuelmul != self.stock_fuelmul
         or self.fuelpower != self.stock_fuelpower)

  def get_modified(self, optmass = None, optmass_percent = None, maxfuel = None, maxfuel_percent = None, fsdmass = None, fsdmass_percent = None):
    fsd = FSD(self.drive)
    if (optmass is not None and optmass_percent is not None):
      raise ValueError("A maximum of one of optmass and optmass_percent must be provided")
    if (fsdmass is not None and fsdmass_percent is not None):
      raise ValueError("A maximum of one of fsdmass and fsdmass_percent must be provided")
    if (maxfuel is not None and maxfuel_percent is not None):
      raise ValueError("A maximum of one of maxfuel and maxfuel_percent must be provided")
    if optmass is not None:
      fsd.optmass = optmass
    elif optmass_percent is not None:
      fsd.optmass *= (1.0 + optmass_percent/100.0)
    if maxfuel is not None:
      fsd.maxfuel = maxfuel
    elif maxfuel_percent is not None:
      fsd.maxfuel *= (1.0 + maxfuel_percent/100.0)
    fsd.range_boost = self.range_boost
    return fsd

  def supercharge(self, boost):
    if not boost:
      self.boost = 1.0
    elif str(boost).upper() == 'D':
      self.boost = 1.25
    elif str(boost).upper() == 'N':
      self.boost = 4.0
    else:
      try:
        self.boost = [1.0, 1.25, 1.5, 2.0][int(boost)]
      except:
        log.error("Invalid boost value {}", boost)
        self.boost = 1.0

  def _range(self, mass, fuel, cargo = 0, fuelmul = None):
    if fuelmul is None:
      fuelmul = self.fuelmul
    cur_maxfuel = min(self.maxfuel, float(fuel))
    return ((self.optmass / (float(mass) + float(max(0.0, fuel)) + float(max(0.0, cargo)))) * math.pow(cur_maxfuel / fuelmul, (1.0 / self.fuelpower)))

  def boosted_fuelmul(self, mass, fuel, cargo = 0):
    base_range = self._range(mass, fuel, cargo)
    return self.fuelmul * math.pow(base_range / (base_range + self.range_boost), self.fuelpower)

  def range(self, mass, fuel, cargo = 0):
    return self.boost * self._range(mass, fuel, cargo, fuelmul = self.boosted_fuelmul(mass, fuel, cargo))

  def cost(self, dist, mass, fuel, cargo = 0):
    return self.boosted_fuelmul(mass, fuel, cargo) * math.pow((dist / self.boost) * ((float(mass) + float(max(0.0, fuel)) + float(max(0.0, cargo))) / self.optmass), self.fuelpower)

  def max_range(self, mass, cargo = 0):
    return self.range(mass, self.maxfuel, cargo)

  def max_fuel_weight(self, dist, mass, cargo = 0, allow_invalid = False):
    # If we're not going anywhere, you can have as much fuel as you like
    if dist <= 0.0:
      return float('inf')
    result = math.pow(self.maxfuel / self.boosted_fuelmul(mass, self.maxfuel, cargo), 1.0 / self.fuelpower) * (self.optmass / (float(dist) / self.boost)) - (float(mass) + float(cargo))
    if allow_invalid or result >= self.maxfuel:
      return result
    else:
      return None

  def min_fuel_weight(self, dist, mass, cargo = 0, allow_invalid = False):
    # If we're not going anywhere, we need no fuel
    if dist <= 0.0:
      return 0.0
    # Iterative check to narrow down the minimum fuel requirement
    clast = self.maxfuel
    c = clast
    # 15 iterations seems to result in at least 6 decimal places accuracy
    for _ in range(15):
      c = self.cost(dist, mass, clast, cargo)
      clast = c + (clast - c) / 4.0
      if clast > 10**10:
        log.debug("Minimum fuel approximation became extremely high, stopping early.")
        break
    return c

  def fuel_weight_range(self, dist, mass, cargo = 0, allow_invalid = False):
    wmin = self.min_fuel_weight(dist, mass, cargo, allow_invalid)
    wmax = self.max_fuel_weight(dist, mass, cargo, allow_invalid)
    if allow_invalid or (wmin <= self.maxfuel and wmax is not None and wmax >= 0.0):
      return (wmin, wmax)
    else:
      return (None, None)

class InfiniteImprobabilityDrive(FSD):
  def __init__(self):
    self.optmass    = float('inf')
    self.maxfuel    = float('inf')
    self.fuelmul    = 1.0
    self.fuelpower  = 1.0
    self.mass       = 0.0
    self.boost      = 1.0
    self.stock_mass      = self.mass
    self.stock_optmass   = self.optmass
    self.stock_maxfuel   = self.maxfuel
    self.stock_fuelmul   = self.fuelmul
    self.stock_fuelpower = self.fuelpower

  def clone(self):
    return InfiniteImprobabilityDrive()

  def __str__(self):
    return "Inf"

  def __repr__(self):
    return "FSD(Inf)"

  def get_modified(self, optmass = None, optmass_percent = None, maxfuel = None, maxfuel_percent = None, fsdmass = None, fsdmass_percent = None):
    return self.clone()

  def range(self, mass, fuel, cargo = 0):
    return float('inf')

  def cost(self, dist, mass, fuel, cargo = 0):
    return 0.0

  def max_fuel_weight(self, dist, mass, cargo = 0, allow_invalid = False):
    return float('inf')

  def min_fuel_weight(self, dist, mass, cargo = 0, allow_invalid = False):
    return 0.0
