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
  SUFFICES = (M_SUFFIX, KM_SUFFIX, MM_SUFFIX, LS_SUFFIX, LY_SUFFIX)

  def __init__(self, metres, scale = None, suffix = None):
    self.metres = metres
    if scale is not None:
      canon = self._canonical_suffix(scale)
      if canon == self.KM_SUFFIX:
        scale = self.KM_SUFFIX
        self.metres *= self.KM
      elif canon == self.MM_SUFFIX:
        scale = self.MM_SUFFIX
        self.metres *= self.MM
      elif canon == self.LS_SUFFIX:
        scale = self.LS_SUFFIX
        self.metres *= self.LS
      elif canon == self.LY_SUFFIX:
        scale = self.LY_SUFFIX
        self.metres *= self.LY
    self.suffix = suffix if suffix is not None else scale

  def _canonical_suffix(self, suffix = ''):
    suffix = suffix.lower()
    if suffix == self.KM_SUFFIX.lower():
      return self.KM_SUFFIX
    elif suffix == self.MM_SUFFIX.lower():
      return self.MM_SUFFIX
    elif suffix == self.LS_SUFFIX.lower():
      return self.LS_SUFFIX
    elif suffix == self.LY_SUFFIX.lower():
      return self.LY_SUFFIX
    return self.M_SUFFIX

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

  def prettyprint(self, f, suffix = '', full = False, long = False):
    fmt = '8g' if long else '.2f'
    if full:
      return ('{:' + fmt + '}{}').format(f, suffix)
    else:
      return ('{:' + fmt + '}').format(f).rstrip('0').rstrip('.') + suffix

  def convert(self, suffix = '', full = False, long = False):
    if suffix:
      suffix = self._canonical_suffix(suffix)
    else:
      if self.metres > 0.1 * self.LY:
        suffix = self.LY_SUFFIX
      elif self.metres > 0.1 * self.LS:
        suffix = self.LS_SUFFIX
      elif self.metres > 0.1 * self.MM:
        suffix = self.MM_SUFFIX
      elif self.metres > self.KM:
        suffix = self.KM_SUFFIX
      else:
        suffix = self.M.SUFFIX
    if suffix == self.LY_SUFFIX:
      return self.prettyprint(self.lightyears, self.LY_SUFFIX, full, long)
    elif suffix == self.LS_SUFFIX:
      return self.prettyprint(self.lightseconds, self.LS_SUFFIX, full, long)
    elif suffix == self.MM_SUFFIX:
      return self.prettyprint(self.megametres, self.MM_SUFFIX, full, long)
    elif suffix == self.KM_SUFFIX:
      return self.prettyprint(self.kilometres, self.KM_SUFFIX, full, long)
    else:
      return self.prettyprint(self.metres, self.M_SUFFIX, full, long)

  def __repr__(self):
    return self.convert(self.suffix, True)

  def __str__(self):
    return self.convert(self.suffix)

  def to_string(self, full = None, long = None):
    return self.convert(self.suffix, full, long)

class Metres(Dist):
  def __init__(self, d):
    super(Metres, self).__init__(d, self.M_SUFFIX)

  def to_string(self, full = None, long = None):
    return self.prettyprint(self.metres, self.suffix, full, long)

class Kilometres(Dist):
  def __init__(self, d):
    super(Kilometres, self).__init__(d, self.KM_SUFFIX)

  def to_string(self, full = None, long = None):
    return self.prettyprint(self.kilometres, self.suffix, full, long)

class Megametres(Dist):
  def __init__(self, d):
    super(Megametres, self).__init__(d, self.MM_SUFFIX)

  def to_string(self, full = None, long = None):
    return self.prettyprint(self.megametres, self.suffix, full, long)

class Lightseconds(Dist):
  def __init__(self, d):
    super(Lightseconds, self).__init__(d, self.LS_SUFFIX)

  def to_string(self, full = None, long = None):
    return self.prettyprint(self.lightseconds, self.suffix, full, long)

class Lightyears(Dist):
  def __init__(self, d):
    super(Lightyears, self).__init__(d, self.LY_SUFFIX)

  def to_string(self, full = None, long = None):
    return self.prettyprint(self.lightyears, self.suffix, full, long)
