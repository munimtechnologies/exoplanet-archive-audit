import unittest

import insol_census as ic

EXOFOP = "<a refstr=EXOFOP href=https://exofop.ipac.caltech.edu/tess/view_toi.php target=ref>ExoFOP</a>"


def row(**kw):
    base = {"pl_name": "X b", "hostname": "X", "discoverymethod": "Transit", "pl_orbper": "", "pl_orbsmax": "",
            "st_mass": "", "st_lum": "", "st_lum_reflink": "", "st_rad": "", "st_teff": "", "pl_insol": "",
            "pl_insol_reflink": "", "pl_eqt": "", "pl_eqt_reflink": ""}
    base.update({k: str(v) for k, v in kw.items()})
    return base


class CensusTest(unittest.TestCase):
    def test_toi_270_b_exofop_insolation_is_high(self):
        # Values from the composite table on 2026-10-15.
        r = ic.check(row(pl_name="TOI-270 b", st_lum=-1.71220, st_rad=0.38, st_teff=3506, pl_orbsmax=0.03197,
                         pl_insol=131.7935, pl_insol_reflink=EXOFOP, pl_eqt=600))
        self.assertEqual(r["lum_from"], "st_lum")
        self.assertAlmostEqual(r["insol_expected"], 18.98, delta=0.05)
        self.assertEqual(r["insol_flag"], "high")
        self.assertEqual(r["insol_ref"], "ExoFOP")
        self.assertEqual(r["eqt_flag"], "ok")

    def test_toi_4504_c_is_low(self):
        r = ic.check(row(st_lum=-0.20761, st_rad=0.93, st_teff=5315, pl_orbsmax=0.3593, pl_insol=0.2639))
        self.assertAlmostEqual(r["insol_expected"], 4.80, delta=0.02)
        self.assertEqual(r["insol_flag"], "low")

    def test_linear_luminosity_falls_back_to_radius_and_teff(self):
        r = ic.check(row(st_lum=2.13, st_rad=1.27, st_teff=6117, pl_orbsmax=2.1, pl_insol=30.5887))
        self.assertEqual(r["lum_from"], "R,Teff")
        self.assertAlmostEqual(r["insol_expected"], 0.461, delta=0.005)
        self.assertEqual(r["insol_flag"], "high")

    def test_kepler_fallback_for_missing_axis(self):
        r = ic.check(row(st_lum=0.0, st_rad=1.0, st_teff=5772, pl_orbper=365.25, st_mass=1.0, pl_insol=1.0,
                         pl_eqt=255))
        self.assertEqual(r["a_from"], "Kepler")
        self.assertAlmostEqual(r["a_used"], 1.0, places=6)
        self.assertEqual(r["insol_flag"], "ok")
        self.assertEqual(r["eqt_flag"], "ok")  # 255 K is albedo 0.3, inside the band

    def test_imaged_planets_skip_teq(self):
        r = ic.check(row(discoverymethod="Imaging", st_lum=0.0, pl_orbsmax=0.5, pl_eqt=1500))
        self.assertEqual(r["eqt_flag"], "")

    def test_untestable_row(self):
        self.assertIsNone(ic.check(row(pl_insol=3.0)))

    def test_by_reference(self):
        res = [ic.check(row(st_lum=0.0, pl_orbsmax=1.0, pl_insol=s, pl_insol_reflink=EXOFOP)) for s in (1.0, 5.0, 0.1)]
        refs = ic.by_reference(res, "insol_ref", "insol_flag", "insol_ratio")
        self.assertEqual(refs[0]["reference"], "ExoFOP")
        self.assertEqual((refs[0]["tested"], refs[0]["flagged"]), (3, 2))
        self.assertEqual(refs[0]["median_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
