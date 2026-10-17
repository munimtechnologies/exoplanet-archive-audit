"""Tests for alias_dupes. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0.

Every expected number below was worked out by hand (see the comments)."""
import csv
import json
import os
import tempfile
import unittest

import alias_dupes as ad


def row(host, name, p, t="", rade="", year="2014"):
    return {"hostname": host, "pl_name": name, "pl_orbper": str(p), "pl_tranmid": str(t),
            "pl_rade": rade, "disc_year": year}


KEPLER_289 = [
    row("Kepler-289", "Kepler-289 b", 34.5383, 2454965.6404),
    row("Kepler-289", "Kepler-289 d", 66.0282, 2454975.6240),
    row("Kepler-289", "Kepler-289 c", 125.8723, 2455069.6528),
    row("Kepler-289", "Kepler-289 e", 330.0716, 2455173.9870, year="2025"),
]


class Classify(unittest.TestCase):
    def test_kepler_289_d_e(self):
        # 330.0716 / 66.0282 = 4.998949, k = 5, rel = 0.001051 / 5 = 0.000210
        # dT = 198.3630, n = 3, off = 198.3630 - 198.0846 = 0.2784, phase = 0.00422
        # drift = |330.0716 - 330.1410| * 1460 / 330.0716 = 0.0694 * 4.4233 = 0.307
        r = ad.classify(66.0282, 2454975.6240, 330.0716, 2455173.9870)
        self.assertEqual(r["status"], "same_events")
        self.assertEqual(r["k"], 5)
        self.assertEqual(r["n"], 3)
        self.assertAlmostEqual(r["off_d"], 0.2784, places=4)
        self.assertAlmostEqual(r["phase"], 0.2784 / 66.0282, places=6)
        self.assertTrue(0.00020 < r["rel"] < 0.00022)
        self.assertAlmostEqual(r["drift_d"], 0.307, places=2)

    def test_resonant_pair_offset(self):
        # 20.01 / 10 = 2.001, rel 0.0005; dT = 2.5, n = 0, phase 0.25
        r = ad.classify(10.0, 0.0, 20.01, 2.5)
        self.assertEqual(r["status"], "offset")
        self.assertEqual(r["k"], 2)
        self.assertEqual(r["n"], 0)
        self.assertAlmostEqual(r["phase"], 0.25)

    def test_non_integer_ratio(self):
        self.assertIsNone(ad.classify(10.0, 0.0, 15.0, 1.0))  # 1.5, rel 0.25
        self.assertIsNone(ad.classify(10.0, 0.0, 20.1, 0.0))  # 2.01, rel 0.005

    def test_no_epoch(self):
        r = ad.classify(10.0, None, 30.0, 5.0)
        self.assertEqual(r["status"], "no_epoch")
        self.assertEqual(r["k"], 3)
        self.assertEqual(r["rel"], 0.0)
        self.assertIsNone(r["phase"])

    def test_same_period_two_names(self):
        r = ad.classify(7.0, 100.0, 7.0, 100.0)
        self.assertEqual((r["status"], r["k"], r["n"], r["off_d"]), ("same_events", 1, 0, 0.0))

    def test_long_planet_epoch_earlier(self):
        # dT = -97.9 - 100 = -197.9, n = round(-2.9985) = -3, off = -197.9 + 198 = 0.1
        r = ad.classify(66.0, 100.0, 330.0, -97.9)
        self.assertEqual(r["status"], "same_events")
        self.assertEqual(r["n"], -3)
        self.assertAlmostEqual(r["off_d"], 0.1, places=6)

    def test_bad_input(self):
        self.assertIsNone(ad.classify(0.0, 0.0, 10.0, 0.0))
        self.assertIsNone(ad.classify(None, 0.0, 10.0, 0.0))
        self.assertIsNone(ad.classify(20.0, 0.0, 10.0, 0.0))


class Scan(unittest.TestCase):
    def rows(self):
        return KEPLER_289 + [
            # same period and phase as Kepler-289 d but another host: must not pair across hosts
            row("Other-1", "Other-1 b", 66.0282, 2454975.6240),
            row("Other-1", "Other-1 c", 200.0, 2455000.0),  # 200 / 66.0282 = 3.029, rel 0.0097
            row("RV-1", "RV-1 b", 5.0),
            row("RV-1", "RV-1 c", 10.0),
            row("RV-1", "RV-1 d", ""),  # no period: skipped
        ]

    def test_flags(self):
        # Kepler-289 pairs: b/d 1.912, b/c 3.644, b/e 9.557, d/c 1.906, c/e 2.622 all fail;
        # only d/e passes. RV-1 b/c: k = 2, rel 0, no times.
        flags = ad.scan(self.rows())
        self.assertEqual([(f["short"], f["long"], f["status"]) for f in flags],
                         [("Kepler-289 d", "Kepler-289 e", "same_events"),
                          ("RV-1 b", "RV-1 c", "no_epoch")])
        self.assertEqual(flags[0]["disc_long"], "2025")

    def test_main_writes_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "in.csv")
            with open(src, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["hostname", "pl_name", "pl_orbper", "pl_tranmid",
                                                  "pl_rade", "disc_year"])
                w.writeheader()
                w.writerows(self.rows())
            out = os.path.join(tmp, "out")
            ad.main(["--out-dir", out, "--csv", src])
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual(s["rows"], 9)
            self.assertEqual(s["hosts"], 3)
            self.assertEqual(s["counts"], {"same_events": 1, "no_epoch": 1})
            self.assertEqual(s["same_events"], ["Kepler-289 d / Kepler-289 e (k=5)"])
            with open(os.path.join(out, "flags.csv"), encoding="utf-8") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 2)


if __name__ == "__main__":
    unittest.main()
