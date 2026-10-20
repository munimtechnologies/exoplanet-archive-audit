# Apache-2.0. Tests for sbdb_mixed 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import os
import tempfile
import unittest

import sbdb_mixed as sm

# Reference strings in the format the single-object SBDB API serves (made-up rows, format as seen in sbdb_source).
REF_A = ("urn:nasa:pds:neowise_diameters_albedos::2.0[mainbelt] "
         "(http://adsabs.harvard.edu/abs/2011ApJ...741...68M)")
REF_B = ("urn:nasa:pds:neowise_diameters_albedos::2.0[mainbelt] "
         "(http://adsabs.harvard.edu/abs/2012ApJ...759L...8M)")
REF_IRAS = "IRAS-A-FPA-3-RDR-IMPS-V6.0"


class TestParsing(unittest.TestCase):
    def test_bibcode(self):
        self.assertEqual(sm.bibcode(REF_A), "2011ApJ...741...68M")
        self.assertEqual(sm.bibcode(REF_B), "2012ApJ...759L...8M")
        self.assertIsNone(sm.bibcode(REF_IRAS))
        self.assertIsNone(sm.bibcode(""))
        self.assertIsNone(sm.bibcode(None))

    def test_ref_year_fixed(self):
        self.assertEqual(sm.ref_year("E2026L10"), 2026)
        self.assertEqual(sm.ref_year("E2026-EA1"), 2026)
        self.assertEqual(sm.ref_year(REF_B), 2012)
        self.assertIsNone(sm.ref_year("MPO190119"))  # sbdb_source 0.1.0 read this as 1901
        self.assertIsNone(sm.ref_year("MPO964292"))
        self.assertIsNone(sm.ref_year(REF_IRAS))
        self.assertIsNone(sm.ref_year(None))


def rec(status="fetched", d_ref=REF_A, p_ref=REF_A, dh=1000):
    r = {"status": status, "d_class": sm.ss.source_class(d_ref) if status == "fetched" else "",
         "d_ref": d_ref, "p_ref": p_ref, "dh_e4": dh, "h_ref_year": 2026,
         "diameter": "10.000", "albedo": "0.100", "detail_diameter": "10.000", "detail_albedo": "0.100",
         "d_bib": sm.bibcode(d_ref), "p_bib": sm.bibcode(p_ref)}
    r["group"] = sm.group(r)
    return r


class TestGroup(unittest.TestCase):
    def test_group(self):
        self.assertEqual(rec().get("group"), "same")
        self.assertEqual(rec(p_ref=REF_B)["group"], "mixed")
        self.assertEqual(rec(p_ref=None)["group"], "other")
        self.assertEqual(rec(p_ref=REF_IRAS)["group"], "other")
        self.assertEqual(rec(d_ref=REF_IRAS, p_ref=REF_IRAS)["group"], "other")
        self.assertEqual(rec(status="fetch_error", d_ref=None, p_ref=None)["group"], "other")


class TestDecisions(unittest.TestCase):
    def test_m1(self):
        self.assertEqual(sm.decide_m1(2999, 60), "underpowered")
        self.assertEqual(sm.decide_m1(3000, 30), "holds")     # 3000 <= 3000
        self.assertEqual(sm.decide_m1(3000, 29), "fails")     # 2900 < 3000
        self.assertEqual(sm.decide_m1(3000, 150), "holds")    # 15000 <= 15000
        self.assertEqual(sm.decide_m1(3000, 151), "fails")    # 15100 > 15000

    def test_m2(self):
        self.assertEqual(sm.decide_m2(40, 49, 0, 100), "underpowered")
        self.assertEqual(sm.decide_m2(40, 60, 0, 49), "underpowered")
        # shares 21/60 = 0.35 and 10/100 = 0.10: difference exactly 0.25 -> 4*(2100-600) = 6000 >= 6000
        self.assertEqual(sm.decide_m2(21, 60, 10, 100), "holds")
        # 20/60 - 10/100 = 0.233: 4*(2000-600) = 5600 < 6000
        self.assertEqual(sm.decide_m2(20, 60, 10, 100), "fails")
        # mixed share below same share
        self.assertEqual(sm.decide_m2(0, 60, 50, 100), "fails")


class TestScore(unittest.TestCase):
    def test_score_counts(self):
        records = [rec(dh=-5), rec(dh=7000), rec(dh=2000),
                   rec(p_ref=REF_B, dh=-6000), rec(p_ref=REF_B, dh=300),
                   rec(d_ref=REF_IRAS, p_ref=REF_IRAS, dh=-100),
                   rec(status="fetch_error", d_ref=None, p_ref=None, dh=0)]
        dec, desc = sm.score(records)
        self.assertEqual(dec["M1"]["n_neowise"], 5)
        self.assertEqual(dec["M1"]["n_mixed"], 2)
        self.assertEqual(dec["M1"]["decision"], "underpowered")
        self.assertEqual(dec["M2"]["n_same"], 3)
        self.assertEqual(dec["M2"]["neg_same"], 1)
        self.assertEqual(dec["M2"]["n_mixed"], 2)
        self.assertEqual(dec["M2"]["neg_mixed"], 1)
        self.assertEqual(dec["M2"]["decision"], "underpowered")
        self.assertEqual(desc["status"], {"fetched": 6, "fetch_error": 1})
        self.assertEqual(desc["group"], {"same": 3, "mixed": 2, "other": 2})
        self.assertEqual(desc["mixed_pairs"], {"2011ApJ...741...68M -> 2012ApJ...759L...8M": 2})
        self.assertEqual(desc["by_group_abs_dh_over_0p5mag"], {"mixed": 1, "other": 0, "same": 1})
        self.assertEqual(desc["by_group_dh_quantiles_e4"]["same"]["50"], 2000)
        self.assertEqual(desc["h_ref_year"], {"2026": 6})
        self.assertEqual(desc["detail_value_mismatch"], 0)

    def test_record_overrides_ref_year(self):
        # made-up fixture row, not taken from any output file
        row = {"spkid": "20999999", "pdes": "fixture", "H": "12.00", "diameter": "10.000", "albedo": "0.100"}
        m = {"dh_e4": 1234, "tol_e4": 200, "shifted": True}
        refs = {"H": ("12.00", "MPO190119"), "diameter": ("10.000", REF_B), "albedo": ("0.100", REF_A)}
        r = sm.record(row, m, "fetched", refs)
        self.assertIsNone(r["h_ref_year"])
        self.assertEqual(r["d_bib"], "2012ApJ...759L...8M")
        self.assertEqual(r["p_bib"], "2011ApJ...741...68M")
        self.assertEqual(r["group"], "mixed")
        self.assertEqual(sorted(r), sorted(sm.OUT_HEADER))


class TestGate(unittest.TestCase):
    def test_main_refuses_without_gate(self):
        with tempfile.TemporaryDirectory() as d:
            seen = os.path.join(d, "seen.csv")
            with open(seen, "w", encoding="utf-8") as f:
                f.write("spkid\n20000010\n")
            rc = sm.main(["--gate-note", os.path.join(d, "missing.md"), "--seen", seen,
                          "--out-dir", os.path.join(d, "out")])
            self.assertEqual(rc, 2)
            with open(os.path.join(d, "out", "summary.json")) as f:
                s = json.load(f)
            self.assertFalse(s["gate"])
            self.assertEqual(s["seen_rows"], 1)

    def test_main_refuses_wrong_seen_count(self):
        with tempfile.TemporaryDirectory() as d:
            note = os.path.join(d, "note.md")
            with open(note, "w", encoding="utf-8") as f:
                f.write("# SBDB mixed-reference pre-registration (M1-M2)\n")
            seen = os.path.join(d, "seen.csv")
            with open(seen, "w", encoding="utf-8") as f:
                f.write("spkid\n20000010\n")
            rc = sm.main(["--gate-note", note, "--seen", seen, "--out-dir", os.path.join(d, "out")])
            self.assertEqual(rc, 2)
            with open(os.path.join(d, "out", "summary.json")) as f:
                self.assertTrue(json.load(f)["gate"])


if __name__ == "__main__":
    unittest.main()
