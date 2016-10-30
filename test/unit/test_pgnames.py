import unittest
import sys

sys.path.insert(0, '../..')
import env
import pgnames
import pgdata
import vector3 as v3
del sys.path[0]


class TestPGNames(unittest.TestCase):
  def setUp(self):
    env.set_verbosity(0)

  def test_sector_names(self):
    self.assertEqual(pgnames.get_sector_name(v3.Vector3(34, 55, 18278)), "Dryau Aowsy")
    self.assertEqual(pgnames.get_sector_name(v3.Vector3(0.0, 0.0, 0.0)), "Jastreb Sector")
    self.assertEqual(pgnames.get_sector_name(v3.Vector3(-904, -103, -11840)), "Soad")
    self.assertEqual(pgnames.get_sector_name(v3.Vector3(8322, 1271, -1169)), "NGC 2818 Sector")
    self.assertEqual(pgnames.get_sector_name(v3.Vector3(4000, 1300, 7000)), "Teakooe")
    self.assertEqual(pgnames.get_sector_name(v3.Vector3(4600, 1550, 7330)), "NGC 5882 Sector")

  def test_sector_names_noha(self):
    self.assertEqual(pgnames.get_sector_name(v3.Vector3(34, 55, 18278), allow_ha=False), "Dryau Aowsy")
    self.assertEqual(pgnames.get_sector_name(v3.Vector3(0.0, 0.0, 0.0), allow_ha=False), "Wregoe")
    self.assertEqual(pgnames.get_sector_name(v3.Vector3(-904, -103, -11840), allow_ha=False), "Soad")
    self.assertEqual(pgnames.get_sector_name(v3.Vector3(8322, 1271, -1169), allow_ha=False), "Praea Thiae")
    self.assertEqual(pgnames.get_sector_name(v3.Vector3(4000, 1300, 7000), allow_ha=False), "Teakooe")
    self.assertEqual(pgnames.get_sector_name(v3.Vector3(4600, 1550, 7330), allow_ha=False), "Teakooe")

  def test_sector_positions(self):
    test1 = pgnames.get_sector("Wregoe")
    self.assertEqual(test1.name, "Wregoe")
    self.assertEqual(test1.centre, v3.Vector3(-65.0, -25.0, -1065.0) + (640, 640, 640))
    self.assertEqual(test1.size, 1280.0)
    test2 = pgnames.get_sector("GRIA EAEC")
    self.assertEqual(test2.name, "Gria Eaec")
    self.assertEqual(test2.centre, v3.Vector3(-2625.0, -1305.0, 15575.0) + (640, 640, 640))
    self.assertEqual(test2.size, 1280.0)
    test2 = pgnames.get_sector("core sys sector")
    self.assertEqual(test2.name, "Core Sys Sector")
    self.assertEqual(test2.centre, v3.Vector3(0, 0, 0))
    self.assertEqual(test2.size, 50.0)

  def test_system_positions(self):
    test1 = pgnames.get_system("Wregoe AC-D d12-0")
    self.assertEqual(test1.name, "Wregoe AC-D d12-0")
    self.assertEqual(test1.position, v3.Vector3(-65.0, -25.0, -25.0) + (40, 40, 40))
    self.assertEqual(test1.uncertainty, 80.0 / 2)
    test2 = pgnames.get_system("Eol Prou RS-T d3-94")
    self.assertEqual(test2.name, "Eol Prou RS-T d3-94")
    self.assertEqual(test2.position, v3.Vector3(-9585.0, -985.0, 19735.0) + (40, 40, 40))
    self.assertEqual(test2.uncertainty, 80.0 / 2)
    test3 = pgnames.get_system("Pipe (stem) Sector AL-X c1-12")
    self.assertEqual(test3.name, "Pipe (stem) Sector AL-X c1-12")
    self.assertEqual(test3.position, v3.Vector3(-25.0, 135.0, 455.0) + (20, 20, 20))
    self.assertEqual(test3.uncertainty, 40.0 / 2)
    test4 = pgnames.get_system("Pipe (stem) Sector AL-X c1-12", allow_ha=False)
    self.assertTrue(test4.name.startswith("Praea Euq RE-Q c5-")) # In case we add special N2 handling later
    self.assertEqual(test4.position, v3.Vector3(-25.0, 135.0, 455.0) + (20, 20, 20))
    self.assertEqual(test4.uncertainty, 40.0 / 2)

  def test_pg_system_names_good(self):
    self.assertTrue(pgnames.is_pg_system_name("Wregoe AC-D d12-0", strict=True))
    self.assertTrue(pgnames.is_pg_system_name("Soad YY-Z d5", strict=True))
    self.assertTrue(pgnames.is_pg_system_name("Eos Aowsy AA-A h0", strict=True))
    self.assertTrue(pgnames.is_pg_system_name("Pipe (stem) Sector GL-A b3-2", strict=True))

  def test_pg_system_names_bad(self):
    self.assertFalse(pgnames.is_pg_system_name("Wregoe ACD d12-0", strict=False))
    self.assertFalse(pgnames.is_pg_system_name("Eos Aowsy AC-D 12-0", strict=False))
    self.assertFalse(pgnames.is_pg_system_name("Wregoe AC-D d1-A", strict=False))

  def test_pg_system_names_nostrict(self):
    self.assertFalse(pgnames.is_pg_system_name("Rubbish Fake Name AB-C d1-23", strict=True))
    self.assertTrue(pgnames.is_pg_system_name("Rubbish Fake Name AB-C d1-23", strict=False))

  def test_canonical_name(self):
    self.assertEqual(pgnames.get_canonical_name("eos aowsy aa-a D12-5155"), "Eos Aowsy AA-A d12-5155")
    self.assertEqual(pgnames.get_canonical_name("WrEgOe Ac-D d0-0"), "Wregoe AC-D d0")
    self.assertEqual(pgnames.get_canonical_name("PIPE (STEM) SECTOR AA-A H0"), "Pipe (stem) Sector AA-A h0")

  def test_sector_fragments(self):
    self.assertEqual(pgnames.get_sector_fragments("dryau aowsy"), ["Dry","au","Ao","wsy"])
    self.assertEqual(pgnames.get_sector_fragments("SOAD"), ["S","oa","d"])
    self.assertEqual(pgnames.get_sector_fragments("WrEGoE"), ["Wr","e","g","oe"])

  def test_sector_Fragments_long(self):
    self.assertIsNone(pgnames.get_sector_fragments("Wharrgarbl", allow_long=False))
    self.assertEqual(pgnames.get_sector_fragments("Wharrgarbl", allow_long=True), ["Wh","a","rr","g","a","rb","l"])

  def test_format_sector_name(self):
    self.assertEqual(pgnames.format_sector_name(["Dry","au","Ao","wsy"]), "Dryau Aowsy")
    self.assertEqual(pgnames.format_sector_name(["Wr","e","go","e"]), "Wregoe")
    self.assertEqual(pgnames.format_sector_name(["Lys","oo","ch"]), "Lysooch")

  def test_valid_sector_name(self):
    self.assertTrue(pgnames.is_valid_sector_name("Wregoe"))
    self.assertTrue(pgnames.is_valid_sector_name(["Wr","e","g","oe"]))
    self.assertTrue(pgnames.is_valid_sector_name("Praea Thiae"))
    self.assertTrue(pgnames.is_valid_sector_name(["Pr","aea","Th","iae"]))
    self.assertTrue(pgnames.is_valid_sector_name("Soad"))
    self.assertTrue(pgnames.is_valid_sector_name(["S","oa","d"]))
    self.assertFalse(pgnames.is_valid_sector_name("Col 285"))
    self.assertFalse(pgnames.is_valid_sector_name("Prfou Aowsy"))
    self.assertFalse(pgnames.is_valid_sector_name(["Pr","f","Ao","wsy"]))
    self.assertFalse(pgnames.is_valid_sector_name("Wharrgarbl"))
    self.assertFalse(pgnames.is_valid_sector_name(["Wh","a","rr","g","a","rb","l"]))

  def test_boxel_origin(self):
    self.assertEqual(pgnames.get_boxel_origin(v3.Vector3(0, 0, 0), 'a'), v3.Vector3(-5, -5, -5))
    self.assertEqual(pgnames.get_boxel_origin(v3.Vector3(0, 0, 0), 'b'), v3.Vector3(-5, -5, -5))
    self.assertEqual(pgnames.get_boxel_origin(v3.Vector3(0, 0, 0), 'c'), v3.Vector3(-25, -25, -25))
    self.assertEqual(pgnames.get_boxel_origin(v3.Vector3(0, 0, 0), 'd'), v3.Vector3(-65, -25, -25))
    self.assertEqual(pgnames.get_boxel_origin(v3.Vector3(0, 0, 0), 'e'), v3.Vector3(-65, -25, -105))
    self.assertEqual(pgnames.get_boxel_origin(v3.Vector3(0, 0, 0), 'f'), v3.Vector3(-65, -25, -105))
    self.assertEqual(pgnames.get_boxel_origin(v3.Vector3(0, 0, 0), 'g'), v3.Vector3(-65, -25, -425))
    self.assertEqual(pgnames.get_boxel_origin(v3.Vector3(0, 0, 0), 'h'), v3.Vector3(-65, -25, -1065))

  def test_system_fragments(self):
    test1 = pgnames.get_system_fragments("eos aowsy ab-c d456", ensure_canonical=True)
    self.assertIsNotNone(test1)
    self.assertEqual(test1['SectorName'], "Eos Aowsy")
    self.assertEqual(test1['L1'], 'A')
    self.assertEqual(test1['L2'], 'B')
    self.assertEqual(test1['L3'], 'C')
    self.assertEqual(test1['MCode'], 'd')
    self.assertEqual(test1['N1'], 0)
    self.assertEqual(test1['N2'], 456)
    test2 = pgnames.get_system_fragments("wregoe xe-a f3-0", ensure_canonical=True)
    self.assertIsNotNone(test2)
    self.assertEqual(test2['SectorName'], "Wregoe")
    self.assertEqual(test2['L1'], 'X')
    self.assertEqual(test2['L2'], 'E')
    self.assertEqual(test2['L3'], 'A')
    self.assertEqual(test2['MCode'], 'f')
    self.assertEqual(test2['N1'], 3)
    self.assertEqual(test2['N2'], 0)
    test3 = pgnames.get_system_fragments("PIPE (STEM) SECTOR DE-F A119-3053", ensure_canonical=True)
    self.assertIsNotNone(test3)
    self.assertEqual(test3['SectorName'], "Pipe (stem) Sector")
    self.assertEqual(test3['L1'], 'D')
    self.assertEqual(test3['L2'], 'E')
    self.assertEqual(test3['L3'], 'F')
    self.assertEqual(test3['MCode'], 'a')
    self.assertEqual(test3['N1'], 119)
    self.assertEqual(test3['N2'], 3053)
    test4 = pgnames.get_system_fragments("eos aowsy ab-c d456", ensure_canonical=False)
    self.assertIsNotNone(test4)
    self.assertEqual(test4['SectorName'], "eos aowsy")
    self.assertEqual(test4['L1'], 'a')
    self.assertEqual(test4['L2'], 'b')
    self.assertEqual(test4['L3'], 'c')
    self.assertEqual(test4['MCode'], 'd')
    self.assertEqual(test4['N1'], 0)
    self.assertEqual(test4['N2'], 456)

  def test_format_system_name(self):
    test1 = {'SectorName': 'Wregoe', 'L1': 'e', 'L2': 'g', 'L3': 'y', 'MCode': 'F', 'N1': 5, 'N2': 17}
    self.assertEqual(pgnames.format_system_name(test1), 'Wregoe EG-Y f5-17')
    test2 = {'SectorName': 'Eol Prou', 'L1': 'x', 'L2': 'E', 'L3': 'a', 'MCode': 'E', 'N1': 0, 'N2': 73}
    self.assertEqual(pgnames.format_system_name(test2), 'Eol Prou XE-A e73')
    self.assertIsNone(pgnames.format_system_name(None))
    self.assertRaises(ValueError, pgnames.format_system_name, {})

  def test_ha_sectors(self):
    test1 = pgnames.get_ha_sectors()
    self.assertEqual(len(test1), len(pgdata.ha_sectors))
    self.assertEqual([s.lower() for s in test1.keys()], list(pgdata.ha_sectors.keys()))
    test2 = pgnames.get_ha_sectors((4616.625, 1543.21875, 7331.09375), 50)
    self.assertEqual(len(test2), 1)
    self.assertTrue("NGC 5882 Sector" in test2)
    test3 = pgnames.get_ha_sectors((616.52344, -446.42578, -1107.67383), 50)
    self.assertEqual(len(test3), 4)
    self.assertEqual(list(test3.keys()), ["Orion Sector", "Trapezium Sector", "Running Man Sector", "NGC 1981 Sector"])
