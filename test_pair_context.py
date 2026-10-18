"""Tests for pair_context. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0.

Expected values were worked by hand from the MAST file-name stamps, the MAST quarter table and the NASA
Exoplanet Archive coordinates (read 2026-10-18).
"""
import csv
import json
import os
import tempfile
import unittest

import pair_context as pc


class StampTests(unittest.TestCase):
    def test_q0_end_matches_mast_exactly(self):
        # 2009 day 131 10:51:31 PDT = 2009-05-11 17:51:31 UTC = MJD 54962.74411
        self.assertAlmostEqual(pc.stamp_to_bkjd("2009131105131"), 130.24411, places=4)

    def test_pdt_before_november_change(self):
        # 2011-10-30 is before the 2011-11-06 change: +7 h
        self.assertAlmostEqual(pc.stamp_to_bkjd("2011303113607"), 1032.27508, places=4)

    def test_pst_after_november_change(self):
        # 2012-11-05 is after the 2012-11-04 change: +8 h
        self.assertAlmostEqual(pc.stamp_to_bkjd("2012310112549"), 1404.30959, places=4)

    def test_pdt_after_march_change(self):
        # 2010-03-19 is after the 2010-03-14 change: +7 h; MAST Q4 end MJD 55274.70384
        self.assertAlmostEqual(pc.stamp_to_bkjd("2010078095331"), 442.20383, places=4)

    def test_every_quarter_stamp_matches_mast_end(self):
        self.assertEqual(sorted(pc.LC_QUARTER_STAMPS), list(range(17)))
        for q, s in pc.LC_QUARTER_STAMPS.items():
            diff = pc.stamp_to_bkjd(s) - pc.mjd_to_bkjd(pc.QUARTER_END_MJD[q])
            self.assertLess(abs(diff), 0.0125, "Q%d off by %.4f d" % (q, diff))

    def test_wheel_rest_start(self):
        # 2013-01-17 11:39:07 PST = 19:39:07 UTC
        self.assertAlmostEqual(pc.stamp_to_bkjd("2013017113907"), 1477.31883, places=4)


class EventTests(unittest.TestCase):
    def test_event_counts(self):
        counts = {k: len(pc.events(v[0][2], v[0][3])) for k, v in pc.PAIRS.items()}
        self.assertEqual(counts, {"A": 4, "B": 4, "C": 3})

    def test_pair_b_trains(self):
        ev = pc.events(416.87893121, 227.5106644)
        for got, want in zip(ev, [227.5107, 644.3896, 1061.2686, 1478.1475]):
            self.assertAlmostEqual(got, want, places=3)

    def test_b3_two_days_before_downlink(self):
        c = pc.context(1061.2686)
        self.assertEqual(c["next"], "Q11 m2 end")
        self.assertAlmostEqual(c["days_before_next"], 1.963, places=2)
        self.assertEqual(c["prev"], "Q11 m1 end")

    def test_b4_inside_wheel_rest(self):
        c = pc.context(1478.1475)
        self.assertEqual(c["prev"], "Q16 wheel-rest start")
        self.assertAlmostEqual(c["days_after_prev"], 0.829, places=2)

    def test_c1_before_q1_end(self):
        c = pc.context(162.9131)
        self.assertEqual((c["prev"], c["next"]), ("Q1 start", "Q1 end"))
        self.assertAlmostEqual(c["days_before_next"], 2.068, places=2)

    def test_c2_after_q7_first_downlink(self):
        c = pc.context(665.1195)
        self.assertEqual(c["prev"], "Q7 m1 end")
        self.assertAlmostEqual(c["days_after_prev"], 4.838, places=2)

    def test_no_event_within_one_day_after_a_boundary(self):
        for key, (m1, _m2) in pc.PAIRS.items():
            for t in pc.events(m1[2], m1[3]):
                c = pc.context(t)
                if c["prev"] == "Q16 wheel-rest start":
                    continue
                self.assertGreater(c["days_after_prev"], 4.0, (key, t))
                self.assertGreater(c["days_before_next"], 1.9, (key, t))

    def test_seasons(self):
        seasons = {k: [pc.context(t)["quarter"] for t in pc.events(v[0][2], v[0][3])] for k, v in pc.PAIRS.items()}
        self.assertEqual(seasons, {"A": [4, 8, 12, 17], "B": [2, 7, 11, 16], "C": [1, 7, 12]})

    def test_cross_pair_min_gap(self):
        best = pc.cross_pair_min_gap()
        self.assertEqual((best[1], best[3]), ("A", "C"))
        self.assertAlmostEqual(best[0], 6.602, places=2)


class GeometryTests(unittest.TestCase):
    def test_centre_is_origin(self):
        x, y = pc.gnomonic(pc.FIELD_RA, pc.FIELD_DEC)
        self.assertAlmostEqual(x, 0.0, places=9)
        self.assertAlmostEqual(y, 0.0, places=9)

    def test_pure_declination_offset(self):
        x, y = pc.gnomonic(pc.FIELD_RA, 41.225510)
        self.assertAlmostEqual(x, 0.0, places=9)
        self.assertAlmostEqual(y, -3.2782, places=3)

    def test_hand_positions(self):
        want = {"A": [(5.839, 1.676), (-0.162, -3.278)], "B": [(2.284, 5.617), (6.291, -0.528)],
                "C": [(3.850, 0.088), (0.159, 1.217)]}
        for key, (m1, m2) in pc.PAIRS.items():
            for m, (wx, wy) in zip((m1, m2), want[key]):
                x, y = pc.gnomonic(m[4], m[5])
                self.assertAlmostEqual(x, wx, delta=0.02, msg=m[0])
                self.assertAlmostEqual(y, wy, delta=0.02, msg=m[0])

    def test_azimuth_gap(self):
        self.assertEqual(pc.azimuth_gap(10, 350), 20)
        self.assertEqual(pc.azimuth_gap(0, 180), 180)

    def test_no_pair_on_a_line_through_the_centre(self):
        want = {"A": 108.84, "B": 72.66, "C": 81.26}
        for key, (m1, m2) in pc.PAIRS.items():
            g = pc.pair_geometry(m1, m2)
            self.assertAlmostEqual(g["azimuth_gap_deg"], want[key], delta=1.5, msg=key)
            self.assertFalse(g["collinear_within_10deg"], key)


class RunTests(unittest.TestCase):
    def test_run_writes_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            summary, rows = pc.run(d)
            self.assertEqual(len(rows), 11)
            with open(os.path.join(d, "event_context.csv")) as f:
                self.assertEqual(len(list(csv.DictReader(f))), 11)
            with open(os.path.join(d, "segment_boundaries.csv")) as f:
                self.assertEqual(len(list(csv.DictReader(f))), 18 + 48 + 1)
            with open(os.path.join(d, "summary.json")) as f:
                self.assertEqual(json.load(f)["version"], pc.VERSION)


if __name__ == "__main__":
    unittest.main()
