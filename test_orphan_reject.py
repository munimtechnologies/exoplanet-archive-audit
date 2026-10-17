"""Tests for orphan_reject. Fixture rows are copied from the published koi_orphans 0.1.0 and
lissauer_xmatch 0.1.0 outputs and the Archive's q1_q17_dr25_tce table; expected values worked by hand.
Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0."""
import json
import os
import tempfile
import unittest

import orphan_reject as orj

ORPHANS = """kepoi_name,kepid,kepler_name,disp,prov,p_orphan,depth_orphan,snr_orphan,n_tce,status,kind,a,b,tce_plnt_num,tce_koi,tce_koi_disp,p_tce,off_d,window_d,p_phase
K00600.02,10718726,,CANDIDATE,q1_q16_koi,294.055263,770.0,21.1,2,same_events,same,1,1,2,,,294.054,-0.0049999999999954525,1.1937499999999999,0.008119222134106131
K01101.02,3245969,,CANDIDATE,q1_q16_koi,11.39110963,593.4,12.1,1,same_events,same,1,1,1,K01101.01,CONFIRMED,11.3911,-0.0053499999999928605,0.22925000000000004,0.04025068802713297
K02433.06,11968463,,CANDIDATE,q1_q17_dr24_koi,6.06330298,200.7,13.1,6,offset,rational,2,5,2,K02433.01,CONFIRMED,15.1623,0.8000244700000056,0.431375,0.2845808638775957
K00364.01,7296438,,CANDIDATE,q1_q16_koi,173.92851338,,,0,no_tce,,,,,,,,,,
K00823.01,5115978,,CANDIDATE,q1_q16_koi,1.028436523,8098.0,89.6,0,no_tce,,,,,,,,,,
K01096.01,3230491,,CANDIDATE,q1_q16_koi,1500.0,9592.0,62.5,0,no_tce,,,,,,,,,,
"""

XMATCH = """kepoi_name,kepid,kepler_name,archive_disposition,parm_prov,orphan,lissauer_status,lissauer_now,lissauer_dr25supp,archive_period,lissauer_period,period_ratio,ratio_fraction,ratio_fraction_err,archive_snr,lissauer_snr,kic_match
K00823.01,5115978,,CANDIDATE,q1_q16_koi,True,RPNN,R,P,1.028436523,1.02843591,0.9999994039496007,1/1,5.960503992596955e-07,89.6,82.6,True
K01096.01,3230491,,CANDIDATE,q1_q16_koi,True,RPNN,R,P,1500.0,-1500.0,-1.0,12/1,1.0833333333333333,62.5,64.2,True
K01101.02,3245969,,CANDIDATE,q1_q16_koi,True,FPNN,F,P,11.39110963,11.39114826,1.0000033912411743,1/1,3.3912411743219906e-06,12.1,0.0,True
K00364.01,7296438,,CANDIDATE,q1_q16_koi,True,PPNN,P,P,173.92851338,173.76047816,0.999033883422939,1/1,0.0009661165770610269,,8.8,True
K00600.02,10718726,,CANDIDATE,q1_q16_koi,True,PPNN,P,P,294.055263,294.0521699,0.9999894812289076,1/1,1.0518771092371537e-05,21.1,21.5,True
K02433.06,11968463,,CANDIDATE,q1_q17_dr24_koi,True,PPNP,P,P,6.06330298,6.0632531,0.9999917734607418,1/1,8.226539258249232e-06,13.1,12.4,True
"""

# Real rogue TCEs: KIC 10718726 TCE 2 (294.054 d) and KIC 2576962 TCE 1 (309.235 d), tce_rogue_flag = 1.
ROGUE = """kepid,tce_plnt_num
10718726,2
2576962,1
"""


def run_fixture(xmatch=XMATCH):
    rogue = {(int(r["kepid"]), int(r["tce_plnt_num"])) for r in orj.read_csv(ROGUE)}
    return orj.analyse(orj.read_csv(ORPHANS), orj.read_csv(xmatch), rogue)


class TestFisher(unittest.TestCase):
    def test_textbook_table(self):
        # [[3, 1], [1, 3]]: (C(4,3) C(4,1) + C(4,4) C(4,0)) / C(8,4) = 17 / 70
        self.assertAlmostEqual(orj.fisher_greater(3, 1, 1, 3), 17 / 70, places=12)

    def test_fixture_table(self):
        # [[2, 1], [1, 2]]: (C(3,2) C(3,1) + C(3,3) C(3,0)) / C(6,3) = 10 / 20
        self.assertAlmostEqual(orj.fisher_greater(2, 1, 1, 2), 0.5, places=12)

    def test_extreme(self):
        self.assertAlmostEqual(orj.fisher_greater(0, 3, 3, 0), 1.0, places=12)
        self.assertAlmostEqual(orj.fisher_greater(3, 0, 0, 3), 1 / 20, places=12)


class TestAnalyse(unittest.TestCase):
    def setUp(self):
        self.rows, self.s = run_fixture()

    def test_join(self):
        self.assertEqual(self.s["n_orphans"], 6)
        self.assertEqual(self.s["n_joined"], 6)
        self.assertEqual(self.s["missing_from_xmatch"], [])
        self.assertEqual(self.s["rejected_total"], 3)

    def test_by_status(self):
        b = self.s["by_status"]
        self.assertEqual(b["no_tce"], {"n": 3, "rejected": 2, "fraction": 0.6667})
        self.assertEqual(b["same_events"], {"n": 2, "rejected": 1, "fraction": 0.5})
        self.assertEqual(b["offset"], {"n": 1, "rejected": 0, "fraction": 0.0})
        self.assertEqual(b["unrelated"], {"n": 0, "rejected": 0, "fraction": None})

    def test_by_prov(self):
        self.assertEqual(self.s["by_prov"]["q1_q16_koi"], {"n": 5, "rejected": 3, "fraction": 0.6})
        self.assertEqual(self.s["by_prov"]["q1_q17_dr24_koi"], {"n": 1, "rejected": 0, "fraction": 0.0})

    def test_no_tce_vs_with_tce(self):
        t = self.s["no_tce_vs_with_tce"]
        self.assertEqual(t["no_tce"]["rejected"], 2)
        self.assertEqual(t["with_tce"], {"n": 3, "rejected": 1, "fraction": 0.3333})
        self.assertAlmostEqual(t["fisher_p_greater"], 0.5, places=12)

    def test_reject_letters(self):
        self.assertEqual(self.s["reject_letters_by_status"], {"same_events": {"F": 1}, "no_tce": {"R": 2}})

    def test_rogue(self):
        self.assertEqual(self.s["same_events_on_rogue_tce"], ["K00600.02 TCE 2 Lissauer PPNN"])
        self.assertEqual(self.s["orphans_with_rogue_on_star"], 1)
        by = {r["kepoi_name"]: r for r in self.rows}
        self.assertFalse(by["K01101.02"]["matched_tce_rogue"])
        self.assertFalse(by["K00364.01"]["matched_tce_rogue"])

    def test_missing(self):
        lines = [l for l in XMATCH.splitlines() if not l.startswith("K00364.01,")]
        _, s = run_fixture("\n".join(lines) + "\n")
        self.assertEqual(s["missing_from_xmatch"], ["K00364.01"])
        self.assertEqual(s["n_joined"], 5)

    def test_main_offline(self):
        with tempfile.TemporaryDirectory() as d:
            paths = {}
            for name, text in (("o", ORPHANS), ("x", XMATCH), ("r", ROGUE)):
                paths[name] = os.path.join(d, name + ".csv")
                with open(paths[name], "w", encoding="utf-8") as f:
                    f.write(text)
            out = os.path.join(d, "out")
            orj.main(["--out-dir", out, "--orphans", paths["o"], "--xmatch", paths["x"], "--rogue", paths["r"]])
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual(s["n_rogue_tces"], 2)
            self.assertEqual(s["rejected_total"], 3)
            self.assertTrue(os.path.exists(os.path.join(out, "orphan_reject.csv")))


if __name__ == "__main__":
    unittest.main()
