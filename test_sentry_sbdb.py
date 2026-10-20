# Apache-2.0. Tests for sentry_sbdb 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import os
import tempfile
import unittest
from decimal import Decimal

import sentry_sbdb as sx


class TestParsing(unittest.TestCase):
    def test_parse_dec(self):
        self.assertEqual(sx.parse_dec("18.56"), (Decimal("18.56"), Decimal("0.005")))
        self.assertEqual(sx.parse_dec(" 0.66 "), (Decimal("0.66"), Decimal("0.005")))
        self.assertEqual(sx.parse_dec("24"), (Decimal("24"), Decimal("0.5")))
        self.assertEqual(sx.parse_dec("-1.5"), (Decimal("-1.5"), Decimal("0.05")))
        for bad in ("1e-3", "", "1.2.3", "abc", None):
            self.assertIsNone(sx.parse_dec(bad))

    def test_d_rule_constant(self):
        # 1329 / sqrt(0.154) = 3386.606 km at H = 0
        self.assertAlmostEqual(sx.d_rule(0.0), 3386.6, delta=0.1)


class TestRules(unittest.TestCase):
    def test_diameter_status(self):
        # H 18.56 -> 0.6573 km at albedo 0.154; allowed 0.6492-0.6654 km after rounding and 1 % slack
        self.assertEqual(sx.diameter_status("18.56", "0.66"), "consistent")
        self.assertEqual(sx.diameter_status("18.56", "0.40"), "inconsistent")
        self.assertEqual(sx.diameter_status("18.56", "1.00"), "inconsistent")
        # H 22.0 -> 0.1348 km; allowed 0.1304-0.1393 km
        self.assertEqual(sx.diameter_status("22.0", "0.13"), "consistent")
        self.assertEqual(sx.diameter_status("22.0", "0.15"), "inconsistent")
        self.assertEqual(sx.diameter_status("18.56", "1e-3"), "unparsed")
        self.assertEqual(sx.diameter_status(None, "0.5"), "unparsed")

    def test_h_differs(self):
        self.assertFalse(sx.h_differs("18.56", "18.6"))    # 0.04 <= 0.005 + 0.05 + 0.01
        self.assertTrue(sx.h_differs("18.56", "18.4"))     # 0.16 > 0.065
        self.assertTrue(sx.h_differs("18.56", "18.62"))    # 0.06 > 0.02
        self.assertFalse(sx.h_differs("18.56", "18.57"))   # 0.01 <= 0.02
        self.assertIsNone(sx.h_differs("18.56", None))

    def test_obs_order_and_gap(self):
        self.assertEqual(sx.obs_order("2020-01-05", "2020-01-05"), "same")
        self.assertEqual(sx.obs_order("2020-01-05", "2021-03-01"), "later")
        self.assertEqual(sx.obs_order("2020-01-05", "2019-12-31"), "earlier")
        self.assertIsNone(sx.obs_order("2020-01-05", "2020-??-??"))
        self.assertIsNone(sx.obs_order("2020-01-05", None))
        self.assertEqual(sx.gap_days("2020-01-05", "2021-03-01"), 421)
        self.assertEqual(sx.gap_days("2020-01-05", "2019-12-31"), -5)
        self.assertIsNone(sx.gap_days("2020-01-05", "2020-??-??"))


class TestDecisions(unittest.TestCase):
    def test_d1(self):
        self.assertEqual(sx.decide_d1(999, 0), "underpowered")
        self.assertEqual(sx.decide_d1(1000, 30), "holds")   # 3000 <= 3000
        self.assertEqual(sx.decide_d1(1000, 31), "fails")

    def test_d2(self):
        self.assertEqual(sx.decide_d2(1000, 0, False), "not_scored_low_match")
        self.assertEqual(sx.decide_d2(999, 0, True), "underpowered")
        self.assertEqual(sx.decide_d2(1000, 20, True), "holds")   # 1000 <= 1000
        self.assertEqual(sx.decide_d2(1000, 21, True), "fails")

    def test_d3(self):
        self.assertEqual(sx.decide_d3(1000, 0, False), "not_scored_low_match")
        self.assertEqual(sx.decide_d3(999, 0, True), "underpowered")
        self.assertEqual(sx.decide_d3(1000, 100, True), "holds")  # 1000 <= 1000
        self.assertEqual(sx.decide_d3(1000, 101, True), "fails")


# Made-up fixture rows in the documented formats, not taken from any download.
SENTRY = [
    {"des": "2099 AA", "fullname": "(2099 AA)", "h": "18.56", "diameter": "0.66", "last_obs": "2020-01-05",
     "ip": "1e-06", "ps_cum": "-5.00"},
    {"des": "2099 AB", "fullname": "(2099 AB)", "h": "22.0", "diameter": "0.15", "last_obs": "2020-01-05",
     "ip": "1e-07", "ps_cum": "-7.00"},
    {"des": "1979 XB", "fullname": "(1979 XB)", "h": "18.56", "diameter": "0.66", "last_obs": "1979-12-15"},
    {"des": "2099 AC", "fullname": "(2099 AC)", "h": "20.00", "diameter": "0.34", "last_obs": "2021-06-30"},
]
SBDB = [
    {"spkid": "3999001", "pdes": "2099 AA", "kind": "au", "H": "18.6", "last_obs": "2021-03-01", "orbit_id": "5",
     "soln_date": "2021-03-02 10:00:00", "producer": "Fixture"},
    {"spkid": "3999002", "pdes": "2099 AB", "kind": "au", "H": "22.30", "last_obs": "2020-01-05", "orbit_id": "3",
     "soln_date": "2020-01-06 10:00:00", "producer": "Fixture"},
    {"spkid": "3999003", "pdes": "2099 ZZ", "kind": "au", "H": "25.1", "last_obs": "2022-01-01", "orbit_id": "1",
     "soln_date": "2022-01-02 10:00:00", "producer": "Fixture"},
]


class TestClassifyScore(unittest.TestCase):
    def test_classify(self):
        recs = sx.classify(SENTRY, SBDB)
        self.assertEqual([r["des"] for r in recs], ["2099 AA", "2099 AB", "2099 AC"])
        a, b, c = recs
        self.assertEqual(sorted(a), sorted(sx.OUT_HEADER))
        self.assertEqual((a["matched"], a["d_status"], a["obs_order"], a["obs_gap_days"], a["h_differs"],
                          a["h_diff"]), (1, "consistent", "later", 421, False, "0.04"))
        self.assertEqual((b["matched"], b["d_status"], b["obs_order"], b["obs_gap_days"], b["h_differs"],
                          b["h_diff"]), (1, "inconsistent", "same", 0, True, "0.30"))
        self.assertAlmostEqual(float(b["d_ratio"]), 1.1126, places=3)   # 0.15 / 0.13482
        self.assertEqual((c["matched"], c["d_status"], c["obs_order"], c["h_differs"], c["spkid"]),
                         (0, "consistent", None, None, None))

    def test_score(self):
        dec, desc = sx.score(sx.classify(SENTRY, SBDB))
        self.assertEqual(dec["D1"], {"n": 3, "inconsistent": 1, "decision": "underpowered"})
        self.assertEqual(dec["D2"], {"n": 2, "sbdb_later": 1, "match_ok": False,
                                     "decision": "not_scored_low_match"})
        self.assertEqual(dec["D3"], {"n": 2, "h_differs": 1, "match_ok": False,
                                     "decision": "not_scored_low_match"})
        self.assertEqual(desc["n_sentry_scored"], 3)
        self.assertEqual(desc["n_matched"], 2)
        self.assertEqual(desc["obs_order"], {"later": 1, "same": 1})
        self.assertEqual(desc["h_vs_obs"], {"h_differs=False obs=later": 1, "h_differs=True obs=same": 1})
        self.assertEqual(desc["producer_of_later"], {"Fixture": 1})
        self.assertEqual(desc["later_gap_days_quantiles"]["50"], 421)
        self.assertEqual(desc["h_diff_quantiles"]["50"], "0.30")
        self.assertEqual(desc["unmatched_des"], ["2099 AC"])
        self.assertEqual(desc["kind"], {"au": 2})
        json.dumps(desc)

    def test_score_match_ok(self):
        dec, _ = sx.score(sx.classify(SENTRY[:2], SBDB))
        self.assertTrue(dec["D2"]["match_ok"])
        self.assertEqual(dec["D2"]["decision"], "underpowered")


class TestGate(unittest.TestCase):
    def test_main_refuses_without_gate(self):
        with tempfile.TemporaryDirectory() as d:
            rc = sx.main(["--gate-note", os.path.join(d, "missing.md"), "--out-dir", os.path.join(d, "out")])
            self.assertEqual(rc, 2)
            with open(os.path.join(d, "out", "summary.json")) as f:
                s = json.load(f)
            self.assertFalse(s["gate"])
            self.assertNotIn("sentry", s)

    def test_gate_text(self):
        with tempfile.TemporaryDirectory() as d:
            note = os.path.join(d, "note.md")
            with open(note, "w", encoding="utf-8") as f:
                f.write("# CNEOS Sentry vs SBDB pre-registration (D1-D3)\n")
            self.assertTrue(sx.check_gate(note))


if __name__ == "__main__":
    unittest.main()
