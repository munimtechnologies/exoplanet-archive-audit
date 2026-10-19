# Apache-2.0. Tests for sbdb_cad 0.1.0, MV2 of Munim, Inc. Made with AI agents.
# Every expected value below was worked out by hand before the code ran. The small table in TestTally is a made-up,
# format-like scenario (fake spkids 3000001-3000005, designations X1-X5), not rows from any output file.
import json
import unittest
from decimal import Decimal

import sbdb_cad as m

D = Decimal


def cad(des, oid, jd, dist, dmin, dmax, vrel="5.0", vinf="4.0"):
    return {"des": des, "orbit_id": oid, "jd": jd, "cd": "2026-Jan-01 00:00", "dist": dist, "dist_min": dmin,
            "dist_max": dmax, "v_rel": vrel, "v_inf": vinf, "t_sigma_f": "< 00:01", "h": "20.0"}


def sbdb(spkid, pdes, oid, epoch, moid):
    return {"spkid": spkid, "pdes": pdes, "orbit_id": oid, "epoch": epoch, "moid": moid, "condition_code": "0",
            "data_arc": "100", "n_obs_used": "50", "last_obs": "2026-01-01", "soln_date": "2026-01-02 00:00:00"}


class TestParsing(unittest.TestCase):
    def test_parse_value_interval(self):
        self.assertEqual(m.parse_value("0.090"), (D("0.090"), D("0.0005")))
        self.assertEqual(m.parse_value("0.0100"), (D("0.0100"), D("0.00005")))
        self.assertEqual(m.parse_value("19.09", exact=True), (D("19.09"), D(0)))
        self.assertIsNone(m.parse_value(""))
        self.assertIsNone(m.parse_value("abc"))
        self.assertIsNone(m.parse_value(None))

    def test_bounds(self):
        self.assertEqual(m.bounds((D("0.0100"), D("0.00005"))), (D("0.00995"), D("0.01005")))

    def test_norm_orbit_id(self):
        self.assertEqual(m.norm_orbit_id("JPL 732"), "732")
        self.assertEqual(m.norm_orbit_id("659"), "659")
        self.assertEqual(m.norm_orbit_id("JPL K284/1"), "K284/1")
        self.assertEqual(m.norm_orbit_id(" 220 "), "220")
        self.assertEqual(m.norm_orbit_id("jpl 5"), "5")
        self.assertIsNone(m.norm_orbit_id(None))
        self.assertIsNone(m.norm_orbit_id(""))
        self.assertIsNone(m.norm_orbit_id("JPL "))

    def test_orbit_id_order(self):
        self.assertEqual(m.orbit_id_order("220", "220"), "same")
        self.assertEqual(m.orbit_id_order("219", "220"), "cad_older")
        self.assertEqual(m.orbit_id_order("221", "220"), "cad_newer")
        self.assertEqual(m.orbit_id_order("K284/1", "K284/2"), "differ")

    def test_parse_page_cad_format_like(self):
        body = json.dumps({"signature": {"version": "1.5"}, "count": 1, "fields": m.CAD_FIELDS,
                           "data": [["99999 XX", "12", "2461250.5", "2026-Jul-29 00:00", "0.0100", "0.0099",
                                     "0.0101", "5.0", "4.0", "< 00:01", "20.0"]]}).encode("utf-8")
        count, fields, rows = m.parse_page(body)
        self.assertEqual(count, 1)
        self.assertEqual(fields, m.CAD_FIELDS)
        self.assertEqual(rows[0]["des"], "99999 XX")
        self.assertEqual(rows[0]["dist"], "0.0100")
        self.assertEqual(rows[0]["h"], "20.0")

    def test_parse_page_sbdb_numbers_become_strings(self):
        body = json.dumps({"signature": {"version": "1.0"}, "fields": ["spkid", "pdes"], "data": [[3000001, "X1"]],
                           "count": 1}).encode("utf-8")
        count, fields, rows = m.parse_page(body)
        self.assertEqual((count, fields), (1, ["spkid", "pdes"]))
        self.assertEqual(rows[0], {"spkid": "3000001", "pdes": "X1"})


class TestPhysics(unittest.TestCase):
    def test_impact_parameter(self):
        dist = m.parse_value("0.0100")
        b = m.impact_parameter(dist, (D("5.0"), D(0)), (D("4.0"), D(0)))
        self.assertEqual(b, (D("0.0124375"), D("0.0125625")))
        self.assertIsNone(m.impact_parameter(dist, (D("5.0"), D(0)), (D("0"), D(0))))
        self.assertIsNone(m.impact_parameter(dist, None, (D("4.0"), D(0))))
        self.assertIsNone(m.impact_parameter(None, (D("5.0"), D(0)), (D("4.0"), D(0))))

    def test_g2_status(self):
        b = (D("0.0124375"), D("0.0125625"))
        self.assertEqual(m.g2_status(b, m.parse_value("0.0300")), "flagged")  # 0.0125625 < 0.02995 - 0.001
        self.assertEqual(m.g2_status(b, m.parse_value("0.0130")), "ok")  # 0.0125625 >= 0.01295 - 0.001
        self.assertEqual(m.g2_status(b, m.parse_value("0.0135625")), "ok")  # lo 0.01356245 - 0.001 < b_hi
        self.assertIsNone(m.g2_status(None, m.parse_value("0.0300")))
        self.assertIsNone(m.g2_status(b, None))

    def test_g3_status(self):
        self.assertEqual(m.g3_status("0.0102", "0.0100", "0.0105"), "ok")
        self.assertEqual(m.g3_status("0.0100", "0.0100", "0.0100"), "ok")
        self.assertEqual(m.g3_status("0.0099", "0.0100", "0.0105"), "violation")
        self.assertEqual(m.g3_status("0.0106", "0.0100", "0.0105"), "violation")
        self.assertIsNone(m.g3_status("0.0102", None, "0.0105"))

    def test_first_and_last(self):
        rows = [{"jd_dec": D("2461000.5")}, {"jd_dec": D("2461300.5")}, {"jd_dec": D("2461250.5")},
                {"jd_dec": D("2461199.5")}]
        e = D("2461200.5")
        self.assertEqual(m.first_after_epoch(rows, e)["jd_dec"], D("2461250.5"))
        self.assertEqual(m.last_before_epoch(rows, e)["jd_dec"], D("2461199.5"))
        self.assertIsNone(m.first_after_epoch(rows, D("2461400")))
        self.assertIsNone(m.last_before_epoch(rows, D("2461000.5")))
        self.assertEqual(m.first_after_epoch(rows, D("2461250.5"))["jd_dec"], D("2461250.5"))

    def test_epoch_window(self):
        self.assertTrue(m.epoch_window_ok(D("2461200.5")))
        self.assertTrue(m.epoch_window_ok(D("2460310.5")))
        self.assertFalse(m.epoch_window_ok(D("2460310.4")))
        self.assertTrue(m.epoch_window_ok(D("2461406.25")))  # + 365.25 = 2461771.5 exactly
        self.assertFalse(m.epoch_window_ok(D("2461406.26")))

    def test_bins(self):
        self.assertEqual(m.bin_label(D("-0.02")), "<-0.01")
        self.assertEqual(m.bin_label(D("-0.005")), "[-0.01,-0.001)")
        self.assertEqual(m.bin_label(D("-0.001")), "[-0.001,0)")
        self.assertEqual(m.bin_label(D("-0.0005")), "[-0.001,0)")
        self.assertEqual(m.bin_label(D("0")), "[0,0.001)")
        self.assertEqual(m.bin_label(D("0.001")), "[0.001,0.01)")
        self.assertEqual(m.bin_label(D("0.05")), "[0.01,0.1)")
        self.assertEqual(m.bin_label(D("0.2")), ">=0.1")
        self.assertEqual(m.dt_label(D("0")), "[0,30]")
        self.assertEqual(m.dt_label(D("50")), "(30,90]")
        self.assertEqual(m.dt_label(D("100")), "(90,180]")
        self.assertEqual(m.dt_label(D("365.25")), "(180,365.25]")
        self.assertEqual(m.dt_label(D("365.26")), ">365.25")


class TestDecisions(unittest.TestCase):
    def test_g1(self):
        self.assertEqual(m.decide_g1(5000, 50), "holds")
        self.assertEqual(m.decide_g1(5000, 51), "fails")
        self.assertEqual(m.decide_g1(4999, 0), "underpowered")

    def test_g2(self):
        self.assertEqual(m.decide_g2(1000, 1), "holds")
        self.assertEqual(m.decide_g2(1000, 2), "fails")
        self.assertEqual(m.decide_g2(999, 0), "underpowered")

    def test_g3(self):
        self.assertEqual(m.decide_g3(5000, 0), "holds")
        self.assertEqual(m.decide_g3(5000, 1), "fails")
        self.assertEqual(m.decide_g3(4999, 0), "underpowered")


class TestTally(unittest.TestCase):
    def setUp(self):
        table = [sbdb("3000001", "X1", "JPL 5", "2461200.5", "0.0300"),
                 sbdb("3000002", "X2", "7", "2461200.5", "0.0050"),
                 sbdb("3000003", "X3", "JPL 9", "2459000.5", "0.1"),
                 sbdb("3000005", "X5", "JPL 11", "2461200.5", "0.0100"),
                 sbdb("20099942", "99942", "220", "2461200.5", "0.0003")]
        self.t = m.Tally({r["pdes"]: r for r in table}, {20099942})
        rows = [cad("X1", "5", "2461250.5", "0.0100", "0.0099", "0.0101"),  # a: G2 first after epoch, flagged
                cad("X2", "6", "2461250.5", "0.0100", "0.0101", "0.0105"),  # b: G3 violation, G1 cad_older
                cad("X4", "1", "2461250.5", "0.05", "0.049", "0.051"),  # c: unmatched
                cad("X3", "9", "2461250.5", "0.0100", "0.0099", "0.0101"),  # d: epoch outside window
                cad("X1", "5", "2460400.5", "0.0100", "0.0099", "0.0101"),  # e: 800 d before epoch
                cad("X1", "5", "2462000.5", "0.0100", "0.0099", "0.0101"),  # f: outside window
                cad("99942", "220", "2461250.5", "0.0003", "0.0002", "0.0004"),  # g: excluded probe
                cad("X5", "11", "2461100.5", "0.0200", "0.0199", "0.0201"),  # h: 100 d before epoch, descriptive
                cad("X5", "11", "2461300.5", "0.0200", "0.0199", "0.0201")]  # i: G2 ok, dt 100
        for r in rows:
            self.t.add_cad(r)
        self.t.finish()
        self.c = self.t.counts

    def test_row_counts(self):
        c = self.c
        self.assertEqual(c["cad_rows"], 9)
        self.assertEqual((c["g3 ok"], c["g3 violation"]), (8, 1))
        self.assertEqual(c["cad outside_window"], 1)
        self.assertEqual((c["join unmatched"], c["join excluded_seen"], c["join matched"]), (1, 1, 6))
        self.assertEqual((c["g1 same"], c["g1 differ"]), (5, 1))
        self.assertEqual((c["g1_order same"], c["g1_order cad_older"]), (5, 1))
        self.assertNotIn("g1_order cad_newer", c)

    def test_g2_counts(self):
        c = self.c
        self.assertEqual((c["g2 flagged"], c["g2 ok"]), (1, 1))
        self.assertEqual(c["g2 epoch_outside_window"], 1)
        self.assertEqual(c["g2_before ok"], 1)
        self.assertNotIn("g2_before flagged", c)
        self.assertEqual((c["g2_naive dist<moid"], c["g2_naive dist>=moid"]), (1, 1))
        self.assertEqual((c["g2_b b<moid"], c["g2_b b>=moid"]), (1, 1))
        self.assertEqual(c["g2_bin b-moid <-0.01"], 1)
        self.assertEqual(c["g2_bin b-moid [0.01,0.1)"], 1)
        self.assertEqual(c["g2_bin dist-moid <-0.01"], 1)
        self.assertEqual(c["g2_bin dist-moid [0.01,0.1)"], 1)
        self.assertEqual((c["g2_dt_bin (30,90]"], c["g2_dt_bin (90,180]"]), (1, 1))
        self.assertEqual((c["precision dist -4"], c["precision moid -4"]), (2, 2))
        self.assertEqual((c["precision v_rel -1"], c["precision v_inf -1"]), (2, 2))
        self.assertEqual(self.t.epochs, {"2461200.5": 2, "2459000.5": 1})

    def test_g2_rows_and_lists(self):
        rows = sorted(self.t.g2_rows)
        self.assertEqual(len(rows), 2)
        x1 = rows[0]
        self.assertEqual(x1[:5], ["X1", "5", "2461250.5", "2461200.5", "50.0"])
        self.assertEqual(x1[5:13], ["0.0100", "5.0", "4.0", "0.0125", "0.0300", "-0.0175", "-0.0200", "flagged"])
        x5 = rows[1]
        self.assertEqual(x5[:5], ["X5", "11", "2461300.5", "2461200.5", "100.0"])
        self.assertEqual(x5[8:13], ["0.0250", "0.0100", "0.0150", "0.0100", "ok"])
        self.assertEqual({k: len(v) for k, v in self.t.lists.items()}, {"g1": 1, "g2": 1, "g3": 1})
        self.assertEqual(self.t.lists["g1"][0][:4], ["g1", "X2", "6", "7"])
        self.assertEqual(self.t.lists["g1"][0][-1], "cad_older")
        self.assertEqual(self.t.lists["g2"][0][:2], ["g2", "X1"])
        self.assertEqual(self.t.lists["g2"][0][-1], "b=0.0125 < moid-0.001")
        self.assertEqual(self.t.lists["g3"][0][:2], ["g3", "X2"])

    def test_decisions(self):
        self.assertEqual(m.decisions(self.t), {
            "G1": {"n_matched": 6, "n_differ": 1, "decision": "underpowered"},
            "G2": {"n_eligible": 2, "n_flagged": 1, "decision": "underpowered"},
            "G3": {"n_rows": 9, "n_violation": 1, "decision": "underpowered"},
        })


if __name__ == "__main__":
    unittest.main()
