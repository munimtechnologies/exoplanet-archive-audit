"""alias_dupes: is any confirmed planet the same planet as a sibling, listed again at a period alias?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

Built after Kepler-289 e (330.0716 d, Ofir et al. 2025) turned out to be Kepler-289 d (66.0282 d)
found at five times its period: ratio 4.9989, and the 330-day events land within minutes of d's
measured transits (findings/2026-10-16-kepler-289.md). This looks for the same pattern across the
whole Archive.

Method, per system with two or more planets in the composite table (pscomppars):
1. For each pair (short period Ps, long period Pl): k = round(Pl / Ps); rel = |Pl / Ps - k| / k.
   A pair is a candidate if k >= 1 and rel <= REL_TOL.
2. If both have a mid-transit time: n = round((Tl - Ts) / Ps), off = (Tl - Ts) - n Ps,
   phase = |off| / Ps.
     same_events  phase <= PHASE_TOL: the long-period planet's transits fall on the short one's
                  (or two names share one period and one phase, k = 1);
     offset       phase > PHASE_TOL: an integer period ratio but different transits, as in a real
                  resonant pair.
   Otherwise: no_epoch (period ratio only; typical of radial-velocity planets).
3. drift_d = |Pl - k Ps| * BASELINE / Pl: how far a strict alias would slide over a Kepler-length
   baseline. Large values with same_events point to TTVs or a chance match; check by hand.
A flag is a lead for a hand check against the papers, not a finding.

Usage: python alias_dupes.py --out-dir /out [--csv pscomppars.csv]
"""
import argparse
import csv
import json
import math
import os
import urllib.parse
import urllib.request

VERSION = "0.1.0"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
UA = f"alias-dupes/{VERSION} (Munim, Inc.; mv2@munimtech.com)"
REL_TOL = 0.002
PHASE_TOL = 0.01
BASELINE = 1460.0  # Kepler Q1-Q17, days
QUERY = ("select hostname,pl_name,pl_orbper,pl_orbpererr1,pl_tranmid,pl_tranmiderr1,pl_rade,"
         "disc_year,disc_facility,sy_pnum from pscomppars where sy_pnum > 1")
FIELDS = ["hostname", "short", "long", "p_short", "p_long", "k", "rel", "status", "n", "off_d",
          "phase", "drift_d", "disc_short", "disc_long", "rade_short", "rade_long"]
ORDER = {"same_events": 0, "no_epoch": 1, "offset": 2}


def http_text(url, timeout=600):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def num(row, key):
    v = (row.get(key) or "").strip()
    try:
        x = float(v)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def classify(ps, ts, pl, tl):
    """Pair test for short period ps (mid-time ts) and long period pl (tl); times may be None.
    Returns None if the ratio is not near an integer, else a dict with k, rel, status, n, off, phase, drift."""
    if not ps or not pl or ps <= 0 or pl < ps:
        return None
    r = pl / ps
    k = round(r)
    if k < 1:
        return None
    rel = abs(r - k) / k
    if rel > REL_TOL:
        return None
    out = {"k": k, "rel": rel, "drift_d": abs(pl - k * ps) * BASELINE / pl,
           "n": None, "off_d": None, "phase": None}
    if ts is None or tl is None:
        out["status"] = "no_epoch"
        return out
    d = tl - ts
    n = round(d / ps)
    off = d - n * ps
    out.update(n=n, off_d=off, phase=abs(off) / ps)
    out["status"] = "same_events" if out["phase"] <= PHASE_TOL else "offset"
    return out


def scan(rows):
    by_host = {}
    for row in rows:
        p = num(row, "pl_orbper")
        if p is None or p <= 0:
            continue
        by_host.setdefault(row["hostname"], []).append(row)
    flags = []
    for host, planets in sorted(by_host.items()):
        planets.sort(key=lambda x: (num(x, "pl_orbper"), x["pl_name"]))
        for i in range(len(planets)):
            for j in range(i + 1, len(planets)):
                a, b = planets[i], planets[j]
                res = classify(num(a, "pl_orbper"), num(a, "pl_tranmid"),
                               num(b, "pl_orbper"), num(b, "pl_tranmid"))
                if res is None:
                    continue
                flags.append({"hostname": host, "short": a["pl_name"], "long": b["pl_name"],
                              "p_short": num(a, "pl_orbper"), "p_long": num(b, "pl_orbper"),
                              "disc_short": a.get("disc_year", ""), "disc_long": b.get("disc_year", ""),
                              "rade_short": a.get("pl_rade", ""), "rade_long": b.get("pl_rade", ""),
                              **res})
    flags.sort(key=lambda f: (ORDER[f["status"]], f["rel"]))
    return flags


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--csv", help="local pscomppars CSV instead of a live TAP query")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    if args.csv:
        with open(args.csv, newline="", encoding="utf-8") as f:
            text = f.read()
    else:
        text = http_text(TAP + "?" + urllib.parse.urlencode({"query": QUERY, "format": "csv"}))
        with open(os.path.join(args.out_dir, "pscomppars.csv"), "w", encoding="utf-8", newline="") as f:
            f.write(text)
    rows = list(csv.DictReader(text.splitlines()))
    flags = scan(rows)
    with open(os.path.join(args.out_dir, "flags.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for fl in flags:
            w.writerow({k: fl.get(k) for k in FIELDS})
    counts = {}
    for fl in flags:
        counts[fl["status"]] = counts.get(fl["status"], 0) + 1
    summary = {"version": VERSION, "rows": len(rows), "hosts": len({r["hostname"] for r in rows}),
               "rel_tol": REL_TOL, "phase_tol": PHASE_TOL, "counts": counts,
               "same_events": [f"{f['short']} / {f['long']} (k={f['k']})" for f in flags
                               if f["status"] == "same_events"]}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
