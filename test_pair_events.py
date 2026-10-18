"""Tests for pair_events. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0.

Synthetic light curves are noise-free, so every expected value is exact and was worked by hand: cadences
every 0.01 d at 0.005, 0.015, ..., 9.995; one box event centred on 5.0 covering |t - 5| < 0.08 d; a 4.8 h
duration (0.2 d), so the in-core window |d| < 0.07 holds 14 cadences and the baseline 0.2 <= |d| <= 0.6
holds 40 on each side. The catalogue checks reproduce the offsets in
findings/2026-10-18-cross-star-ephemeris-pairs.md.
"""
import math
import unittest

import pair_events as pe

TIMES = [0.005 + 0.01 * i for i in range(1000)]


def boxed(base, step, slope=0.0):
    """base + slope (t - 5), plus step inside the event."""
    return [base + slope * (t - 5.0) + (step if abs(t - 5.0) < 0.08 else 0.0) for t in TIMES]


def quarter():
    q = {"time": list(TIMES), "pdc": boxed(2000.0, -2.0), "sap": boxed(10000.0, -12.0),
         "bkg": boxed(50.0, 6.0), "c1": boxed(500.0, 0.01), "c2": boxed(300.0, 0.0),
         "quality": [0.0] * len(TIMES)}
    q["quality"][530] = 8.0        # t = 5.305, outside the event: dropped from the fits, counted as a flag
    q["pdc"][469] = float("nan")   # t = 4.695: dropped from pdc only
    return q


class BoxTest(unittest.TestCase):
    def test_flat_box(self):
        resid, err, a, n_in, n_out = pe.box_fit(TIMES, boxed(1.0, -0.001), 5.0, 4.8)
        self.assertAlmostEqual(resid, -0.001, places=12)
        self.assertAlmostEqual(a, 1.0, places=12)
        self.assertEqual((n_in, n_out), (14, 80))
        self.assertEqual(err, pe.ERR_FLOOR)
        d, e = pe.deficit_ppm((resid, err, a, n_in, n_out))
        self.assertAlmostEqual(d, 1000.0, places=6)

    def test_sloped_baseline(self):
        fit = pe.box_fit(TIMES, boxed(1.0, -0.002, slope=0.01), 5.0, 4.8)
        self.assertAlmostEqual(pe.deficit_ppm(fit)[0], 2000.0, places=5)

    def test_too_few_points(self):
        self.assertIsNone(pe.box_fit([4.99, 5.0, 5.01], [1.0, 1.0, 1.0], 5.0, 4.8))
        self.assertIsNone(pe.deficit_ppm(None))


class HelperTest(unittest.TestCase):
    def test_mask(self):
        m = [(10.0, 2.0, 24.0)]
        self.assertTrue(pe.in_mask(11.5, m))
        self.assertTrue(pe.in_mask(2.0, m))
        self.assertFalse(pe.in_mask(13.5, m))
        self.assertFalse(pe.in_mask(5.0, []))

    def test_events_in(self):
        self.assertEqual(pe.events_in(10.0, 3.0, 0.0, 25.0), [3.0, 13.0, 23.0])

    def test_null_times(self):
        self.assertEqual(pe.null_times([0.0, 100.0], [50.0], n=10, avoid=6.0),
                         [5.0, 15.0, 25.0, 35.0, 65.0, 75.0, 85.0, 95.0])
        self.assertEqual(pe.null_times([], [1.0]), [])

    def test_percentile_and_sigma(self):
        self.assertEqual(pe.percentile_rank(3, [1, 2, 3, 4]), 0.5)
        self.assertIsNone(pe.percentile_rank(3, []))
        self.assertAlmostEqual(pe.robust_sigma([1, 2, 3, 4, 100]), 1.4826)

    def test_flags(self):
        self.assertEqual(pe.flag_summary([0.0, 0.5, 1.0, 1.5, 2.5], [0, 4, 0, 128, 1024], 1.0), (2, 132))


class MeasureTest(unittest.TestCase):
    def test_every_column(self):
        series, flag_t, flag_q = pe.build_series([quarter()], [])
        self.assertEqual(len(series["pdc"][0]), 998)
        self.assertEqual(len(series["sap"][0]), 999)
        row = pe.measure(series, 5.0, 4.8)
        self.assertEqual(row["pdc_ppm"], 1000.0)
        self.assertEqual(row["sap_ppm"], 1200.0)
        self.assertEqual(row["bkg_ppm"], 600.0)
        self.assertEqual(row["c1_mpix"], 10.0)
        self.assertEqual(row["c2_mpix"], 0.0)
        self.assertEqual(pe.flag_summary(flag_t, flag_q, 5.0), (1, 8))

    def test_mask_removes_points(self):
        series, _, _ = pe.build_series([quarter()], [(100.0, 5.0, 24.0)])
        self.assertTrue(all(abs(t - 5.0) >= 1.0 for t in series["pdc"][0]))
        self.assertEqual(pe.measure(series, 5.0, 4.8)["pdc_ppm"], "")

    def test_star_rows_against_a_flat_null(self):
        saved = pe.STARS, pe.HYPS
        try:
            pe.STARS = {"X": (1, 4.8, [])}
            pe.HYPS = {"X": (100.0, 5.0)}
            series, flag_t, flag_q = pe.build_series([quarter()], [])
            rows, summary = pe.star_rows("X", series, flag_t, flag_q)
        finally:
            pe.STARS, pe.HYPS = saved
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r["own"], r["time"], r["pdc_ppm"], r["pct"], r["dip"], r["z"]), (1, 5.0, 1000.0, 1.0, 1, ""))
        self.assertGreaterEqual(summary["null_n"], 100)
        self.assertEqual(summary["null_median_ppm"], 0.0)

    def test_pair_table(self):
        rows = [{"star": "K05660.01", "own": 1, "time": 369.5, "dip": 1, "pdc_ppm": 400.0},
                {"star": "K08259.01", "own": 1, "time": 369.7, "dip": 0, "pdc_ppm": 100.0},
                {"star": "K08259.01", "own": 0, "time": 370.0, "dip": 1, "pdc_ppm": 900.0}]
        out = pe.pair_table(rows)
        self.assertEqual(len(out), 1)
        self.assertEqual((out[0]["pair"], out[0]["dip_a"], out[0]["time_b"], out[0]["dip_b"]), ("A", 1, 369.7, 0))


class CatalogueTest(unittest.TestCase):
    """The configuration reproduces the published offsets (Q1-Q17 span 131.5-1591.0 BKJD)."""

    def test_pairs_share_every_event(self):
        expect = {"A": (4, 0.361), "B": (4, 0.119), "C": (3, 0.329)}
        for pair, a, b in pe.PAIRS:
            ea = pe.events_in(*pe.HYPS[a], 131.5, 1591.0)
            eb = pe.events_in(*pe.HYPS[b], 131.5, 1591.0)
            self.assertEqual(len(ea), expect[pair][0])
            self.assertEqual(len(eb), expect[pair][0])
            self.assertAlmostEqual(max(abs(x - y) for x, y in zip(ea, eb)), expect[pair][1], delta=0.0006)

    def test_eb_tce_every_second_event_on_pair_c(self):
        eb = pe.events_in(*pe.HYPS["EB-TCE3"], 131.5, 1591.0)[::2]
        c = pe.events_in(*pe.HYPS["K07040.01"], 131.5, 1591.0)
        self.assertEqual(len(c), 3)
        offsets = [abs(x - y) for x, y in zip(eb, c)]
        for got, want in zip(offsets, (0.4979, 0.2535, 0.0091)):
            self.assertAlmostEqual(got, want, delta=0.0006)

    def test_every_star_has_its_ephemeris(self):
        self.assertEqual(set(pe.STARS), set(pe.HYPS))
        self.assertTrue(all(math.isfinite(d) and d > 0 for _, d, _ in pe.STARS.values()))


if __name__ == "__main__":
    unittest.main()
