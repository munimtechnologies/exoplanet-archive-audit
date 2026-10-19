# Apache-2.0. Tests for scan_rubble 0.1.0 (pure functions only; no network). Made with AI agents, MV2 of Munim, Inc.
import math
import unittest

import scan_rubble as sr

CAD = sr.CADENCE_MIN / 1440.0


def ev(c1, c2):
    """An event from two {source: value} dicts given as (init, white, pdc, resid) tuples."""
    return {"cov1": dict(zip(sr.SOURCES, c1)), "cov2": dict(zip(sr.SOURCES, c2))}


# full; partial (real); not real (no LC_INIT cadence in transit)
EVENTS = [ev((1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0)),
          ev((0.4, 1.0, 0.4, 0.0), (0.6, 0.9, 0.6, 0.3)),
          ev((0.0, 0.5, 0.0, 0.0), (0.2, 0.6, 0.2, 0.0))]


class Coverage(unittest.TestCase):
    def test_expected_two_durations(self):
        # 2 * 2.94244 h * 60 / 29.4244 = 12 exactly
        self.assertAlmostEqual(sr.expected_cadences(2.94244), 12.0, places=9)

    def test_count_within_inclusive(self):
        valid = [0.0, 0.5, 1.0, 1.5, 2.0]
        self.assertEqual(sr.count_within(valid, 1.0, 0.5), 3)
        self.assertEqual(sr.count_within(valid, 1.0, 0.49), 1)
        self.assertEqual(sr.count_within([], 1.0, 0.5), 0)

    def test_eleven_of_twelve(self):
        valid = [k * CAD for k in range(-5, 6)]
        self.assertAlmostEqual(sr.coverage(valid, 0.0, 2.94244), 11.0 / 12.0, places=9)

    def test_zero_duration_is_nan(self):
        self.assertTrue(math.isnan(sr.coverage([1.0], 1.0, 0.0)))

    def test_event_coverage(self):
        # 3.0 h: one duration is +-0.0625 d, which holds |k| <= 3 (3 * 0.020434 = 0.0613): 7 cadences over
        # 180/29.4244 expected; two durations is +-0.125 d, which holds all 11 cadences over 360/29.4244 expected
        grid = [k * CAD for k in range(-5, 6)]
        e = sr.event_coverage({"init": grid, "white": grid, "pdc": [], "resid": [0.0]}, 0.0, 3.0)
        self.assertAlmostEqual(e["cov1"]["init"], 7.0 / (180.0 / 29.4244), places=9)
        self.assertAlmostEqual(e["cov2"]["white"], 11.0 / (360.0 / 29.4244), places=9)
        self.assertEqual(e["cov1"]["pdc"], 0.0)
        self.assertAlmostEqual(e["cov1"]["resid"], 1.0 / (180.0 / 29.4244), places=9)


class Events(unittest.TestCase):
    def test_inside_span(self):
        self.assertEqual(sr.events_in_span(100.0, 10.0, 95.0, 135.0), [100.0, 110.0, 120.0, 130.0])

    def test_epoch_after_span_start(self):
        self.assertEqual(sr.events_in_span(200.0, 10.0, 95.0, 135.0), [100.0, 110.0, 120.0, 130.0])

    def test_bad_period(self):
        self.assertEqual(sr.events_in_span(100.0, 0.0, 95.0, 135.0), [])


class Counts(unittest.TestCase):
    def test_real(self):
        self.assertEqual([sr.n_real(EVENTS, s) for s in sr.SOURCES], [2, 3, 2, 1])

    def test_fail(self):
        self.assertEqual(sr.n_fail(EVENTS, "init", 2, 0.75), 1)   # 0.6; the third event is not real
        self.assertEqual(sr.n_fail(EVENTS, "init", 2, 0.5), 0)
        self.assertEqual(sr.n_fail(EVENTS, "white", 2, 0.75), 0)  # 0.9
        self.assertEqual(sr.n_fail(EVENTS, "white", 1, 0.75), 0)
        self.assertEqual(sr.n_fail(EVENTS, "resid", 1, 0.25), 1)  # 0.0
        self.assertEqual(sr.n_fail(EVENTS, "pdc", 1, 0.5), 1)     # 0.4

    def test_tce_counts_keys(self):
        c = sr.tce_counts(EVENTS)
        self.assertEqual(len(c), 4 + 24)
        self.assertEqual(c["fail_init_2_0.75"], 1)
        self.assertEqual(c["nreal_white"], 3)

    def test_variant_names(self):
        names = sr.variant_names()
        self.assertEqual(len(names), 24)
        self.assertEqual(names[0], "init_1_0.25")
        self.assertEqual(names[5], "init_2_0.75")
        self.assertEqual(names[-1], "resid_2_0.75")


def row(pn, nrealt, ngoodt, iflags, nreal, fails):
    r = {"pn": pn, "nrealt": nrealt, "ngoodt": ngoodt, "iflags": iflags}
    r.update({"nreal_" + s: n for s, n in zip(sr.SOURCES, nreal)})
    r.update({"fail_" + v: 0 for v in sr.variant_names()})
    r.update(fails)
    return r


class Score(unittest.TestCase):
    def setUp(self):
        a = row(1, 2, 1, [1, 0, 0, 0, 0, 0], (2, 3, 2, 1), {"fail_init_2_0.75": 1})
        b = row(2, 3, 3, [0] * 6, (3, 3, 3, 3), {"fail_init_2_0.75": 1})
        self.res = sr.score([a, b])

    def test_nreal(self):
        self.assertEqual(self.res["n"], 2)
        self.assertEqual(self.res["nreal"]["init"], {"exact": 2, "within1": 2, "over": 0, "under": 0})
        self.assertEqual(self.res["nreal"]["white"], {"exact": 1, "within1": 2, "over": 0, "under": 0})
        self.assertEqual(self.res["nreal"]["resid"], {"exact": 1, "within1": 2, "over": 0, "under": 0})

    def test_literal_variant(self):
        v = self.res["variants"]["init_2_0.75"]
        self.assertEqual(v["all"], {"tp": 1, "fp": 1, "fn": 0, "tn": 0})
        self.assertEqual(v["pn1"], {"tp": 1, "fp": 0, "fn": 0, "tn": 0})
        self.assertEqual(v["pn>1"], {"tp": 0, "fp": 1, "fn": 0, "tn": 0})
        self.assertEqual(v["rubble_only"], {"n": 1, "exact": 1, "within1": 1})

    def test_silent_variant(self):
        v = self.res["variants"]["init_2_0.5"]
        self.assertEqual(v["all"], {"tp": 0, "fp": 0, "fn": 1, "tn": 1})
        self.assertEqual(v["rubble_only"], {"n": 1, "exact": 0, "within1": 1})


class Sample(unittest.TestCase):
    def test_split(self):
        kics = list(range(1, 31))
        dev, res = sr.draw_sample(kics, seed=7, n_dev=10, n_reserve=12, excluded=(3, 4))
        self.assertEqual((len(dev), len(res)), (10, 12))
        self.assertFalse(set(dev) & set(res))
        self.assertFalse({3, 4} & (set(dev) | set(res)))
        self.assertEqual(dev, sorted(dev))
        self.assertEqual((dev, res), sr.draw_sample(list(reversed(kics)) + [5, 5], seed=7, n_dev=10, n_reserve=12,
                                                    excluded=(3, 4)))

    def test_short_pool(self):
        dev, res = sr.draw_sample([1, 2, 3], seed=1, n_dev=2, n_reserve=5, excluded=())
        self.assertEqual((len(dev), len(res)), (2, 1))

    def test_default_excludes_probe_stars(self):
        self.assertIn(6922244, sr.LOOKED_UP)
        self.assertIn(11442793, sr.LOOKED_UP)


class Parsing(unittest.TestCase):
    def line(self):
        f = ["OBS", "000757450-01", "757450", "1", "1", "10", "9", "8", "1", "0", "0", "0", "0", "0"] + ["0"] * 9
        f += ["0", "0", "0.5"]
        f += ["8.88491", "0.0001", "134.52", "0.001", "2.5", "0.1", "0.3", "0.1", "500", "10", "480", "0.08", "1.0",
              "12.3", "0.5", "11.9"]
        f += ["0"] * (101 - len(f))
        return "  ".join(f)

    def test_row(self):
        r = sr.parse_rv_line(self.line())
        self.assertEqual((r["kic"], r["pn"], r["ntrans"], r["nrealt"], r["ngoodt"]), (757450, 1, 10, 9, 8))
        self.assertEqual(r["iflags"], [1, 0, 0, 0, 0, 0])
        self.assertAlmostEqual(r["epoch"], 134.52)
        self.assertAlmostEqual(r["duration"], 2.5)

    def test_header_and_comment_lines_skipped(self):
        self.assertIsNone(sr.parse_rv_line("\\name = Kepler DR25 Robovetter Input File"))
        self.assertIsNone(sr.parse_rv_line("|Data_Set|      TCE_ID|      KIC|"))
        self.assertIsNone(sr.parse_rv_line("# " + self.line()))
        self.assertIsNone(sr.parse_rv_line(""))

    def test_tce_number(self):
        self.assertEqual(sr.tce_number("TCE_7"), 7)
        self.assertEqual(sr.tce_number("TCE_12"), 12)
        self.assertIsNone(sr.tce_number("Statistics"))
        self.assertIsNone(sr.tce_number("PRIMARY"))


if __name__ == "__main__":
    unittest.main()
