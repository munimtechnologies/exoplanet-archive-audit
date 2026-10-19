# Apache-2.0. Tests for sbdb_source 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
import json
import os
import tempfile
import unittest

import sbdb_source as ss

NEOWISE_REF = ("urn:nasa:pds:neowise_diameters_albedos::2.0[mainbelt] "
               "(http://adsabs.harvard.edu/abs/2014ApJ...791..121M)")


def payload(pars):
    return json.dumps({"signature": {"version": "1.3"}, "object": {"spkid": "20001544"},
                       "phys_par": pars}).encode()


class TestClassify(unittest.TestCase):
    def test_source_class(self):
        self.assertEqual(ss.source_class(NEOWISE_REF), "neowise")
        self.assertEqual(ss.source_class("Masiero et al. (2011) WISE"), "neowise")
        self.assertEqual(ss.source_class("Usui et al. (2011)"), "akari")
        self.assertEqual(ss.source_class("AKARI AcuA"), "akari")
        self.assertEqual(ss.source_class("Tedesco et al. (2004) SIMPS"), "iras")
        self.assertEqual(ss.source_class("IRAS"), "iras")
        self.assertEqual(ss.source_class("radar (Ostro)"), "other")
        self.assertEqual(ss.source_class(""), "none")
        self.assertEqual(ss.source_class(None), "none")

    def test_ref_year(self):
        self.assertEqual(ss.ref_year("E2026E71"), 2026)
        self.assertEqual(ss.ref_year(NEOWISE_REF), 2014)
        self.assertIsNone(ss.ref_year("MPO123456"))
        self.assertIsNone(ss.ref_year(None))
        self.assertIsNone(ss.ref_year("120145"))

    def test_detail_url(self):
        self.assertEqual(ss.detail_url("20001544"), "https://ssd-api.jpl.nasa.gov/sbdb.api?spk=20001544&phys-par=1")


class TestPayload(unittest.TestCase):
    def test_phys_refs(self):
        body = payload([{"name": "H", "value": "11.94", "ref": "E2026E71"},
                        {"name": "diameter", "value": "24.561", "ref": NEOWISE_REF},
                        {"name": "rot_per", "value": "13.536", "ref": "LCDB"},
                        {"name": "albedo", "value": "0.058", "ref": NEOWISE_REF}])
        status, refs = ss.phys_refs(body)
        self.assertEqual(status, "fetched")
        self.assertEqual(refs["H"], ("11.94", "E2026E71"))
        self.assertEqual(refs["diameter"], ("24.561", NEOWISE_REF))
        self.assertEqual(sorted(refs), ["H", "albedo", "diameter"])

    def test_bad_payloads(self):
        self.assertEqual(ss.phys_refs(b"not json")[0], "bad_json")
        self.assertEqual(ss.phys_refs(json.dumps({"message": "specified object was not found"}).encode())[0],
                         "no_phys_par")
        self.assertEqual(ss.phys_refs(payload([{"name": "H", "value": "11.94", "ref": "E2026E71"}]))[0],
                         "no_diameter")


class TestDecisions(unittest.TestCase):
    def test_s1(self):
        self.assertEqual(ss.decide_s1(999, 999), "underpowered")
        self.assertEqual(ss.decide_s1(1000, 800), "holds")
        self.assertEqual(ss.decide_s1(1000, 799), "fails")
        self.assertEqual(ss.decide_s1(1001, 801), "holds")   # 8010 >= 8008
        self.assertEqual(ss.decide_s1(1001, 800), "fails")   # 8000 < 8008

    def test_s2(self):
        self.assertEqual(ss.decide_s2(999, 999), "underpowered")
        self.assertEqual(ss.decide_s2(1000, 950), "holds")
        self.assertEqual(ss.decide_s2(1000, 949), "fails")
        self.assertEqual(ss.decide_s2(1001, 951), "holds")   # 19020 >= 19019
        self.assertEqual(ss.decide_s2(1001, 950), "fails")   # 19000 < 19019

    def test_s3(self):
        self.assertEqual(ss.decide_s3([1000] * 29, [0] * 30), "underpowered")
        self.assertEqual(ss.decide_s3([1000] * 30, [0] * 29), "underpowered")
        self.assertEqual(ss.decide_s3([1000] * 30, [0] * 30), "holds")
        self.assertEqual(ss.decide_s3([999] * 30, [0] * 30), "fails")
        # lower median of 30 values is the 15th smallest
        self.assertEqual(ss.decide_s3([0] * 15 + [5000] * 15, [0] * 30), "fails")
        self.assertEqual(ss.decide_s3([0] * 14 + [5000] * 16, [0] * 30), "holds")


def rec(spkid, status, d_class, dh, d_ref="a", p_ref="a"):
    return {"spkid": spkid, "status": status, "d_class": d_class, "dh_e4": dh, "d_ref": d_ref, "p_ref": p_ref,
            "h_ref_year": 2026, "diameter": "1.000", "albedo": "0.100", "detail_diameter": "1.000",
            "detail_albedo": "0.100"}


class TestScore(unittest.TestCase):
    def test_score_counts(self):
        records = [rec(1, "fetched", "neowise", 3000), rec(2, "fetched", "neowise", 2000),
                   rec(3, "fetched", "akari", 100, p_ref="b"), rec(4, "fetched", "none", 0),
                   rec(5, "fetch_error", "", 50)]
        dec, desc = ss.score(records)
        self.assertEqual(dec["S1"]["n_fetched"], 4)
        self.assertEqual(dec["S1"]["n_neowise"], 2)
        self.assertEqual(dec["S1"]["decision"], "underpowered")
        self.assertEqual(dec["S2"]["n_same_ref"], 3)
        self.assertEqual(dec["S3"]["n_other_sources"], 1)
        self.assertEqual(dec["S3"]["median_neowise_e4"], 2000)
        self.assertEqual(desc["status"], {"fetched": 4, "fetch_error": 1})
        self.assertEqual(desc["d_class"], {"neowise": 2, "akari": 1, "none": 1})
        self.assertEqual(desc["detail_value_mismatch"], 0)


class TestSampling(unittest.TestCase):
    def test_load_seen_and_pool(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a.csv"), os.path.join(d, "b.csv")
            with open(a, "w", encoding="utf-8") as f:
                f.write("spkid,pdes\n20000010,10\n20000011,11\n")
            with open(b, "w", encoding="utf-8") as f:
                f.write("spkid,pdes\n20000012,12\n")
            seen = ss.load_seen([a, b])
        self.assertEqual(seen, {20000010, 20000011, 20000012})
        scored = [({"spkid": str(s)}, {"dh_e4": 0}) for s in (20000013, 20000010, 20000020, 20000012)]
        pool = ss.make_pool(scored, seen)
        self.assertEqual([r["spkid"] for r, _ in pool], ["20000013", "20000020"])

    def test_draw_sample_deterministic(self):
        pool = [({"spkid": str(i)}, {}) for i in range(100)]
        s1 = ss.draw_sample(pool, 10, seed=7)
        s2 = ss.draw_sample(pool, 10, seed=7)
        self.assertEqual(s1, s2)
        self.assertEqual(len(s1), 10)
        ids = [int(r["spkid"]) for r, _ in s1]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(ss.draw_sample(pool[:5], 10)), 5)


class TestGate(unittest.TestCase):
    def test_main_refuses_without_gate(self):
        with tempfile.TemporaryDirectory() as d:
            seen = os.path.join(d, "seen.csv")
            with open(seen, "w", encoding="utf-8") as f:
                f.write("spkid\n20000010\n")
            rc = ss.main(["--gate-note", os.path.join(d, "missing.md"), "--seen", seen,
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
                f.write("# SBDB diameter-source pre-registration (S1-S3)\n")
            seen = os.path.join(d, "seen.csv")
            with open(seen, "w", encoding="utf-8") as f:
                f.write("spkid\n20000010\n")
            rc = ss.main(["--gate-note", note, "--seen", seen, "--out-dir", os.path.join(d, "out")])
            self.assertEqual(rc, 2)
            with open(os.path.join(d, "out", "summary.json")) as f:
                self.assertTrue(json.load(f)["gate"])


if __name__ == "__main__":
    unittest.main()
