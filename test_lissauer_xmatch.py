"""Tests for lissauer_xmatch. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0.

Row values for KOI 1101, 1922 and 2167 (KIC, period, S/N, Status) are as read from Lissauer et al. 2024
Table 1 and the Archive's cumulative table on 2026-10-17. K06262.01's two periods are the paper's
0.673 -> 0.3365 d halving, with KIC left blank. K08339.01 and K09999.01 are synthetic.
"""
import csv
import json
import os
import tempfile
import unittest

import lissauer_xmatch as lx

HEADER = """Title: Updated Catalog of Kepler Planet Candidates: Focus on Accuracy and Orbital Periods
Authors: Lissauer J.J., Rowe J.F., Jontof-Hutter D., et al.
Table: Catalog of planet candidates
================================================================================
Byte-by-byte Description of file: psjad0e6et1_mrt.txt
--------------------------------------------------------------------------------
   Bytes Format Units   Label     Explanations
--------------------------------------------------------------------------------
{spec}
--------------------------------------------------------------------------------
Note (14): Four letters, e.g.
    1.01 PPPP
    5.02 FFNN
--------------------------------------------------------------------------------
"""

SPEC_FMT = {"KIC": "I8", "KOI": "F7.2", "Kepler": "A14", "Period": "F14.8", "S/N": "F6.1",
            "MES": "F8.1", "Status": "A4"}

ROWS = [
    {"KIC": "3245969", "KOI": "1101.01", "Kepler": "Kepler-768 b", "Period": "11.39116273",
     "S/N": "24.5", "MES": "20.4", "Status": "PPPP"},
    {"KIC": "3245969", "KOI": "1101.02", "Period": "11.39114826", "S/N": "0.0", "MES": "0.0",
     "Status": "FPNN"},
    {"KIC": "9411166", "KOI": "1922.02", "Period": "15.09681793", "S/N": "4.1", "MES": "0.0",
     "Status": "SPNN"},
    {"KIC": "6041734", "KOI": "2167.02", "Period": "6.95745228", "S/N": "1.9", "MES": "0.0",
     "Status": "SPNN"},
    {"KIC": "11446443", "KOI": "1.01", "Kepler": "Kepler-1 b", "Period": "2.47061340",
     "S/N": "999.0", "MES": "999.0", "Status": "PPPP"},
    {"KOI": "6262.01", "Period": "0.33650000", "S/N": "12.0", "MES": "10.0", "Status": "PFFP"},
    {"KOI": "8339.01", "Period": "5.00000000", "S/N": "6.0", "MES": "0.0", "Status": "SNNN"},
]

ARCHIVE = [
    {"kepoi_name": "K00001.01", "kepid": "11446443", "kepler_name": "Kepler-1 b",
     "koi_disposition": "CONFIRMED", "koi_parm_prov": "q1_q17_dr25_koi", "koi_period": "2.470613377",
     "koi_model_snr": "4304.30"},
    {"kepoi_name": "K01101.01", "kepid": "3245969", "kepler_name": "Kepler-768 b",
     "koi_disposition": "CONFIRMED", "koi_parm_prov": "q1_q17_dr25_koi", "koi_period": "11.39102358",
     "koi_model_snr": ""},
    {"kepoi_name": "K01101.02", "kepid": "3245969", "kepler_name": "", "koi_disposition": "CANDIDATE",
     "koi_parm_prov": "q1_q16_koi", "koi_period": "11.39110963", "koi_model_snr": "12.10"},
    {"kepoi_name": "K01922.02", "kepid": "9411166", "kepler_name": "", "koi_disposition": "CANDIDATE",
     "koi_parm_prov": "q1_q16_koi", "koi_period": "15.09521323", "koi_model_snr": ""},
    {"kepoi_name": "K02167.02", "kepid": "6041734", "kepler_name": "", "koi_disposition": "CANDIDATE",
     "koi_parm_prov": "q1_q16_koi", "koi_period": "6.95787", "koi_model_snr": "1.80"},
    {"kepoi_name": "K06262.01", "kepid": "", "kepler_name": "", "koi_disposition": "CANDIDATE",
     "koi_parm_prov": "q1_q17_dr25_koi", "koi_period": "0.673", "koi_model_snr": ""},
    {"kepoi_name": "K09999.01", "kepid": "", "kepler_name": "", "koi_disposition": "CANDIDATE",
     "koi_parm_prov": "q1_q17_dr25_koi", "koi_period": "1.0", "koi_model_snr": ""},
]


def spec_lines(cols):
    out = []
    for key, (a, b) in cols.items():
        out.append(f"{a:4d}-{b:3d} {SPEC_FMT[key]:<6} ---     {key:<9} explanation")
    return "\n".join(out)


def build_row(cols, values):
    buf = [" "] * 600
    for key, (a, b) in cols.items():
        v = values.get(key)
        if v is None:
            continue
        width = b - a + 1
        s = v.ljust(width) if key in ("Kepler", "Status") else v.rjust(width)
        assert len(s) == width, (key, v)
        buf[a - 1:b] = list(s)
    return "".join(buf).rstrip()


def build_mrt(cols, rows=ROWS, header=True):
    head = HEADER.format(spec=spec_lines(cols)) if header else "-" * 80 + "\n"
    return head + "\n".join(build_row(cols, r) for r in rows) + "\n"


class TestNames(unittest.TestCase):
    def test_koi_name(self):
        self.assertEqual(lx.koi_name("1101.02"), "K01101.02")
        self.assertEqual(lx.koi_name("   1.01"), "K00001.01")
        self.assertEqual(lx.koi_name("8339.1"), "K08339.10")

    def test_letters(self):
        self.assertEqual(lx.letter("SPNN", 0), "S")
        self.assertEqual(lx.letter("SPNN", 1), "P")
        self.assertEqual(lx.letter("", 1), "")
        self.assertEqual(lx.archive_letter("CANDIDATE"), "P")
        self.assertEqual(lx.archive_letter("FALSE POSITIVE"), "F")
        self.assertEqual(lx.archive_letter("NOT DISPOSITIONED"), "")


class TestFraction(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(lx.nearest_fraction(1.0)[0], "1/1")
        self.assertEqual(lx.nearest_fraction(0.5)[0], "1/2")
        self.assertEqual(lx.nearest_fraction(1 / 11)[0], "1/11")
        self.assertAlmostEqual(lx.nearest_fraction(0.5)[1], 0.0)

    def test_kepler_1016(self):
        # Kepler-1016 c over K01922.02, both Lissauer periods: 6.99850, 2.14e-4 from 7.
        frac, err = lx.nearest_fraction(105.65509204 / 15.09681793)
        self.assertEqual(frac, "7/1")
        self.assertTrue(1e-4 < err < 3e-4, err)


class TestParse(unittest.TestCase):
    def test_header_spec(self):
        spec = lx.parse_byte_spec(spec_lines(lx.FALLBACK).splitlines())
        self.assertEqual(spec["Status"], (548, 551))
        self.assertEqual(spec["S/N"], (255, 260))
        self.assertEqual(spec["KIC"], (1, 8))

    def test_spec_ignores_notes_and_data(self):
        lines = ["    1.01 PPPP", "Note (14): text", build_row(lx.FALLBACK, ROWS[0])]
        self.assertEqual(lx.parse_byte_spec(lines), {})

    def test_parse_rows(self):
        rows, cols = lx.parse_mrt(build_mrt(lx.FALLBACK))
        self.assertEqual(len(rows), 7)
        r = {x["kepoi_name"]: x for x in rows}
        self.assertEqual(r["K01101.02"]["status"], "FPNN")
        self.assertEqual(r["K01101.02"]["kic"], 3245969)
        self.assertEqual(r["K01922.02"]["snr"], 4.1)
        self.assertAlmostEqual(r["K02167.02"]["period"], 6.95745228)
        self.assertEqual(r["K00001.01"]["kepler_name"], "Kepler-1 b")
        self.assertEqual(r["K08339.01"]["kic"], 0)

    def test_header_positions_win(self):
        moved = dict(lx.FALLBACK, Status=(560, 563), **{"S/N": (300, 305)})
        rows, cols = lx.parse_mrt(build_mrt(moved))
        self.assertEqual(cols["Status"], (560, 563))
        r = {x["kepoi_name"]: x for x in rows}
        self.assertEqual(r["K01922.02"]["status"], "SPNN")
        self.assertEqual(r["K01922.02"]["snr"], 4.1)

    def test_fallback_without_header(self):
        rows, cols = lx.parse_mrt(build_mrt(lx.FALLBACK, header=False))
        self.assertEqual(cols, lx.FALLBACK)
        self.assertEqual(len(rows), 7)


class TestMatch(unittest.TestCase):
    def setUp(self):
        rows, _ = lx.parse_mrt(build_mrt(lx.FALLBACK))
        self.merged, self.arch_only, self.lis_only = lx.xmatch(ARCHIVE, rows)
        self.s = lx.summarize(self.merged, self.arch_only, self.lis_only, len(rows))
        self.by = {m["kepoi_name"]: m for m in self.merged}

    def test_join(self):
        self.assertEqual(len(self.merged), 6)
        self.assertEqual(self.arch_only, ["K09999.01"])
        self.assertEqual(self.lis_only, ["K08339.01"])
        self.assertEqual(self.s["n_kic_mismatch"], 0)

    def test_crosstab(self):
        c = self.s["crosstab_archive_vs_lissauer_now"]
        self.assertEqual(c["CONFIRMED"], {"P": 2})
        self.assertEqual(c["CANDIDATE"], {"F": 1, "S": 2, "P": 1})
        self.assertEqual(self.s["candidates_rejected"], 3)
        self.assertEqual(self.s["confirmed_rejected"], 0)
        self.assertEqual(self.s["fp_now_p"], 0)

    def test_orphan_rates(self):
        self.assertTrue(self.by["K01922.02"]["orphan"])
        self.assertFalse(self.by["K06262.01"]["orphan"])
        self.assertEqual(self.s["candidate_reject_rate_orphan"], {"n": 3, "rejected": 3, "fraction": 1.0})
        self.assertEqual(self.s["candidate_reject_rate_dr25"], {"n": 1, "rejected": 0, "fraction": 0.0})
        self.assertEqual(self.s["candidates_by_prov_vs_lissauer_now"]["q1_q16_koi"], {"F": 1, "S": 2})

    def test_dr25supp_letter(self):
        # K06262.01 is PFFP in the fixture: DR25supp F against an Archive CANDIDATE.
        self.assertEqual(self.s["dr25supp_letter_vs_archive"], {"n": 6, "agree": 5})

    def test_periods(self):
        self.assertEqual(self.s["n_period_flags"], 1)
        self.assertEqual(self.by["K06262.01"]["ratio_fraction"], "1/2")
        self.assertFalse(self.by["K01922.02"]["period_flag"])  # 1.00011
        self.assertFalse(self.by["K02167.02"]["period_flag"])  # 0.99994
        self.assertEqual(self.s["period_flags_by_fraction"], {"1/2": 1})

    def test_watch(self):
        w = self.s["watch"]
        self.assertEqual(w["K01101.02"]["lissauer_status"], "FPNN")
        self.assertEqual(w["K02167.02"]["lissauer_status"], "SPNN")
        self.assertIsNone(w["K01353.03"])


class TestMain(unittest.TestCase):
    def test_offline_run(self):
        with tempfile.TemporaryDirectory() as d:
            mrt = os.path.join(d, "t1.txt")
            with open(mrt, "w", encoding="utf-8") as fh:
                fh.write(build_mrt(lx.FALLBACK))
            cum = os.path.join(d, "cum.csv")
            with open(cum, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(ARCHIVE[0]), lineterminator="\r\n")
                w.writeheader()
                w.writerows(ARCHIVE)
            out = os.path.join(d, "out")
            self.assertEqual(lx.main(["--out-dir", out, "--mrt-file", mrt, "--cumulative-file", cum]), 0)
            with open(os.path.join(out, "summary.json"), encoding="utf-8") as fh:
                s = json.load(fh)
            self.assertEqual(s["candidates_rejected"], 3)
            self.assertEqual(s["n_lissauer_rows"], 7)
            with open(os.path.join(out, "candidates_rejected.csv"), encoding="utf-8") as fh:
                names = [r["kepoi_name"] for r in csv.DictReader(fh)]
            self.assertEqual(sorted(names), ["K01101.02", "K01922.02", "K02167.02"])


if __name__ == "__main__":
    unittest.main()
