import collections
from . import util

class ColumnObjectWriter(object):
  def __init__(self, columns = 0, padding = None, separator = None):
    self._rows = []
    self._lengths = []
    self._padding = []
    self._intra = []
    self.fmt = ''
    self.columns = 0
    self.rows = 0
    self.expand(columns, padding, separator)

  def _expand_parameter(self, columns, parameter, values):
    if isinstance(values, collections.Iterable) and not util.is_str(values):
      values += [values[-1] for column in range(0, columns - len(values))]
      parameter += values
    else:
      parameter += [values for column in range(0, columns)]

  def expand(self, columns, padding = None, intra = None):
    if padding is None:
      padding = self._padding[-1] if len(self._padding) else '<'
    if intra is None:
      intra = self._intra[-1] if len(self._intra) else '   '
    if columns > 0:
      self._lengths += [0 for column in range(0, columns)]
      self._expand_parameter(columns, self._padding, padding)
      self._expand_parameter(columns, self._intra, intra)
      self.columns += columns

  def size(self, column):
    return self._lengths[column]

  def add(self, row):
    columns = len(row)
    self.expand(columns - self.columns)
    s = []
    reformat = False
    for column in range(0, columns):
      content = str(row[column])
      s.append(content)
      l = len(content)
      o = self._lengths[column]
      reformat |= (l != o)
      self._lengths[column] = max(l, o)
    self._rows.append(s)
    self.rows += 1
    if reformat:
      self.reformat()

  def reformat(self, intra = None):
    if intra is None:
      _intra = self._intra
    else:
      _intra = []
      self._expand_parameter(self.columns, _intra, intra)
    self.fmt = ''.join(['{}'.format(_intra[column - 1] if column > 0 else '') + '{: ' + self._padding[column] + str(self._lengths[column]) + '}' for column in range(0, self.columns)])

  def render(self, intra = None):
    if not self.fmt or (intra is not None and intra != self._intra):
      self.reformat(intra)
    for row in self._rows:
      yield self.fmt.format(*row)

  def to_string(self, intra = None):
    s = ''
    for row in self.render(intra):
      if len(s):
        s += "\n"
      s += row
    return s

  def out(self, intra = None):
    for row in self.render(intra):
      print(row)
