import unittest

import kepler_alias as ka


def joined(**kw):
    # DR25 TCE 2 and KOI K02174.03 of KIC 8261920, as returned by the Archive's TAP join on 2026-10-16.
    # tce_bin_oedp_stat and koi_num_transits were not part of that query; the values here are made up.
    base = {"kepid": "8261920", "tce_plnt_num": "2", "tce_period": "15.4502", "tce_time0bk": "145.907",
            "tce_depth": "738.7", "tce_duration": "1.772", "tce_bin_oedp_stat": "0.5",
            "kepoi_name": "K02174.03", "kepler_name": "Kepler-1802 b",
            "koi_period": "7.72513619", "koi_time0bk": "176.80202", "koi_depth": "382.2", "koi_duration": "2.042",
            "koi_disposition": "CONFIRMED", "koi_prad": "1.71", "koi_num_transits": "150"}
    base.update({k: str(v) for k, v in kw.items()})
    return base


def link(text):
    return f"<a refstr=X href=https://ui.adsabs.harvard.edu/abs/X/abstract target=ref>{text}</a>"


COMP = {"Kepler-1802 b": {"pl_name": "Kepler-1802 b", "pl_orbper": "15.45020008",
                          "pl_orbper_reflink": link("Valizadegan et al. 2022"), "pl_orbsmax": "0.0662",
                          "pl_orbsmax_reflink": link("Q1-Q17 DR25 KOI Table"), "st_mass": "0.649"}}

# DR25 KOI K04441.01 of KIC 8416523 as returned on 2026-10-16; the composite period is Morton et al.
# 2016's. The pl_tranmid here is made up: one KOI period after the KOI epoch, in BJD.
KOI_1604 = {"kepid": "8416523", "kepoi_name": "K04441.01", "kepler_name": "Kepler-1604 b",
            "koi_disposition": "CONFIRMED", "koi_period": "0.341842017", "koi_time0bk": "131.660336",
            "koi_depth": "285.6", "koi_duration": "1.1554", "koi_prad": "1.72"}
COMP_1604 = {"Kepler-1604 b": {"pl_name": "Kepler-1604 b", "pl_orbper": "0.683684256",
                               "pl_orbper_reflink": link("Morton et al. 2016"), "pl_tranmid": "2454965.002178",
                               "pl_orbsmax": "", "pl_orbsmax_reflink": "", "st_mass": ""}}


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
        self.assertEqual((c["census"], c["k"], c["which_long"]), ("tce", 2, "tce_long"))
        self.assertEqual((c["p_short"], c["p_long"], c["t0_short"]), (7.72513619, 15.4502, 176.80202))
        self.assertEqual(c["long_group"], 0)  # TCE epoch is 4 KOI periods before the KOI epoch
        self.assertAlmostEqual(c["depth_ratio"], 1.9328, delta=0.001)
        self.assertEqual(c["depth_hint"], "long")
        self.assertEqual((c["archive_matches"], c["archive_period_ref"]), ("long", "Valizadegan et al. 2022"))
        self.assertEqual(c["archive_smax_ref"], "Q1-Q17 DR25 KOI Table")
        self.assertAlmostEqual(c["smax_kepler_ratio"], 0.630, delta=0.002)  # 2^(-2/3): a from the 7.725 d fit
        # 1459.5 / 7.72513619 = 188.93, so at most 189 transits; 150 is allowed
        self.assertEqual((c["oedp_stat"], c["koi_num_transits"], c["max_transits"], c["impossible_count"]),
                         (0.5, 150.0, 189, ""))

    def test_kepler_1301_b_transit_count_is_impossible(self):
        # DR25: KOI 9.08233411 d with 298 transits (read 2026-10-16), TCE 4.54116 d; other values made up.
        c = ka.census_row(joined(kepoi_name="K02643.01", kepler_name="Kepler-1301 b", tce_period=4.54116,
                                 tce_time0bk=131.9, koi_period=9.08233411, koi_time0bk=131.9,
                                 koi_num_transits=298, tce_bin_oedp_stat=0.7513), {})
        self.assertEqual((c["k"], c["which_long"]), (2, "koi_long"))
        self.assertEqual(c["max_transits"], 161)  # 1459.5 / 9.08233411 = 160.69
        self.assertEqual(c["impossible_count"], "yes")
        self.assertEqual(c["oedp_stat"], 0.7513)

    def test_max_transits(self):
        self.assertEqual(ka.max_transits(1459.5), 2)
        self.assertEqual(ka.max_transits(1000.0), 2)
        self.assertEqual(ka.max_transits(224.150923), 7)  # 6.51
        self.assertIsNone(ka.max_transits(None))
        self.assertIsNone(ka.max_transits(0.0))

    def test_same_period_row_is_skipped(self):
        self.assertIsNone(ka.census_row(joined(tce_period=7.72513, tce_depth=380), COMP))

    def test_koi_long_row_and_short_hint(self):
        c = ka.census_row(joined(tce_period=3.0, tce_time0bk=101.0, tce_depth=400, koi_period=6.0,
                                 koi_time0bk=104.0, koi_depth=410, kepler_name="", koi_num_transits=""), COMP)
        self.assertEqual((c["k"], c["which_long"], c["p_short"], c["p_long"]), (2, "koi_long", 3.0, 6.0))
        self.assertEqual(c["long_group"], 1)  # (104 - 101) / 3 = 1
        self.assertEqual(c["depth_hint"], "short")  # ratio 1.025, not near 2
        self.assertEqual((c["archive_period"], c["smax_kepler_ratio"]), ("", ""))
        self.assertEqual((c["koi_num_transits"], c["impossible_count"]), (None, ""))

    def test_kepler_smax(self):
        self.assertAlmostEqual(ka.kepler_smax(1.0, 365.25), 1.0, places=9)
        self.assertAlmostEqual(ka.kepler_smax(0.649, 7.72513619), 0.0662, delta=0.0002)
        self.assertIsNone(ka.kepler_smax(None, 5.0))


class ArchiveRowTest(unittest.TestCase):
    def test_kepler_1604_b_archive_period_is_twice_the_koi_period(self):
        c = ka.archive_row(KOI_1604, COMP_1604)
        self.assertEqual((c["census"], c["k"], c["which_long"]), ("archive", 2, "archive_long"))
        self.assertEqual((c["p_short"], c["p_long"], c["t0_short"]), (0.341842017, 0.683684256, 131.660336))
        self.assertEqual(c["long_group"], 1)  # pl_tranmid - 2454833 = 132.002178, one KOI period later
        self.assertEqual((c["archive_matches"], c["archive_period_ref"]), ("long", "Morton et al. 2016"))
        self.assertEqual((c["koi_duration_h"], c["archive_smax"], c["smax_kepler_ratio"]), (1.1554, "", ""))
        self.assertEqual((c["koi_num_transits"], c["max_transits"]), (None, 4270))  # 1459.5 / 0.3418 = 4269.5

    def test_no_tranmid_leaves_the_long_phase_unknown(self):
        comp = {"Kepler-1604 b": dict(COMP_1604["Kepler-1604 b"], pl_tranmid="")}
        self.assertEqual(ka.archive_row(KOI_1604, comp)["long_group"], "")

    def test_archive_period_shorter_folds_on_koi_period_over_k(self):
        koi = dict(KOI_1604, kepler_name="X b", koi_period="6.0", koi_time0bk="104.0")
        c = ka.archive_row(koi, {"X b": {"pl_name": "X b", "pl_orbper": "3.0", "pl_tranmid": ""}})
        self.assertEqual((c["k"], c["which_long"], c["p_short"], c["p_long"]), (2, "koi_long", 3.0, 6.0))
        self.assertEqual((c["t0_short"], c["long_group"], c["archive_matches"]), (104.0, 0, "short"))

    def test_same_period_or_no_composite_row_is_skipped(self):
        koi = dict(KOI_1604, kepler_name="X b", koi_period="6.0")
        self.assertIsNone(ka.archive_row(koi, {"X b": {"pl_name": "X b", "pl_orbper": "6.0001"}}))
        self.assertIsNone(ka.archive_row(KOI_1604, {}))


class SelectTargetsTest(unittest.TestCase):
    @staticmethod
    def row(name, disp, census="tce", t0=1.0, dur=2.0, group=0):
        return {"census": census, "kepoi_name": name, "koi_disposition": disp, "t0_short": t0,
                "koi_duration_h": dur, "long_group": group}

    def test_dispositions_archive_rows_and_duplicates(self):
        census = [self.row("A", "CONFIRMED"), self.row("B", "CANDIDATE"), self.row("C", "FALSE POSITIVE"),
                  self.row("D", "CANDIDATE", t0=None), self.row("E", "CANDIDATE", group="")]
        arch = [self.row("A", "CONFIRMED", census="archive"), self.row("F", "CONFIRMED", census="archive")]
        names = lambda ts: [(t["kepoi_name"], t["census"]) for t in ts]
        self.assertEqual(names(ka.select_targets(census, arch, {"CANDIDATE"}, 40)), [("B", "tce")])
        self.assertEqual(names(ka.select_targets(census, arch, {"CONFIRMED"}, 40)),
                         [("A", "tce"), ("F", "archive")])
        self.assertEqual(names(ka.select_targets(census, arch, {"CONFIRMED", "CANDIDATE"}, 2)),
                         [("A", "tce"), ("B", "tce")])


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

    def test_halves_split_at_the_middle_epoch(self):
        times, fluxes = synthetic(7.7, 3.0, 2.0, 5e-4, every=2)
        h1, h2 = ka.split_halves(ka.epoch_depths(times, fluxes, 7.7, 3.0, 2.0), 2)
        self.assertEqual([g["epochs"] for g in h1], [7, 6])  # epochs 0..12
        self.assertEqual([g["epochs"] for g in h2], [6, 7])  # epochs 13..25
        self.assertAlmostEqual(h1[0]["depth"], 5e-4, delta=1e-9)
        self.assertAlmostEqual(h2[0]["depth"], 5e-4, delta=1e-9)
        self.assertAlmostEqual(h2[1]["depth"], 0.0, delta=1e-9)
        e1, e2 = ka.split_halves([], 2)
        self.assertEqual([g["epochs"] for g in e1 + e2], [0, 0, 0, 0])

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

    def test_line_fit_ref_text_and_groups_text(self):
        a, b, rms = ka.line_fit([(0.0, 1.0), (1.0, 3.0), (2.0, 5.0)])
        self.assertAlmostEqual((a, b, rms)[0], 1.0)
        self.assertAlmostEqual(b, 2.0)
        self.assertAlmostEqual(rms, 0.0)
        self.assertEqual(ka.ref_text(link("Fulton &amp; Petigura 2018")), "Fulton & Petigura 2018")
        self.assertEqual(ka.groups_text([{"group": 0, "epochs": 3, "depth": 2.5e-4, "err": 1e-5, "snr": 25.0}]),
                         "g0: n=3 depth=250.0+-10.0 ppm snr=25.0")


if __name__ == "__main__":
    unittest.main()
