import math
import os
import shutil
import struct
import sys
import tempfile

from . import util

log = util.get_logger('starcache')

IMPORTFILE = "ImportStars.txt"
IMPORTFORMAT = 'ImportStars{}.txt'
IMPORTEDFILE = "ImportStars.txt.imported"
CACHEFILE = "VisitedStarsCache.dat"
RECENTFILE = "RecentlyVisitedStars.dat"
# ED 2.x: 100; ED 3.0: 200
KNOWN_VERSIONS = [100, 200]

class VisitedStarsCacheHeader(object):
  def __init__(self):
    self.start_magic = 'VisitedStars'
    self.recent_magic = 0x7f00
    self.end_magic = 0x5AFEC0DE5AFEC0DE
    self.magic = self.start_magic
    self.recent = False
    self.version = KNOWN_VERSIONS[0]
    self.start = 0x30
    self.end = 0x30
    self.num_entries_offset = 0x18
    self.num_entries = 0
    self.entry_len = self.expected_entry_len
    self.account_id = 0
    self.padding = 0
    self.cmdr_id = 0

  @property
  def has_visit_count(self):
    # This field was added as part of ED 3.0
    return self.version >= 200

  @property
  def has_last_visit_date(self):
    # This field was added as part of ED 3.0
    return self.version >= 200

  @property
  def expected_entry_len(self):
    exp_len = 8
    if self.has_visit_count:
      exp_len += 4
    if self.has_last_visit_date:
      exp_len += 4
    return exp_len

def read_struct(f, format, size):
  try:
    data = f.read(size)
    return struct.unpack(format, data)[0]
  except:
    log.error('Failed to read {} octets!', size)
    raise

def read_uint32(f):
  return read_struct(f, '<L', 4)

def read_uint64(f):
  return read_struct(f, '<Q', 8)

def write_uint32(f, n):
  return write_struct(f, '<L', n)

def write_struct(f, format, n):
  try:
    f.write(struct.pack(format, n))
  except:
    log.error('Failed to write {} as {}', n, format)
    raise

def write_uint64(f, n):
  return write_struct(f, '<Q', n)

def write_str(f, s):
  try:
    f.write(util.get_bytes(s, 'ascii'))
  except:
    log.error('Failed to write "{}" as string', s)
    raise

def read_visited_stars_cache_header(f):
  try:
    header = VisitedStarsCacheHeader()
    header.magic = f.read(len(header.start_magic))
    if header.magic.decode("utf-8") != header.start_magic:
      log.error('Missing "VisitedStars" header!')
      return None
    recent = read_uint32(f)
    if recent == header.recent_magic:
      header.recent = True
    elif recent:
      log.warning('Unexpected recent magic: {0:08X}'.format(recent))
    header.version = read_uint32(f)
    if header.version in KNOWN_VERSIONS:
      log.debug('Found known VSC version {}', header.version)
    else:
      log.warning('Unexpected version {} not {}...', header.version, ', '.join([str(version) for version in KNOWN_VERSIONS]))
    header.start = read_uint32(f)
    header.num_entries = read_uint32(f)
    header.entry_len = read_uint32(f)
    header.account_id = read_uint32(f)
    header.padding = read_uint32(f)
    header.cmdr_id = read_uint64(f)
    if not header.recent:
      header.end = header.start + (header.num_entries * header.entry_len)
      f.seek(header.end, 0)
      if f.tell() != header.end:
        log.error('Failed to seek to end of entries!')
        return None
      if read_uint64(f) != header.end_magic:
        log.warning('Missing magic EOF marker!')
    f.seek(header.start)
    if f.tell() != header.start:
      log.error('Failed to seek to start of entries!')
      return None
    return header
  except:
    return None

def write_visited_stars_cache(filename, systems, recent = False, version = KNOWN_VERSIONS[-1]):
  scratch = None
  try:
    dirname = os.path.dirname(filename)
    fd, scratch = tempfile.mkstemp('.tmp', os.path.basename(filename), dirname if dirname else '.')
    with os.fdopen(fd, 'wb') as f:
      header = VisitedStarsCacheHeader()
      if version is not None:
        header.version = version
      header.entry_len = header.expected_entry_len
      write_str(f, header.magic)
      if recent:
        write_uint32(f, header.recent_magic)
      else:
        write_uint32(f, 0)
      write_uint32(f, header.version)
      write_uint32(f, header.start)
      header.num_entries_offset = f.tell()
      write_uint32(f, header.num_entries)
      write_uint32(f, header.entry_len)
      write_uint32(f, header.account_id)
      write_uint32(f, header.padding)
      write_uint64(f, header.cmdr_id)
      for system in systems:
        if system.id64 is None:
          log.error('{} has no id64!', system.name)
          continue
        write_uint64(f, system.id64)
        if header.has_visit_count:
          visit_count = 1
          write_uint32(f, visit_count)
        if header.has_last_visit_date:
          last_visit_date = 0
          write_uint32(f, last_visit_date)
        header.num_entries += 1
      if not recent:
        write_uint64(f, header.end_magic)
        f.seek(header.num_entries_offset)
        if f.tell() != header.num_entries_offset:
          log.error('Failed to seek to entry count offset!')
          raise RuntimeError
        write_uint32(f, header.num_entries)
    shutil.move(scratch, filename)
  except:
    if scratch is not None:
      os.unlink(scratch)
    raise
    return False
  return True

def parse_visited_stars_cache(filename):
  with open(filename, 'rb') as f:
    header = read_visited_stars_cache_header(f)
    if not header:
      return
    n = 0
    while n < header.num_entries:
      cur_id = read_uint64(f)
      # Check if this matches the magic EOF value
      if cur_id == header.end_magic:
        break
      if header.has_visit_count:
        visit_count = read_uint32(f)
      if header.has_last_visit_date:
        last_visit_date = read_uint32(f)
      n += 1
      # Return this ID
      yield cur_id


def create_import_lists(data):
  count = int(math.ceil(math.log(len(data), 2)))
  lists = [[] for _ in range(count)]
  for idx, s in enumerate(data):
    for i in range(count):
      if (idx & (2**i)) == (2**i):
        lists[i].append(s)
  return lists


def create_import_list_files(data, output_format = IMPORTFORMAT):
  names = ['Full']
  with open(output_format.format('Full'), 'w') as f:
    f.writelines(['{}\n'.format(d) for d in data])
  for i, l in enumerate(create_import_lists(data)):
    names.append(str(i))
    with open(output_format.format(i), 'w') as f:
      f.writelines(['{}\n'.format(d) for d in l])
  return names


def calculate_id64s_from_lists(names, full, lists):
  if len(names) == 0 or len(full) == 0 or len(lists) == 0:
    return {}
  if len(names) < len(full):
    return {}
  count = 2**len(lists)
  output = {}
  dups = 0
  for n in full:
    idx = 0
    for i in range(len(lists)):
      if n in lists[i]:
        idx += (2**i)
    try:
      output[names[idx]] = n
    except IndexError:
      log.warning("Possible duplicate name for ID {} (entry {}; index {}/{})", n, i, idx, len(full))
      dups += 1
  if dups:
    raise IndexError("Found {} possible duplicate name(s)".format(dups))
  return output


def calculate_id64s_from_list_files(names_file, full_file, list_files):
  with open(names_file, 'r') as f:
    names = [n.strip() for n in f]
  full = list(parse_visited_stars_cache(full_file))
  lists = []
  for fname in list_files:
    lists.append(list(parse_visited_stars_cache(fname)))
  return calculate_id64s_from_lists(names, full, lists)

