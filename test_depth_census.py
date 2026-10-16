import unittest

import depth_census as dc


def ref(name):
    return f"<a refstr=X href=https://ui.adsabs.harvard.edu/abs/X/abstract target=ref>{name}</a>"


def row(paper="Guenther et al. 2026", **kw):
    base = {c: "" for c in dc.PS_COLS}
    base.update({"pl_name": "X b", "hostname": "X", "tran_flag": "1", "cb_flag": "0", "default_flag": "1",
                 "pl_refname": ref(paper)})
    base.update({k: str(v) for k, v in kw.items()})
    return base


def comp(refs, **kw):
    base = {c: "" for c in dc.COMP_COLS}
    base.update({"pl_name": "X b", "hostname": "X", "tran_flag": "1", "cb_flag": "0"})
    base.update({f + "_reflink": ref(n) for f, n in refs.items()})
    base.update({k: str(v) for k, v in kw.items()})
    return base


# Guenther et al. 2026 rows as stored in ps on 2026-10-16 (default_flag = 1).
TOI_4427 = dict(pl_name="TOI-4427 b", pl_ratror=0.1073, pl_trandep=1.86143353, pl_rade=13.09208946, st_rad=0.89,
                pl_imppar=0.61884)
TOI_2049 = dict(pl_name="TOI-2049 b", pl_ratror=1.49, pl_trandep=0.2275, pl_rade=16.64533634, st_rad=3.2,
                pl_imppar=0.883)
TOI_4458 = dict(pl_name="TOI-4458 b", pl_ratror=0.05804, pl_trandep=0.3368, pl_rade=12.40834163, st_rad=1.96,
                pl_imppar=0.055)


class DepthTest(unittest.TestCase):
    def test_toi_4427_b_ratror_is_odd_one(self):
        r = dc.check(row(**TOI_4427))
        self.assertEqual(r["class"], "ratror")
        self.assertAlmostEqual(r["k_depth"], 0.13643, delta=0.00002)
        self.assertAlmostEqual(r["k_radii"], 0.13486, delta=0.00002)
        self.assertAlmostEqual(r["depth_over_k2"], 1.6168, delta=0.0002)

    def test_toi_2049_b_planet_larger_than_star(self):
        r = dc.check(row(**TOI_2049))
        self.assertEqual(r["class"], "ratror")
        self.assertAlmostEqual(r["k_depth"], 0.04770, delta=0.00002)
        self.assertAlmostEqual(r["k_radii"], 0.04769, delta=0.00002)

    def test_toi_4458_b_consistent(self):
        r = dc.check(row(**TOI_4458))
        self.assertEqual(r["class"], "ok")
        self.assertAlmostEqual(r["k_depth"], 0.05803, delta=0.00002)
        self.assertAlmostEqual(r["k_radii"], 0.05804, delta=0.00002)

    def test_toi_2048_b_composite_and_ps(self):
        r = dc.check(comp({"pl_ratror": "Newton et al. 2022", "pl_trandep": "ExoFOP", "pl_rade": "Newton et al. 2022",
                           "st_rad": "Newton et al. 2022"}, pl_name="TOI-2048 b", pl_ratror=0.0239, pl_trandep=0.114,
                          pl_rade=2.61, st_rad=0.79, pl_imppar=0.33), composite=True)
        self.assertEqual((r["class"], r["table"], r["ref"], r["trandep_ref"], r["one_source"]),
                         ("ratror", "pscomppars", "Newton et al. 2022", "ExoFOP", "no"))
        self.assertAlmostEqual(r["k_depth"], 0.03376, delta=0.00002)
        self.assertAlmostEqual(r["k_radii"], 0.03029, delta=0.00002)
        # The ps row from Newton et al. 2022 has no depth, so only Rp/R* is compared.
        r = dc.check(row("Newton et al. 2022", pl_name="TOI-2048 b", pl_ratror=0.0239, pl_rade=2.61, st_rad=0.79))
        self.assertEqual((r["class"], r["k_depth"]), ("two-way", ""))

    def test_kepler_132_b_composite_ok(self):
        r = dc.check(comp({"pl_ratror": "Q1-Q8 KOI Table", "pl_trandep": "Q1-Q17 DR25 KOI Table",
                           "pl_rade": "Rowe et al. 2014", "st_rad": "Rowe et al. 2014"}, pl_name="Kepler-132 b",
                          pl_ratror=0.01087, pl_trandep=0.01019, pl_rade=1.21, st_rad=1.178, pl_imppar=0.26),
                     composite=True)
        self.assertEqual(r["class"], "ok")

    def test_other_classes(self):
        self.assertEqual(dc.check(row(pl_ratror=0.1, pl_trandep=1.1, pl_rade=14.17988, st_rad=1))["class"], "radius")
        self.assertEqual(dc.check(row(pl_ratror=0.1, pl_trandep=0.1, pl_rade=10.9076, st_rad=1))["class"], "trandep")
        self.assertEqual(dc.check(row(pl_ratror=0.1, pl_trandep=1.69, pl_rade=7.63532, st_rad=1))["class"], "mixed")
        self.assertEqual(dc.check(row(pl_ratror=0.1, pl_trandep=0.5, pl_rade=10.9076, st_rad=1, pl_imppar=0.95))["class"],
                         "grazing")
        self.assertEqual(dc.check(row(pl_ratror=0.1, pl_trandep=1.0))["class"], "ok")
        self.assertEqual(dc.check(row(pl_ratror=0.1, pl_trandep=2.0))["class"], "two-way")

    def test_skips(self):
        # WD 1856+534 b (Vanderburg et al. 2020): every estimate is large, so the row is skipped.
        self.assertIsNone(dc.check(row(pl_ratror=7.28, pl_trandep=56.65, pl_rade=10.4, st_rad=0.0131)))
        self.assertIsNone(dc.check(row(pl_ratror=0.1, pl_ratrorlim=1, pl_trandep=1.0)))
        self.assertIsNone(dc.check(row(pl_ratror=0.1)))
        self.assertIsNone(dc.check(row(pl_ratror=0.1, pl_trandep=1.0, cb_flag=1)))

    def test_summary_and_sources(self):
        results = [dc.check(row(**kw)) for kw in (TOI_4427, TOI_2049, TOI_4458)]
        s = dc.summarize(results)
        self.assertEqual((s["rows_checked"], s["ratror"], s["ok"], s["default_ratror"]), (3, 2, 1, 2))
        src = dc.by_source(results)
        self.assertEqual((len(src), src[0]["source"], src[0]["rows"], src[0]["ratror"]),
                         (1, "Guenther et al. 2026", 3, 2))


if __name__ == "__main__":
    unittest.main()
