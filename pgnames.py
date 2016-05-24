from __future__ import print_function, division
import logging
import math
import string
import sys
import time

import pgdata
import sector
import util
import vector3

app_name = "pgnames"

logging.basicConfig(level = logging.INFO, format="[%(asctime)-15s] [%(name)-6s] %(message)s")
log = logging.getLogger(app_name)

_srp_divisor1 = len(string.ascii_uppercase)
_srp_divisor2 = _srp_divisor1**2
_srp_divisor3 = _srp_divisor1**3
_srp_rowlength = 128
_srp_sidelength = _srp_rowlength**2

_expected_fragment_limit = 4

# Get a star's relative position within a sector
# Original version by Kay Johnston (CMDR Jackie Silver)
# Note that in the form "Sector AB-C d3", the "3" is number2, NOT 1
def get_star_relpos(prefix, centre, suffix, lcode, number1, number2):
  if number1 is None:
    number1 = 0

  position  = _srp_divisor3 * int(number1)
  position += _srp_divisor2 * string.ascii_uppercase.index(suffix.upper())
  position += _srp_divisor1 * string.ascii_uppercase.index(centre.upper())
  position +=                 string.ascii_uppercase.index(prefix.upper())

  row = int(position // _srp_sidelength)
  position -= (row * _srp_sidelength)

  stack = int(position // _srp_rowlength)
  position -= (stack * _srp_rowlength)

  column = position

  cubeside = sector.cube_size / pow(2, ord('h') - ord(lcode.lower()))
  halfwidth = cubeside / 2

  approx_x = (column * cubeside) + halfwidth
  approx_y = (stack * cubeside) + halfwidth
  approx_z = (row * cubeside) + halfwidth
  
  if (approx_x < 0 or approx_x > sector.cube_size
   or approx_y < 0 or approx_y > sector.cube_size
   or approx_z < 0 or approx_z > sector.cube_size):
    input_star = "{0}{1}-{2} {3}{4}".format(
      prefix, centre, suffix, lcode, "{0}-{1}".format(number1, number2) if int(number1) > 0 else number2)
    log.error("Relative star position calculation produced invalid result [{0},{1},{2}] for input {3}. "
      "Please report this error.".format(approx_x, approx_y, approx_z, input_star))

  return (vector3.Vector3(approx_x,approx_y,approx_z), halfwidth)

  
def get_ha_sector_origin(centre, radius, modulo):
  sector_origin = centre - vector3.Vector3(radius, radius, radius)
  sox = math.floor(sector_origin.x)
  soy = math.floor(sector_origin.y)
  soz = math.floor(sector_origin.z)
  sox -= (sox - int(sector.base_coords.x)) % modulo
  soy -= (soy - int(sector.base_coords.y)) % modulo
  soz -= (soz - int(sector.base_coords.z)) % modulo 
  return vector3.Vector3(float(sox), float(soy), float(soz))


# Get a sector, either from its position or from its name
def get_sector(pos):
  if isinstance(pos, vector3.Vector3):
    x = (pos.x - sector.base_coords.x) // sector.cube_size
    y = (pos.y - sector.base_coords.y) // sector.cube_size
    z = (pos.z - sector.base_coords.z) // sector.cube_size
    # We don't authoritatively know the name, so return it without one
    return sector.Sector(int(x), int(y), int(z))
  else:
    # Assume we have a string, call down to get it by name
    return get_sector_from_name(pos)


# Get a list of fragments from an input sector name
# e.g. "Dryau Aowsy" --> ["Dry","au","Ao","wsy"]
def get_fragments(sector_name, allow_long = False):
  sector_name = sector_name.replace(' ', '')
  segments = []
  current_str = sector_name
  while len(current_str) > 0:
    found = False
    for frag in pgdata.cx_fragments:
      if current_str[0:len(frag)] == frag:
        segments.append(frag)
        current_str = current_str[len(frag):]
        found = True
        break
    if not found:
      break
  if len(current_str) == 0 and (allow_long or len(segments) <= _expected_fragment_limit):
    return segments
  else:
    return None


# Mild weakness: due to the way get_fragments works, this currently ignores all spaces
# This means that names like "Synoo kio" are considered valid
def is_valid_name(input):
  frags = get_fragments(input) if util.is_str(input) else frags
  if frags is None or len(frags) == 0 or frags[0] not in pgdata.cx_prefixes:
    return False
  if len(frags) == 4 and frags[2] in pgdata.cx_prefixes:
    # Class 2
    f1idx = pgdata.c2_prefix_suffix_override_map.get(frags[0], 1)
    f3idx = pgdata.c2_prefix_suffix_override_map.get(frags[2], 1)
    return (frags[1] in pgdata.c2_suffixes[f1idx] and frags[3] in pgdata.c2_suffixes[f3idx])
  elif len(frags) in [3,4]:
    # Class 1
    fli_idx = pgdata.c1_prefix_infix_override_map.get(frags[0], 1)
    if frags[1] not in pgdata.c1_infixes[fli_idx]:
      return False
    if len(frags) == 4:
      fli_idx = 2 if fli_idx == 1 else 1
      if frags[2] not in pgdata.c1_infixes[fli_idx]:
        return False
    flastidx = 2 if fli_idx == 1 else 1
    return (frags[-1] in pgdata.c1_suffixes[flastidx])
  else:
    # Class NOPE
    return False


# Format a given set of fragments into a full name
def format_name(frags):
  frags = get_fragments(input) if util.is_str(input) else frags
  if frags is None:
    return None
  if len(frags) == 4 and frags[2] in pgdata.cx_prefixes:
    return "{0}{1} {2}{3}".format(*frags)
  else:
    return "".join(frags)


# Get the class of the sector
# e.g. Froawns = 1, Froadue = 1, Eos Aowsy = 2
def get_sector_class(sect):
  frags = get_fragments(sect) if util.is_str(sect) else sect
  if frags is None:
    return None
  if frags[2] in pgdata.cx_prefixes:
    return 2
  else:
    return 1


# Return the next prefix in the list, wrapping if necessary
def get_next_prefix(prefix):
  return pgdata.cx_prefixes[(pgdata.cx_prefixes.index(prefix) + 1) % len(pgdata.cx_prefixes)]


# Get the full list of suffixes for a given set of fragments missing a suffix
# e.g. "Dryau Ao", "Ogair", "Wreg"
def get_suffixes(input, get_all = False):
  frags = get_fragments(input) if util.is_str(input) else input
  if frags is None:
    return None
  wordstart = frags[0]
  if frags[-1] in pgdata.cx_prefixes:
    # Append suffix straight onto a prefix (probably C2)
    suffix_map_idx = pgdata.c2_prefix_suffix_override_map.get(frags[-1], 1)
    result = pgdata.c2_suffixes[suffix_map_idx]
    wordstart = frags[-1]
  else:
    # Likely C1
    if frags[-1] in pgdata.c1_infixes[2]:
      # Last infix is consonant-ish, return the vowel-ish suffix list
      result = pgdata.c1_suffixes[1]
    else:
      result = pgdata.c1_suffixes[2]
  
  if get_all:
    return result
  else:
    return result[0 : get_prefix_run_length(wordstart)]


# Get the full list of infixes for a given set of fragments missing an infix
# e.g. "Ogai", "Wre", "P"
def c1_get_infixes(input):
  frags = get_fragments(input) if util.is_str(input) else input
  if frags is None:
    return None
  if frags[-1] in pgdata.cx_prefixes:
    if frags[-1] in pgdata.c1_prefix_infix_override_map:
      return pgdata.c1_infixes[pgdata.c1_prefix_infix_override_map[frags[-1]]]
    else:
      return pgdata.c1_infixes[1]
  elif frags[-1] in pgdata.c1_infixes[1]:
    return pgdata.c1_infixes[2]
  elif frags[-1] in pgdata.c1_infixes[2]:
    return pgdata.c1_infixes[1]
  else:
    return None


# Get the specified prefix's run length (e.g. Th => 35, Tz => 1)
def get_prefix_run_length(frag):
  return pgdata.cx_prefix_length_overrides.get(frag, pgdata.cx_prefix_length_default)


# Get the specified infix's run length
def c1_get_infix_run_length(frag):
  if frag in pgdata.c1_infixes_s1:
    def_len = pgdata.c1_infix_s1_length_default
  else:
    def_len = pgdata.c1_infix_s2_length_default
  return pgdata.c1_infix_length_overrides.get(frag, def_len)


# Get the total run length for the series of infixes the input is part of
def c1_get_infix_total_run_length(frag):
  if frag in pgdata.c1_infixes_s1:
    return pgdata.c1_infix_s1_total_run_length
  else:
    return pgdata.c1_infix_s2_total_run_length


# Given a full system name, get its approximate coordinates
def get_coords_from_name(system_name):
  m = pgdata.pg_system_regex.match(system_name)
  if m is None:
    return (None, None)
  sector_name = m.group("sector")
  # Get the absolute position of the sector
  sect = get_sector_from_name(sector_name)
  abs_pos = sect.origin
  # Get the relative position of the star within the sector
  # Also get the +/- error bounds
  rel_pos, rel_pos_error = get_star_relpos(*m.group("prefix", "centre", "suffix", "lcode", "number1", "number2"))

  if abs_pos is not None and rel_pos is not None:
    return (abs_pos + rel_pos, rel_pos_error)
  else:
    return (None, None)


# Given a sector name, get a sector object representing it
def get_sector_from_name(sector_name):
  frags = get_fragments(sector_name) if util.is_str(sector_name) else sector_name
  if frags is None:
    return None
  
  sc = get_sector_class(frags)
  if sc == 2:
    # Class 2: get matching YZ candidates, do full runs through them to find a match
    for candidate in c2_get_yz_candidates(frags[0], frags[2]):
      for idx, testfrags in c2_get_run(candidate['frags']):
        if testfrags == frags:
          return sector.Sector(idx, candidate['y'], candidate['z'], format_name(frags))
    return None
  elif sc is not None:
    # Class 1: calculate and return
    return c1_get_sector(frags)


# Get all YZ-constrained lines which could possibly contain the prefixes specified
# Note that multiple lines can (and often do) match, this is filtered later
def c2_get_yz_candidates(frag0, frag2):
  if (frag0, frag2) in _c2_candidate_cache:
    for candidate in _c2_candidate_cache[(frag0, frag2)]:
      yield {'frags': list(candidate['frags']), 'y': candidate['y'], 'z': candidate['z']}


# Get the name of a class 2 sector based on its position
def c2_get_name(sector):
  # Get run start from YZ
  (pre0, suf0), (pre1, suf1) = _c2_start_points[sector.index[2]][sector.index[1]]
  # Now do a full run across it until we reach the right x position
  for (xpos, frags) in c2_get_run([pre0, suf0, pre1, suf1]):
    if xpos == sector.x:
      return frags
  return None


# Get the zero-based offset (counting from bottom-left of the galaxy) of the input sector
def c1_get_offset(input):
  frags = get_fragments(input) if util.is_str(input) else input
  if frags is None:
    return None

  sufs = get_suffixes(frags[0:-1], True)
  suf_len = len(sufs)
  
  # Add the total length of all the infixes we've already passed over
  if len(frags) > 3:
    # We have a 4-phoneme name, which means we have to handle adjusting our "coordinates"
    # from individual suffix runs up to fragment3 runs and then to fragment2 runs
    
    # STEP 1: Acquire the offset for suffix runs, and adjust it
    suf_offset = sufs.index(frags[-1])
    # Check which fragment3 run we're on, and jump us up by that many total run lengths if not the first
    suf_offset += (sufs.index(frags[-1]) // c1_get_infix_run_length(frags[2])) * c1_get_infix_total_run_length(frags[2])
    
    # STEP 2: Take our current offset from "suffix space" to "fragment3 space"
    # Divide by the current fragment3's run length
    # Remember the offset that we're at on the current suffix-run
    f3_offset, f3_offset_mod = divmod(suf_offset, c1_get_infix_run_length(frags[2]))
    # Multiply by the total run length for this series of fragment3s
    f3_offset *= c1_get_infix_total_run_length(frags[2])
    # Reapply the f3 offset from earlier
    f3_offset += f3_offset_mod
    # Add the offset of the current fragment3, to give us our overall position in the f3-sequence
    f3_offset += _c1_infix_offsets[frags[2]][0]
   
    # STEP 3: Take our current offset from "fragment3 space" to "fragment2 space"
    # Divide by the current fragment2's run length
    # Remember the offset that we're at on the current f3-run
    f2_offset, f2_offset_mod = divmod(f3_offset, c1_get_infix_run_length(frags[1]))
    # Multiply by the total run length for this series of fragment2s
    f2_offset *= c1_get_infix_total_run_length(frags[1])
    # Reapply the f2 offset from earlier
    f2_offset += f2_offset_mod
    # Add the offset of the current fragment2, to give us our overall position in the f2-sequence
    f2_offset += _c1_infix_offsets[frags[1]][0]
    
    # Set this as the global offset to be manipulated by the prefix step
    offset = f2_offset
  else:
    # We have a 3-phoneme name, which means we just have to adjust our coordinates
    # from "suffix space" to "fragment2 space" (since there is no fragment3)
    
    # STEP 1: Acquire the offset for suffix runs, and adjust it
    suf_offset = sufs.index(frags[-1])
    
    # STEP 2: Take our current offset from "suffix space" to "fragment2 space"
    # Divide by the current fragment2's run length
    # Remember the offset we're at on the current suffix-run
    f2_offset, f2_offset_mod = divmod(suf_offset, c1_get_infix_run_length(frags[1]))
    # Multiply by the total run length for this series of fragment2s
    f2_offset *= c1_get_infix_total_run_length(frags[1])
    # Reapply the f2 offset from earlier
    f2_offset += f2_offset_mod
    # Add the offset of the current fragment2, to give us our overall position in the f2-sequence
    f2_offset += _c1_infix_offsets[frags[1]][0]
    
    # Set this as the global offset to be manipulated by the prefix step
    offset = f2_offset

  # Divide by the current prefix's run length, this is now how many iterations of the full 3037 we should have passed over
  # Also remember the current offset's position within a prefix run
  offset, offset_mod = divmod(offset, get_prefix_run_length(frags[0]))
  # Subtract one because ... I have no idea right now, because it works, just subtract one
  offset -= 1

  # Now multiply by the total run length (3037) to get the actual offset of this run
  offset *= pgdata.cx_prefix_total_run_length
  # Add the infixes/suffix's position within this prefix's part of the overall prefix run
  offset += offset_mod
  # Subtract a magic number, "Just 'Cause!"
  offset -= pgdata.c1_arbitrary_index_offset
  # Add the base position of this prefix within the run
  offset += _c1_prefix_offsets[frags[0]][0]
  # Whew!
  return offset


# Get the sector position of the given input class 1 sector name
def c1_get_sector(input):
  frags = get_fragments(input) if util.is_str(input) else input
  if frags is None:
    return None
  offset = c1_get_offset(frags)
  if offset is None:
    return None

  # Calculate the X/Y/Z positions from the offset
  x = (offset % pgdata.c1_galaxy_size[0])
  y = (offset // pgdata.c1_galaxy_size[0]) % pgdata.c1_galaxy_size[1]
  z = (offset // (pgdata.c1_galaxy_size[0] * pgdata.c1_galaxy_size[1])) % pgdata.c1_galaxy_size[2]
  # Put it in "our" coordinate space
  x -= sector.base_sector_coords[0]
  y -= sector.base_sector_coords[1]
  z -= sector.base_sector_coords[2]
  return sector.Sector(x, y, z, input)


def c1_get_name(sector):
  if sector is None:
    return None
  offset  = sector.index[2] * pgdata.c1_galaxy_size[1] * pgdata.c1_galaxy_size[0]
  offset += sector.index[1] * pgdata.c1_galaxy_size[0]
  offset += sector.index[0]
  
  prefix_cnt, cur_offset = divmod(offset + pgdata.c1_arbitrary_index_offset, pgdata.cx_prefix_total_run_length)
  prefix = [c for c in _c1_prefix_offsets if cur_offset >= _c1_prefix_offsets[c][0] and cur_offset < (_c1_prefix_offsets[c][0] + _c1_prefix_offsets[c][1])][0]
  cur_offset -= _c1_prefix_offsets[prefix][0]
  
  infix1s = c1_get_infixes([prefix])
  infix1_total_len = c1_get_infix_total_run_length(infix1s[0])
  infix1_cnt, cur_offset = divmod(prefix_cnt * get_prefix_run_length(prefix) + cur_offset + pgdata.c1_arbitrary_index_offset, infix1_total_len)
  infix1 = [c for c in _c1_infix_offsets if c in infix1s and cur_offset >= _c1_infix_offsets[c][0] and cur_offset < (_c1_infix_offsets[c][0] + _c1_infix_offsets[c][1])][0]
  cur_offset -= _c1_infix_offsets[infix1][0]
  
  infix1_run_len = c1_get_infix_run_length(infix1)
  sufs = get_suffixes([prefix, infix1], True)
  next_idx = (infix1_run_len * infix1_cnt) + cur_offset
  
  frags = [prefix, infix1]
  
  if next_idx >= len(sufs):
    # 4-phoneme
    infix2s = c1_get_infixes(frags)
    infix2_total_len = c1_get_infix_total_run_length(infix2s[0])
    infix2_cnt, cur_offset = divmod(infix1_cnt * c1_get_infix_run_length(infix1) + cur_offset, infix2_total_len)
    infix2 = [c for c in _c1_infix_offsets if c in infix2s and cur_offset >= _c1_infix_offsets[c][0] and cur_offset < (_c1_infix_offsets[c][0] + _c1_infix_offsets[c][1])][0]
    cur_offset -= _c1_infix_offsets[infix2][0]
    
    infix2_run_len = c1_get_infix_run_length(infix2)
    sufs = get_suffixes([prefix, infix1, infix2], True)
    next_idx = (infix2_run_len * infix2_cnt) + cur_offset
    
    frags.append(infix2)

  frags.append(sufs[next_idx])
  return frags
  

# Get a full run of class 2 system names
# The input MUST be the start point (at c2_run_states[0]), or it'll be wrong
def c2_get_run(input, length = None):
  frags = get_fragments(input) if util.is_str(input) else input
  if frags is None:
    return

  # Get the initial suffix list
  suffixes_0_temp = get_suffixes(frags[0:1])
  suffixes_1_temp = get_suffixes(frags[-2:-1])
  suffixes_0 = [(frags[0], f1) for f1 in suffixes_0_temp[suffixes_0_temp.index(frags[1]):]]
  suffixes_1 = [(frags[2], f3) for f3 in suffixes_1_temp[suffixes_1_temp.index(frags[3]):]]

  if length is None:
    length = pgdata.c2_galaxy_size[0]
  
  for i in range(0, length):
    # Calculate the run state indexes for phonemes 1 and 3
    idx0 = i % len(pgdata.c2_run_states)
    idx1 = i % len(pgdata.c2_run_states)
    
    # Calculate the current base index
    # (in case we've done a full run and are onto the next set of phonemes)
    cur_base_0 = int(i // len(pgdata.c2_run_states)) * pgdata.c2_run_step
    cur_base_1 = 0
    
    # Ensure we have all the suffixes we need, and append the next set if not
    if (cur_base_0 + pgdata.c2_run_states[idx0][0]) >= len(suffixes_0):
      next_prefix0_idx = pgdata.cx_prefixes.index(suffixes_0[-1][0]) + 1
      next_prefix0 = pgdata.cx_prefixes[next_prefix0_idx % len(pgdata.cx_prefixes)]
      suffixes_0 += [(next_prefix0, f1) for f1 in get_suffixes([next_prefix0])]
    if (cur_base_1 + pgdata.c2_run_states[idx1][1]) >= len(suffixes_1):
      next_prefix1_idx = pgdata.cx_prefixes.index(suffixes_1[-1][0]) + 1
      next_prefix1 = pgdata.cx_prefixes[next_prefix1_idx % len(pgdata.cx_prefixes)]
      suffixes_1 += [(next_prefix1, f3) for f3 in get_suffixes([next_prefix1])]
    
    # Set current fragments
    frags[0], frags[1] = suffixes_0[cur_base_0 + pgdata.c2_run_states[idx0][0]]
    frags[2], frags[3] = suffixes_1[cur_base_1 + pgdata.c2_run_states[idx1][1]]
    
    yield (i - sector.base_sector_coords[0], frags)


# Get all prefix combinations present in a particular run
def c2_get_run_prefixes(input):
  prefixes = []
  for xpos, frags in c2_get_run(input):
    if (frags[0], frags[2]) not in prefixes:
      prefixes.append((frags[0], frags[2]))
  return prefixes


# Get all the C2 "start points" - sector names at the starts of runs
def c2_get_start_points(limit = 1248):
  base_idx0 = 0
  base_idx1 = 0
  count = 0
  while count < limit:
    for (ors0, ors1) in pgdata.c2_vouter_states:
      for (oos0, oos1) in pgdata.c2_vouter_states:
        for (os0, os1) in pgdata.c2_outer_states:
          cur_idx0 = base_idx0 + (ors0 * pgdata.c2_vouter_diff) + (oos0 * pgdata.c2_outer_diff) + (os0 * pgdata.c2_run_diff)
          cur_idx1 = base_idx1 + (ors1 * pgdata.c2_vouter_diff) + (oos1 * pgdata.c2_outer_diff) + (os1 * pgdata.c2_run_diff)
          yield (_prefix_runs[cur_idx0], _prefix_runs[cur_idx1])
          count += 1
          if count >= limit:
            return
    # One more layer out...
    base_idx0 += pgdata.c2_full_vouter_step * pgdata.c2_vouter_step
    base_idx1 += pgdata.c2_full_vouter_step * pgdata.c2_vouter_step
    

# Cache to support faster repeat querying
_c2_candidate_cache = {}
# Constructs a cache to speed up later searching for YZ candidates
def _construct_c2_candidate_cache():
  global _c2_candidate_cache
  # For each Z slice...
  for z in range(len(_c2_start_points)):
    # For each Y stack...
    for y in range(len(_c2_start_points[z])):
      # Get the correct starting fragments, check they aren't blank
      f0, f1 = _c2_start_points[z][y][0]
      f2, f3 = _c2_start_points[z][y][1]
      # Get all run prefixes present, and store that they're in this YZ-constrained line
      prefixes = c2_get_run_prefixes([f0, f1, f2, f3])
      for pf in prefixes:
        if pf not in _c2_candidate_cache:
          _c2_candidate_cache[pf] = []
        _c2_candidate_cache[pf].append({'frags': [f0, f1, f2, f3], 'y': y - sector.base_sector_coords[1], 'z': z - sector.base_sector_coords[2]})

# Cache all valid prefix/suffix combinations for later querying
_prefix_runs = []
def _construct_prefix_run_cache():
  global _prefix_runs
  _prefix_runs = [(p, suf) for p in pgdata.cx_prefixes for suf in get_suffixes([p])]

# Cache all starting fragments to support the candidate cache
_c2_start_points = [[None for _ in range(pgdata.c2_galaxy_size[1])] for _ in range(pgdata.c2_galaxy_size[2])]
def _construct_c2_start_point_cache():
  global _c2_start_points
  y = 0
  z = 0
  for w in c2_get_start_points():
    _c2_start_points[z][y] = w
    y += 1
    if y >= pgdata.c2_galaxy_size[1]:
      y = 0
      z += 1

# Cache the run offsets of all prefixes and C1 infixes
_c1_prefix_offsets = {}
_c1_infix_offsets = {}
def _construct_c1_offsets():
  global _c1_prefix_offsets, _c1_infix_offsets
  cnt = 0
  for p in pgdata.cx_prefixes:
    plen = get_prefix_run_length(p)
    _c1_prefix_offsets[p] = (cnt, plen)
    cnt += plen
  cnt = 0
  for i in pgdata.c1_infixes_s1:
    ilen = c1_get_infix_run_length(i)
    _c1_infix_offsets[i] = (cnt, ilen)
    cnt += ilen
  cnt = 0
  for i in pgdata.c1_infixes_s2:
    ilen = c1_get_infix_run_length(i)
    _c1_infix_offsets[i] = (cnt, ilen)
    cnt += ilen
  
# Initialisation
_init_start = time.clock()
_construct_prefix_run_cache()
_construct_c2_start_point_cache()
_construct_c2_candidate_cache()
_construct_c1_offsets()
_init_time = time.clock() - _init_start