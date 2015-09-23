import logging
import math
import re

log = logging.getLogger("fsd")

class FSD:
  def __init__(self, classrating, fsdspec):
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
    if not classrating in fsdspec:
      log.error("Error: No definition available for '{0} ' drive.".format(classrating))

    self.drive = classrating
    fsdobj = fsdspec[self.drive]
    self.optmass = float(fsdobj['optmass'])
    self.maxfuel = float(fsdobj['maxfuel'])
    self.fuelmul = float(fsdobj['fuelmul'])
    self.fuelpower = float(fsdobj['fuelpower'])

  def range(self, mass, fuel, cargo = 0):
    return (self.optmass / (mass + fuel + cargo)) * math.pow((self.maxfuel / self.fuelmul), (1 / self.fuelpower))

  def cost(self, dist, mass, fuel, cargo):
    return self.fuelmul * math.pow(dist * (mass / self.optmass), self.fuelpower)
