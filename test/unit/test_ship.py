import unittest
import sys

sys.path.insert(0, '../..')
from edtslib import env
from edtslib import ship
from edtslib import vector3 as v3
del sys.path[0]


class TestShip(unittest.TestCase):
  def setUp(self):
    env.set_verbosity(0)
    env.start()

  def tearDown(self):
    env.stop()
  
  