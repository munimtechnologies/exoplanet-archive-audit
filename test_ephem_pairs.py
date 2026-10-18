"""Tests for ephem_pairs. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0.

Fixture rows are the NASA Exoplanet Archive cumulative-table values read on 2026-10-18 (~01:00 UTC) for the
three hand-found pairs; expected offsets were worked by hand from those ephemerides.
"""
import csv
import json
import os
import tempfile
import unittest

import ephem_pairs as ep

FIELDS = ["kepid", "kepoi_name", "koi_disposition", "koi_pdisposition", "koi_period", "koi_time0bk",
          "koi_duration", "koi_depth", "koi_model_snr", "koi_kepmag", "ra", "dec", "koi_fpflag_ec",
          "koi_tce_delivname"]
# kepid, name, period, time0bk, duration, depth, snr, kepmag, ra, dec, delivname
REAL = [
    ("9363944", "K05660.01", "402.20969", "369.5086", "5.298", "472.5", "9.50", "13.660", "299.035280", "45.869289", "q1_q16_tce"),
    ("5956171", "K08259.01", "402.27493", "369.6734", "15.67", "294.5", "11.10", "14.619", "290.451900", "41.225510", "q1_q17_dr25_tce"),
    ("11818566", "K05935.01", "416.87893121", "227.5106644", "4.45", "", "", "15.690", "294.206300", "50.045399", "q1_q16_tce"),
    ("7917068", "K05446.01", "416.9504", "227.392", "4.026", "479.8", "6.90", "12.692", "299.341030", "43.643162", "q1_q16_tce"),
    ("8442795", "K07040.01", "502.20642", "162.9131", "9.39", "447.9", "7.10", "14.948", "296.057280", "44.461079", "q1_q17_dr24_tce"),
    ("9278575", "K07932.01", "502.25648", "162.5842", "14.84", "153.2", "8.10", "13.339", "290.893950", "45.716640", "q1_q17_dr25_tce"),
]


def row(kepid, name, p, t, dur="5", depth="100", snr="10", mag="14", ra="290", dec="44", deliv="", disp="CANDIDATE"):
    return {"kepid": kepid, "kepoi_name": name, "koi_disposition": disp, "koi_pdisposition": disp,
            "koi_period": p, "koi_time0bk": t, "koi_duration": dur, "koi_depth": depth, "koi_model_snr": snr,
            "koi_kepmag": mag, "ra": ra, "dec": dec, "koi_fpflag_ec": "0", "koi_tce_delivname": deliv}


def real_rows():
    return [row(*r) for r in REAL]


def by_name(ks):
    return {k["kepoi_name"]: k for k in ks}


class Events(unittest.TestCase):
    def test_k05660_four_events(self):
        e = ep.events(402.20969, 369.5086)
        self.assertEqual(len(e), 4)
        self.assertAlmostEqual(e[-1], 1576.13767, places=5)

    def test_k07040_three_events(self):
        self.assertEqual(len(ep.events(502.20642, 162.9131)), 3)

    def test_nearest_uses_any_cycle(self):
        self.assertAlmostEqual(ep.nearest(771.71829, 402.27493, 369.6734), 0.23004, places=5)
        self.assertAlmostEqual(ep.nearest(0.0, 402.27493, 369.6734), 32.60153, places=5)

    def test_single_event_train_has_no_offset(self):
        self.assertIsNone(ep.max_offset(129995.7784, 393.59962, 402.2, 369.5))


class Offsets(unittest.TestCase):
    def test_pair_a_402d(self):
        self.assertAlmostEqual(ep.max_offset(402.20969, 369.5086, 402.27493, 369.6734), 0.36052, places=5)

    def test_pair_b_417d(self):
        self.assertAlmostEqual(ep.max_offset(416.87893121, 227.5106644, 416.9504, 227.392), 0.1186644, places=6)

    def test_pair_c_502d(self):
        self.assertAlmostEqual(ep.max_offset(502.20642, 162.9131, 502.25648, 162.5842), 0.3289, places=5)

    def test_symmetric(self):
        self.assertAlmostEqual(ep.max_offset(502.25648, 162.5842, 502.20642, 162.9131), 0.3289, places=5)

    def test_shifted_epoch_misses(self):
        self.assertGreater(ep.max_offset(402.20969, 374.5086, 402.27493, 369.6734), ep.W)


class Geometry(unittest.TestCase):
    def test_d_max_matches_thompson_examples(self):
        self.assertAlmostEqual(ep.d_max_arcsec(10.0), 552.7, delta=0.1)  # "up to 550 arcsec"
        self.assertAlmostEqual(ep.d_max_arcsec(5.0), 5500.3, delta=0.1)  # "up to 5500 arcsec"
        self.assertAlmostEqual(ep.d_max_arcsec(13.66), 115.8, delta=0.1)

    def test_separations(self):
        self.assertTrue(7.70 < ep.sep_deg(299.03528, 45.869289, 290.4519, 41.22551) < 7.80)
        self.assertTrue(7.20 < ep.sep_deg(294.2063, 50.045399, 299.34103, 43.643162) < 7.40)
        self.assertTrue(3.80 < ep.sep_deg(296.05728, 44.461079, 290.89395, 45.71664) < 3.90)

    def test_gnomonic_centre(self):
        x, y = ep.gnomonic(ep.FOV_RA, ep.FOV_DEC)
        self.assertAlmostEqual(x, 0.0, places=9)
        self.assertAlmostEqual(y, 0.0, places=9)

    def test_labels(self):
        star = lambda ra, dec, mag=15.0: {"ra": ra, "dec": dec, "kepmag": mag}
        self.assertEqual(ep.geometry(star(290.0, 44.0), star(290.0, 44.008))[0], "near")  # 28.8"
        anti = ep.geometry(star(ep.FOV_RA, ep.FOV_DEC + 2), star(ep.FOV_RA, ep.FOV_DEC - 2))
        self.assertEqual(anti[0], "antipodal")
        self.assertLess(anti[3], 1.0)
        self.assertEqual(ep.geometry(star(295.0, 46.0), star(295.0, 48.0))[0], "module")
        self.assertEqual(ep.geometry(star(295.0, 46.0), star(295.0, 50.0))[0], "far")

    def test_real_pairs_are_far(self):
        ks = by_name(ep.kois(real_rows()))
        for a, b in (("K05660.01", "K08259.01"), ("K05935.01", "K05446.01"), ("K07040.01", "K07932.01")):
            self.assertEqual(ep.geometry(ks[a], ks[b])[0], "far")


class Population(unittest.TestCase):
    def test_kois_filters(self):
        rows = real_rows() + [row("1", "K00001.01", "2.47", "132.0"),  # P < 50
                              row("10287723", "K01174.01", "129995.7784", "393.59962"),  # one event
                              row("2", "K00002.01", "60", "")]  # no epoch
        ks = ep.kois(rows)
        self.assertEqual(len(ks), 6)
        self.assertEqual([k["p"] for k in ks], sorted(k["p"] for k in ks))

    def test_candidate_pairs(self):
        rows = [row("1", "K1.01", "60.0", "140"), row("2", "K2.01", "60.04", "140"),  # 0.04 x 23 = 0.92
                row("3", "K3.01", "60.09", "140"),  # vs 60.0: 0.09 x 23 > 1; vs 60.04: 0.05 x 23 > 1
                row("1", "K1.02", "60.01", "140")]  # same star as K1.01
        ks = ep.kois(rows)
        names = {(ks[i]["kepoi_name"], ks[j]["kepoi_name"]) for i, j in ep.candidate_pairs(ks)}
        self.assertIn(("K1.01", "K2.01"), names)
        self.assertIn(("K1.02", "K2.01"), names)
        self.assertNotIn(("K1.01", "K1.02"), names)
        self.assertNotIn(("K1.01", "K3.01"), names)

    def test_matches_find_the_three(self):
        ks = ep.kois(real_rows())
        found = ep.matches(ks, ep.candidate_pairs(ks))
        got = {frozenset((ks[i]["kepoi_name"], ks[j]["kepoi_name"])) for i, j, _ in found}
        self.assertEqual(got, {frozenset(("K05660.01", "K08259.01")), frozenset(("K05935.01", "K05446.01")),
                               frozenset(("K07040.01", "K07932.01"))})

    def test_null_is_seeded_and_small(self):
        ks = ep.kois(real_rows())
        pairs = ep.candidate_pairs(ks)
        geoms = {pq: ep.geometry(ks[pq[0]], ks[pq[1]]) for pq in pairs}
        a = ep.null_counts(ks, pairs, geoms, n=200)
        self.assertEqual(a, ep.null_counts(ks, pairs, geoms, n=200))
        self.assertLess(sum(a) / len(a), 0.1)


class Main(unittest.TestCase):
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            koi = os.path.join(d, "k.csv")
            with open(koi, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=FIELDS)
                w.writeheader()
                w.writerows(real_rows())
            xm = os.path.join(d, "x.csv")
            with open(xm, "w", newline="", encoding="utf-8") as f:
                f.write("kepoi_name,lissauer_now\nK05660.01,P\nK08259.01,P\n")
            out = os.path.join(d, "out")
            ep.main(["--out-dir", out, "--koi-csv", koi, "--xmatch", xm, "--shuffles", "50"])
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual(s["kois_used"], 6)
            self.assertEqual(s["far_candidate_matches"], 3)
            self.assertEqual(s["matches_by_geom"]["far"], 3)
            self.assertEqual(s["far_candidate_p_gt_200"], 3)
            self.assertEqual(s["null"]["shuffles"], 50)
            with open(os.path.join(out, "ephem_pairs.csv"), encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows[0]["kepoi_a"], "K05660.01")
            self.assertEqual(rows[0]["lissauer_a"], "P")
            self.assertEqual(rows[0]["max_offset"], "0.3605")


if __name__ == "__main__":
    unittest.main()
