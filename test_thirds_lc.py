"""Tests for thirds_lc on synthetic light curves. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0.

The synthetic star has box transits on the KOI-5600.01 DR24-based ephemeris (P = 17.1702343 d, T0 = BKJD
134.5069313, so group 2 holds the DR24 epoch 168.8474), Kepler long cadence from 131.5 to 700 BKJD and no
noise unless stated. With flat flux the out-of-transit line is exactly 1, so each epoch's depth is the
box depth times the fraction of core cadences inside the box, and its error is kepler_alias's 1e-6 floor.
These numbers are made up to exercise the code; they are not measurements.
"""
import random
import unittest

import thirds_lc as tl

CAD = 0.0204336
P, T0 = 17.1702343, 134.5069313
WIDE, NARROW = 13.04, 4.66


def synthetic(groups=(2,), dur_h=WIDE, depth=6e-4, sigma=0.0, seed=11, start=131.5, end=700.0, k=3):
    """(times, fluxes) with a box of depth and dur_h at every epoch n of (P, T0) with n mod k in groups."""
    rng = random.Random(seed)
    centres = [T0 + n * P for n in range(0, int((end - T0) / P) + 2) if n % k in groups]
    times, fluxes = [], []
    for i in range(int((end - start) / CAD) + 1):
        t = start + i * CAD
        f = 1.0 + (rng.gauss(0, sigma) if sigma else 0.0)
        if any(abs(t - tc) < dur_h / 48.0 for tc in centres):
            f -= depth
        times.append(t)
        fluxes.append(f)
    return times, fluxes


class GroupTest(unittest.TestCase):
    def test_long_period_box_only_in_group_2(self):
        times, fluxes = synthetic(groups=(2,))
        epochs, groups, v, _ = tl.run_groups(times, fluxes, P, T0, WIDE, 3, 2)
        self.assertEqual(v, "long_period_real")
        self.assertAlmostEqual(groups[2]["depth"], 6e-4, places=12)  # the core lies inside the 13.04 h box
        self.assertEqual(groups[0]["depth"], 0.0)
        self.assertEqual(groups[1]["depth"], 0.0)
        self.assertEqual(len(epochs), sum(g["epochs"] for g in groups))
        self.assertGreaterEqual(min(g["epochs"] for g in groups), 10)  # 33 epochs from 134.5 to ~700

    def test_every_event_is_short_period_real(self):
        times, fluxes = synthetic(groups=(0, 1, 2))
        _, groups, v, _ = tl.run_groups(times, fluxes, P, T0, WIDE, 3, 2)
        self.assertEqual(v, "short_period_real")
        for g in groups:
            self.assertAlmostEqual(g["depth"], 6e-4, places=12)

    def test_long_period_real_in_another_group_is_not_long(self):
        times, fluxes = synthetic(groups=(0,))
        _, _, v, _ = tl.run_groups(times, fluxes, P, T0, WIDE, 3, 2)
        self.assertEqual(v, "inconclusive")

    def test_half_period_shift_is_a_null(self):
        times, fluxes = synthetic(groups=(2,))
        _, groups, v, _ = tl.run_groups(times, fluxes, P, T0 + P / 2, WIDE, 3, 2)
        self.assertEqual(v, "inconclusive")
        for g in groups:
            self.assertEqual(g["depth"], 0.0)

    def test_narrow_transit_in_both_windows(self):
        times, fluxes = synthetic(groups=(2,), dur_h=NARROW)
        _, groups, v, _ = tl.run_groups(times, fluxes, P, T0, NARROW, 3, 2)
        self.assertEqual(v, "long_period_real")
        self.assertAlmostEqual(groups[2]["depth"], 6e-4, places=12)  # core +-1.63 h inside the +-2.33 h box
        # In the 13.04 h window 9-10 of 18-19 core cadences fall in the box: 0.47-0.56 of the depth.
        _, groups, v, _ = tl.run_groups(times, fluxes, P, T0, WIDE, 3, 2)
        self.assertEqual(v, "long_period_real")
        self.assertGreater(groups[2]["depth"], 2.5e-4)
        self.assertLess(groups[2]["depth"], 3.6e-4)

    def test_noisy_long_period(self):
        # 200 ppm white noise: one epoch's error is about 200 x sqrt(1/18.6 + 1/106) = 50 ppm, a group of 11
        # about 15 ppm, so a 300 ppm box gives S/N ~20 and the empty groups scatter about zero.
        times, fluxes = synthetic(groups=(2,), depth=3e-4, sigma=2e-4)
        _, groups, _, _ = tl.run_groups(times, fluxes, P, T0, WIDE, 3, 2)
        self.assertGreater(groups[2]["snr"], 8)
        self.assertLess(abs(groups[0]["snr"]), 4)
        self.assertLess(abs(groups[1]["snr"]), 4)

    def test_contrast(self):
        times, fluxes = synthetic(groups=(2,))
        _, groups, _, _ = tl.run_groups(times, fluxes, P, T0, WIDE, 3, 2)
        c = tl.contrast(groups, 2)
        self.assertEqual(c["contrast_ppm"], 600.0)
        self.assertEqual(c["others_mean_ppm"], 0.0)
        self.assertGreater(c["snr"], 100)
        times, fluxes = synthetic(groups=(0, 1, 2))
        _, groups, _, _ = tl.run_groups(times, fluxes, P, T0, WIDE, 3, 2)
        c = tl.contrast(groups, 2)
        self.assertEqual(c["contrast_ppm"], 0.0)
        self.assertEqual(c["others_mean_ppm"], 600.0)

    def test_contrast_by_hand_and_empty_group(self):
        groups = [{"group": 0, "epochs": 5, "depth": 1e-4, "err": 3e-5},
                  {"group": 1, "epochs": 5, "depth": -1e-4, "err": 4e-5},
                  {"group": 2, "epochs": 5, "depth": 2e-4, "err": 2e-5}]
        # 200 - 0 = 200 ppm; error sqrt(20^2 + (30^2 + 40^2) / 4) = sqrt(400 + 625) = 32.02 ppm; S/N 6.25
        self.assertEqual(tl.contrast(groups, 2), {"contrast_ppm": 200.0, "err_ppm": 32.0, "snr": 6.25,
                                                  "others_mean_ppm": 0.0})
        groups[0] = {"group": 0, "epochs": 0, "depth": None, "err": None}
        self.assertIsNone(tl.contrast(groups, 2))

    def test_halves_split_the_epochs(self):
        times, fluxes = synthetic(groups=(2,))
        epochs, _, _, (first, second) = tl.run_groups(times, fluxes, P, T0, WIDE, 3, 2)
        self.assertEqual(sum(g["epochs"] for g in first) + sum(g["epochs"] for g in second), len(epochs))
        self.assertAlmostEqual(first[2]["depth"], 6e-4, places=12)
        self.assertAlmostEqual(second[2]["depth"], 6e-4, places=12)


class RuleTest(unittest.TestCase):
    def test_outcome(self):
        L, S, I = "long_period_real", "short_period_real", "inconclusive"
        self.assertEqual(tl.outcome(L, I), "long")
        self.assertEqual(tl.outcome(I, L), "long")
        self.assertEqual(tl.outcome(L, L), "long")
        self.assertEqual(tl.outcome(S, I), "short")
        self.assertEqual(tl.outcome(S, S), "short")
        self.assertEqual(tl.outcome(I, S), "inconclusive")  # the narrow window alone cannot say "short"
        self.assertEqual(tl.outcome(L, S), "conflict")
        self.assertEqual(tl.outcome(S, L), "conflict")
        self.assertEqual(tl.outcome(I, I), "inconclusive")

    def test_parse_runs(self):
        self.assertEqual(tl.parse_runs("A=17.1702343@134.5069313/13.04, N=1.5@2/4.66,"),
                         [("A", 17.1702343, 134.5069313, 13.04), ("N", 1.5, 2.0, 4.66)])

    def test_group_dicts(self):
        g = tl.group_dicts([{"group": 0, "epochs": 0, "depth": None, "err": None, "snr": None},
                            {"group": 1, "epochs": 3, "depth": 1.5e-4, "err": 5e-5, "snr": 3.0}])
        self.assertIsNone(g[0]["depth_ppm"])
        self.assertEqual(g[1], {"group": 1, "epochs": 3, "depth_ppm": 150.0, "err_ppm": 50.0, "snr": 3.0})


if __name__ == "__main__":
    unittest.main()
