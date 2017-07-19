class Body(object):
  STAR       = 1 << 0

  def __init__(self, body_type = None, name = None):
    self.type = body_type
    self.name = name

class Star(Body):
  MAIN_SEQUENCE   = ('O', 'B', 'A', 'F', 'G', 'K', 'M')
  BLACK_HOLE      = ('BH', 'SMBH')
  NEUTRON         = 'N'
  NON_SEQUENCE    = (BLACK_HOLE, 'X', NEUTRON)
  SCOOPABLE       = MAIN_SEQUENCE
  SUPERCHARGEABLE = ('D', NEUTRON)

  CLASS_NAMES     = {
    'A': 'A (blue-white) star',
    'AEBE': 'Herbig Ae/Be star',
    'B': 'B (blue-white) star',
    'C': 'C star',
    'CH': 'CH star',
    'CHD': 'Chd star',
    'CJ': 'CJ star',
    'CN': 'CN star',
    'CS': 'CS star',
    'D': 'D (white dwarf) star',
    'DA': 'DA (white dwarf) star',
    'DAB': 'DAB (white dwarf) star',
    'DAO': 'DAO (white dwarf) star',
    'DAV': 'DAV (white dwarf) star',
    'DAZ': 'DAZ (white dwarf) star',
    'DB': 'DB (white dwarf) star',
    'DBV': 'DBV (white dwarf) star',
    'DBZ': 'DBZ (white dwarf) star',
    'DC': 'DC (white dwarf) star',
    'DCV': 'DCV (white dwarf) star',
    'DO': 'DO (white dwarf) star',
    'DOV': 'DOV (white dwarf) star',
    'DQ': 'DQ (white dwarf) star',
    'DX': 'DX (white dwarf) star',
    'F': 'F (white) star',
    'G': 'G (white-yellow) star',
    'H': 'Black hole',
    'K': 'K (yellow-orange) star',
    'L': 'L (brown dwarf) star',
    'M': 'M (red) star',
    'MS': 'MS star',
    'N': 'Neutron star',
    'O': 'O (blue-white) star',
    'S': 'S star',
    'SMBH': 'Supermassive black hole',
    'T': 'T (brown dwarf) star',
    'TTS': 'T Tauri star',
    'W': 'Wolf-Rayet star',
    'WC': 'Wolf-Rayet C star',
    'WN': 'Wolf-Rayet N star',
    'WNC': 'Wolf-Rayet NC star',
    'WO': 'Wolf-Rayet O star',
    'X': 'Exotic star',
    'Y': 'Y (brown dwarf) star'
  }

  def __init__(self, data):
    super(Star, self).__init__(self.STAR, data.get('name'))
    self.spectral_class = None
    self.arrival = bool(data.get('is_main_star'))
    if data.get('spectral_class'):
      self.spectral_class = data['spectral_class']
    elif data.get('group_name') == 'Compact star':
      star_type = data.get('type_name', '').lower()
      if star_type.startswith('neutron'):
        self.spectral_class = self.NEUTRON
      elif star_type == 'supermassive black hole':
        self.spectral_class = self.SMBH
      elif star_type.endswith('black hole'):
        self.spectral_class = self.BH
      elif star_type == 'exotic':
        self.spectral_class = self.EXOTIC

  @property
  def main_sequence(self):
    return self.spectral_class in self.MAIN_SEQUENCE

  @property
  def scoopable(self):
    return self.main_sequence()

  @property
  def non_sequence(self):
    return self.spectral_class in self.NON_SEQUENCE

  @property
  def classification(self):
    if self.spectral_class is None:
      return None
    elif self.spectral_class in ['AEBE', self.BLACK_HOLE, 'MS', self.NEUTRON, 'TTS']:
      return self.spectral_class
    else:
      return self.spectral_class[0]

  @property
  def superchargeable(self):
    return self.classification in self.SUPERCHARGEABLE

  def to_string(self, use_long = False):
    if use_long:
      name = self.CLASS_NAMES.get(self.spectral_class)
      if name is not None:
        return u'{}'.format(name)
      else:
        return u'Star'
    else:
      return u'{}'.format(self.classification if self.spectral_class is not None else 'Star')

  def __str__(self):
    return self.to_string()

  def __repr__(self):
    return u'Star({})'.format(self.classification)
