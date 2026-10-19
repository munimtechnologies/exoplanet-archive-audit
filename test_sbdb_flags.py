# Apache-2.0. Tests for sbdb_flags 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import os
import tempfile
import unittest
from decimal import Decimal

import sbdb_flags as sf


def pv(s):
    return sf.parse_value(s)


def row(spkid, cls, neo, pha, h, moid, q, a, e, ad):
    return {"spkid": spkid, "pdes": "x" + spkid, "class": cls, "neo": neo, "pha": pha, "H": h, "moid": moid,
            "q": q, "a": a, "e": e, "ad": ad}


class TestParse(unittest.TestCase):
    def test_parse_value(self):
        self.assertEqual(sf.parse_value("0.090"), (Decimal("0.090"), Decimal("0.0005")))
        self.assertEqual(sf.parse_value("939"), (Decimal("939"), Decimal("0.5")))
        self.assertEqual(sf.parse_value(" 1.2e-05 "), (Decimal("0.000012"), Decimal("0.0000005")))
        self.assertEqual(sf.parse_value("22.0", exact=True), (Decimal("22"), Decimal(0)))
        for bad in (None, "", "abc", "nan", "inf"):
            self.assertIsNone(sf.parse_value(bad))

    def test_page_url(self):
        u = sf.page_url(40000)
        self.assertIn("limit-from=40000", u)
        self.assertIn("limit=20000", u)
        self.assertIn("sort=spkid", u)
        self.assertIn("sb-kind=a", u)
        self.assertIn("pha", u)

    def test_parse_page_keeps_strings(self):
        body = json.dumps({"count": 1, "fields": ["spkid", "neo", "moid"],
                           "data": [[20000433, "Y", "0.149"]]}).encode()
        count, fields, rows = sf.parse_page(body)
        self.assertEqual(count, 1)
        self.assertEqual(rows[0], {"spkid": "20000433", "neo": "Y", "moid": "0.149"})


class TestThreeValued(unittest.TestCase):
    def test_lt(self):
        self.assertIs(sf.lt(pv("1.2999"), sf.NEO_Q), True)
        self.assertIsNone(sf.lt(pv("1.3"), sf.NEO_Q))
        self.assertIsNone(sf.lt(pv("1.3000"), sf.NEO_Q))
        self.assertIs(sf.lt(pv("1.30001"), sf.NEO_Q), False)

    def test_le_and_gt(self):
        self.assertIsNone(sf.le(pv("0.0500"), sf.PHA_MOID))
        self.assertIs(sf.le(pv("0.04994"), sf.PHA_MOID), True)
        self.assertIs(sf.le(sf.parse_value("22.0", exact=True), sf.PHA_H), True)
        self.assertIs(sf.le(sf.parse_value("22.01", exact=True), sf.PHA_H), False)
        self.assertIs(sf.gt(pv("1.0171"), Decimal("1.017")), True)
        self.assertIsNone(sf.gt(pv("1.017"), Decimal("1.017")))
        self.assertIs(sf.gt(pv("1.016"), Decimal("1.017")), False)

    def test_all3(self):
        self.assertIs(sf.all3(True, True), True)
        self.assertIs(sf.all3(None, False), False)
        self.assertIsNone(sf.all3(None, True))

    def test_pha_rule_and_reason(self):
        h = lambda s: sf.parse_value(s, exact=True)
        self.assertIs(sf.pha_rule(pv("0.0123"), h("21.9")), True)
        self.assertIs(sf.pha_rule(pv("0.0123"), h("22.4")), False)
        self.assertIs(sf.pha_rule(pv("0.0500"), h("23.0")), False)
        self.assertIsNone(sf.pha_rule(pv("0.0500"), h("21.0")))
        self.assertEqual(sf.pha_reason(pv("0.0123"), h("22.4")), "H>22")
        self.assertEqual(sf.pha_reason(pv("0.3"), h("23.0")), "H>22+moid>0.05")
        self.assertEqual(sf.pha_reason(pv("0.0123"), h("20.0")), "both_met")


class TestClass(unittest.TestCase):
    def check(self, served, a, e, q, ad):
        return sf.class_check(served, pv(a), pv(e), pv(q), pv(ad))

    def test_main_belt(self):
        self.assertEqual(self.check("MBA", "2.77", "0.0789", "2.55", "2.99"), ("consistent", ("MBA",)))
        self.assertEqual(self.check("OMB", "2.77", "0.0789", "2.55", "2.99"), ("inconsistent", ("MBA",)))

    def test_overlapping_definitions(self):
        self.assertEqual(self.check("APO", "3.5", "0.75", "0.875", "6.125"), ("consistent", ("APO", "OMB")))
        self.assertEqual(self.check("AST", "3.5", "0.75", "0.875", "6.125"), ("inconsistent", ("APO", "OMB")))

    def test_ast_when_nothing_matches(self):
        self.assertEqual(self.check("AST", "5.0", "0.5", "2.5", "7.5"), ("consistent", ()))
        self.assertEqual(self.check("TJN", "5.0", "0.5", "2.5", "7.5"), ("inconsistent", ()))

    def test_boundary_missing_unbound(self):
        self.assertEqual(self.check("ATE", "1.0", "0.2", "0.8", "1.2"), ("boundary", ()))
        self.assertEqual(sf.class_check("MBA", pv("2.77"), None, pv("2.55"), pv("2.99")), ("missing", ()))
        self.assertEqual(sf.class_check("MBA", pv("2.77"), pv("0.0789"), pv("2.55"), None), ("missing", ()))
        self.assertEqual(sf.class_check("", pv("2.77"), pv("0.0789"), pv("2.55"), pv("2.99")), ("missing", ()))
        self.assertEqual(sf.class_check("HYA", pv("-1.3"), pv("1.2"), pv("0.26"), None), ("consistent", ("HYA",)))
        self.assertEqual(sf.class_check("PAA", None, pv("1"), pv("2.1"), None), ("consistent", ("PAA",)))


class TestTally(unittest.TestCase):
    def setUp(self):
        t = sf.Tally(seen={20000001})
        for r in [
            row("2000001", "MBA", "N", "N", "3.34", "1.58", "2.55", "2.77", "0.0789", "2.99"),
            row("3000001", "APO", "Y", "Y", "20.5", "0.0123", "0.875", "3.5", "0.75", "6.125"),
            row("3000002", "APO", "Y", "Y", "22.4", "0.0123", "0.875", "3.5", "0.75", "6.125"),
            row("3000003", "AMO", "N", "N", "18.0", "0.2", "1.2", "2.5", "0.52", "3.8"),
            row("20000001", "MBA", "N", "N", "3.34", "1.58", "2.55", "2.77", "0.0789", "2.99"),
            row("3000004", "AMO", "Y", "N", "19.0", "0.3", "1.3", "2.5", "0.48", "3.7"),
            row("3000005", "OMB", "N", "N", "15.0", "1.0", "2.55", "2.77", "0.0789", "2.99"),
            row("3000006", "MBA", "N", None, "16", None, "2.55", "2.77", "0.0789", "2.99"),
        ]:
            t.add(r)
        self.t = t

    def test_counts(self):
        c = self.t.counts
        self.assertEqual(c["rows"], 7)
        self.assertEqual(c["excluded_seen"], 1)
        self.assertEqual((c["neo agree"], c["neo mismatch"], c["neo boundary"]), (5, 1, 1))
        self.assertEqual((c["pha_all agree"], c["pha_all mismatch"], c["pha_all flag_other"]), (5, 1, 1))
        self.assertEqual((c["pha_neo agree"], c["pha_neo mismatch"]), (2, 1))
        self.assertEqual((c["class consistent"], c["class inconsistent"], c["class boundary"]), (5, 1, 1))
        self.assertEqual(c["neo_confusion flag=N rule=N"], 3)
        self.assertEqual(c["neo_confusion flag=Y rule=Y"], 2)
        self.assertEqual(c["neo_confusion flag=N rule=Y"], 1)
        self.assertEqual(c["pha_reason H>22"], 1)
        self.assertEqual(c["class_matrix APO -> APO+OMB"], 2)
        self.assertEqual(c["class_matrix OMB -> MBA"], 1)
        self.assertEqual(c["precision q -2"], 3)

    def test_mismatch_rows(self):
        m = self.t.mismatches
        self.assertEqual([r[1] for r in m["neo"]], ["3000003"])
        self.assertEqual(m["neo"][0][-2:], ["Y", "rule q<1.3"])
        self.assertEqual(m["pha"][0][:2], ["pha", "3000002"])
        self.assertEqual(m["pha"][0][-2:], ["N", "H>22"])
        self.assertEqual(m["class"][0][1], "3000005")
        self.assertEqual(m["class"][0][-2], "MBA")
        self.assertEqual(len(sf.MISMATCH_HEADER), len(m["pha"][0]))

    def test_decisions_underpowered(self):
        d = sf.decisions(self.t)
        self.assertEqual(d["F1"], {"n_decidable": 6, "n_mismatch": 1, "decision": "underpowered"})
        self.assertEqual(d["F2"], {"n_decidable": 3, "n_mismatch": 1, "decision": "underpowered"})
        self.assertEqual(d["F3"], {"n_decidable": 6, "n_inconsistent": 1, "decision": "underpowered"})


class TestDecisions(unittest.TestCase):
    def test_f1_f3(self):
        for f in (sf.decide_f1, sf.decide_f3):
            self.assertEqual(f(99999, 0), "underpowered")
            self.assertEqual(f(100000, 10), "holds")
            self.assertEqual(f(100000, 11), "fails")

    def test_f2(self):
        self.assertEqual(sf.decide_f2(9999, 0), "underpowered")
        self.assertEqual(sf.decide_f2(10000, 10), "holds")
        self.assertEqual(sf.decide_f2(10000, 11), "fails")


class TestGate(unittest.TestCase):
    def test_gate(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "note.md")
            self.assertFalse(sf.check_gate(p))
            with open(p, "w", encoding="utf-8") as f:
                f.write("# SBDB flag-consistency pre-registration (F1-F3)\n")
            self.assertTrue(sf.check_gate(p))

    def test_main_refuses_without_gate_or_seen(self):
        with tempfile.TemporaryDirectory() as d:
            note = os.path.join(d, "note.md")
            with open(note, "w", encoding="utf-8") as f:
                f.write("SBDB flag-consistency pre-registration\n")
            seen = os.path.join(d, "seen.csv")
            with open(seen, "w", encoding="utf-8") as f:
                f.write("spkid,pdes\n20000004,4\n")
            out = os.path.join(d, "out")
            self.assertEqual(sf.main(["--gate-note", os.path.join(d, "missing.md"), "--seen", seen,
                                      "--out-dir", out]), 2)
            with open(os.path.join(out, "summary.json")) as f:
                self.assertFalse(json.load(f)["gate"])
            self.assertEqual(sf.main(["--gate-note", note, "--seen", seen, "--out-dir", out]), 2)
            with open(os.path.join(out, "summary.json")) as f:
                s = json.load(f)
            self.assertTrue(s["gate"])
            self.assertEqual(s["seen_rows"], 1)


if __name__ == "__main__":
    unittest.main()
