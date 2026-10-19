"""Hand-worked tests for robnik_rejoin. Apache-2.0. MV2 of Munim, Inc.; made with AI."""
import unittest

import robnik_rejoin as rr

ROBNIK_LIKE = "# This file was produced by someone\n# KOI: name\nkepid\tKOI\tperiod\n1\t4921.01\t95.7\n2\t5.01\t3.1\n"


def row(name, period, fail, in_dr25="0"):
    return {"kepoi_name": name, "kepid": "1", "period": period, "in_dr25": in_dr25, "would_fail": fail}


class StripComments(unittest.TestCase):
    def test_leading_comments_go(self):
        self.assertEqual(rr.strip_comments("# a\n# b\nx\ty\n1\t2\n"), "x\ty\n1\t2\n")

    def test_later_hash_lines_stay(self):
        self.assertEqual(rr.strip_comments("x\n# y\n"), "x\n# y\n")

    def test_old_bug_and_fix(self):
        # without the fix the first comment line is the header: no KOI column, no names
        self.assertEqual(rr.robnik_names(rr.read_table(ROBNIK_LIKE)), set())
        rows = rr.read_table(rr.strip_comments(ROBNIK_LIKE))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rr.robnik_names(rows), {"K04921.01", "K00005.01"})


class Stats(unittest.TestCase):
    def test_koi_name(self):
        self.assertEqual(rr.koi_name("5269.01"), "K05269.01")
        self.assertEqual(rr.koi_name("12.1"), "K00012.10")

    def test_fisher(self):
        self.assertAlmostEqual(rr.fisher_greater(1, 0, 0, 1), 0.5)
        self.assertAlmostEqual(rr.fisher_greater(2, 0, 0, 2), 1 / 6)
        self.assertAlmostEqual(rr.fisher_greater(1, 1, 0, 1), 2 / 3)

    def test_compare_and_window(self):
        rows = [row("A", "100", "1"), row("B", "350", "0"), row("C", "360", "1", "1")]
        m = rr.compare(rows, {"A"})
        self.assertEqual((m["n_fail"], m["fail_listed"], m["n_pass"], m["pass_listed"]), (2, 1, 1, 0))
        self.assertAlmostEqual(m["p_one_sided"], 2 / 3)
        w = rr.compare(rows, {"A"}, 340.0, 400.0)
        self.assertEqual((w["n_fail"], w["fail_listed"], w["n_pass"], w["pass_listed"]), (1, 0, 1, 0))
        self.assertAlmostEqual(w["p_one_sided"], 1.0)
        c = rr.comparisons(rows, {"A"})
        self.assertEqual((c["in_dr25_only"]["n_fail"], c["in_dr25_only"]["n_pass"]), (1, 0))
        self.assertIsNone(c["in_dr25_only"]["p_one_sided"])

    def test_scored(self):
        main = {"n_fail": 10, "fail_fraction": 0.2, "pass_fraction": 0.1, "p_one_sided": 0.001}
        win = {"fail_fraction": 0.0, "pass_fraction": 0.0}
        self.assertEqual(rr.scored(main, win),
                         {"q1_enough_fails": True, "q2_enrichment": True, "q3_window_direction": False})
        main["n_fail"] = 9
        self.assertEqual(rr.scored(main, {"fail_fraction": 0.5, "pass_fraction": 0.1}),
                         {"q1_enough_fails": False, "q2_enrichment": False, "q3_window_direction": True})


class Checks(unittest.TestCase):
    def test_population_ok(self):
        cmp = {"main": {"n_fail": 20, "n_pass": 620}, "window_340_400": {"n_fail": 6, "n_pass": 77},
               "in_dr25_only": {"n_fail": 4, "n_pass": 271}}
        self.assertTrue(rr.population_ok([{}] * 640, cmp))
        self.assertFalse(rr.population_ok([{}] * 639, cmp))
        cmp["window_340_400"] = {"n_fail": 5, "n_pass": 78}
        self.assertFalse(rr.population_ok([{}] * 640, cmp))

    def test_robnik_ok(self):
        rows = [{"KOI": "1.01"}] * 406
        self.assertTrue(rr.robnik_ok(rows, rr.ROBNIK_SHA256))
        self.assertFalse(rr.robnik_ok(rows, "0" * 64))
        self.assertFalse(rr.robnik_ok(rows[:405], rr.ROBNIK_SHA256))
        self.assertFalse(rr.robnik_ok(rows[:405] + [{"KOI": " "}], rr.ROBNIK_SHA256))

    def test_gate(self):
        files = {rr.PREREG: b"x", rr.SELF: b"code\r\n"}

        def fetch(p):
            return files[p]
        self.assertEqual(rr.gate(b"code\n", fetch)[0], True)
        self.assertEqual(rr.gate(b"other\n", fetch)[0], False)
        del files[rr.PREREG]
        self.assertEqual(rr.gate(b"code\n", fetch)[0], False)


if __name__ == "__main__":
    unittest.main()
