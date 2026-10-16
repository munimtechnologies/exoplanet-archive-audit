import unittest

import kepler_coverage as kc

# Every other 90 d "quarter" observed, a 186 d cycle, like KIC 8745553's even quarters.
STROBE = [(0.0, 90.0), (186.0, 276.0), (372.0, 462.0), (558.0, 648.0)]


def link(text):
    return f"<a refstr=X href=https://ui.adsabs.harvard.edu/abs/X/abstract target=ref>{text}</a>"


class SegmentTest(unittest.TestCase):
    def test_overlap(self):
        cov = kc.Coverage([(0.0, 10.0), (20.0, 30.0)])
        self.assertAlmostEqual(cov.overlap(5.0, 25.0), 10.0)
        self.assertAlmostEqual(cov.overlap(10.0, 20.0), 0.0)
        self.assertAlmostEqual(cov.overlap(-5.0, 2.0), 2.0)

    def test_merge(self):
        self.assertEqual(kc.merge([(5.0, 8.0), (0.0, 6.0), (10.0, 12.0)]), [(0.0, 8.0), (10.0, 12.0)])

    def test_segments_from_times(self):
        segs = kc.segments_from_times([0.0, 0.02, 0.04, 1.0, 1.02])
        self.assertEqual(len(segs), 2)
        for got, want in zip(segs, [(-0.0102, 0.0502), (0.9898, 1.0302)]):
            self.assertAlmostEqual(got[0], want[0])
            self.assertAlmostEqual(got[1], want[1])
        self.assertEqual(kc.segments_from_times([]), [])

    def test_half_window_counts_as_covered(self):
        cov = kc.Coverage([(0.0, 10.0)])
        self.assertEqual(kc.covered_epochs(cov, 100.0, 10.0, 12.0), [0])  # [9.75, 10.25], half inside
        self.assertEqual(kc.covered_epochs(cov, 100.0, 10.0, 12.0, min_frac=0.6), [])


class AliasFlagsTest(unittest.TestCase):
    def test_62_day_period_on_a_186_day_cycle_cannot_exclude_3p(self):
        f = kc.alias_flags(kc.Coverage(STROBE), 62.0, 45.0, 6.0)
        self.assertEqual(f["observed"], [0, 3, 6, 9])  # 45, 231, 417, 603; the rest fall in gaps
        self.assertEqual(f["long"], {2: False, 3: True, 4: False, 5: False})
        self.assertEqual(f["short"][2], 8)  # 14, 76, 200, 262, 386, 448, 572, 634
        self.assertEqual(f["flags"], ["3P"])

    def test_186_day_period_on_a_186_day_cycle_cannot_exclude_p2_p3_p4(self):
        f = kc.alias_flags(kc.Coverage(STROBE), 186.0, 45.0, 6.0)
        self.assertEqual(f["observed"], [0, 1, 2, 3])
        self.assertEqual(f["short"], {2: 0, 3: 0, 4: 0, 5: 8})  # P/5: 7.8, 82.2, 193.8, ... 640.2
        self.assertEqual(f["flags"], ["P/2", "P/3", "P/4"])

    def test_full_coverage_has_no_flags(self):
        f = kc.alias_flags(kc.Coverage([(0.0, 1000.0)]), 10.0, 5.0, 3.0)
        self.assertEqual(len(f["observed"]), 100)
        self.assertEqual(f["flags"], [])

    def test_one_epoch_and_no_coverage(self):
        f = kc.alias_flags(kc.Coverage([(0.0, 10.0)]), 100.0, 5.0, 6.0)
        self.assertEqual(f["observed"], [0])
        self.assertEqual(f["flags"], ["P/2", "P/3", "P/4", "P/5", "one_epoch"])
        self.assertEqual(kc.alias_flags(kc.Coverage([(0.0, 10.0)]), 100.0, 50.0, 6.0)["flags"], ["no_coverage"])
        self.assertEqual(kc.alias_flags(kc.Coverage([]), 100.0, 5.0, 6.0)["flags"], ["no_coverage"])


class QuarterTest(unittest.TestCase):
    def test_quarters_from_string(self):
        self.assertEqual(kc.quarters_from_string("01010101010101010"), [2, 4, 6, 8, 10, 12, 14, 16])
        self.assertEqual(kc.quarters_from_string(""), [])

    def test_best_quarters_keeps_the_fullest_string(self):
        rows = [{"kepid": "1", "st_quarters": ""}, {"kepid": "1", "st_quarters": "0101"},
                {"kepid": "1", "st_quarters": "0111"}, {"kepid": "2", "st_quarters": ""}]
        self.assertEqual(kc.best_quarters(rows), {"1": "0111"})

    def test_epochs_and_short_text(self):
        self.assertEqual(kc.epochs_text([0, 3, 6]), "0 3 6")
        self.assertEqual(kc.epochs_text(list(range(20))), "0..19 (20)")
        self.assertEqual(kc.short_text({3: 0, 2: 8}), "2:8;3:0")


class CensusRowsTest(unittest.TestCase):
    QSEGS = {1: [(0.0, 90.0)], 2: [(93.0, 183.0)], 3: [(186.0, 276.0)], 4: [(279.0, 369.0)],
             5: [(372.0, 462.0)], 6: [(465.0, 555.0)], 7: [(558.0, 648.0)]}
    KOI = {"kepid": "1", "kepoi_name": "K0X.01", "kepler_name": "X b", "koi_disposition": "CONFIRMED",
           "koi_period": "62.0", "koi_time0bk": "45.0", "koi_duration": "6.0", "koi_num_transits": "4"}
    COMP = {"X b": {"pl_name": "X b", "pl_orbper": "186.0", "pl_tranmid": "2454878.0", "pl_trandur": "6.0",
                    "pl_orbper_reflink": link("Morton et al. 2016")}}

    def test_koi_and_archive_ephemerides(self):
        fp = dict(self.KOI, kepoi_name="K0Y.01", kepler_name="", koi_disposition="FALSE POSITIVE")
        nostar = dict(self.KOI, kepid="2", kepoi_name="K0Z.01", kepler_name="")
        rows, missing = kc.census_rows([self.KOI, fp, nostar], self.COMP, {"1": "1010101"}, self.QSEGS)
        self.assertEqual(missing, 1)
        self.assertEqual([(r["kepoi_name"], r["source"]) for r in rows], [("K0X.01", "koi"), ("K0X.01", "archive")])
        koi, arch = rows
        self.assertEqual((koi["flags"], koi["observed"], koi["n_quarters"]), ("3P", "0 3 6 9", 4))
        self.assertEqual((arch["period"], arch["t0_bkjd"], arch["period_ref"]), (186.0, 45.0, "Morton et al. 2016"))
        self.assertEqual((arch["flags"], arch["short_covered"]), ("P/2;P/3;P/4", "2:0;3:0;4:0;5:8"))

    def test_same_composite_period_adds_no_archive_row(self):
        comp = {"X b": dict(self.COMP["X b"], pl_orbper="62.05")}  # within 0.2 % of 62.0
        rows, _ = kc.census_rows([self.KOI], comp, {"1": "1010101"}, self.QSEGS)
        self.assertEqual([r["source"] for r in rows], ["koi"])


if __name__ == "__main__":
    unittest.main()
