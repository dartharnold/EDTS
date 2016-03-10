#!/usr/bin/env python

from __future__ import print_function
import argparse
import logging
import re
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
c3_suffixes = {
  "Eu": ["rl", "q", "r"],
  "Au": ["b", "c", "wsy"],
  "Ao": ["c", "d"]
}


c1_positions = [
  "Synoo",
  "Screa",
  "Wredg"
]

c3_positions_y0_z0_index = 2
c3_positions_y0_z0_subindex = 1
c3_positions_y0 = [
  (("Hyp", "Ph"), ("Ae", "Th")),
  (("Bl", "By"), ("Ai", "Eu")),
  (("Pl", "Pr"), ("Ai", "Ao")),
  (("Ch", "Ty"), ("Th", "Au"))
]


