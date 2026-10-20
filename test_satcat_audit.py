#!/usr/bin/env python3
# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Tests for satcat_audit.py 0.1.1. Written by AI agents working in MV2's name.
#
# Fixtures: two SERVED records (Vanguard 1, NORAD 5; ISS, NORAD 25544) fetched from
# celestrak.org/satcat/records.php on 2026-10-20 to fix the decimal precision; both are excluded from
# scoring. Every other row is MADE UP (format-like, NORAD ids 900001+), never copied from any output.
# Hand-checked values: Vanguard 1 Kepler period 132.587 min (served 132.59); ISS 92.960 min (served 92.97);
# GEO a = 42164.000 km gives 1436.06 min.
import csv
import json
import os
import tempfile
import unittest
from decimal import Decimal

import satcat_audit as sa

HEADER = sa.COLUMNS
VANGUARD = "VANGUARD 1,1958-002B,5,PAY,,US,1958-03-17,AFETR,,132.59,34.25,3819,651,0.1220,,EA,ORB"
ISS = "ISS (ZARYA),1998-067A,25544,PAY,+,ISS,1998-11-20,TYMSC,,92.97,51.63,424,415,399.0524,,EA,ORB"


def row(norad, period, apo, peri, launch="2099-01-01", decay="", status="", center="EA", otype="ORB"):
    """A made-up, format-like SATCAT row as a dict."""
    vals = ["MADE-UP %s" % norad, "2099-001A", str(norad), "PAY", "", "XX", launch, "XXXX", decay,
            period, "45.00", apo, peri, "1.0", status, center, otype]
    return dict(zip(HEADER, vals))


def served_period(apo, peri):
    return str(sa.period_minutes(Decimal(apo), Decimal(peri)).quantize(Decimal("0.01")))


class Intervals(unittest.TestCase):
    def test_two_decimals(self):
        self.assertEqual(sa.interval("132.59"), (Decimal("132.585"), Decimal("132.595")))

    def test_integer(self):
        self.assertEqual(sa.interval("3819"), (Decimal("3818.5"), Decimal("3819.5")))

    def test_strip(self):
        self.assertEqual(sa.interval(" 651 "), (Decimal("650.5"), Decimal("651.5")))

    def test_not_a_number(self):
        with self.assertRaises(Exception):
            sa.interval("abc")


class Tokens(unittest.TestCase):
    def test_text_missing_tokens(self):
        for tok in ("", "  ", "null", " NULL ", "None", "n/a", "N/A", "NA", "NaN", "-"):
            self.assertEqual(sa.text(tok), "", tok)
        self.assertEqual(sa.text(" 3819 "), "3819")
        self.assertEqual(sa.text("abc"), "abc")
        self.assertEqual(sa.text(None), "")

    def test_num_values(self):
        self.assertEqual(sa.num("3819"), Decimal("3819"))
        self.assertEqual(sa.num(" 132.59 "), Decimal("132.59"))
        self.assertEqual(sa.num("1e3"), Decimal("1000"))
        for tok in ("", "null", "NULL", "n/a", "nan", "-", None):
            self.assertIsNone(sa.num(tok), tok)

    def test_num_rejects_non_finite_and_junk(self):
        for tok in ("abc", "12abc", "Infinity", "-Infinity", "inf", "1,234"):
            self.assertIsNone(sa.num(tok), tok)


class KeplerPeriod(unittest.TestCase):
    def test_geo_hand_value(self):
        # a = 6378.135 + 35785.865 = 42164.000 km; hand: 1436.06 min (sidereal day 1436.07)
        p = sa.period_minutes(Decimal("35785.865"), Decimal("35785.865"))
        self.assertTrue(Decimal("1436.0") <= p <= Decimal("1436.2"), p)

    def test_vanguard_served_row(self):
        mis, gap, pmid, res = sa.kepler_check("132.59", "3819", "651")
        self.assertFalse(mis)
        self.assertEqual(gap, Decimal(0))
        self.assertLessEqual(abs(pmid - Decimal("132.587")), Decimal("0.005"), pmid)
        self.assertGreater(res, 0)

    def test_iss_served_row(self):
        mis, gap, pmid, res = sa.kepler_check("92.97", "424", "415")
        self.assertFalse(mis)
        self.assertEqual(gap, Decimal(0))
        self.assertLessEqual(abs(pmid - Decimal("92.960")), Decimal("0.005"), pmid)
        self.assertLessEqual(abs(res - Decimal("0.010")), Decimal("0.005"), res)

    def test_made_up_mismatch(self):
        mis, gap, pmid, res = sa.kepler_check("200.00", "424", "415")
        self.assertTrue(mis)
        self.assertGreater(gap, Decimal("100"))

    def test_rounded_kepler_period_is_not_a_mismatch(self):
        p = served_period("1000", "900")
        mis, gap, pmid, res = sa.kepler_check(p, "1000", "900")
        self.assertFalse(mis)
        self.assertEqual(gap, Decimal(0))

    def test_half_percent_slack_edge(self):
        # Kepler mid for (1000, 900) shifted by +0.4 % stays inside the slack; +0.6 % does not
        pmid = sa.period_minutes(Decimal("1000"), Decimal("900"))
        inside = str((pmid * Decimal("1.004")).quantize(Decimal("0.01")))
        outside = str((pmid * Decimal("1.006")).quantize(Decimal("0.01")))
        self.assertFalse(sa.kepler_check(inside, "1000", "900")[0])
        self.assertTrue(sa.kepler_check(outside, "1000", "900")[0])


class Classify(unittest.TestCase):
    def test_ok_row(self):
        c = sa.classify(row(900001, served_period("1000", "900"), "1000", "900"))
        self.assertFalse(c["excluded"])
        self.assertTrue(c["e1_eligible"] and not c["e1_mismatch"])
        self.assertTrue(c["e2_eligible"] and not c["e2_violation"])
        self.assertFalse(c["e3_eligible"])
        self.assertTrue(c["e4_eligible"] and not c["e4_violation"])
        self.assertEqual(c["unusable"], {})

    def test_low_perigee(self):
        c = sa.classify(row(900002, served_period("150", "100"), "150", "100"))
        self.assertTrue(c["e2_violation"])

    def test_perigee_exactly_120_is_not_a_violation(self):
        c = sa.classify(row(900003, served_period("200", "120"), "200", "120"))
        self.assertTrue(c["e2_eligible"])
        self.assertFalse(c["e2_violation"])

    def test_no_current_elements_not_e2_eligible(self):
        c = sa.classify(row(900004, served_period("150", "100"), "150", "100", status="NCE"))
        self.assertFalse(c["e2_eligible"])
        self.assertTrue(c["e1_eligible"])  # E1 still scores it

    def test_decayed_not_e2_eligible(self):
        c = sa.classify(row(900005, served_period("150", "100"), "150", "100", decay="2099-02-01"))
        self.assertFalse(c["e2_eligible"])

    def test_decay_before_launch(self):
        c = sa.classify(row(900006, served_period("500", "500"), "500", "500",
                            launch="2000-01-01", decay="1999-12-31"))
        self.assertTrue(c["e3_eligible"] and c["e3_violation"])

    def test_decay_with_time_uses_date_part(self):
        c = sa.classify(row(900007, served_period("500", "500"), "500", "500",
                            launch="2000-01-01", decay="2000-01-01T12:00:00"))
        self.assertTrue(c["e3_eligible"])
        self.assertFalse(c["e3_violation"])

    def test_perigee_above_apogee(self):
        c = sa.classify(row(900008, "100.00", "300", "400"))
        self.assertTrue(c["e4_violation"])
        self.assertFalse(c["e1_eligible"])
        self.assertTrue(c["e2_eligible"] and not c["e2_violation"])

    def test_equal_apsides_not_a_violation(self):
        c = sa.classify(row(900009, served_period("500", "500"), "500", "500"))
        self.assertFalse(c["e4_violation"])
        self.assertTrue(c["e1_eligible"])

    def test_docked_object_center_is_norad_id(self):
        c = sa.classify(row(900010, "93.00", "430", "420", center="25544", otype="DOC"))
        self.assertFalse(c["e1_eligible"])
        self.assertFalse(c["e2_eligible"])
        self.assertTrue(c["e4_eligible"])

    def test_missing_elements(self):
        c = sa.classify(row(900011, "", "", "", status="NEA"))
        self.assertFalse(c["e1_eligible"] or c["e2_eligible"] or c["e4_eligible"])

    def test_excluded_served_rows(self):
        for line in (VANGUARD, ISS):
            c = sa.classify(dict(zip(HEADER, next(csv.reader([line])))))
            self.assertTrue(c["excluded"])

    def test_null_token_elements_are_missing(self):
        # The format page says "null if no data available": a literal null must behave like a blank.
        c = sa.classify(row(900012, "null", "null", "null", status="NEA"))
        self.assertFalse(c["e1_eligible"] or c["e2_eligible"] or c["e3_eligible"] or c["e4_eligible"])
        self.assertEqual(c["unusable"], {})  # documented token, not counted as unusable

    def test_null_decay_counts_as_blank(self):
        c = sa.classify(row(900013, served_period("500", "500"), "500", "500", decay="null"))
        self.assertTrue(c["e2_eligible"])
        self.assertFalse(c["e3_eligible"])
        self.assertEqual(c["served"]["DECAY_DATE"], "")

    def test_bad_date_not_e3_eligible(self):
        c = sa.classify(row(900014, served_period("500", "500"), "500", "500",
                            launch="2000-01-01", decay="unknown"))
        self.assertFalse(c["e3_eligible"])
        self.assertFalse(c["e2_eligible"])  # a non-empty, unparseable decay is not "no decay"
        self.assertEqual(c["unusable"], {"DECAY_DATE": "unknown"})

    def test_unusable_numeric_tokens_recorded(self):
        c = sa.classify(row(900015, "abc", "300", "x"))
        self.assertFalse(c["e1_eligible"] or c["e2_eligible"] or c["e4_eligible"])
        self.assertEqual(c["unusable"], {"PERIOD": "abc", "PERIGEE": "x"})


class Decide(unittest.TestCase):
    def test_e1(self):
        self.assertEqual(sa.decide("E1", 20000, 200), "holds")
        self.assertEqual(sa.decide("E1", 20000, 201), "fails")
        self.assertEqual(sa.decide("E1", 19999, 0), "underpowered")

    def test_e2(self):
        self.assertEqual(sa.decide("E2", 20000, 20), "holds")
        self.assertEqual(sa.decide("E2", 20000, 21), "fails")
        self.assertEqual(sa.decide("E2", 19999, 0), "underpowered")

    def test_e3_e4(self):
        self.assertEqual(sa.decide("E3", 1000, 0), "holds")
        self.assertEqual(sa.decide("E3", 1000, 1), "fails")
        self.assertEqual(sa.decide("E3", 999, 0), "underpowered")
        self.assertEqual(sa.decide("E4", 20000, 0), "holds")
        self.assertEqual(sa.decide("E4", 20000, 1), "fails")
        self.assertEqual(sa.decide("E4", 19999, 0), "underpowered")


class Median(unittest.TestCase):
    def test_median(self):
        self.assertIsNone(sa.median([]))
        self.assertEqual(sa.median([Decimal(3), Decimal(1), Decimal(2)]), Decimal(2))
        self.assertEqual(sa.median([Decimal(1), Decimal(4)]), Decimal("2.5"))


class FindCsv(unittest.TestCase):
    def test_single_csv(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "satcat.csv")
            open(p, "w").close()
            self.assertEqual(sa.find_csv(d), p)

    def test_prefers_satcat_name_even_in_subdir(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "a.csv"), "w").close()
            os.makedirs(os.path.join(d, "sub"))
            p = os.path.join(d, "sub", "SATCAT-2026.CSV")
            open(p, "w").close()
            self.assertEqual(sa.find_csv(d), p)

    def test_only_file_without_extension(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "blob")
            open(p, "w").close()
            self.assertEqual(sa.find_csv(d), p)

    def test_empty_dir_exits(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                sa.find_csv(d)


class EndToEnd(unittest.TestCase):
    def test_small_file_via_data_dir(self):
        rows = [
            row(900001, served_period("1000", "900"), "1000", "900"),                     # all fine
            row(900002, served_period("150", "100"), "150", "100", launch="2099-01-02"),  # E2 violation
            row(900003, served_period("500", "500"), "500", "500",
                launch="2000-01-01", decay="1999-12-31"),                                # E3 violation
            row(900004, "100.00", "300", "400", launch="2099-01-03"),                     # E4 violation
            row(900005, "93.00", "430", "420", launch="2099-01-04", center="25544", otype="DOC"),
            row(900006, "null", "null", "null", status="NEA"),                            # no elements
            row(900007, "abc", "300", "200", launch="2099-01-05"),                        # junk period
            dict(zip(HEADER, next(csv.reader([VANGUARD])))),                              # excluded
        ]
        with tempfile.TemporaryDirectory() as d:
            data = os.path.join(d, "data")
            os.makedirs(data)
            path = os.path.join(data, "satcat.csv")
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=HEADER)
                w.writeheader()
                for r in rows:
                    w.writerow(r)
            out = os.path.join(d, "out")
            self.assertEqual(sa.main(["--data-dir", data, "--out-dir", out]), 0)
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual(s["source_file"], "satcat.csv")
            self.assertEqual(s["rows_total"], 8)
            self.assertEqual(s["rows_excluded"], 1)
            t = s["tests"]
            self.assertEqual((t["E1"]["n"], t["E1"]["k"]), (3, 0))
            self.assertEqual((t["E2"]["n"], t["E2"]["k"]), (4, 1))
            self.assertEqual((t["E3"]["n"], t["E3"]["k"]), (1, 1))
            self.assertEqual((t["E4"]["n"], t["E4"]["k"]), (6, 1))
            for name in t:
                self.assertEqual(t[name]["decision"], "underpowered")
            u = s["descriptive_not_scored"]["unusable_tokens"]
            self.assertEqual(u["PERIOD"], {"abc": 1})
            self.assertEqual(u["APOGEE"], {})
            self.assertEqual(u["DECAY_DATE"], {})
            with open(os.path.join(out, "e2-flagged.csv"), newline="", encoding="utf-8") as f:
                flagged = list(csv.DictReader(f))
            self.assertEqual([r["NORAD_CAT_ID"] for r in flagged], ["900002"])
            with open(os.path.join(out, "e4-flagged.csv"), newline="", encoding="utf-8") as f:
                self.assertEqual([r["NORAD_CAT_ID"] for r in csv.DictReader(f)], ["900004"])

    def test_csv_flag_still_works(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x.csv")
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=HEADER)
                w.writeheader()
                w.writerow(row(900001, served_period("1000", "900"), "1000", "900"))
            out = os.path.join(d, "out")
            self.assertEqual(sa.main(["--csv", path, "--out-dir", out]), 0)
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f)["rows_total"], 1)

    def test_missing_column_exits(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "bad.csv")
            with open(path, "w", newline="", encoding="utf-8") as f:
                f.write("OBJECT_NAME,NORAD_CAT_ID\nX,1\n")
            with self.assertRaises(SystemExit):
                list(sa.read_rows(path))


if __name__ == "__main__":
    unittest.main()
