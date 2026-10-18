"""Tests for skye_inv (Apache-2.0; MV2 of Munim, Inc.; made with AI). Expected values worked by hand."""
import unittest

import skye_inv as si

# Real rows of skye-census-v3's tce_skye.csv (csv module output, CRLF line ends), as in test_skye_diag
TCE_CSV = ("kepid,pn,period,t0,skygroup,n_events,n_flagged,n_flagged_v1bins,rv_found,rv_nitrans,rv_nrealtrans,"
           "rv_ngoodtrans,rv_skye,rv_comment_skye\r\n"
           "2304168,2,431.719,219.298,84,4,0,0,1,4,4,2,0,0\r\n"
           "893507,1,380.787,401.972,84,4,0,0,0,,,,,0\r\n")

# A header line and the first 13 columns of the first three rows of kplr_dr25_inv_tces.txt (read 2026-10-18), then
# two made-up rows that must be skipped: a KIC that differs from the TCE_ID, and a null period
INV_LINES = [
    "\\nrows = 19536",
    "|      TCE_ID|      KIC|  Disp| Score| NTL|  SS|  CO|  EM|      period|       epoch|Expected_MES|        MES|NTran|",
    " 000892667-01    892667     FP  0.000    1    0    0    0   2.26180947 131.74016724         null      7.9110   580",
    " 000892667-02    892667     FP  0.000    1    0    0    0 155.73335596 275.32133767         null     10.0871     3",
    " 000892667-03    892667     FP  0.000    1    0    1    0 114.54273462 205.27220685         null      9.6127     3",
    " 000892667-04    892668     FP  0.000    1    0    0    0  50.00000000 140.00000000         null      8.0000     3",
    " 000892667-05    892667     FP  0.000    1    0    0    0         null 140.00000000         null      8.0000     3",
    "",
]

# Made-up Robovetter input lines in the OBS layout (Data_Set TCE_ID KIC pn n_plan ntrans nrealt ngoodt iflag0-4);
# the INV input is not opened before the pre-registration is public
RV_LINES = [
    "\\     A flag that has a value of 1 if at least one transit event failed SKYE, else it is 0.",
    "|Data_Set|      TCE_ID|      KIC|  pn|n_plan|ntrans|nrealt|ngoodt|iflag0|iflag1|iflag2|iflag3|iflag4|",
    "INV 000892667-02 892667 2 3 3 3 2 0 0 1 1 0",
    "INV 000892667-03 892667 3 3 null null null 0 0 0 0 0",
    "INV 000892667-01 892667 1 3 580 571 570 0 0 0 0 0",
]
HEADER = ["\\ iflag3\n",
          "|Data_Set|      TCE_ID|      KIC|  pn|n_plan|ntrans|nrealt|ngoodt|iflag0|iflag1|iflag2|iflag3|iflag4|\n",
          "|    char|        char|      int| int|   int|   int|   int|   int|   int|   int|   int|   int|   int|\n"]


def tce(kid, pn, t0, found, skye=None):
    """A synthetic P = 100 d TCE; in quarter 1 alone it has exactly one event, at t0."""
    return {"kepid": kid, "pn": pn, "period": 100.0, "t0": t0, "rv_found": found,
            "nitrans": 1 if found else None, "nrealtrans": 1 if found else None, "skye": skye}


# As in test_skye_diag: skygroup 1, quarter 1 only: 33 rate bins (0..32). Three scored Skye TCEs in bin 5 (137.0),
# an unscored TCE (140.0) and a scored non-Skye TCE (140.2) in bin 8.
TCES = [tce(1, 1, 137.0, True, 1), tce(1, 2, 137.0, True, 1), tce(1, 3, 137.0, True, 1),
        tce(2, 1, 140.0, False), tce(3, 1, 140.2, True, 0)]
MAST = {1: (1, {1}), 2: (1, {1}), 3: (1, {1})}


class TestCopied(unittest.TestCase):
    """The functions copied from skye_diag 0.1.0 give skye_diag's hand-checked results."""

    def test_load(self):
        rows = si.load_tces(TCE_CSV)
        self.assertEqual(rows[0], {"kepid": 2304168, "pn": 2, "period": 431.719, "t0": 219.298, "rv_found": True,
                                   "nitrans": 4, "nrealtrans": 4, "skye": 0})
        self.assertFalse(rows[1]["rv_found"])

    def test_near_and_bins(self):
        self.assertTrue(si.near(1.05, [1.0, 2.0, 5.0], 0.1))
        self.assertFalse(si.near(3.5, [1.0, 2.0, 5.0], 0.5))
        self.assertEqual(si.data_bins([131.6, 131.9, 133.2]), {0, 1})
        self.assertEqual(si.rate_bins({1: si.QUARTERS[1]}), list(range(33)))

    def test_v3_style(self):
        out, rows = si.run_variant(TCES, MAST)
        self.assertEqual((out["tp"], out["fp"], out["fn"], out["tn"]), (3, 1, 0, 0))
        self.assertEqual((out["tces_compared"], out["bad_bins"], out["bin_events"]), (4, 2, 5))
        self.assertEqual(rows[-1], (1, 1, 1, 1, 0))

    def test_keep_and_only_bins(self):
        out, _ = si.run_variant(TCES, MAST, keep=lambda t: t < 139)
        self.assertEqual((out["tp"], out["fp"], out["fn"], out["tn"]), (3, 0, 0, 1))
        out, _ = si.run_variant(TCES, MAST, use_all=False, only_bins=set(range(33)) - {8})
        self.assertEqual((out["tp"], out["fp"], out["bad_bins"], out["bin_events"]), (3, 1, 2, 4))


class TestParse(unittest.TestCase):
    def test_inv_tces(self):
        self.assertEqual(si.parse_inv_tces(INV_LINES), [(892667, 1, 2.26180947, 131.74016724),
                                                        (892667, 2, 155.73335596, 275.32133767),
                                                        (892667, 3, 114.54273462, 205.27220685)])

    def test_rv_input(self):
        self.assertEqual(si.parse_rv_input(RV_LINES), {(892667, 2): (3, 3, 2, 1), (892667, 1): (580, 571, 570, 0)})

    def test_rv_names(self):
        names = si.rv_names(HEADER)
        self.assertEqual(len(names), 13)
        self.assertEqual((names[0], names[2], names[11]), ("Data_Set", "KIC", "iflag3"))
        self.assertTrue(si.names_ok(names))
        swapped = names[:10] + ["iflag3", "iflag2"] + names[12:]
        self.assertFalse(si.names_ok(swapped))
        self.assertEqual(si.rv_names([]), [])
        self.assertFalse(si.names_ok([]))

    def test_rv_output_and_comment(self):
        out = si.parse_rv_output(["000892667-02  0.000  FP  1  0  0  0  INDIV_TRANS_MARSHALL_SKYE---LPP_DV_TOO_HIGH"])
        self.assertTrue(si.has_skye(out[(892667, 2)]))
        self.assertFalse(si.has_skye("LPP_DV_TOO_HIGH---INDIV_TRANS_RUBBLE"))

    def test_tce_dicts(self):
        d = si.tce_dicts([(892667, 1, 2.26, 131.7), (892667, 2, 155.7, 275.3)], {(892667, 2): (3, 3, 2, 1)})
        self.assertEqual(d[0], {"kepid": 892667, "pn": 1, "period": 2.26, "t0": 131.7, "rv_found": False,
                                "nitrans": None, "nrealtrans": None, "ngoodtrans": None, "skye": None})
        self.assertEqual(d[1], {"kepid": 892667, "pn": 2, "period": 155.7, "t0": 275.3, "rv_found": True,
                                "nitrans": 3, "nrealtrans": 3, "ngoodtrans": 2, "skye": 1})


class TestGate(unittest.TestCase):
    def test_open(self):
        files = {si.PREREG: b"prereg", si.SELF: b"code\r\nline\r\n"}
        ok, detail = si.gate(b"code\nline\n", lambda p: files[p])
        self.assertTrue(ok)
        self.assertEqual(detail, {"prereg_live": True, "code_matches": True})

    def test_code_differs(self):
        files = {si.PREREG: b"prereg", si.SELF: b"code\n"}
        ok, detail = si.gate(b"other\n", lambda p: files[p])
        self.assertFalse(ok)
        self.assertFalse(detail["code_matches"])

    def test_prereg_missing_or_empty(self):
        ok, detail = si.gate(b"code\n", lambda p: {si.SELF: b"code\n"}[p])
        self.assertFalse(ok)
        self.assertIn("error", detail)
        ok, _ = si.gate(b"code\n", lambda p: {si.PREREG: b"", si.SELF: b"code\n"}[p])
        self.assertFalse(ok)


class TestScores(unittest.TestCase):
    def test_f1(self):
        # skye_diag 0.1.0 on OBS: chosen 7658 / 9468, scored_only 7584 / 9468
        chosen = {"tp": 3829, "fp": 1364, "fn": 446}
        scored_only = {"tp": 3792, "fp": 1401, "fn": 483}
        self.assertAlmostEqual(si.f1(chosen), 0.8088, places=4)
        self.assertAlmostEqual(si.f1(scored_only), 0.8010, places=4)
        self.assertGreater(si.f1(chosen), si.f1(scored_only))
        self.assertIsNone(si.f1({"tp": 0, "fp": 0, "fn": 0}))

    def test_data_check(self):
        base = {"inv_rows": 19536, "inv_long_rows": 1000, "inv_long_stars": 800, "stars_with_skygroup": 793,
                "rv_rows": 19341, "rv_names_ok": True, "rv_found": 991, "comment_skye_tces": 50,
                "comment_skye_with_flag_1": 50, "valid_cadences": 128918}
        self.assertTrue(si.data_check(base))
        for k, v in (("inv_rows", 19340), ("rv_rows", 19340), ("rv_names_ok", False), ("stars_with_skygroup", 791),
                     ("rv_found", 989), ("comment_skye_tces", 49), ("comment_skye_with_flag_1", 49),
                     ("valid_cadences", 128917), ("inv_long_rows", 0)):
            self.assertFalse(si.data_check(dict(base, **{k: v})), k)


if __name__ == "__main__":
    unittest.main()
