import unittest
import sys

sys.path.insert(0, '../..')
from edtslib import env
from edtslib import fsd
from edtslib import vector3 as v3
del sys.path[0]


class TestFSD(unittest.TestCase):
  def setUp(self):
    env.set_verbosity(0)
    env.start()

  def tearDown(self):
    env.stop()

  def test_drive(self):
    self.assertEqual(fsd.FSD("6A").drive, "6A")
    self.assertEqual(fsd.FSD("A6").drive, "6A")
    self.assertEqual(fsd.FSD("E2").drive, "2E")

  def test_range(self):
    f = fsd.FSD("6A")
    self.assertAlmostEqual(f.range(mass=521.8, fuel=32), 39.63, 2)
    self.assertAlmostEqual(f.range(mass=521.8, fuel=16), 40.81, 2)
    self.assertAlmostEqual(f.range(mass=521.8, fuel=12), 41.12, 2)
    self.assertAlmostEqual(f.range(mass=521.8, fuel=8), 41.43, 2)
    f = fsd.FSD("2A")
    self.assertAlmostEqual(f.range(mass=20.0, fuel=4), 32.48, 2)
    self.assertAlmostEqual(f.range(mass=20.0, fuel=2), 35.43, 2)
    self.assertAlmostEqual(f.range(mass=20.0, fuel=1), 37.12, 2)
    f = fsd.FSD("2E")
    self.assertAlmostEqual(f.range(mass=20.0, fuel=4), 14.77, 2)
    self.assertAlmostEqual(f.range(mass=20.0, fuel=2), 16.11, 2)
    self.assertAlmostEqual(f.range(mass=20.0, fuel=1), 16.88, 2)

  def test_max_range(self):
    f = fsd.FSD("6A")
    self.assertAlmostEqual(f.max_range(mass=521.8), 41.43, 2)
    f = fsd.FSD("2A")
    self.assertAlmostEqual(f.max_range(mass=20.0), 37.29, 2)
    f = fsd.FSD("2E")
    self.assertAlmostEqual(f.max_range(mass=20.0), 17.21, 2)

  def test_cost(self):
    f = fsd.FSD("6A")
    self.assertAlmostEqual(f.cost(41.42, mass=521.8, fuel=8), 8.00, 2)
    self.assertAlmostEqual(f.cost(15.0, mass=521.8, fuel=32), 0.64, 2)
    self.assertAlmostEqual(f.cost(50.0, mass=521.8, fuel=32), 14.64, 2)
    self.assertEqual(f.cost(0.0, mass=521.8, fuel=32), 0.0)

  def test_fuel_weight_range(self):
    f = fsd.FSD("6A")
    wmin, wmax = f.fuel_weight_range(41.41, mass=521.8)
    self.assertAlmostEqual(wmin, 7.99, 2)
    self.assertAlmostEqual(wmax, 8.21, 2)
    wmin, wmax = f.fuel_weight_range(15.0, mass=521.8)
    self.assertAlmostEqual(wmin, 0.55, 2)
    self.assertAlmostEqual(wmax, 941.39, 2)
    wmin, wmax = f.fuel_weight_range(300.0, mass=521.8)
    self.assertIsNone(wmin)
    self.assertIsNone(wmax)
    wmin, wmax = f.fuel_weight_range(300.0, mass=521.8, allow_invalid=True)
    self.assertGreater(wmin, 10**10)
    self.assertLess(wmax, 0)

  def test_boost(self):
    f = fsd.FSD("6A")
    f.supercharge('D')
    self.assertAlmostEqual(f.range(mass=521.8, fuel=32), 49.54, 2)
    self.assertAlmostEqual(f.cost(41.42, mass=521.8, fuel=32), 5.02, 2)
    wmin, wmax = f.fuel_weight_range(41.41, mass=521.8)
    self.assertAlmostEqual(wmin, 4.40, 2)
    self.assertAlmostEqual(wmax, 140.72, 2)
    f.supercharge(2)
    self.assertAlmostEqual(f.range(mass=521.8, fuel=32), 59.45, 2)
    self.assertAlmostEqual(f.cost(41.42, mass=521.8, fuel=32), 3.13, 2)
    wmin, wmax = f.fuel_weight_range(41.41, mass=521.8)
    self.assertAlmostEqual(wmin, 2.71, 2)
    self.assertAlmostEqual(wmax, 273.22, 2)
    f.supercharge(3)
    self.assertAlmostEqual(f.range(mass=521.8, fuel=32), 79.26, 2)
    self.assertAlmostEqual(f.cost(41.42, mass=521.8, fuel=32), 1.48, 2)
    wmin, wmax = f.fuel_weight_range(41.41, mass=521.8)
    self.assertAlmostEqual(wmin, 1.28, 2)
    self.assertAlmostEqual(wmax, 538.22, 2)
    f.supercharge('N')
    self.assertAlmostEqual(f.range(mass=521.8, fuel=32), 158.53, 2)
    self.assertAlmostEqual(f.cost(41.42, mass=521.8, fuel=32), 0.24, 2)
    wmin, wmax = f.fuel_weight_range(41.41, mass=521.8)
    self.assertAlmostEqual(wmin, 0.21, 2)
    self.assertAlmostEqual(wmax, 1598.25, 2)
