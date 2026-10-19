# Apache-2.0. Tests for sbdb_triplet 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import os
import tempfile
import unittest

import sbdb_triplet as st


class TestParsing(unittest.TestCase):
    def test_half_unit(self):
        self.assertAlmostEqual(st.half_unit("0.090"), 0.0005)
        self.assertAlmostEqual(st.half_unit("939.4"), 0.05)
        self.assertAlmostEqual(st.half_unit("939"), 0.5)
        self.assertAlmostEqual(st.half_unit("-0.5"), 0.05)
        self.assertIsNone(st.half_unit("1e-3"))
        self.assertIsNone(st.half_unit(""))
        self.assertIsNone(st.half_unit("1.2.3"))
        self.assertIsNone(st.half_unit("abc"))

    def test_parse_page_keeps_strings(self):
        body = json.dumps({"signature": {"version": "1.0"}, "count": 2, "fields": ["spkid", "H", "albedo"],
                           "data": [[20000001, "3.34", "0.090"], [20000004, "3.25", None]]}).encode()
        count, fields, rows = st.parse_page(body)
        self.assertEqual(count, 2)
        self.assertEqual(fields, ["spkid", "H", "albedo"])
        self.assertEqual(rows[0], {"spkid": "20000001", "H": "3.34", "albedo": "0.090"})
        self.assertIsNone(rows[1]["albedo"])

    def test_page_url(self):
        u = st.page_url(40000)
        self.assertIn("limit-from=40000", u)
        self.assertIn("limit=20000", u)
        self.assertIn("sort=spkid", u)
        self.assertIn("sb-kind=a", u)


class TestMetrics(unittest.TestCase):
    def test_h_fit_hand_value(self):
        # D = 10 km, p = 0.1: 10 * 0.316228 / 1329 = 0.00237944, log10 = -2.623525, H = 13.1176
        self.assertAlmostEqual(st.h_fit(10.0, 0.1), 13.1176, places=3)

    def test_ceres_hand_values(self):
        # H 3.34, D 939.4, p 0.090: D sqrt(p) / 1329 = 0.2120542, H_fit = 3.367765, dH = -0.027765 -> -278.
        # Worst corner (D - 0.05, p - 0.0005): 0.000116 + 0.006049, plus 0.005 for H -> ceil(111.64) + 100 = 212.
        m = st.row_metrics("3.34", "939.4", "0.090")
        self.assertEqual(m["status"], "ok")
        self.assertAlmostEqual(m["h_fit"], 3.367765, places=4)
        self.assertEqual(m["dh_e4"], -278)
        self.assertEqual(m["tol_e4"], 212)
        self.assertTrue(m["shifted"])
        self.assertAlmostEqual(m["p_now"], 0.090 * 10 ** (0.4 * 0.027765), places=6)

    def test_consistent_row_not_shifted(self):
        m = st.row_metrics("13.12", "10.000", "0.100")
        self.assertEqual(m["status"], "ok")
        self.assertEqual(m["dh_e4"], 24)
        self.assertFalse(m["shifted"])

    def test_fainter_h_is_positive_shift(self):
        m = st.row_metrics("13.40", "10.000", "0.100")
        self.assertEqual(m["dh_e4"], 2824)
        self.assertTrue(m["shifted"])
        self.assertLess(m["p_now"], 0.100)

    def test_bad_rows(self):
        self.assertEqual(st.row_metrics("13.4", "0", "0.1")["status"], "nonpositive")
        self.assertEqual(st.row_metrics("13.4", "10", "0.000")["status"], "nonpositive")
        self.assertEqual(st.row_metrics("13.4", "10", "0.0")["status"], "nonpositive")
        self.assertEqual(st.row_metrics("13.4", "10", "1e-3")["status"], "unparsed")


class TestDecisions(unittest.TestCase):
    def test_p1(self):
        self.assertEqual(st.decide_p1(999, 999), "underpowered")
        self.assertEqual(st.decide_p1(1000, 500), "holds")
        self.assertEqual(st.decide_p1(1000, 499), "fails")
        self.assertEqual(st.decide_p1(1001, 501), "holds")
        self.assertEqual(st.decide_p1(1001, 500), "fails")

    def test_p2(self):
        self.assertEqual(st.decide_p2(99, 99), "underpowered")
        self.assertEqual(st.decide_p2(100, 60), "holds")
        self.assertEqual(st.decide_p2(100, 59), "fails")
        self.assertEqual(st.decide_p2(101, 61), "holds")
        self.assertEqual(st.decide_p2(101, 60), "fails")

    def test_p3(self):
        bright = [0] * 100
        self.assertEqual(st.decide_p3([1000] * 99, bright), "underpowered")
        self.assertEqual(st.decide_p3([1000] * 100, bright[:99]), "underpowered")
        self.assertEqual(st.decide_p3([1000] * 100, bright), "holds")
        self.assertEqual(st.decide_p3([999] * 100, bright), "fails")
        # lower median of 100 values is the 50th smallest
        self.assertEqual(st.decide_p3([0] * 50 + [5000] * 50, bright), "fails")
        self.assertEqual(st.decide_p3([0] * 49 + [5000] * 51, bright), "holds")

    def test_lower_median_and_quantiles(self):
        self.assertEqual(st.lower_median([4, 1, 3, 2]), 2)
        self.assertEqual(st.lower_median([3, 1, 2]), 2)
        self.assertIsNone(st.lower_median([]))
        q = st.quantiles_e4(list(range(1, 101)))
        self.assertEqual(q, {"5": 5, "25": 25, "50": 50, "75": 75, "95": 95})


class TestAnalyse(unittest.TestCase):
    def test_excludes_probe_rows_and_counts(self):
        rows = [{"spkid": "20000001", "H": "3.34", "diameter": "939.4", "albedo": "0.090"},
                {"spkid": "20000010", "H": "13.12", "diameter": "10.000", "albedo": "0.100", "neo": "N"},
                {"spkid": "20000011", "H": "13.40", "diameter": "10.000", "albedo": "0.100", "neo": "N"},
                {"spkid": "20000012", "H": None, "diameter": "10.000", "albedo": "0.100"}]
        scored, status, dec, desc = st.analyse(rows)
        self.assertEqual(status, {"excluded_probe": 1, "ok": 2, "missing": 1})
        self.assertEqual(dec["P1"]["n_scored"], 2)
        self.assertEqual(dec["P1"]["n_shifted"], 1)
        self.assertEqual(dec["P2"]["n_positive"], 1)
        self.assertEqual(dec["P1"]["decision"], "underpowered")
        self.assertEqual(desc["H 12-14"]["n"], 2)
        self.assertEqual(desc["all"]["shifted"], 1)

    def test_h_bin_labels(self):
        self.assertEqual(st.h_bin(3.3), "<10")
        self.assertEqual(st.h_bin(10.0), "10-12")
        self.assertEqual(st.h_bin(14.0), "14-16")
        self.assertEqual(st.h_bin(18.0), ">=18")


class TestGate(unittest.TestCase):
    def test_gate(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "note.md")
            self.assertFalse(st.check_gate(p))
            with open(p, "w", encoding="utf-8") as f:
                f.write("# SBDB triplet pre-registration (P1-P3)\n")
            self.assertTrue(st.check_gate(p))
            with open(p, "w", encoding="utf-8") as f:
                f.write("# something else\n")
            self.assertFalse(st.check_gate(p))

    def test_main_refuses_without_gate(self):
        with tempfile.TemporaryDirectory() as d:
            rc = st.main(["--gate-note", os.path.join(d, "missing.md"), "--out-dir", os.path.join(d, "out")])
            self.assertEqual(rc, 2)
            with open(os.path.join(d, "out", "summary.json")) as f:
                self.assertFalse(json.load(f)["gate"])


if __name__ == "__main__":
    unittest.main()
