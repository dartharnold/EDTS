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

  def test_range(self):
    s = ship.Ship("6A", 521.8, 32)
    self.assertAlmostEqual(s.range(), 39.63, 2)
    s.range_boost = 10.5
    self.assertAlmostEqual(s.range(), 50.13, 2)
    s.supercharge('N')
    self.assertAlmostEqual(s.range(), 200.53, 2)

  def test_cost(self):
    s = ship.Ship("6A", 521.8, 32)
    self.assertAlmostEqual(s.cost(39.63), 8, 2)
    s.supercharge('N')
    self.assertAlmostEqual(s.cost(39.63), 0.22, 2)
    s.range_boost = 10.5
    self.assertAlmostEqual(s.cost(39.63), 0.12, 2)

  def test_reserve_tank(self):
    s = ship.Ship("6A", 521.8, 32, reserve_tank = 2.0)
    self.assertEqual(s.unladen_mass, 523.8)
    self.assertAlmostEqual(s.range(), 39.49, 2)
    self.assertAlmostEqual(s.cost(39.49), 8, 2)
    s.range_boost = 10.5
    self.assertAlmostEqual(s.range(), 49.99, 2)
    self.assertAlmostEqual(s.cost(41.42), 4.91, 2)
    s.supercharge('N')
    self.assertAlmostEqual(s.range(), 199.95, 2)
    self.assertAlmostEqual(s.cost(100.0), 1.32, 2)
