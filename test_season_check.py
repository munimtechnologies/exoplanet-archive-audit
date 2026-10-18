"""Tests for season_check. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0.

Every expected value was worked by hand. Quarter starts are the first cadences of quarters 3, 7, 11 and 15 in
the KIC 9018021 files (results/2026-10-18-koi5600-lightcurve-0.1.0/coverage.csv); they are spacecraft-wide.
The synthetic light curve is noise-free: cadences every 0.02 d from 0 to 39.98, flux 1, and a 1,000 ppm step
over |t - 21.2| < 0.25, wider than the 12 h box's core (|d| < 0.175) and inside its baseline gap (|d| < 0.5).
"""
import unittest

import season_check as sc

STARTS = [260.2451, 630.1955, 1001.2288, 1373.5085]


def koi(kepid, disp, p, ra, dec, kp, name=None, t0=100.0, dur=3.0):
    return {"kepid": str(kepid), "kepoi_name": name or f"K{kepid:05d}.01", "koi_disposition": disp,
            "koi_period": str(p), "koi_time0bk": str(t0), "koi_duration": str(dur), "ra": str(ra), "dec": str(dec),
            "koi_kepmag": str(kp)}


ROWS = [koi(1, "CANDIDATE", 10.0, 290.0, 41.5, 14.0),
        koi(2, "CONFIRMED", 50.0, 290.0, 41.5, 14.0), koi(2, "FALSE POSITIVE", 5.0, 290.0, 41.5, 14.0, "K00002.02"),
        koi(3, "CANDIDATE", 400.0, 290.0, 41.5, 14.0),
        koi(4, "CANDIDATE", 20.0, 290.0, 41.5, 17.0),
        koi(5, "CANDIDATE", 5.0, 290.1, 41.5, 13.0),
        koi(6, "CANDIDATE", 5.0, 290.0, 41.5, 13.0),
        koi(7, "CANDIDATE", 3.0, 280.0, 41.5, 15.0)]


class Geometry(unittest.TestCase):
    def test_sep(self):
        self.assertAlmostEqual(sc.sep_deg(0.0, 0.0, 0.0, 1.0), 1.0, places=9)
        a, b = sc.KOIS["K05269.01"], sc.KOIS["K05227.01"]
        self.assertAlmostEqual(sc.sep_deg(a[4], a[5], b[4], b[5]), 0.877, delta=0.002)

    def test_in_season(self):
        self.assertTrue(all(sc.in_season(q) for q in (3, 7, 11, 15)))
        self.assertFalse(any(sc.in_season(q) for q in (0, 1, 2, 4, 16, 17, None, "")))


class Offsets(unittest.TestCase):
    def test_k05269(self):
        p, t0 = sc.KOIS["K05269.01"][1:3]
        got = sc.offsets_after_start(p, t0, STARTS + [352.3973])
        self.assertEqual(len(got), 4)
        for (_, _, d), want in zip(got, (-0.1208, 1.4351, 1.9081, 1.1347)):
            self.assertAlmostEqual(d, want, places=4)

    def test_all_five_open_the_season_quarters(self):
        for label, (_, p, t0, _, _, _) in sc.KOIS.items():
            got = sc.offsets_after_start(p, t0, STARTS)
            self.assertEqual(len(got), 4, label)
            self.assertTrue(all(-0.40 <= d <= 1.93 for _, _, d in got), label)


class Locate(unittest.TestCase):
    METAS = [{"quarter": 2, "start": 169.7653, "end": 258.4675}, {"quarter": 3, "start": 260.2451, "end": 349.4958}]

    def test_in_gap_before_start(self):
        self.assertEqual(sc.locate(259.8491, self.METAS), ("", 3, -0.396))

    def test_after_start(self):
        q_in, q_near, d = sc.locate(261.0, self.METAS)
        self.assertEqual((q_in, q_near), (3, 3))
        self.assertAlmostEqual(d, 0.7549, places=4)

    def test_mid_quarter(self):
        self.assertEqual(sc.locate(300.0, self.METAS), (3, "", ""))


class Null(unittest.TestCase):
    def test_avoids_starts_and_events(self):
        times = [0.5 * i for i in range(201)]
        got = sc.null_times(times, [50.0], [20.0], n=100)
        self.assertEqual(len(got), 92)
        for t in (49.5, 50.5, 52.5, 18.5, 21.5):
            self.assertNotIn(t, got)
        for t in (48.5, 53.5, 17.5, 22.5):
            self.assertIn(t, got)


class Controls(unittest.TestCase):
    def test_one_each(self):
        got = sc.select_controls(ROWS, [(290.0, 41.5), (290.1, 41.5)], each=1, exclude={6})
        self.assertEqual([c[0] for c in got], [1, 5])
        self.assertEqual(got[0][4], [(10.0, 100.0, 3.0)])
        self.assertEqual([c[5] for c in got], [0, 1])
        self.assertEqual([c[6] for c in got], [0.0, 0.0])

    def test_two_each_distinct(self):
        got = sc.select_controls(ROWS, [(290.0, 41.5), (290.1, 41.5)], each=2, exclude={6})
        self.assertEqual([c[0] for c in got], [1, 5, 7])

    def test_masks_for(self):
        self.assertEqual(sc.masks_for(2, ROWS), [(50.0, 100.0, 3.0), (5.0, 100.0, 3.0)])
        self.assertEqual(sc.masks_for(2, ROWS, skip="K00002.02"), [(50.0, 100.0, 3.0)])


def cell(season, dip, group="control", kind="qstart"):
    return {"group": group, "kind": kind, "in_season": season, "dip": dip}


class Stats(unittest.TestCase):
    def test_binom_tail(self):
        self.assertAlmostEqual(sc.binom_tail(0, 5, 0.3), 1.0, places=12)
        self.assertAlmostEqual(sc.binom_tail(2, 2, 0.5), 0.25, places=12)
        self.assertAlmostEqual(sc.binom_tail(1, 2, 0.05), 0.0975, places=12)

    def test_fractions_and_p3(self):
        rows = [cell(1, 1), cell(1, 1), cell(1, 0), cell(1, ""), cell(0, 0), cell(0, 0), cell(0, 1), cell(0, 0),
                cell(0, 0), cell(1, 1, group="fp"), cell(1, 1, group="candidate", kind="own")]
        f = sc.fractions(rows, ("control",))
        self.assertEqual((f["season"]["dips"], f["season"]["cells"], f["season"]["fraction"]), (2, 3, 0.667))
        self.assertEqual((f["other"]["dips"], f["other"]["cells"], f["other"]["fraction"]), (1, 5, 0.2))
        self.assertAlmostEqual(f["season"]["p_binom"], 0.00725, places=6)
        self.assertAlmostEqual(f["other"]["p_binom"], 0.226219, places=6)
        self.assertTrue(sc.p3(f))
        f["other"]["fraction"] = 0.25
        self.assertFalse(sc.p3(f))
        self.assertIsNone(sc.p3({"season": {"cells": 0}, "other": {"cells": 5, "fraction": 0.2}}))


def flat_series(dip_at=21.2, depth=0.001, half=0.25):
    times = [0.02 * i for i in range(2000)]
    pdc = [1.0 - (depth if abs(t - dip_at) < half else 0.0) for t in times]
    return {"pdc": (times, pdc), "sap": (times, list(pdc)), "bkg": (times, [0.0] * len(times)),
            "c1": (times, [100.0] * len(times)), "c2": (times, [200.0] * len(times))}, times


class Evaluate(unittest.TestCase):
    def test_synthetic(self):
        series, times = flat_series()
        metas = [{"quarter": 2, "season": 0, "module": 10, "output": 1, "channel": 29, "start": 0.0, "end": 19.98,
                  "file": "a"},
                 {"quarter": 3, "season": 1, "module": 16, "output": 2, "channel": 58, "start": 20.0, "end": 39.98,
                  "file": "b"}]
        rows, info = sc.evaluate("K", "candidate", 1, 12.0, series, times, [0] * len(times), metas, [21.2])
        self.assertEqual([r["kind"] for r in rows], ["own", "qstart", "qstart"])
        own, q2, q3 = rows
        for r in (own, q3):
            self.assertEqual((r["quarter"], r["in_season"], r["channel"], r["dip"]), (3, 1, 58, 1))
            self.assertAlmostEqual(r["pdc_ppm"], 1000.0, delta=0.1)
            self.assertAlmostEqual(r["after_start_d"], 1.2, places=4)
            self.assertEqual(r["flag_cadences"], 0)
        self.assertEqual((q2["quarter"], q2["in_season"], q2["channel"]), (2, 0, 29))
        self.assertAlmostEqual(q2["pdc_ppm"], 0.0, delta=0.1)
        self.assertGreater(info["null_n"], 10)
        self.assertEqual(info["quarters"][1]["channel"], 58)


class Tap(unittest.TestCase):
    def test_query(self):
        self.assertIn("from+cumulative", sc.TAP)
        self.assertIn("koi_kepmag", sc.TAP)


if __name__ == "__main__":
    unittest.main()
