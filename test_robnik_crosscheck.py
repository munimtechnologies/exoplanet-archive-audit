"""Hand-worked tests for robnik_crosscheck.py. Apache-2.0. MV2 of Munim, Inc.; written by AI agents."""
import unittest

import robnik_crosscheck as rc


def koi(name, kepid, period, fail, disp="CANDIDATE", status="ok", eligible="1", in_dr25="1"):
    return {"kepoi_name": name, "kepid": kepid, "period": period, "would_fail": fail, "disposition": disp,
            "status": status, "eligible": eligible, "in_dr25": in_dr25}


class Names(unittest.TestCase):
    def test_koi_name(self):
        self.assertEqual(rc.koi_name("5269.01"), "K05269.01")
        self.assertEqual(rc.koi_name("7894.01"), "K07894.01")
        self.assertEqual(rc.koi_name("1.01"), "K00001.01")

    def test_read_table_tab_and_comma(self):
        self.assertEqual(rc.read_table("kepid\tKOI\n6359929\t5269.01\n"), [{"kepid": "6359929", "KOI": "5269.01"}])
        self.assertEqual(rc.read_table("a,b\n1,2\n"), [{"a": "1", "b": "2"}])

    def test_robnik_names_skips_blank(self):
        self.assertEqual(rc.robnik_names([{"KOI": "4426.01"}, {"KOI": ""}]), {"K04426.01"})


class Population(unittest.TestCase):
    def test_planets_per_star(self):
        rows = [{"kepid": "1", "koi_disposition": "CANDIDATE"}, {"kepid": "1", "koi_disposition": "CONFIRMED"},
                {"kepid": "2", "koi_disposition": "FALSE POSITIVE"}, {"kepid": "3", "koi_disposition": "CANDIDATE"}]
        self.assertEqual(rc.planets_per_star(rows), {"1": 2, "3": 1})

    def test_filters(self):
        rows = [koi("K00010.01", "3", "100.0", "0"),
                koi("K00011.01", "1", "100.0", "0"),                    # two planets on star 1
                koi("K00012.01", "3", "40.0", "0"),                     # P <= 45
                koi("K00013.01", "3", "100.0", "0", disp="CONFIRMED"),
                koi("K00014.01", "3", "100.0", "", status="no_skygroup", eligible=""),
                koi("K00015.01", "3", "100.0", "0", eligible="0"),
                koi("K05269.01", "3", "371.5", "1")]                    # looked up beforehand
        got = rc.population(rows, {"1": 2, "3": 1})
        self.assertEqual([r["kepoi_name"] for r in got], ["K00010.01"])


class Stats(unittest.TestCase):
    def test_fisher(self):
        # [[3,1],[1,3]]: (C(4,3)C(4,1) + C(4,4)C(4,0)) / C(8,4) = 17/70
        self.assertAlmostEqual(rc.fisher_greater(3, 1, 1, 3), 17 / 70)
        # [[2,0],[0,2]]: C(2,2)C(2,0) / C(4,2) = 1/6
        self.assertAlmostEqual(rc.fisher_greater(2, 0, 0, 2), 1 / 6)
        self.assertAlmostEqual(rc.fisher_greater(0, 5, 0, 5), 1.0)

    def test_compare(self):
        rows = [koi("A", "1", "100", "1"), koi("B", "2", "370", "1"), koi("C", "3", "100", "1"),
                koi("D", "4", "370", "0"), koi("E", "5", "100", "0"), koi("F", "6", "100", "0"),
                koi("G", "7", "100", "0")]
        got = rc.compare(rows, {"A", "B", "D"})
        self.assertEqual((got["n_fail"], got["fail_listed"], got["n_pass"], got["pass_listed"]), (3, 2, 4, 1))
        self.assertAlmostEqual(got["fail_fraction"], 2 / 3)
        self.assertAlmostEqual(got["pass_fraction"], 1 / 4)
        # [[2,1],[1,3]]: (C(3,2)C(4,1) + C(3,3)C(4,0)) / C(7,3) = 13/35
        self.assertAlmostEqual(got["p_one_sided"], 13 / 35)
        win = rc.compare(rows, {"A", "B", "D"}, 340.0, 400.0)
        self.assertEqual((win["n_fail"], win["fail_listed"], win["n_pass"], win["pass_listed"]), (1, 1, 1, 1))

    def test_scored(self):
        main = {"n_fail": 10, "fail_fraction": 0.5, "pass_fraction": 0.1, "p_one_sided": 0.001}
        win = {"fail_fraction": 0.3, "pass_fraction": 0.3}
        self.assertEqual(rc.scored(main, win),
                         {"q1_enough_fails": True, "q2_enrichment": True, "q3_window_direction": False})
        self.assertFalse(rc.scored(dict(main, p_one_sided=0.02), win)["q2_enrichment"])
        self.assertFalse(rc.scored(dict(main, pass_fraction=0.3), win)["q2_enrichment"])
        few = rc.scored(dict(main, n_fail=9), {"fail_fraction": 0.4, "pass_fraction": 0.3})
        self.assertEqual(few, {"q1_enough_fails": False, "q2_enrichment": False, "q3_window_direction": True})


if __name__ == "__main__":
    unittest.main()
