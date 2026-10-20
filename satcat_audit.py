#!/usr/bin/env python3
# satcat_audit.py 0.1.1
# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# MV2 (Munim, Inc.), mv2@munimtech.com. Written by AI agents working in his name.
"""Internal-consistency audit of the CelesTrak SATCAT CSV (lane E, pre-registered decisions E1-E4).

Pure standard library. Decimal arithmetic. Every served number is treated as a last-digit interval
(the served string '3819' means [3818.5, 3819.5]; '132.59' means [132.585, 132.595]).

Decisions (see findings/<date>-satcat-prereg.md for the full wording):
  E1 Kepler consistency: among ORBIT_CENTER = EA rows with PERIOD, APOGEE and PERIGEE present and
     APOGEE >= PERIGEE, a row is a MISMATCH if the served-period interval and the Kepler-period interval
     (from the apogee/perigee intervals, WGS-72 mu = 398600.8 km^3/s^2, R = 6378.135 km) are separated by
     more than 0.5 % of the mid Kepler period.  Holds if mismatches <= 1 % (100 k <= n), n >= 20,000.
  E2 Survivability: among rows with ORBIT_CENTER = EA, ORBIT_TYPE = ORB, empty DECAY_DATE, empty
     DATA_STATUS_CODE and a PERIGEE, the share with PERIGEE < 120 km is <= 0.1 % (1000 k <= n), n >= 20,000.
  E3 Date order: rows with both dates where DECAY_DATE (first 10 characters) sorts before LAUNCH_DATE: k = 0,
     n >= 1,000.
  E4 Apsides: rows with both APOGEE and PERIGEE where APOGEE < PERIGEE: k = 0, n >= 20,000.
Rows whose NORAD_CAT_ID is in EXCLUDED_NORAD (looked at before pre-registration) are never scored.

"Present" means the served string is a finite number (for dates: starts with YYYY-MM-DD). The format page
says missing values are "null if no data available", so an empty cell and the tokens null / none / n/a /
nan / - all count as MISSING. Any other non-numeric or non-date string is also treated as missing and is
counted, by field and token, under descriptive_not_scored.unusable_tokens, so nothing is hidden.

Changes 0.1.0 -> 0.1.1 (before any catalogue row was read): missing-token handling, date-format check,
--data-dir (finds the downloaded catalogue without assuming its file name), unusable-token counts.

Usage: python satcat_audit.py --csv /data/satcat.csv --out-dir /out
       python satcat_audit.py --data-dir /data --out-dir /out
"""
import argparse
import csv
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation, getcontext

getcontext().prec = 40

VERSION = "0.1.1"
MU = Decimal("398600.8")        # km^3/s^2, WGS-72 gravitational parameter used by SGP4
R_EARTH = Decimal("6378.135")   # km, WGS-72 equatorial radius used by SGP4 / Space-Track altitudes
PI = Decimal("3.14159265358979323846264338327950288")
SLACK = Decimal("0.005")        # E1: 0.5 % of the mid Kepler period, on top of rounding
PERIGEE_FLOOR_KM = Decimal("120")
# Served records read on 2026-10-20 to fix the decimal precision (Vanguard 1, ISS). Never scored.
EXCLUDED_NORAD = frozenset({"5", "25544"})
# Tokens that mean "no data" (compared lower-case after stripping). "" is the documented blank.
MISSING_TOKENS = frozenset({"", "null", "none", "n/a", "na", "nan", "-"})
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
NUMERIC_FIELDS = ("PERIOD", "APOGEE", "PERIGEE")
DATE_FIELDS = ("LAUNCH_DATE", "DECAY_DATE")

COLUMNS = ["OBJECT_NAME", "OBJECT_ID", "NORAD_CAT_ID", "OBJECT_TYPE", "OPS_STATUS_CODE", "OWNER",
           "LAUNCH_DATE", "LAUNCH_SITE", "DECAY_DATE", "PERIOD", "INCLINATION", "APOGEE", "PERIGEE",
           "RCS", "DATA_STATUS_CODE", "ORBIT_CENTER", "ORBIT_TYPE"]


def text(served):
    """Stripped served string, or '' when it is a documented missing token."""
    s = (served or "").strip()
    return "" if s.lower() in MISSING_TOKENS else s


def num(served):
    """Decimal from a served numeric string; None if missing or not a finite number."""
    s = text(served)
    if s == "":
        return None
    try:
        d = Decimal(s)
    except InvalidOperation:
        return None
    return d if d.is_finite() else None


def interval(served):
    """Last-digit interval (lo, hi) of a served decimal string."""
    d = Decimal(served.strip())
    exp = d.as_tuple().exponent
    if not isinstance(exp, int):
        raise ValueError("not a finite number: %r" % served)
    half = Decimal(1).scaleb(exp) / 2
    return d - half, d + half


def period_minutes(apogee_km, perigee_km):
    """Two-body period in minutes from apogee and perigee altitudes (Decimal km)."""
    a = R_EARTH + (apogee_km + perigee_km) / 2
    return 2 * PI * (a ** 3 / MU).sqrt() / 60


def kepler_check(period_s, apogee_s, perigee_s, slack=SLACK):
    """Return (mismatch, gap_minutes, p_mid, signed_residual).

    gap is the distance between the served-period interval and the Kepler-period interval (0 if they
    overlap). mismatch is True when gap > slack * p_mid. signed_residual = served mid - Kepler mid."""
    p_lo, p_hi = interval(period_s)
    ap_lo, ap_hi = interval(apogee_s)
    pe_lo, pe_hi = interval(perigee_s)
    k_lo = period_minutes(ap_lo, pe_lo)
    k_hi = period_minutes(ap_hi, pe_hi)
    p_mid = period_minutes(Decimal(apogee_s.strip()), Decimal(perigee_s.strip()))
    gap = max(Decimal(0), p_lo - k_hi, k_lo - p_hi)
    residual = Decimal(period_s.strip()) - p_mid
    return gap > slack * p_mid, gap, p_mid, residual


def classify(row):
    """Flags for one SATCAT row (a dict keyed by the CSV header)."""
    g = lambda k: (row.get(k) or "").strip()
    norad, center, otype = g("NORAD_CAT_ID"), g("ORBIT_CENTER"), g("ORBIT_TYPE")
    period, apo, peri = text(g("PERIOD")), text(g("APOGEE")), text(g("PERIGEE"))
    decay, launch, status = text(g("DECAY_DATE")), text(g("LAUNCH_DATE")), text(g("DATA_STATUS_CODE"))
    per_d, apo_d, peri_d = num(period), num(apo), num(peri)
    launch_ok, decay_ok = bool(DATE_RE.match(launch)), bool(DATE_RE.match(decay))
    unusable = {}
    for name, raw, ok in (("PERIOD", period, per_d is not None), ("APOGEE", apo, apo_d is not None),
                          ("PERIGEE", peri, peri_d is not None), ("LAUNCH_DATE", launch, launch_ok),
                          ("DECAY_DATE", decay, decay_ok)):
        if raw != "" and not ok:
            unusable[name] = raw.lower()
    out = {"norad": norad, "excluded": norad in EXCLUDED_NORAD, "unusable": unusable}
    out["e4_eligible"] = apo_d is not None and peri_d is not None
    out["e4_violation"] = out["e4_eligible"] and apo_d < peri_d
    out["e1_eligible"] = center == "EA" and per_d is not None and out["e4_eligible"] and not out["e4_violation"]
    if out["e1_eligible"]:
        mis, gap, pmid, res = kepler_check(period, apo, peri)
        out["e1_mismatch"] = mis
        out["e1_gap_min"] = str(gap.quantize(Decimal("0.0001")))
        out["e1_rel_ppm"] = str((res / pmid * 1000000).quantize(Decimal("1")))
    else:
        out["e1_mismatch"] = False
    out["e2_eligible"] = (center == "EA" and otype == "ORB" and decay == "" and status == "" and peri_d is not None)
    out["e2_violation"] = out["e2_eligible"] and peri_d < PERIGEE_FLOOR_KM
    out["e3_eligible"] = launch_ok and decay_ok
    out["e3_violation"] = out["e3_eligible"] and decay[:10] < launch[:10]
    out["status"] = status
    out["served"] = {"PERIOD": period, "APOGEE": apo, "PERIGEE": peri, "LAUNCH_DATE": launch,
                     "DECAY_DATE": decay, "ORBIT_CENTER": center, "ORBIT_TYPE": otype,
                     "DATA_STATUS_CODE": status}
    return out


def decide(test, n, k):
    """Pre-registered decision for one test from its counts only."""
    power = {"E1": 20000, "E2": 20000, "E3": 1000, "E4": 20000}[test]
    if n < power:
        return "underpowered"
    if test == "E1":
        return "holds" if 100 * k <= n else "fails"
    if test == "E2":
        return "holds" if 1000 * k <= n else "fails"
    return "holds" if k == 0 else "fails"


def median(values):
    s = sorted(values)
    m = len(s)
    if m == 0:
        return None
    return s[m // 2] if m % 2 else (s[m // 2 - 1] + s[m // 2]) / 2


def audit(rows):
    """Score an iterable of row dicts. Returns (summary dict, lists of flagged rows)."""
    n = {"E1": 0, "E2": 0, "E3": 0, "E4": 0}
    k = {"E1": 0, "E2": 0, "E3": 0, "E4": 0}
    flagged = {"E1": [], "E2": [], "E3": [], "E4": []}
    residuals, pos, neg = [], 0, 0
    by_status = {}
    unusable = {f: {} for f in NUMERIC_FIELDS + DATE_FIELDS}
    total = excluded = 0
    for row in rows:
        total += 1
        c = classify(row)
        if c["excluded"]:
            excluded += 1
            continue
        for field, token in c["unusable"].items():
            d = unusable[field]
            key = token if (token in d or len(d) < 20) else "(other)"
            d[key] = d.get(key, 0) + 1
        for t in ("E1", "E2", "E3", "E4"):
            key = t.lower()
            if c[key + "_eligible"]:
                n[t] += 1
                hit = c["e1_mismatch"] if t == "E1" else c[key + "_violation"]
                if hit:
                    k[t] += 1
                    rec = {"NORAD_CAT_ID": c["norad"]}
                    rec.update(c["served"])
                    if t == "E1":
                        rec["gap_min"] = c["e1_gap_min"]
                        rec["rel_ppm"] = c["e1_rel_ppm"]
                    flagged[t].append(rec)
        if c["e1_eligible"]:
            r = Decimal(c["e1_rel_ppm"])
            residuals.append(r)
            pos += r > 0
            neg += r < 0
            st = c["status"] or "(blank)"
            d = by_status.setdefault(st, {"n": 0, "mismatch": 0})
            d["n"] += 1
            d["mismatch"] += bool(c["e1_mismatch"])
    med = median(residuals)
    summary = {
        "tool": "satcat_audit.py", "version": VERSION, "rows_total": total, "rows_excluded": excluded,
        "excluded_norad": sorted(EXCLUDED_NORAD, key=int),
        "constants": {"mu_km3_s2": str(MU), "r_earth_km": str(R_EARTH), "e1_slack": str(SLACK),
                      "e2_perigee_floor_km": str(PERIGEE_FLOOR_KM)},
        "tests": {t: {"n": n[t], "k": k[t], "decision": decide(t, n[t], k[t])} for t in n},
        "descriptive_not_scored": {
            "e1_residual_ppm_median": None if med is None else str(med),
            "e1_residual_positive": pos, "e1_residual_negative": neg,
            "e1_by_data_status_code": by_status,
            "unusable_tokens": unusable,
        },
    }
    return summary, flagged


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit("missing columns: %s" % ", ".join(missing))
        for row in reader:
            yield row


def find_csv(data_dir):
    """The downloaded catalogue under data_dir: a *.csv named like satcat, else any *.csv, else the only file."""
    found = []
    for root, _dirs, files in os.walk(data_dir):
        found.extend(os.path.join(root, f) for f in files)
    found.sort()
    csvs = [p for p in found if p.lower().endswith(".csv")]
    named = [p for p in csvs if "satcat" in os.path.basename(p).lower()]
    pick = named or csvs or (found if len(found) == 1 else [])
    if not pick:
        raise SystemExit("no catalogue file under %s: %s" % (data_dir, [os.path.relpath(p, data_dir) for p in found]))
    return pick[0]


def write_flagged(out_dir, flagged):
    for t, recs in flagged.items():
        path = os.path.join(out_dir, "%s-flagged.csv" % t.lower())
        fields = ["NORAD_CAT_ID", "PERIOD", "APOGEE", "PERIGEE", "LAUNCH_DATE", "DECAY_DATE",
                  "ORBIT_CENTER", "ORBIT_TYPE", "DATA_STATUS_CODE"] + (["gap_min", "rel_ppm"] if t == "E1" else [])
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in recs:
                w.writerow(r)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csv", help="path to the downloaded SATCAT CSV")
    ap.add_argument("--data-dir", help="directory holding the downloaded SATCAT CSV (used when --csv is not given)")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    if not args.csv and not args.data_dir:
        ap.error("give --csv or --data-dir")
    path = args.csv or find_csv(args.data_dir)
    os.makedirs(args.out_dir, exist_ok=True)
    summary, flagged = audit(read_rows(path))
    summary["source_file"] = os.path.basename(path)
    summary["source_bytes"] = os.path.getsize(path)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, sort_keys=True)
    write_flagged(args.out_dir, flagged)
    print(json.dumps(summary["tests"], indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
