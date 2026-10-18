"""Tests for event_check on synthetic light curves. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0.

The synthetic star has two 6,000 ppm, 13 h box transits at 335.817 and 1,123.255 BKJD (787.438 d apart),
300 ppm white noise, Kepler long cadence from 300 to 1,200 BKJD and a data gap from 715 to 735. These
numbers are made up to mimic KOI-1356.01; they are not measurements.
"""
import random
import unittest

import event_check as ec

CAD = 0.0204336
T1, T2 = 335.817, 1123.255


def synthetic(transits=(T1, T2), depth=0.006, dur_h=13.0, start=300.0, end=1200.0, gap=(715.0, 735.0),
              sigma=3e-4, seed=7):
    rng = random.Random(seed)
    times, fluxes = [], []
    for i in range(int((end - start) / CAD) + 1):
        t = start + i * CAD
        if gap[0] <= t < gap[1]:
            continue
        f = 1.0 + rng.gauss(0, sigma)
        if any(abs(t - tc) < dur_h / 48.0 for tc in transits):
            f -= depth
        times.append(t)
        fluxes.append(f)
    return times, fluxes


class EventTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.times, cls.fluxes = synthetic()
        cls.ref = ec.one_event(cls.times, cls.fluxes, T1, 13.5)

    def test_one_event_measures_the_box_depth(self):
        d, e, n_in, n_out = self.ref
        self.assertAlmostEqual(d, 0.006, delta=0.0005)
        self.assertGreater(d / e, 30)
        self.assertGreater(n_in, 10)
        self.assertGreater(n_out, 50)

    def test_event_in_a_gap_has_no_data(self):
        self.assertIsNone(ec.one_event(self.times, self.fluxes, 725.0, 13.5))
        self.assertEqual(ec.core_points(self.times, 725.0, 13.5), 0)
        self.assertEqual(ec.status(None, self.ref), "no_data")

    def test_flat_epoch_is_absent_and_transit_is_deep(self):
        self.assertEqual(ec.status(ec.one_event(self.times, self.fluxes, 1000.0, 13.5), self.ref), "absent")
        self.assertEqual(ec.status(ec.one_event(self.times, self.fluxes, T2, 13.5), self.ref), "deep")

    def test_best_centre_finds_the_transit(self):
        c, d, e = ec.best_centre(self.times, self.fluxes, T1 - 0.2, 13.5)
        self.assertLess(abs(c - T1), 0.1)
        self.assertGreater(d / e, 30)

    def test_hypotheses(self):
        rows, v = ec.check_hypothesis(self.times, self.fluxes, "tce", 393.719, 335.817, 13.5, self.ref)
        self.assertEqual([r["status"] for r in rows], ["deep", "no_data", "deep"])
        self.assertEqual(v, "supported")
        rows, v = ec.check_hypothesis(self.times, self.fluxes, "q16", 384.02570682, 335.816169, 13.5, self.ref)
        self.assertEqual([r["status"] for r in rows], ["deep", "no_data", "absent"])
        self.assertEqual(v, "excluded")
        rows, v = ec.check_hypothesis(self.times, self.fluxes, "n3", (T2 - T1) / 3, T1, 13.5, self.ref)
        self.assertEqual([r["status"] for r in rows], ["deep", "absent", "absent", "deep"])
        self.assertEqual(v, "excluded")

    def test_refine_fills_best_centre_only_where_there_is_data(self):
        rows, _ = ec.check_hypothesis(self.times, self.fluxes, "tce", 393.719, 335.817, 13.5, self.ref, refine=True)
        self.assertNotEqual(rows[0]["best_centre"], "")
        self.assertEqual(rows[1]["best_centre"], "")

    def test_dip_search_ranks_the_two_transits_first(self):
        dips, scale = ec.dip_search(self.times, self.fluxes, 13.5, step=0.1)
        top = sorted(d["time"] for d in dips[:2])
        self.assertLess(abs(top[0] - T1), 0.3)
        self.assertLess(abs(top[1] - T2), 0.3)
        self.assertGreater(dips[0]["snr_robust"], 10)
        self.assertLess(dips[2]["snr"], dips[1]["snr"] / 3)
        self.assertGreater(scale, 0)

    def test_gaps(self):
        g = ec.gaps(self.times)
        self.assertEqual(len(g), 1)
        self.assertLess(g[0][0], 715.0)
        self.assertGreater(g[0][1], 735.0 - CAD)


class RuleTest(unittest.TestCase):
    def test_status_thresholds(self):
        ref = (0.006, 1e-4)
        self.assertEqual(ec.status((0.0035, 1e-4), ref), "deep")      # >= 0.5 ref, S/N 35
        self.assertEqual(ec.status((0.0035, 6e-4), ref), "unclear")   # S/N 5.8 < 7, not < 0.3 ref
        self.assertEqual(ec.status((0.001, 1e-4), ref), "absent")     # < 0.3 ref, 35 sigma below
        self.assertEqual(ec.status((0.001, 1e-3), ref), "unclear")    # 5.0e-3 / 1.005e-3 = 4.97 sigma < 5
        self.assertEqual(ec.status((0.001, 1e-4), None), "unclear")
        self.assertEqual(ec.status(None, ref), "no_data")

    def test_judge(self):
        self.assertEqual(ec.judge(["deep", "no_data", "deep"]), "supported")
        self.assertEqual(ec.judge(["deep", "absent", "deep"]), "excluded")
        self.assertEqual(ec.judge(["deep", "no_data"]), "untested")
        self.assertEqual(ec.judge(["deep", "unclear"]), "unclear")

    def test_epochs_in(self):
        self.assertEqual(ec.epochs_in(393.719, 335.817, 300.0, 1200.0), [0, 1, 2])
        self.assertEqual(ec.epochs_in(384.02570682, 335.816169, 131.5, 1591.0), [0, 1, 2, 3])

    def test_parse_hypotheses(self):
        self.assertEqual(ec.parse_hypotheses("a=1.5@2, b=3@4.5,"), [("a", 1.5, 2.0), ("b", 3.0, 4.5)])


if __name__ == "__main__":
    unittest.main()
