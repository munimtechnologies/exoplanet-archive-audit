"""orphan_reject: are Kepler's 600 "orphan" CANDIDATEs rejected by Lissauer et al. 2024 more often when the
final pipeline run (DR25) found nothing at all on their star?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

Joins two published outputs of munimtechnologies/exoplanet-archive-audit:
  results/2026-10-17-koi-orphans-0.1.0/orphans.csv   (koi_orphans 0.1.0: one row per orphan, its census status)
  results/2026-10-17-lissauer-xmatch-0.1.0/xmatch.csv (lissauer_xmatch 0.1.0: Lissauer 2024 Status per KOI)
and the DR25 rogue-TCE flags from the Archive's TAP service (q1_q17_dr25_tce, tce_rogue_flag = 1).

    python orphan_reject.py --out-dir out                       # live: GitHub raw + Archive TAP
    python orphan_reject.py --out-dir out --orphans o.csv --xmatch x.csv --rogue r.csv
"""
import argparse
import csv
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from math import comb

VERSION = "0.1.0"
RAW = "https://raw.githubusercontent.com/munimtechnologies/exoplanet-archive-audit/main/"
ORPHANS_URL = RAW + "results/2026-10-17-koi-orphans-0.1.0/orphans.csv"
XMATCH_URL = RAW + "results/2026-10-17-lissauer-xmatch-0.1.0/xmatch.csv"
TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
ROGUE_QUERY = "select kepid,tce_plnt_num from q1_q17_dr25_tce where tce_rogue_flag=1"
UA = f"orphan_reject/{VERSION} (MV2 of Munim, Inc.; mv2@munimtech.com)"
REJECT = set("FSMR")
STATUSES = ["no_tce", "unrelated", "offset", "same_events"]


def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read().decode("utf-8")
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(10 * (i + 1))


def read_csv(text):
    return list(csv.DictReader(io.StringIO(text.replace("\r\n", "\n"))))


def fisher_greater(a, b, c, d):
    """One-sided Fisher exact p: chance of >= a in the top-left cell of [[a, b], [c, d]] with margins fixed."""
    r1, c1, n = a + b, a + c, a + b + c + d
    total = comb(n, c1)
    hi = min(r1, c1)
    return sum(comb(r1, k) * comb(n - r1, c1 - k) for k in range(a, hi + 1)) / total


def rate(rows):
    n = len(rows)
    k = sum(1 for r in rows if r["rejected"])
    return {"n": n, "rejected": k, "fraction": round(k / n, 4) if n else None}


def analyse(orphans, xmatch, rogue_pairs):
    """orphans, xmatch: lists of dicts as in the published CSVs; rogue_pairs: set of (kepid, tce_plnt_num)."""
    status_of = {r["kepoi_name"]: r for r in xmatch}
    rogue_stars = {k for k, _ in rogue_pairs}
    rows, missing = [], []
    for o in orphans:
        x = status_of.get(o["kepoi_name"])
        if x is None:
            missing.append(o["kepoi_name"])
            continue
        letter = x["lissauer_now"]
        tce = o.get("tce_plnt_num") or ""
        kepid = int(o["kepid"])
        rows.append({
            "kepoi_name": o["kepoi_name"], "kepid": kepid, "prov": o["prov"], "status": o["status"],
            "kind": o.get("kind", ""), "tce_plnt_num": tce, "lissauer_status": x["lissauer_status"],
            "lissauer_now": letter, "rejected": letter in REJECT,
            "matched_tce_rogue": bool(tce) and (kepid, int(tce)) in rogue_pairs,
            "rogue_on_star": kepid in rogue_stars,
        })
    by_status = {s: rate([r for r in rows if r["status"] == s]) for s in STATUSES}
    no_tce = [r for r in rows if r["status"] == "no_tce"]
    with_tce = [r for r in rows if r["status"] != "no_tce"]
    a = sum(r["rejected"] for r in no_tce)
    c = sum(r["rejected"] for r in with_tce)
    p = fisher_greater(a, len(no_tce) - a, c, len(with_tce) - c) if rows else None
    reasons = {}
    for r in rows:
        if r["rejected"]:
            reasons.setdefault(r["status"], {}).setdefault(r["lissauer_now"], 0)
            reasons[r["status"]][r["lissauer_now"]] += 1
    rogue_same = [r for r in rows if r["status"] == "same_events" and r["matched_tce_rogue"]]
    return rows, {
        "version": VERSION,
        "n_orphans": len(orphans),
        "n_joined": len(rows),
        "missing_from_xmatch": missing,
        "rejected_total": sum(r["rejected"] for r in rows),
        "by_status": by_status,
        "by_prov": {pv: rate([r for r in rows if r["prov"] == pv]) for pv in sorted({r["prov"] for r in rows})},
        "no_tce_vs_with_tce": {"no_tce": rate(no_tce), "with_tce": rate(with_tce), "fisher_p_greater": p},
        "reject_letters_by_status": reasons,
        "same_events_on_rogue_tce": [
            f'{r["kepoi_name"]} TCE {r["tce_plnt_num"]} Lissauer {r["lissauer_status"]}' for r in rogue_same],
        "orphans_with_rogue_on_star": sum(r["rogue_on_star"] for r in rows),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--orphans")
    ap.add_argument("--xmatch")
    ap.add_argument("--rogue")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)

    def load(path, url):
        if path:
            with open(path, encoding="utf-8") as f:
                return f.read()
        return fetch(url)

    rogue_url = TAP_URL + "?" + urllib.parse.urlencode({"query": ROGUE_QUERY, "format": "csv"})
    orphans = read_csv(load(args.orphans, ORPHANS_URL))
    xmatch = read_csv(load(args.xmatch, XMATCH_URL))
    rogue_rows = read_csv(load(args.rogue, rogue_url))
    rogue_pairs = {(int(r["kepid"]), int(r["tce_plnt_num"])) for r in rogue_rows}
    rows, summary = analyse(orphans, xmatch, rogue_pairs)
    summary["n_rogue_tces"] = len(rogue_pairs)
    summary["sources"] = {"orphans": args.orphans or ORPHANS_URL, "xmatch": args.xmatch or XMATCH_URL,
                          "rogue": args.rogue or rogue_url,
                          "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(os.path.join(args.out_dir, "orphan_reject.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["kepoi_name"])
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    json.dump(summary, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
