import os
import struct
import sys
import util

_vscache_entry_len = 8 # bytes / 64 bits
_vscache_header_len = 6 * _vscache_entry_len
_vscache_eof_marker = 0x5AFEC0DE5AFEC0DE

def parse_visited_stars_cache(filename):
  with open(filename, 'rb') as f:
    # Skip over file header
    f.seek(_vscache_header_len, 0)
    cur_entry = f.read(_vscache_entry_len)
    while cur_entry is not None and len(cur_entry) == _vscache_entry_len:
      # Swap bytes to make it a sensible integer
      cur_id = struct.unpack('<Q', cur_entry)[0]
      # Check if this matches the magic EOF value
      if cur_id == _vscache_eof_marker:
        break
      # Return this ID
      yield cur_id
      cur_entry = f.read(_vscache_entry_len)