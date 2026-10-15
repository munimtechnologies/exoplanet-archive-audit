import unittest

import geometry_census as gc

DR25 = "<a refstr=Q1_Q17_DR25_KOI_TABLE href=https://exoplanetarchive.ipac.caltech.edu/docs/Kepler_KOI_docs.html target=ref>Q1-Q17 DR25 KOI Table</a>"


def row(**kw):
    base = {c: "" for c in gc.COLS}
    base.update({"pl_name": "X b", "hostname": "X", "tran_flag": "1", "cb_flag": "0"})
    base.update({k: str(v) for k, v in kw.items()})
    return base


class GeometryTest(unittest.TestCase):
    def test_kepler_1943_b_cannot_transit(self):
        # Composite values on 2026-10-15.
        r = gc.check(row(pl_name="Kepler-1943 b", pl_orbsmax=0.05975, st_rad=0.973, pl_ratdor=1.769,
                         pl_ratdor_reflink=DR25, pl_orbincl=56.15, pl_orbincl_reflink=DR25, pl_rade=1.54869189,
                         pl_orbeccen=0, pl_imppar=0.2278, pl_ratror=0.007534))
        self.assertAlmostEqual(r["dor_calc"], 13.205, delta=0.01)
        self.assertAlmostEqual(r["b_calc"], 7.355, delta=0.01)
        self.assertEqual((r["flag_dor"], r["flag_transit"], r["flag_imppar"]), ("yes", "yes", "ok"))
        self.assertEqual(r["dor_ref"], "Q1-Q17 DR25 KOI Table")

    def test_kepler_91_b_is_consistent(self):
        r = gc.check(row(pl_orbsmax=0.0731, st_rad=6.30, pl_ratdor=2.496, pl_orbincl=69.68, pl_rade=15.0))
        self.assertAlmostEqual(r["dor_ratio"], 1.0, delta=0.01)
        self.assertAlmostEqual(r["b_calc"], 0.866, delta=0.005)
        self.assertEqual((r["flag_dor"], r["flag_transit"]), ("ok", "ok"))

    def test_kepler_1935_b_ratror_and_kepler_fallback(self):
        r = gc.check(row(pl_orbper=3.951400042, st_mass=0.845, st_rad=0.899, pl_orbincl=79.61, pl_ratdor=6.75,
                         pl_rade=2.50271696, pl_ratror=0.661038, pl_imppar=1.6426))
        self.assertEqual(r["a_from"], "Kepler")
        self.assertAlmostEqual(r["a_used"], 0.04625, delta=0.0001)
        self.assertAlmostEqual(r["b_calc"], 1.995, delta=0.01)
        self.assertEqual(r["flag_transit"], "yes")
        self.assertEqual(r["flag_ratror"], "yes")
        self.assertEqual(r["flag_dor"], "yes")
        self.assertEqual(r["flag_imppar"], "ok")  # b from the row is above 1 as well

    def test_imppar_above_one_with_central_geometry(self):
        r = gc.check(row(pl_orbsmax=0.046505, st_rad=1.0, pl_orbincl=90, pl_imppar=1.7, pl_rade=2.0))
        self.assertAlmostEqual(r["dor_calc"], 10.0, places=3)
        self.assertEqual(r["flag_imppar"], "yes")

    def test_eccentric_orbits_not_flagged_for_transit(self):
        r = gc.check(row(pl_orbsmax=0.1, st_rad=1.0, pl_orbincl=80, pl_orbeccen=0.3))
        self.assertEqual(r["flag_transit"], "eccentric")

    def test_white_dwarf_and_circumbinary_skipped(self):
        self.assertIsNone(gc.check(row(pl_orbsmax=0.02, st_rad=0.0131, pl_orbincl=88.8)))
        self.assertIsNone(gc.check(row(cb_flag=1, pl_orbsmax=0.3, st_rad=1.0, pl_orbincl=89.9)))
        self.assertIsNone(gc.check(row(tran_flag=0, pl_orbsmax=0.3, st_rad=1.0)))

    def test_by_source(self):
        res = [gc.check(row(pl_orbsmax=0.046505, st_rad=1.0, pl_ratdor=d, pl_ratdor_reflink=DR25)) for d in (10, 2, 30)]
        refs = gc.by_source(res, "dor", "dor_ref")
        self.assertEqual(refs[0]["source"], "Q1-Q17 DR25 KOI Table")
        self.assertEqual((refs[0]["tested"], refs[0]["flagged"]), (3, 2))


if __name__ == "__main__":
    unittest.main()
