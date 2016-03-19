#!/usr/bin/env python

from __future__ import print_function, division
import argparse
import logging
import math
import re
import sys
import time

import pgdata
import sector
import util
import vector3

app_name = "pgnames"

log = logging.getLogger(app_name)

_srp_alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
_srp_divisor = len(_srp_alphabet)
_srp_middle = _srp_divisor**2
_srp_biggest = _srp_divisor**3
_srp_rowlength = 128
_srp_sidelength = _srp_rowlength**2

# Get a star's relative position within a sector
# Original version by Jackie Silver
def get_star_relative_position(prefix, centre, suffix, lcode, number1, number2):
  position = int(number1) * _srp_biggest
  
  for letter in range(_srp_divisor):
      if _srp_alphabet[letter] == suffix:
          position += letter * _srp_middle
          
  for letter in range(_srp_divisor):
      if _srp_alphabet[letter] == centre:
          position += letter * _srp_divisor
          
  for letter in range(_srp_divisor):
      if _srp_alphabet[letter] == prefix:
          position += letter
          
  working = position

  row = int(working / _srp_sidelength)
  working = working - (row * _srp_sidelength)

  stack = int(working / _srp_rowlength)
  working = working - (stack * _srp_rowlength)

  column = working
  
  cubeside = sector.cube_size / pow(2, ord('h') - ord(lcode.lower()))
  halfwidth = cubeside / 2

  approx_x = (column * cubeside) + halfwidth
  approx_y = (stack * cubeside) + halfwidth
  approx_z = (row * cubeside) + halfwidth

  return (vector3.Vector3(approx_x,approx_y,approx_z), halfwidth)


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
def get_fragments(sector_name):
  input = sector_name.replace(' ', '')
  segments = []
  current_str = input
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
  if len(current_str) == 0:
    return segments
  else:
    return None


# Get the class of the sector
# e.g. Froawns = 1b, Froadue = 1a, Eos Aowsy = 2
def get_sector_class(sect):
  frags = get_fragments(sect) if util.is_str(sect) else sect
  if frags is None:
    return None
  if frags[2] in pgdata.cx_prefixes:
    return "2"
  elif len(frags) == 4:
    return "1a"
  else:
    return "1b"


# Return the next prefix in the list, wrapping if necessary
def get_next_prefix(prefix):
  return pgdata.cx_prefixes[(pgdata.cx_prefixes.index(prefix) + 1) % len(pgdata.cx_prefixes)]


# Get the full list of suffixes for a given set of fragments missing a suffix
# e.g. "Dryau Ao", "Ogair", "Wreg"
def get_suffixes(input):
  frags = get_fragments(input) if util.is_str(input) else input
  if frags is None:
    return None
  if frags[-1] in pgdata.cx_prefixes:
    # Append suffix straight onto a prefix (probably C2)
    suffix_map_idx = 1
    if frags[-1] in pgdata.c2_prefix_suffix_override_map:
      suffix_map_idx = pgdata.c2_prefix_suffix_override_map[frags[-1]]
    return pgdata.c2_suffixes[suffix_map_idx]
  else:
    # Likely C1
    if frags[-1] in pgdata.c1_infixes[2]:
      # Last infix is consonant-ish, return the vowel-ish suffix list
      return pgdata.c1_suffixes[1]
    else:
      # TODO: Work out how it decides which list to use
      pass


# Get the full list of infixes for a given set of fragments missing an infix
# e.g. "Ogai", "Wre", "Pue"
def c1_get_infixes(input):
  frags = get_fragments(input) if util.is_str(input) else input
  if frags is None:
    return None
  if frags[-1] in pgdata.cx_prefixes and frags[-1] in pgdata.c1_prefix_infix_override_map:
    return pgdata.c1_infixes[pgdata.c1_prefix_infix_override_map[frags[-1]]]
  elif frags[-1] in pgdata.c1_infixes[1]:
    return pgdata.c1_infixes[2]
  elif frags[-1] in pgdata.c1_infixes[2]:
    return pgdata.c1_infixes[1]
  else:
    return None


# TODO: Fix this, not currently correct
def c1_get_next_sector(sect):
  frags = get_fragments(sect) if util.is_str(sect) else sect
  if frags is None:
    return None
  suffixes = get_suffixes(frags[0:-1])
  suff_index = suffixes.index(frags[-1])
  if suff_index + 1 >= len(suffixes):
    # Last suffix, jump to next prefix unless it's in overrides
    if frags[-2] in c1_infix_rollover_overrides:
      infixes = c1_get_infixes(frags[0:-2])
      inf_index = infixes.index(frags[-2])
      if inf_index + 1 >= len(infixes):
        frags[-2] = infixes[0]
      else:
        frags[-2] = infixes[inf_index+1]
    else:
      pre_index = pgdata.cx_prefixes.index(frags[0])
      if pre_index + 1 >= len(pgdata.cx_prefixes):
        frags[0] = pgdata.cx_prefixes[0]
      else:
        frags[0] = pgdata.cx_prefixes[pre_index+1]
    frags[-1] = suffixes[0]
  else:
    frags[-1] = suffixes[suff_index+1]
  return frags


# Given a full system name, get its approximate coordinates
def get_coords_from_name(system_name):
  m = pgdata.pg_system_regex.match(system_name)
  if m is None:
    return None
  sector_name = m.group("sector")
  # Get the absolute position of the sector
  sect = get_sector_from_name(sector_name)
  abs_pos = sect.origin
  # Get the relative position of the star within the sector
  # Also get the +/- error bounds
  rel_pos, rel_pos_confidence = get_star_relative_position(*m.group("prefix", "centre", "suffix", "lcode", "number1", "number2"))

  return (abs_pos + rel_pos, rel_pos_confidence)


# Given a sector name, get a sector object representing it
def get_sector_from_name(sector_name):
  frags = get_fragments(sector_name) if util.is_str(sector_name) else sector_name
  if frags is None:
    return None
  
  sc = get_sector_class(frags)
  if sc == "2":
    # Class 2: get matching YZ candidates, do full runs through them to find a match
    for candidate in c2_get_yz_candidates(frags[0], frags[2]):
      for idx, testfrags in c2_get_run(candidate['frags']):
        if testfrags == frags:
          return sector.Sector(idx, candidate['y'], candidate['z'], "{0}{1} {2}{3}".format(*frags))
    return None
  elif sc == "1a":
    # TODO
    pass
  else:
    # TODO
    pass


# Get all YZ-constrained lines which could possibly contain the prefixes specified
# Note that multiple lines can (and often do) match, this is filtered later
def c2_get_yz_candidates(frag0, frag2):
  if (frag0, frag2) in c2_candidate_cache:
    for candidate in c2_candidate_cache[(frag0, frag2)]:
      yield {'frags': list(candidate['frags']), 'y': candidate['y'], 'z': candidate['z']}


# Convenience function to get the right suffix list for a particular suffix
def get_suffix_index(s):
  if s in pgdata.cx_suffixes_s1:
    return 1
  if s in pgdata.cx_suffixes_s2:
    return 2
  if s in pgdata.cx_suffixes_s3:
    return 3
  return None


# Get the name of a class 2 sector based on its position
def c2_get_name(sector):
  # For each set of prefix combinations going upwards in Z...
  for (pre0y0, pre1y0), idx in pgdata.get_c2_positions():
    if idx == sector.z:
      # If the Z value is correct, find the appropriate starting prefix/suffix at that Y level
      pre0, suf0 = pgdata.c2_word1_y_mapping[pre0y0][sector.y + pgdata.c2_y_mapping_offset]
      pre1, suf1 = pgdata.c2_word2_y_mapping[pre1y0][sector.y + pgdata.c2_y_mapping_offset]
      # Now do a full run across it until we reach the right x position
      for (xpos, frags) in c2_get_run([pre0, suf0, pre1, suf1]):
        if xpos == sector.x:
          return frags
  return None


# Get a full run of class 2 system names
# The input MUST be the start point (at c2_run_states[0]), or it'll be wrong
def c2_get_run(input):
  frags = get_fragments(input) if util.is_str(input) else input
  if frags is None:
    return

  # Get the initial suffix list
  suffixes_0_temp = get_suffixes(frags[0:1])
  suffixes_1_temp = get_suffixes(frags[0:-1])
  suffixes_0 = [(frags[0], f1) for f1 in suffixes_0_temp[suffixes_0_temp.index(frags[1]):]]
  suffixes_1 = [(frags[2], f3) for f3 in suffixes_1_temp[suffixes_1_temp.index(frags[3]):]]

  for i in range(0, sector.base_sector_coords[0] * 2):
    # Calculate the run state indexes for phonemes 1 and 3
    idx0 = i % len(pgdata.c2_run_states)
    idx1 = i % len(pgdata.c2_run_states)
    
    # Calculate the current base index
    # (in case we've done a full run and are onto the next set of phonemes)
    cur_base_0 = int(i / len(pgdata.c2_run_states)) * 8
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


# Cache to support faster repeat querying
c2_candidate_cache = {}
# Constructs a cache to speed up later searching for YZ candidates
def construct_c2_candidate_cache():
  # For each Z slice...
  for ((f0y0, f2y0), z) in pgdata.get_c2_positions():
    # For each Y stack...
    for y in range(0, len(pgdata.c2_word1_y_mapping)):
      # As long as we have data for it...
      if len(pgdata.c2_word1_y_mapping[f0y0]) > y and len(pgdata.c2_word2_y_mapping[f2y0]) > y:
        # Get the correct starting fragments, check they aren't blank
        f0, f1 = pgdata.c2_word1_y_mapping[f0y0][y]
        f2, f3 = pgdata.c2_word2_y_mapping[f2y0][y]
        if None not in [f0, f1, f2, f3]:
          # Get all run prefixes present, and store that they're in this YZ-constrained line
          prefixes = c2_get_run_prefixes([f0, f1, f2, f3])
          for pf in prefixes:
            if pf not in c2_candidate_cache:
              c2_candidate_cache[pf] = []
            c2_candidate_cache[pf].append({'frags': [f0, f1, f2, f3], 'y': y - pgdata.c2_y_mapping_offset, 'z': z})


# Initialisation
_init_start = time.clock()
construct_c2_candidate_cache()
_init_time = time.clock() - _init_start


# Test modes
if __name__ == '__main__':
  if len(sys.argv) >= 2:
    if sys.argv[1] == "debug":
      with open("edsm_data.txt") as f:
        names = [n.strip() for n in f.readlines()]
      
      print(len(names))
      
      prefixes = {}
      
      for n in names:
        frags = get_fragments(n)
        sc = get_sector_class(n)
        if sc != "2":
          if frags[0] not in prefixes:
            prefixes[frags[0]] = 1
          if get_suffix_index(frags[-1]) is not None:
            prefixes[frags[0]] += 1
          else:
            print("Bad sector: {0}".format(n))
          
      print(len(prefixes))
      for p in pgdata.cx_prefixes:
        print("{0}: {1}".format(p, prefixes[p] if p in prefixes else 0))

    elif sys.argv[1] == "run1":
      input = sys.argv[2] # "Smooreau"
      frags = get_fragments(input)
      
      start_x = sector.base_coords.x - (int(sys.argv[3]) * 1280)
      
      cur_idx = pgdata.cx_suffixes_s1.index(frags[-1])
      
      for i in range(0, int(sys.argv[4])):
        frags[-1] = pgdata.cx_suffixes_s1[cur_idx]
        print ("[{1}] {0}".format("".join(frags), start_x + (i * 1280)))
        if cur_idx + 1 == len(pgdata.cx_suffixes_s1):
          cur_idx = 0
          frags[0] = pgdata.cx_prefixes[pgdata.cx_prefixes.index(frags[0])+1]
        else:
          cur_idx += 1
        
      
    elif sys.argv[1] == "run2":
      input = sys.argv[2] # "Schuae Flye"
      limit = int(sys.argv[3]) if len(sys.argv) > 3 else None

      for idx, frags in c2_get_run(input):
        if limit is not None and (idx + sector.base_sector_coords[0]) >= limit:
          break
        x = sector.base_coords.x + (idx * sector.cube_size)
        print ("[{4}/{5}] {0}{1} {2}{3}".format(frags[0], frags[1], frags[2], frags[3], idx, x))

    elif sys.argv[1] == "search2":
      input = sys.argv[2]
      coords, relpos_confidence = get_coords_from_name(input)
      print("Est. position of {0}: {1} (+/- {2}Ly)".format(input, coords, int(relpos_confidence)))

    elif sys.argv[1] == "eddbtest":
      import env
      
      with open("edsm_data.txt") as f:
        edsm_sectors = [s.strip() for s in f.readlines() if len(s) > 1]

      ok = 0
      bad = 0
      none1 = 0
      none2 = 0
      notpg = 0

      for system in env.data.eddb_systems:
        m = pgdata.pg_system_regex.match(system.name)
        if m is not None and m.group("sector") in edsm_sectors:
          sect = get_sector(m.group("sector"))
          if sect is not None:
            pos_sect = get_sector(system.position)
            if sect == pos_sect:
              ok += 1
            else:
              bad += 1
              bn = c2_get_name(sect)
              print("Bad: {0} @ {1} is not in {2} @ {3}".format(system.name, system.position, "{0}{1} {2}{3}".format(bn[0], bn[1], bn[2], bn[3]), sect))
          else:
            cls = get_sector_class(m.group("sector"))
            if cls == "2":
              none2 += 1
              print("None2: {0} @ {1}".format(system.name, system.position))
            else:
              none1 += 1
        else:
          notpg += 1

      print("Totals: OK = {0}, bad = {1}, none1 = {2}, none2 = {3}, notPG = {4}".format(ok, bad, none1, none2, notpg))
