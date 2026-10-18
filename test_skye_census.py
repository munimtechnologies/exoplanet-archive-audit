"""Tests for skye_census. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0.

Every expected value below was worked by hand.
"""
import unittest

import skye_census as sc

SPANS = {1: (131.5, 165.0), 2: (169.5, 258.5)}


class TestEvents(unittest.TestCase):
    def test_two_quarters(self):
        # n = ceil((131.5 - 150) / 100) = 0 -> 150 in Q1; n = ceil(19.5 / 100) = 1 -> 250 in Q2
        self.assertEqual(sc.events(100.0, 150.0, {1, 2}, SPANS), [150.0, 250.0])

    def test_missing_quarter_and_unknown_quarter(self):
        self.assertEqual(sc.events(100.0, 150.0, {2, 0}, SPANS), [250.0])

    def test_t0_after_the_span(self):
        # n = ceil((131.5 - 950) / 100) = ceil(-8.185) = -8 -> 950 - 800 = 150
        self.assertEqual(sc.events(100.0, 950.0, {1}, SPANS), [150.0])

    def test_bad_period(self):
        self.assertEqual(sc.events(0.0, 150.0, {1}, SPANS), [])
        self.assertEqual(sc.events(-5.0, 150.0, {1}, SPANS), [])

    def test_real_quarters_k05227(self):
        # K05227.01: P 371.56492, T0 259.8491 lies in the Q2-Q3 gap (258.47-260.22), so three events remain
        evs = sc.events(371.56492, 259.8491, set(range(1, 18)))
        # 259.8491 + 3 * 371.56492 = 1374.54386 -> 1374.5439
        self.assertEqual(evs, [631.414, 1002.9789, 1374.5439])

    def test_real_quarters_k05269(self):
        # K05269.01: T0 260.1243 is 0.10 d before Q3's first cadence (260.22), so three events remain
        evs = sc.events(371.50631, 260.1243, set(range(1, 18)))
        self.assertEqual(evs, [631.6306, 1003.1369, 1374.6432])


class TestBins(unittest.TestCase):
    def test_bin_index(self):
        self.assertEqual(sc.bin_index(260.12), 129)
        self.assertEqual(sc.bin_index(131.0), 0)
        self.assertEqual(sc.bin_index(130.99), -1)

    def test_rate_bins(self):
        # centres 131.5 132.5 (in span 1), 133.5 134.5 (out), 135.5 (in span 2), 136.5 (out)
        self.assertEqual(sc.rate_bins({1: (131.5, 133.2), 2: (135.0, 136.0)}, 131.0), [0, 1, 4])

    def test_one_outlier(self):
        # 19 / 10 = 1.9, thr 1.9 + 3 * 1.378405 = 6.035 -> reject bin 9; then 9 / 9 = 1, thr 4 -> stable
        counts = {k: 1 for k in range(9)}
        counts[9] = 10
        flagged, r, thr = sc.skye_bins(counts, list(range(10)))
        self.assertEqual(flagged, {9})
        self.assertAlmostEqual(r, 1.0)
        self.assertAlmostEqual(thr, 4.0)

    def test_no_outlier(self):
        flagged, r, thr = sc.skye_bins({0: 2, 1: 2, 2: 2, 3: 2}, [0, 1, 2, 3])
        self.assertEqual(flagged, set())
        self.assertAlmostEqual(r, 2.0)
        self.assertAlmostEqual(thr, 2.0 + 3 * 2 ** 0.5)

    def test_flagged_outside_rate_bins(self):
        # rate 4 / 4 = 1, thr 4; bin 7 is not a rate bin but its 9 events exceed 4
        flagged, r, thr = sc.skye_bins({0: 1, 1: 1, 2: 1, 3: 1, 7: 9}, [0, 1, 2, 3])
        self.assertEqual(flagged, {7})
        self.assertAlmostEqual(thr, 4.0)

    def test_cascade(self):
        # 59 / 20 = 2.95, thr 8.1027 -> {19}; 29 / 19 = 1.526316, thr 5.232642 -> {17, 18, 19};
        # 17 / 17 = 1, thr 4 -> stable
        counts = {k: 1 for k in range(17)}
        counts.update({17: 6, 18: 6, 19: 30})
        flagged, r, thr = sc.skye_bins(counts, list(range(20)))
        self.assertEqual(flagged, {17, 18, 19})
        self.assertAlmostEqual(r, 1.0)
        self.assertAlmostEqual(thr, 4.0)


class TestStats(unittest.TestCase):
    def test_binom_tail(self):
        self.assertAlmostEqual(sc.binom_tail(1, 2, 0.5), 0.75)
        self.assertAlmostEqual(sc.binom_tail(0, 5, 0.3), 1.0)

    def test_census_pass(self):
        # p0 = max(5 / 500, 0.02) = 0.02; 10 / 50 = 0.2 >= 0.04; tail(10, 50, 0.02) ~ 1e-7
        ok, p = sc.census_test((10, 50), (5, 500))
        self.assertTrue(ok)
        self.assertLess(p, 1e-4)

    def test_census_fail_on_p(self):
        # 2 / 50 = 0.04 >= 0.04, but tail = 1 - 0.98^50 - 50 * 0.02 * 0.98^49 = 1 - 0.364170 - 0.371602
        ok, p = sc.census_test((2, 50), (5, 500))
        self.assertFalse(ok)
        self.assertAlmostEqual(p, 0.264228, places=4)

    def test_census_no_data(self):
        self.assertEqual(sc.census_test((0, 0), (5, 500)), (None, None))


class TestMast(unittest.TestCase):
    def test_parse(self):
        text = ("Kepler ID,Quarter,Skygroup_ID,Target Type\ninteger,integer,integer,ustring\n"
                "6359929,1,66,LC\n6359929,3,66,LC\n6359929,3,66,SC\n6034834,2,66,LC\n")
        self.assertEqual(sc.parse_mast(text), {6359929: (66, {1, 3}), 6034834: (66, {2})})

    def test_parse_junk(self):
        self.assertEqual(sc.parse_mast(""), {})
        self.assertEqual(sc.parse_mast("<html><body>no rows found</body></html>"), {})


class TestKoiRow(unittest.TestCase):
    SP = {1: (100.0, 500.0)}
    MAST = {1: (66, {1})}
    DR25 = {"K1": {"koi_pdisposition": "CANDIDATE", "koi_comment": "INDIV_TRANS_SKYE---X"}}

    def test_fails(self):
        # events 150 250 350 450 -> bins 19 119 219 319; Skye bins 119 and 219 -> good 2 < 3
        r = sc.koi_row("K1", 1, "CANDIDATE", 100.0, 150.0, self.MAST, {66: {119, 219}}, self.DR25, self.SP)
        self.assertEqual((r["n_events"], r["n_flagged"], r["good"], r["eligible"], r["would_fail"]),
                         (4, 2, 2, 1, 1))
        self.assertEqual(r["flagged_times"], "250.0000 350.0000")
        self.assertEqual((r["in_dr25"], r["dr25_pc"], r["dr25_skye"], r["never_dr25"]), (1, 1, 1, 0))

    def test_passes(self):
        r = sc.koi_row("K2", 1, "CANDIDATE", 100.0, 150.0, self.MAST, {66: {119}}, self.DR25, self.SP)
        self.assertEqual((r["good"], r["would_fail"]), (3, 0))
        self.assertEqual((r["in_dr25"], r["dr25_pc"], r["dr25_skye"], r["never_dr25"]), (0, 0, 0, 1))

    def test_not_eligible(self):
        # P 300: events 150 and 450 only -> 2 events, not eligible, never counted as a Skye failure
        r = sc.koi_row("K3", 1, "CANDIDATE", 300.0, 150.0, self.MAST, {66: set()}, self.DR25, self.SP)
        self.assertEqual((r["n_events"], r["eligible"], r["would_fail"]), (2, 0, 0))

    def test_no_skygroup(self):
        r = sc.koi_row("K4", 2, "FALSE POSITIVE", 100.0, 150.0, self.MAST, {}, self.DR25, self.SP)
        self.assertEqual((r["status"], r["never_dr25"]), ("no_skygroup", 0))

    def test_group_stats(self):
        rows = [sc.koi_row("K1", 1, "CANDIDATE", 100.0, 150.0, self.MAST, {66: {119, 219}}, self.DR25, self.SP),
                sc.koi_row("K2", 1, "CANDIDATE", 100.0, 150.0, self.MAST, {66: {119}}, self.DR25, self.SP),
                sc.koi_row("K3", 1, "CANDIDATE", 300.0, 150.0, self.MAST, {66: set()}, self.DR25, self.SP)]
        self.assertEqual(sc.group_stats(rows, "never_dr25"),
                         {"n": 2, "with_flagged": 1, "flagged_fraction": 0.5, "eligible": 1, "fails": 0,
                          "fail_fraction": 0.0})


if __name__ == "__main__":
    unittest.main()
