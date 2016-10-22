import unittest
import sys

sys.path.insert(0, '../..')
import pgnames
import vector3 as v3
del sys.path[0]


class TestPGNames(unittest.TestCase):
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
