import collections
from . import util

class ColumnObjectWriter(object):
  def __init__(self, columns = 0, padding = None):
    self._rows = []
    self._lengths = []
    self._padding = []
    self.fmt = ''
    self.intra = None
    self.columns = 0
    self.rows = 0
    self.expand(columns, padding)

  def expand(self, columns, padding = None):
    if padding is None:
      padding = '<'
    if columns > 0:
      self._lengths += [0 for column in range(0, columns)]
      if isinstance(padding, collections.Iterable) and not util.is_str(padding):
        padding += [padding[-1] for column in range(0, columns - len(padding))]
        self._padding += padding
      else:
        self._padding += [padding for column in range(0, columns)]
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
      intra = '  '
    self.intra = intra
    self.fmt = self.intra.join(['{}'.format(' ' if column > 0 else '') + '{: ' + self._padding[column] + str(self._lengths[column]) + '}' for column in range(0, self.columns)])

  def render(self, intra = None):
    if not self.fmt or (intra is not None and intra != self.intra):
      self.reformat()
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
