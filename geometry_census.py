"""geometry_census: the transit geometry of every transiting planet in the NASA Exoplanet
Archive's composite table (pscomppars), checked against the orbit and star in the same row.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

Found by hand first (2026-10-15): of the 14 transiting planets with composite
pl_orbincl < 70 deg, 13 cannot transit with the composite's own a and R* (impact
parameter b = (a/R*) cos i = 1.3-7.4). Their pl_ratdor and pl_orbincl come from Kepler KOI
pipeline fits (Q1-Q8, DR24, DR25), which the composite table picks as "the most precise
value"; e.g. Kepler-1943 b: stored a/R* 1.769 against 13.20 from a = 0.05975 au and
R* = 0.973 R_sun.

Per row (tran_flag = 1, cb_flag = 0, R* >= 0.05 R_sun so white-dwarf hosts are left out):
  a/R* from the row = a / (R* x 0.0046505 au), with a from pl_orbsmax or Kepler's third law;
  k = Rp/R* from pl_rade and st_rad;
  flags:  dor     stored pl_ratdor off from a/R* by more than a factor 1.5
          transit b = (a/R*) cos i exceeds 1 + k + 0.05, i.e. no transit (circular orbits,
                  e < 0.1, only; eccentric orbits are listed but not flagged)
          imppar  stored pl_imppar above 1 + k + 0.05 while b from the row is below 1
          ratror  stored pl_ratror off from k by more than a factor 1.5
Each flag is a candidate to check against its source, not a confirmed error.

Usage: python geometry_census.py --out-dir /out [--data-dir /data]
"""
import argparse
import csv
import datetime as dt
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request

VERSION = "0.1.0"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
UA = f"geometry-census/{VERSION} (Munim, Inc.; mv2@munimtech.com)"
AU_PER_RSUN = 0.0046505
REARTH_PER_RSUN = 109.076
DOR_FACTOR = 1.5
RATROR_FACTOR = 1.5
B_MARGIN = 0.05
E_CIRCULAR = 0.1
MIN_STAR_RADIUS = 0.05
COLS = ["pl_name", "hostname", "tran_flag", "cb_flag", "pl_orbper", "pl_orbsmax", "pl_orbsmax_reflink",
        "pl_orbeccen", "st_mass", "st_rad", "st_rad_reflink", "pl_rade", "pl_ratdor", "pl_ratdor_reflink",
        "pl_orbincl", "pl_orbincl_reflink", "pl_imppar", "pl_imppar_reflink", "pl_ratror", "pl_ratror_reflink"]
FLAGS = ("dor", "transit", "imppar", "ratror")


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


def semi_major_axis(row):
    a = num(row, "pl_orbsmax")
    if a and a > 0:
        return a, "pl_orbsmax"
    p, m = num(row, "pl_orbper"), num(row, "st_mass")
    if p and m and p > 0 and m > 0:
        return (m * (p / 365.25) ** 2) ** (1 / 3), "Kepler"
    return None, ""


def check(row):
    """One result per transiting row that can be tested, else None."""
    if num(row, "tran_flag") != 1 or num(row, "cb_flag") == 1:
        return None
    rs = num(row, "st_rad")
    a, a_src = semi_major_axis(row)
    if not rs or rs < MIN_STAR_RADIUS or a is None:
        return None
    dor_calc = a / (rs * AU_PER_RSUN)
    rp = num(row, "pl_rade")
    k = rp / (rs * REARTH_PER_RSUN) if rp and rp > 0 else 0.0
    e = num(row, "pl_orbeccen") or 0.0
    dor, inc, imp, kr = (num(row, c) for c in ("pl_ratdor", "pl_orbincl", "pl_imppar", "pl_ratror"))
    out = {"pl_name": row.get("pl_name", ""), "hostname": row.get("hostname", ""),
           "a_used": round(a, 6), "a_from": a_src, "a_ref": ref_text(row.get("pl_orbsmax_reflink", "")),
           "st_rad": rs, "rad_ref": ref_text(row.get("st_rad_reflink", "")), "e": e,
           "dor_calc": round(dor_calc, 3), "k_calc": round(k, 5),
           "pl_ratdor": "" if dor is None else dor, "dor_ref": ref_text(row.get("pl_ratdor_reflink", "")),
           "dor_ratio": "",
           "pl_orbincl": "" if inc is None else inc, "incl_ref": ref_text(row.get("pl_orbincl_reflink", "")),
           "b_calc": "",
           "pl_imppar": "" if imp is None else imp, "imppar_ref": ref_text(row.get("pl_imppar_reflink", "")),
           "pl_ratror": "" if kr is None else kr, "ratror_ref": ref_text(row.get("pl_ratror_reflink", "")),
           "ratror_ratio": ""}
    for f in FLAGS:
        out["flag_" + f] = ""
    if dor is not None and dor > 0:
        r = dor / dor_calc
        out["dor_ratio"] = round(r, 4)
        out["flag_dor"] = "yes" if r > DOR_FACTOR or r < 1 / DOR_FACTOR else "ok"
    b = None
    if inc is not None and 0 < inc <= 180:
        b = dor_calc * abs(math.cos(math.radians(inc)))
        out["b_calc"] = round(b, 3)
        if e < E_CIRCULAR:
            out["flag_transit"] = "yes" if b > 1 + k + B_MARGIN else "ok"
        else:
            out["flag_transit"] = "eccentric"
    if imp is not None and b is not None and e < E_CIRCULAR:
        out["flag_imppar"] = "yes" if imp > 1 + k + B_MARGIN and b < 1 else "ok"
    if kr is not None and kr > 0 and k > 0:
        r = kr / k
        out["ratror_ratio"] = round(r, 4)
        out["flag_ratror"] = "yes" if r > RATROR_FACTOR or r < 1 / RATROR_FACTOR else "ok"
    return out


def by_source(results, flag, ref_key):
    by = {}
    for x in results:
        if x["flag_" + flag] not in ("yes", "ok"):
            continue
        e = by.setdefault(x[ref_key], {"source": x[ref_key], "tested": 0, "flagged": 0})
        e["tested"] += 1
        e["flagged"] += x["flag_" + flag] == "yes"
    out = list(by.values())
    for e in out:
        e["share_flagged"] = round(e["flagged"] / e["tested"], 4)
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
    path = os.path.join(args.data_dir, "pc-geometry.csv") if args.data_dir else None
    rows = list(csv.DictReader(fetch("select " + ",".join(COLS) + " from pscomppars where tran_flag = 1",
                                     path).splitlines()))
    results = [x for x in (check(r) for r in rows) if x]
    flagged = [x for x in results if any(x["flag_" + f] == "yes" for f in FLAGS)]
    flagged.sort(key=lambda x: -(x["b_calc"] if x["flag_transit"] == "yes" else 0))
    fields = list(results[0].keys()) if results else []
    write_csv(os.path.join(args.out_dir, "flagged.csv"), flagged, fields)
    sources = {"dor": by_source(results, "dor", "dor_ref"), "transit_incl": by_source(results, "transit", "incl_ref"),
               "imppar": by_source(results, "imppar", "imppar_ref"), "ratror": by_source(results, "ratror", "ratror_ref")}
    for name, refs in sources.items():
        write_csv(os.path.join(args.out_dir, f"{name}_by_source.csv"), refs,
                  ["source", "tested", "flagged", "share_flagged"])

    count = lambda f, v: sum(1 for x in results if x["flag_" + f] == v)
    stats = {"version": VERSION, "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "transiting_rows": len(rows), "rows_testable": len(results)}
    for f in FLAGS:
        stats[f + "_tested"] = count(f, "yes") + count(f, "ok")
        stats[f + "_flagged"] = count(f, "yes")
    stats["transit_eccentric_skipped"] = count("transit", "eccentric")
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

    lines = [f"# geometry-census {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results "
             "CC BY 4.0. Each flagged row is a candidate to check against its source, not a confirmed error.", ""]
    lines += [f"- {k}: {v}" for k, v in stats.items() if k not in ("version", "run_at")]
    for name, refs in sources.items():
        lines += ["", f"## {name}: sources with flagged values (first 30)", "",
                  "| source | tested | flagged | share |", "|---|---|---|---|"]
        for e in [e for e in refs if e["flagged"]][:30]:
            lines.append(f"| {e['source']} | {e['tested']} | {e['flagged']} | {e['share_flagged']} |")
    lines += ["", "## Flagged planets, no-transit cases first (first 200)", "",
              "| planet | a/R* stored (source) | a/R* from a, R* | i (source) | b from a, R*, i | "
              "pl_imppar (source) | pl_ratror (source) | k from Rp, R* | flags |",
              "|---|---|---|---|---|---|---|---|---|"]
    for x in flagged[:200]:
        fl = ",".join(f for f in FLAGS if x["flag_" + f] == "yes")
        lines.append(f"| {x['pl_name']} | {x['pl_ratdor']} ({x['dor_ref']}) | {x['dor_calc']} | "
                     f"{x['pl_orbincl']} ({x['incl_ref']}) | {x['b_calc']} | {x['pl_imppar']} ({x['imppar_ref']}) | "
                     f"{x['pl_ratror']} ({x['ratror_ref']}) | {x['k_calc']} | {fl} |")
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
