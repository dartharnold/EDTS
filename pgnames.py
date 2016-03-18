#!/usr/bin/env python

from __future__ import print_function
import argparse
import logging
import math
import re
import sys
import pgdata
import sector
import vector3

app_name = "pgnames"

log = logging.getLogger(app_name)

#__all__ = [
#  "get_relative_star_position",
#  "get_sector",
#  "get_fragments",
#  "get_sector_class",
#  "get_suffixes",
#]

_srp_alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
_srp_divisor = len(_srp_alphabet)
_srp_middle = _srp_divisor**2
_srp_biggest = _srp_divisor**3
_srp_rowlength = 128
_srp_sidelength = _srp_rowlength**2

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


def get_sector(pos):
  if isinstance(pos, vector3.Vector3):
    x = math.floor((pos.x - sector.base_coords.x) / sector.cube_size)
    y = math.floor((pos.y - sector.base_coords.y) / sector.cube_size)
    z = math.floor((pos.z - sector.base_coords.z) / sector.cube_size)
    return sector.Sector(int(x), int(y), int(z))
  else:
    return get_sector_from_name(pos)


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


def get_sector_class(sect):
  frags = get_fragments(sect) if isinstance(sect, str) else sect
  if frags is None:
    return None
  if frags[2] in pgdata.cx_prefixes:
    return "2"
  elif len(frags) == 4:
    return "1a"
  else:
    return "1b"


def get_suffixes(prefix):
  frags = get_fragments(prefix) if isinstance(prefix, str) else prefix
  if frags is None:
    return None
  if frags[-1] in pgdata.cx_prefixes:
    # Append suffix straight onto a prefix (probably C2)
    suffix_map_idx = 1
    if frags[-1] in pgdata.c2_prefix_suffix_override_map:
      suffix_map_idx = pgdata.c2_prefix_suffix_override_map[frags[-1]]
    return pgdata.cx_suffixes[suffix_map_idx]
  else:
    # Likely C1
    if frags[-1] in pgdata.c1_infixes[2]:
      # Last infix is consonant-ish, return the vowel-ish suffix list
      return pgdata.cx_suffixes[1]
    else:
      # TODO: Work out how it decides which list to use
      pass

def c1_get_infixes(prefix):
  frags = get_fragments(prefix) if isinstance(prefix, str) else prefix
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
  frags = get_fragments(sect) if isinstance(sect, str) else sect
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


def get_coords_from_name(system_name):
  m = pgdata.pg_system_regex.match(system_name)
  if m is None:
    return None
  sector_name = m.group("sector")

  sect = get_sector_from_name(sector_name)
  abs_pos = sect.origin

  rel_pos, rel_pos_confidence = get_star_relative_position(*m.group("prefix", "centre", "suffix", "lcode", "number1", "number2"))

  return (abs_pos + rel_pos, rel_pos_confidence)


def get_sector_from_name(sector_name):
  frags = get_fragments(sector_name) if isinstance(sector_name, str) else sector_name
  sname = "{0}{1} {2}{3}".format(frags[0], frags[1], frags[2], frags[3])
  sc = get_sector_class(frags)
  if sc == "2":
    yz_candidates = c2_get_yz_candidates(frags[0], frags[2])
    for candidate in yz_candidates:
      start1 = pgdata.c2_word1_suffix_starts[frags[0]][candidate['offsets'][0]]
      start2 = pgdata.c2_word2_suffix_starts[frags[2]][candidate['offsets'][1]]
      if c2_validate_suffix(frags[1], start1) and c2_validate_suffix(frags[3], start2):
        for sysname, idx in c2_get_run([frags[0],start1,frags[2],start2]):
          if sysname == sname:
            return sector.Sector(idx, candidate['coords'][0], candidate['coords'][1])
    return None
  elif sc == "1a":
    # TODO
    pass
  else:
    # TODO
    pass


def c2_get_yz_candidates(frag0, frag2):
  matches = []
  # Find Z slice
  for z in range(0, len(pgdata.c2_positions_y0z)):
    pair = pgdata.c2_positions_y0z[z]
    for zo1 in range(0, len(pair[0])):
      pre1 = pair[0][zo1]
      for i in range(0, len(pgdata.c2_word1_y_mapping[pre1])):
        if len(pgdata.c2_word1_y_mapping[pre1]) > i and pgdata.c2_word1_y_mapping[pre1][i][0] == frag0:
          for zo2 in range(0, len(pair[1])):
            pre2 = pair[1][zo2]
            if len(pgdata.c2_word2_y_mapping[pre2]) > i and pgdata.c2_word2_y_mapping[pre2][i][0] == frag2:
              # zo2*2 + zo1: Blu Aec, Byeia Aec, Blu Ain, Byeia Ain
              matches.append({'coords': (i - pgdata.c2_y_mapping_offset, z*4 + zo2*2 + zo1 - pgdata.c2_positions_y0z_offset), 'offsets': (pgdata.c2_word1_y_mapping[pre1][i][1], pgdata.c2_word2_y_mapping[pre2][i][1])})
  return matches

def c2_validate_suffix(frag, base):
  suffixlist = pgdata.cx_suffixes[get_suffix_index(base)]
  base_idx = suffixlist.index(base)
  if frag in suffixlist[base_idx:base_idx+8]:
    return True
  if base_idx + 8 >= len(suffixlist) and frag in suffixlist[0:((base_idx+8) % len(suffixlist))]:
    return True
  return False

def get_suffix_index(s):
  if s in pgdata.cx_suffixes_s1:
    return 1
  if s in pgdata.cx_suffixes_s2:
    return 2
  if s in pgdata.cx_suffixes_s3:
    return 3
  return None


def c2_get_run(input):
  frags = get_fragments(input) if isinstance(input, str) else input

  # Calculate the actual starting suffix index
  suffixes_0_temp = get_suffixes(frags[0:1])
  suffixes_1_temp = get_suffixes(frags[0:-1])
  suffixes_0 = [(frags[0], f1) for f1 in suffixes_0_temp[suffixes_0_temp.index(frags[1]):]]
  suffixes_1 = [(frags[2], f3) for f3 in suffixes_1_temp[suffixes_1_temp.index(frags[3]):]]

  for i in range(0, sector.base_sector_coords[0] * 2):
    # Calculate the run state indexes for phonemes 1 and 3
    idx0 = i % len(pgdata.c2_run_states)
    idx1 = i % len(pgdata.c2_run_states)
    
    # Calculate the current base index
    # (in case we've done a full run and are onto the next set of phoneme 3s)
    cur_base_0 = 0
    cur_base_1 = int(i / len(pgdata.c2_run_states)) * 8
    
    # Ensure we have all the suffixes we need, and add the next set if not
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
    yield ("{0}{1} {2}{3}".format(frags[0], frags[1], frags[2], frags[3]), i - sector.base_sector_coords[0])


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
    elif sys.argv[1] == "baseline":
      baselines = {
        "Vegnao": vector3.Vector3(4300, 1000, 36650),
        "Vegnau": vector3.Vector3(5200, 1000, 36650),
        "Weqo": vector3.Vector3(6500, 1000, 36650),
        "Veqo": vector3.Vector3(-38450, 1000, 36650),
        "Vequia": vector3.Vector3(-26560, 1000, 36650),
        "Veqeau": vector3.Vector3(-22750, 1000, 36650),
        "Veqee": vector3.Vector3(-21700, 1000, 36650)
      }
      
      start = "Veqo"
      start_coords = baselines[start]
      
      current = start
      current_coords = start_coords
      for i in range(0, int(sys.argv[1])):
        extra = ""
        if current in baselines:
          if get_sector(current_coords) == get_sector(baselines[current]):
            extra = " CORRECT"
          else:
            extra = " INCORRECT"
            
        print("{0} @ {1} / {2}{3}".format(current, get_sector(current_coords).origin, get_sector(current_coords), extra))
        frags = get_fragments(current)
        
        suffix_idx = pgdata.cx_suffixes[1].index(frags[-1])
        if suffix_idx + 1 >= len(pgdata.cx_suffixes[1]):
          frags[-1] = pgdata.cx_suffixes[1][0]
          done = False
          cur_frag = len(frags) - 2
          while not done:
            cur_idx = pgdata.cx_infix.index(frags[cur_frag])
            if cur_idx + 1 >= len(pgdata.cx_infix):
              frags[cur_frag] = pgdata.cx_infix[0]
            else:
              frags[cur_frag] = pgdata.cx_infix[cur_idx+1]
              done = True
        else:
          frags[-1] = pgdata.cx_suffixes[1][suffix_idx+1]
        current = "".join(frags)
        current_coords.x += sector.cube_size

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

      frags = get_fragments(input)

      # This should put us at -49985
      start_x = sector.base_coords.x - (int(sys.argv[3]) * 1280)

      # The index in the valid set of suffixes we believe we're at
      base_idx_0 = 0
      base_idx_1 = 0
      # The state that we think this system is at in the run
      base_slot_0 = 0
      base_slot_1 = 0
      # Calculate the actual starting suffix index
      suffixes_0 = get_suffixes(frags[0:1])
      suffixes_1 = get_suffixes(frags[0:-1])
      start_idx_0 = suffixes_0.index(frags[1]) - base_idx_0
      start_idx_1 = suffixes_1.index(frags[3]) - base_idx_1

      for i in range(0, int(sys.argv[4])):
        # Calculate the run state indexes for phonemes 1 and 3
        idx0 = (i+base_slot_0) % len(pgdata.c2_run_states)
        idx1 = (i+base_slot_1) % len(pgdata.c2_run_states)
        # Calculate the current base index
        # (in case we've done a full run and are onto the next set of phoneme 3s)
        cur_base_0 = start_idx_0
        cur_base_1 = start_idx_1 + int((i + base_slot_1) / len(pgdata.c2_run_states)) * 8
        # print("idx0 = {0}, idx1 = {1}, cb0 = {2}, cb1 = {3}".format(idx0, idx1, cur_base_0, cur_base_1))
        # print("slots[{0}] = {1}, slots[{2}] = {3}".format(idx0, slots[idx0][0], idx1, slots[idx1][1]))
        frags[1] = suffixes_0[(cur_base_0 + pgdata.c2_run_states[idx0][0]) % len(suffixes_0)]
        frags[3] = suffixes_1[(cur_base_1 + pgdata.c2_run_states[idx1][1]) % len(suffixes_1)]
        print ("[{4}/{5},{6}/{7},{8}] {0}{1} {2}{3}".format(frags[0], frags[1], frags[2], frags[3], start_x + (i * 1280), idx0, idx1, cur_base_0, cur_base_1))

    elif sys.argv[1] == "search2":
      input = sys.argv[2]
      sinfo = pgdata.pg_system_regex.match(input)
      sname = sinfo.group("sector")
      frags = get_fragments(sname)
      
      yz_candidates = c2_get_yz_candidates(frags[0], frags[2])
      for candidate in yz_candidates:
        print("{0},{1}".format(candidate['coords'][0],candidate['coords'][1]))
        start1 = pgdata.c2_word1_suffix_starts[frags[0]][candidate['offsets'][0]]
        start2 = pgdata.c2_word2_suffix_starts[frags[2]][candidate['offsets'][1]]
        print("start1 = {0}, start2 = {1}".format(start1, start2))
        if c2_validate_suffix(frags[1], start1) and c2_validate_suffix(frags[3], start2):
          for sysname, idx in c2_get_run([frags[0],start1,frags[2],start2]):
            if sysname == sname:
              s = sector.Sector(idx, candidate['coords'][0], candidate['coords'][1])
              print("MATCH: {0}, {1}, origin: {2}".format(sname, s, s.origin))
              
              relpos, relpos_confidence = get_star_relative_position(sinfo.group("prefix"), sinfo.group("centre"), sinfo.group("suffix"), sinfo.group("lcode"), sinfo.group("number1"), sinfo.group("number2"))
              
              print("Est. position of {0}: {1} (+/- {2}Ly)".format(input, s.origin + relpos, int(relpos_confidence)))
