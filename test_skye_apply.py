"""Tests for skye_apply (Apache-2.0; MV2 of Munim, Inc.; made with AI). Expected values worked by hand."""
import csv
import io
import unittest

import skye_apply as sa

# Real rows of skye-census-v3's tce_skye.csv (csv module output, CRLF line ends), as in test_skye_inv
TCE_CSV = ("kepid,pn,period,t0,skygroup,n_events,n_flagged,n_flagged_v1bins,rv_found,rv_nitrans,rv_nrealtrans,"
           "rv_ngoodtrans,rv_skye,rv_comment_skye\r\n"
           "2304168,2,431.719,219.298,84,4,0,0,1,4,4,2,0,0\r\n"
           "893507,1,380.787,401.972,84,4,0,0,0,,,,,0\r\n")

# The header and K05227.01's row of skye-census-v3's koi_skye.csv (already seen, as the pre-registration says)
KOI_CSV = ("kepoi_name,kepid,disposition,period,t0,skygroup,status,n_events,n_flagged,good,eligible,would_fail,"
           "in_dr25,dr25_pc,dr25_skye,never_dr25,flagged_times,event_times\r\n"
           "K05227.01,6034834,CANDIDATE,371.56492,259.8491,66,ok,3,1,2,1,1,0,0,0,1,1002.9789,"
           "631.4140 1002.9789 1374.5439\r\n")


def tce(kid, pn, t0, found, skye=None):
    """A synthetic P = 100 d TCE; in quarter 1 alone it has exactly one event, at t0."""
    return {"kepid": kid, "pn": pn, "period": 100.0, "t0": t0, "rv_found": found,
            "nitrans": 1 if found else None, "nrealtrans": 1 if found else None, "skye": skye}


# As in test_skye_inv: skygroup 1, quarter 1 only: 33 rate bins (0..32). Three scored Skye TCEs in bin 5 (137.0),
# an unscored TCE (140.0) and a scored non-Skye TCE (140.2) in bin 8.
TCES = [tce(1, 1, 137.0, True, 1), tce(1, 2, 137.0, True, 1), tce(1, 3, 137.0, True, 1),
        tce(2, 1, 140.0, False), tce(3, 1, 140.2, True, 0)]
MAST = {1: (1, {1}), 2: (1, {1}), 3: (1, {1})}


def koi(t0, events_text, kepid="1", skygroup="1", name="K00001.01"):
    """A synthetic koi_skye.csv row: P = 100 d, never scored by DR25."""
    return {"kepoi_name": name, "kepid": kepid, "disposition": "CANDIDATE", "period": "100.0", "t0": t0,
            "skygroup": skygroup, "would_fail": "0", "in_dr25": "0", "dr25_pc": "0", "dr25_skye": "0",
            "never_dr25": "1", "event_times": events_text}


# Quarters 1-3: a P = 100 d KOI with t0 = 137.0 has events 137.0 (bin 5), 237.0 (bin 105) and 337.0 (bin 205);
# with t0 = 150.0 it has 150.0 (bin 18) and 250.0 (bin 118), 350.0 falling after quarter 3 ends (349.50).
KOI_MAST = {1: (1, {1, 2, 3})}
BAD = {1: {5}}


class TestCopied(unittest.TestCase):
    """Functions copied from skye_inv 0.1.0 give skye_inv's hand-checked results."""

    def test_load(self):
        rows = sa.load_tces(TCE_CSV)
        self.assertEqual(rows[0], {"kepid": 2304168, "pn": 2, "period": 431.719, "t0": 219.298, "rv_found": True,
                                   "nitrans": 4, "nrealtrans": 4, "skye": 0})
        self.assertFalse(rows[1]["rv_found"])

    def test_near_and_bins(self):
        self.assertTrue(sa.near(1.05, [1.0, 2.0, 5.0], 0.1))
        self.assertFalse(sa.near(3.5, [1.0, 2.0, 5.0], 0.5))
        self.assertEqual(sa.data_bins([131.6, 131.9, 133.2]), {0, 1})
        self.assertEqual(sa.rate_bins({1: sa.QUARTERS[1]}), list(range(33)))

    def test_run_variant(self):
        out, _ = sa.run_variant(TCES, MAST, use_all=False, only_bins=set(range(33)) - {8})
        self.assertEqual((out["tp"], out["fp"], out["bad_bins"], out["bin_events"]), (3, 1, 2, 4))


class TestFrozenBins(unittest.TestCase):
    """frozen_bins gives the bins run_variant uses, so frozen_confusion gives run_variant's counts."""

    def test_scored_only(self):
        # counts {5: 3, 8: 1} over 33 rate bins: R = 4/33, cutoff 1.166 drops bin 5; R = 1/32, cutoff 0.562 drops
        # bin 8; then R = 0 and the cutoff is 0, so both bins are bad. The unscored TCE (140.0) is not counted.
        bad = sa.frozen_bins(TCES, MAST)
        self.assertEqual(bad, {1: {5, 8}})
        c = sa.frozen_confusion(TCES, MAST, bad)
        out, _ = sa.run_variant(TCES, MAST, use_all=False)
        self.assertEqual((c["tp"], c["fp"], c["fn"], c["tn"]), (3, 1, 0, 0))
        self.assertEqual(c, {k: out[k] for k in c})

    def test_keep(self):
        # 140.2 dropped: counts {5: 3}, R = 3/33, cutoff 0.995, then 0: bin 5 bad; TCE (3, 1) has no kept event
        keep = lambda t: t < 139
        bad = sa.frozen_bins(TCES, MAST, keep=keep)
        self.assertEqual(bad, {1: {5}})
        c = sa.frozen_confusion(TCES, MAST, bad, keep=keep)
        out, _ = sa.run_variant(TCES, MAST, use_all=False, keep=keep)
        self.assertEqual((c["tp"], c["fp"], c["fn"], c["tn"]), (3, 0, 0, 1))
        self.assertEqual(c, {k: out[k] for k in c})

    def test_only_bins(self):
        # bin 8 out of the rate: R = 3/32, cutoff 1.012, then 0; bin 8 (count 1) is still above it, so bad
        self.assertEqual(sa.frozen_bins(TCES, MAST, only_bins=set(range(33)) - {8}), {1: {5, 8}})


class TestApplyKoi(unittest.TestCase):
    def test_fails(self):
        r = sa.apply_koi(koi("137.0", "137.0000 237.0000 337.0000"), KOI_MAST, BAD)
        self.assertEqual({k: r[k] for k in ("skygroup", "status", "n_events", "n_kept", "n_flagged", "good",
                                            "eligible", "would_fail", "v3_would_fail", "never_dr25", "events_match",
                                            "flagged_times", "kept_times")},
                         {"skygroup": 1, "status": "ok", "n_events": 3, "n_kept": 3, "n_flagged": 1, "good": 2,
                          "eligible": 1, "would_fail": 1, "v3_would_fail": 0, "never_dr25": 1, "events_match": 1,
                          "flagged_times": "137.0000", "kept_times": "137.0000 237.0000 337.0000"})

    def test_keep_makes_ineligible(self):
        r = sa.apply_koi(koi("137.0", "137.0000 237.0000 337.0000"), KOI_MAST, BAD, keep=lambda t: t < 300)
        self.assertEqual((r["n_events"], r["n_kept"], r["n_flagged"], r["good"], r["eligible"], r["would_fail"]),
                         (3, 2, 1, 1, 0, 0))

    def test_mismatch_and_missing(self):
        self.assertEqual(sa.apply_koi(koi("137.0", "137.0000 237.0000"), KOI_MAST, BAD)["events_match"], 0)
        self.assertEqual(sa.apply_koi(koi("137.0", "137.0000 237.0000 337.0000", skygroup="2"), KOI_MAST,
                                      BAD)["events_match"], 0)
        r = sa.apply_koi(koi("137.0", "", kepid="9"), KOI_MAST, BAD)
        self.assertEqual((r["status"], r["events_match"], r["would_fail"]), ("no_skygroup", 0, ""))

    def test_real_row(self):
        # K05227.01 with every quarter: events in Q7, Q11, Q15 as v3 wrote them; bin of 1002.9789 is 871
        row = next(csv.DictReader(io.StringIO(KOI_CSV)))
        r = sa.apply_koi(row, {6034834: (66, set(range(1, 18)))}, {66: {871}})
        self.assertEqual((r["events_match"], r["n_kept"], r["n_flagged"], r["good"], r["would_fail"],
                          r["v3_would_fail"], r["flagged_times"]), (1, 3, 1, 2, 1, 1, "1002.9789"))


class TestGroupsAndCensus(unittest.TestCase):
    def test_group_stats(self):
        rows = [sa.apply_koi(koi("137.0", "137.0000 237.0000 337.0000"), KOI_MAST, BAD),
                sa.apply_koi(koi("150.0", "150.0000 250.0000", name="K00002.01"), KOI_MAST, BAD)]
        self.assertEqual(rows[1]["events_match"], 1)
        self.assertEqual(sa.group_stats(rows, "never_dr25"),
                         {"n": 2, "with_flagged": 1, "flagged_fraction": 0.5, "eligible": 1, "fails": 1,
                          "fail_fraction": 1.0})
        self.assertEqual(sa.group_stats(rows, "dr25_pc"),
                         {"n": 0, "with_flagged": 0, "flagged_fraction": None, "eligible": 0, "fails": 0,
                          "fail_fraction": None})

    def test_census(self):
        # v3's P8 numbers: 22 / 415 against max(7 / 668, 0.02) = 0.02, published p = 4.5e-5
        passed, p = sa.census_test((22, 415), (7, 668))
        self.assertTrue(passed)
        self.assertTrue(0 < p < 1e-4)
        # 5 / 100 is 2.5 x 0.02, but P(X >= 5 | n = 100, p = 0.02) = 0.0508 > 0.01
        self.assertFalse(sa.census_test((5, 100), (1, 100))[0])
        self.assertEqual(sa.census_test((1, 0), (0, 5)), (None, None))


class TestRobnik(unittest.TestCase):
    def test_names(self):
        self.assertEqual(sa.koi_name("5269.01"), "K05269.01")
        self.assertEqual(sa.koi_name("70.1"), "K00070.10")
        rows = sa.read_table("kepid\tKOI\n6359929\t5269.01\n")
        self.assertEqual(rows, [{"kepid": "6359929", "KOI": "5269.01"}])
        self.assertEqual(sa.robnik_names(rows), {"K05269.01"})

    def test_population(self):
        per_star = sa.planets_per_star([{"kepid": "1", "koi_disposition": "CANDIDATE"},
                                        {"kepid": "1", "koi_disposition": "FALSE POSITIVE"},
                                        {"kepid": "2", "koi_disposition": "CONFIRMED"},
                                        {"kepid": "2", "koi_disposition": "CANDIDATE"}])
        self.assertEqual(per_star, {"1": 1, "2": 2})
        a = sa.apply_koi(koi("137.0", "137.0000 237.0000 337.0000"), KOI_MAST, BAD)
        b = sa.apply_koi(koi("150.0", "150.0000 250.0000", name="K00002.01"), KOI_MAST, BAD)
        self.assertEqual(sa.population([a, b], per_star), [a])
        self.assertEqual(sa.population([a], {"1": 2}), [])
        self.assertEqual(sa.population([a], per_star, excluded={"K00001.01"}), [])

    def test_fisher_compare_scored(self):
        self.assertAlmostEqual(sa.fisher_greater(1, 0, 0, 1), 0.5)
        self.assertAlmostEqual(sa.fisher_greater(2, 0, 0, 2), 1 / 6)
        rows = [{"kepoi_name": "K1", "period": "350", "would_fail": 1},
                {"kepoi_name": "K2", "period": "100", "would_fail": 1},
                {"kepoi_name": "K3", "period": "360", "would_fail": 0},
                {"kepoi_name": "K4", "period": "100", "would_fail": 0}]
        main = sa.compare(rows, {"K1"})
        self.assertEqual((main["n_fail"], main["fail_listed"], main["n_pass"], main["pass_listed"]), (2, 1, 2, 0))
        self.assertAlmostEqual(main["p_one_sided"], 0.5)
        win = sa.compare(rows, {"K1"}, *sa.RB_WINDOW)
        self.assertEqual((win["n_fail"], win["fail_listed"], win["n_pass"], win["pass_listed"]), (1, 1, 1, 0))
        self.assertEqual(sa.scored(main, win),
                         {"q1_enough_fails": False, "q2_enrichment": False, "q3_window_direction": True})


class TestChecks(unittest.TestCase):
    def test_data_check(self):
        base = {"koi_rows": 2257, "koi_with_skygroup": 2257, "events_match": 2257, "valid_cadences": 128918}
        self.assertTrue(sa.data_check(base))
        for k, v in (("koi_rows", 2256), ("koi_with_skygroup", 2256), ("events_match", 2256),
                     ("valid_cadences", 128917)):
            self.assertFalse(sa.data_check(dict(base, **{k: v})), k)

    def test_robnik_check(self):
        self.assertTrue(sa.robnik_check({"robnik_rows": 406, "cumulative_sha256_ok": True}))
        self.assertFalse(sa.robnik_check({"robnik_rows": 405, "cumulative_sha256_ok": True}))
        self.assertFalse(sa.robnik_check({"robnik_rows": 406, "cumulative_sha256_ok": False}))


class TestGate(unittest.TestCase):
    def test_open(self):
        files = {sa.PREREG: b"prereg", sa.SELF: b"code\r\nline\r\n"}
        ok, detail = sa.gate(b"code\nline\n", lambda p: files[p])
        self.assertTrue(ok)
        self.assertEqual(detail, {"prereg_live": True, "code_matches": True})

    def test_code_differs(self):
        files = {sa.PREREG: b"prereg", sa.SELF: b"code\n"}
        ok, detail = sa.gate(b"other\n", lambda p: files[p])
        self.assertFalse(ok)
        self.assertFalse(detail["code_matches"])

    def test_prereg_missing(self):
        ok, detail = sa.gate(b"code\n", lambda p: {sa.SELF: b"code\n"}[p])
        self.assertFalse(ok)
        self.assertIn("error", detail)


if __name__ == "__main__":
    unittest.main()
