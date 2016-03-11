#!/usr/bin/env python

from __future__ import print_function
import argparse
import logging
import math
import re
import sys
from vector3 import Vector3

app_name = "pgnames"

log = logging.getLogger(app_name)

# This does not validate sector names, just ensures that it matches the 'Something AB-C d1' or 'Something AB-C d1-23' format
pg_system_regex = re.compile('^(?P<sector>[\\w\\s]+) (?P<prefix>\\w)(?P<centre>\\w)-(?P<suffix>\\w) (?P<lcode>\\w)(?P<number1>\\d+)(?:-(?P<number2>\\d+))?$')
# m = pg_system_regex.match('Eodgols ZP-R b13-45')
# m.group('sector', 'number1', 'number2')


# Dummy example data, is not correct

c12_prefixes = ["Eo", "Stu", "Myr", "Oo", "Sy"]
c3_prefixes = ["Eo", "Dry", "Bl", "Ph", "Pl", "Pr"]

c1_suffixes = ["oe", "ua", "ai"]
c2_suffixes = ["phs", "rps", "wns"]
c3_w1_suffixes = {
  "Ae": ["sms", "dst", "rb"], 
  "Au": ["sms", "dst", "rb"],
  "Eo": ["rd", "rld", "lls"],
  "Oo": ["b", "scs", "wsy", "vsky"]
}

c3_w2_suffixes = {
  "Ae": ["wsy"],
  "Ai": ["rgh", "rg", "hm"],
  "Ao": ["wsy"],
  "Au": ["wsy"],
  "Eae": ["wsy"],
  "Eo": ["hn", "rk", "rl", "rm"],
  
  "Eu": ["rk", "q", "rl", "r", ],
  "Au": ["b", "c", "d"],
  "Ao": [None, "b", "scs", "wsy", "c", "d", "scs", "wsy", "c", "d"]
  # "scs", "wsy",
}

cx_prefixes = [
  "Th", "Eo", "Oo", "Eu", "Tr", "Sly", "Dry", "Ou", "Tz", "Phl", "Ae", "Sch",
  "Hyp", "Syst", "Ai", "Kyl", "Phr", "Eae", "Ph", "Fl", "Scr", "Shr", "Fly",
  "Pl", "Fr", "Au", "Pry", "Pr", "Hyph", "Py", "Chr", "Phyl", "Bl", "Cry",
  "Gl", "Br", "Gr", "By", "Aae", "Myc", "Gyr", "Ly", "Myl", "Lych", "Myn",
  "Ch", "Myr", "Cl", "Rh", "Wh", "Pyr", "Cr", "Syn", "Str", "Syr", "Cy",
  "Wr", "Hy", "My", "Sty", "Sc", "Sph", "Spl", "A", "Sh", "B", "C", "D",
  "Sk", "Io", "Dr", "E", "Sl", "F", "Sm", "G", "H", "I", "Sp", "J", "Sq",
  "K", "L", "Pyth", "M", "St", "N", "O", "Ny", "Lyr", "P", "Sw", "Thr", "Lys",
  "Q", "R", "S", "T", "Ea", "U", "V", "W", "Schr", "X", "Ee", "Y", "Z", "Ei", "Oe" ]

cx_repeating_suffixes = [
  "oe",
  "io",  "oea", "oi",  "aa",  "ua", "eia", "ae",  "ooe",
  "oo",  "a",   "ue",  "ai",  "e",  "iae", "oae", "ou",
  "uae", "i",   "ao",  "au",  "o",  "eae", "u",   "aea", 
  "ia",  "ie",  "eou", "aei", "ea", "uia", "oa",  "aae", "eau", "ee" ]


c3_positions_y0z_z0_index = 3
c3_positions_y0z_z0_subindex = 4
c3_positions_y0z = [
  (("Hyp", "Ph"), ("Th", "Eu")),
  (("Eo", "Dry"), ("Ae", "Ai")),
  (("Hyp", "Ph"), ("Ae", "Ai")),
  (("Pl", "Pr" ), ("Th", "Eu")),
  (("Bl", "By" ), ("Th", "Eu")),
  (("Pl", "Pr" ), ("Ae", "Ai")),
  (("Bl", "By" ), ("Ae", "Ai")),
  (("Eo", "Dry"), ("Ao", "Au")),
  (("Hyp", "Ph"), ("Ao", "Au")),
  (("Eo", "Dry"), ("Ch", "Br")),
  (("Hyp", "Ph"), ("Ch", "Br")),
  (("Pl", "Pr" ), ("Ao", "Au")),
  (("Bl", "By" ), ("Ao", "Au")),
  (("Pl", "Pr" ), ("Ch", "Br")),
  (("Bl", "By" ), ("Ch", "Br")),
  (("Ch", "Py" ), ("Th", "Eu")),
  (("Sy", "My" ), ("Th", "Eu"))
]


slots = [
  (0, 0), (1, 0), (0, 1), (1, 1),
  (2, 0), (3, 0), (2, 1), (3, 1),
  (0, 2), (1, 2), (0, 3), (1, 3),
  (2, 2), (3, 2), (2, 3), (3, 3),
  (4, 0), (5, 0), (4, 1), (5, 1),
  (6, 0), (7, 0), (6, 1), (7, 1),
  (4, 2), (5, 2), (4, 3), (5, 3),
  (6, 2), (7, 2), (6, 3), (7, 3),
  (0, 4), (1, 4), (0, 5), (1, 5),
  (2, 4), (3, 4), (2, 5), (3, 5),
  (0, 6), (1, 6), (0, 7), (1, 7),
  (2, 6), (3, 6), (2, 7), (3, 7),
  (4, 4), (5, 4), (4, 5), (5, 5),
  (6, 4), (7, 4), (6, 5), (7, 5),
  (4, 6), (5, 6), (4, 7), (5, 7),
  (6, 6), (7, 6), (6, 7), (7, 7)
]

with open("PGFragments.txt") as f:
  fragments = f.readlines()
orig_fragments = [f.strip() for f in fragments]
fragments = sorted(orig_fragments, key=len, reverse=True)

def get_fragments(raw_name):
  input = raw_name.replace(' ', '')
  segments = []
  current_str = input
  while len(current_str) > 0:
    found = False
    for frag in fragments:
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


input = "Dryua Flyua"

frags = get_fragments(input)

start_x = -29400

base_idx_0 = int(sys.argv[1])
base_idx_1 = int(sys.argv[2])
base_slot_0 = int(sys.argv[3])
base_slot_1 = int(sys.argv[4])
start_idx_0 = cx_repeating_suffixes.index(frags[1]) - base_idx_0
start_idx_1 = cx_repeating_suffixes.index(frags[3]) - base_idx_1

print ("[{4}] {0}{1} {2}{3}".format(frags[0], frags[1], frags[2], frags[3], start_x))
for i in range(1, int(sys.argv[5])):
  idx0 = (i+base_slot_0) % len(slots)
  idx1 = (i+base_slot_1) % len(slots)
  cur_base_0 = start_idx_0 # + (int((i + base_slot_0) / len(slots)) % 2) * 8
  cur_base_1 = start_idx_1 + int((i + base_slot_1) / len(slots)) * 8
  # print("idx0 = {0}, idx1 = {1}, cb0 = {2}, cb1 = {3}".format(idx0, idx1, cur_base_0, cur_base_1))
  # print("slots[{0}] = {1}, slots[{2}] = {3}".format(idx0, slots[idx0][0], idx1, slots[idx1][1]))
  frags[1] = cx_repeating_suffixes[(cur_base_0 + slots[idx0][0]) % len(cx_repeating_suffixes)]
  frags[3] = cx_repeating_suffixes[(cur_base_1 + slots[idx1][1]) % len(cx_repeating_suffixes)]
  print ("[{4}/{5},{6}/{7},{8}] {0}{1} {2}{3}".format(frags[0], frags[1], frags[2], frags[3], start_x + (i * 1280), idx0, idx1, cur_base_0, cur_base_1))
  