# -*- coding: utf-8 -*-

"""
EDTS: Elite Dangerous Travel Scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A library and collection of scripts to assist in
travel and exploration in Elite: Dangerous.

:copyright: (c) 2015-2017 Andy Martin
:license: 3-clause BSD, see LICENSE for more details.

"""

from . import defs

__title__ = 'EDTS'
__author__ = 'Alot'
__license__ = 'BSD'
__copyright__ = 'Copyright 2015-2017 Andy Martin'
__version__ = defs.version


# Convenience includes
from .calc import Calc
from .db_sqlite3 import open_db
from .defs import version
from .env import use
from .fsd import FSD
from .ship import Ship
from .station import Station
from .system import System, KnownSystem, PGSystem, PGSystemPrototype
from .vector3 import Vector3, Vector3M