# Apache-2.0. Tests for pick_variant 0.1.0, MV2 of Munim, Inc. Made with AI agents. Every expected value is hand-worked.
import json
import unittest

import pick_variant as pv


def stats(tp, fp, fn, tn, ro_n=12, ro_exact=4):
    zero = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    return {"all": {"tp": tp, "fp": fp, "fn": fn, "tn": tn}, "pn1": dict(zero), "pn>1": dict(zero),
            "rubble_only": {"n": ro_n, "exact": ro_exact, "within1": ro_n}}


def make_res(n=100, nreal_exact=80, overrides=None):
    """All 24 variants at tp 25, fp 15, fn 15, tn 45 (error 30 of 100), 40 flagged, 12 Rubble-only (4 exact)."""
    res = {"n": n, "nreal": {s: {"exact": nreal_exact, "within1": n, "over": 0, "under": 0} for s in pv.SOURCES},
           "variants": {name: stats(25, 15, 15, 45) for name in pv.variant_names()}}
    for name, st in (overrides or {}).items():
        res["variants"][name] = st
    return res


class Names(unittest.TestCase):
    def test_variant_names(self):
        names = pv.variant_names()
        self.assertEqual(len(names), 24)
        self.assertEqual(names[0], "init_1_0.25")
        self.assertEqual(names[-1], "resid_2_0.75")
        self.assertEqual(len(set(names)), 24)

    def test_parse_variant(self):
        self.assertEqual(pv.parse_variant("white_2_0.75"), ("white", 2, 0.75))
        self.assertEqual(pv.parse_variant("init_1_0.25"), ("init", 1, 0.25))
        for name in pv.variant_names():  # round trip
            s, w, t = pv.parse_variant(name)
            self.assertEqual("{}_{}_{}".format(s, w, t), name)


class Arithmetic(unittest.TestCase):
    def test_tolerance_integer_ceil(self):
        # ceil(min_error / 10), at least 1; 30 must give 3 (0.1 * 30 is 3.0000000000000004 in floats)
        self.assertEqual([pv.tolerance(x) for x in (0, 9, 10, 11, 25, 30, 31)], [1, 1, 1, 2, 3, 3, 4])

    def test_ratio_zero_denominator(self):
        self.assertEqual(pv.ratio(0, 0), 0.0)
        self.assertEqual(pv.ratio(3, 4), 0.75)

    def test_error_and_flagged(self):
        v = stats(35, 5, 5, 55)
        self.assertEqual(pv.error(v), 10)
        self.assertEqual(pv.flagged(v), 40)


class Decide(unittest.TestCase):
    def test_negative_when_every_variant_is_above_20_percent(self):
        d = pv.decide(make_res())  # every variant error 30 of 100
        self.assertEqual(d["status"], "negative")
        self.assertEqual(d["best_error_rate"], 0.3)
        self.assertNotIn("chosen", d)
        self.assertEqual(d["flagged"], 40)
        self.assertEqual(d["rubble_only_n"], 12)

    def test_exactly_20_percent_is_not_negative(self):
        d = pv.decide(make_res(overrides={"init_2_0.75": stats(30, 10, 10, 50)}))  # error 20 of 100
        self.assertEqual(d["status"], "chosen")
        self.assertEqual(d["chosen"], "init_2_0.75")
        self.assertEqual(d["how"]["min_error"], 20)
        self.assertEqual(d["how"]["tolerance"], 2)
        self.assertEqual(d["how"]["candidates"], ["init_2_0.75"])

    def test_single_winner_rates_and_bars(self):
        d = pv.decide(make_res(overrides={"init_2_0.75": stats(35, 5, 5, 55, ro_exact=9)}))
        self.assertEqual(d["status"], "chosen")
        self.assertEqual(d["chosen"], "init_2_0.75")
        self.assertEqual(d["how"], {"min_error": 10, "tolerance": 1, "candidates": ["init_2_0.75"],
                                    "restricted_to_0.75": True})
        # recall 35/40, precision 35/40, Rubble-only 9/12, nrealt exact 80/100
        self.assertEqual(d["dev_rates"], {"recall": 0.875, "precision": 0.875, "rubble_only_exact": 0.75,
                                          "nreal_exact": 0.8})
        self.assertEqual(d["bars"], {"recall": 0.775, "precision": 0.775, "rubble_only_exact": 0.6,
                                     "nreal_exact": 0.7})
        self.assertEqual(d["error_rates"]["init_2_0.75"], 0.1)
        self.assertEqual(d["error_rates"]["resid_1_0.25"], 0.3)
        json.dumps(d)  # serialisable

    def test_threshold_0_75_beats_a_better_rubble_only_count_within_tolerance(self):
        d = pv.decide(make_res(overrides={"init_2_0.5": stats(37, 7, 3, 53, ro_exact=9),      # error 10
                                          "white_2_0.75": stats(34, 5, 6, 55, ro_exact=5)}))  # error 11
        self.assertEqual(d["how"]["candidates"], ["init_2_0.5", "white_2_0.75"])
        self.assertTrue(d["how"]["restricted_to_0.75"])
        self.assertEqual(d["chosen"], "white_2_0.75")

    def test_outside_tolerance_is_not_a_candidate(self):
        d = pv.decide(make_res(overrides={"init_2_0.5": stats(37, 7, 3, 53, ro_exact=9),      # error 10
                                          "white_2_0.75": stats(34, 6, 6, 54, ro_exact=5)}))  # error 12 > 11
        self.assertEqual(d["how"]["candidates"], ["init_2_0.5"])
        self.assertFalse(d["how"]["restricted_to_0.75"])
        self.assertEqual(d["chosen"], "init_2_0.5")

    def test_most_rubble_only_exact_wins_before_window(self):
        d = pv.decide(make_res(overrides={"init_2_0.75": stats(35, 5, 5, 55, ro_exact=6),
                                          "pdc_2_0.75": stats(35, 5, 5, 55, ro_exact=6),
                                          "white_1_0.75": stats(35, 5, 5, 55, ro_exact=7)}))
        self.assertEqual(d["chosen"], "white_1_0.75")

    def test_tie_goes_to_source_order(self):
        d = pv.decide(make_res(overrides={"pdc_2_0.75": stats(35, 5, 5, 55, ro_exact=6),
                                          "init_2_0.75": stats(35, 5, 5, 55, ro_exact=6)}))
        self.assertEqual(d["chosen"], "init_2_0.75")

    def test_tie_goes_to_window_2_before_source(self):
        d = pv.decide(make_res(overrides={"init_1_0.75": stats(35, 5, 5, 55, ro_exact=6),
                                          "pdc_2_0.75": stats(35, 5, 5, 55, ro_exact=6)}))
        self.assertEqual(d["chosen"], "pdc_2_0.75")

    def test_without_0_75_candidates_higher_threshold_wins_ties(self):
        d = pv.decide(make_res(overrides={"white_2_0.25": stats(37, 7, 3, 53, ro_exact=6),
                                          "init_2_0.5": stats(37, 7, 3, 53, ro_exact=6)}))
        self.assertFalse(d["how"]["restricted_to_0.75"])
        self.assertEqual(d["chosen"], "init_2_0.5")

    def test_underpowered_too_few_flagged(self):
        res = make_res(overrides={name: stats(5, 15, 5, 75) for name in pv.variant_names()})  # 10 flagged
        d = pv.decide(res)
        self.assertEqual(d["status"], "underpowered_dev")
        self.assertEqual(d["flagged"], 10)
        self.assertNotIn("chosen", d)

    def test_underpowered_too_few_rubble_only(self):
        res = make_res(overrides={name: stats(35, 5, 5, 55, ro_n=5, ro_exact=5) for name in pv.variant_names()})
        d = pv.decide(res)
        self.assertEqual(d["status"], "underpowered_dev")
        self.assertEqual(d["rubble_only_n"], 5)

    def test_empty_scan(self):
        self.assertEqual(pv.decide({"n": 0, "nreal": {}, "variants": {}})["status"], "underpowered_dev")
        self.assertEqual(pv.decide({})["status"], "underpowered_dev")


class Reserve(unittest.TestCase):
    def decision(self):
        return pv.decide(make_res(overrides={"init_2_0.75": stats(35, 5, 5, 55, ro_exact=9)}))

    def test_reserve_pass(self):
        res = make_res(n=200, nreal_exact=170,
                       overrides={"init_2_0.75": stats(70, 20, 10, 100, ro_n=20, ro_exact=14)})
        r = pv.evaluate_reserve(self.decision(), res)
        self.assertEqual(r["status"], "pass")
        self.assertEqual((r["flagged"], r["rubble_only_n"], r["reserve_n"]), (80, 20, 200))
        # recall 70/80, precision 70/90 -> 0.778, Rubble-only 14/20, nrealt 170/200
        self.assertEqual({k: c["got"] for k, c in r["checks"].items()},
                         {"recall": 0.875, "precision": 0.778, "rubble_only_exact": 0.7, "nreal_exact": 0.85})
        self.assertTrue(all(c["pass"] for c in r["checks"].values()))

    def test_reserve_fail_on_recall(self):
        res = make_res(n=200, nreal_exact=170,
                       overrides={"init_2_0.75": stats(50, 20, 30, 100, ro_n=20, ro_exact=14)})
        r = pv.evaluate_reserve(self.decision(), res)
        self.assertEqual(r["status"], "fail")
        self.assertFalse(r["checks"]["recall"]["pass"])      # 0.625 < 0.775
        self.assertFalse(r["checks"]["precision"]["pass"])   # 50/70 = 0.714 < 0.775
        self.assertTrue(r["checks"]["rubble_only_exact"]["pass"])
        self.assertTrue(r["checks"]["nreal_exact"]["pass"])

    def test_reserve_underpowered(self):
        res = make_res(n=200, nreal_exact=170,
                       overrides={"init_2_0.75": stats(20, 5, 5, 170, ro_n=20, ro_exact=14)})  # 25 flagged
        r = pv.evaluate_reserve(self.decision(), res)
        self.assertEqual(r["status"], "underpowered_reserve")
        self.assertNotIn("checks", r)

    def test_render_mentions_status_and_variant(self):
        d = self.decision()
        text = pv.render(d, None)
        self.assertIn("Status: **chosen**", text)
        self.assertIn("init_2_0.75", text)
        self.assertIn(">= 0.775", text)
        self.assertIn("Munim, Inc.", text)


if __name__ == "__main__":
    unittest.main()
