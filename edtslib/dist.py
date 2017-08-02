class Dist(object):
  KM = 1000.0
  MM = 1000 * KM
  LS = 299.792 * MM
  LY = 31557600 * LS
  M_SUFFIX  = 'm'
  KM_SUFFIX = 'km'
  MM_SUFFIX = 'Mm'
  LS_SUFFIX = 'Ls'
  LY_SUFFIX = 'Ly'

  def __init__(self, d, s = None):
    self.metres = d
    self.suffix = s

  @property
  def kilometres(self):
    return self.metres / self.KM

  @property
  def megametres(self):
    return self.metres / self.MM

  @property
  def lightseconds(self):
    return self.metres / self.LS

  @property
  def lightyears(self):
    return self.metres / self.LY

  def prettyprint(self, f, suffix = '', full = False):
    if full:
      return '{:.2f}{}'.format(f, suffix)
    else:
      return '{:.2f}'.format(f).rstrip('0').rstrip('.') + suffix

  def __str__(self):
    if self.metres > 0.1 * self.LY:
      return self.prettyprint(self.lightyears, self.LY_SUFFIX)
    if self.metres > 0.1 * self.LS:
      return self.prettyprint(self.lightseconds, self.LS_SUFFIX)
    if self.metres > 0.1 * self.MM:
      return self.prettyprint(self.megametres, self.MM_SUFFIX)
    if self.metres > self.KM:
      return self.prettyprint(self.kilometres, self.KM_SUFFIX)
    return self.prettyprint(self.metres, self.M_SUFFIX)

  def to_string(self, full = None):
    return str(self)

class Metres(Dist):
  def __init__(self, d):
    super(Metres, self).__init__(d, self.M_SUFFIX)

  def to_string(self, full = None):
    return self.prettyprint(self.metres, self.suffix, full)

class Kilometres(Dist):
  def __init__(self, d):
    super(Kilometres, self).__init__(d * self.KM, self.KM_SUFFIX)

  def to_string(self, full = None):
    return self.prettyprint(self.kilometres, self.suffix, full)

class Megametres(Dist):
  def __init__(self, d):
    super(Megametres, self).__init__(d * self.MM, self.MM_SUFFIX)

  def to_string(self, full = None):
    return self.prettyprint(self.megametres, self.suffix, full)

class Lightseconds(Dist):
  def __init__(self, d):
    super(Lightseconds, self).__init__(d * self.LS, self.LS_SUFFIX)

  def to_string(self, full = None):
    return self.prettyprint(self.lightseconds, self.suffix, full)

class Lightyears(Dist):
  def __init__(self, d):
    super(Lightyears, self).__init__(d * self.LY, self.LY_SUFFIX)

  def to_string(self, full = None):
    return self.prettyprint(self.lightyears, self.suffix, full)
