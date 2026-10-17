import math
import unittest

import kepler_pixels as kp

TIMES = [i * 0.02 for i in range(1000)]  # 0 to 19.98 d, the in/out edges below sit between samples
DUR_H = 2.76  # 0.115 d: in-transit |dt| < 0.0575 (5 cadences), out 0.115 <= |dt| < 0.365 (13 a side)


def gauss_img(nrow, ncol, r0, c0, amp, sigma=1.2):
    return [amp * math.exp(-((r - r0) ** 2 + (c - c0) ** 2) / (2 * sigma ** 2))
            for r in range(nrow) for c in range(ncol)]


def synthetic_quarter():
    # 9x9 pixels. Target at (4, 4), 1000 units; neighbour at (3.5, 3.5), 10 units. The target dips 1 %
    # at P = 5 d, T0 = 2.5; the neighbour is fully eclipsed half a period later (5, 10, 15 d).
    # jac: east = -4 * dcol, north = 4 * drow, so the neighbour is 2" east and 2" south.
    tgt, nb = gauss_img(9, 9, 4, 4, 1.0), gauss_img(9, 9, 3.5, 3.5, 1.0)
    frames = []
    for t in TIMES:
        a_t = 990.0 if abs((t % 5) - 2.5) < 0.05 else 1000.0
        a_n = 0.0 if abs(((t + 2.5) % 5) - 2.5) < 0.05 else 10.0
        frames.append([a_t * x + a_n * y for x, y in zip(tgt, nb)])
    return {"quarter": 1, "times": TIMES, "frames": frames, "nrow": 9, "ncol": 9, "valid": [True] * 81,
            "jac": [[-4.0, 0.0], [0.0, 4.0]], "scale": 4.0}


class Windows(unittest.TestCase):
    def test_two_full_events(self):
        ev = kp.event_windows(TIMES[:500], 5.0, 2.5, DUR_H)
        self.assertEqual([n for n, _, _ in ev], [0, 1])
        self.assertEqual([len(i) for _, i, _ in ev], [5, 5])
        self.assertEqual([len(o) for _, _, o in ev], [26, 26])

    def test_mask_and_partial(self):
        ev = kp.event_windows(TIMES[:500], 5.0, 2.5, DUR_H, mask=[t > 5 for t in TIMES[:500]])
        self.assertEqual([n for n, _, _ in ev], [0])
        self.assertEqual(kp.event_windows(TIMES[:128], 5.0, 2.5, DUR_H), [])  # ends at 2.54: no after side

    def test_mask_others(self):
        self.assertEqual(kp.mask_others([1.0, 1.04, 1.2], [(10.0, 1.0, 2.4)]), [True, True, False])

    def test_other_ephemerides(self):
        # The star's KOI rows as TAP returns them (strings); the KOI itself and any unmasked KOI are left out.
        rows = [{"kepoi_name": "K02167.01", "koi_period": "24.3", "koi_time0bk": "136.1", "koi_duration": "3.9"},
                {"kepoi_name": "K02167.02", "koi_period": "6.96", "koi_time0bk": "359.0", "koi_duration": "4.5"},
                {"kepoi_name": "K02167.03", "koi_period": "76.5", "koi_time0bk": "164.2", "koi_duration": "5.6"}]
        self.assertEqual(kp.other_ephemerides(rows, "K02167.03"), [(24.3, 136.1, 3.9), (6.96, 359.0, 4.5)])
        self.assertEqual(kp.other_ephemerides(rows, "K02167.03", ["K02167.02"]), [(24.3, 136.1, 3.9)])
        self.assertEqual(kp.other_ephemerides(rows, "K02167.02", ["K02167.03"]), [(24.3, 136.1, 3.9)])


class Period(unittest.TestCase):
    def test_scaled_period(self):
        # KOI-4711.01: 4.3638313 x 2 = 8.7276626 d
        self.assertAlmostEqual(kp.scaled_period(4.3638313, 2), 8.7276626, places=9)
        self.assertEqual(kp.scaled_period(9.0, 1.0), 9.0)
        for bad in ((4.0, 1.5), (4.0, 0), (None, 2)):
            with self.assertRaises(ValueError):
                kp.scaled_period(*bad)

    def test_doubled_period_splits_alternate_events(self):
        # Seen at a catalogued 2.5 d, the synthetic quarter's dips alternate target / neighbour; at 2 x 2.5 d
        # phase 0 holds only the target's events and phase 0.5 only the neighbour's.
        p = kp.scaled_period(2.5, 2)
        rows = {r["phase"]: r for r in kp.quarter_fits(synthetic_quarter(), p, 2.5, DUR_H,
                                                       [0, 0.5], [], (2.0, -2.0))}
        self.assertLess(math.hypot(rows[0]["b_east"] / rows[0]["a"], rows[0]["b_north"] / rows[0]["a"]), 0.4)
        self.assertGreater(rows[0.5]["b_east"] / rows[0.5]["a"], 1.5)


class LinearAlgebra(unittest.TestCase):
    def test_invert(self):
        inv = kp.invert([[2, 1], [1, 3]])
        for got, want in zip(sum(inv, []), [0.6, -0.2, -0.2, 0.4]):
            self.assertAlmostEqual(got, want)
        self.assertIsNone(kp.invert([[1, 2], [2, 4]]))

    def test_lstsq_exact(self):
        beta, cov = kp.lstsq([[1, 0, 1, 2], [0, 1, 1, 1]], [2, 3, 5, 7])
        self.assertAlmostEqual(beta[0], 2.0)
        self.assertAlmostEqual(beta[1], 3.0)
        self.assertAlmostEqual(cov[0][0], 0.0)

    def test_gradients(self):
        gx, gy = kp.gradients([0, 1, 2, 10, 11, 12], 2, 3, [True] * 6)
        self.assertEqual(gx, [1, 1, 1, 1, 1, 1])
        self.assertEqual(gy, [10, 10, 10, 10, 10, 10])
        gx, gy = kp.gradients([0, 1, 2, 10, 11, 12], 2, 3, [True, False, True, True, True, True])
        self.assertEqual(gx[0], 0)  # right neighbour invalid, no left one
        self.assertEqual(gx[2], 0)
        self.assertEqual(gx[1], 0)  # invalid pixel itself
        self.assertEqual(gx[4], 1)

    def test_shifted(self):
        self.assertEqual(kp.shifted([1, 2, 3, 4], 2, 2, 0.0, 0.5), [1, 1.5, 3, 3.5])
        self.assertEqual(kp.shifted([1, 2, 3, 4], 2, 2, 0.0, 0.0), [1, 2, 3, 4])

    def test_sky_round_trip(self):
        jac = [[-3.0, 2.0], [1.5, 3.5]]
        self.assertEqual(kp.to_sky(jac, 1, 2), (1.0, 8.5))
        dcol, drow = kp.to_pix(jac, 1.0, 8.5)
        self.assertAlmostEqual(dcol, 1.0)
        self.assertAlmostEqual(drow, 2.0)


class Fit(unittest.TestCase):
    def test_small_shift_recovered(self):
        # For a Gaussian of sigma 1.2 px, central differences make the fitted shift about 17 % too large
        # (exp(-1/4s2) / (s2 (1 - exp(-1/s2))) = 1.166, s2 = 1.44): about -0.233 and 0.117 here.
        # a is 0.01 exp(-0.05 / 5.76) = 0.0099.
        o_img = gauss_img(9, 9, 4, 4, 1000.0)
        d_img = gauss_img(9, 9, 4.1, 3.8, 10.0)
        a, b, c, _ = kp.fit_shift(d_img, o_img, 9, 9, [True] * 81)
        self.assertAlmostEqual(a, 0.01, delta=0.0005)
        self.assertAlmostEqual(b / a, -0.2, delta=0.05)
        self.assertAlmostEqual(c / a, 0.1, delta=0.03)

    def test_quarter_on_target_and_neighbour(self):
        rows = {r["phase"]: r for r in kp.quarter_fits(synthetic_quarter(), 5.0, 2.5, DUR_H,
                                                       [0, 0.5, 0.25], [], (2.0, -2.0))}
        self.assertEqual((rows[0]["events"], rows[0.5]["events"], rows[0.25]["events"]), (4, 3, 4))
        r0 = rows[0]
        self.assertTrue(0.008 < r0["a"] < 0.011)
        self.assertLess(math.hypot(r0["b_east"] / r0["a"], r0["b_north"] / r0["a"]), 0.4)
        r5 = rows[0.5]
        e5, n5 = r5["b_east"] / r5["a"], r5["b_north"] / r5["a"]
        self.assertGreater(e5, 1.5)
        self.assertLess(n5, -1.5)
        self.assertLess(math.hypot(e5 - r5["cal_east"], n5 - r5["cal_north"]), 0.6)
        self.assertLess(abs(rows[0.25]["a"]), 1e-9)  # nothing happens at phase 0.25


def row(phase, a, east, north, cal=(2.0, -2.0)):
    return {"quarter": 0, "phase": phase, "events": 10, "a": a, "var_a": 1e-6, "b_east": a * east,
            "b_north": a * north, "cal_east": cal[0], "cal_north": cal[1]}


class Summary(unittest.TestCase):
    def test_jackknife(self):
        # Leave-one-out east values 2.0, 1.9, 2.1: se = sqrt(2/3 * 0.02) = 0.11547.
        e, n, se, sn = kp.jackknife([(1, 0.01, 0.020, -0.020), (1, 0.01, 0.022, -0.018), (1, 0.01, 0.018, -0.022)])
        self.assertAlmostEqual(e, 2.0)
        self.assertAlmostEqual(n, -2.0)
        self.assertAlmostEqual(se, 0.11547, places=4)
        self.assertAlmostEqual(sn, 0.11547, places=4)
        self.assertIsNone(kp.jackknife([(1, 0.01, 0.02, -0.02)] * 2))

    def test_verdicts(self):
        rows = [row(0.5, 0.01, 2.0, -2.0), row(0.5, 0.01, 2.2, -1.8), row(0.5, 0.01, 1.8, -2.2),
                row(0, 0.01, 0.0, 0.0), row(0, 0.01, 0.1, -0.1), row(0, 0.01, -0.1, 0.1),
                row(0.25, 1e-5, 0, 0), row(0.25, -1e-5, 0, 0), row(0.25, 0.0, 0, 0)]
        s5 = kp.summarise(rows, 0.5)
        self.assertEqual(s5["verdict"], "neighbour")
        self.assertAlmostEqual(s5["depth_ppm"], 10000.0)
        self.assertAlmostEqual(s5["chi2_zero"], 600.0, places=3)
        s0 = kp.summarise(rows, 0)
        self.assertEqual(s0["verdict"], "on_target")
        self.assertAlmostEqual(s0["err_east"], 0.057735, places=5)
        self.assertEqual(kp.summarise(rows, 0.25)["verdict"], "no_signal")
        self.assertEqual(kp.summarise(rows, 0.75)["verdict"], "unclear")  # no rows at all

    def test_verdict_rules(self):
        self.assertEqual(kp.verdict(10, 2, 50), "on_target")
        self.assertEqual(kp.verdict(10, 50, 2), "neighbour")
        self.assertEqual(kp.verdict(10, 2, 5), "unclear")
        self.assertEqual(kp.verdict(2, 0, 0), "no_signal")
        self.assertEqual(kp.verdict(None, 0, 0), "unclear")


if __name__ == "__main__":
    unittest.main()
