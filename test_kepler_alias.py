import unittest

import kepler_alias as ka


def joined(**kw):
    # DR25 TCE 2 and KOI K02174.03 of KIC 8261920, as returned by the Archive's TAP join on 2026-10-16.
    base = {"kepid": "8261920", "tce_plnt_num": "2", "tce_period": "15.4502", "tce_time0bk": "145.907",
            "tce_depth": "738.7", "tce_duration": "1.772", "kepoi_name": "K02174.03", "kepler_name": "Kepler-1802 b",
            "koi_period": "7.72513619", "koi_time0bk": "176.80202", "koi_depth": "382.2", "koi_duration": "2.042",
            "koi_disposition": "CONFIRMED", "koi_prad": "1.71"}
    base.update({k: str(v) for k, v in kw.items()})
    return base


def link(text):
    return f"<a refstr=X href=https://ui.adsabs.harvard.edu/abs/X/abstract target=ref>{text}</a>"


COMP = {"Kepler-1802 b": {"pl_name": "Kepler-1802 b", "pl_orbper": "15.45020008",
                          "pl_orbper_reflink": link("Valizadegan et al. 2022"), "pl_orbsmax": "0.0662",
                          "pl_orbsmax_reflink": link("Q1-Q17 DR25 KOI Table"), "st_mass": "0.649"}}


def synthetic(p, t0, dur_h, depth, every=1, span=200.0, step=0.0204):
    """Box transits on every `every`-th epoch of (p, t0); noiseless, flux 1 elsewhere."""
    times, fluxes = [], []
    for i in range(int(span / step)):
        t = i * step
        n = round((t - t0) / p)
        inside = abs(t - (t0 + n * p)) < 0.5 * dur_h / 24.0 and n % every == 0
        times.append(t)
        fluxes.append(1.0 - depth if inside else 1.0)
    return times, fluxes


class AliasFactorTest(unittest.TestCase):
    def test_kepler_1802_b_is_a_factor_two(self):
        self.assertEqual(ka.alias_factor(15.4502, 7.72513619), (2, "tce_long"))
        self.assertEqual(ka.alias_factor(7.72513619, 15.4502), (2, "koi_long"))

    def test_same_and_unrelated_periods(self):
        self.assertEqual(ka.alias_factor(6.69332, 6.69332825), (1, "same"))
        self.assertEqual(ka.alias_factor(33.1361, 6.69332825), (0, "other"))  # ratio 4.95, not 5 within 0.2 %
        self.assertEqual(ka.alias_factor(None, 3.0), (0, "other"))


class CensusRowTest(unittest.TestCase):
    def test_kepler_1802_b_row(self):
        c = ka.census_row(joined(), COMP)
        self.assertEqual((c["k"], c["which_long"]), (2, "tce_long"))
        self.assertEqual((c["p_short"], c["p_long"], c["t0_short"]), (7.72513619, 15.4502, 176.80202))
        self.assertEqual(c["long_group"], 0)  # TCE epoch is 4 KOI periods before the KOI epoch
        self.assertAlmostEqual(c["depth_ratio"], 1.9328, delta=0.001)
        self.assertEqual(c["depth_hint"], "long")
        self.assertEqual((c["archive_matches"], c["archive_period_ref"]), ("long", "Valizadegan et al. 2022"))
        self.assertEqual(c["archive_smax_ref"], "Q1-Q17 DR25 KOI Table")
        self.assertAlmostEqual(c["smax_kepler_ratio"], 0.630, delta=0.002)  # 2^(-2/3): a from the 7.725 d fit

    def test_same_period_row_is_skipped(self):
        self.assertIsNone(ka.census_row(joined(tce_period=7.72513, tce_depth=380), COMP))

    def test_koi_long_row_and_short_hint(self):
        c = ka.census_row(joined(tce_period=3.0, tce_time0bk=101.0, tce_depth=400, koi_period=6.0,
                                 koi_time0bk=104.0, koi_depth=410, kepler_name=""), COMP)
        self.assertEqual((c["k"], c["which_long"], c["p_short"], c["p_long"]), (2, "koi_long", 3.0, 6.0))
        self.assertEqual(c["long_group"], 1)  # (104 - 101) / 3 = 1
        self.assertEqual(c["depth_hint"], "short")  # ratio 1.025, not near 2
        self.assertEqual((c["archive_period"], c["smax_kepler_ratio"]), ("", ""))

    def test_kepler_smax(self):
        self.assertAlmostEqual(ka.kepler_smax(1.0, 365.25), 1.0, places=9)
        self.assertAlmostEqual(ka.kepler_smax(0.649, 7.72513619), 0.0662, delta=0.0002)
        self.assertIsNone(ka.kepler_smax(None, 5.0))


class LightCurveTest(unittest.TestCase):
    def test_alternate_transits_mean_the_long_period_is_real(self):
        times, fluxes = synthetic(7.7, 3.0, 2.0, 5e-4, every=2)
        epochs = ka.epoch_depths(times, fluxes, 7.7, 3.0, 2.0)
        self.assertEqual(len(epochs), 26)  # epochs 0..25 all inside 0-200 d
        groups = ka.group_stats(epochs, 2)
        self.assertEqual([g["epochs"] for g in groups], [13, 13])
        self.assertAlmostEqual(groups[0]["depth"], 5e-4, delta=1e-9)
        self.assertAlmostEqual(groups[1]["depth"], 0.0, delta=1e-9)
        self.assertEqual(ka.verdict(groups, 0), "long_period_real")
        self.assertEqual(ka.verdict(groups, 1), "inconclusive")  # deep group is not where the long period says

    def test_every_transit_means_the_short_period_is_real(self):
        times, fluxes = synthetic(7.7, 3.0, 2.0, 5e-4, every=1)
        groups = ka.group_stats(ka.epoch_depths(times, fluxes, 7.7, 3.0, 2.0), 2)
        self.assertEqual(ka.verdict(groups, 0), "short_period_real")

    def test_unequal_groups_and_missing_groups_are_inconclusive(self):
        g = [{"group": 0, "epochs": 5, "depth": 5e-4, "err": 2e-5, "snr": 25.0},
             {"group": 1, "epochs": 5, "depth": 2e-4, "err": 2e-5, "snr": 10.0}]
        self.assertEqual(ka.verdict(g, 0), "inconclusive")
        g[1] = {"group": 1, "epochs": 0, "depth": None, "err": None, "snr": None}
        self.assertEqual(ka.verdict(g, 0), "inconclusive")

    def test_points_in_another_kois_transit_are_masked(self):
        mask = ka.mask_others([5.0, 5.3, 5.5, 6.0, 15.2], [(10.0, 5.0, 24.0)])
        self.assertEqual(mask, [True, True, True, False, True])
        self.assertEqual(ka.mask_others([5.0], [(None, 5.0, 24.0)]), [False])

    def test_epoch_needs_points_on_both_sides(self):
        times, fluxes = synthetic(7.7, 3.0, 2.0, 5e-4, span=3.05)  # data stop just after mid-transit
        self.assertEqual(ka.epoch_depths(times, fluxes, 7.7, 3.0, 2.0), [])

    def test_line_fit_and_ref_text(self):
        a, b, rms = ka.line_fit([(0.0, 1.0), (1.0, 3.0), (2.0, 5.0)])
        self.assertAlmostEqual((a, b, rms)[0], 1.0)
        self.assertAlmostEqual(b, 2.0)
        self.assertAlmostEqual(rms, 0.0)
        self.assertEqual(ka.ref_text(link("Fulton &amp; Petigura 2018")), "Fulton & Petigura 2018")


if __name__ == "__main__":
    unittest.main()
