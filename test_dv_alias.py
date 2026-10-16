import unittest

import dv_alias as dv

# DR25 values for KOI-4893.01 and KOI-4711.01 (NASA Exoplanet Archive TAP, 2026-10-16).
ROW_4893 = {"kepoi_name": "K04893.01", "kepid": "11970050", "koi_period": "6.58753699", "koi_pdisposition": "CANDIDATE",
            "tce_period": "13.1750793", "tce_duration": "2.013", "tce_depth": "415.5", "tce_model_snr": "10.35",
            "tce_maxmes": "2.747", "tce_maxmesd": "8.562597", "wst_depth": "109.3", "tce_bin_oedp_stat": "1.941"}
DR24_4893 = {"kepoi_name": "K04893.01", "koi_period": "6.5875", "tce_period": "13.1751", "tce_maxmes": "3.671",
             "tce_maxmesd": "8.571"}
ROW_4711 = {"kepoi_name": "K04711.01", "kepid": "8355131", "koi_period": "4.3638313", "koi_pdisposition": "CANDIDATE",
            "tce_period": "8.72763776", "tce_duration": "1.37", "tce_depth": "275.7", "tce_model_snr": "10.29",
            "tce_maxmes": "3.359", "tce_maxmesd": "4.3652086", "wst_depth": "82.4", "tce_bin_oedp_stat": "0.01057"}


class Factor(unittest.TestCase):
    def test_whole_ratios(self):
        self.assertEqual(dv.alias_factor(6.58753699, 13.1750793), ("tce_long", 2))
        self.assertEqual(dv.alias_factor(10.8206034, 5.41038), ("koi_long", 2))  # KOI-521.02
        self.assertEqual(dv.alias_factor(0.428046051, 1.284126917), ("tce_long", 3))  # KOI-4844.01

    def test_not_alias(self):
        self.assertEqual(dv.alias_factor(9.0, 9.0001), (None, 1))
        self.assertEqual(dv.alias_factor(10.0, 25.0), (None, 1))  # 2.5 rounds to 2, 25 % off
        self.assertEqual(dv.alias_factor(1.0, 12.0), (None, 1))  # k above KMAX
        self.assertEqual(dv.alias_factor(None, 5.0), (None, 1))

    def test_tolerance(self):
        self.assertEqual(dv.alias_factor(10.0, 20.01), ("tce_long", 2))  # 0.05 % off
        self.assertEqual(dv.alias_factor(10.0, 20.03), (None, 1))  # 0.15 % off


class Offset(unittest.TestCase):
    def test_4893(self):
        j, d = dv.alias_offset(8.562597, 13.1750793, 2)
        self.assertEqual(j, 1)
        self.assertAlmostEqual(d, 1.97505735, places=7)

    def test_wrap_and_k3(self):
        self.assertEqual(dv.alias_offset(-4.0, 10.0, 2), (1, 1.0))  # -4 d is phase 6 d
        j, d = dv.alias_offset(0.85, 1.284126917, 3)
        self.assertEqual(j, 2)
        self.assertAlmostEqual(d, 0.006084611, places=7)

    def test_verdicts(self):
        self.assertEqual(dv.secondary_verdict(8.562597, 13.1750793, 2, 2.013), "no_alias_secondary")
        self.assertEqual(dv.secondary_verdict(4.3652086, 8.72763776, 2, 1.37), "secondary_at_alias")
        self.assertEqual(dv.secondary_verdict(None, 8.7, 2, 1.37), "no_secondary_data")
        # 0.24 h is under one cadence, so the tolerance is 0.0204 d
        self.assertEqual(dv.secondary_verdict(0.515, 1.0, 2, 0.24), "secondary_at_alias")
        self.assertEqual(dv.secondary_verdict(0.53, 1.0, 2, 0.24), "no_alias_secondary")


class Classify(unittest.TestCase):
    def test_4893(self):
        r = dv.classify(ROW_4893, DR24_4893, {"kepler_name": "", "koi_disposition": "CANDIDATE"})
        self.assertEqual((r["kind"], r["k"], r["verdict"]), ("tce_long", 2, "no_alias_secondary"))
        self.assertEqual(r["sec_phase"], 0.64991)
        self.assertEqual(r["nearest_alias_phase"], "1/2")
        self.assertEqual(r["offset_d"], 1.97506)
        self.assertAlmostEqual(r["dr24_sec_phase"], 0.6505, places=3)
        self.assertEqual(r["dr24_verdict"], "no_alias_secondary")
        self.assertEqual(r["koi_disposition"], "CANDIDATE")

    def test_4711(self):
        r = dv.classify(ROW_4711)
        self.assertEqual(r["verdict"], "secondary_at_alias")
        self.assertEqual(r["sec_phase"], 0.50016)
        self.assertEqual(r["kepler_name"], "")
        self.assertNotIn("dr24_verdict", r)

    def test_koi_long_and_none(self):
        r = dv.classify({"kepoi_name": "K00521.02", "koi_period": "10.8206034", "tce_period": "5.41038",
                         "tce_bin_oedp_stat": "0.3783"})
        self.assertEqual((r["kind"], r["k"], r["verdict"], r["oedp_stat"]), ("koi_long", 2, "koi_long", 0.3783))
        self.assertIsNone(dv.classify({"koi_period": "9.0", "tce_period": "9.0001"}))


if __name__ == "__main__":
    unittest.main()
