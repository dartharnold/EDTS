from __future__ import division
import collections
import re
import sector
import vector3

# "Imagine the galaxy is a giant slice of Battenberg
#  which for reasons beyond our ken has had small chunks
#  of carrot cake pushed into it all over the place..."
#   - CMDR Jackie Silver


# This does not validate sector names, just ensures that it matches the 'Something AB-C d1' or 'Something AB-C d1-23' format
pg_system_regex = re.compile('^(?P<sector>[\\w\\s]+) (?P<prefix>[A-Za-z])(?P<centre>[A-Za-z])-(?P<suffix>[A-Za-z]) (?P<mcode>[A-Za-z])(?:(?P<number1>\\d+)-)?(?P<number2>\\d+)$')


# Hopefully-complete list of valid name fragments / phonemes
cx_raw_fragments = [
  "Th", "Eo", "Oo", "Eu", "Tr", "Sly", "Dry", "Ou",
  "Tz", "Phl", "Ae", "Sch", "Hyp", "Syst", "Ai", "Kyl",
  "Phr", "Eae", "Ph", "Fl", "Ao", "Scr", "Shr", "Fly",
  "Pl", "Fr", "Au", "Pry", "Pr", "Hyph", "Py", "Chr",
  "Phyl", "Tyr", "Bl", "Cry", "Gl", "Br", "Gr", "By",
  "Aae", "Myc", "Gyr", "Ly", "Myl", "Lych", "Myn", "Ch",
  "Myr", "Cl", "Rh", "Wh", "Pyr", "Cr", "Syn", "Str",
  "Syr", "Cy", "Wr", "Hy", "My", "Sty", "Sc", "Sph",
  "Spl", "A", "Sh", "B", "C", "D", "Sk", "Io",
  "Dr", "E", "Sl", "F", "Sm", "G", "H", "I",
  "Sp", "J", "Sq", "K", "L", "Pyth", "M", "St",
  "N", "O", "Ny", "Lyr", "P", "Sw", "Thr", "Lys",
  "Q", "R", "S", "T", "Ea", "U", "V", "W",
  "Schr", "X", "Ee", "Y", "Z", "Ei", "Oe",

  "ll", "ss", "b", "c", "d", "f", "dg", "g", "ng", "h", "j", "k", "l", "m", "n",
  "mb", "p", "q", "gn", "th", "r", "s", "t", "ch", "tch", "v", "w", "wh",
  "ck", "x", "y", "z", "ph", "sh", "ct", "wr", "o", "ai", "a", "oi", "ea",
  "ie", "u", "e", "ee", "oo", "ue", "i", "oa", "au", "ae", "oe", "scs",
  "wsy", "vsky", "sms", "dst", "rb", "nts", "rd", "rld", "lls", "rgh",
  "rg", "hm", "hn", "rk", "rl", "rm", "cs", "wyg", "rn", "hs", "rbs", "rp",
  "tts", "wn", "ms", "rr", "mt", "rs", "cy", "rt", "ws", "lch", "my", "ry",
  "nks", "nd", "sc", "nk", "sk", "nn", "ds", "sm", "sp", "ns", "nt", "dy",
  "st", "rrs", "xt", "nz", "sy", "xy", "rsch", "rphs", "sts", "sys", "sty",
  "tl", "tls", "rds", "nch", "rns", "ts", "wls", "rnt", "tt", "rdy", "rst",
  "pps", "tz", "sks", "ppy", "ff", "sps", "kh", "sky", "lts", "wnst", "rth",
  "ths", "fs", "pp", "ft", "ks", "pr", "ps", "pt", "fy", "rts", "ky",
  "rshch", "mly", "py", "bb", "nds", "wry", "zz", "nns", "ld", "lf",
  "gh", "lks", "sly", "lk", "rph", "ln", "bs", "rsts", "gs", "ls", "vvy",
  "lt", "rks", "qs", "rps", "gy", "wns", "lz", "nth", "phs", "io", "oea",
  "aa", "ua", "eia", "ooe", "iae", "oae", "ou", "uae", "ao", "eae", "aea",
  "ia", "eou", "aei", "uia", "aae", "eau" ]

# Sort fragments by length to ensure we check the longest ones first
cx_fragments = sorted(cx_raw_fragments, key=len, reverse=True)

# Order here is relevant, keep it
cx_prefixes = cx_raw_fragments[0:111]

#
# Sequences used in runs
#

# Vowel-ish infixes
c1_infixes_s1 = [
  "o", "ai", "a", "oi", "ea", "ie", "u", "e",
  "ee", "oo", "ue", "i", "oa", "au", "ae", "oe"
]

# Consonant-ish infixes
c1_infixes_s2 = [
  "ll", "ss", "b", "c", "d", "f", "dg", "g",
  "ng", "h", "j", "k", "l", "m", "n", "mb",
  "p", "q", "gn", "th", "r", "s", "t", "ch",
  "tch", "v", "w", "wh", "ck", "x", "y", "z",
  "ph", "sh", "ct", "wr"
]

c1_infixes = [
  [],
  c1_infixes_s1,
  c1_infixes_s2
]


# Sequence 1
cx_suffixes_s1 = [
  "oe",  "io",  "oea", "oi",  "aa",  "ua", "eia", "ae",
  "ooe", "oo",  "a",   "ue",  "ai",  "e",  "iae", "oae",
  "ou",  "uae", "i",   "ao",  "au",  "o",  "eae", "u",
  "aea", "ia",  "ie",  "eou", "aei", "ea", "uia", "oa",
  "aae", "eau", "ee"
]

# Sequence 2
c1_suffixes_s2 = [
  "b", "scs", "wsy", "c", "d", "vsky", "f", "sms",
  "dst", "g", "rb", "h", "nts", "ch", "rd", "rld",
  "k", "lls", "ck", "rgh", "l", "rg", "m", "n", 
  # Formerly sequence 4/5...
  "hm", "p", "hn", "rk", "q", "rl", "r", "rm",
  "s", "cs", "wyg", "rn", "ct", "t", "hs", "rbs",
  "rp", "tts", "v", "wn", "ms", "w", "rr", "mt",
  "x", "rs", "cy", "y", "rt", "z", "ws", "lch", # "y" is speculation
  "my", "ry", "nks", "nd", "sc", "ng", "sh", "nk",
  "sk", "nn", "ds", "sm", "sp", "ns", "nt", "dy",
  "ss", "st", "rrs", "xt", "nz", "sy", "xy", "rsch",
  "rphs", "sts", "sys", "sty", "th", "tl", "tls", "rds",
  "nch", "rns", "ts", "wls", "rnt", "tt", "rdy", "rst",
  "pps", "tz", "tch", "sks", "ppy", "ff", "sps", "kh",
  "sky", "ph", "lts", "wnst", "rth", "ths", "fs", "pp",
  "ft", "ks", "pr", "ps", "pt", "fy", "rts", "ky",
  "rshch", "mly", "py", "bb", "nds", "wry", "zz", "nns",
  "ld", "lf", "gh", "lks", "sly", "lk", "ll", "rph",
  "ln", "bs", "rsts", "gs", "ls", "vvy", "lt", "rks",
  "qs", "rps", "gy", "wns", "lz", "nth", "phs"
]

# Class 2 appears to use a subset of sequence 2
c2_suffixes_s2 = c1_suffixes_s2[0:len(cx_suffixes_s1)]


c1_suffixes = [
  [],
  cx_suffixes_s1,
  c1_suffixes_s2
]

c2_suffixes = [
  [],
  cx_suffixes_s1,
  c2_suffixes_s2
]

# These prefixes use the specified index into the c2_suffixes list
c2_prefix_suffix_override_map = {
  "Eo":  2,  "Oo": 2, "Eu": 2,
  "Ou":  2,  "Ae": 2, "Ai": 2,
  "Eae": 2,  "Ao": 2, "Au": 2,
  "Aae": 2
}

# These prefixes use the specified index into the c1_infixes list
c1_prefix_infix_override_map = {
  "Eo": 2, "Oo":  2, "Eu":  2, "Ou": 2,
  "Ae": 2, "Ai":  2, "Eae": 2, "Ao": 2,
  "Au": 2, "Aae": 2, "A":   2, "Io": 2,
  "E":  2, "I":   2, "O":   2, "Ea": 2,
  "U":  2, "Ee":  2, "Ei":  2, "Oe": 2
}


# The default run length for most prefixes
cx_prefix_length_default = 35
# Some prefixes use short run lengths; specify them here
cx_prefix_length_overrides = {
   'Eu': 31,  'Sly':  4,   'Tz':  1,  'Phl': 13,
   'Ae': 12,  'Hyp': 25,  'Kyl': 30,  'Phr': 10,
  'Eae':  4,   'Ao':  5,  'Scr': 24,  'Shr': 11,
  'Fly': 20,  'Pry':  3, 'Hyph': 14,   'Py': 12,
 'Phyl':  8,  'Tyr': 25,  'Cry':  5,  'Aae':  5,
  'Myc':  2,  'Gyr': 10,  'Myl': 12, 'Lych':  3,
  'Myn': 10,  'Myr':  4,   'Rh': 15,   'Wr': 31,
  'Sty':  4,  'Spl': 16,   'Sk': 27,   'Sq':  7,
 'Pyth':  1,  'Lyr': 10,   'Sw': 24,  'Thr': 32,
  'Lys': 10, 'Schr':  3,    'Z': 34,
}
# Get the total length of one run over all prefixes
cx_prefix_total_run_length = sum([cx_prefix_length_overrides.get(p, cx_prefix_length_default) for p in cx_prefixes])

# Default infix run lengths
c1_infix_s1_length_default = len(c1_suffixes_s2)
c1_infix_s2_length_default = len(cx_suffixes_s1)
# Some infixes use short runs too
c1_infix_length_overrides = {
  # Sequence 1
 'oi':  88,  'ue': 147,  'oa':  57,
 'au': 119,  'ae':  12,  'oe':  39,
  # Sequence 2
 'dg':  31, 'tch':  20,  'wr':  31,
}
# Total lengths of runs over all infixes, for each sequence
c1_infix_s1_total_run_length = sum([c1_infix_length_overrides.get(p, c1_infix_s1_length_default) for p in c1_infixes_s1])
c1_infix_s2_total_run_length = sum([c1_infix_length_overrides.get(p, c1_infix_s2_length_default) for p in c1_infixes_s2])

# Welp
c1_arbitrary_index_offset = 35


# Index modifiers for outer states
# Unit is a full run set using 128 suffixes
c2_vouter_step = 4
c2_vouter_states = [
  (0, 0), (1, 0),
  (0, 1), (1, 1),
  (2, 0), (3, 0),
  (2, 1), (3, 1),
  (0, 2), (1, 2),
  (0, 3), (1, 3),
  (2, 2), (3, 2),
  (2, 3), (3, 3),
]

# Index modifiers for runs
# Unit is a full run using 8 suffixes
c2_outer_step = 16
c2_outer_states = [
  (0, 2), (0, 3), (2, 2), (2, 3),
  (4, 6), (4, 7), (6, 6), (6, 7),
  (8, 0), (8, 1), (10, 0), (10, 1),
  (12, 4), (12, 5), (14, 4), (14, 5),
]

# Index modifiers for all states
# In pairs of (phoneme 1, phoneme 3)
c2_run_step = 8
c2_run_states = [
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

c2_full_run_step = c2_run_step * 2
c2_full_outer_step = c2_full_run_step * c2_outer_step
c2_full_vouter_step = c2_full_outer_step * c2_vouter_step

c2_run_diff = c2_full_run_step // 2
c2_outer_diff = c2_full_outer_step // 2
c2_vouter_diff = c2_full_vouter_step // 2

c1_galaxy_size = [128, 128,  78]
c2_galaxy_size = [128,  16,  78]


# Hand-authored sectors
# Data of unknown origin from an mysterious benefactor
ha_sectors = collections.OrderedDict([
  ("Trianguli Sector", sector.HASector(vector3.Vector3(60.85156, -47.94922, -81.32031), 50.0, "Trianguli Sector")),
  ("Crucis Sector", sector.HASector(vector3.Vector3(75.91016, 8.32812, 44.83984), 60.0, "Crucis Sector")),
  ("Tascheter Sector", sector.HASector(vector3.Vector3(1.46094, -22.39844, -62.74023), 50.0, "Tascheter Sector")),
  ("Hydrae Sector", sector.HASector(vector3.Vector3(77.57031, 84.07031, 69.47070), 60.0, "Hydrae Sector")),
  ("Col 285 Sector", sector.HASector(vector3.Vector3(-53.46875, 56.27344, -19.35547), 326.0, "Col 285 Sector")),
  ("Scorpii Sector", sector.HASector(vector3.Vector3(37.69141, 0.51953, 126.83008), 60.0, "Scorpii Sector")),
  ("Shui Wei Sector", sector.HASector(vector3.Vector3(67.51172, -119.44922, 24.85938), 80.0, "Shui Wei Sector")),
  ("Shudun Sector", sector.HASector(vector3.Vector3(-3.51953, 34.16016, 12.98047), 30.0, "Shudun Sector")),
  ("Yin Sector", sector.HASector(vector3.Vector3(6.42969, 20.21094, -46.98047), 50.0, "Yin Sector")),
  ("Jastreb Sector", sector.HASector(vector3.Vector3(-12.51953, 3.82031, -40.75000), 50.0, "Jastreb Sector")),
  ("Pegasi Sector", sector.HASector(vector3.Vector3(-170.26953, -95.17188, -19.18945), 100.0, "Pegasi Sector")),
  ("Cephei Sector", sector.HASector(vector3.Vector3(-107.98047, 30.05078, -42.23047), 50.0, "Cephei Sector")),
  ("Bei Dou Sector", sector.HASector(vector3.Vector3(-33.64844, 72.48828, -20.64062), 40.0, "Bei Dou Sector")),
  ("Puppis Sector", sector.HASector(vector3.Vector3(56.69141, 5.23828, -28.21094), 50.0, "Puppis Sector")),
  ("Sharru Sector", sector.HASector(vector3.Vector3(37.87891, 60.19922, -34.04297), 50.0, "Sharru Sector")),
  ("Alrai Sector", sector.HASector(vector3.Vector3(-38.60156, 23.42188, 68.25977), 70.0, "Alrai Sector")),
  ("Lyncis Sector", sector.HASector(vector3.Vector3(-68.51953, 65.10156, -141.03906), 70.0, "Lyncis Sector")),
  ("Tucanae Sector", sector.HASector(vector3.Vector3(105.60938, -218.21875, 159.47070), 100.0, "Tucanae Sector")),
  ("Piscium Sector", sector.HASector(vector3.Vector3(-44.83984, -54.75000, -29.10938), 60.0, "Piscium Sector")),
  ("Herculis Sector", sector.HASector(vector3.Vector3(-73.00000, 70.64844, 38.49023), 50.0, "Herculis Sector")),
  ("Antliae Sector", sector.HASector(vector3.Vector3(175.87109, 65.89062, 29.18945), 70.0, "Antliae Sector")),
  ("Arietis Sector", sector.HASector(vector3.Vector3(-72.16016, -76.82812, -135.36914), 80.0, "Arietis Sector")),
  ("Capricorni Sector", sector.HASector(vector3.Vector3(-58.37891, -119.78906, 107.34961), 60.0, "Capricorni Sector")),
  ("Ceti Sector", sector.HASector(vector3.Vector3(-14.10156, -116.94922, -32.50000), 70.0, "Ceti Sector")),
  ("Core Sys Sector", sector.HASector(vector3.Vector3(0.00000, 0.00000, 0.00000), 50.0, "Core Sys Sector")),
  ("Blanco 1 Sector", sector.HASector(vector3.Vector3(-42.28906, -864.69922, 157.82031), 231.0, "Blanco 1 Sector")),
  ("NGC 129 Sector", sector.HASector(vector3.Vector3(-4571.64062, -231.18359, -2671.45117), 309.0, "NGC 129 Sector")),
  ("NGC 225 Sector", sector.HASector(vector3.Vector3(-1814.48828, -41.08203, -1133.81836), 100.0, "NGC 225 Sector")),
  ("NGC 188 Sector", sector.HASector(vector3.Vector3(-5187.57031, 2556.32422, -3343.16016), 331.0, "NGC 188 Sector")),
  ("IC 1590 Sector", sector.HASector(vector3.Vector3(-7985.20703, -1052.35156, -5205.49023), 558.0, "IC 1590 Sector")),
  ("NGC 457 Sector", sector.HASector(vector3.Vector3(-6340.41797, -593.83203, -4708.80859), 461.0, "NGC 457 Sector")),
  ("M103 Sector", sector.HASector(vector3.Vector3(-5639.37109, -224.90234, -4405.96094), 105.0, "M103 Sector")),
  ("NGC 654 Sector", sector.HASector(vector3.Vector3(-5168.34375, -46.49609, -4200.19922), 97.0, "NGC 654 Sector")),
  ("NGC 659 Sector", sector.HASector(vector3.Vector3(-4882.00391, -165.43750, -4010.12305), 92.0, "NGC 659 Sector")),
  ("NGC 663 Sector", sector.HASector(vector3.Vector3(-4914.64062, -100.05469, -4051.31836), 260.0, "NGC 663 Sector")),
  ("Col 463 Sector", sector.HASector(vector3.Vector3(-1793.73438, 381.90234, -1371.41211), 200.0, "Col 463 Sector")),
  ("NGC 752 Sector", sector.HASector(vector3.Vector3(-929.80469, -589.36328, -1004.09766), 326.0, "NGC 752 Sector")),
  ("NGC 744 Sector", sector.HASector(vector3.Vector3(-2892.49609, -425.51562, -2641.21289), 115.0, "NGC 744 Sector")),
  ("Stock 2 Sector", sector.HASector(vector3.Vector3(-718.91406, -32.82422, -679.84180), 130.0, "Stock 2 Sector")),
  ("h Persei Sector", sector.HASector(vector3.Vector3(-4817.47266, -437.52734, -4750.67383), 355.0, "h Persei Sector")),
  ("Chi Persei Sector", sector.HASector(vector3.Vector3(-5389.26172, -480.34766, -5408.10742), 401.0, "Chi Persei Sector")),
  ("IC 1805 Sector", sector.HASector(vector3.Vector3(-4370.87891, 96.60156, -4325.34375), 358.0, "IC 1805 Sector")),
  ("NGC 957 Sector", sector.HASector(vector3.Vector3(-4085.48438, -278.87109, -4275.21484), 190.0, "NGC 957 Sector")),
  ("Tr 2 Sector", sector.HASector(vector3.Vector3(-1431.65234, -144.19141, -1556.91211), 112.0, "Tr 2 Sector")),
  ("M34 Sector", sector.HASector(vector3.Vector3(-931.64062, -438.33984, -1263.64648), 171.0, "M34 Sector")),
  ("NGC 1027 Sector", sector.HASector(vector3.Vector3(-1756.25391, 65.96484, -1805.99609), 147.0, "NGC 1027 Sector")),
  ("IC 1848 Sector", sector.HASector(vector3.Vector3(-4436.20312, 102.57031, -4790.66406), 342.0, "IC 1848 Sector")),
  ("NGC 1245 Sector", sector.HASector(vector3.Vector3(-5101.33984, -1451.18359, -7736.58789), 246.0, "NGC 1245 Sector")),
  ("NGC 1342 Sector", sector.HASector(vector3.Vector3(-884.15234, -576.25781, -1896.07422), 95.0, "NGC 1342 Sector")),
  ("IC 348 Sector", sector.HASector(vector3.Vector3(-402.66016, -383.08203, -1130.80273), 26.0, "IC 348 Sector")),
  ("Mel 22 Sector", sector.HASector(vector3.Vector3(-104.13672, -195.38672, -437.12695), 172.0, "Mel 22 Sector")),
  ("NGC 1444 Sector", sector.HASector(vector3.Vector3(-2065.66016, -88.70703, -3318.62500), 46.0, "NGC 1444 Sector")),
  ("NGC 1502 Sector", sector.HASector(vector3.Vector3(-1572.28906, 359.08203, -2140.41211), 63.0, "NGC 1502 Sector")),
  ("NGC 1528 Sector", sector.HASector(vector3.Vector3(-1183.84766, 13.24609, -2235.89648), 118.0, "NGC 1528 Sector")),
  ("NGC 1545 Sector", sector.HASector(vector3.Vector3(-1038.79297, 8.09766, -2074.42578), 122.0, "NGC 1545 Sector")),
  ("Hyades Sector", sector.HASector(vector3.Vector3(0.00000, -56.67578, -138.88086), 144.0, "Hyades Sector")),
  ("NGC 1647 Sector", sector.HASector(vector3.Vector3(11.76172, -508.69531, -1684.84180), 205.0, "NGC 1647 Sector")),
  ("NGC 1662 Sector", sector.HASector(vector3.Vector3(178.12891, -512.99609, -1317.47070), 83.0, "NGC 1662 Sector")),
  ("NGC 1664 Sector", sector.HASector(vector3.Vector3(-1227.67969, -27.29688, -3712.16406), 171.0, "NGC 1664 Sector")),
  ("NGC 1746 Sector", sector.HASector(vector3.Vector3(-35.15625, -380.61719, -2014.04883), 251.0, "NGC 1746 Sector")),
  ("NGC 1778 Sector", sector.HASector(vector3.Vector3(-921.61719, -167.16797, -4697.52930), 98.0, "NGC 1778 Sector")),
  ("NGC 1817 Sector", sector.HASector(vector3.Vector3(665.49609, -1457.36719, -6227.20508), 281.0, "NGC 1817 Sector")),
  ("NGC 1857 Sector", sector.HASector(vector3.Vector3(-1246.36328, 140.66016, -6071.80273), 109.0, "NGC 1857 Sector")),
  ("NGC 1893 Sector", sector.HASector(vector3.Vector3(-1192.19141, -317.42969, -10628.63672), 343.0, "NGC 1893 Sector")),
  ("M38 Sector", sector.HASector(vector3.Vector3(-466.23828, 42.51562, -3448.36328), 203.0, "M38 Sector")),
  ("Col 69 Sector", sector.HASector(vector3.Vector3(366.92969, -299.39453, -1359.90039), 300.0, "Col 69 Sector")),
  ("NGC 1981 Sector", sector.HASector(vector3.Vector3(578.95703, -423.23828, -1084.28711), 106.0, "NGC 1981 Sector")),
  ("Trapezium Sector", sector.HASector(vector3.Vector3(594.46875, -431.80859, -1072.44922), 182.0, "Trapezium Sector")),
  ("Col 70 Sector", sector.HASector(vector3.Vector3(508.68359, -372.59375, -1090.87891), 514.0, "Col 70 Sector")),
  ("M36 Sector", sector.HASector(vector3.Vector3(-412.07422, 75.04688, -4279.55078), 126.0, "M36 Sector")),
  ("M37 Sector", sector.HASector(vector3.Vector3(-180.73047, 243.89453, -4499.77148), 184.0, "M37 Sector")),
  ("NGC 2129 Sector", sector.HASector(vector3.Vector3(567.78906, 8.62109, -4907.25391), 72.0, "NGC 2129 Sector")),
  ("NGC 2169 Sector", sector.HASector(vector3.Vector3(921.21484, -173.53516, -3299.41602), 50.0, "NGC 2169 Sector")),
  ("M35 Sector", sector.HASector(vector3.Vector3(305.50781, 102.11328, -2640.42383), 194.0, "M35 Sector")),
  ("NGC 2175 Sector", sector.HASector(vector3.Vector3(940.29688, 37.07031, -5225.95117), 78.0, "NGC 2175 Sector")),
  ("Col 89 Sector", sector.HASector(vector3.Vector3(603.48438, 273.61719, -4187.90430), 593.0, "Col 89 Sector")),
  ("NGC 2232 Sector", sector.HASector(vector3.Vector3(655.20312, -154.73828, -956.90234), 154.0, "NGC 2232 Sector")),
  ("Col 97 Sector", sector.HASector(vector3.Vector3(878.88281, -64.39062, -1850.92383), 250.0, "Col 97 Sector")),
  ("NGC 2244 Sector", sector.HASector(vector3.Vector3(2092.95703, -164.37500, -4216.23242), 412.0, "NGC 2244 Sector")),
  ("NGC 2251 Sector", sector.HASector(vector3.Vector3(1733.50781, 7.55859, -3967.84375), 126.0, "NGC 2251 Sector")),
  ("Col 107 Sector", sector.HASector(vector3.Vector3(2591.42578, -89.05859, -5042.36914), 578.0, "Col 107 Sector")),
  ("NGC 2264 Sector", sector.HASector(vector3.Vector3(851.16406, 83.68359, -2005.22070), 510.0, "NGC 2264 Sector")),
  ("M41 Sector", sector.HASector(vector3.Vector3(1731.03125, -400.21094, -1396.76758), 350.0, "M41 Sector")),
  ("NGC 2286 Sector", sector.HASector(vector3.Vector3(5456.35547, -379.24609, -7706.28711), 385.0, "NGC 2286 Sector")),
  ("NGC 2281 Sector", sector.HASector(vector3.Vector3(-151.60938, 535.15234, -1732.92383), 133.0, "NGC 2281 Sector")),
  ("NGC 2301 Sector", sector.HASector(vector3.Vector3(1530.08984, 14.87109, -2392.53125), 116.0, "NGC 2301 Sector")),
  ("Col 121 Sector", sector.HASector(vector3.Vector3(1246.80469, -278.00000, -860.11328), 459.0, "Col 121 Sector")),
  ("M50 Sector", sector.HASector(vector3.Vector3(2015.20703, -63.45703, -2261.81836), 124.0, "M50 Sector")),
  ("NGC 2324 Sector", sector.HASector(vector3.Vector3(2088.35938, 218.74219, -3167.16211), 78.0, "NGC 2324 Sector")),
  ("NGC 2335 Sector", sector.HASector(vector3.Vector3(3185.22266, -104.81641, -3344.81250), 135.0, "NGC 2335 Sector")),
  ("NGC 2345 Sector", sector.HASector(vector3.Vector3(5319.95703, -294.56641, -5048.45312), 257.0, "NGC 2345 Sector")),
  ("NGC 2343 Sector", sector.HASector(vector3.Vector3(2402.10547, -66.03906, -2461.52930), 51.0, "NGC 2343 Sector")),
  ("NGC 2354 Sector", sector.HASector(vector3.Vector3(11248.28125, -1574.77344, -6919.98828), 500.0, "NGC 2354 Sector")),
  ("NGC 2353 Sector", sector.HASector(vector3.Vector3(2567.32812, 25.48047, -2594.35547), 192.0, "NGC 2353 Sector")),
  ("Col 132 Sector", sector.HASector(vector3.Vector3(1355.99609, -235.59766, -690.91602), 426.0, "Col 132 Sector")),
  ("Col 135 Sector", sector.HASector(vector3.Vector3(942.32812, -198.29688, -365.50586), 150.0, "Col 135 Sector")),
  ("NGC 2360 Sector", sector.HASector(vector3.Vector3(4695.94141, -150.25781, -3968.37891), 233.0, "NGC 2360 Sector")),
  ("NGC 2362 Sector", sector.HASector(vector3.Vector3(3826.82812, -449.91797, -2381.99023), 66.0, "NGC 2362 Sector")),
  ("NGC 2367 Sector", sector.HASector(vector3.Vector3(5384.37891, -433.42969, -3686.76172), 77.0, "NGC 2367 Sector")),
  ("Col 140 Sector", sector.HASector(vector3.Vector3(1186.89453, -181.42578, -548.42188), 162.0, "Col 140 Sector")),
  ("NGC 2374 Sector", sector.HASector(vector3.Vector3(3581.40625, 83.59766, -3179.72266), 210.0, "NGC 2374 Sector")),
  ("NGC 2384 Sector", sector.HASector(vector3.Vector3(5674.66016, -288.94141, -3914.68555), 101.0, "NGC 2384 Sector")),
  ("NGC 2395 Sector", sector.HASector(vector3.Vector3(674.53906, 404.00781, -1473.32031), 64.0, "NGC 2395 Sector")),
  ("NGC 2414 Sector", sector.HASector(vector3.Vector3(8802.37109, 393.31641, -7026.83984), 164.0, "NGC 2414 Sector")),
  ("M47 Sector", sector.HASector(vector3.Vector3(1241.61328, 86.52734, -1005.43945), 117.0, "M47 Sector")),
  ("NGC 2423 Sector", sector.HASector(vector3.Vector3(1925.25391, 156.97656, -1587.05859), 88.0, "NGC 2423 Sector")),
  ("Mel 71 Sector", sector.HASector(vector3.Vector3(7730.26562, 807.34375, -6743.53906), 240.0, "Mel 71 Sector")),
  ("NGC 2439 Sector", sector.HASector(vector3.Vector3(11484.73047, -964.35938, -5017.55664), 330.0, "NGC 2439 Sector")),
  ("M46 Sector", sector.HASector(vector3.Vector3(3516.44531, 320.30859, -2757.24609), 261.0, "M46 Sector")),
  ("M93 Sector", sector.HASector(vector3.Vector3(2930.09375, 11.79688, -1684.87891), 99.0, "M93 Sector")),
  ("NGC 2451A Sector", sector.HASector(vector3.Vector3(757.34375, -93.33594, -240.24414), 105.0, "NGC 2451A Sector")),
  ("NGC 2477 Sector", sector.HASector(vector3.Vector3(3808.06641, -403.21484, -1120.77539), 175.0, "NGC 2477 Sector")),
  ("NGC 2467 Sector", sector.HASector(vector3.Vector3(3941.64844, 30.85547, -1999.71289), 193.0, "NGC 2467 Sector")),
  ("NGC 2482 Sector", sector.HASector(vector3.Vector3(3850.51562, 152.85938, -2081.96484), 153.0, "NGC 2482 Sector")),
  ("NGC 2483 Sector", sector.HASector(vector3.Vector3(4895.04688, 28.32812, -2303.43359), 142.0, "NGC 2483 Sector")),
  ("NGC 2489 Sector", sector.HASector(vector3.Vector3(11855.98828, -180.25000, -5105.99414), 263.0, "NGC 2489 Sector")),
  ("NGC 2516 Sector", sector.HASector(vector3.Vector3(1276.15234, -364.36719, 87.00000), 117.0, "NGC 2516 Sector")),
  ("NGC 2506 Sector", sector.HASector(vector3.Vector3(8599.23047, 1962.22266, -7063.48828), 395.0, "NGC 2506 Sector")),
  ("Col 173 Sector", sector.HASector(vector3.Vector3(1341.08203, -193.03516, -202.82031), 500.0, "Col 173 Sector")),
  ("NGC 2527 Sector", sector.HASector(vector3.Vector3(1790.95312, 64.98438, -793.64062), 58.0, "NGC 2527 Sector")),
  ("NGC 2533 Sector", sector.HASector(vector3.Vector3(10181.95312, 249.56250, -4155.17969), 160.0, "NGC 2533 Sector")),
  ("NGC 2539 Sector", sector.HASector(vector3.Vector3(3519.28906, 856.72266, -2585.17578), 117.0, "NGC 2539 Sector")),
  ("NGC 2547 Sector", sector.HASector(vector3.Vector3(1457.24609, -218.75781, -137.75000), 108.0, "NGC 2547 Sector")),
  ("NGC 2546 Sector", sector.HASector(vector3.Vector3(2894.65234, -104.69922, -781.03711), 611.0, "NGC 2546 Sector")),
  ("M48 Sector", sector.HASector(vector3.Vector3(1795.49219, 666.54688, -1622.35156), 220.0, "M48 Sector")),
  ("NGC 2567 Sector", sector.HASector(vector3.Vector3(5126.51953, 286.27734, -1886.19336), 144.0, "NGC 2567 Sector")),
  ("NGC 2571 Sector", sector.HASector(vector3.Vector3(4083.74219, -275.02344, -1559.42969), 102.0, "NGC 2571 Sector")),
  ("NGC 2579 Sector", sector.HASector(vector3.Vector3(3250.51562, 17.64453, -889.24023), 89.0, "NGC 2579 Sector")),
  ("Pismis 4 Sector", sector.HASector(vector3.Vector3(1912.67578, -80.82031, -245.01953), 102.0, "Pismis 4 Sector")),
  ("NGC 2627 Sector", sector.HASector(vector3.Vector3(6248.08594, 773.52734, -2078.46094), 193.0, "NGC 2627 Sector")),
  ("NGC 2645 Sector", sector.HASector(vector3.Vector3(5410.67188, -275.22656, -492.41016), 48.0, "NGC 2645 Sector")),
  ("NGC 2632 Sector", sector.HASector(vector3.Vector3(221.48438, 327.75391, -464.35156), 125.0, "NGC 2632 Sector")),
  ("IC 2391 Sector", sector.HASector(vector3.Vector3(565.85938, -68.47656, 3.95117), 100.0, "IC 2391 Sector")),
  ("IC 2395 Sector", sector.HASector(vector3.Vector3(2290.90234, -152.42969, -136.10547), 114.0, "IC 2395 Sector")),
  ("NGC 2669 Sector", sector.HASector(vector3.Vector3(3389.15234, -374.19531, 41.40820), 199.0, "NGC 2669 Sector")),
  ("NGC 2670 Sector", sector.HASector(vector3.Vector3(3858.68750, -243.00000, -168.47461), 91.0, "NGC 2670 Sector")),
  ("Tr 10 Sector", sector.HASector(vector3.Vector3(1369.04297, 14.44922, -172.95117), 57.0, "Tr 10 Sector")),
  ("M67 Sector", sector.HASector(vector3.Vector3(1466.01953, 1555.39453, -2047.71289), 216.0, "M67 Sector")),
  ("IC 2488 Sector", sector.HASector(vector3.Vector3(3654.96484, -283.85938, 500.66797), 194.0, "IC 2488 Sector")),
  ("NGC 2910 Sector", sector.HASector(vector3.Vector3(8461.80469, -178.01172, 784.97852), 99.0, "NGC 2910 Sector")),
  ("NGC 2925 Sector", sector.HASector(vector3.Vector3(2505.64453, -52.77344, 263.35352), 74.0, "NGC 2925 Sector")),
  ("NGC 3114 Sector", sector.HASector(vector3.Vector3(2883.98828, -196.83203, 681.74609), 312.0, "NGC 3114 Sector")),
  ("NGC 3228 Sector", sector.HASector(vector3.Vector3(1733.04688, 141.95312, 330.59570), 26.0, "NGC 3228 Sector")),
  ("NGC 3247 Sector", sector.HASector(vector3.Vector3(4886.86328, -26.44141, 1272.93359), 74.0, "NGC 3247 Sector")),
  ("IC 2581 Sector", sector.HASector(vector3.Vector3(7722.32031, 0.00000, 2011.51367), 117.0, "IC 2581 Sector")),
  ("NGC 3293 Sector", sector.HASector(vector3.Vector3(7299.60547, 13.24609, 2079.34766), 133.0, "NGC 3293 Sector")),
  ("NGC 3324 Sector", sector.HASector(vector3.Vector3(7259.77734, -26.39062, 2109.16016), 264.0, "NGC 3324 Sector")),
  ("NGC 3330 Sector", sector.HASector(vector3.Vector3(2824.55859, 193.51953, 714.72266), 43.0, "NGC 3330 Sector")),
  ("Col 228 Sector", sector.HASector(vector3.Vector3(6846.64453, -125.30859, 2158.73828), 293.0, "Col 228 Sector")),
  ("IC 2602 Sector", sector.HASector(vector3.Vector3(497.46484, -45.26953, 177.13867), 155.0, "IC 2602 Sector")),
  ("Tr 14 Sector", sector.HASector(vector3.Vector3(8501.81641, -93.30469, 2664.30664), 130.0, "Tr 14 Sector")),
  ("Tr 16 Sector", sector.HASector(vector3.Vector3(8311.20312, -106.53125, 2636.46875), 254.0, "Tr 16 Sector")),
  ("NGC 3519 Sector", sector.HASector(vector3.Vector3(4392.18359, -90.03516, 1642.16992), 82.0, "NGC 3519 Sector")),
  ("Fe 1 Sector", sector.HASector(vector3.Vector3(3551.95312, 26.39062, 1292.80469), 275.0, "Fe 1 Sector")),
  ("NGC 3532 Sector", sector.HASector(vector3.Vector3(1497.35938, 41.62109, 533.18555), 232.0, "NGC 3532 Sector")),
  ("NGC 3572 Sector", sector.HASector(vector3.Vector3(6089.70312, 22.72266, 2301.10742), 95.0, "NGC 3572 Sector")),
  ("Col 240 Sector", sector.HASector(vector3.Vector3(4804.97656, 17.94141, 1825.23828), 374.0, "Col 240 Sector")),
  ("NGC 3590 Sector", sector.HASector(vector3.Vector3(5015.87109, -18.78125, 1945.52734), 47.0, "NGC 3590 Sector")),
  ("NGC 3680 Sector", sector.HASector(vector3.Vector3(2802.88672, 889.54688, 846.24219), 107.0, "NGC 3680 Sector")),
  ("NGC 3766 Sector", sector.HASector(vector3.Vector3(5194.02734, 0.00000, 2323.40039), 83.0, "NGC 3766 Sector")),
  ("IC 2944 Sector", sector.HASector(vector3.Vector3(5317.44531, -142.92969, 2434.51562), 613.0, "IC 2944 Sector")),
  ("Stock 14 Sector", sector.HASector(vector3.Vector3(6333.31641, -85.51953, 2980.23242), 102.0, "Stock 14 Sector")),
  ("NGC 4103 Sector", sector.HASector(vector3.Vector3(4713.57031, 111.41406, 2464.19336), 93.0, "NGC 4103 Sector")),
  ("NGC 4349 Sector", sector.HASector(vector3.Vector3(6160.53516, 99.13281, 3528.17188), 207.0, "NGC 4349 Sector")),
  ("Mel 111 Sector", sector.HASector(vector3.Vector3(21.80859, 308.30078, -23.96680), 109.0, "Mel 111 Sector")),
  ("NGC 4463 Sector", sector.HASector(vector3.Vector3(2938.90234, -119.35547, 1744.99219), 512.0, "NGC 4463 Sector")),
  ("NGC 4609 Sector", sector.HASector(vector3.Vector3(3387.39062, -6.96484, 2108.46484), 512.0, "NGC 4609 Sector")),
  ("Jewel Box Sector", sector.HASector(vector3.Vector3(5383.63281, 280.91016, 3522.95117), 188.0, "Jewel Box Sector")),
  ("NGC 5138 Sector", sector.HASector(vector3.Vector3(5131.33984, 395.59375, 3937.41602), 132.0, "NGC 5138 Sector")),
  ("NGC 5281 Sector", sector.HASector(vector3.Vector3(2797.33984, -44.10156, 2281.45508), 512.0, "NGC 5281 Sector")),
  ("NGC 5316 Sector", sector.HASector(vector3.Vector3(3024.62891, 6.91016, 2556.00781), 250.0, "NGC 5316 Sector")),
  ("NGC 5460 Sector", sector.HASector(vector3.Vector3(1503.62891, 482.09766, 1546.21484), 232.0, "NGC 5460 Sector")),
  ("NGC 5606 Sector", sector.HASector(vector3.Vector3(4178.73438, 102.79297, 4149.66406), 52.0, "NGC 5606 Sector")),
  ("NGC 5617 Sector", sector.HASector(vector3.Vector3(3553.99219, -8.72656, 3516.96875), 146.0, "NGC 5617 Sector")),
  ("NGC 5662 Sector", sector.HASector(vector3.Vector3(1479.93750, 132.47656, 1581.49609), 190.0, "NGC 5662 Sector")),
  ("NGC 5822 Sector", sector.HASector(vector3.Vector3(1849.48438, 187.74219, 2341.85156), 314.0, "NGC 5822 Sector")),
  ("NGC 5823 Sector", sector.HASector(vector3.Vector3(2435.16797, 169.67969, 3028.73828), 136.0, "NGC 5823 Sector")),
  ("NGC 6025 Sector", sector.HASector(vector3.Vector3(1426.48047, -258.18359, 1999.84961), 101.0, "NGC 6025 Sector")),
  ("NGC 6067 Sector", sector.HASector(vector3.Vector3(2322.23828, -177.35156, 3990.00586), 189.0, "NGC 6067 Sector")),
  ("NGC 6087 Sector", sector.HASector(vector3.Vector3(1543.78906, -273.85547, 2451.49414), 119.0, "NGC 6087 Sector")),
  ("NGC 6124 Sector", sector.HASector(vector3.Vector3(546.19922, 174.56250, 1568.46875), 195.0, "NGC 6124 Sector")),
  ("NGC 6134 Sector", sector.HASector(vector3.Vector3(1264.10547, -10.40234, 2698.57812), 53.0, "NGC 6134 Sector")),
  ("NGC 6152 Sector", sector.HASector(vector3.Vector3(1528.39062, -181.70312, 2986.73828), 245.0, "NGC 6152 Sector")),
  ("NGC 6169 Sector", sector.HASector(vector3.Vector3(1261.91016, 156.59375, 3357.25586), 105.0, "NGC 6169 Sector")),
  ("NGC 6167 Sector", sector.HASector(vector3.Vector3(1508.11328, -81.90234, 3278.87109), 74.0, "NGC 6167 Sector")),
  ("NGC 6178 Sector", sector.HASector(vector3.Vector3(1218.22656, 69.32031, 3076.88477), 49.0, "NGC 6178 Sector")),
  ("NGC 6193 Sector", sector.HASector(vector3.Vector3(1490.62500, -105.26562, 3461.19336), 154.0, "NGC 6193 Sector")),
  ("NGC 6200 Sector", sector.HASector(vector3.Vector3(2509.40234, -128.62109, 6210.98633), 234.0, "NGC 6200 Sector")),
  ("NGC 6208 Sector", sector.HASector(vector3.Vector3(1056.18750, -309.23047, 2855.24805), 161.0, "NGC 6208 Sector")),
  ("NGC 6231 Sector", sector.HASector(vector3.Vector3(1150.01172, 84.81641, 3882.36914), 165.0, "NGC 6231 Sector")),
  ("NGC 6242 Sector", sector.HASector(vector3.Vector3(923.09375, 154.51953, 3569.33203), 97.0, "NGC 6242 Sector")),
  ("Tr 24 Sector", sector.HASector(vector3.Vector3(978.63281, 97.11719, 3577.28125), 500.0, "Tr 24 Sector")),
  ("NGC 6250 Sector", sector.HASector(vector3.Vector3(926.94531, -88.57812, 2661.82812), 83.0, "NGC 6250 Sector")),
  ("NGC 6259 Sector", sector.HASector(vector3.Vector3(1037.94141, -87.95312, 3194.45508), 118.0, "NGC 6259 Sector")),
  ("NGC 6281 Sector", sector.HASector(vector3.Vector3(329.46484, 54.44141, 1523.83984), 37.0, "NGC 6281 Sector")),
  ("NGC 6322 Sector", sector.HASector(vector3.Vector3(823.50781, -175.75781, 3139.01953), 48.0, "NGC 6322 Sector")),
  ("IC 4651 Sector", sector.HASector(vector3.Vector3(977.73438, -398.58984, 2700.95703), 85.0, "IC 4651 Sector")),
  ("NGC 6383 Sector", sector.HASector(vector3.Vector3(235.09375, 5.60156, 3201.37500), 187.0, "NGC 6383 Sector")),
  ("M6 Sector", sector.HASector(vector3.Vector3(94.28906, -19.42578, 1587.08203), 93.0, "M6 Sector")),
  ("NGC 6416 Sector", sector.HASector(vector3.Vector3(126.60547, -67.57031, 2415.74219), 99.0, "NGC 6416 Sector")),
  ("IC 4665 Sector", sector.HASector(vector3.Vector3(-559.51953, 338.14453, 946.09570), 235.0, "IC 4665 Sector")),
  ("NGC 6425 Sector", sector.HASector(vector3.Vector3(96.70312, -73.71484, 2637.19922), 77.0, "NGC 6425 Sector")),
  ("M7 Sector", sector.HASector(vector3.Vector3(69.85156, -76.89062, 974.47852), 229.0, "M7 Sector")),
  ("M23 Sector", sector.HASector(vector3.Vector3(-348.48438, 103.71484, 2017.50000), 179.0, "M23 Sector")),
  ("M20 Sector", sector.HASector(vector3.Vector3(-324.17188, -9.28516, 2640.15625), 217.0, "M20 Sector")),
  ("NGC 6520 Sector", sector.HASector(vector3.Vector3(-259.73828, -251.08594, 5127.28906), 90.0, "NGC 6520 Sector")),
  ("M21 Sector", sector.HASector(vector3.Vector3(-526.55469, -27.43750, 3894.46875), 161.0, "M21 Sector")),
  ("NGC 6530 Sector", sector.HASector(vector3.Vector3(-461.04688, -106.03516, 4314.13867), 177.0, "NGC 6530 Sector")),
  ("NGC 6546 Sector", sector.HASector(vector3.Vector3(-388.70312, -74.76172, 3034.29102), 125.0, "NGC 6546 Sector")),
  ("NGC 6604 Sector", sector.HASector(vector3.Vector3(-1735.61328, 164.05469, 5248.01172), 81.0, "NGC 6604 Sector")),
  ("M16 Sector", sector.HASector(vector3.Vector3(-1666.35547, 79.58594, 5450.40625), 100.0, "M16 Sector")),
  ("M18 Sector", sector.HASector(vector3.Vector3(-1037.49219, -73.82422, 4100.12891), 62.0, "M18 Sector")),
  ("M17 Sector", sector.HASector(vector3.Vector3(-1104.42969, -59.19922, 4093.20508), 309.0, "M17 Sector")),
  ("NGC 6633 Sector", sector.HASector(vector3.Vector3(-717.30078, 175.43359, 983.66602), 72.0, "NGC 6633 Sector")),
  ("M25 Sector", sector.HASector(vector3.Vector3(-473.52344, -158.48828, 1957.30859), 177.0, "M25 Sector")),
  ("NGC 6664 Sector", sector.HASector(vector3.Vector3(-1545.53906, -33.16016, 3471.33984), 166.0, "NGC 6664 Sector")),
  ("IC 4756 Sector", sector.HASector(vector3.Vector3(-933.74219, 143.19922, 1266.49805), 184.0, "IC 4756 Sector")),
  ("M26 Sector", sector.HASector(vector3.Vector3(-2112.12891, -264.09375, 4766.29297), 107.0, "M26 Sector")),
  ("NGC 6705 Sector", sector.HASector(vector3.Vector3(-2803.58594, -298.96094, 5431.84570), 232.0, "NGC 6705 Sector")),
  ("NGC 6709 Sector", sector.HASector(vector3.Vector3(-2349.81250, 287.60547, 2591.48047), 143.0, "NGC 6709 Sector")),
  ("Col 394 Sector", sector.HASector(vector3.Vector3(-566.87109, -371.35547, 2145.51953), 144.0, "Col 394 Sector")),
  ("Steph 1 Sector", sector.HASector(vector3.Vector3(-1125.68750, 339.39453, 480.14648), 74.0, "Steph 1 Sector")),
  ("NGC 6716 Sector", sector.HASector(vector3.Vector3(-672.92188, -428.59375, 2443.02734), 100.0, "NGC 6716 Sector")),
  ("NGC 6755 Sector", sector.HASector(vector3.Vector3(-2887.29297, -137.35547, 3616.84766), 189.0, "NGC 6755 Sector")),
  ("Stock 1 Sector", sector.HASector(vector3.Vector3(-902.64844, 41.73828, 514.86133), 243.0, "Stock 1 Sector")),
  ("NGC 6811 Sector", sector.HASector(vector3.Vector3(-3810.01172, 816.57031, 706.14453), 162.0, "NGC 6811 Sector")),
  ("NGC 6819 Sector", sector.HASector(vector3.Vector3(-7320.41406, 1138.13281, 2099.09570), 112.0, "NGC 6819 Sector")),
  ("NGC 6823 Sector", sector.HASector(vector3.Vector3(-5310.76953, -10.76953, 3140.78125), 108.0, "NGC 6823 Sector")),
  ("NGC 6830 Sector", sector.HASector(vector3.Vector3(-4635.60938, -168.04688, 2665.59375), 187.0, "NGC 6830 Sector")),
  ("NGC 6834 Sector", sector.HASector(vector3.Vector3(-6141.51172, 141.15234, 2772.99805), 99.0, "NGC 6834 Sector")),
  ("NGC 6866 Sector", sector.HASector(vector3.Vector3(-4616.57812, 560.05078, 863.96875), 138.0, "NGC 6866 Sector")),
  ("NGC 6871 Sector", sector.HASector(vector3.Vector3(-4891.96484, 187.98047, 1533.04883), 448.0, "NGC 6871 Sector")),
  ("NGC 6885 Sector", sector.HASector(vector3.Vector3(-1769.88281, -139.42188, 806.58203), 57.0, "NGC 6885 Sector")),
  ("IC 4996 Sector", sector.HASector(vector3.Vector3(-5466.14844, 128.18359, 1423.82617), 83.0, "IC 4996 Sector")),
  ("Mel 227 Sector", sector.HASector(vector3.Vector3(238.19531, -198.52734, 236.53906), 57.0, "Mel 227 Sector")),
  ("NGC 6910 Sector", sector.HASector(vector3.Vector3(-3635.86328, 129.47656, 726.51758), 108.0, "NGC 6910 Sector")),
  ("M29 Sector", sector.HASector(vector3.Vector3(-3642.46875, 39.16406, 847.62891), 109.0, "M29 Sector")),
  ("NGC 6939 Sector", sector.HASector(vector3.Vector3(-3751.41797, 822.29688, -387.67188), 113.0, "NGC 6939 Sector")),
  ("NGC 6940 Sector", sector.HASector(vector3.Vector3(-2338.53906, -314.58594, 855.78320), 183.0, "NGC 6940 Sector")),
  ("NGC 7039 Sector", sector.HASector(vector3.Vector3(-3096.74609, -91.96484, 108.14062), 127.0, "NGC 7039 Sector")),
  ("NGC 7063 Sector", sector.HASector(vector3.Vector3(-2200.44141, -386.83984, 266.28320), 59.0, "NGC 7063 Sector")),
  ("NGC 7082 Sector", sector.HASector(vector3.Vector3(-4692.53125, -245.98047, -98.29492), 342.0, "NGC 7082 Sector")),
  ("M39 Sector", sector.HASector(vector3.Vector3(-1058.13672, -42.53906, -46.19922), 93.0, "M39 Sector")),
  ("IC 1396 Sector", sector.HASector(vector3.Vector3(-2678.65234, 175.52734, -438.64648), 500.0, "IC 1396 Sector")),
  ("IC 5146 Sector", sector.HASector(vector3.Vector3(-2759.04688, -266.45312, -212.29688), 73.0, "IC 5146 Sector")),
  ("NGC 7160 Sector", sector.HASector(vector3.Vector3(-2478.12109, 286.47656, -617.86523), 38.0, "NGC 7160 Sector")),
  ("NGC 7209 Sector", sector.HASector(vector3.Vector3(-3761.71875, -484.11719, -362.21289), 200.0, "NGC 7209 Sector")),
  ("NGC 7235 Sector", sector.HASector(vector3.Vector3(-8983.79688, 128.58984, -2024.58594), 134.0, "NGC 7235 Sector")),
  ("NGC 7243 Sector", sector.HASector(vector3.Vector3(-2595.76562, -257.61719, -406.48633), 223.0, "NGC 7243 Sector")),
  ("NGC 7380 Sector", sector.HASector(vector3.Vector3(-6928.64453, -113.87891, -2131.52930), 422.0, "NGC 7380 Sector")),
  ("NGC 7510 Sector", sector.HASector(vector3.Vector3(-6320.33984, 0.00000, -2426.15039), 99.0, "NGC 7510 Sector")),
  ("M52 Sector", sector.HASector(vector3.Vector3(-4268.12109, 32.32422, -1794.15430), 203.0, "M52 Sector")),
  ("NGC 7686 Sector", sector.HASector(vector3.Vector3(-3010.24609, -655.51562, -1065.98438), 133.0, "NGC 7686 Sector")),
  ("NGC 7789 Sector", sector.HASector(vector3.Vector3(-6847.17578, -717.10547, -3265.93555), 555.0, "NGC 7789 Sector")),
  ("NGC 7790 Sector", sector.HASector(vector3.Vector3(-8582.57422, -167.54297, -4297.83203), 336.0, "NGC 7790 Sector")),
  ("NGC 1624 Sector", sector.HASector(vector3.Vector3(-8349.38672, 872.38672, -18152.86963), 150.0, "NGC 1624 Sector")),
  ("IC 410 Sector", sector.HASector(vector3.Vector3(-1225.55469, -345.51953, -10926.05273), 150.0, "IC 410 Sector")),
  ("NGC 3603 Sector", sector.HASector(vector3.Vector3(18594.82031, -174.53125, 7362.21094), 150.0, "NGC 3603 Sector")),
  ("NGC 7822 Sector", sector.HASector(vector3.Vector3(-2443.97266, 302.39844, -1332.49805), 100.0, "NGC 7822 Sector")),
  ("NGC 281 Sector", sector.HASector(vector3.Vector3(-6661.27734, -877.87500, -4342.43164), 100.0, "NGC 281 Sector")),
  ("LBN 623 Sector", sector.HASector(vector3.Vector3(-499.50781, -18.84766, -331.87109), 100.0, "LBN 623 Sector")),
  ("Heart Sector", sector.HASector(vector3.Vector3(-5321.12500, 117.80469, -5284.10547), 100.0, "Heart Sector")),
  ("Soul Sector", sector.HASector(vector3.Vector3(-5095.17969, 117.80469, -5502.29492), 100.0, "Soul Sector")),
  ("Pleiades Sector", sector.HASector(vector3.Vector3(-81.75391, -149.41406, -343.34766), 100.0, "Pleiades Sector")),
  ("Perseus Dark Region", sector.HASector(vector3.Vector3(-359.89844, -316.98438, -1045.22461), 100.0, "Perseus Dark Region")),
  ("California Sector", sector.HASector(vector3.Vector3(-332.56641, -213.03125, -918.70508), 100.0, "California Sector")),
  ("NGC 1491 Sector", sector.HASector(vector3.Vector3(-4908.28906, -174.52344, -8710.81152), 100.0, "NGC 1491 Sector")),
  ("Hind Sector", sector.HASector(vector3.Vector3(-32.95312, -206.39062, -557.28516), 100.0, "Hind Sector")),
  ("Trifid of the North Sector", sector.HASector(vector3.Vector3(-643.14844, -402.24609, -2486.87695), 100.0, "Trifid of the North Sector")),
  ("Flaming Star Sector", sector.HASector(vector3.Vector3(-233.46875, -68.22266, -1682.50977), 100.0, "Flaming Star Sector")),
  ("NGC 1931 Sector", sector.HASector(vector3.Vector3(-743.83984, 36.65234, -6960.26953), 100.0, "NGC 1931 Sector")),
  ("Crab Sector", sector.HASector(vector3.Vector3(558.51953, -707.39453, -6941.73242), 100.0, "Crab Sector")),
  ("Running Man Sector", sector.HASector(vector3.Vector3(586.15625, -425.38281, -1079.56836), 100.0, "Running Man Sector")),
  ("Orion Sector", sector.HASector(vector3.Vector3(616.52344, -446.42578, -1107.67383), 100.0, "Orion Sector")),
  ("Col 359 Sector", sector.HASector(vector3.Vector3(-393.00781, 175.31641, 686.22852), 566.0, "Col 359 Sector")),
  ("Spirograph Sector", sector.HASector(vector3.Vector3(577.89844, -452.66406, -819.22266), 100.0, "Spirograph Sector")),
  ("NGC 1999 Sector", sector.HASector(vector3.Vector3(549.36719, -374.51172, -926.56445), 100.0, "NGC 1999 Sector")),
  ("Flame Sector", sector.HASector(vector3.Vector3(428.26172, -280.66797, -858.96289), 100.0, "Flame Sector")),
  ("Horsehead Sector", sector.HASector(vector3.Vector3(411.68359, -272.99219, -811.47461), 100.0, "Horsehead Sector")),
  ("Witch Head Sector", sector.HASector(vector3.Vector3(369.41406, -401.57812, -715.72852), 100.0, "Witch Head Sector")),
  ("Monkey Head Sector", sector.HASector(vector3.Vector3(1133.31641, 44.67969, -6298.69922), 100.0, "Monkey Head Sector")),
  ("Jellyfish Sector", sector.HASector(vector3.Vector3(789.77734, 252.96484, -4930.74609), 100.0, "Jellyfish Sector")),
  ("Rosette Sector", sector.HASector(vector3.Vector3(2346.98438, -175.72266, -4748.76562), 100.0, "Rosette Sector")),
  ("Hubble's Variable Sector", sector.HASector(vector3.Vector3(1210.32422, 68.06250, -2744.17188), 100.0, "Hubble's Variable Sector")),
  ("Cone Sector", sector.HASector(vector3.Vector3(855.44141, 84.45312, -2025.11328), 100.0, "Cone Sector")),
  ("Seagull Sector", sector.HASector(vector3.Vector3(2656.38672, -159.12891, -2712.61523), 100.0, "Seagull Sector")),
  ("Thor's Helmet Sector", sector.HASector(vector3.Vector3(2704.18750, -19.17578, -2469.26172), 100.0, "Thor's Helmet Sector")),
  ("Skull and Crossbones Neb. Sector", sector.HASector(vector3.Vector3(13388.46094, 104.71875, -6762.99805), 100.0, "Skull and Crossbones Neb. Sector")),
  ("Pencil Sector", sector.HASector(vector3.Vector3(813.80078, 2.84375, -44.07422), 100.0, "Pencil Sector")),
  ("NGC 3199 Sector", sector.HASector(vector3.Vector3(14577.19531, -261.78516, 3526.59375), 100.0, "NGC 3199 Sector")),
  ("Eta Carina Sector", sector.HASector(vector3.Vector3(8582.39453, -141.36719, 2706.01758), 100.0, "Eta Carina Sector")),
  ("Statue of Liberty Sector", sector.HASector(vector3.Vector3(5589.73047, -73.30078, 2179.34375), 100.0, "Statue of Liberty Sector")),
  ("NGC 5367 Sector", sector.HASector(vector3.Vector3(1348.62500, 755.99219, 1421.15430), 100.0, "NGC 5367 Sector")),
  ("NGC 6188 Sector", sector.HASector(vector3.Vector3(1704.75391, -84.46875, 4055.45117), 100.0, "NGC 6188 Sector")),
  ("Cat's Paw Sector", sector.HASector(vector3.Vector3(850.85938, 57.59375, 5433.48047), 100.0, "Cat's Paw Sector")),
  ("NGC 6357 Sector", sector.HASector(vector3.Vector3(964.84375, 142.23828, 8091.43555), 100.0, "NGC 6357 Sector")),
  ("Trifid Sector", sector.HASector(vector3.Vector3(-633.71094, -27.22656, 5161.16992), 100.0, "Trifid Sector")),
  ("Lagoon Sector", sector.HASector(vector3.Vector3(-470.27344, -94.24219, 4474.36719), 100.0, "Lagoon Sector")),
  ("Eagle Sector", sector.HASector(vector3.Vector3(-2046.40234, 97.73438, 6693.48047), 100.0, "Eagle Sector")),
  ("Omega Sector", sector.HASector(vector3.Vector3(-1432.63672, -76.79297, 5309.58203), 100.0, "Omega Sector")),
  ("IC 1287 Sector", sector.HASector(vector3.Vector3(-358.35547, -8.72656, 933.54492), 100.0, "IC 1287 Sector")),
  ("R CrA Sector", sector.HASector(vector3.Vector3(0.00000, -128.39062, 399.89453), 100.0, "R CrA Sector")),
  ("NGC 6820 Sector", sector.HASector(vector3.Vector3(-5577.41406, -11.34375, 3338.01367), 100.0, "NGC 6820 Sector")),
  ("Crescent Sector", sector.HASector(vector3.Vector3(-4836.49219, 209.37891, 1250.80273), 100.0, "Crescent Sector")),
  ("Sadr Region Sector", sector.HASector(vector3.Vector3(-1794.68359, 53.71094, 365.84961), 100.0, "Sadr Region Sector")),
  ("Veil West Sector", sector.HASector(vector3.Vector3(-1395.62891, -194.41797, 418.70898), 100.0, "Veil West Sector")),
  ("North America Sector", sector.HASector(vector3.Vector3(-1893.85547, -33.16016, 149.04883), 100.0, "North America Sector")),
  ("Pelican Sector", sector.HASector(vector3.Vector3(-1891.56641, 3.31641, 178.80469), 100.0, "Pelican Sector")),
  ("Veil East Sector", sector.HASector(vector3.Vector3(-1914.36328, -305.97266, 491.52539), 100.0, "Veil East Sector")),
  ("Iris Sector", sector.HASector(vector3.Vector3(-1410.35547, 367.96094, -354.25781), 100.0, "Iris Sector")),
  ("Elephant's Trunk Sector", sector.HASector(vector3.Vector3(-2658.95703, 174.23828, -435.41992), 100.0, "Elephant's Trunk Sector")),
  ("Cocoon Sector", sector.HASector(vector3.Vector3(-3175.87891, -306.70703, -244.37109), 100.0, "Cocoon Sector")),
  ("Cave Sector", sector.HASector(vector3.Vector3(-2250.06641, 108.87109, -827.86328), 100.0, "Cave Sector")),
  ("NGC 7538 Sector", sector.HASector(vector3.Vector3(-8372.94141, 125.66016, -3298.18945), 100.0, "NGC 7538 Sector")),
  ("Bubble Sector", sector.HASector(vector3.Vector3(-6573.64062, 24.78516, -2682.65234), 100.0, "Bubble Sector")),
  ("Aries Dark Region", sector.HASector(vector3.Vector3(-93.57031, -184.53516, -257.08398), 100.0, "Aries Dark Region")),
  ("NGC 1333 Sector", sector.HASector(vector3.Vector3(-381.21094, -383.42969, -957.94531), 100.0, "NGC 1333 Sector")),
  ("Taurus Dark Region", sector.HASector(vector3.Vector3(-62.37891, -103.47656, -443.84766), 100.0, "Taurus Dark Region")),
  ("Orion Dark Region", sector.HASector(vector3.Vector3(596.77344, -311.86719, -1340.37305), 100.0, "Orion Dark Region")),
  ("Messier 78 Sector", sector.HASector(vector3.Vector3(665.03125, -395.19922, -1400.55469), 100.0, "Messier 78 Sector")),
  ("Barnard's Loop Sector", sector.HASector(vector3.Vector3(726.50391, -365.36328, -1377.93555), 100.0, "Barnard's Loop Sector")),
  ("Puppis Dark Region", sector.HASector(vector3.Vector3(1440.26562, -286.21484, -306.13672), 100.0, "Puppis Dark Region")),
  ("Puppis Dark Region B Sector", sector.HASector(vector3.Vector3(1352.29688, 0.00000, -362.34570), 100.0, "Puppis Dark Region B Sector")),
  ("Vela Dark Region", sector.HASector(vector3.Vector3(991.18750, -121.87109, -51.94531), 100.0, "Vela Dark Region")),
  ("Musca Dark Region", sector.HASector(vector3.Vector3(415.92578, -68.19531, 249.91211), 100.0, "Musca Dark Region")),
  ("Coalsack Sector", sector.HASector(vector3.Vector3(418.85938, -0.87109, 273.05078), 100.0, "Coalsack Sector")),
  ("Chamaeleon Sector", sector.HASector(vector3.Vector3(483.30078, -152.70312, 301.99805), 100.0, "Chamaeleon Sector")),
  ("Coalsack Dark Region", sector.HASector(vector3.Vector3(450.26562, -9.07422, 259.96094), 100.0, "Coalsack Dark Region")),
  ("Lupus Dark Region B Sector", sector.HASector(vector3.Vector3(173.39062, 81.61328, 429.15625), 100.0, "Lupus Dark Region B Sector")),
  ("Lupus Dark Region", sector.HASector(vector3.Vector3(158.46484, 126.79297, 412.81055), 100.0, "Lupus Dark Region")),
  ("Scorpius Dark Region", sector.HASector(vector3.Vector3(110.22656, 0.00000, 477.44141), 100.0, "Scorpius Dark Region")),
  ("IC 4604 Sector", sector.HASector(vector3.Vector3(62.72266, 182.41797, 568.14453), 100.0, "IC 4604 Sector")),
  ("Ophiuchus Dark Region B Sector", sector.HASector(vector3.Vector3(-42.85156, 169.29688, 489.79883), 100.0, "Ophiuchus Dark Region B Sector")),
  ("Scutum Dark Region", sector.HASector(vector3.Vector3(-274.66016, 11.34375, 589.00977), 100.0, "Scutum Dark Region")),
  ("B92 Sector", sector.HASector(vector3.Vector3(-142.89062, -6.80859, 634.06250), 100.0, "B92 Sector")),
  ("Snake Sector", sector.HASector(vector3.Vector3(-18.70703, 73.12109, 595.23438), 100.0, "Snake Sector")),
  ("Ophiuchus Dark Region C Sector", sector.HASector(vector3.Vector3(-9.00781, 63.37109, 516.04492), 100.0, "Ophiuchus Dark Region C Sector")),
  ("Rho Ophiuchi Sector", sector.HASector(vector3.Vector3(52.26953, 152.01562, 473.45508), 100.0, "Rho Ophiuchi Sector")),
  ("Ophiuchus Dark Region", sector.HASector(vector3.Vector3(43.33984, 152.03516, 495.38672), 100.0, "Ophiuchus Dark Region")),
  ("Corona Austr. Dark Region", sector.HASector(vector3.Vector3(-8.52734, -177.85156, 488.56641), 100.0, "Corona Austr. Dark Region")),
  ("Aquila Dark Region", sector.HASector(vector3.Vector3(-719.23047, -17.45312, 694.55273), 100.0, "Aquila Dark Region")),
  ("Vulpecula Dark Region", sector.HASector(vector3.Vector3(-543.80859, 45.33984, 353.15234), 100.0, "Vulpecula Dark Region")),
  ("Cepheus Dark Region", sector.HASector(vector3.Vector3(-1373.48438, 243.10938, -120.16406), 100.0, "Cepheus Dark Region")),
  ("Cepheus Dark Region B Sector", sector.HASector(vector3.Vector3(-945.42578, 241.92188, -218.26953), 100.0, "Cepheus Dark Region B Sector")),
  ("Horsehead Dark Region", sector.HASector(vector3.Vector3(608.46094, -404.64453, -1194.16992), 200.0, "Horsehead Dark Region")),
  ("Pipe (stem) Sector", sector.HASector(vector3.Vector3(12.15234, 51.39453, 497.20312), 100.0, "Pipe (stem) Sector")),
  ("Pipe (bowl) Sector", sector.HASector(vector3.Vector3(-11.31250, 36.61719, 498.52930), 100.0, "Pipe (bowl) Sector")),
  ("Parrot's Head Sector", sector.HASector(vector3.Vector3(19.11719, -90.63281, 995.70117), 100.0, "Parrot's Head Sector")),
  ("Struve's Lost Sector", sector.HASector(vector3.Vector3(-30.95703, -178.36719, -466.07617), 100.0, "Struve's Lost Sector")),
  ("B133 Sector", sector.HASector(vector3.Vector3(-474.18359, -111.46875, 873.33984), 100.0, "B133 Sector")),
  ("B352 Sector", sector.HASector(vector3.Vector3(-1896.42969, 9.94922, 115.99023), 100.0, "B352 Sector")),
  ("Bow-Tie Sector", sector.HASector(vector3.Vector3(-2985.95312, 601.75000, -1723.94141), 100.0, "Bow-Tie Sector")),
  ("Skull Sector", sector.HASector(vector3.Vector3(-369.61719, -1543.29297, -204.04102), 100.0, "Skull Sector")),
  ("Little Dumbbell Sector", sector.HASector(vector3.Vector3(-1560.71484, -382.69531, -1351.93164), 100.0, "Little Dumbbell Sector")),
  ("IC 289 Sector", sector.HASector(vector3.Vector3(-1118.43359, 83.04297, -1277.57812), 100.0, "IC 289 Sector")),
  ("NGC 1360 Sector", sector.HASector(vector3.Vector3(437.24219, -925.14844, -513.75586), 100.0, "NGC 1360 Sector")),
  ("IC 351 Sector", sector.HASector(vector3.Vector3(-10947.40625, -8337.61523, -28668.42285), 100.0, "IC 351 Sector")),
  ("NGC 1501 Sector", sector.HASector(vector3.Vector3(-2071.58984, 413.77344, -2915.01367), 100.0, "NGC 1501 Sector")),
  ("NGC 1514 Sector", sector.HASector(vector3.Vector3(-202.23438, -218.68750, -807.39844), 100.0, "NGC 1514 Sector")),
  ("NGC 1535 Sector", sector.HASector(vector3.Vector3(1422.89844, -2733.25000, -2853.89062), 100.0, "NGC 1535 Sector")),
  ("NGC 2022 Sector", sector.HASector(vector3.Vector3(2934.63281, -1966.59375, -9781.63867), 100.0, "NGC 2022 Sector")),
  ("IC 2149 Sector", sector.HASector(vector3.Vector3(-1688.68359, 1312.09766, -6875.08203), 100.0, "IC 2149 Sector")),
  ("IC 2165 Sector", sector.HASector(vector3.Vector3(9024.47656, -3006.29297, -10272.34375), 100.0, "IC 2165 Sector")),
  ("Butterfly Sector", sector.HASector(vector3.Vector3(1747.16797, 188.37109, -2431.44336), 100.0, "Butterfly Sector")),
  ("NGC 2371/2 Sector", sector.HASector(vector3.Vector3(661.47266, 1497.67188, -4084.04688), 100.0, "NGC 2371/2 Sector")),
  ("Eskimo Sector", sector.HASector(vector3.Vector3(234.63281, 239.23438, -726.43945), 100.0, "Eskimo Sector")),
  ("NGC 2438 Sector", sector.HASector(vector3.Vector3(2508.30469, 228.79297, -1973.84180), 100.0, "NGC 2438 Sector")),
  ("NGC 2440 Sector", sector.HASector(vector3.Vector3(4653.64062, 238.69141, -3282.78125), 100.0, "NGC 2440 Sector")),
  ("NGC 2452 Sector", sector.HASector(vector3.Vector3(9387.19141, -183.25000, -4700.75391), 100.0, "NGC 2452 Sector")),
  ("IC 2448 Sector", sector.HASector(vector3.Vector3(8457.82422, -2355.25391, 2393.32227), 100.0, "IC 2448 Sector")),
  ("NGC 2792 Sector", sector.HASector(vector3.Vector3(8157.05078, 586.27734, -599.01562), 100.0, "NGC 2792 Sector")),
  ("NGC 2818 Sector", sector.HASector(vector3.Vector3(8322.63672, 1271.05078, -1169.66992), 100.0, "NGC 2818 Sector")),
  ("NGC 2867 Sector", sector.HASector(vector3.Vector3(12208.21094, -1274.62891, 1759.23047), 100.0, "NGC 2867 Sector")),
  ("NGC 2899 Sector", sector.HASector(vector3.Vector3(6434.56641, -430.78125, 812.87500), 100.0, "NGC 2899 Sector")),
  ("IC 2501 Sector", sector.HASector(vector3.Vector3(18754.05469, -1906.93750, 3645.41797), 100.0, "IC 2501 Sector")),
  ("Eight Burst Sector", sector.HASector(vector3.Vector3(2049.63281, 450.94531, 75.15625), 100.0, "Eight Burst Sector")),
  ("IC 2553 Sector", sector.HASector(vector3.Vector3(12855.33984, -1261.05078, 3565.10156), 100.0, "IC 2553 Sector")),
  ("NGC 3195 Sector", sector.HASector(vector3.Vector3(4656.55469, -1895.47656, 2331.83008), 100.0, "NGC 3195 Sector")),
  ("NGC 3211 Sector", sector.HASector(vector3.Vector3(8797.93750, -785.83594, 2572.69727), 100.0, "NGC 3211 Sector")),
  ("Ghost of Jupiter Sector", sector.HASector(vector3.Vector3(1171.69141, 743.95703, -183.48242), 100.0, "Ghost of Jupiter Sector")),
  ("IC 2621 Sector", sector.HASector(vector3.Vector3(14360.99219, -1297.00781, 5685.91992), 100.0, "IC 2621 Sector")),
  ("Owl Sector", sector.HASector(vector3.Vector3(-624.37891, 1847.16406, -1018.89062), 100.0, "Owl Sector")),
  ("NGC 3699 Sector", sector.HASector(vector3.Vector3(4150.35156, 102.09375, 1736.13086), 100.0, "NGC 3699 Sector")),
  ("Blue planetary Sector", sector.HASector(vector3.Vector3(4527.26562, 409.69141, 2082.31055), 100.0, "Blue planetary Sector")),
  ("NGC 4361 Sector", sector.HASector(vector3.Vector3(3106.92969, 3241.21094, 1389.79688), 100.0, "NGC 4361 Sector")),
  ("Lemon Slice Sector", sector.HASector(vector3.Vector3(-3085.35938, 2548.82812, -2057.67773), 100.0, "Lemon Slice Sector")),
  ("IC 4191 Sector", sector.HASector(vector3.Vector3(11811.59375, -1204.96094, 8148.27148), 100.0, "IC 4191 Sector")),
  ("Spiral Planetary Sector", sector.HASector(vector3.Vector3(1415.32812, -105.56641, 1074.29297), 100.0, "Spiral Planetary Sector")),
  ("NGC 5307 Sector", sector.HASector(vector3.Vector3(5879.41797, 1490.00781, 5368.64453), 100.0, "NGC 5307 Sector")),
  ("NGC 5315 Sector", sector.HASector(vector3.Vector3(6499.57812, -644.44141, 5282.06250), 100.0, "NGC 5315 Sector")),
  ("Retina Sector", sector.HASector(vector3.Vector3(1867.97656, 811.80078, 2202.64258), 100.0, "Retina Sector")),
  ("NGC 5873 Sector", sector.HASector(vector3.Vector3(13791.82031, 8670.95312, 25191.27344), 100.0, "NGC 5873 Sector")),
  ("NGC 5882 Sector", sector.HASector(vector3.Vector3(4616.64062, 1543.22656, 7331.10352), 100.0, "NGC 5882 Sector")),
  ("NGC 5979 Sector", sector.HASector(vector3.Vector3(5443.01172, -831.33594, 7119.16406), 100.0, "NGC 5979 Sector")),
  ("Fine Ring Sector", sector.HASector(vector3.Vector3(513.22656, 34.89844, 857.54297), 100.0, "Fine Ring Sector")),
  ("NGC 6058 Sector", sector.HASector(vector3.Vector3(-5472.94922, 6794.40625, 2587.05273), 100.0, "NGC 6058 Sector")),
  ("White Eyed Pea Sector", sector.HASector(vector3.Vector3(-3882.09375, 7841.04688, 8212.63281), 100.0, "White Eyed Pea Sector")),
  ("NGC 6153 Sector", sector.HASector(vector3.Vector3(1670.20703, 508.18359, 5110.00586), 100.0, "NGC 6153 Sector")),
  ("NGC 6210 Sector", sector.HASector(vector3.Vector3(-2861.42969, 3248.40625, 3057.78906), 100.0, "NGC 6210 Sector")),
  ("IC 4634 Sector", sector.HASector(vector3.Vector3(-51.17578, 1584.93750, 7330.44141), 100.0, "IC 4634 Sector")),
  ("Bug Sector", sector.HASector(vector3.Vector3(619.48828, 65.26953, 3342.45117), 100.0, "Bug Sector")),
  ("Box Sector", sector.HASector(vector3.Vector3(-1759.31250, 2758.81250, 10292.41406), 100.0, "Box Sector")),
  ("NGC 6326 Sector", sector.HASector(vector3.Vector3(4041.22266, -1606.91406, 10103.77734), 100.0, "NGC 6326 Sector")),
  ("NGC 6337 Sector", sector.HASector(vector3.Vector3(901.19531, -94.06641, 4815.49609), 100.0, "NGC 6337 Sector")),
  ("Little Ghost Sector", sector.HASector(vector3.Vector3(-204.10547, 503.68359, 4869.76758), 100.0, "Little Ghost Sector")),
  ("IC 4663 Sector", sector.HASector(vector3.Vector3(1523.71094, -927.08984, 6250.50586), 100.0, "IC 4663 Sector")),
  ("NGC 6445 Sector", sector.HASector(vector3.Vector3(-632.58594, 306.07031, 4444.78906), 100.0, "NGC 6445 Sector")),
  ("Cat's Eye Sector", sector.HASector(vector3.Vector3(-2809.64062, 1626.06641, -320.11719), 100.0, "Cat's Eye Sector")),
  ("IC 4673 Sector", sector.HASector(vector3.Vector3(-840.65625, -561.13281, 13361.82812), 100.0, "IC 4673 Sector")),
  ("Red Spider Sector", sector.HASector(vector3.Vector3(-526.06250, 36.65234, 2953.28906), 100.0, "Red Spider Sector")),
  ("NGC 6565 Sector", sector.HASector(vector3.Vector3(-359.02734, -473.17188, 5870.02539), 100.0, "NGC 6565 Sector")),
  ("NGC 6563 Sector", sector.HASector(vector3.Vector3(80.49219, -393.89844, 3073.81836), 100.0, "NGC 6563 Sector")),
  ("NGC 6572 Sector", sector.HASector(vector3.Vector3(-4333.99219, 1608.39453, 6282.48047), 100.0, "NGC 6572 Sector")),
  ("NGC 6567 Sector", sector.HASector(vector3.Vector3(-851.64453, -51.31250, 4112.42969), 100.0, "NGC 6567 Sector")),
  ("IC 4699 Sector", sector.HASector(vector3.Vector3(4137.37891, -4924.67578, 19464.83203), 100.0, "IC 4699 Sector")),
  ("NGC 6629 Sector", sector.HASector(vector3.Vector3(-1041.14844, -568.92188, 6289.06445), 100.0, "NGC 6629 Sector")),
  ("NGC 6644 Sector", sector.HASector(vector3.Vector3(-1420.00781, -1245.23438, 9616.28516), 100.0, "NGC 6644 Sector")),
  ("IC 4776 Sector", sector.HASector(vector3.Vector3(-855.50781, -5561.94922, 23330.94141), 100.0, "IC 4776 Sector")),
  ("Ring Sector", sector.HASector(vector3.Vector3(-1977.24219, 552.30859, 998.77734), 100.0, "Ring Sector")),
  ("Phantom Streak Sector", sector.HASector(vector3.Vector3(-3611.90625, -306.19141, 5395.40234), 100.0, "Phantom Streak Sector")),
  ("NGC 6751 Sector", sector.HASector(vector3.Vector3(-3105.76172, -657.87109, 5557.10742), 100.0, "NGC 6751 Sector")),
  ("IC 4846 Sector", sector.HASector(vector3.Vector3(-11325.47656, -4178.53516, 21663.64062), 100.0, "IC 4846 Sector")),
  ("IC 1297 Sector", sector.HASector(vector3.Vector3(215.14844, -2871.37109, 7249.06445), 100.0, "IC 1297 Sector")),
  ("NGC 6781 Sector", sector.HASector(vector3.Vector3(-3394.65625, -266.91406, 3796.71680), 100.0, "NGC 6781 Sector")),
  ("NGC 6790 Sector", sector.HASector(vector3.Vector3(-2014.89844, -362.12500, 2588.25195), 100.0, "NGC 6790 Sector")),
  ("NGC 6803 Sector", sector.HASector(vector3.Vector3(-4117.21484, -407.53516, 3920.77148), 100.0, "NGC 6803 Sector")),
  ("NGC 6804 Sector", sector.HASector(vector3.Vector3(-3573.00781, -400.99609, 3474.59766), 100.0, "NGC 6804 Sector")),
  ("Little Gem Sector", sector.HASector(vector3.Vector3(-2493.94922, -1844.14062, 5136.08398), 100.0, "Little Gem Sector")),
  ("Blinking Sector", sector.HASector(vector3.Vector3(-1938.14453, 443.09766, 217.39844), 100.0, "Blinking Sector")),
  ("NGC 6842 Sector", sector.HASector(vector3.Vector3(-5476.70312, 62.83203, 2449.84766), 100.0, "NGC 6842 Sector")),
  ("Dumbbell Sector", sector.HASector(vector3.Vector3(-958.21094, -70.98438, 535.52734), 100.0, "Dumbbell Sector")),
  ("NGC 6852 Sector", sector.HASector(vector3.Vector3(-3276.57812, -1251.89844, 3563.25391), 100.0, "NGC 6852 Sector")),
  ("NGC 6884 Sector", sector.HASector(vector3.Vector3(-2457.28516, 309.00391, 340.97656), 100.0, "NGC 6884 Sector")),
  ("NGC 6879 Sector", sector.HASector(vector3.Vector3(-17024.14453, -3171.56250, 10971.31250), 100.0, "NGC 6879 Sector")),
  ("NGC 6886 Sector", sector.HASector(vector3.Vector3(-7731.72266, -1205.87500, 4445.93750), 100.0, "NGC 6886 Sector")),
  ("NGC 6891 Sector", sector.HASector(vector3.Vector3(-6740.87891, -1781.75781, 4861.67578), 100.0, "NGC 6891 Sector")),
  ("IC 4997 Sector", sector.HASector(vector3.Vector3(-6681.43359, -1526.47266, 4126.53711), 100.0, "IC 4997 Sector")),
  ("Blue Flash Sector", sector.HASector(vector3.Vector3(-2599.53125, 500.30469, 1411.42969), 100.0, "Blue Flash Sector")),
  ("Fetus Sector", sector.HASector(vector3.Vector3(-2881.56641, 277.95312, -171.19727), 100.0, "Fetus Sector")),
  ("Saturn Sector", sector.HASector(vector3.Vector3(-2623.43359, -2952.78906, 3382.10742), 100.0, "Saturn Sector")),
  ("NGC 7026 Sector", sector.HASector(vector3.Vector3(-5998.94141, 41.88672, 104.71094), 100.0, "NGC 7026 Sector")),
  ("NGC 7027 Sector", sector.HASector(vector3.Vector3(-3380.22266, -207.56641, 301.67773), 100.0, "NGC 7027 Sector")),
  ("NGC 7048 Sector", sector.HASector(vector3.Vector3(-5596.30859, -166.13281, 117.22656), 100.0, "NGC 7048 Sector")),
  ("IC 5117 Sector", sector.HASector(vector3.Vector3(-2988.11719, -266.68359, 5.21484), 100.0, "IC 5117 Sector")),
  ("IC 5148 Sector", sector.HASector(vector3.Vector3(-86.22656, -2376.86719, 1828.40430), 100.0, "IC 5148 Sector")),
  ("IC 5217 Sector", sector.HASector(vector3.Vector3(-9198.58594, -884.61719, -1721.46875), 100.0, "IC 5217 Sector")),
  ("Helix Sector", sector.HASector(vector3.Vector3(-222.85938, -583.28516, 304.50195), 100.0, "Helix Sector")),
  ("NGC 7354 Sector", sector.HASector(vector3.Vector3(-3995.72266, 168.55469, -1282.88672), 100.0, "NGC 7354 Sector")),
  ("Blue Snowball Sector", sector.HASector(vector3.Vector3(-5024.05469, -1663.03516, -1497.73438), 100.0, "Blue Snowball Sector")),
  ("G2 Dust Cloud Sector", sector.HASector(vector3.Vector3(27.12500, -22.49609, 27899.97656), 100.0, "G2 Dust Cloud Sector")),
  ("Regor Sector", sector.HASector(vector3.Vector3(1099.23828, -146.67188, -133.58008), 100.0, "Regor Sector")),
  ("ICZ", sector.HASectorCluster(vector3.Vector3(60, -120, 55), 100, 40, "ICZ", [
    sector.HASector(vector3.Vector3(11, -118, 56), 40, "ICZ"),
    sector.HASector(vector3.Vector3(17, -122, 32), 40, "ICZ"),
    sector.HASector(vector3.Vector3(32, -170, 13), 40, "ICZ"),
    sector.HASector(vector3.Vector3(34, -115, 100), 40, "ICZ"),
    sector.HASector(vector3.Vector3(45, -118, 85), 40, "ICZ"),
    sector.HASector(vector3.Vector3(53, -130, 14), 40, "ICZ"),
    sector.HASector(vector3.Vector3(62, -105, 22), 40, "ICZ"),
    sector.HASector(vector3.Vector3(65, -117, 47), 40, "ICZ"),
    sector.HASector(vector3.Vector3(67, -119, 24), 40, "ICZ"),
    sector.HASector(vector3.Vector3(75, -135, 19), 40, "ICZ"),
    sector.HASector(vector3.Vector3(78, -100, 16), 40, "ICZ"),
    sector.HASector(vector3.Vector3(79, -167, 25), 40, "ICZ"),
    sector.HASector(vector3.Vector3(81, -150, 96), 40, "ICZ"),
    sector.HASector(vector3.Vector3(82, -131, 0), 40, "ICZ"),
    sector.HASector(vector3.Vector3(92, -95, 11), 40, "ICZ"),
    sector.HASector(vector3.Vector3(106, -95, 0), 40, "ICZ"),
  ])),
])
# Sort by increasing size for checks
ha_sectors = collections.OrderedDict(sorted(ha_sectors.items(), key=lambda t: t[1].size))



ha_permit_regions = {
  "BLEIA1": (vector3.Vector3(-43, 155, 37500), 512),
  "BLEIA2": (vector3.Vector3(-43, 155, 37000), 512),
  "BLEIA3": (vector3.Vector3(-43, 155, 36500), 512),
  "BLEIA4": (vector3.Vector3(450, 155, 37000), 512),
  "BLEIA5": (vector3.Vector3(-450, 155, 37000), 512),
  "BOVOMIT": (vector3.Vector3(-20070, 90, -6930), 512),
  "DRYMAN": (vector3.Vector3(19100, 20, 21160), 512),
  "FROADIK": (vector3.Vector3(-18860, -200, 14300), 512),
  "HYPONIA": (vector3.Vector3(-23020, -10, 24080), 512),
  "PRAEI1": (vector3.Vector3(-1000, -155, 54000), 512),
  "PRAEI2": (vector3.Vector3(-1000, -155, 54400), 512),
  "PRAEI3": (vector3.Vector3(-1000, -155, 53600), 512),
  "PRAEI4": (vector3.Vector3(-1000, -555, 54000), 512),
  "PRAEI5": (vector3.Vector3(-1000, 455, 54000), 512),
  "PRAEI6": (vector3.Vector3(-500, -100, 53500), 512),
  "SIDGOIR": (vector3.Vector3(-24120, 10, -1220), 100),
}

