from __future__ import print_function, division
import logging
import math
import string
import sys
import time

import pgdata
import sector
import system
import util
import vector3

app_name = "pgnames"
log = logging.getLogger(app_name)

###
# Publicly-useful functions
###

"""
Get the name of a sector that a position falls within.

Args:
  pos: A Vector3 position
  format_output: Whether or not to format the output or return it as fragments
  
Returns:
  The name of the sector which contains the input position, either as a string or as a list of fragments
"""  
def get_sector_name(pos, allow_ha=True, format_output=True):
  if allow_ha:
    ha_name = _ha_get_name(pos)
    if ha_name is not None:
      return ha_name
  offset = _c1_get_offset(pos)
  if _get_c1_or_c2(offset) == 1:
    output = _c1_get_name(pos)
  else:
    output = _c2_get_name(pos)
  
  if format_output:
    return format_name(output)
  else:
    return output


"""
Get a Sector object represented by a name, or which a position falls within.

Args:
  input: A sector name, or a Vector3 position
  allow_ha: Whether to include hand-authored sectors in the search
  get_name: Whether to look up the name of the sector

Returns:
  A Sector object, or None if the input could not be looked up
"""
def get_sector(input, allow_ha = True, get_name = True):
  if isinstance(input, vector3.Vector3):
    if allow_ha:
      ha_name = _ha_get_name(input)
      if ha_name is not None:
        return pgdata.ha_sectors[ha_name.lower()]
    # If we're not checking HA or it's not in such a sector, do PG
    x = (input.x - sector.base_coords.x) // sector.cube_size
    y = (input.y - sector.base_coords.y) // sector.cube_size
    z = (input.z - sector.base_coords.z) // sector.cube_size
    # Get the name, if we are
    frags = None
    if get_name:
      frags = get_sector_name(input, allow_ha=allow_ha, format_output=False)
    # We don't authoritatively know the name, so return it without one
    return sector.PGSector(int(x), int(y), int(z), format_name(frags), _get_sector_class(frags))
  else:
    # Assume we have a string, call down to get it by name
    return get_sector_from_name(input, allow_ha=allow_ha)


"""
Get a system's name based on its position

Args:
  input: The system's Vector3 position
  mcode: The system's mass code ('a'-'h')

Returns:
  A system name, missing the final number ("number2")
"""
def get_system_name_from_pos(input, mcode):
  psect = get_sector(input, allow_ha=True)
  # Get cube width for this mcode, and the sector origin
  cwidth = _get_mcode_cube_width(mcode)
  psorig = psect.get_origin(cwidth)
  # Get the relative inputition within this sector and the system identifier
  relpos = vector3.Vector3(input.x - psorig.x, input.y - psorig.y, input.z - psorig.z)
  sysid = _get_sysid_from_relpos(relpos, mcode, format_output=True)
  return "{} {}".format(psect.name, sysid)


"""
Get a System object based on its name

Args:
  input: The system's name

Returns:
  A System object
"""
def get_system_from_name(input):
  coords, uncertainty = get_coords_from_name(input)
  return system.PGSystem(coords.x, coords.y, coords.z, uncertainty=uncertainty, name=get_canonical_name(input), sector=get_sector(coords))


"""
Given a sector name, get a sector object representing it

Args:
  raw_sector_name: The name of the sector

Returns:
  A Sector object
"""
def get_sector_from_name(raw_sector_name, allow_ha = True):
  sector_name = get_canonical_name(raw_sector_name, sector_only=True)
  if sector_name is None:
    return None
  if allow_ha and util.is_str(sector_name) and sector_name.lower() in pgdata.ha_sectors:
    return pgdata.ha_sectors[sector_name.lower()]
  else:
    frags = get_fragments(sector_name) if util.is_str(sector_name) else sector_name
    if frags is None:
      return None
    
    sc = _get_sector_class(frags)
    if sc == 2:
      # Class 2: get matching YZ candidates, do full runs through them to find a match
      for candidate in _c2_get_yz_candidates(frags[0], frags[2]):
        for idx, testfrags in _c2_get_run(candidate['frags']):
          if testfrags == frags:
            return sector.PGSector(idx, candidate['y'], candidate['z'], format_name(frags), 2)
      return None
    elif sc == 1:
      # Class 1: calculate and return
      return _c1_get_sector(frags)
    else:
      return None


"""
Given a full system name, get its approximate coordinates

Args:
  raw_system_name: A full system name

Returns:
  A (Vector3, Number) tuple of the approximate coordinates and the uncertainty per axis
"""
def get_coords_from_name(raw_system_name):
  system_name = get_canonical_name(raw_system_name)
  if system_name is None:
    return (None, None)
  # Reparse it now it's (hopefully) right
  m = pgdata.pg_system_regex.match(system_name)
  if m is None:
    return (None, None)
  sector_name = m.group("sector")
  sect = get_sector_from_name(sector_name)
  if sect is None:
    return (None, None)
  # Get the absolute position of the sector
  abs_pos = sect.get_origin(_get_mcode_cube_width(m.group("mcode")))
  # Get the relative position of the star within the sector
  # Also get the +/- error bounds
  rel_pos, rel_pos_error = _get_relpos_from_sysid(*m.group("prefix", "centre", "suffix", "mcode", "number1", "number2"))

  if abs_pos is not None and rel_pos is not None:
    return (abs_pos + rel_pos, rel_pos_error)
  else:
    return (None, None)
    

"""
Get the correctly-cased name for a given sector or system name

Args:
  name: A system or sector name, in any case

Returns:
  The input system/sector name with its case corrected
"""
def get_canonical_name(name, sector_only = False):
  sectname = None
  sysid = None

  # See if we have a full system name
  m = pgdata.pg_system_regex.match(name)
  if m is not None:
    sectname_raw = m.group("sector")
  else:
    sectname_raw = name

  # Check if this sector name appears in ha_sectors, pass it through the fragment process if not
  if sectname_raw.lower() in pgdata.ha_sectors:
    sectname = pgdata.ha_sectors[sectname_raw.lower()].name
  else:
    # get_fragments converts to Title Case, so we don't need to
    frags = get_fragments(sectname_raw)
    if frags is not None:
      sectname = format_name(frags)

  if sector_only:
    return sectname

  # Work out what we should be returning, and do it
  if m is not None and sectname is not None:
    if m.group("number1") is not None and int(m.group("number1")) != 0:
      sysid = "{}{}-{} {}{}-{}".format(m.group("prefix").upper(), m.group("centre").upper(), m.group("suffix").upper(), m.group("mcode").lower(), m.group("number1"), m.group("number2"))
    else:
      sysid = "{}{}-{} {}{}".format(m.group("prefix").upper(), m.group("centre").upper(), m.group("suffix").upper(), m.group("mcode").lower(), m.group("number2"))
    return "{} {}".format(sectname, sysid)
  else:
    # This may be none if get_fragments/format_name failed
    return sectname


"""
Get a list of fragments from an input sector name
e.g. "Dryau Aowsy" --> ["Dry","au","Ao","wsy"]

Args:
  sector_name: The name of the sector
  allow_long: Whether to allow sector names longer than the usual maximum fragment count (4)

Returns:
  A list of fragments representing the sector name
"""
def get_fragments(sector_name, allow_long = False):
  # Convert the string to Title Case, then remove spaces
  sector_name = sector_name.title().replace(' ', '')
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


"""
Checks whether or not the provided sector name is a valid PG name

Mild weakness: due to the way get_fragments works, this currently ignores all spaces
This means that names like "Synoo kio" are considered valid

Args:
  input: A candidate sector name

Returns:
  True if the sector name is valid, False if not
"""
def is_valid_sector_name(input):
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


"""
Format a given set of fragments into a full name

Args:
  frags: A list of sector name fragments

Returns:
  The sector name as a string
"""
def format_name(input):
  frags = get_fragments(input) if util.is_str(input) else input
  if frags is None:
    return None
  if len(frags) == 4 and frags[2] in pgdata.cx_prefixes:
    return "{0}{1} {2}{3}".format(*frags)
  else:
    return "".join(frags)


###
# Internal variables
###

_srp_divisor1 = len(string.ascii_uppercase)
_srp_divisor2 = _srp_divisor1**2
_srp_divisor3 = _srp_divisor1**3
_srp_rowlength = 128
_srp_sidelength = _srp_rowlength**2
_expected_fragment_limit = 4


###
# Internal functions: shared/HA
###

def _get_mcode_cube_width(mcode):
  return sector.cube_size / pow(2, ord('h') - ord(mcode.lower()))


# Get a system's relative position within a sector
# Original version by Kay Johnston (CMDR Jackie Silver)
# Note that in the form "Sector AB-C d3", the "3" is number2, NOT number1 (which is 0)
def _get_relpos_from_sysid(prefix, centre, suffix, mcode, number1, number2):
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

  cubeside = _get_mcode_cube_width(mcode.lower())
  halfwidth = cubeside / 2

  approx_x = (column * cubeside) + halfwidth
  approx_y = (stack  * cubeside) + halfwidth
  approx_z = (row    * cubeside) + halfwidth
  
  if (approx_x < 0 or approx_x > sector.cube_size
   or approx_y < 0 or approx_y > sector.cube_size
   or approx_z < 0 or approx_z > sector.cube_size):
    input_star = "{0}{1}-{2} {3}{4}".format(
      prefix, centre, suffix, mcode, "{0}-{1}".format(number1, number2) if int(number1) > 0 else number2)
    log.error("System relpos calculation produced invalid result [{0},{1},{2}] for input '{3}'".format(approx_x, approx_y, approx_z, input_star))

  return (vector3.Vector3(approx_x,approx_y,approx_z), halfwidth)


def _get_sysid_from_relpos(pos, mcode, format_output=False):
  cubeside = _get_mcode_cube_width(mcode.lower())
  column = int(pos.x // cubeside)
  stack  = int(pos.y // cubeside)
  row    = int(pos.z // cubeside)

  position = column + (_srp_rowlength * stack) + (_srp_sidelength * row)

  prefixn = int((position)                  % len(string.ascii_uppercase))
  centren = int((position // _srp_divisor1) % len(string.ascii_uppercase))
  suffixn = int((position // _srp_divisor2) % len(string.ascii_uppercase))
  number1 = int((position // _srp_divisor3))

  prefix = string.ascii_uppercase[prefixn]
  centre = string.ascii_uppercase[centren]
  suffix = string.ascii_uppercase[suffixn]

  if format_output:
    output = '{}{}-{} {}'.format(prefix, centre, suffix, mcode)
    if number1 != 0:
      output += '{}-'.format(number1)
    return output
  else:
    return [prefix, centre, suffix, mcode, number1]


# Get the class of the sector from its name
# e.g. Froawns = 1, Froadue = 1, Eos Aowsy = 2
def _get_sector_class(sect):
  if util.is_str(sect) and sect.lower() in pgdata.ha_sectors:
    return "ha"
  frags = get_fragments(sect) if util.is_str(sect) else sect
  if frags is not None and len(frags) == 4 and frags[0] in pgdata.cx_prefixes and frags[2] in pgdata.cx_prefixes:
    return 2
  elif frags is not None and len(frags) in [3,4] and frags[0] in pgdata.cx_prefixes:
    return 1
  else:
    return None


# Get the full list of suffixes for a given set of fragments missing a suffix
# e.g. "Dryau Ao", "Ogair", "Wreg"
def _get_suffixes(input, get_all = False):
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
    return result[0 : _get_prefix_run_length(wordstart)]


# Get the specified prefix's run length (e.g. Th => 35, Tz => 1)
def _get_prefix_run_length(frag):
  return pgdata.cx_prefix_length_overrides.get(frag, pgdata.cx_prefix_length_default)


# Determines whether a given sector should be C1 or C2
def _get_c1_or_c2(key):
  # Add the offset we subtract to make the normal positions make sense
  key += pgdata.c1_arbitrary_index_offset
  # 32-bit hashing algorithm found at http://papa.bretmulvey.com/post/124027987928/hash-functions
  # Seemingly originally by Bob Jenkins <bob_jenkins-at-burtleburtle.net> in the 1990s
  key += (key << 12)
  key &= 0xFFFFFFFF
  key ^= (key >> 22)
  key += (key << 4)
  key &= 0xFFFFFFFF
  key ^= (key >> 9)
  key += (key << 10)
  key &= 0xFFFFFFFF
  key ^= (key >> 2)
  key += (key << 7)
  key &= 0xFFFFFFFF
  key ^= (key >> 12)
  # Key is now an even/odd number, depending on which scheme we use
  # Return 1 for a class 1 sector, 2 for a class 2
  return (key % 2) + 1


# Get which HA sector this position would be part of, if any
def _ha_get_name(pos):
  for (sname, s) in pgdata.ha_sectors.items():
    if s.contains(pos):
      return s.name
  return None


##
# Internal functions: c1-specific
##

# Get the full list of infixes for a given set of fragments missing an infix
# e.g. "Ogai", "Wre", "P"
def _c1_get_infixes(input):
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


# Get the specified infix's run length
def _c1_get_infix_run_length(frag):
  if frag in pgdata.c1_infixes_s1:
    def_len = pgdata.c1_infix_s1_length_default
  else:
    def_len = pgdata.c1_infix_s2_length_default
  return pgdata.c1_infix_length_overrides.get(frag, def_len)


# Get the total run length for the series of infixes the input is part of
def _c1_get_infix_total_run_length(frag):
  if frag in pgdata.c1_infixes_s1:
    return pgdata.c1_infix_s1_total_run_length
  else:
    return pgdata.c1_infix_s2_total_run_length


# Get the sector offset of a position
def _c1_get_offset_from_pos(pos):
  sect = get_sector(pos, allow_ha=False, get_name=False) if not isinstance(pos, sector.PGSector) else pos
  offset  = sect.index[2] * pgdata.c1_galaxy_size[1] * pgdata.c1_galaxy_size[0]
  offset += sect.index[1] * pgdata.c1_galaxy_size[0]
  offset += sect.index[0]
  return offset


# Get the zero-based offset (counting from bottom-left of the galaxy) of the input sector name/position
def _c1_get_offset(input):
  if isinstance(input, vector3.Vector3):
    return _c1_get_offset_from_pos(input)
  else:
    return _c1_get_offset_from_name(input)

def _c1_get_offset_from_name(input):
  frags = get_fragments(input) if util.is_str(input) else input
  if frags is None:
    return None

  sufs = _get_suffixes(frags[0:-1], True)
  suf_len = len(sufs)
  
  # Add the total length of all the infixes we've already passed over
  if len(frags) > 3:
    # We have a 4-phoneme name, which means we have to handle adjusting our "coordinates"
    # from individual suffix runs up to fragment3 runs and then to fragment2 runs
    
    # STEP 1: Acquire the offset for suffix runs, and adjust it
    suf_offset = sufs.index(frags[-1])
    # Check which fragment3 run we're on, and jump us up by that many total run lengths if not the first
    suf_offset += (sufs.index(frags[-1]) // _c1_get_infix_run_length(frags[2])) * _c1_get_infix_total_run_length(frags[2])
    
    # STEP 2: Take our current offset from "suffix space" to "fragment3 space"
    # Divide by the current fragment3's run length
    # Remember the offset that we're at on the current suffix-run
    f3_offset, f3_offset_mod = divmod(suf_offset, _c1_get_infix_run_length(frags[2]))
    # Multiply by the total run length for this series of fragment3s
    f3_offset *= _c1_get_infix_total_run_length(frags[2])
    # Reapply the f3 offset from earlier
    f3_offset += f3_offset_mod
    # Add the offset of the current fragment3, to give us our overall position in the f3-sequence
    f3_offset += _c1_infix_offsets[frags[2]][0]
   
    # STEP 3: Take our current offset from "fragment3 space" to "fragment2 space"
    # Divide by the current fragment2's run length
    # Remember the offset that we're at on the current f3-run
    f2_offset, f2_offset_mod = divmod(f3_offset, _c1_get_infix_run_length(frags[1]))
    # Multiply by the total run length for this series of fragment2s
    f2_offset *= _c1_get_infix_total_run_length(frags[1])
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
    f2_offset, f2_offset_mod = divmod(suf_offset, _c1_get_infix_run_length(frags[1]))
    # Multiply by the total run length for this series of fragment2s
    f2_offset *= _c1_get_infix_total_run_length(frags[1])
    # Reapply the f2 offset from earlier
    f2_offset += f2_offset_mod
    # Add the offset of the current fragment2, to give us our overall position in the f2-sequence
    f2_offset += _c1_infix_offsets[frags[1]][0]
    
    # Set this as the global offset to be manipulated by the prefix step
    offset = f2_offset

  # Divide by the current prefix's run length, this is now how many iterations of the full 3037 we should have passed over
  # Also remember the current offset's position within a prefix run
  offset, offset_mod = divmod(offset, _get_prefix_run_length(frags[0]))
  # Subtract one because ... I have no idea right now, because it works, just subtract one

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
def _c1_get_sector(input):
  frags = get_fragments(input) if util.is_str(input) else input
  if frags is None:
    return None
  offset = _c1_get_offset(frags)
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
  name = format_name(frags)
  return sector.PGSector(x, y, z, format_name(frags), _get_sector_class(frags))


def _c1_get_name(pos):
  if pos is None:
    return None
  offset = _c1_get_offset(pos)

  prefix_cnt, cur_offset = divmod(offset + pgdata.c1_arbitrary_index_offset, pgdata.cx_prefix_total_run_length)
  prefix = [c for c in _c1_prefix_offsets if cur_offset >= _c1_prefix_offsets[c][0] and cur_offset < (_c1_prefix_offsets[c][0] + _c1_prefix_offsets[c][1])][0]
  cur_offset -= _c1_prefix_offsets[prefix][0]
  
  infix1s = _c1_get_infixes([prefix])
  infix1_total_len = _c1_get_infix_total_run_length(infix1s[0])
  infix1_cnt, cur_offset = divmod(prefix_cnt * _get_prefix_run_length(prefix) + cur_offset, infix1_total_len)
  infix1 = [c for c in _c1_infix_offsets if c in infix1s and cur_offset >= _c1_infix_offsets[c][0] and cur_offset < (_c1_infix_offsets[c][0] + _c1_infix_offsets[c][1])][0]
  cur_offset -= _c1_infix_offsets[infix1][0]
  
  infix1_run_len = _c1_get_infix_run_length(infix1)
  sufs = _get_suffixes([prefix, infix1], True)
  next_idx = (infix1_run_len * infix1_cnt) + cur_offset
  
  frags = [prefix, infix1]
  
  if next_idx >= len(sufs):
    # 4-phoneme
    infix2s = _c1_get_infixes(frags)
    infix2_total_len = _c1_get_infix_total_run_length(infix2s[0])
    infix2_cnt, cur_offset = divmod(infix1_cnt * _c1_get_infix_run_length(infix1) + cur_offset, infix2_total_len)
    infix2 = [c for c in _c1_infix_offsets if c in infix2s and cur_offset >= _c1_infix_offsets[c][0] and cur_offset < (_c1_infix_offsets[c][0] + _c1_infix_offsets[c][1])][0]
    cur_offset -= _c1_infix_offsets[infix2][0]
    
    infix2_run_len = _c1_get_infix_run_length(infix2)
    sufs = _get_suffixes([prefix, infix1, infix2], True)
    next_idx = (infix2_run_len * infix2_cnt) + cur_offset
    
    frags.append(infix2)

  frags.append(sufs[next_idx])
  return frags


##
# Internal functions: c2-specific
##

# Get all YZ-constrained lines which could possibly contain the prefixes specified
# Note that multiple lines can (and often do) match, this is filtered later
def _c2_get_yz_candidates(frag0, frag2):
  if (frag0, frag2) in _c2_candidate_cache:
    for candidate in _c2_candidate_cache[(frag0, frag2)]:
      yield {'frags': list(candidate['frags']), 'y': candidate['y'], 'z': candidate['z']}


# Get the name of a class 2 sector based on its position
def _c2_get_name(pos):
  sect = get_sector(pos, allow_ha=False, get_name=False) if not isinstance(pos, sector.PGSector) else pos
  # Get run start from YZ
  (pre0, suf0), (pre1, suf1) = _c2_start_points[sect.index[2]][sect.index[1]]
  # Now do a full run across it until we reach the right x position
  for (xpos, frags) in _c2_get_run([pre0, suf0, pre1, suf1]):
    if xpos == sect.x:
      return frags
  return None
  

# Get a full run of class 2 system names
# The input MUST be the start point (at c2_run_states[0]), or it'll be wrong
def _c2_get_run(input, length = None):
  frags = get_fragments(input) if util.is_str(input) else input
  if frags is None:
    return

  # Get the initial suffix list
  suffixes_0_temp = _get_suffixes(frags[0:1])
  suffixes_1_temp = _get_suffixes(frags[-2:-1])
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
      suffixes_0 += [(next_prefix0, f1) for f1 in _get_suffixes([next_prefix0])]
    if (cur_base_1 + pgdata.c2_run_states[idx1][1]) >= len(suffixes_1):
      next_prefix1_idx = pgdata.cx_prefixes.index(suffixes_1[-1][0]) + 1
      next_prefix1 = pgdata.cx_prefixes[next_prefix1_idx % len(pgdata.cx_prefixes)]
      suffixes_1 += [(next_prefix1, f3) for f3 in _get_suffixes([next_prefix1])]
    
    # Set current fragments
    frags[0], frags[1] = suffixes_0[cur_base_0 + pgdata.c2_run_states[idx0][0]]
    frags[2], frags[3] = suffixes_1[cur_base_1 + pgdata.c2_run_states[idx1][1]]
    
    yield (i - sector.base_sector_coords[0], frags)


# Get all prefix combinations present in a particular run
def _c2_get_run_prefixes(input):
  prefixes = []
  for xpos, frags in _c2_get_run(input):
    if (frags[0], frags[2]) not in prefixes:
      prefixes.append((frags[0], frags[2]))
  return prefixes


# Get all the C2 "start points" - sector names at the starts of runs
def _c2_get_start_points(limit = 1248):
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


##
# Setup functions
##

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
      prefixes = _c2_get_run_prefixes([f0, f1, f2, f3])
      for pf in prefixes:
        if pf not in _c2_candidate_cache:
          _c2_candidate_cache[pf] = []
        _c2_candidate_cache[pf].append({'frags': [f0, f1, f2, f3], 'y': y - sector.base_sector_coords[1], 'z': z - sector.base_sector_coords[2]})

# Cache all valid prefix/suffix combinations for later querying
_prefix_runs = []
def _construct_prefix_run_cache():
  global _prefix_runs
  _prefix_runs = [(p, suf) for p in pgdata.cx_prefixes for suf in _get_suffixes([p])]

# Cache all starting fragments to support the candidate cache
_c2_start_points = [[None for _ in range(pgdata.c2_galaxy_size[1])] for _ in range(pgdata.c2_galaxy_size[2])]
def _construct_c2_start_point_cache():
  global _c2_start_points
  y = 0
  z = 0
  for w in _c2_get_start_points():
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
    plen = _get_prefix_run_length(p)
    _c1_prefix_offsets[p] = (cnt, plen)
    cnt += plen
  cnt = 0
  for i in pgdata.c1_infixes_s1:
    ilen = _c1_get_infix_run_length(i)
    _c1_infix_offsets[i] = (cnt, ilen)
    cnt += ilen
  cnt = 0
  for i in pgdata.c1_infixes_s2:
    ilen = _c1_get_infix_run_length(i)
    _c1_infix_offsets[i] = (cnt, ilen)
    cnt += ilen


##
# Initialisation
##

_init_start = time.clock()
_construct_prefix_run_cache()
_construct_c2_start_point_cache()
_construct_c2_candidate_cache()
_construct_c1_offsets()
_init_time = time.clock() - _init_start
