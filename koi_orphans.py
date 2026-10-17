"""koi_orphans: do the Kepler candidates that DR25 never re-delivered ("orphans") match anything the
final pipeline run did detect on the same star?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

The cumulative KOI table keeps KOIs from earlier deliveries that DR25 did not deliver, with parameters
from the Q1-Q16 or DR24 table (koi_parm_prov) and a disposition inherited by the DR25 supplemental table.
Thompson et al. 2018 (arXiv:1710.06758, sec. VI.1) say such KOIs, with no DR25 observed TCE federated to
them, were simply left out of the DR25 table; they were not checked for period aliases. koi_dupes 0.1.0
found three CANDIDATE orphans that repeat a confirmed sibling's transits (K01101.02, K02167.02,
K01922.02). This tool checks every orphan against every DR25 TCE on its star.

Pair test, orphan period Po (mid-time To, duration Do) against TCE period Pt (Tt, Dt), times in BKJD:
1. Ratio: the fraction a/b (lowest terms, 1 <= a, b <= N_MAX) with Po / Pt nearest a / b. Every b-th
   orphan event and every a-th TCE event can coincide, once per L = b Po. drift_d = |b Po - a Pt| *
   BASELINE / L is how far they slide apart over Q1-Q17. Commensurate if drift_d <= DRIFT_MAX.
2. Phase: g = Po / a (= Pt / b, the spacing of possible offsets). off_d = (To - Tt) folded into
   [-g/2, g/2); window_d = (Do + Dt) / 24 as in koi_dupes. same_events if |off_d| <= window_d, else offset.
   p_phase = min(1, 2 window_d / g) is the chance that a random epoch passes.
   kind: same (a = b = 1), integer (a or b is 1), rational (otherwise).
Per orphan, the best pair decides its status: same_events beats offset, then kind same > integer >
rational, then smaller |off_d|. Orphans with TCEs on the star but no commensurate one are unrelated
(no_params if the orphan lacks a period, mid-time or duration), and orphans on a star without DR25
TCEs are no_tce.

Null: each orphan star's TCE set is swapped for another orphan star's (random derangements, fixed seed),
so the period and duration mix is kept and only the star link is broken.
Control: KOIs whose parameters come from DR25 tested against their own federated TCE should come out
same_events.
A flag is a lead for a hand check against the catalogue history and pixels, not a finding.

Usage: python koi_orphans.py --out-dir /out [--koi-csv cumulative.csv --tce-csv dr25_tce.csv]
"""
import argparse
import csv
import json
import math
import os
import random
import urllib.parse
import urllib.request

VERSION = "0.1.0"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
UA = f"koi-orphans/{VERSION} (Munim, Inc.; mv2@munimtech.com)"
BASELINE = 1460.0  # Kepler Q1-Q17, days
DRIFT_MAX = 0.5  # days
N_MAX = 12
N_SHUFFLES = 100
SEED = 20261017
DR25_PROV = "q1_q17_dr25_koi"
DR25_TCE = "q1_q17_dr25_tce"
KOI_QUERY = ("select kepid,kepoi_name,kepler_name,koi_disposition,koi_parm_prov,koi_tce_delivname,"
             "koi_tce_plnt_num,koi_period,koi_time0bk,koi_duration,koi_depth,koi_model_snr from cumulative")
TCE_QUERY = ("select kepid,tce_plnt_num,tce_period,tce_time0bk,tce_duration,tce_depth,tce_model_snr,"
             "tce_rogue_flag from q1_q17_dr25_tce")
KIND_ORDER = {"same": 0, "integer": 1, "rational": 2}
STATUS_ORDER = ["same_events", "offset", "unrelated", "no_params", "no_tce"]
PAIR_FIELDS = ["kepoi_name", "kepid", "disp", "prov", "p_orphan", "tce_plnt_num", "tce_koi", "tce_koi_disp",
               "p_tce", "a", "b", "kind", "drift_d", "off_d", "window_d", "p_phase", "status",
               "depth_orphan", "tce_depth", "tce_snr", "tce_rogue"]
ORPHAN_FIELDS = ["kepoi_name", "kepid", "kepler_name", "disp", "prov", "p_orphan", "depth_orphan",
                 "snr_orphan", "n_tce", "status", "kind", "a", "b", "tce_plnt_num", "tce_koi", "tce_koi_disp",
                 "p_tce", "off_d", "window_d", "p_phase"]


def http_text(url, timeout=900):
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


def fractions(n_max=N_MAX):
    """Every a/b in lowest terms with 1 <= a, b <= n_max."""
    return [(a, b) for a in range(1, n_max + 1) for b in range(1, n_max + 1) if math.gcd(a, b) == 1]


FRACTIONS = fractions()


def ratio_match(po, pt):
    """(a, b, drift_d) for the a/b with the smallest drift, or None if none is within DRIFT_MAX."""
    if not po or not pt or po <= 0 or pt <= 0:
        return None
    best = None
    for a, b in FRACTIONS:
        drift = abs(b * po - a * pt) * BASELINE / (b * po)
        if best is None or drift < best[2]:
            best = (a, b, drift)
    return best if best[2] <= DRIFT_MAX else None


def fold(x, g):
    """x folded into [-g/2, g/2)."""
    return (x + g / 2.0) % g - g / 2.0


def kind_of(a, b):
    if a == 1 and b == 1:
        return "same"
    return "integer" if a == 1 or b == 1 else "rational"


def pair_test(po, to, do_h, pt, tt, dt_h):
    """Pair test; periods and mid-times in days, durations in hours. None if not commensurate."""
    if to is None or tt is None or do_h is None or dt_h is None:
        return None
    m = ratio_match(po, pt)
    if m is None:
        return None
    a, b, drift = m
    g = po / a
    off = fold(to - tt, g)
    window = (do_h + dt_h) / 24.0
    return {"a": a, "b": b, "kind": kind_of(a, b), "drift_d": drift, "off_d": off, "window_d": window,
            "p_phase": min(1.0, 2 * window / g), "status": "same_events" if abs(off) <= window else "offset"}


def rank(p):
    return (STATUS_ORDER.index(p["status"]), KIND_ORDER[p["kind"]], abs(p["off_d"]))


def koi_entry(row):
    return {"kepoi_name": row["kepoi_name"], "kepid": (row.get("kepid") or "").strip(),
            "kepler_name": (row.get("kepler_name") or "").strip(), "disp": row.get("koi_disposition", ""),
            "prov": row.get("koi_parm_prov", ""), "p": num(row, "koi_period"), "t": num(row, "koi_time0bk"),
            "dur": num(row, "koi_duration"), "depth": num(row, "koi_depth"), "snr": num(row, "koi_model_snr")}


def plnt(v):
    """'1', '1.0' -> '1'; '' -> ''."""
    v = (v or "").strip()
    return str(int(float(v))) if v else ""


def tce_entry(row, fed):
    kid, n = (row.get("kepid") or "").strip(), plnt(row.get("tce_plnt_num"))
    koi = fed.get((kid, n), {})
    return {"kepid": kid, "n": n, "p": num(row, "tce_period"), "t": num(row, "tce_time0bk"),
            "dur": num(row, "tce_duration"), "depth": num(row, "tce_depth"), "snr": num(row, "tce_model_snr"),
            "rogue": (row.get("tce_rogue_flag") or "").strip(), "koi": koi.get("kepoi_name", ""),
            "koi_disp": koi.get("koi_disposition", "")}


def federation(koi_rows):
    """(kepid, tce_plnt_num) -> cumulative row, for KOIs federated to a DR25 TCE."""
    fed = {}
    for r in koi_rows:
        if (r.get("koi_tce_delivname") or "").strip() == DR25_TCE:
            n = plnt(r.get("koi_tce_plnt_num"))
            if n:
                fed[((r.get("kepid") or "").strip(), n)] = r
    return fed


def orphans_of(koi_rows, dispositions):
    return [koi_entry(r) for r in koi_rows
            if r.get("koi_parm_prov", "") not in ("", DR25_PROV) and r.get("koi_disposition", "") in dispositions]


def tces_by_star(tce_rows, fed):
    out = {}
    for r in tce_rows:
        e = tce_entry(r, fed)
        out.setdefault(e["kepid"], []).append(e)
    return out


def scan(orphans, tces, star_map=None):
    """Returns (pairs, per_orphan). star_map sends an orphan's kepid to the kepid whose TCEs it is
    tested against (the null); default is its own star."""
    pairs, per = [], []
    for o in orphans:
        src = star_map.get(o["kepid"], o["kepid"]) if star_map else o["kepid"]
        ts = tces.get(src, [])
        mine = []
        for t in ts:
            res = pair_test(o["p"], o["t"], o["dur"], t["p"], t["t"], t["dur"])
            if res is None:
                continue
            mine.append({"kepoi_name": o["kepoi_name"], "kepid": o["kepid"], "disp": o["disp"], "prov": o["prov"],
                         "p_orphan": o["p"], "tce_plnt_num": t["n"], "tce_koi": t["koi"],
                         "tce_koi_disp": t["koi_disp"], "p_tce": t["p"], "depth_orphan": o["depth"],
                         "tce_depth": t["depth"], "tce_snr": t["snr"], "tce_rogue": t["rogue"], **res})
        mine.sort(key=rank)
        pairs += mine
        row = {"kepoi_name": o["kepoi_name"], "kepid": o["kepid"], "kepler_name": o["kepler_name"],
               "disp": o["disp"], "prov": o["prov"], "p_orphan": o["p"], "depth_orphan": o["depth"],
               "snr_orphan": o["snr"], "n_tce": len(ts)}
        if mine:
            best = mine[0]
            row.update({k: best[k] for k in ("status", "kind", "a", "b", "tce_plnt_num", "tce_koi", "tce_koi_disp",
                                             "p_tce", "off_d", "window_d", "p_phase")})
        elif not ts:
            row["status"] = "no_tce"
        else:
            row["status"] = "unrelated" if None not in (o["p"], o["t"], o["dur"]) else "no_params"
        per.append(row)
    return pairs, per


def tally(per):
    out = {s: 0 for s in STATUS_ORDER}
    for k in KIND_ORDER:
        out[f"same_events_{k}"] = 0
    for r in per:
        out[r["status"]] += 1
        if r["status"] == "same_events":
            out[f"same_events_{r['kind']}"] += 1
    return out


def derangement(keys, rng):
    """A random permutation of keys with no fixed point, as a dict."""
    keys = sorted(keys)
    if len(keys) < 2:
        return {}
    while True:
        perm = keys[:]
        rng.shuffle(perm)
        if all(k != p for k, p in zip(keys, perm)):
            return dict(zip(keys, perm))


def null_tallies(orphans, tces, n=N_SHUFFLES, seed=SEED):
    stars = {o["kepid"] for o in orphans if tces.get(o["kepid"])}
    if len(stars) < 2:
        return {}, []
    rng = random.Random(seed)
    runs = []
    for _ in range(n):
        star_map = derangement(stars, rng)
        live = [o for o in orphans if o["kepid"] in stars]
        runs.append(tally(scan(live, tces, star_map)[1]))
    keys = runs[0].keys() if runs else []
    return {k: sum(r[k] for r in runs) / len(runs) for k in keys}, runs


def control(koi_rows, tces, dispositions):
    """DR25-parameter KOIs against their own federated TCE."""
    counts = {"tested": 0, "no_tce_row": 0, "same_events_same": 0, "same_events_other": 0, "offset": 0,
              "not_commensurate": 0}
    misses = []
    for r in koi_rows:
        if r.get("koi_parm_prov") != DR25_PROV or r.get("koi_disposition", "") not in dispositions:
            continue
        o = koi_entry(r)
        n = plnt(r.get("koi_tce_plnt_num"))
        t = next((t for t in tces.get(o["kepid"], []) if n and t["n"] == n), None)
        counts["tested"] += 1
        if t is None:
            counts["no_tce_row"] += 1
            continue
        res = pair_test(o["p"], o["t"], o["dur"], t["p"], t["t"], t["dur"])
        if res is None:
            counts["not_commensurate"] += 1
            key = "not_commensurate"
        elif res["status"] == "same_events":
            key = "same_events_same" if res["kind"] == "same" else "same_events_other"
            counts[key] += 1
        else:
            key = "offset"
            counts[key] += 1
        if key != "same_events_same":
            misses.append(f"{o['kepoi_name']} P={o['p']} TCE {n} P={t['p']}: {key}"
                          + (f" {res['a']}/{res['b']} off={res['off_d']:.4f}" if res else ""))
    return counts, misses


def read_or_fetch(path, query, out_path):
    if path:
        with open(path, newline="", encoding="utf-8") as f:
            return f.read()
    text = http_text(TAP + "?" + urllib.parse.urlencode({"query": query, "format": "csv"}))
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return text


def write_csv(path, fields, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--koi-csv", help="local cumulative CSV instead of a live TAP query")
    ap.add_argument("--tce-csv", help="local DR25 TCE CSV instead of a live TAP query")
    ap.add_argument("--dispositions", default="CANDIDATE", help="comma-separated koi_disposition values")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    disps = tuple(d.strip() for d in args.dispositions.split(",") if d.strip())
    koi_rows = list(csv.DictReader(read_or_fetch(args.koi_csv, KOI_QUERY,
                                                 os.path.join(args.out_dir, "cumulative.csv")).splitlines()))
    tce_rows = list(csv.DictReader(read_or_fetch(args.tce_csv, TCE_QUERY,
                                                 os.path.join(args.out_dir, "dr25_tce.csv")).splitlines()))
    fed = federation(koi_rows)
    tces = tces_by_star(tce_rows, fed)
    orphans = orphans_of(koi_rows, disps)
    pairs, per = scan(orphans, tces)
    per.sort(key=lambda r: (STATUS_ORDER.index(r["status"]), KIND_ORDER.get(r.get("kind"), 9), r["kepoi_name"]))
    write_csv(os.path.join(args.out_dir, "pairs.csv"), PAIR_FIELDS, pairs)
    write_csv(os.path.join(args.out_dir, "orphans.csv"), ORPHAN_FIELDS, per)
    null_mean, _ = null_tallies(orphans, tces)
    ctl, misses = control(koi_rows, tces, disps)
    prov = {}
    for o in orphans:
        prov[o["prov"]] = prov.get(o["prov"], 0) + 1
    same = [r for r in per if r["status"] == "same_events"]
    summary = {"version": VERSION, "dispositions": list(disps), "koi_rows": len(koi_rows),
               "tce_rows": len(tce_rows), "federated_tces": len(fed), "orphans": len(orphans),
               "orphans_by_prov": prov, "orphans_with_tce": sum(1 for o in orphans if tces.get(o["kepid"])),
               "orphan_tce_pairs": sum(len(tces.get(o["kepid"], [])) for o in orphans),
               "commensurate_pairs": len(pairs), "n_max": N_MAX, "drift_max_d": DRIFT_MAX,
               "counts": tally(per), "null_mean": null_mean, "null_shuffles": N_SHUFFLES, "seed": SEED,
               "expected_same_events_by_chance": round(sum(p["p_phase"] for p in pairs), 3),
               "control": ctl, "control_misses": misses[:60],
               "same_events": [f"{r['kepoi_name']} ({r['prov']}) P={r['p_orphan']} ~ {r['a']}/{r['b']} x TCE "
                               f"{r['tce_plnt_num']} P={r['p_tce']} ({r['tce_koi'] or 'no KOI'} "
                               f"{r['tce_koi_disp']}) off={r['off_d']:.4f} d p_phase={r['p_phase']:.3f}"
                               for r in same]}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
