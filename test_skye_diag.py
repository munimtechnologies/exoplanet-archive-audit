"""Tests for skye_diag (Apache-2.0; MV2 of Munim, Inc.; made with AI). Expected values worked by hand."""
import unittest

import skye_diag as sd

# Real rows of skye-census-v3's tce_skye.csv and skygroups.csv (csv module output, CRLF line ends)
TCE_CSV = ("kepid,pn,period,t0,skygroup,n_events,n_flagged,n_flagged_v1bins,rv_found,rv_nitrans,rv_nrealtrans,"
           "rv_ngoodtrans,rv_skye,rv_comment_skye\r\n"
           "2304168,2,431.719,219.298,84,4,0,0,1,4,4,2,0,0\r\n"
           "893507,1,380.787,401.972,84,4,0,0,0,,,,,0\r\n"
           "892376,6,64.5178,188.638,84,22,1,1,1,22,6,1,1,1\r\n")
SG_CSV = ("kepid,skygroup,lc_quarters\r\n"
          "892376,84,1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17\r\n"
          "893507,84,2 3 4 6 7 8 10 11 12 14 15 16\r\n")


def tce(kid, pn, t0, found, skye=None):
    """A synthetic P = 100 d TCE; in quarter 1 alone it has exactly one event, at t0."""
    return {"kepid": kid, "pn": pn, "period": 100.0, "t0": t0, "rv_found": found,
            "nitrans": 1 if found else None, "nrealtrans": 1 if found else None, "skye": skye}


# Skygroup 1, quarter 1 only: 33 rate bins (0..32). Three scored Skye TCEs in bin 5 (137.0), an unscored TCE
# (140.0) and a scored non-Skye TCE (140.2) in bin 8.
TCES = [tce(1, 1, 137.0, True, 1), tce(1, 2, 137.0, True, 1), tce(1, 3, 137.0, True, 1),
        tce(2, 1, 140.0, False), tce(3, 1, 140.2, True, 0)]
MAST = {1: (1, {1}), 2: (1, {1}), 3: (1, {1})}


class TestLoad(unittest.TestCase):
    def test_tces(self):
        rows = sd.load_tces(TCE_CSV)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], {"kepid": 2304168, "pn": 2, "period": 431.719, "t0": 219.298, "rv_found": True,
                                   "nitrans": 4, "nrealtrans": 4, "skye": 0})
        self.assertEqual(rows[1], {"kepid": 893507, "pn": 1, "period": 380.787, "t0": 401.972, "rv_found": False,
                                   "nitrans": None, "nrealtrans": None, "skye": None})
        self.assertEqual((rows[2]["nitrans"], rows[2]["nrealtrans"], rows[2]["skye"]), (22, 6, 1))

    def test_skygroups(self):
        m = sd.load_skygroups(SG_CSV)
        self.assertEqual(m[892376], (84, set(range(1, 18))))
        self.assertEqual(m[893507], (84, {2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16}))


class TestNear(unittest.TestCase):
    def test_near(self):
        valid = [1.0, 2.0, 5.0]
        self.assertTrue(sd.near(1.05, valid, 0.1))
        self.assertFalse(sd.near(3.5, valid, 0.5))
        self.assertTrue(sd.near(4.6, valid, 0.5))
        self.assertFalse(sd.near(10.0, valid, 4.9))
        self.assertTrue(sd.near(10.0, valid, 5.0))
        self.assertTrue(sd.near(0.5, valid, 0.5))
        self.assertFalse(sd.near(0.0, [], 1.0))

    def test_data_bins(self):
        self.assertEqual(sd.data_bins([131.6, 131.9, 133.2]), {0, 1})


class TestVariant(unittest.TestCase):
    def test_rate_bins_quarter_1(self):
        self.assertEqual(sd.rate_bins({1: sd.QUARTERS[1]}), list(range(33)))

    def test_v3_style(self):
        # 5 events in 33 bins: R = 0.1515, cutoff 1.319; bins 5 (3) and 8 (2) drop, then R = 0, cutoff 0
        out, rows = sd.run_variant(TCES, MAST)
        self.assertEqual((out["tp"], out["fp"], out["fn"], out["tn"]), (3, 1, 0, 0))
        self.assertEqual((out["recall"], out["precision"]), (1.0, 0.75))
        self.assertEqual((out["tces_compared"], out["bad_bins"], out["bin_events"]), (4, 2, 5))
        self.assertEqual((out["events_equal_nitrans"], out["events_equal_nrealtrans"]), (1.0, 1.0))
        self.assertEqual(rows[-1], (1, 1, 1, 1, 0))

    def test_scored_only(self):
        # the unscored TCE no longer counts; bin 8 holds 1, still above the final cutoff of 0
        out, _ = sd.run_variant(TCES, MAST, use_all=False)
        self.assertEqual((out["tp"], out["fp"], out["bad_bins"], out["bin_events"]), (3, 1, 2, 4))

    def test_keep(self):
        # events after 139 are dropped: only bin 5 (3) remains; the 140.2 TCE has no event left
        out, rows = sd.run_variant(TCES, MAST, keep=lambda t: t < 139)
        self.assertEqual((out["tp"], out["fp"], out["fn"], out["tn"]), (3, 0, 0, 1))
        self.assertEqual((out["bad_bins"], out["bin_events"], out["events_equal_nrealtrans"]), (1, 3, 0.75))
        self.assertEqual(rows[-1], (0, 1, 1, 0, 0))

    def test_only_bins(self):
        # bin 8 leaves the rate bins but is still tested against the cutoff
        out, _ = sd.run_variant(TCES, MAST, only_bins=set(range(33)) - {8})
        self.assertEqual((out["tp"], out["fp"], out["bad_bins"]), (3, 1, 2))

    def test_missing_star(self):
        out, _ = sd.run_variant(TCES + [tce(9, 1, 150.0, True, 1)], MAST)
        self.assertEqual(out["tces_compared"], 4)


class TestByEventCount(unittest.TestCase):
    def test_split(self):
        rows = [(4, 4, 4, 1, 1), (5, 5, 4, 1, 0), (3, 4, 4, 0, 1), (4, 4, 4, 0, 0)]
        g = sd.by_event_count(rows)
        self.assertEqual((g["equal"]["n"], g["equal"]["tp"], g["equal"]["tn"]), (2, 1, 1))
        self.assertEqual((g["more"]["fp"], g["more"]["recall"], g["more"]["precision"]), (1, None, 0.0))
        self.assertEqual((g["fewer"]["fn"], g["fewer"]["recall"], g["fewer"]["precision"]), (1, 0.0, None))


if __name__ == "__main__":
    unittest.main()
