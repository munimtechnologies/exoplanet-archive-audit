"""Tests for shared_events. Expected values are worked out by hand from Exoplanet Archive rows (cumulative and
q1_q17_dr25_tce as fetched by koi_orphans 0.1.0 on 2026-10-17) and the DR25 Robovetter output.
Apache-2.0. Munim, Inc. (MV2 of Munim, Inc.). Made with AI."""
import csv
import io
import json
import os
import random
import tempfile
import unittest
from contextlib import redirect_stdout

import shared_events as se

# cumulative rows (Q1-Q16 parameters): period, time0bk, duration (h)
K01356_01 = (384.02570682, 335.816169, 14.56)
K01032_01 = (1500.1406772, 176.08226, 25.727)
K00099_01 = (2190.7010353, 140.04806, 19.891)
K00682_01 = (562.1725914, 185.968547, 9.8841)
K01421_01 = (1693.6636225, 524.27995, 22.604)
K01192_01 = (1295.362215, 176.10646, 28.297)
# DR25 TCE rows: period, time0bk, duration (h)
TCE_7363829_1 = (393.719, 335.817, 12.51)
TCE_2162635_1 = (293.805, 176.09, 25.12)
TCE_8505215_1 = (627.765, 140.063, 20.53)
TCE_7619236_1 = (563.276, 184.864, 9.926)  # rogue
TCE_7619236_2 = (472.466, 233.565, 24.63)
TCE_11342550_1 = (327.155, 197.119, 21.48)
TCE_3644071_1 = (359.047, 295.777, 32.21)
TCE_3644071_2 = (359.039, 274.227, 15.58)

ROBO = ("#1:TCE  2:Robovetter_Score  3:Disposition  4:Not_Transit-Like_Flag  5:Stellar_Eclipse_Flag\n"
        "000757450-01 0.999 PC 0 0 0 0 \n"
        "007363829-01 0.000 FP 1 0 0 0 INDIV_TRANS_MARSHALL_SKYE---INCONSISTENT_TRANS---CENT_FEW_DIFFS\n")
XMATCH = ("kepoi_name,kepid,kepler_name,archive_disposition,parm_prov,orphan,lissauer_status,lissauer_now,"
          "lissauer_dr25supp,archive_period,lissauer_period,period_ratio,ratio_fraction,ratio_fraction_err,"
          "archive_snr,lissauer_snr,kic_match\n"
          "K01356.01,7363829,,CANDIDATE,q1_q16_koi,True,PPNN,P,P,384.02570682,787.43235205,2.0504678152160376,"
          "2/1,0.025233907608018802,,83.9,True\n")
ORPHAN_FIELDS = ["kepoi_name", "kepid", "status"]
KOI_FIELDS = ["kepid", "kepoi_name", "koi_disposition", "koi_tce_delivname", "koi_tce_plnt_num", "koi_period",
              "koi_time0bk", "koi_duration"]
TCE_FIELDS = ["kepid", "tce_plnt_num", "tce_period", "tce_time0bk", "tce_duration", "tce_depth", "tce_model_snr",
              "tce_rogue_flag"]


def koi(kepid, name, ptd, disp="CANDIDATE", deliv="", n=""):
    return {"kepid": kepid, "kepoi_name": name, "koi_disposition": disp, "koi_tce_delivname": deliv,
            "koi_tce_plnt_num": n, "koi_period": repr(ptd[0]), "koi_time0bk": repr(ptd[1]),
            "koi_duration": "" if ptd[2] is None else repr(ptd[2])}


def tce(kepid, n, ptd, rogue="0"):
    return {"kepid": kepid, "tce_plnt_num": str(n), "tce_period": repr(ptd[0]), "tce_time0bk": repr(ptd[1]),
            "tce_duration": repr(ptd[2]), "tce_depth": "500", "tce_model_snr": "20", "tce_rogue_flag": rogue}


def sample():
    orphans = [{"kepoi_name": n, "kepid": k, "status": s} for n, k, s in [
        ("K01356.01", "7363829", "unrelated"), ("K01192.01", "3644071", "unrelated"),
        ("K00682.01", "7619236", "unrelated"), ("K09001.01", "1000001", "unrelated"),
        ("K09002.01", "7363829", "unrelated"), ("K00600.02", "10718726", "same_events"),
        ("K09003.01", "1000003", "unrelated")]]
    kois = [koi("7363829", "K01356.01", K01356_01), koi("3644071", "K01192.01", K01192_01),
            koi("3644071", "K01192.02", (359.047933, 295.76934, 16.637), "FALSE POSITIVE", "q1_q17_dr25_tce", "1"),
            koi("7619236", "K00682.01", K00682_01),
            koi("1000001", "K09001.01", (10.0, 140.0, 3.0)),  # synthetic: star with no DR25 TCE
            koi("7363829", "K09002.01", (50.0, 140.0, None)),  # synthetic: no duration
            koi("10718726", "K00600.02", (294.055263, 300.0, 10.0))]  # same_events, skipped: T0, dur placeholders
    tces = [tce("7363829", 1, TCE_7363829_1), tce("3644071", 1, TCE_3644071_1), tce("3644071", 2, TCE_3644071_2),
            tce("7619236", 1, TCE_7619236_1, rogue="1"), tce("7619236", 2, TCE_7619236_2)]
    return orphans, kois, tces


class TestEvents(unittest.TestCase):
    def test_events_before_t0(self):
        ev = se.events(10.0, 500.0)
        self.assertEqual(len(ev), 146)
        self.assertAlmostEqual(ev[0], 140.0)
        self.assertAlmostEqual(ev[-1], 1590.0)

    def test_events_bad(self):
        self.assertEqual(se.events(0, 140.0), [])
        self.assertEqual(se.events(10.0, None), [])

    def test_poisson_sf(self):
        self.assertEqual(se.poisson_sf(0, 3.0), 1.0)
        self.assertAlmostEqual(se.poisson_sf(1, 0.5), 0.39346934, places=7)
        self.assertAlmostEqual(se.poisson_sf(2, 0.5), 0.09020401, places=7)
        self.assertEqual(se.poisson_sf(1, 0.0), 0.0)
        self.assertAlmostEqual(se.poisson_sf(1, 1000.0), 1.0)  # no underflow at large lam

    def test_tce_id(self):
        self.assertEqual(se.tce_id("7363829", "1"), "007363829-01")


class TestPairs(unittest.TestCase):
    def test_koi1356(self):
        r = se.pair(*K01356_01, *TCE_7363829_1)
        self.assertEqual((r["n_o"], r["n_t"], r["k"]), (4, 4, 1))
        self.assertAlmostEqual(r["window_d"], 27.07 / 24)
        self.assertAlmostEqual(r["lam"], 0.024730, places=6)
        self.assertAlmostEqual(r["p_chance"], 0.024427, places=5)
        self.assertEqual(r["shared_at"], [335.8162])
        self.assertAlmostEqual(r["orphan_events"][1], 719.8419, places=4)
        for got, want in zip(r["tce_events"], [335.817, 729.536, 1123.255, 1516.974]):
            self.assertAlmostEqual(got, want, places=3)

    def test_koi1032_single_transit(self):
        r = se.pair(*K01032_01, *TCE_2162635_1)
        self.assertEqual((r["n_o"], r["n_t"], r["k"]), (1, 5, 1))
        self.assertAlmostEqual(r["lam"], 0.0145161, places=6)
        self.assertAlmostEqual(r["p_chance"], 0.014411, places=5)

    def test_koi99_single_transit(self):
        r = se.pair(*K00099_01, *TCE_8505215_1)
        self.assertEqual((r["n_o"], r["n_t"], r["k"]), (1, 3, 1))
        self.assertAlmostEqual(r["p_chance"], 0.006900, places=5)

    def test_koi682_middle_event_only(self):
        r = se.pair(*K00682_01, *TCE_7619236_1)
        self.assertEqual((r["n_o"], r["n_t"], r["k"]), (3, 3, 1))
        self.assertEqual(r["shared_at"], [748.1411])
        self.assertAlmostEqual(r["p_chance"], 0.010128, places=5)
        r2 = se.pair(*K00682_01, *TCE_7619236_2)
        self.assertEqual((r2["n_t"], r2["k"]), (3, 0))
        self.assertEqual(r2["p_chance"], 1.0)

    def test_koi1421(self):
        r = se.pair(*K01421_01, *TCE_11342550_1)
        self.assertEqual((r["n_o"], r["n_t"], r["k"]), (1, 5, 1))
        self.assertAlmostEqual(r["p_chance"], 0.012507, places=5)

    def test_koi1192_disjoint(self):
        a = se.pair(*K01192_01, *TCE_3644071_1)
        b = se.pair(*K01192_01, *TCE_3644071_2)
        self.assertEqual((a["n_o"], a["n_t"], a["k"]), (2, 4, 0))
        self.assertEqual((b["n_t"], b["k"]), (4, 0))

    def test_identical_short_period(self):
        # 146 events each, window 2 d, neighbours 10 d apart: every event matches once; lam = 146^2 * 4 / 1459.5
        r = se.pair(10.0, 140.0, 24.0, 10.0, 140.0, 24.0)
        self.assertEqual((r["n_o"], r["k"], len(r["shared_at"]), len(r["tce_events"])), (146, 146, 20, 20))
        self.assertAlmostEqual(r["lam"], 58.4200, places=4)
        self.assertLess(r["p_chance"], 1e-6)

    def test_missing(self):
        self.assertIsNone(se.pair(10.0, 140.0, None, 10.0, 140.0, 3.0))


class TestClassify(unittest.TestCase):
    def test_disjoint(self):
        self.assertEqual(se.classify([("a", {"k": 0, "p_chance": 1.0})])[0], "disjoint")
        self.assertEqual(se.classify([])[0], "disjoint")

    def test_chance_overlap(self):
        s, t, _ = se.classify([("a", {"k": 1, "p_chance": 0.2}), ("b", {"k": 0, "p_chance": 1.0})])
        self.assertEqual((s, t), ("chance_overlap", "a"))

    def test_smallest_p_wins(self):
        s, t, _ = se.classify([("a", {"k": 2, "p_chance": 0.03}), ("b", {"k": 1, "p_chance": 0.01})])
        self.assertEqual((s, t), ("shared_event", "b"))


class TestRobovetter(unittest.TestCase):
    def test_parse(self):
        rv = se.parse_robovetter(ROBO)
        self.assertEqual(len(rv), 2)
        self.assertEqual(rv["000757450-01"]["rv_flags"], "")
        r = rv["007363829-01"]
        self.assertEqual((r["rv_score"], r["rv_disp"], r["rv_nt"], r["rv_ss"]), ("0.000", "FP", "1", "0"))
        self.assertTrue(r["rv_flags"].startswith("INDIV_TRANS_MARSHALL_SKYE"))


class TestScan(unittest.TestCase):
    def setUp(self):
        orphans, kois, tces = sample()
        self.tces = se.tces_by_star(tces, se.federation(kois))
        self.orphans, self.missing = se.unrelated_orphans(orphans, kois)

    def test_unrelated_only(self):
        self.assertEqual([o["kepoi_name"] for o in self.orphans],
                         ["K01356.01", "K01192.01", "K00682.01", "K09001.01", "K09002.01"])
        self.assertEqual(self.missing, ["K09003.01"])

    def test_federation(self):
        t = {x["n"]: x for x in self.tces["3644071"]}
        self.assertEqual(t["1"]["koi"], "K01192.02")
        self.assertEqual(t["2"]["koi"], "")

    def test_statuses(self):
        rows = {r["kepoi_name"]: r for r in se.scan(self.orphans, self.tces)}
        self.assertEqual(rows["K01356.01"]["status"], "shared_event")
        self.assertEqual(rows["K01356.01"]["tce_plnt_num"], "1")
        self.assertEqual(rows["K00682.01"]["status"], "shared_event")
        self.assertEqual(rows["K00682.01"]["tce_rogue"], "1")
        self.assertEqual(rows["K01192.01"]["status"], "disjoint")
        self.assertEqual(rows["K09001.01"]["status"], "no_tce")
        self.assertEqual(rows["K09002.01"]["status"], "no_params")

    def test_null(self):
        mean, runs = se.null_tallies(self.orphans, self.tces, n=5, seed=1)
        self.assertEqual(len(runs), 5)
        for r in runs:
            self.assertEqual(sum(r.values()), 5)
        self.assertEqual(mean, se.null_tallies(self.orphans, self.tces, n=5, seed=1)[0])

    def test_derangement(self):
        d = se.derangement(["a", "b", "c"], random.Random(3))
        self.assertEqual(sorted(d.values()), ["a", "b", "c"])
        self.assertTrue(all(k != v for k, v in d.items()))


class TestMain(unittest.TestCase):
    def test_end_to_end(self):
        orphans, kois, tces = sample()
        with tempfile.TemporaryDirectory() as d:
            paths = {}
            for name, fields, rows in [("o.csv", ORPHAN_FIELDS, orphans), ("k.csv", KOI_FIELDS, kois),
                                       ("t.csv", TCE_FIELDS, tces)]:
                paths[name] = os.path.join(d, name)
                with open(paths[name], "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=fields)
                    w.writeheader()
                    w.writerows(rows)
            for name, text in [("r.txt", ROBO), ("x.csv", XMATCH)]:
                paths[name] = os.path.join(d, name)
                with open(paths[name], "w", encoding="utf-8") as f:
                    f.write(text)
            out = os.path.join(d, "out")
            with redirect_stdout(io.StringIO()):
                se.main(["--out-dir", out, "--orphans", paths["o.csv"], "--koi-csv", paths["k.csv"],
                         "--tce-csv", paths["t.csv"], "--robovetter", paths["r.txt"], "--xmatch", paths["x.csv"]])
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            with open(os.path.join(out, "shared_events.csv"), encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        self.assertEqual(s["unrelated"], 5)
        self.assertEqual(s["missing_from_cumulative"], ["K09003.01"])
        self.assertEqual(s["counts"], {"shared_event": 2, "chance_overlap": 0, "disjoint": 1, "no_params": 1,
                                       "no_tce": 1})
        self.assertEqual(s["shared_tce_kind"], {"rogue": 1, "FP": 1})
        self.assertEqual([r["kepoi_name"] for r in rows[:2]], ["K00682.01", "K01356.01"])
        r1356 = rows[1]
        self.assertEqual((r1356["rv_disp"], r1356["rv_score"], r1356["rv_nt"]), ("FP", "0.000", "1"))
        self.assertEqual((r1356["lissauer_status"], r1356["lissauer_period"]), ("PPNN", "787.43235205"))
        self.assertEqual(rows[0]["rv_disp"], "absent")


if __name__ == "__main__":
    unittest.main()
