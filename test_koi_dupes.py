"""Tests for koi_dupes. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0.

Every expected number below was worked out by hand (see the comments). The Kepler-289 values are the
live cumulative and pscomppars rows read on 2026-10-17."""
import csv
import json
import os
import tempfile
import unittest

import koi_dupes as kd

BKJD = 2454833.0


def koi(kepid, name, p, t0bk, dur_h, disp="CANDIDATE", kepler_name=""):
    return {"kepid": str(kepid), "kepoi_name": name, "kepler_name": kepler_name,
            "koi_disposition": disp, "koi_pdisposition": disp, "koi_period": str(p),
            "koi_time0bk": str(t0bk), "koi_duration": str(dur_h), "koi_depth": "", "koi_prad": "",
            "koi_fpflag_ec": "0"}


def ps(host, name, p, t, dur_h=""):
    return {"hostname": host, "pl_name": name, "pl_orbper": str(p), "pl_tranmid": str(t),
            "pl_trandur": str(dur_h), "pl_rade": "", "disc_year": "", "disc_facility": ""}


KOI_289 = [
    koi(7303287, "K01353.01", 125.86540191, 236.659731, 9.0191, "CONFIRMED", "Kepler-289 c"),
    koi(7303287, "K01353.02", 34.5439452, 132.68453, 3.482, "CONFIRMED", "Kepler-289 b"),
    koi(7303287, "K01353.03", 330.071558, 340.9871, 4.295, "CONFIRMED", "Kepler-289 e"),
]
PS_289 = [
    ps("Kepler-289", "Kepler-289 e", 330.0716, 2455173.987, 4.295),
    ps("Kepler-289", "Kepler-289 b", 34.5383, 2454965.6879, 3.178),
    ps("Kepler-289", "Kepler-289 d", 66.0282, 2454975.624, 3.557),
    ps("Kepler-289", "Kepler-289 c", 125.8723, 2455069.6734, 9.0191),
]
OTHER = [
    # kepid 1: a k = 3 duplicate. 30.0009 / 10 = 3.00009; drift = 0.0009 * 1460 / 30.0009 = 0.0438;
    # dT = 20.01, n = 2, off = 0.01 <= window (2 + 3) / 24 = 0.2083
    koi(1, "K09001.01", 10.0, 100.0, 2.0),
    koi(1, "K09001.02", 30.0009, 120.01, 3.0),
    # kepid 2: an eclipsing binary's primary and secondary: k = 1, dT = 2.5, n = round(0.5) = 0
    koi(2, "K09002.01", 5.0, 100.0, 2.0, "FALSE POSITIVE"),
    koi(2, "K09002.02", 5.0, 102.5, 2.0, "FALSE POSITIVE"),
    koi(3, "K09003.01", "", 100.0, 2.0),  # no period: skipped
]


class Classify(unittest.TestCase):
    def test_kepler_289_d_vs_koi_1353_03(self):
        # 330.071558 / 66.0282 = 4.99895, k = 5; |330.071558 - 330.141| = 0.069442
        # drift = 0.069442 * 1460 / 330.071558 = 0.3072
        # dT = 2455173.9871 - 2454975.624 = 198.3631, n = 3, off = 198.3631 - 198.0846 = 0.2785
        # window = (3.557 + 4.295) / 24 = 0.32717
        r = kd.classify(66.0282, 2454975.624, 3.557 / 24, 330.071558, 340.9871 + BKJD, 4.295 / 24)
        self.assertEqual((r["status"], r["k"], r["n"]), ("same_events", 5, 3))
        self.assertAlmostEqual(r["off_d"], 0.2785, places=4)
        self.assertAlmostEqual(r["drift_d"], 0.307, places=2)
        self.assertAlmostEqual(r["window_d"], 0.32717, places=4)

    def test_resonant_pair_offset(self):
        # 20.001 / 10, k = 2, drift = 0.001 * 1460 / 20.001 = 0.073; dT = 2.5, n = 0, off 2.5 > 0.2
        r = kd.classify(10.0, 0.0, 0.1, 20.001, 2.5, 0.1)
        self.assertEqual((r["status"], r["k"], r["n"]), ("offset", 2, 0))
        self.assertAlmostEqual(r["off_d"], 2.5)

    def test_drift_too_large(self):
        # 20.01: drift = 0.01 * 1460 / 20.01 = 0.73 > 0.5
        self.assertIsNone(kd.classify(10.0, 0.0, 0.1, 20.01, 0.0, 0.1))
        # 15 / 10 = 1.5, k = 2, drift = 5 * 1460 / 15
        self.assertIsNone(kd.classify(10.0, 0.0, 0.1, 15.0, 0.0, 0.1))

    def test_k_max(self):
        self.assertIsNone(kd.classify(1.0, 0.0, 0.05, 31.0, 0.0, 0.05))
        r = kd.classify(1.0, 0.0, 0.05, 30.0, 0.0, 0.05)
        self.assertEqual((r["status"], r["k"], r["n"], r["off_d"]), ("same_events", 30, 0, 0.0))

    def test_same_period_duplicate(self):
        # k = 1, dT = 0.05, off 0.05 <= 0.2
        r = kd.classify(7.0, 100.0, 0.1, 7.0, 100.05, 0.1)
        self.assertEqual((r["status"], r["k"], r["n"]), ("same_events", 1, 0))
        self.assertAlmostEqual(r["off_d"], 0.05)

    def test_null_shift(self):
        # shift 0.25: dT = 0 + 1.75, n = 0, off 1.75 > 0.2
        r = kd.classify(7.0, 100.0, 0.1, 7.0, 100.0, 0.1, shift=0.25)
        self.assertEqual(r["status"], "offset")
        self.assertAlmostEqual(r["off_d"], 1.75)

    def test_bad_input(self):
        self.assertIsNone(kd.classify(0.0, 0.0, 0.1, 10.0, 0.0, 0.1))
        self.assertIsNone(kd.classify(10.0, None, 0.1, 10.0, 0.0, 0.1))
        self.assertIsNone(kd.classify(20.0, 0.0, 0.1, 10.0, 0.0, 0.1))

    def test_host_of(self):
        self.assertEqual(kd.host_of("Kepler-289 e"), "Kepler-289")
        self.assertIsNone(kd.host_of(""))
        self.assertIsNone(kd.host_of(None))


class Scan(unittest.TestCase):
    def test_flags(self):
        # KOI pairs on 7303287: .01/.02 ratio 3.644, .01/.03 2.622, .02/.03 9.555: all drift out.
        # Cross: only Kepler-289 d has no KOI; vs .01 (1.906) and .02 (1.911) drift out; vs .03 flags.
        flags = kd.scan(KOI_289 + OTHER, PS_289)
        self.assertEqual([(f["mode"], f["short"], f["long"], f["status"], f["k"]) for f in flags],
                         [("cross", "Kepler-289 d", "K01353.03", "same_events", 5),
                          ("koi", "K09001.01", "K09001.02", "same_events", 3),
                          ("koi", "K09002.01", "K09002.02", "offset", 1)])
        self.assertEqual((flags[0]["disp_short"], flags[0]["disp_long"]), ("PS", "CONFIRMED"))
        self.assertEqual(flags[0]["host"], "Kepler-289")
        self.assertAlmostEqual(flags[1]["off_d"], 0.01, places=6)

    def test_null(self):
        # shift 0.5 turns the binary's secondary into a match: dT = 2.5 + 2.5 = 5, n = 1, off 0.
        # kepid 1 at 0.5: dT = 25.01, n = 3, off -4.99. Kepler-289 at 0.5: dT = 231.377, n = 4.
        rows = KOI_289 + OTHER
        t = kd.tally(kd.scan(rows, PS_289, 0.5))
        self.assertEqual((t["koi"]["same_events"], t["cross"]["same_events"]), (1, 0))
        # 0.25: kepid 1 dT 22.51 off 2.51; kepid 2 dT 3.75 off -1.25; Kepler-289 dT 214.870 off 16.79
        # 0.75: kepid 1 dT 27.51 off -2.49; kepid 2 dT 6.25 off 1.25; Kepler-289 dT 247.884 off -16.23
        for s in (0.25, 0.75):
            t = kd.tally(kd.scan(rows, PS_289, s))
            self.assertEqual((t["koi"]["same_events"], t["cross"]["same_events"]), (0, 0))

    def test_main_writes_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            kc, pc = os.path.join(tmp, "koi.csv"), os.path.join(tmp, "ps.csv")
            for path, rows in ((kc, KOI_289 + OTHER), (pc, PS_289)):
                with open(path, "w", encoding="utf-8", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0]))
                    w.writeheader()
                    w.writerows(rows)
            out = os.path.join(tmp, "out")
            kd.main(["--out-dir", out, "--koi-csv", kc, "--ps-csv", pc])
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual((s["koi_rows"], s["ps_rows"], s["stars"]), (8, 4, 4))
            self.assertEqual(s["counts"]["cross"], {"same_events": 1, "offset": 0,
                                                    "same_both_not_fp": 1, "same_any_fp": 0})
            self.assertEqual(s["counts"]["koi"], {"same_events": 1, "offset": 1,
                                                  "same_both_not_fp": 1, "same_any_fp": 0})
            self.assertEqual(s["null"]["0.5"]["koi"]["same_events"], 1)
            self.assertEqual(s["chance_same_events"], {"koi": 0.0, "cross": 0.0})
            self.assertEqual(len(s["same_events"]), 2)
            self.assertTrue(s["same_events"][0].startswith("cross: Kepler-289 d (PS) / K01353.03"))
            with open(os.path.join(out, "flags.csv"), encoding="utf-8") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 3)


if __name__ == "__main__":
    unittest.main()
