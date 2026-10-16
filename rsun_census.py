"""rsun_census: which published transit solutions in the NASA Exoplanet Archive store a/R* and
Rp/R* that were divided by the Sun's radius instead of the star's?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

Found by hand first (2026-10-16), from solution-census 0.1.0 flags: Hedges et al. 2019
(ApJL 880, L5) prints "a/R*" for all seven of its planets (K2-43 b/c, K2-168 b/c, K2-198 b/c/d)
equal to a / R_sun from Kepler's law with the table's M* (K2-198 b: 0.120268 au / 0.0046505 =
25.861, printed 25.86), and "Rp/R*" within 7% of Rp / R_sun (K2-198 b: 4.189 / 109.076 = 0.0384,
printed 0.039). The printed impact parameters agree with the true a/R* (a / R*) times cos i, so only
the two ratio columns are mislabelled. The Archive stores them as the default pl_ratdor and
pl_ratror for all seven planets.

Per ps row (tran_flag = 1, cb_flag = 0, limit flags all 0):
  dor     pl_ratdor against a / R_sun (a from pl_orbsmax, or Kepler's law with st_mass); a hit is
          within 2%. Tested only if st_rad is at least 0.1 from 1, so a / R_sun and a / R* differ.
  ratror  pl_ratror against Rp / R_sun; a hit is within 7% and closer to it than to Rp / R*.
          Tested only if st_rad is at least 0.15 from 1.
Controls: the same windows centred on 0.85 and 1/0.85 of a / R_sun (and of Rp / R_sun) count how
often a row lands near a / R_sun by chance. Each hit is a candidate to check against the paper.

Usage: python rsun_census.py --out-dir /out [--data-dir /data]
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
UA = f"rsun-census/{VERSION} (Munim, Inc.; mv2@munimtech.com)"
AU_PER_RSUN = 0.0046505
REARTH_PER_RSUN = 109.076
DOR_TOL = 0.02
DOR_MIN_SEP = 0.1
RATROR_TOL = 0.07
RATROR_MIN_SEP = 0.15
CONTROL_CENTRES = (0.85, 1 / 0.85)
# Same columns and cache file as solution-census 0.1.0, so the job reuses its download.
COLS = ["pl_name", "hostname", "default_flag", "tran_flag", "cb_flag", "pl_refname", "st_refname",
        "pl_orbper", "pl_orbsmax", "pl_orbsmaxlim", "pl_orbeccen", "st_mass", "st_masslim", "st_rad", "st_radlim",
        "pl_rade", "pl_radelim", "pl_ratror", "pl_ratrorlim", "pl_ratdor", "pl_ratdorlim",
        "pl_orbincl", "pl_orbincllim", "pl_imppar", "pl_impparlim"]


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


def exact(row, key):
    """The value only if its limit flag is 0 or empty (not an upper or lower limit)."""
    lim = num(row, key + "lim") if key + "lim" in row else None
    return num(row, key) if not lim else None


def ref_text(html):
    if not html:
        return ""
    m = re.search(r">([^<]+)<", html)
    return (m.group(1) if m else html).replace("&amp;", "&").replace("&iacute;", "i").strip()


def semi_major_axis(row):
    a = exact(row, "pl_orbsmax")
    if a and a > 0:
        return a, "pl_orbsmax"
    p, m = num(row, "pl_orbper"), exact(row, "st_mass")
    if p and m and p > 0 and m > 0:
        return (m * (p / 365.25) ** 2) ** (1 / 3), "Kepler"
    return None, ""


def near(q, centre, tol):
    return abs(q / centre - 1) <= tol


def check(row):
    """One result per transiting ps row with at least one testable ratio, else None."""
    if num(row, "tran_flag") != 1 or num(row, "cb_flag") == 1:
        return None
    rs = exact(row, "st_rad")
    if not rs or rs <= 0:
        return None
    rp, kr, dor = exact(row, "pl_rade"), exact(row, "pl_ratror"), exact(row, "pl_ratdor")
    a, a_src = semi_major_axis(row)
    out = {"pl_name": row.get("pl_name", ""), "ref": ref_text(row.get("pl_refname", "")),
           "default_flag": row.get("default_flag", ""), "st_rad": rs, "a_used": "" if a is None else round(a, 6),
           "a_from": a_src, "pl_ratdor": "" if dor is None else dor, "dor_sun": "", "dor_star": "",
           "dor_q": "", "dor_hit": "", "pl_rade": "" if rp is None else rp, "pl_ratror": "" if kr is None else kr,
           "k_sun": "", "k_star": "", "ratror_q": "", "ratror_hit": "", "dor_ctrl": 0, "ratror_ctrl": 0}
    if dor and dor > 0 and a and abs(rs - 1) >= DOR_MIN_SEP:
        ds = a / AU_PER_RSUN
        q = dor / ds
        out.update(dor_sun=round(ds, 3), dor_star=round(ds / rs, 3), dor_q=round(q, 4),
                   dor_hit="yes" if near(q, 1, DOR_TOL) else "no",
                   dor_ctrl=sum(near(q, c, DOR_TOL) for c in CONTROL_CENTRES))
    if kr and kr > 0 and rp and rp > 0 and abs(rs - 1) >= RATROR_MIN_SEP:
        ks = rp / REARTH_PER_RSUN
        q = kr / ks
        closer = abs(math.log(q)) < abs(math.log(q * rs))
        out.update(k_sun=round(ks, 5), k_star=round(ks / rs, 5), ratror_q=round(q, 4),
                   ratror_hit="yes" if near(q, 1, RATROR_TOL) and closer else "no",
                   ratror_ctrl=sum(near(q, c, RATROR_TOL) for c in CONTROL_CENTRES))
    if not out["dor_hit"] and not out["ratror_hit"]:
        return None
    return out


def is_hit(x):
    return x["dor_hit"] == "yes" or x["ratror_hit"] == "yes"


def by_source(results):
    by = {}
    for x in results:
        e = by.setdefault(x["ref"], {"source": x["ref"], "rows": 0, "hit_rows": 0, "both_rows": 0,
                                     "dor_tested": 0, "dor_hits": 0, "ratror_tested": 0, "ratror_hits": 0})
        e["rows"] += 1
        e["hit_rows"] += is_hit(x)
        e["both_rows"] += x["dor_hit"] == "yes" and x["ratror_hit"] == "yes"
        for f in ("dor", "ratror"):
            e[f + "_tested"] += x[f + "_hit"] in ("yes", "no")
            e[f + "_hits"] += x[f + "_hit"] == "yes"
    out = list(by.values())
    out.sort(key=lambda e: (-e["both_rows"], -e["hit_rows"], -e["rows"]))
    return out


def summarize(results):
    stats = {"rows_testable": len(results)}
    for f in ("dor", "ratror"):
        tested = [x for x in results if x[f + "_hit"] in ("yes", "no")]
        stats[f + "_tested"] = len(tested)
        stats[f + "_hits"] = sum(x[f + "_hit"] == "yes" for x in tested)
        # Mean count per control window: what chance alone puts in a window of the same width.
        stats[f + "_control_per_window"] = round(sum(x[f + "_ctrl"] for x in tested) / len(CONTROL_CENTRES), 1)
    stats["rows_both"] = sum(x["dor_hit"] == "yes" and x["ratror_hit"] == "yes" for x in results)
    stats["default_rows_hit"] = sum(is_hit(x) and x["default_flag"] == "1" for x in results)
    return stats


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
    path = os.path.join(args.data_dir, "ps-solutions.csv") if args.data_dir else None
    rows = list(csv.DictReader(fetch("select " + ",".join(COLS) + " from ps where tran_flag = 1", path).splitlines()))
    results = [x for x in (check(r) for r in rows) if x]
    hits = [x for x in results if is_hit(x)]
    hits.sort(key=lambda x: (-(x["dor_hit"] == "yes" and x["ratror_hit"] == "yes"), x["ref"], x["pl_name"]))
    fields = list(results[0].keys()) if results else []
    write_csv(os.path.join(args.out_dir, "hits.csv"), hits, fields)
    sources = by_source(results)
    write_csv(os.path.join(args.out_dir, "by_source.csv"), sources, list(sources[0].keys()) if sources else [])

    stats = {"version": VERSION, "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "ps_transiting_rows": len(rows), **summarize(results)}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

    lines = [f"# rsun-census {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results "
             "CC BY 4.0. A hit is a row whose a/R* or Rp/R* matches the value divided by the Sun's radius "
             "rather than the star's; it is a candidate to check against the paper, not a confirmed error.", ""]
    lines += [f"- {k}: {v}" for k, v in stats.items() if k not in ("version", "run_at")]
    lines += ["", "## Sources with hits", "",
              "| source | rows tested | rows with a hit | both ratios | dor hits/tested | ratror hits/tested |",
              "|---|---|---|---|---|---|"]
    for e in [e for e in sources if e["hit_rows"]][:60]:
        lines.append(f"| {e['source']} | {e['rows']} | {e['hit_rows']} | {e['both_rows']} | "
                     f"{e['dor_hits']}/{e['dor_tested']} | {e['ratror_hits']}/{e['ratror_tested']} |")
    lines += ["", "## Hit rows, both ratios first (first 300)", "",
              "| planet | source | default | R* | a/R* stored | a/R_sun | a/R* | Rp/R* stored | Rp/R_sun | Rp/R* | hits |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in hits[:300]:
        h = ",".join(f for f in ("dor", "ratror") if x[f + "_hit"] == "yes")
        lines.append(f"| {x['pl_name']} | {x['ref']} | {x['default_flag']} | {x['st_rad']} | {x['pl_ratdor']} | "
                     f"{x['dor_sun']} | {x['dor_star']} | {x['pl_ratror']} | {x['k_sun']} | {x['k_star']} | {h} |")
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
