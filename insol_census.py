"""insol_census: every insolation and equilibrium temperature in the NASA Exoplanet
Archive's composite table (pscomppars), whatever its source, checked against the
star's luminosity and the planet's orbit in the same row.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

Found by hand first (2026-10-15): for TOI-270 b, c and d, TOI-4600 c, TOI-199 b and
TOI-4504 c the composite pl_insol comes from ExoFOP's TOI table and differs from
L / a^2 (same row's st_lum and pl_orbsmax) by factors of 2.5 to 153. ExoFOP's own
table carries the same numbers (TOI-270.03 = b: 131.79 S_earth where L / a^2 = 19).

Expected values:  S = L / a^2 (L in L_sun from st_lum, or from R and Teff when st_lum
is missing or disagrees with them by more than 0.15 dex; a from pl_orbsmax, or from
Kepler's third law with st_mass when pl_orbsmax is missing), and
Teq = 278.6 K * S^(1/4) (zero albedo, full redistribution). A stored value is flagged
when S is off by more than a factor 2 or Teq by more than 25% high / 20% low (albedo and
day-side-only redistribution stay inside that band). Directly imaged planets and
orbits beyond 5 au are left out of the Teq test (their Teq is internal heat).

Usage: python insol_census.py --out-dir /out [--data-dir /data]
"""
import argparse
import csv
import datetime as dt
import json
import math
import os
import re
import statistics
import sys
import urllib.parse
import urllib.request

VERSION = "0.1.0"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
UA = f"insol-census/{VERSION} (Munim, Inc.; mv2@munimtech.com)"
TSUN = 5772.0
T_EQ_1AU = 278.6
LUM_TOL_DEX = 0.15
S_FACTOR = 2.0
TEQ_HIGH, TEQ_LOW = 1.25, 0.80
COLS = ["pl_name", "hostname", "discoverymethod", "pl_orbper", "pl_orbsmax", "st_mass", "st_lum",
        "st_lum_reflink", "st_rad", "st_teff", "pl_insol", "pl_insol_reflink", "pl_eqt", "pl_eqt_reflink"]


def fetch(query, path):
    if path and os.path.exists(path) and os.path.getsize(path) > 1000:
        with open(path, encoding="utf-8") as f:
            return f.read()
    url = TAP + "?" + urllib.parse.urlencode({"query": query, "format": "csv"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=900) as r:
        text = r.read().decode("utf-8")
    if path:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return text


def num(row, key):
    v = (row.get(key) or "").strip()
    if not v:
        return None
    try:
        x = float(v)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def ref_text(html):
    if not html:
        return ""
    m = re.search(r">([^<]+)<", html)
    return (m.group(1) if m else html).replace("&amp;", "&").strip()


def luminosity(row):
    """(L in L_sun, how it was obtained) or (None, '')."""
    lum, r, t = num(row, "st_lum"), num(row, "st_rad"), num(row, "st_teff")
    rt = 2 * math.log10(r) + 4 * math.log10(t / TSUN) if r and t and r > 0 and t > 0 else None
    if lum is not None and (rt is None or abs(lum - rt) <= LUM_TOL_DEX):
        return 10 ** lum, "st_lum"
    if rt is not None:
        return 10 ** rt, "R,Teff"
    return None, ""


def semi_major_axis(row):
    a = num(row, "pl_orbsmax")
    if a and a > 0:
        return a, "pl_orbsmax"
    p, m = num(row, "pl_orbper"), num(row, "st_mass")
    if p and m and p > 0 and m > 0:
        return (m * (p / 365.25) ** 2) ** (1 / 3), "Kepler"
    return None, ""


def check(row):
    """One result per row that can be tested, else None."""
    lum, lum_src = luminosity(row)
    a, a_src = semi_major_axis(row)
    if lum is None or a is None:
        return None
    s_exp = lum / a ** 2
    teq_exp = T_EQ_1AU * s_exp ** 0.25
    s, teq = num(row, "pl_insol"), num(row, "pl_eqt")
    imaged = (row.get("discoverymethod") or "").strip() == "Imaging" or a > 5
    out = {"pl_name": row.get("pl_name", ""), "hostname": row.get("hostname", ""),
           "lum_used": round(lum, 5), "lum_from": lum_src, "a_used": round(a, 6), "a_from": a_src,
           "insol_expected": round(s_exp, 5), "teq_expected": round(teq_exp, 1),
           "pl_insol": "" if s is None else s, "insol_ref": ref_text(row.get("pl_insol_reflink", "")),
           "insol_ratio": "", "insol_flag": "",
           "pl_eqt": "" if teq is None else teq, "eqt_ref": ref_text(row.get("pl_eqt_reflink", "")),
           "eqt_ratio": "", "eqt_flag": ""}
    if s is not None and s > 0:
        r = s / s_exp
        out["insol_ratio"] = round(r, 4)
        out["insol_flag"] = "high" if r > S_FACTOR else "low" if r < 1 / S_FACTOR else "ok"
    if teq is not None and teq > 0 and not imaged:
        r = teq / teq_exp
        out["eqt_ratio"] = round(r, 4)
        out["eqt_flag"] = "high" if r > TEQ_HIGH else "low" if r < TEQ_LOW else "ok"
    return out


def by_reference(results, key_ref, key_flag, key_ratio):
    by = {}
    for x in results:
        if not x[key_flag]:
            continue
        e = by.setdefault(x[key_ref], {"reference": x[key_ref], "tested": 0, "flagged": 0, "ratios": []})
        e["tested"] += 1
        e["flagged"] += x[key_flag] != "ok"
        e["ratios"].append(x[key_ratio])
    out = []
    for e in by.values():
        r = e.pop("ratios")
        e["share_flagged"] = round(e["flagged"] / e["tested"], 4)
        e["median_ratio"] = round(statistics.median(r), 4)
        out.append(e)
    out.sort(key=lambda e: (-e["flagged"], -e["tested"]))
    return out


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-dir", default="")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.data_dir, "pc-insol.csv") if args.data_dir else None
    rows = list(csv.DictReader(fetch("select " + ",".join(COLS) + " from pscomppars", path).splitlines()))
    results = [x for x in (check(r) for r in rows) if x]
    flagged = [x for x in results if x["insol_flag"] in ("high", "low") or x["eqt_flag"] in ("high", "low")]
    flagged.sort(key=lambda x: -max(abs(math.log10(x["insol_ratio"])) if x["insol_ratio"] else 0,
                                    abs(math.log10(x["eqt_ratio"])) * 4 if x["eqt_ratio"] else 0))
    fields = list(results[0].keys()) if results else []
    write_csv(os.path.join(args.out_dir, "flagged.csv"), flagged, fields)
    insol_refs = by_reference(results, "insol_ref", "insol_flag", "insol_ratio")
    eqt_refs = by_reference(results, "eqt_ref", "eqt_flag", "eqt_ratio")
    ref_fields = ["reference", "tested", "flagged", "share_flagged", "median_ratio"]
    write_csv(os.path.join(args.out_dir, "insol_by_reference.csv"), insol_refs, ref_fields)
    write_csv(os.path.join(args.out_dir, "eqt_by_reference.csv"), eqt_refs, ref_fields)

    count = lambda key, val: sum(1 for x in results if x[key] == val)
    stats = {
        "version": VERSION, "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "pscomppars_rows": len(rows), "rows_testable": len(results),
        "insol_tested": sum(1 for x in results if x["insol_flag"]),
        "insol_high": count("insol_flag", "high"), "insol_low": count("insol_flag", "low"),
        "eqt_tested": sum(1 for x in results if x["eqt_flag"]),
        "eqt_high": count("eqt_flag", "high"), "eqt_low": count("eqt_flag", "low"),
        "exofop_insol": next((e for e in insol_refs if e["reference"] == "ExoFOP"), None),
        "exofop_eqt": next((e for e in eqt_refs if e["reference"] == "ExoFOP"), None),
    }
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

    lines = [f"# insol-census {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results "
             "CC BY 4.0. Each flagged row is a candidate to check against its source, not a confirmed error.", ""]
    lines += [f"- {k}: {v}" for k, v in stats.items() if k not in ("version", "run_at")]
    for title, refs in (("Insolation", insol_refs), ("Equilibrium temperature", eqt_refs)):
        lines += ["", f"## {title}: sources with flagged values (first 40)", "",
                  "| source | tested | flagged | share | median stored/expected |", "|---|---|---|---|---|"]
        for e in [e for e in refs if e["flagged"]][:40]:
            lines.append(f"| {e['reference']} | {e['tested']} | {e['flagged']} | {e['share_flagged']} | "
                         f"{e['median_ratio']} |")
    lines += ["", "## Flagged planets, largest disagreement first (first 150)", "",
              "| planet | pl_insol (source) | L/a^2 | ratio | pl_eqt (source) | expected | ratio | L from | a from |",
              "|---|---|---|---|---|---|---|---|---|"]
    for x in flagged[:150]:
        lines.append(f"| {x['pl_name']} | {x['pl_insol']} ({x['insol_ref']}) | {x['insol_expected']} | "
                     f"{x['insol_ratio']} | {x['pl_eqt']} ({x['eqt_ref']}) | {x['teq_expected']} | "
                     f"{x['eqt_ratio']} | {x['lum_from']} | {x['a_from']} |")
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
