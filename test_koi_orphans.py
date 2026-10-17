"""Tests for koi_orphans. Expected values are worked out by hand from Exoplanet Archive rows (2026-10-17).
Apache-2.0. Munim, Inc. (MV2 of Munim, Inc.). Made with AI."""
import csv
import io
import json
import os
import random
import tempfile
import unittest
from contextlib import redirect_stdout

import koi_orphans as ko

# DR25 TCE rows (q1_q17_dr25_tce) on KIC 6041734 (Kepler-1129), 9411166 (Kepler-1016), 3245969 (Kepler-768)
TCE_1129_1 = (24.3395604109332, 136.064226829553, 3.74289132310602)
TCE_1129_2 = (76.5357819793002, 164.174137531446, 6.38738709583979)
TCE_1016_1 = (1.95450587819908, 132.302812157451, 2.16932720493733)
TCE_1016_2 = (105.654585975035, 230.104555360967, 9.30408594520766)
TCE_768_1 = (11.3910578906768, 137.702418233469, 2.75258195203890)
# cumulative rows (Q1-Q16 parameters): period, time0bk, duration (h)
K02167_02 = (6.95787, 359.007, 4.537)
K01922_02 = (15.09521323, 139.474359, 3.41)
K01101_02 = (11.39110963, 137.69665, 2.749)

KOI_FIELDS = ["kepid", "kepoi_name", "kepler_name", "koi_disposition", "koi_parm_prov", "koi_tce_delivname",
              "koi_tce_plnt_num", "koi_period", "koi_time0bk", "koi_duration", "koi_depth", "koi_model_snr"]
TCE_FIELDS = ["kepid", "tce_plnt_num", "tce_period", "tce_time0bk", "tce_duration", "tce_depth", "tce_model_snr",
              "tce_rogue_flag"]


def koi(kepid, name, disp, prov, p, t, d, plnt="", kepler_name="", deliv=""):
    return {"kepid": kepid, "kepoi_name": name, "kepler_name": kepler_name, "koi_disposition": disp,
            "koi_parm_prov": prov, "koi_tce_delivname": deliv, "koi_tce_plnt_num": plnt, "koi_period": str(p),
            "koi_time0bk": str(t), "koi_duration": str(d), "koi_depth": "100", "koi_model_snr": "10"}


def tce(kepid, n, ptd):
    return {"kepid": kepid, "tce_plnt_num": str(n), "tce_period": repr(ptd[0]), "tce_time0bk": repr(ptd[1]),
            "tce_duration": repr(ptd[2]), "tce_depth": "500", "tce_model_snr": "20", "tce_rogue_flag": "0"}


def sample():
    q16, dr25, cand = "q1_q16_koi", "q1_q17_dr25_koi", "CANDIDATE"
    kois = [
        koi("6041734", "K02167.02", cand, q16, *K02167_02),
        koi("6041734", "K02167.03", "CONFIRMED", dr25, 76.5369531, TCE_1129_2[1] + 0.01, 6.4, plnt="2.0",
            kepler_name="Kepler-1129 c", deliv="q1_q17_dr25_tce"),
        koi("9411166", "K01922.02", cand, q16, *K01922_02),
        koi("3245969", "K01101.02", cand, "q1_q17_dr24_koi", *K01101_02),  # really Q1-Q16; DR24 covers that path
        koi("3245969", "K01101.01", cand, dr25, TCE_768_1[0], TCE_768_1[1], 2.75, plnt="1",
            kepler_name="Kepler-768 b", deliv="q1_q17_dr25_tce"),
        koi("1000001", "K09001.01", cand, q16, 10.0, 140.0, 3.0),  # star with no DR25 TCE
        koi("9411166", "K09002.01", "FALSE POSITIVE", q16, 15.09521323, 139.474359, 3.41),  # not a CANDIDATE
        koi("1000002", "K09003.01", cand, q16, 10.0, 140.0, 3.0),  # TCE on star, not commensurate
    ]
    tces = [tce("6041734", 1, TCE_1129_1), tce("6041734", 2, TCE_1129_2), tce("9411166", 1, TCE_1016_1),
            tce("9411166", 2, TCE_1016_2), tce("3245969", 1, TCE_768_1), tce("1000002", 1, (13.7, 150.0, 3.0))]
    return kois, tces


class TestMath(unittest.TestCase):
    def test_fraction_count(self):
        # coprime pairs in 1..12: 2 * (sum of phi(1..12) = 46) - 1
        self.assertEqual(len(ko.FRACTIONS), 91)

    def test_fold(self):
        self.assertAlmostEqual(ko.fold(7.0, 5.0), 2.0)
        self.assertAlmostEqual(ko.fold(-3.0, 5.0), 2.0)
        self.assertAlmostEqual(ko.fold(2.5, 5.0), -2.5)

    def test_kind(self):
        self.assertEqual(ko.kind_of(1, 1), "same")
        self.assertEqual(ko.kind_of(1, 7), "integer")
        self.assertEqual(ko.kind_of(7, 1), "integer")
        self.assertEqual(ko.kind_of(3, 2), "rational")

    def test_ratio_rational(self):
        self.assertEqual(ko.ratio_match(3.0, 2.0), (3, 2, 0.0))
        self.assertIsNone(ko.ratio_match(0, 2.0))

    def test_k02167_02_is_one_eleventh(self):
        a, b, drift = ko.ratio_match(K02167_02[0], TCE_1129_2[0])
        self.assertEqual((a, b), (1, 11))
        self.assertAlmostEqual(drift, 0.015032, places=4)  # 0.000788 d * 1460 / 76.53657
        r = ko.pair_test(*K02167_02, *TCE_1129_2)
        self.assertEqual((r["kind"], r["status"]), ("integer", "same_events"))
        self.assertAlmostEqual(r["off_d"], 0.0125025, places=5)  # 194.832862 - 28 * 6.95787
        self.assertAlmostEqual(r["window_d"], 0.4551828, places=5)
        self.assertAlmostEqual(r["p_phase"], 0.13084, places=4)

    def test_k02167_02_vs_inner_planet_not_commensurate(self):
        # nearest is 2/7 with drift 0.0259692 * 1460 / 48.70509 = 0.78 d > 0.5 d
        self.assertIsNone(ko.ratio_match(K02167_02[0], TCE_1129_1[0]))

    def test_k01922_02_is_one_seventh(self):
        r = ko.pair_test(*K01922_02, *TCE_1016_2)
        self.assertEqual((r["a"], r["b"], r["status"]), (1, 7, "same_events"))
        self.assertAlmostEqual(r["drift_d"], 0.164515, places=4)
        self.assertAlmostEqual(r["off_d"], -0.058917, places=5)
        self.assertAlmostEqual(r["window_d"], 0.5297536, places=5)
        self.assertIsNone(ko.pair_test(*K01922_02, *TCE_1016_1))  # 7.723: no a/b with a, b <= 12

    def test_k01101_02_same_as_tce(self):
        r = ko.pair_test(*K01101_02, *TCE_768_1)
        self.assertEqual((r["kind"], r["status"]), ("same", "same_events"))
        self.assertAlmostEqual(r["drift_d"], 0.0066314, places=5)
        self.assertAlmostEqual(r["off_d"], -0.0057682, places=6)

    def test_offset_status(self):
        r = ko.pair_test(10.0, 143.0, 2.4, 10.0, 140.0, 2.4)
        self.assertEqual((r["status"], r["kind"]), ("offset", "same"))
        self.assertAlmostEqual(r["off_d"], 3.0)
        self.assertAlmostEqual(r["p_phase"], 0.04)

    def test_rank(self):
        a = {"status": "offset", "kind": "same", "off_d": 0.0}
        b = {"status": "same_events", "kind": "rational", "off_d": 0.1}
        c = {"status": "same_events", "kind": "integer", "off_d": 0.3}
        self.assertEqual(sorted([a, b, c], key=ko.rank), [c, b, a])


class TestScan(unittest.TestCase):
    def setUp(self):
        self.kois, self.tces = sample()
        self.fed = ko.federation(self.kois)
        self.by_star = ko.tces_by_star(self.tces, self.fed)
        self.orphans = ko.orphans_of(self.kois, ("CANDIDATE",))

    def test_federation(self):
        self.assertEqual(self.fed[("6041734", "2")]["kepoi_name"], "K02167.03")
        self.assertEqual(self.fed[("3245969", "1")]["kepoi_name"], "K01101.01")
        self.assertEqual(len(self.fed), 2)

    def test_orphans(self):
        self.assertEqual(sorted(o["kepoi_name"] for o in self.orphans),
                         ["K01101.02", "K01922.02", "K02167.02", "K09001.01", "K09003.01"])

    def test_scan(self):
        pairs, per = ko.scan(self.orphans, self.by_star)
        by = {r["kepoi_name"]: r for r in per}
        self.assertEqual((by["K02167.02"]["status"], by["K02167.02"]["b"]), ("same_events", 11))
        self.assertEqual((by["K02167.02"]["tce_koi"], by["K02167.02"]["tce_koi_disp"]), ("K02167.03", "CONFIRMED"))
        self.assertEqual((by["K01922.02"]["status"], by["K01922.02"]["b"], by["K01922.02"]["tce_koi"]),
                         ("same_events", 7, ""))
        self.assertEqual((by["K01101.02"]["kind"], by["K01101.02"]["tce_koi"]), ("same", "K01101.01"))
        self.assertEqual(by["K09001.01"]["status"], "no_tce")
        self.assertEqual(by["K09003.01"]["status"], "unrelated")
        self.assertEqual(by["K02167.02"]["n_tce"], 2)
        self.assertEqual(len(pairs), 3)
        t = ko.tally(per)
        self.assertEqual((t["same_events"], t["same_events_same"], t["same_events_integer"], t["no_tce"],
                          t["unrelated"]), (3, 1, 2, 1, 1))

    def test_no_params(self):
        o = ko.koi_entry(koi("6041734", "K09004.01", "CANDIDATE", "q1_q16_koi", 6.95787, 359.007, ""))
        self.assertIsNone(o["dur"])
        self.assertEqual(ko.scan([o], self.by_star)[1][0]["status"], "no_params")

    def test_derangement(self):
        rng = random.Random(1)
        for _ in range(20):
            d = ko.derangement(["a", "b", "c", "d", "e"], rng)
            self.assertEqual(sorted(d.values()), ["a", "b", "c", "d", "e"])
            self.assertTrue(all(k != v for k, v in d.items()))
        self.assertEqual(ko.derangement(["a"], rng), {})

    def test_null_breaks_links(self):
        mean, runs = ko.null_tallies(self.orphans, self.by_star, n=10)
        self.assertEqual(len(runs), 10)
        self.assertEqual(mean["same_events"], 0.0)

    def test_control(self):
        counts, misses = ko.control(self.kois, self.by_star, ("CANDIDATE", "CONFIRMED"))
        self.assertEqual(counts["tested"], 2)
        self.assertEqual(counts["same_events_same"], 2)
        self.assertEqual(misses, [])


class TestMain(unittest.TestCase):
    def test_end_to_end(self):
        kois, tces = sample()
        with tempfile.TemporaryDirectory() as d:
            kp, tp = os.path.join(d, "k.csv"), os.path.join(d, "t.csv")
            for path, fields, rows in ((kp, KOI_FIELDS, kois), (tp, TCE_FIELDS, tces)):
                with open(path, "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=fields)
                    w.writeheader()
                    w.writerows(rows)
            out = os.path.join(d, "out")
            with redirect_stdout(io.StringIO()):
                ko.main(["--out-dir", out, "--koi-csv", kp, "--tce-csv", tp])
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual((s["orphans"], s["orphans_with_tce"], s["orphan_tce_pairs"]), (5, 4, 6))
            self.assertEqual(s["orphans_by_prov"], {"q1_q16_koi": 4, "q1_q17_dr24_koi": 1})
            self.assertEqual(s["counts"]["same_events"], 3)
            self.assertEqual(s["control"]["tested"], 1)  # K01101.01; K02167.03 is CONFIRMED
            with open(os.path.join(out, "orphans.csv"), encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows[0]["status"], "same_events")
            self.assertEqual(rows[-1]["status"], "no_tce")


if __name__ == "__main__":
    unittest.main()
