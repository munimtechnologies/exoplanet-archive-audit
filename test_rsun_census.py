import unittest

import rsun_census as rc


def ref(name):
    return f"<a refstr=X href=https://ui.adsabs.harvard.edu/abs/X/abstract target=ref>{name}</a>"


def row(paper="Hedges et al. 2019", **kw):
    base = {c: "" for c in rc.COLS}
    base.update({"pl_name": "X b", "hostname": "X", "tran_flag": "1", "cb_flag": "0", "default_flag": "1",
                 "pl_refname": ref(paper), "st_refname": ref(paper)})
    base.update({k: str(v) for k, v in kw.items()})
    return base


# Hedges et al. 2019 Table 1 as stored in ps on 2026-10-16 (no pl_orbsmax, so a comes from Kepler's law).
HEDGES = [
    dict(pl_name="K2-43 b", st_rad=0.542, st_mass=0.571, pl_orbper=3.471149, pl_ratdor=8.0, pl_rade=4.51, pl_ratror=0.04298),
    dict(pl_name="K2-43 c", st_rad=0.542, st_mass=0.571, pl_orbper=2.198884, pl_ratdor=5.9, pl_rade=2.42, pl_ratror=0.02319),
    dict(pl_name="K2-168 b", st_rad=0.83, st_mass=0.877, pl_orbper=15.8523, pl_ratdor=25.42, pl_rade=1.86, pl_ratror=0.01812),
    dict(pl_name="EPIC 205950854 c", st_rad=0.83, st_mass=0.877, pl_orbper=8.050722, pl_ratdor=16.18, pl_rade=1.31,
         pl_ratror=0.01258),
    dict(pl_name="K2-198 b", st_rad=0.757, st_mass=0.799, pl_orbper=17.0428683, pl_ratdor=25.86, pl_rade=4.189, pl_ratror=0.039),
    dict(pl_name="K2-198 c", st_rad=0.757, st_mass=0.799, pl_orbper=3.3596055, pl_ratdor=8.76, pl_rade=1.423, pl_ratror=0.013),
    dict(pl_name="K2-198 d", st_rad=0.757, st_mass=0.799, pl_orbper=7.4500177, pl_ratdor=14.9, pl_rade=2.438, pl_ratror=0.022),
]
# Mayo et al. 2018's K2-198 b row: a/R* and Rp/R* are true stellar-radius ratios.
MAYO = dict(pl_name="K2-198 b", default_flag=0, st_rad=0.778475, st_mass=0.835734, pl_orbper=17.0428683,
            pl_ratdor=42.001955, pl_rade=4.11850271, pl_ratror=0.048502)


class RsunTest(unittest.TestCase):
    def test_all_seven_hedges_planets_hit_both(self):
        for kw in HEDGES:
            r = rc.check(row(**kw))
            self.assertEqual((r["dor_hit"], r["ratror_hit"]), ("yes", "yes"), kw["pl_name"])

    def test_k2_198_b_values(self):
        r = rc.check(row(**HEDGES[4]))
        self.assertEqual(r["a_from"], "Kepler")
        self.assertAlmostEqual(r["a_used"], 0.120268, delta=0.000003)
        self.assertAlmostEqual(r["dor_sun"], 25.861, delta=0.01)
        self.assertAlmostEqual(r["dor_star"], 34.163, delta=0.01)
        self.assertAlmostEqual(r["k_sun"], 0.0384, delta=0.0001)

    def test_k2_168_b_ratror_within_tolerance(self):
        r = rc.check(row(**HEDGES[2]))
        self.assertAlmostEqual(r["ratror_q"], 1.0626, delta=0.001)
        self.assertAlmostEqual(r["dor_q"], 1.0, delta=0.001)

    def test_true_ratios_not_hit(self):
        r = rc.check(row("Mayo et al. 2018", **MAYO))
        self.assertAlmostEqual(r["dor_q"], 1.60, delta=0.01)
        self.assertAlmostEqual(r["ratror_q"], 1.2845, delta=0.001)
        self.assertEqual((r["dor_hit"], r["ratror_hit"], r["dor_ctrl"], r["ratror_ctrl"]), ("no", "no", 0, 0))

    def test_sun_like_star_untested(self):
        self.assertIsNone(rc.check(row(st_rad=1.05, st_mass=1.0, pl_orbper=10, pl_ratdor=20, pl_rade=2, pl_ratror=0.018)))

    def test_control_window_and_limit_flag(self):
        r = rc.check(row(st_rad=0.5, pl_orbsmax=0.1, pl_ratdor=18.2776))
        self.assertEqual(r["a_from"], "pl_orbsmax")
        self.assertAlmostEqual(r["dor_q"], 0.85, delta=0.0005)
        self.assertEqual((r["dor_hit"], r["dor_ctrl"], r["ratror_hit"]), ("no", 1, ""))
        self.assertIsNone(rc.check(row(st_rad=0.5, pl_orbsmax=0.1, pl_ratdor=21.5, pl_ratdorlim=1)))

    def test_summary_and_sources(self):
        results = [rc.check(row(**kw)) for kw in HEDGES] + [rc.check(row("Mayo et al. 2018", **MAYO))]
        s = rc.summarize(results)
        self.assertEqual((s["rows_testable"], s["dor_tested"], s["dor_hits"], s["ratror_hits"], s["rows_both"]),
                         (8, 8, 7, 7, 7))
        self.assertEqual(s["default_rows_hit"], 7)
        src = rc.by_source(results)
        self.assertEqual((src[0]["source"], src[0]["both_rows"], src[1]["hit_rows"]), ("Hedges et al. 2019", 7, 0))


if __name__ == "__main__":
    unittest.main()
