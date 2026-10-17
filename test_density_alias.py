import math
import unittest

import density_alias as da

# DR25 KOI fits (q1_q17_dr25_koi) and Berger et al. 2020 table2 stars, NASA Exoplanet Archive TAP and VizieR,
# 2026-10-17. Expected values worked by hand.
FIT_1301 = {"kepoi_name": "K02643.01", "kepid": "6933567", "koi_period": "9.08233411", "koi_dor": "33.91",
            "koi_srho": "8.94101", "koi_srho_err1": "1.74986", "koi_srho_err2": "-3.89657", "koi_impact": "0.262",
            "koi_ror": "0.015633", "koi_smass": "0.8840", "koi_srad": "0.7880"}
BER_1301 = {"KIC": "6933567", "Mass": "0.838", "E_Mass": "0.051", "e_Mass": "-0.053", "Rad": "0.838",
            "E_Rad": "0.026", "e_Rad": "-0.025"}
FIT_458 = {"kepoi_name": "K00179.02", "kepid": "9663113", "koi_period": "572.376632", "koi_dor": "136.1",
           "koi_srho": "0.14543", "koi_srho_err1": "0.16461", "koi_srho_err2": "-0.06180", "koi_impact": "0.712",
           "koi_ror": "0.040914"}
BER_458 = {"KIC": "9663113", "Mass": "1.544", "E_Mass": "0.063", "e_Mass": "-0.075", "Rad": "2.208",
           "E_Rad": "0.078", "e_Rad": "-0.073"}
FIT_167 = {"kepoi_name": "K00490.02", "kepid": "3239945", "koi_period": "1071.232624", "koi_dor": "557.3",
           "koi_srho": "2.85277", "koi_srho_err1": "0.16754", "koi_srho_err2": "-0.06130", "koi_impact": "0.216",
           "koi_ror": "0.122698"}
BER_167 = {"KIC": "3239945", "Mass": "0.755", "E_Mass": "0.035", "e_Mass": "-0.036", "Rad": "0.738",
           "E_Rad": "0.013", "e_Rad": "-0.012"}
FIT_1604 = {"kepoi_name": "K04441.01", "kepid": "8416523", "koi_period": "0.341842017", "koi_dor": "1.268",
            "koi_srho": "0.32970", "koi_srho_err1": "2.65191", "koi_srho_err2": "-0.46806", "koi_impact": "0.957",
            "koi_ror": "0.021058"}

TSV = ("#\n#   VizieR Astronomical Server\n#Column\tKIC\t(I8)\n\nKIC\tMass\tE_Mass\te_Mass\tRad\tE_Rad\te_Rad\n"
       "\tMsun\tMsun\tMsun\tRsun\tRsun\tRsun\n--------\t-----\t-----\t------\t-----\t-----\t------\n"
       "6933567\t0.838\t0.051\t-0.053\t0.838\t0.026\t-0.025\n9663113\t1.544\t0.063\t-0.075\t2.208\t0.078\t-0.073\n")


class Physics(unittest.TestCase):
    def test_rho_star(self):
        self.assertAlmostEqual(da.rho_star(0.838, 0.838), 2.00757, places=4)
        self.assertAlmostEqual(da.rho_star(1.0, 1.0), 1.4098, places=4)

    def test_rho_from_dor_matches_dr25(self):
        self.assertAlmostEqual(da.rho_from_dor(33.91, 9.08233411), 8.942, places=2)  # koi_srho 8.94101

    def test_scale_large_dor(self):
        self.assertAlmostEqual(da.period_scale(200.0, 0.0, 0.01, 100.0, 200.0), 2.0, places=4)
        self.assertAlmostEqual(da.period_scale(200.0, 0.0, 0.01, 100.0, 50.0), 0.5, places=4)

    def test_scale_1301_half(self):
        self.assertAlmostEqual(da.period_scale(33.91, 0.262, 0.015633, 9.08233411, 4.54116706), 0.50076, places=4)

    def test_scale_no_solution(self):
        self.assertIsNone(da.period_scale(10.0, 1.2, 0.05, 5.0, 2.5))  # b > 1 + k
        self.assertIsNone(da.period_scale(1.5, 0.0, 0.02, 1.0, 0.2))  # half-chord angle past 90 degrees
        self.assertIsNone(da.period_scale(None, 0.1, 0.01, 1.0, 2.0))

    def test_sigmas_and_tension(self):
        up, dn = da.fit_sigmas(8.94101, 1.74986, -3.89657)
        self.assertAlmostEqual(dn, 0.57237, places=4)
        self.assertAlmostEqual(up, math.log(10.69087 / 8.94101), places=6)
        self.assertEqual(da.fit_sigmas(1.0, 0.5, -1.2), (math.log(1.5), None))
        self.assertEqual(da.tension(1.2, 0.1, 0.1, 0.1), 0.0)  # inside the e <= 0.1 band
        self.assertIsNone(da.tension(3.0, 0.1, None, 0.1))

    def test_verdicts(self):
        self.assertEqual(da.verdict(0.5, 2.5, 0.2, 0.2), "favors_koi")
        self.assertEqual(da.verdict(2.5, 0.5, 0.2, 0.2), "favors_alt")
        self.assertEqual(da.verdict(2.5, 3.0, 0.2, 0.2), "both_tense")
        self.assertEqual(da.verdict(1.5, 0.5, 0.2, 0.2), "ambiguous")
        self.assertEqual(da.verdict(0.5, 2.5, 1.0, 0.5), "unconstrained")  # spans more than 4x


class Parse(unittest.TestCase):
    def test_vizier(self):
        b = da.parse_vizier_tsv(TSV)
        self.assertEqual(sorted(b), ["6933567", "9663113"])
        self.assertEqual(b["9663113"]["Rad"], "2.208")

    def test_star_for(self):
        rho, s, src = da.star_for("6933567", FIT_1301, {"6933567": BER_1301})
        self.assertEqual(src, "berger2020")
        self.assertAlmostEqual(rho, 2.00757, places=4)
        self.assertAlmostEqual(s, 0.11038, places=4)
        rho, s, src = da.star_for("6933567", FIT_1301, {})
        self.assertEqual(src, "dr25")
        self.assertAlmostEqual(rho, 1.4098 * 0.884 / 0.788 ** 3, places=6)


class Assess(unittest.TestCase):
    def test_kepler_1301b(self):
        a = da.assess(FIT_1301, 4.54116706, da.star_for("6933567", FIT_1301, {"6933567": BER_1301}))
        self.assertAlmostEqual(a["r_koi"], 4.4537, places=3)
        self.assertAlmostEqual(a["r_alt"], 2.2302, places=3)
        self.assertAlmostEqual(a["t_koi"], 2.048, delta=0.005)
        self.assertAlmostEqual(a["t_alt"], 0.861, delta=0.005)
        self.assertEqual(a["density_verdict"], "favors_alt")
        self.assertAlmostEqual(a["dor_check"], 1.0001, places=3)

    def test_kepler_458b_ambiguous(self):
        a = da.assess(FIT_458, 286.187067846481, da.star_for("9663113", FIT_458, {"9663113": BER_458}))
        self.assertAlmostEqual(a["r_koi"], 0.7192, places=3)
        self.assertLess(a["t_koi"], 0.05)
        self.assertAlmostEqual(a["t_alt"], 0.944, delta=0.005)
        self.assertEqual(a["density_verdict"], "ambiguous")

    def test_kepler_167e_favors_koi(self):
        a = da.assess(FIT_167, 535.6163, da.star_for("3239945", FIT_167, {"3239945": BER_167}))
        self.assertEqual(a["t_koi"], 0.0)
        self.assertAlmostEqual(a["t_alt"], 3.551, delta=0.01)
        self.assertEqual(a["density_verdict"], "favors_koi")

    def test_kepler_1604b_unconstrained(self):
        a = da.assess(FIT_1604, 0.683684256, (2.0, 0.1, "berger2020"))
        self.assertEqual(a["density_verdict"], "unconstrained")

    def test_missing_star(self):
        a = da.assess(FIT_458, 286.187, (None, None, "none"))
        self.assertEqual(a["density_verdict"], "unconstrained")


if __name__ == "__main__":
    unittest.main()
