"""depth_census: in which NASA Exoplanet Archive rows does the stored radius ratio Rp/R* disagree
with both the row's own transit depth and its own Rp / R*?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

Found by hand first (2026-10-16), three default rows where pl_ratror is the odd one out:
  TOI-4427 b (Guenther et al. 2026, AJ 172, 54): pl_ratror 0.1073, but sqrt(depth 1.8614%) = 0.1364
    and Rp / R* = 13.092 / (0.89 x 109.076) = 0.1349. 0.1073 is the paper's Table 4 value for its
    neighbour TOI-2578 b.
  TOI-2049 b (same paper): pl_ratror 1.49 (a planet larger than its star) is the planet's radius in
    Jupiter radii; sqrt(depth 0.2275%) = 0.0477 and Rp / R* = 16.645 / (3.2 x 109.076) = 0.0477.
  TOI-2048 b (Newton et al. 2022, composite row): pl_ratror 0.0239 is Rp / R_sun; Rp / R* = 0.0303
    and the composite depth (ExoFOP, 0.114%) gives 0.0338.

Per row (tran_flag = 1, cb_flag = 0, limit flags all 0), three estimates of the radius ratio:
  k   pl_ratror
  s   sqrt(pl_trandep / 100), the depth in percent
  kr  pl_rade / (st_rad x 109.076)
Two estimates agree if the larger is at most 1 + AGREE times the smaller (limb darkening alone
moves sqrt(depth) by up to about 15%). The class names the odd one out:
  ok        every available pair agrees
  ratror    s and kr agree, k agrees with neither (the target)
  trandep   k and kr agree, s agrees with neither (e.g. a depth unit slip)
  radius    k and s agree, kr agrees with neither (e.g. dilution-corrected Rp, or a wrong R*)
  two-way   only k and one other estimate exist, and they disagree
  mixed     any other pattern
  grazing   |b| > 1 - min(k, s, kr): the depth is not ~k^2, so the row is not judged
Rows where min(k, s, kr) > 0.4 (white-dwarf hosts and the like) are skipped.
Both the ps table (one row per published solution) and pscomppars (the composite default, whose
columns can come from different papers) are checked; composite rows say whether all four
columns come from one source.

Usage: python depth_census.py --out-dir /out [--data-dir /data]
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
UA = f"depth-census/{VERSION} (Munim, Inc.; mv2@munimtech.com)"
REARTH_PER_RSUN = 109.076
AGREE = 0.18
MAX_K = 0.4
CLASSES = ("ratror", "trandep", "radius", "two-way", "mixed", "grazing", "ok")
PS_COLS = ["pl_name", "hostname", "default_flag", "tran_flag", "cb_flag", "pl_refname",
           "pl_ratror", "pl_ratrorlim", "pl_trandep", "pl_trandeplim", "pl_rade", "pl_radelim",
           "st_rad", "st_radlim", "pl_imppar", "pl_impparlim"]
COMP_COLS = ["pl_name", "hostname", "tran_flag", "cb_flag",
             "pl_ratror", "pl_ratrorlim", "pl_ratror_reflink", "pl_trandep", "pl_trandeplim", "pl_trandep_reflink",
             "pl_rade", "pl_radelim", "pl_rade_reflink", "st_rad", "st_radlim", "st_rad_reflink",
             "pl_imppar", "pl_impparlim"]


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


def agree(x, y):
    return max(x / y, y / x) <= 1 + AGREE


def classify(k, s, kr, b=None):
    """The class of one row's three radius-ratio estimates (s or kr may be None)."""
    if b is not None and abs(b) > 1 - min(x for x in (k, s, kr) if x is not None):
        return "grazing"
    if s is None or kr is None:
        other = s if kr is None else kr
        return "ok" if agree(k, other) else "two-way"
    ks, kk, sk = agree(k, s), agree(k, kr), agree(s, kr)
    if ks and kk and sk:
        return "ok"
    if sk and not ks and not kk:
        return "ratror"
    if kk and not ks and not sk:
        return "trandep"
    if ks and not kk and not sk:
        return "radius"
    return "mixed"


def check(row, composite=False):
    """One result per transiting row with pl_ratror and at least one other estimate, else None."""
    if num(row, "tran_flag") != 1 or num(row, "cb_flag") == 1:
        return None
    k = exact(row, "pl_ratror")
    if not k or k <= 0:
        return None
    d, rp, rs = exact(row, "pl_trandep"), exact(row, "pl_rade"), exact(row, "st_rad")
    s = math.sqrt(d / 100) if d and d > 0 else None
    kr = rp / (rs * REARTH_PER_RSUN) if rp and rs and rp > 0 and rs > 0 else None
    if s is None and kr is None:
        return None
    if min(x for x in (k, s, kr) if x is not None) > MAX_K:
        return None
    b = exact(row, "pl_imppar")
    out = {"pl_name": row.get("pl_name", ""), "table": "pscomppars" if composite else "ps",
           "default_flag": "1" if composite else row.get("default_flag", ""),
           "pl_ratror": k, "pl_trandep": "" if d is None else d, "pl_rade": "" if rp is None else rp,
           "st_rad": "" if rs is None else rs, "pl_imppar": "" if b is None else b,
           "k_depth": "" if s is None else round(s, 5), "k_radii": "" if kr is None else round(kr, 5),
           "depth_over_k2": "" if d is None else round(d / 100 / k ** 2, 4),
           "class": classify(k, s, kr, b)}
    if composite:
        refs = {f: ref_text(row.get(f + "_reflink", "")) for f in ("pl_ratror", "pl_trandep", "pl_rade", "st_rad")}
        out["ref"] = refs["pl_ratror"]
        out["trandep_ref"] = refs["pl_trandep"]
        out["radius_refs"] = refs["pl_rade"] + " / " + refs["st_rad"]
        used = [refs["pl_ratror"]] + [refs[f] for f, v in (("pl_trandep", d), ("pl_rade", rp), ("st_rad", rs)) if v]
        out["one_source"] = "yes" if len(set(used)) == 1 else "no"
    else:
        out["ref"] = ref_text(row.get("pl_refname", ""))
        out["trandep_ref"] = out["radius_refs"] = ""
        out["one_source"] = "yes"
    return out


def is_flag(x):
    return x["class"] not in ("ok", "grazing")


def summarize(results):
    stats = {"rows_checked": len(results)}
    for c in CLASSES:
        stats[c] = sum(x["class"] == c for x in results)
    stats["default_ratror"] = sum(x["class"] == "ratror" and x["default_flag"] == "1" for x in results)
    return stats


def by_source(results):
    by = {}
    for x in results:
        e = by.setdefault(x["ref"], {"source": x["ref"], "rows": 0, **{c: 0 for c in CLASSES}})
        e["rows"] += 1
        e[x["class"]] += 1
    out = list(by.values())
    out.sort(key=lambda e: (-e["ratror"], -e["trandep"], -(e["rows"] - e["ok"] - e["grazing"]), e["source"]))
    return out


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def run_table(name, query, path, composite):
    try:
        rows = list(csv.DictReader(fetch(query, path).splitlines()))
    except Exception as e:  # one table failing should not lose the other
        return [], {"table": name, "error": f"{type(e).__name__}: {e}"}
    results = [x for x in (check(r, composite) for r in rows) if x]
    return results, {"table": name, "transiting_rows": len(rows), **summarize(results)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-dir", default="")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    p = (lambda f: os.path.join(args.data_dir, f)) if args.data_dir else (lambda f: None)
    ps, ps_stats = run_table("ps", "select " + ",".join(PS_COLS) + " from ps where tran_flag = 1",
                             p("ps-depth.csv"), False)
    comp, comp_stats = run_table("pscomppars", "select " + ",".join(COMP_COLS) + " from pscomppars where tran_flag = 1",
                                 p("pscomp-depth.csv"), True)
    results = ps + comp
    order = {c: i for i, c in enumerate(CLASSES)}
    flags = sorted((x for x in results if is_flag(x)),
                   key=lambda x: (order[x["class"]], x["default_flag"] != "1", x["table"], x["ref"], x["pl_name"]))
    fields = ["pl_name", "table", "ref", "default_flag", "class", "pl_ratror", "k_depth", "k_radii", "depth_over_k2",
              "pl_trandep", "pl_rade", "st_rad", "pl_imppar", "one_source", "trandep_ref", "radius_refs"]
    write_csv(os.path.join(args.out_dir, "flags.csv"), flags, fields)
    sources = by_source(ps)
    write_csv(os.path.join(args.out_dir, "by_source.csv"), sources, ["source", "rows", *CLASSES])

    stats = {"version": VERSION, "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "agree_factor": 1 + AGREE, "ps": ps_stats, "pscomppars": comp_stats}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

    lines = [f"# depth-census {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results "
             "CC BY 4.0. A flag is a row whose three radius-ratio estimates (pl_ratror, sqrt of the depth, "
             "Rp/R*) disagree; it is a candidate to check against the paper, not a confirmed error.", ""]
    for t in (ps_stats, comp_stats):
        lines.append("- " + ", ".join(f"{k}: {v}" for k, v in t.items()))
    lines += ["", "## ps sources with flags (first 60)", "",
              "| source | rows | " + " | ".join(CLASSES) + " |", "|---|---|" + "---|" * len(CLASSES)]
    for e in [e for e in sources if e["rows"] - e["ok"] - e["grazing"]][:60]:
        lines.append(f"| {e['source']} | {e['rows']} | " + " | ".join(str(e[c]) for c in CLASSES) + " |")
    lines += ["", "## Flagged rows, ratror class first, defaults first (first 400)", "",
              "| planet | table | source | default | class | pl_ratror | sqrt(depth) | Rp/R* | depth/k^2 | one source |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for x in flags[:400]:
        lines.append(f"| {x['pl_name']} | {x['table']} | {x['ref']} | {x['default_flag']} | {x['class']} | "
                     f"{x['pl_ratror']} | {x['k_depth']} | {x['k_radii']} | {x['depth_over_k2']} | {x['one_source']} |")
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=1))
    return 0 if "error" not in ps_stats else 1


if __name__ == "__main__":
    sys.exit(main())
