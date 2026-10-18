"""Tests for skye_census. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0.

Every expected value below was worked by hand.
"""
import hashlib
import os
import tempfile
import unittest

import skye_census as sc

SPANS = {1: (131.5, 165.0), 2: (169.5, 258.5)}


class TestEvents(unittest.TestCase):
    def test_two_quarters(self):
        # n = ceil((131.5 - 150) / 100) = 0 -> 150 in Q1; n = ceil(19.5 / 100) = 1 -> 250 in Q2
        self.assertEqual(sc.events(100.0, 150.0, {1, 2}, SPANS), [150.0, 250.0])

    def test_missing_quarter_and_unknown_quarter(self):
        self.assertEqual(sc.events(100.0, 150.0, {2, 0}, SPANS), [250.0])

    def test_t0_after_the_span(self):
        # n = ceil((131.5 - 950) / 100) = ceil(-8.185) = -8 -> 950 - 800 = 150
        self.assertEqual(sc.events(100.0, 950.0, {1}, SPANS), [150.0])

    def test_bad_period(self):
        self.assertEqual(sc.events(0.0, 150.0, {1}, SPANS), [])
        self.assertEqual(sc.events(-5.0, 150.0, {1}, SPANS), [])

    def test_real_quarters_k05227(self):
        # K05227.01: P 371.56492, T0 259.8491 lies in the Q2-Q3 gap (258.47-260.22), so three events remain
        evs = sc.events(371.56492, 259.8491, set(range(1, 18)))
        # 259.8491 + 3 * 371.56492 = 1374.54386 -> 1374.5439
        self.assertEqual(evs, [631.414, 1002.9789, 1374.5439])

    def test_real_quarters_k05269(self):
        # K05269.01: T0 260.1243 is 0.10 d before Q3's first cadence (260.22), so three events remain
        evs = sc.events(371.50631, 260.1243, set(range(1, 18)))
        self.assertEqual(evs, [631.6306, 1003.1369, 1374.6432])


class TestBins(unittest.TestCase):
    def test_bin_index(self):
        # Skye.py edges at 131.5 + k: 260.12 - 131.5 = 128.62 -> 128
        self.assertEqual(sc.bin_index(260.12), 128)
        self.assertEqual(sc.bin_index(131.5), 0)
        self.assertEqual(sc.bin_index(131.49), -1)
        self.assertEqual(sc.bin_index(260.12, 131.0), 129)

    def test_rate_bins(self):
        # centres 131.5 132.5 (in span 1), 133.5 134.5 (out), 135.5 (in span 2), 136.5 (out)
        self.assertEqual(sc.rate_bins({1: (131.5, 133.2), 2: (135.0, 136.0)}, 131.0), [0, 1, 4])

    def test_rate_bins_default_origin(self):
        # centres 132 133 (in span 1), 134 (out), 135 136 (in span 2, ends inclusive)
        self.assertEqual(sc.rate_bins({1: (131.5, 133.2), 2: (135.0, 136.0)}), [0, 1, 3, 4])

    def test_rate_bins_empty(self):
        self.assertEqual(sc.rate_bins({}), [])

    def test_one_outlier(self):
        # 19 / 10 = 1.9, thr 1.9 + 3 * 1.378405 = 6.035 -> drop bin 9; then 9 / 9 = 1, thr 4 -> stable
        counts = {k: 1 for k in range(9)}
        counts[9] = 10
        flagged, r, thr = sc.skye_bins(counts, list(range(10)))
        self.assertEqual(flagged, {9})
        self.assertAlmostEqual(r, 1.0)
        self.assertAlmostEqual(thr, 4.0)

    def test_no_outlier(self):
        flagged, r, thr = sc.skye_bins({0: 2, 1: 2, 2: 2, 3: 2}, [0, 1, 2, 3])
        self.assertEqual(flagged, set())
        self.assertAlmostEqual(r, 2.0)
        self.assertAlmostEqual(thr, 2.0 + 3 * 2 ** 0.5)

    def test_flagged_outside_rate_bins(self):
        # rate 4 / 4 = 1, thr 4; bin 7 is not a rate bin but its 9 events exceed 4
        flagged, r, thr = sc.skye_bins({0: 1, 1: 1, 2: 1, 3: 1, 7: 9}, [0, 1, 2, 3])
        self.assertEqual(flagged, {7})
        self.assertAlmostEqual(thr, 4.0)

    def test_cascade(self):
        # 59 / 20 = 2.95, thr 8.1027 -> drop 19; 29 / 19 = 1.526316, thr 5.232642 -> drop 17, 18;
        # 17 / 17 = 1, thr 4 -> stable for the remaining passes
        counts = {k: 1 for k in range(17)}
        counts.update({17: 6, 18: 6, 19: 30})
        flagged, r, thr = sc.skye_bins(counts, list(range(20)))
        self.assertEqual(flagged, {17, 18, 19})
        self.assertAlmostEqual(r, 1.0)
        self.assertAlmostEqual(thr, 4.0)

    def test_zero_passes(self):
        # no pass: R 2.95, cutoff 2.95 + 3 * 1.717556 = 8.102669; only bin 19 (30) is above it
        counts = {k: 1 for k in range(17)}
        counts.update({17: 6, 18: 6, 19: 30})
        flagged, r, thr = sc.skye_bins(counts, list(range(20)), passes=0)
        self.assertEqual(flagged, {19})
        self.assertAlmostEqual(r, 2.95)
        self.assertAlmostEqual(thr, 2.95 + 3 * 2.95 ** 0.5)


class TestBuildSkye(unittest.TestCase):
    # four stars of skygroup 5 observed only in Q3 (260.22-349.50); star 99 has no skygroup
    MAST = {1: (5, {3}), 2: (5, {3}), 3: (5, {3}), 4: (5, {3})}
    # stars 1-3: one event each at 300.2 (P 400); star 4: 270.0 and 320.0 (P 50; 370.0 is after Q3)
    TCES = [(1, 400.0, 300.2), (2, 400.0, 300.2), (3, 400.0, 300.2), (4, 50.0, 270.0), (99, 400.0, 300.2)]

    def test_skye_py_origin(self):
        # bins: 300.2 -> 168, 270.0 -> 138, 320.0 -> 188; rate bins: centres 261.0 .. 349.0 = bins 129 .. 217 (89)
        # R 5 / 89, cutoff 0.767; the first pass drops all three bins, leaving R 0 and cutoff 0
        skye, info, rows = sc.build_skye(self.TCES, self.MAST)
        self.assertEqual(skye, {5: {138, 168, 188}})
        self.assertEqual((info[5]["events"], info[5]["rate_bins"], info[5]["rate"], info[5]["threshold"]),
                         (5, 89, 0.0, 0.0))
        self.assertEqual([(r["bin"], r["start"], r["count"]) for r in rows],
                         [(138, 269.5, 1), (168, 299.5, 3), (188, 319.5, 1)])

    def test_v1_origin(self):
        # bins: 300.2 -> 169, 270.0 -> 139, 320.0 -> 189; rate bins: centres 260.5 .. 349.5 = bins 129 .. 218 (90)
        skye, info, _ = sc.build_skye(self.TCES, self.MAST, 131.0)
        self.assertEqual(skye, {5: {139, 169, 189}})
        self.assertEqual(info[5]["rate_bins"], 90)


class TestSkyeComment(unittest.TestCase):
    def test_skye_alone_and_with_other_flags(self):
        self.assertTrue(sc.has_skye("INDIV_TRANS_SKYE"))
        self.assertTrue(sc.has_skye("INDIV_TRANS_MARSHALL_SKYE---CENT_FEW_DIFFS"))
        self.assertTrue(sc.has_skye("INDIV_TRANS_RUBBLE_SKYE_ZUMA_TRACKER---CENT_KIC_POS"))

    def test_no_skye(self):
        self.assertFalse(sc.has_skye("INDIV_TRANS_RUBBLE_ZUMA---SKYE_LIKE"))
        self.assertFalse(sc.has_skye("ALL_TRANS_CHASES---CENT_FEW_DIFFS"))
        self.assertFalse(sc.has_skye("NO_COMMENT"))
        self.assertFalse(sc.has_skye(""))
        self.assertFalse(sc.has_skye(None))


class TestRobovetter(unittest.TestCase):
    def test_parse_input(self):
        lines = ["# a header line with many fields 1 2 3 4 5 6 7 8 9 10 11 12\n",
                 "OBS 001026032-01 1026032 1 1 4 3 3 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 1 2 3\n",
                 "OBS 001026032-02 1026032 2 2 10 9 7 1 0 0 0 0 0\n",
                 "short line 1 2\n",
                 "OBS x notanumber 1 1 4 3 3 0 0 0 1 0 0\n"]
        self.assertEqual(sc.parse_rv_input(lines), {(1026032, 1): (4, 3, 3, 1), (1026032, 2): (10, 9, 7, 0)})

    def test_tce_key(self):
        self.assertEqual(sc.tce_key("001026032-01"), (1026032, 1))
        self.assertEqual(sc.tce_key(" 010000009-12 "), (10000009, 12))
        self.assertIsNone(sc.tce_key("junk"))
        self.assertIsNone(sc.tce_key(""))

    def test_parse_output(self):
        lines = ["#1:TCE  2:Robovetter_Score  3:Disposition 8:Minor_Descriptive_Flags\n",
                 "001026032-01 0.000 FP 1 0 0 0 INDIV_TRANS_MARSHALL_SKYE---CENT_FEW_DIFFS\n",
                 "001026032-02 0.987 PC 0 0 0 0 \n",
                 "\n"]
        self.assertEqual(sc.parse_rv_output(lines),
                         {(1026032, 1): "INDIV_TRANS_MARSHALL_SKYE---CENT_FEW_DIFFS", (1026032, 2): ""})

    def test_confusion(self):
        c = sc.confusion([(1, 1), (1, 0), (0, 1), (0, 0), (1, 1)])
        self.assertEqual(c, {"tp": 2, "fp": 1, "fn": 1, "tn": 1, "recall": 0.6667, "precision": 0.6667})
        self.assertEqual(sc.confusion([])["recall"], None)

    def test_validation(self):
        tce_rows = [{"rv_found": 1, "n_events": 3, "rv_nrealtrans": 3, "n_flagged": 1, "n_flagged_v1bins": 0,
                     "rv_skye": 1},
                    {"rv_found": 1, "n_events": 4, "rv_nrealtrans": 3, "n_flagged": 0, "n_flagged_v1bins": 0,
                     "rv_skye": 0},
                    {"rv_found": 0, "n_events": 2, "rv_nrealtrans": "", "n_flagged": 2, "n_flagged_v1bins": 2,
                     "rv_skye": ""}]
        rv_table = {(1, 1): (3, 3, 2, 1), (1, 2): (4, 3, 3, 0), (2, 1): (5, 5, 5, 1)}
        rv_comments = {(1, 1): "INDIV_TRANS_SKYE", (1, 2): "NO_COMMENT", (3, 1): "INDIV_TRANS_RUBBLE_SKYE"}
        v = sc.validation(tce_rows, rv_table, rv_comments)
        self.assertEqual((v["rv_rows"], v["tces_with_skygroup"], v["tces_found_in_rv"], v["join_fraction"]),
                         (3, 3, 2, 0.6667))
        # (3, 1) carries a SKYE comment but is not in the input table, so 1 of 2
        self.assertEqual((v["rv_skye_flag_1_all_periods"], v["comment_skye_tces"], v["comment_skye_with_flag_1"],
                          v["comment_flag_fraction"], v["events_equal_nrealtrans"]), (2, 2, 1, 0.5, 0.5))
        self.assertEqual(v["primary"], {"tp": 1, "fp": 0, "fn": 0, "tn": 1, "recall": 1.0, "precision": 1.0})
        self.assertEqual(v["v1_bins"], {"tp": 0, "fp": 0, "fn": 1, "tn": 1, "recall": 0.0, "precision": None})


class TestTables(unittest.TestCase):
    def test_looks_like_table(self):
        # the header line of skye-census-v1's dr25_koi.csv, as TAP wrote it
        koi = (b'kepoi_name,kepid,koi_pdisposition,koi_period,koi_time0bk,koi_comment\n'
               b'"K00753.01",10811496,"FALSE POSITIVE",19.89913995,175.850252,"DEEP_V_SHAPED"\n')
        self.assertTrue(sc.looks_like_table(koi, sc.QUERIES["dr25_koi"]))
        self.assertTrue(sc.looks_like_table(b"kepid,tce_plnt_num\r\n1,2\r\n",
                                            "select kepid,tce_plnt_num from q1_q17_dr25_tce"))
        self.assertFalse(sc.looks_like_table(koi, sc.QUERIES["cumulative"]))
        self.assertFalse(sc.looks_like_table(b"<html>ORA-01653</html>", sc.QUERIES["dr25_tce"]))
        self.assertFalse(sc.looks_like_table(b"", sc.QUERIES["dr25_tce"]))

    def test_snapshot_bytes(self):
        saved = sc.SNAPSHOT_SHA256
        self.addCleanup(setattr, sc, "SNAPSHOT_SHA256", saved)
        sc.SNAPSHOT_SHA256 = {"t": hashlib.sha256(b"a\nb\n").hexdigest()}
        self.assertEqual(sc.snapshot_bytes("t", b"a\nb\n"), b"a\nb\n")
        self.assertEqual(sc.snapshot_bytes("t", b"a\r\nb\r\n"), b"a\nb\n")
        self.assertIsNone(sc.snapshot_bytes("t", b"a\nc\n"))
        self.assertIsNone(sc.snapshot_bytes("other", b"a\nb\n"))

    def test_snapshot_covers_every_query(self):
        self.assertEqual(set(sc.SNAPSHOT_SHA256), set(sc.QUERIES))
        self.assertTrue(all(len(v) == 64 for v in sc.SNAPSHOT_SHA256.values()))

    def test_fetch_in_dir(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "dr25_tce.csv"), "wb") as f:
                f.write(b"kepid\n1\n")
            self.assertEqual(sc.fetch_table("dr25_tce", "select kepid from q1_q17_dr25_tce", d),
                             (b"kepid\n1\n", "in_dir", ""))


class TestStats(unittest.TestCase):
    def test_binom_tail(self):
        self.assertAlmostEqual(sc.binom_tail(1, 2, 0.5), 0.75)
        self.assertAlmostEqual(sc.binom_tail(0, 5, 0.3), 1.0)

    def test_census_pass(self):
        # p0 = max(5 / 500, 0.02) = 0.02; 10 / 50 = 0.2 >= 0.04; tail(10, 50, 0.02) ~ 1e-7
        ok, p = sc.census_test((10, 50), (5, 500))
        self.assertTrue(ok)
        self.assertLess(p, 1e-4)

    def test_census_fail_on_p(self):
        # 2 / 50 = 0.04 >= 0.04, but tail = 1 - 0.98^50 - 50 * 0.02 * 0.98^49 = 1 - 0.364170 - 0.371602
        ok, p = sc.census_test((2, 50), (5, 500))
        self.assertFalse(ok)
        self.assertAlmostEqual(p, 0.264228, places=4)

    def test_census_no_data(self):
        self.assertEqual(sc.census_test((0, 0), (5, 500)), (None, None))


class TestMast(unittest.TestCase):
    def test_parse(self):
        text = ("Kepler ID,Quarter,Skygroup_ID,Target Type\ninteger,integer,integer,ustring\n"
                "6359929,1,66,LC\n6359929,3,66,LC\n6359929,3,66,SC\n6034834,2,66,LC\n")
        self.assertEqual(sc.parse_mast(text), {6359929: (66, {1, 3}), 6034834: (66, {2})})

    def test_parse_junk(self):
        self.assertEqual(sc.parse_mast(""), {})
        self.assertEqual(sc.parse_mast("<html><body>no rows found</body></html>"), {})


class TestKoiRow(unittest.TestCase):
    SP = {1: (100.0, 500.0)}
    MAST = {1: (66, {1})}
    DR25 = {"K1": {"koi_pdisposition": "CANDIDATE", "koi_comment": "INDIV_TRANS_SKYE---X"},
            "K5": {"koi_pdisposition": "FALSE POSITIVE", "koi_comment": "INDIV_TRANS_MARSHALL_SKYE---CENT_FEW_DIFFS"}}

    def test_fails(self):
        # events 150 250 350 450 -> bins 18 118 218 318 (origin 131.5); bad bins 118 and 218 -> good 2 < 3
        r = sc.koi_row("K1", 1, "CANDIDATE", 100.0, 150.0, self.MAST, {66: {118, 218}}, self.DR25, self.SP)
        self.assertEqual((r["n_events"], r["n_flagged"], r["good"], r["eligible"], r["would_fail"]),
                         (4, 2, 2, 1, 1))
        self.assertEqual(r["flagged_times"], "250.0000 350.0000")
        self.assertEqual((r["in_dr25"], r["dr25_pc"], r["dr25_skye"], r["never_dr25"]), (1, 1, 1, 0))

    def test_skye_comment_with_other_flags(self):
        # v1 missed this group: SKYE after MARSHALL in the INDIV_TRANS comment
        r = sc.koi_row("K5", 1, "FALSE POSITIVE", 100.0, 150.0, self.MAST, {66: set()}, self.DR25, self.SP)
        self.assertEqual((r["in_dr25"], r["dr25_pc"], r["dr25_skye"], r["never_dr25"]), (1, 0, 1, 0))

    def test_passes(self):
        r = sc.koi_row("K2", 1, "CANDIDATE", 100.0, 150.0, self.MAST, {66: {118}}, self.DR25, self.SP)
        self.assertEqual((r["good"], r["would_fail"]), (3, 0))
        self.assertEqual((r["in_dr25"], r["dr25_pc"], r["dr25_skye"], r["never_dr25"]), (0, 0, 0, 1))

    def test_not_eligible(self):
        # P 300: events 150 and 450 only -> 2 events, not eligible, never counted as a Skye failure
        r = sc.koi_row("K3", 1, "CANDIDATE", 300.0, 150.0, self.MAST, {66: set()}, self.DR25, self.SP)
        self.assertEqual((r["n_events"], r["eligible"], r["would_fail"]), (2, 0, 0))

    def test_no_skygroup(self):
        r = sc.koi_row("K4", 2, "FALSE POSITIVE", 100.0, 150.0, self.MAST, {}, self.DR25, self.SP)
        self.assertEqual((r["status"], r["never_dr25"]), ("no_skygroup", 0))

    def test_group_stats(self):
        rows = [sc.koi_row("K1", 1, "CANDIDATE", 100.0, 150.0, self.MAST, {66: {118, 218}}, self.DR25, self.SP),
                sc.koi_row("K2", 1, "CANDIDATE", 100.0, 150.0, self.MAST, {66: {118}}, self.DR25, self.SP),
                sc.koi_row("K3", 1, "CANDIDATE", 300.0, 150.0, self.MAST, {66: set()}, self.DR25, self.SP)]
        self.assertEqual(sc.group_stats(rows, "never_dr25"),
                         {"n": 2, "with_flagged": 1, "flagged_fraction": 0.5, "eligible": 1, "fails": 0,
                          "fail_fraction": 0.0})


if __name__ == "__main__":
    unittest.main()
