"""Unit tests for exo_audit.py. Apache-2.0. Munim, Inc. (MV2 of Munim, Inc.)."""
import csv
import json
import os
import tempfile
import unittest

import exo_audit as ea


def row(**kw):
    r = {"pl_name": "Test b", "hostname": "Test", "default_flag": "1",
         "pl_refname": '<a href="x">Ref A 2020</a>', "st_refname": '<a href="x">Ref A 2020</a>',
         "discoverymethod": "Transit", "pl_bmassprov": "Mass", "pl_controv_flag": "0", "cb_flag": "0"}
    r.update({k: str(v) for k, v in kw.items()})
    return r


EARTH = dict(pl_orbper=365.256363, pl_orbsmax=1.0, st_mass=1.0, pl_bmasse=1.0,
             pl_rade=1.0, pl_dens=5.514, st_rad=1.0, pl_ratdor=215.032,
             pl_ratror=1 / 109.076, pl_trandep=100 / 109.076 ** 2, st_teff=5772,
             pl_insol=1.0, st_logg=4.438, st_dens=1.4098)

ADS = "https://ui.adsabs.harvard.edu/abs/2018AJ....156..264F/abstract"


def solar_unit_star(i, ref="Ref S 2018", default="0"):
    """A self-consistent star whose st_dens is written in solar units."""
    m, rad = 0.7 + 0.1 * i, 0.65 + 0.12 * i
    r = row(st_mass=m, st_rad=rad, st_dens=round(m / rad ** 3, 4), pl_name=f"S-{i} b", default_flag=default)
    r["st_refname"] = r["pl_refname"] = f'<a refstr=S href={ADS} target=ref>{ref}</a>'
    return r


class Physics(unittest.TestCase):
    def test_kepler_earth(self):
        self.assertAlmostEqual(ea.kepler_a_au(365.256363, 1.0), 1.0, places=6)

    def test_kepler_hot_jupiter(self):
        # 3-day orbit around the Sun: a = (3/365.256)^(2/3) = 0.0407 au
        self.assertAlmostEqual(ea.kepler_a_au(3.0, 1.0), 0.04073, places=4)

    def test_earth_density(self):
        self.assertAlmostEqual(ea.bulk_density(1.0, 1.0), 5.514, places=3)

    def test_sun_density_from_earth_transit(self):
        self.assertAlmostEqual(ea.star_density_from_transit(215.032, 365.256363), 1.41, delta=0.01)

    def test_logg_sun(self):
        self.assertAlmostEqual(ea.logg(1.0, 1.0), 4.438, places=3)

    def test_insolation_earth(self):
        self.assertAlmostEqual(ea.insolation(5772, 1.0, 1.0), 1.0, places=9)

    def test_unit_slip(self):
        self.assertTrue(ea.unit_slip(101.0).startswith("x100"))
        self.assertTrue(ea.unit_slip(1 / 318.0).startswith("Jupiter vs Earth mass"))
        self.assertTrue(ea.unit_slip(1 / 1.41, "st_dens_vs_MR").startswith("solar vs g/cm3"))
        self.assertEqual(ea.unit_slip(1.7), "")

    def test_density_factor_only_explains_stellar_densities(self):
        # a 0.71 offset in log g or insolation is not a density unit slip
        for check in ("logg_vs_MR", "insolation", "bulk_density", None):
            self.assertEqual(ea.unit_slip(1 / 1.41, check), "", check)
        self.assertTrue(ea.unit_slip(1 / 1.41, "rhostar_transit_vs_MR").startswith("solar vs g/cm3"))

    def test_ppt_factor_only_explains_depths(self):
        self.assertTrue(ea.unit_slip(10.0, "depth_vs_k2").startswith("x10 (ppt"))
        self.assertFalse(ea.unit_slip(10.0, "st_dens_vs_MR").startswith("x10"))

    def test_unit_fixed(self):
        self.assertAlmostEqual(ea.unit_fixed(1 / 1.4098, "solar vs g/cm3 density (1.41)"), 1.0, places=9)
        self.assertAlmostEqual(ea.unit_fixed(100.0, "x100 (percent vs fraction)"), 1.0, places=9)

    def test_ref_text(self):
        self.assertEqual(ea.ref_text('<a refstr=X href=y target=ref>Smith et al. 2020</a>'), "Smith et al. 2020")
        self.assertEqual(ea.ref_text('<a href=y>Fulton &amp; Petigura 2018</a>'), "Fulton & Petigura 2018")

    def test_ref_bibcode(self):
        self.assertEqual(ea.ref_bibcode(f'<a refstr=X href={ADS} target=ref>F&amp;P 2018</a>'), "2018AJ....156..264F")
        self.assertEqual(ea.ref_bibcode('<a href="https://ui.adsabs.harvard.edu/abs/2016AJ%2E%2E%2E%2E152%2E%2E105M/abstract">M</a>'),
                         "2016AJ....152..105M")
        self.assertEqual(ea.ref_bibcode('<a href=https://exoplanetarchive.ipac.caltech.edu/docs/koi.html>KOI</a>'), "")
        self.assertEqual(ea.ref_bibcode(""), "")

    def test_pipeline(self):
        self.assertTrue(ea.is_pipeline("Q1-Q17 DR25 KOI Table"))
        self.assertFalse(ea.is_pipeline("Fulton & Petigura 2018"))


class Audit(unittest.TestCase):
    def test_consistent_earth_has_no_flags(self):
        stats, flags = ea.audit([row(**EARTH)], "ps")
        self.assertEqual(flags, [])
        for name in ("kepler3_a", "bulk_density", "a_over_rstar", "rp_over_rstar", "depth_vs_k2",
                     "rhostar_transit_vs_MR", "st_dens_vs_MR", "logg_vs_MR", "insolation"):
            self.assertEqual(stats[name]["tested"], 1, name)

    def test_depth_in_ppm_is_a_unit_slip(self):
        bad = dict(EARTH, pl_trandep=EARTH["pl_trandep"] * 1e4)
        _, flags = ea.audit([row(**bad)], "ps")
        f = [x for x in flags if x["check"] == "depth_vs_k2"]
        self.assertEqual(len(f), 1)
        self.assertTrue(f[0]["likely_unit_slip"].startswith("x1e4"))

    def test_depth_in_ppt_is_a_unit_slip(self):
        bad = dict(EARTH, pl_trandep=EARTH["pl_trandep"] * 10)
        _, flags = ea.audit([row(**bad)], "ps")
        f = [x for x in flags if x["check"] == "depth_vs_k2"]
        self.assertTrue(f[0]["likely_unit_slip"].startswith("x10 (ppt"))

    def test_mass_in_jupiter_units_flags_density(self):
        bad = dict(EARTH, pl_bmasse=1 / 317.83)
        _, flags = ea.audit([row(**bad)], "ps")
        f = [x for x in flags if x["check"] == "bulk_density"]
        self.assertEqual(len(f), 1)
        self.assertIn("Jupiter vs Earth mass", f[0]["likely_unit_slip"])

    def test_errors_protect_against_false_flags(self):
        off = dict(EARTH, pl_orbsmax=1.15, pl_orbsmaxerr1=0.2, pl_orbsmaxerr2=-0.2,
                   st_masserr1=0.01, st_masserr2=-0.01, pl_orbpererr1=0.001, pl_orbpererr2=-0.001)
        _, flags = ea.audit([row(**off)], "ps")
        self.assertFalse([x for x in flags if x["check"] == "kepler3_a"])
        off = dict(EARTH, pl_orbsmax=1.15, pl_orbsmaxerr1=0.01, pl_orbsmaxerr2=-0.01,
                   st_masserr1=0.01, st_masserr2=-0.01, pl_orbpererr1=0.001, pl_orbpererr2=-0.001)
        _, flags = ea.audit([row(**off)], "ps")
        self.assertTrue([x for x in flags if x["check"] == "kepler3_a"])

    def test_limits_are_skipped(self):
        r = row(**dict(EARTH, pl_bmasse=50.0))
        r["pl_bmasselim"] = "1"
        stats, _ = ea.audit([r], "ps")
        self.assertEqual(stats["bulk_density"]["tested"], 0)

    def test_microlensing_skipped_for_kepler(self):
        r = row(**dict(EARTH, pl_orbsmax=3.0))
        r["discoverymethod"] = "Microlensing"
        _, flags = ea.audit([r], "ps")
        self.assertFalse([x for x in flags if x["check"] == "kepler3_a"])

    def test_circumbinary_skipped_for_kepler(self):
        r = row(**dict(EARTH, pl_orbsmax=1.25))
        r["cb_flag"] = "1"
        stats, _ = ea.audit([r], "ps")
        self.assertEqual(stats["kepler3_a"]["tested"], 0)


class Systematics(unittest.TestCase):
    def test_reference_in_solar_density_units_is_found(self):
        groups = {}
        rows = [solar_unit_star(i) for i in range(6)] + [row(**EARTH)]
        ea.audit(rows, "ps", groups)
        sys_rows = ea.systematics(groups)
        hits = [s for s in sys_rows if s["reference"] == "Ref S 2018" and s["check"] == "st_dens_vs_MR"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["rows"], 6)
        self.assertTrue(hits[0]["unit_pattern"].startswith("solar vs g/cm3"))
        self.assertAlmostEqual(float(hits[0]["median_ratio"]), 1 / 1.4098, delta=0.002)
        self.assertAlmostEqual(float(hits[0]["median_after_unit_fix"]), 1.0, delta=0.002)
        # the consistent reference is not listed
        self.assertFalse([s for s in sys_rows if s["reference"] == "Ref A 2020"])

    def test_logg_offset_gets_no_density_label(self):
        groups = {}
        rows = []
        for i in range(6):
            r = row(**dict(EARTH, st_logg=4.438 - 0.149, pl_name=f"G-{i} b"))
            r["st_refname"] = '<a href="x">Ref G 2024</a>'
            rows.append(r)
        ea.audit(rows, "ps", groups)
        hits = [s for s in ea.systematics(groups) if s["check"] == "logg_vs_MR"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["unit_pattern"], "")

    def test_too_few_rows_is_not_systematic(self):
        groups = {}
        ea.audit([solar_unit_star(i) for i in range(4)], "ps", groups)
        self.assertEqual(ea.systematics(groups), [])

    def test_scatter_is_not_systematic(self):
        groups = {}
        rows = []
        for i, f in enumerate((0.5, 0.7, 0.9, 1.3, 1.6, 2.0)):
            r = row(**dict(EARTH, st_dens=1.4098 * f, pl_name=f"X-{i} b"))
            r["st_refname"] = '<a href="x">Ref N 2019</a>'
            rows.append(r)
        ea.audit(rows, "ps", groups)
        self.assertFalse([s for s in ea.systematics(groups) if s["check"] == "st_dens_vs_MR"])

    def test_pscomppars_charges_the_value_source(self):
        r = row(**dict(EARTH, st_dens=1.0))
        for k in ea.REFLINKS:
            r[k] = '<a href="x">Comp Ref 2021</a>'
        r["st_dens_reflink"] = '<a href="x">Dens Ref 2018</a>'
        groups = {}
        _, flags = ea.audit([r], "pscomppars", groups)
        f = [x for x in flags if x["check"] == "st_dens_vs_MR"]
        self.assertEqual(f[0]["source_ref"], "Dens Ref 2018")
        self.assertIn(("pscomppars", "st_dens_vs_MR", "Dens Ref 2018"), groups)

    def test_merge_reflinks(self):
        rows = [row(**EARTH)]
        text = "pl_name," + ",".join(ea.REFLINKS) + "\nTest b," + ",".join(["R"] * len(ea.REFLINKS)) + "\n"
        self.assertEqual(ea.merge_reflinks(rows, text), 1)
        self.assertEqual(rows[0]["st_dens_reflink"], "R")


class UnitGroups(unittest.TestCase):
    def test_rows_of_a_unit_pattern_reference_are_listed_in_both_tables(self):
        groups = {}
        ps = [solar_unit_star(i, default="1" if i == 0 else "0") for i in range(6)]
        ea.audit(ps, "ps", groups)
        # two composite values from the same reference: too few for a group of their own
        comp = []
        for i in range(2):
            r = solar_unit_star(10 + i)
            for k in ea.REFLINKS:
                r[k] = '<a href="x">Other 2021</a>'
            r["st_dens_reflink"] = r["st_refname"]
            comp.append(r)
        ea.audit(comp, "pscomppars", groups)
        sys_rows = ea.systematics(groups)
        self.assertFalse([s for s in sys_rows if s["table"] == "pscomppars" and s["check"] == "st_dens_vs_MR"])
        ug = ea.unit_group_rows(groups, sys_rows)
        dens = [u for u in ug if u["check"] == "st_dens_vs_MR"]
        self.assertEqual(len(dens), 8)
        self.assertEqual(sum(1 for u in dens if u["table"] == "pscomppars"), 2)
        self.assertTrue(all(u["bibcode"] == "2018AJ....156..264F" for u in dens))
        self.assertTrue(all(u["fix_within_10pct"] == 1 for u in dens))
        summ = [s for s in ea.unit_group_summary(ug) if s["check"] == "st_dens_vs_MR"][0]
        self.assertEqual((summ["ps_rows"], summ["ps_default_rows"], summ["composite_rows"]), (6, 1, 2))
        self.assertEqual(summ["bibcodes"], "2018AJ....156..264F")

    def test_no_pattern_no_rows(self):
        groups = {}
        ea.audit([row(**EARTH)], "ps", groups)
        self.assertEqual(ea.unit_group_rows(groups, ea.systematics(groups)), [])


class EndToEnd(unittest.TestCase):
    def test_offline_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "ps.csv")
            rows = [row(**EARTH), row(**dict(EARTH, pl_trandep=EARTH["pl_trandep"] * 100))]
            rows += [solar_unit_star(i) for i in range(5)]
            keys = sorted({k for r in rows for k in r})
            with open(src, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                w.writerows(rows)
            out = os.path.join(d, "out")
            self.assertEqual(ea.main(["--out-dir", out, "--offline", src]), 0)
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual(s["meta"]["version"], ea.VERSION)
            self.assertEqual(len(s["unit_groups"]), 1)
            for name in ("report.md", "by_reference.csv", "systematics.csv", "flags.csv", "unit_groups.csv"):
                self.assertTrue(os.path.exists(os.path.join(out, name)), name)
            with open(os.path.join(out, "unit_groups.csv"), encoding="utf-8") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 5)


if __name__ == "__main__":
    unittest.main()
