"""koi_dupes: is any Kepler Object of Interest the same signal as another one on its star, listed again
at a period alias?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

alias_dupes (0.1.0) found one duplicate among confirmed planets: Kepler-289 e (330.07 d) is Kepler-289 d
(66.03 d) at five times its period. In the cumulative KOI table, Kepler-289 e is K01353.03 and d has no
KOI at all. DR25 federation (Thompson et al. 2018, sec. VI.2) only matches a new TCE to a known KOI at
the same period or at 2x / 1/2x, and only within DR25; the cumulative table merges KOIs from every
delivery. This tool checks the whole table.

Two modes, both per Kepler star (kepid):
  koi    every pair of KOIs on the star;
  cross  every KOI against each confirmed planet in pscomppars on the same host that has no KOI of its
         own (host = the kepler_name of any KOI on the star, minus its letter), like Kepler-289 d.
Pair test for short period Ps (mid-time Ts, duration Ds) and long period Pl (Tl, Dl), times in BJD:
1. k = round(Pl / Ps), 1 <= k <= K_MAX. drift_d = |Pl - k Ps| * BASELINE / Pl: how far the long
   signal's transits would slide against every k-th short transit over Q1-Q17. Pass if <= DRIFT_MAX.
2. n = round((Tl - Ts) / Ps), off_d = (Tl - Ts) - n Ps, window_d = (Ds + Dl) / 24.
     same_events  |off_d| <= window_d: the long signal's transits land on the short one's;
     offset       otherwise (a near-integer period ratio with different transits, e.g. a resonance
                  or an eclipsing binary's primary and secondary).
   window_d is twice the half-sum of the two durations so TTVs as large as Kepler-289 d's
   (off 0.28 d) still match. A missing duration in pscomppars is taken as equal to the KOI's.
3. Null: the same test with Tl moved by 0.25 and 0.75 of Ps. Those pairs cannot share events, so
   their same_events count is the chance rate for the real one (0.5 is also reported but not used,
   since it picks up eclipse secondaries).
A flag is a lead for a hand check against the papers, not a finding.

Usage: python koi_dupes.py --out-dir /out [--koi-csv cumulative.csv --ps-csv pscomppars.csv]
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
UA = f"koi-dupes/{VERSION} (Munim, Inc.; mv2@munimtech.com)"
BKJD = 2454833.0
BASELINE = 1460.0  # Kepler Q1-Q17, days
K_MAX = 30
DRIFT_MAX = 0.5  # days
NULL_SHIFTS = (0.25, 0.5, 0.75)
CHANCE_SHIFTS = (0.25, 0.75)
KOI_QUERY = ("select kepid,kepoi_name,kepler_name,koi_disposition,koi_pdisposition,koi_period,"
             "koi_time0bk,koi_duration,koi_depth,koi_prad,koi_fpflag_ec from cumulative")
PS_QUERY = ("select hostname,pl_name,pl_orbper,pl_tranmid,pl_trandur,pl_rade,disc_year,disc_facility "
            "from pscomppars where hostname like 'Kepler-%'")
FIELDS = ["mode", "kepid", "host", "short", "long", "disp_short", "disp_long", "p_short", "p_long",
          "k", "drift_d", "n", "off_d", "window_d", "status", "depth_short", "depth_long",
          "rade_short", "rade_long"]
ORDER = {"same_events": 0, "offset": 1}
NOT_FP = ("CANDIDATE", "CONFIRMED", "PS")


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


def host_of(kepler_name):
    """'Kepler-289 e' -> 'Kepler-289'; '' -> None."""
    name = (kepler_name or "").strip()
    if " " not in name:
        return None
    return name.rsplit(" ", 1)[0]


def classify(ps, ts, ds, pl, tl, dl, shift=0.0):
    """Pair test; periods and durations in days, times in BJD (or any common zero point).
    shift moves tl by shift * ps (for the null). Returns None if the periods are not an alias."""
    if not ps or not pl or ps <= 0 or pl < ps or ts is None or tl is None:
        return None
    k = round(pl / ps)
    if k < 1 or k > K_MAX:
        return None
    drift = abs(pl - k * ps) * BASELINE / pl
    if drift > DRIFT_MAX:
        return None
    d = (tl + shift * ps) - ts
    n = round(d / ps)
    off = d - n * ps
    window = ds + dl
    return {"k": k, "drift_d": drift, "n": n, "off_d": off, "window_d": window,
            "status": "same_events" if abs(off) <= window else "offset"}


def koi_entry(row):
    """KOI row -> (name, disposition, P, T0 in BJD, duration in days, depth, radius) or None."""
    p, t, dur = num(row, "koi_period"), num(row, "koi_time0bk"), num(row, "koi_duration")
    if p is None or p <= 0 or t is None or dur is None:
        return None
    return {"name": row["kepoi_name"], "disp": row.get("koi_disposition", ""), "p": p,
            "t": t + BKJD, "dur": dur / 24.0, "depth": row.get("koi_depth", ""),
            "rade": row.get("koi_prad", "")}


def ps_entry(row, dur_default):
    p, t = num(row, "pl_orbper"), num(row, "pl_tranmid")
    if p is None or p <= 0 or t is None:
        return None
    dur = num(row, "pl_trandur")
    return {"name": row["pl_name"], "disp": "PS", "p": p, "t": t,
            "dur": dur / 24.0 if dur else dur_default, "depth": "", "rade": row.get("pl_rade", "")}


def pair(mode, kepid, host, a, b, shift=0.0):
    s, l = (a, b) if (a["p"], a["name"]) <= (b["p"], b["name"]) else (b, a)
    res = classify(s["p"], s["t"], s["dur"], l["p"], l["t"], l["dur"], shift)
    if res is None:
        return None
    return {"mode": mode, "kepid": kepid, "host": host or "", "short": s["name"], "long": l["name"],
            "disp_short": s["disp"], "disp_long": l["disp"], "p_short": s["p"], "p_long": l["p"],
            "depth_short": s["depth"], "depth_long": l["depth"], "rade_short": s["rade"],
            "rade_long": l["rade"], **res}


def scan(koi_rows, ps_rows, shift=0.0):
    by_star, hosts = {}, {}
    for row in koi_rows:
        kid = (row.get("kepid") or "").strip()
        h = host_of(row.get("kepler_name"))
        if h:
            hosts[kid] = h
        e = koi_entry(row)
        if e is not None:
            e["kepler_name"] = (row.get("kepler_name") or "").strip()
            by_star.setdefault(kid, []).append(e)
    ps_by_host = {}
    for row in ps_rows:
        ps_by_host.setdefault(row["hostname"], []).append(row)
    flags = []
    for kid in sorted(by_star, key=lambda x: (len(x), x)):
        kois = sorted(by_star[kid], key=lambda e: e["name"])
        for i in range(len(kois)):
            for j in range(i + 1, len(kois)):
                f = pair("koi", kid, hosts.get(kid), kois[i], kois[j], shift)
                if f:
                    flags.append(f)
        h = hosts.get(kid)
        named = {e["kepler_name"] for e in kois}
        for row in ps_by_host.get(h, []) if h else []:
            if row["pl_name"] in named:
                continue
            for e in kois:
                q = ps_entry(row, e["dur"])
                if q is None:
                    continue
                f = pair("cross", kid, h, e, q, shift)
                if f:
                    flags.append(f)
    flags.sort(key=lambda f: (f["mode"], ORDER[f["status"]], abs(f["off_d"])))
    return flags


def tally(flags):
    out = {}
    for mode in ("koi", "cross"):
        same = [f for f in flags if f["mode"] == mode and f["status"] == "same_events"]
        out[mode] = {"same_events": len(same),
                     "offset": sum(1 for f in flags if f["mode"] == mode and f["status"] == "offset"),
                     "same_both_not_fp": sum(1 for f in same if f["disp_short"] in NOT_FP
                                             and f["disp_long"] in NOT_FP),
                     "same_any_fp": sum(1 for f in same if "FALSE POSITIVE" in (f["disp_short"],
                                                                                f["disp_long"]))}
    return out


def read_or_fetch(path, query, out_path):
    if path:
        with open(path, newline="", encoding="utf-8") as f:
            return f.read()
    text = http_text(TAP + "?" + urllib.parse.urlencode({"query": query, "format": "csv"}))
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return text


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--koi-csv", help="local cumulative CSV instead of a live TAP query")
    ap.add_argument("--ps-csv", help="local pscomppars CSV instead of a live TAP query")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    koi_rows = list(csv.DictReader(read_or_fetch(args.koi_csv, KOI_QUERY,
                                                 os.path.join(args.out_dir, "cumulative.csv")).splitlines()))
    ps_rows = list(csv.DictReader(read_or_fetch(args.ps_csv, PS_QUERY,
                                                os.path.join(args.out_dir, "pscomppars.csv")).splitlines()))
    flags = scan(koi_rows, ps_rows)
    with open(os.path.join(args.out_dir, "flags.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for fl in flags:
            w.writerow({k: fl.get(k) for k in FIELDS})
    null = {str(s): tally(scan(koi_rows, ps_rows, s)) for s in NULL_SHIFTS}
    chance = {mode: sum(null[str(s)][mode]["same_events"] for s in CHANCE_SHIFTS) / len(CHANCE_SHIFTS)
              for mode in ("koi", "cross")}
    summary = {"version": VERSION, "koi_rows": len(koi_rows), "ps_rows": len(ps_rows),
               "stars": len({r.get("kepid") for r in koi_rows}), "k_max": K_MAX,
               "drift_max_d": DRIFT_MAX, "counts": tally(flags), "null": null,
               "chance_same_events": chance,
               "same_events": [f"{f['mode']}: {f['short']} ({f['disp_short']}) / {f['long']} "
                               f"({f['disp_long']}) k={f['k']} off={f['off_d']:.4f} d"
                               for f in flags if f["status"] == "same_events"]}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
