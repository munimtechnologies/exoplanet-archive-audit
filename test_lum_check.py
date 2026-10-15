"""Offline tests for lum_check. MV2 of Munim, Inc. Made with AI. Apache-2.0.

Values are the Archive's own rows, checked by hand on 2026-10-15."""
import unittest

import lum_check as lc

FISCHER = '<a refstr=FISCHER_ET_AL__2012 href=https://ui.adsabs.harvard.edu/abs/2012ApJ...745...21F/abstract target=ref>Fischer et al. 2012</a>'
PEPE = '<a href=x>Pepe et al. 2011</a>'


def row(**kw):
    r = {"pl_name": "P b", "hostname": "P", "default_flag": "0", "st_refname": FISCHER, "st_lum": "",
         "st_rad": "", "st_teff": ""}
    r.update(kw)
    return r


class Luminosity(unittest.TestCase):
    def test_logl_rt(self):
        self.assertAlmostEqual(lc.logl_rt(1.0, 5772.0), 0.0)
        self.assertAlmostEqual(lc.logl_rt(0.68, 4640.0), -0.7142, places=3)   # HIP 57274
        self.assertIsNone(lc.logl_rt(None, 5000.0))

    def test_linear_in_log(self):
        # HIP 57274 (Fischer et al. 2012): paper prints L = 0.19 L_sun; Archive stores st_lum = 0.19
        self.assertEqual(lc.lum_class(0.19, lc.logl_rt(0.68, 4640.0)), "linear_in_log")
        # TOI-5542 (Grieves et al. 2022): L = 1.057 L_sun stored as log
        self.assertEqual(lc.lum_class(1.057, lc.logl_rt(1.058, 5700.0)), "linear_in_log")
        # HD 187085 (Jones et al. 2006, printed under a log label): 2.13
        self.assertEqual(lc.lum_class(2.13, lc.logl_rt(1.27, 6117.0)), "linear_in_log")
        # TOI-3568 (Martioli et al. 2024, labelled log): 0.33, log10 lands 0.065 dex from R and Teff
        self.assertEqual(lc.lum_class(0.33, lc.logl_rt(0.719, 4969.0)), "linear_in_log")

    def test_ok_and_mismatch(self):
        self.assertEqual(lc.lum_class(-0.41454, lc.logl_rt(0.80, 5166.0)), "ok")
        # Lupus-TR-3 (TICv8): -1.464 where R and Teff give -0.42; off, but not a linear value
        self.assertEqual(lc.lum_class(-1.46393, lc.logl_rt(0.82, 5000.0)), "mismatch")
        self.assertIsNone(lc.lum_class(None, 0.0))

    def test_lum_rows_and_refs(self):
        rows = [row(pl_name=p, st_lum="0.19", st_rad="0.68", st_teff="4640") for p in ("HIP 57274 b", "HIP 57274 c")]
        rows.append(row(pl_name="HD 192310 b", st_refname=PEPE, st_lum="-0.41454", st_rad="0.80", st_teff="5166"))
        flagged = lc.lum_rows(rows, "st_refname", "ps")
        self.assertEqual([f["pl_name"] for f in flagged], ["HIP 57274 b", "HIP 57274 c"])
        self.assertEqual(flagged[0]["reference"], "Fischer et al. 2012")
        refs = lc.lum_refs(rows, "st_refname")
        self.assertEqual(len(refs), 1)
        self.assertEqual((refs[0]["rows"], refs[0]["linear_in_log"], refs[0]["mismatch"]), (2, 2, 0))


class Calculated(unittest.TestCase):
    def pc(self, **kw):
        r = {"pl_name": "P b", "st_lum": "", "st_lum_reflink": FISCHER, "st_rad": "", "st_teff": "",
             "pl_orbsmax": "", "pl_insol": "", "pl_insol_reflink": "Calculated Value"}
        r.update(kw)
        return r

    def test_insol_follows_formula_but_lum_is_linear(self):
        # HD 187085 b: pl_insol 30.5887 = 10**2.13 / 2.1**2; with L = 2.13 L_sun it would be 0.483
        out = lc.calc_rows([self.pc(pl_name="HD 187085 b", st_lum="2.13", st_rad="1.27", st_teff="6117",
                                    pl_orbsmax="2.1", pl_insol="30.5887")], "pl_insol")
        self.assertEqual(out[0]["status"], "ok")
        self.assertEqual(out[0]["st_lum_class"], "linear_in_log")
        self.assertAlmostEqual(out[0]["insol_if_linear"], 0.483, places=3)

    def test_insol_differs_and_missing(self):
        out = lc.calc_rows([self.pc(st_lum="0.0", pl_orbsmax="1", pl_insol="5.0"),
                            self.pc(pl_name="Q b", st_lum="", pl_orbsmax="1", pl_insol="5.0"),
                            self.pc(pl_name="R b", st_lum="0.0", pl_orbsmax="1", pl_insol="1.0",
                                    pl_insol_reflink='<a href=x>Some et al. 2020</a>')], "pl_insol")
        self.assertEqual([o["status"] for o in out], ["differs", "inputs_missing"])

    def test_other_formulas(self):
        eqt = lc.predict("pl_eqt", {"st_teff": "5772", "st_rad": "1", "pl_orbsmax": "1"})
        self.assertAlmostEqual(eqt, 278.3, places=0)
        self.assertAlmostEqual(lc.predict("pl_dens", {"pl_bmasse": "1", "pl_rade": "1"}), 5.514)
        self.assertAlmostEqual(lc.predict("pl_angsep", {"pl_orbsmax": "1", "sy_dist": "10"}), 100.0)
        self.assertIsNone(lc.predict("pl_angsep", {"pl_orbsmax": "1", "sy_dist": ""}))


if __name__ == "__main__":
    unittest.main()
