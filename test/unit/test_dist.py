import unittest
import sys

sys.path.insert(0, '../..')
from edtslib import dist
del sys.path[0]

class TestDist(unittest.TestCase):
  def test_km(self):
    d = dist.Kilometres(1.5)
    self.assertEqual(d.metres, 1500)
    self.assertEqual(d.to_string(), "1.5km")

  def test_mm(self):
    d = dist.Megametres(0.1)
    self.assertEqual(d.metres, 100000)
    self.assertEqual(d.to_string(), "0.1Mm")

  def test_ls(self):
    d = dist.Lightseconds(1)
    self.assertEqual(d.metres, 299792000)
    self.assertEqual(d.to_string(), "1Ls")

  def test_ly(self):
    d = dist.Lightyears(0.22)
    self.assertAlmostEqual(d.metres, 0.22 * 31557600 * 299.792 * 1000000, delta=2)
    self.assertEqual(d.to_string(), "0.22Ly")

  def test_convert(self):
    d = dist.Lightyears(0.22)
    self.assertAlmostEqual(d.lightseconds, 6942672)
    self.assertAlmostEqual(d.megametres, 2081357524, delta=2)
    self.assertAlmostEqual(d.kilometres, 2081357524224)
