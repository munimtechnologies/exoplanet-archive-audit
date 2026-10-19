# Apache-2.0. Tests for probe_rubble 0.1.0 (pure functions only; no network). Made with AI agents, MV2 of Munim, Inc.
import unittest

import probe_rubble as pr


class Cadences(unittest.TestCase):
    def test_expected_two_durations(self):
        # 2 * 2.94244 h * 60 / 29.4244 = 12 exactly
        self.assertAlmostEqual(pr.expected_cadences(2.94244), 12.0, places=9)

    def test_expected_one_duration(self):
        self.assertAlmostEqual(pr.expected_cadences(2.0, 1.0), 120.0 / 29.4244, places=9)

    def test_count_within_inclusive(self):
        valid = [0.0, 0.5, 1.0, 1.5, 2.0]
        self.assertEqual(pr.count_within(valid, 1.0, 0.5), 3)
        self.assertEqual(pr.count_within(valid, 1.0, 0.49), 1)
        self.assertEqual(pr.count_within(valid, 5.0, 0.5), 0)
        self.assertEqual(pr.count_within([], 1.0, 0.5), 0)


class Rubble(unittest.TestCase):
    def test_eleven_of_twelve(self):
        cad = pr.CADENCE_MIN / 1440.0
        valid = [k * cad for k in range(-5, 6)]  # 11 cadences; window +-0.1226 d holds |k| <= 6
        self.assertAlmostEqual(pr.rubble(valid, 0.0, 2.94244), 11.0 / 12.0, places=9)

    def test_in_transit_fraction(self):
        cad = pr.CADENCE_MIN / 1440.0
        valid = [k * cad for k in range(-5, 6)]
        # one duration of 2.0 h: half-width 1/24 d holds |k| <= 2 -> 5 cadences over 120/29.4244 expected
        self.assertAlmostEqual(pr.rubble(valid, 0.0, 2.0, 1.0), 5.0 / (120.0 / 29.4244), places=9)

    def test_empty_is_zero(self):
        self.assertEqual(pr.rubble([], 10.0, 3.0), 0.0)

    def test_zero_duration_is_nan(self):
        import math
        self.assertTrue(math.isnan(pr.rubble([1.0], 1.0, 0.0)))


class Events(unittest.TestCase):
    def test_inside_span(self):
        self.assertEqual(pr.events_in_span(100.0, 10.0, 95.0, 135.0), [100.0, 110.0, 120.0, 130.0])

    def test_inclusive_ends(self):
        self.assertEqual(pr.events_in_span(100.0, 10.0, 100.0, 130.0), [100.0, 110.0, 120.0, 130.0])

    def test_epoch_after_span_start(self):
        self.assertEqual(pr.events_in_span(200.0, 10.0, 95.0, 135.0), [100.0, 110.0, 120.0, 130.0])

    def test_bad_period(self):
        self.assertEqual(pr.events_in_span(100.0, 0.0, 95.0, 135.0), [])


class Rules(unittest.TestCase):
    def test_trans_gapped(self):
        self.assertTrue(pr.trans_gapped(5, 10))
        self.assertFalse(pr.trans_gapped(6, 10))
        self.assertFalse(pr.trans_gapped(0, 0))

    def test_labels(self):
        self.assertEqual(pr.label(3, pr.NTRANS_BINS), "ntrans3-5")
        self.assertEqual(pr.label(100, pr.NTRANS_BINS), "ntrans21-100")
        self.assertEqual(pr.label(101, pr.NTRANS_BINS), "ntrans>100")
        self.assertEqual(pr.label(45.0, pr.PERIOD_BINS), "10-45d")
        self.assertEqual(pr.label(45.01, pr.PERIOD_BINS), "45-200d")
        self.assertEqual(pr.label(0.5, pr.PERIOD_BINS), "P<10d")


def synthetic_line():
    f = ["OBS", "000757450-01", "757450", "1", "1", "10", "9", "8", "1", "0", "0", "0", "0", "0"] + ["0"] * 9
    f += ["0", "0", "0.5"]
    f += ["8.88491", "0.0001", "134.52", "0.001", "2.5", "0.1", "0.3", "0.1", "500", "10", "480", "0.08", "1.0",
          "12.3", "0.5", "11.9"]
    f += ["0"] * (101 - len(f))
    assert len(f) == 101
    return "  ".join(f)


class Parsing(unittest.TestCase):
    def test_row(self):
        r = pr.parse_rv_line(synthetic_line())
        self.assertEqual((r["kic"], r["pn"], r["n_plan"], r["ntrans"], r["nrealt"], r["ngoodt"]), (757450, 1, 1, 10, 9, 8))
        self.assertEqual(r["iflags"], [1, 0, 0, 0, 0, 0])
        self.assertAlmostEqual(r["period"], 8.88491)
        self.assertAlmostEqual(r["epoch"], 134.52)
        self.assertAlmostEqual(r["duration"], 2.5)
        self.assertAlmostEqual(r["mes"], 12.3)
        self.assertAlmostEqual(r["new_mes"], 11.9)

    def test_header_lines_skipped(self):
        self.assertIsNone(pr.parse_rv_line("\\name = Kepler DR25 Robovetter Input File"))
        self.assertIsNone(pr.parse_rv_line("|Data_Set|      TCE_ID|      KIC|"))
        self.assertIsNone(pr.parse_rv_line(""))
        self.assertIsNone(pr.parse_rv_line("OBS 000757450-01 757450 1"))

    def test_listing(self):
        html = ('<a href="kplr006359929-20160209194854_dvt.fits">x</a> <a href="kplr006359929-20160209194854_dvr.pdf">'
                '</a> <a href="kplr006359929-20160209194854_dvt.fits">again</a>')
        self.assertEqual(pr.dvt_names_from_listing(html), ["kplr006359929-20160209194854_dvt.fits"])


class Stats(unittest.TestCase):
    def test_two_rows(self):
        a = {"kic": 1, "pn": 1, "n_plan": 2, "ntrans": 10, "nrealt": 9, "ngoodt": 8, "iflags": [1, 0, 0, 0, 0, 0],
             "period": 5.0, "epoch": 0.0, "duration": 2.0, "mes": 10.0, "new_mes": 10.0}
        b = {"kic": 1, "pn": 2, "n_plan": 2, "ntrans": 4, "nrealt": 2, "ngoodt": 2, "iflags": [0] * 6,
             "period": 300.0, "epoch": 0.0, "duration": 5.0, "mes": 8.0, "new_mes": 6.0}
        st = pr.iflag_stats([a, b])
        self.assertEqual(st["rows"], 2)
        self.assertEqual(st["iflag_any"], [1, 0, 0, 0, 0, 0])
        self.assertEqual(st["iflag0_by_pn"], {"pn1": [1, 1], "pn>1": [0, 1]})
        self.assertEqual(st["iflag0_by_period"], {"P<10d": [1, 1], "P>200d": [0, 1]})
        self.assertEqual(st["iflag0_by_ntrans"], {"ntrans6-20": [1, 1], "ntrans3-5": [0, 1]})
        self.assertEqual(st["ntrans_gt_nrealt"], [1, 2])
        self.assertEqual(st["ngoodt_lt_nrealt"], [1, 1])
        self.assertEqual(st["ngoodt_lt_nrealt_no_iflag"], 0)
        self.assertEqual(st["iflag0_and_ntrans_eq_nrealt"], 0)
        self.assertEqual(st["trans_gapped"], 1)
        self.assertEqual(st["rubble_only_flag"], {"tces": 1, "removed_hist": {"1": 1}})
        self.assertEqual((st["ngoodt_lt3"], st["new_mes_lt_7p1"], st["indiv_trans_fail"]), (1, 1, 1))


if __name__ == "__main__":
    unittest.main()
