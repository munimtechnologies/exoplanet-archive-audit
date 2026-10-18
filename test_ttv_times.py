"""Tests for ttv_times 0.1.0 (standard library; no network). MV2 of Munim, Inc. Apache-2.0."""
import math
import unittest

import ttv_times as tt

CAD = 0.0204336


def synth(tc=100.123, depth=0.005, t14_h=3.1, frac=0.3, slope=1e-4, start=99.0, n=98, noise=1e-4):
    times, fluxes = [], []
    for i in range(n):
        t = start + i * CAD
        base = 1.0 + slope * (t - tc)
        f = base * (1.0 - depth * tt.trapezoid(t, tc, t14_h / 24.0, frac)) + noise * math.sin(37.0 * t)
        times.append(t)
        fluxes.append(f)
    return times, fluxes


class TrapezoidTests(unittest.TestCase):
    def test_shape_values(self):
        t14 = 0.1
        self.assertEqual(tt.trapezoid(5.0, 5.0, t14, 0.3), 1.0)
        self.assertEqual(tt.trapezoid(5.06, 5.0, t14, 0.3), 0.0)
        self.assertEqual(tt.trapezoid(4.94, 5.0, t14, 0.3), 0.0)
        # mid-ingress: half = 0.05, tau = 0.03, flat = 0.02; x = 0.035 -> (0.05 - 0.035) / 0.03 = 0.5
        self.assertAlmostEqual(tt.trapezoid(5.035, 5.0, t14, 0.3), 0.5, places=9)
        # V shape (frac 0.5): x = 0.025 -> 0.5
        self.assertAlmostEqual(tt.trapezoid(5.025, 5.0, t14, 0.5), 0.5, places=9)


class SolveTests(unittest.TestCase):
    def test_solve3(self):
        A = [[2.0, 1.0, 0.0], [1.0, 3.0, 1.0], [0.0, 1.0, 4.0]]
        x = [1.0, -2.0, 0.5]
        b = [sum(A[i][j] * x[j] for j in range(3)) for i in range(3)]
        sol = tt.solve3(A, b)
        for got, want in zip(sol, x):
            self.assertAlmostEqual(got, want, places=12)

    def test_singular(self):
        self.assertIsNone(tt.solve3([[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [0.0, 0.0, 1.0]], [1.0, 2.0, 3.0]))


class FitTests(unittest.TestCase):
    def test_recovers_synthetic(self):
        times, fluxes = synth()
        r = tt.fit_event(times, fluxes, 100.1)
        self.assertIsNotNone(r)
        self.assertLessEqual(abs(r["tc"] - 100.123), 0.006)
        self.assertLessEqual(abs(r["depth_ppm"] - 5000.0), 500.0)
        self.assertFalse(r["at_edge"])
        self.assertLessEqual(r["tc_hi"] - r["tc_lo"], 0.05)
        self.assertGreater(r["n_in"], 3)

    def test_no_in_transit_points(self):
        times, fluxes = synth()
        self.assertIsNone(tt.fit_shape(times, fluxes, 150.0, 0.13, 0.3))

    def test_ingress_in_hole(self):
        times, fluxes = synth()
        keep = [(t, f) for t, f in zip(times, fluxes) if not (100.123 - 0.25 <= t <= 100.123 - 0.01)]
        r = tt.fit_event([k[0] for k in keep], [k[1] for k in keep], 100.1)
        self.assertIsNotNone(r)
        self.assertLessEqual(abs(r["tc"] - 100.123), 0.1)

    def test_too_few_points(self):
        self.assertIsNone(tt.fit_event([1.0, 2.0], [1.0, 1.0], 1.5))


class LinearTests(unittest.TestCase):
    def test_exact_line(self):
        P, T0 = 272.137, 378.2
        times = [T0 + P * n for n in range(5)]
        lin = tt.linear_fit(times, [0.01] * 5)
        self.assertAlmostEqual(lin["P"], P, places=6)
        self.assertAlmostEqual(lin["T0"], T0, places=6)
        self.assertEqual(lin["n"], [0, 1, 2, 3, 4])
        self.assertLess(lin["max_abs_oc"], 1e-6)
        self.assertEqual(lin["dof"], 3)

    def test_residual(self):
        P, T0 = 272.1, 378.2
        times = [T0 + P * n for n in range(5)]
        times[3] += 0.4
        lin = tt.linear_fit(times, [0.02] * 5)
        self.assertGreater(lin["max_abs_oc"], 0.2)
        self.assertGreater(lin["chi2"], 25.0)


class CdsTests(unittest.TestCase):
    HEADER = (
        "Title: test\n"
        "--------------------------------------------------------------------------------\n"
        "Byte-by-byte Description of file: x.txt\n"
        "--------------------------------------------------------------------------------\n"
        "   Bytes Format Units   Label   Explanations\n"
        "--------------------------------------------------------------------------------\n"
        "   1-  7 F7.2   ---     KOI     KOI number\n"
        "   9- 19 F11.6  d       T0      Mid-transit time (BJD-2454900)\n"
        "  21     I1     ---     Flag    A flag\n"
        "--------------------------------------------------------------------------------\n"
        "Note (1): nothing\n"
        "--------------------------------------------------------------------------------\n"
    )
    DATA = "1209.01  311.176783 1\n1210.01  400.000000 0\n"

    def test_parse_and_slice(self):
        text = self.HEADER + self.DATA
        specs = tt.parse_bbb(tt.header_block(text))
        self.assertEqual([s[4] for s in specs], ["KOI", "T0", "Flag"])
        self.assertEqual(specs[2][:2], (21, 21))
        lines = tt.extract_koi(text, "1209.01")
        self.assertEqual(len(lines), 1)
        row = tt.slice_row(lines[0], specs)
        self.assertEqual(row["KOI"], "1209.01")
        self.assertAlmostEqual(float(row["T0"]) + tt.BJD_OFFSET, 378.176783, places=6)
        self.assertEqual(row["Flag"], "1")

    def test_data_lines_do_not_parse_as_specs(self):
        self.assertEqual(tt.parse_bbb(self.DATA), [])


class WindowTests(unittest.TestCase):
    def test_dedupe(self):
        rows = [("a", 10.0, 1.0), ("b", 10.0, 1.0), ("a", 10.5, 0.99), ("a", 12.0, 1.0)]
        times, fluxes = tt.collect_window(rows, 10.2, window=1.0)
        self.assertEqual(times, [10.0, 10.5])
        self.assertEqual(fluxes, [1.0, 0.99])


if __name__ == "__main__":
    unittest.main()
