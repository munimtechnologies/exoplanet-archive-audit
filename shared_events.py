"""shared_events: do the "unrelated" Kepler orphans share a transit with a DR25 TCE at a period that is
not a simple ratio of theirs?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

koi_orphans 0.1.0 called an orphan CANDIDATE "unrelated" when no DR25 TCE on its star has a period within
a/b (a, b <= 12) of the orphan's with less than 0.5 d drift over Q1-Q17. That misses KOI-1356.01: the
Q1-Q16 row says 384.026 d and the DR25 TCE says 393.719 d, both from the same first transit at 335.82
BKJD. A TCE that keeps one real transit and pairs it with other events at a wrong period fails the
ratio test by design. This tool tests the events themselves.

Per orphan-TCE pair, times in BKJD, periods in days, durations in hours:
1. Events: every T0 + n P inside the Q1-Q17 span [T_START, T_END] (data gaps are not removed).
2. Window w = (Do + Dt) / 24, as in koi_orphans. k = number of (orphan event, TCE event) pairs with
   |to - tt| <= w (sorted-list search, so 1-day periods stay fast).
3. Chance: lam = n_o n_t 2 w / (T_END - T_START), the expected number of such pairs for unrelated
   random phases; p_chance = P(Poisson(lam) >= k).
Per orphan the TCE with k >= 1 and the smallest p_chance decides: shared_event if p_chance <= P_MAX,
chance_overlap if k >= 1 but p_chance > P_MAX, disjoint if no TCE on the star shares an event.

Null: each orphan's TCE set is swapped for another unrelated orphan star's (random derangements, fixed
seed). Joins: DR25 Robovetter output (score, disposition, NT/SS/CO/EC flags, minor flags), the federated
KOI of each TCE, and Lissauer et al. 2024 status from lissauer_xmatch 0.1.0.
A flag is a lead for a hand check against the light curve, not a new period.

    python shared_events.py --out-dir out                       # live: GitHub raw, Archive TAP, NASA GitHub
    python shared_events.py --out-dir out --orphans o.csv --koi-csv k.csv --tce-csv t.csv --robovetter r.txt --xmatch x.csv
"""
import argparse
import bisect
import csv
import io
import json
import math
import os
import random
import sys
import time
import urllib.parse
import urllib.request

VERSION = "0.1.0"
RAW = "https://raw.githubusercontent.com/munimtechnologies/exoplanet-archive-audit/main/"
ORPHANS_URL = RAW + "results/2026-10-17-koi-orphans-0.1.0/orphans.csv"
XMATCH_URL = RAW + "results/2026-10-17-lissauer-xmatch-0.1.0/xmatch.csv"
ROBOVETTER_URL = "https://raw.githubusercontent.com/nasa/kepler-robovetter/master/kplr_dr25_obs_robovetter_output.txt"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
KOI_QUERY = ("select kepid,kepoi_name,koi_disposition,koi_tce_delivname,koi_tce_plnt_num,koi_period,"
             "koi_time0bk,koi_duration from cumulative")
TCE_QUERY = ("select kepid,tce_plnt_num,tce_period,tce_time0bk,tce_duration,tce_depth,tce_model_snr,"
             "tce_rogue_flag from q1_q17_dr25_tce")
UA = f"shared_events/{VERSION} (MV2 of Munim, Inc.; mv2@munimtech.com)"
DR25_TCE = "q1_q17_dr25_tce"
T_START = 131.5  # Q1 start, BKJD
T_END = 1591.0  # Q17 end, BKJD
P_MAX = 0.05
MAX_LIST = 20  # event lists in the output keep their first 20 entries
N_SHUFFLES = 100
SEED = 20261017
STATUSES = ["shared_event", "chance_overlap", "disjoint", "no_params", "no_tce"]
ROW_FIELDS = ["kepoi_name", "kepid", "status", "p_orphan", "t_orphan", "dur_orphan", "n_o", "n_tce",
              "tce_plnt_num", "p_tce", "t_tce", "dur_tce", "n_t", "window_d", "k", "lam", "p_chance",
              "shared_at", "orphan_events", "tce_events", "tce_rogue", "tce_depth", "tce_snr", "tce_koi",
              "tce_koi_disp", "rv_score", "rv_disp", "rv_nt", "rv_ss", "rv_co", "rv_ec", "rv_flags",
              "lissauer_status", "lissauer_period"]


def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=600) as r:
                return r.read().decode("utf-8")
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(10 * (i + 1))


def read_csv(text):
    return list(csv.DictReader(io.StringIO(text.replace("\r\n", "\n"))))


def num(row, key):
    v = (row.get(key) or "").strip()
    try:
        x = float(v)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def plnt(v):
    """'1', '1.0' -> '1'; '' -> ''."""
    v = (v or "").strip()
    return str(int(float(v))) if v else ""


def events(p, t0, lo=T_START, hi=T_END):
    """Every t0 + n p in [lo, hi]."""
    if not p or p <= 0 or t0 is None:
        return []
    n0, n1 = math.ceil((lo - t0) / p), math.floor((hi - t0) / p)
    return [t0 + n * p for n in range(n0, n1 + 1)]


def poisson_sf(k, lam):
    """P(X >= k) for X ~ Poisson(lam)."""
    if k <= 0:
        return 1.0
    if lam <= 0:
        return 0.0
    cdf = math.fsum(math.exp(-lam + i * math.log(lam) - math.lgamma(i + 1)) for i in range(k))
    return max(0.0, 1.0 - cdf)


def pair(po, to, do_h, pt, tt, dt_h, lo=T_START, hi=T_END):
    """Event test for one orphan-TCE pair; None if a period, mid-time or duration is missing."""
    if None in (po, to, do_h, pt, tt, dt_h):
        return None
    eo, et = events(po, to, lo, hi), events(pt, tt, lo, hi)
    w = (do_h + dt_h) / 24.0
    hits = []
    for a in eo:
        hits += [a] * (bisect.bisect_right(et, a + w) - bisect.bisect_left(et, a - w))
    lam = len(eo) * len(et) * 2 * w / (hi - lo)
    return {"n_o": len(eo), "n_t": len(et), "window_d": w, "k": len(hits), "lam": lam,
            "p_chance": poisson_sf(len(hits), lam), "shared_at": [round(a, 4) for a in hits[:MAX_LIST]],
            "orphan_events": [round(a, 4) for a in eo[:MAX_LIST]],
            "tce_events": [round(b, 4) for b in et[:MAX_LIST]]}


def classify(results, p_max=P_MAX):
    """results: list of (tce, pair-result). Returns (status, best tce, best result)."""
    hit = [(t, r) for t, r in results if r and r["k"] >= 1]
    if not hit:
        return "disjoint", None, None
    t, r = min(hit, key=lambda x: (x[1]["p_chance"], -x[1]["k"]))
    return ("shared_event" if r["p_chance"] <= p_max else "chance_overlap"), t, r


def parse_robovetter(text):
    """TCE id 'KKKKKKKKK-NN' -> dict of score, disposition, NT/SS/CO/EC and minor flags."""
    out = {}
    for line in text.splitlines():
        f = line.split()
        if len(f) < 7 or line.startswith("#") or "-" not in f[0]:
            continue
        out[f[0]] = {"rv_score": f[1], "rv_disp": f[2], "rv_nt": f[3], "rv_ss": f[4], "rv_co": f[5],
                     "rv_ec": f[6], "rv_flags": f[7] if len(f) > 7 else ""}
    return out


def tce_id(kepid, n):
    return f"{int(kepid):09d}-{int(n):02d}"


def federation(koi_rows):
    """(kepid, tce_plnt_num) -> cumulative row, for KOIs federated to a DR25 TCE."""
    fed = {}
    for r in koi_rows:
        if (r.get("koi_tce_delivname") or "").strip() == DR25_TCE:
            n = plnt(r.get("koi_tce_plnt_num"))
            if n:
                fed[((r.get("kepid") or "").strip(), n)] = r
    return fed


def tces_by_star(tce_rows, fed):
    out = {}
    for r in tce_rows:
        kid, n = (r.get("kepid") or "").strip(), plnt(r.get("tce_plnt_num"))
        koi = fed.get((kid, n), {})
        out.setdefault(kid, []).append({
            "kepid": kid, "n": n, "p": num(r, "tce_period"), "t": num(r, "tce_time0bk"),
            "dur": num(r, "tce_duration"), "depth": num(r, "tce_depth"), "snr": num(r, "tce_model_snr"),
            "rogue": (r.get("tce_rogue_flag") or "").strip(), "koi": koi.get("kepoi_name", ""),
            "koi_disp": koi.get("koi_disposition", "")})
    return out


def scan(orphans, tces, star_map=None, p_max=P_MAX):
    """orphans: dicts with kepoi_name, kepid, p, t, dur. star_map sends an orphan's kepid to the kepid
    whose TCEs it is tested against (the null); default is its own star."""
    rows = []
    for o in orphans:
        src = star_map.get(o["kepid"], o["kepid"]) if star_map else o["kepid"]
        ts = tces.get(src, [])
        row = {"kepoi_name": o["kepoi_name"], "kepid": o["kepid"], "p_orphan": o["p"], "t_orphan": o["t"],
               "dur_orphan": o["dur"], "n_tce": len(ts)}
        if not ts:
            row["status"] = "no_tce"
        elif None in (o["p"], o["t"], o["dur"]):
            row["status"] = "no_params"
        else:
            res = [(t, pair(o["p"], o["t"], o["dur"], t["p"], t["t"], t["dur"])) for t in ts]
            row["status"], t, r = classify(res, p_max)
            if t:
                row.update({"tce_plnt_num": t["n"], "p_tce": t["p"], "t_tce": t["t"], "dur_tce": t["dur"],
                            "tce_rogue": t["rogue"], "tce_depth": t["depth"], "tce_snr": t["snr"],
                            "tce_koi": t["koi"], "tce_koi_disp": t["koi_disp"], **r})
        rows.append(row)
    return rows


def tally(rows):
    out = {s: 0 for s in STATUSES}
    for r in rows:
        out[r["status"]] += 1
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
    stars = sorted({o["kepid"] for o in orphans if tces.get(o["kepid"])})
    rng = random.Random(seed)
    runs = [tally(scan(orphans, tces, derangement(stars, rng))) for _ in range(n)] if len(stars) > 1 else []
    return ({k: sum(r[k] for r in runs) / len(runs) for k in runs[0]} if runs else {}), runs


def unrelated_orphans(orphan_rows, koi_rows):
    """Census rows with status 'unrelated', with period, mid-time and duration from the cumulative table."""
    by_name = {r["kepoi_name"]: r for r in koi_rows}
    out, missing = [], []
    for r in orphan_rows:
        if r.get("status") != "unrelated":
            continue
        k = by_name.get(r["kepoi_name"])
        if k is None:
            missing.append(r["kepoi_name"])
            continue
        out.append({"kepoi_name": r["kepoi_name"], "kepid": (r.get("kepid") or "").strip(),
                    "p": num(k, "koi_period"), "t": num(k, "koi_time0bk"), "dur": num(k, "koi_duration")})
    return out, missing


def annotate(rows, robo, xmatch):
    lis = {r["kepoi_name"]: r for r in xmatch}
    for r in rows:
        if r.get("tce_plnt_num"):
            r.update(robo.get(tce_id(r["kepid"], r["tce_plnt_num"]), {"rv_disp": "absent"}))
        x = lis.get(r["kepoi_name"], {})
        r["lissauer_status"] = x.get("lissauer_status", "")
        r["lissauer_period"] = x.get("lissauer_period", "")
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--orphans")
    ap.add_argument("--koi-csv")
    ap.add_argument("--tce-csv")
    ap.add_argument("--robovetter")
    ap.add_argument("--xmatch")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)

    def load(path, url, save):
        if path:
            with open(path, encoding="utf-8") as f:
                return f.read()
        text = fetch(url)
        with open(os.path.join(args.out_dir, save), "w", encoding="utf-8", newline="") as f:
            f.write(text)
        return text

    def tap(q):
        return TAP + "?" + urllib.parse.urlencode({"query": q, "format": "csv"})

    orphan_rows = read_csv(load(args.orphans, ORPHANS_URL, "orphans_in.csv"))
    koi_rows = read_csv(load(args.koi_csv, tap(KOI_QUERY), "cumulative.csv"))
    tce_rows = read_csv(load(args.tce_csv, tap(TCE_QUERY), "dr25_tce.csv"))
    robo = parse_robovetter(load(args.robovetter, ROBOVETTER_URL, "robovetter.txt"))
    xmatch = read_csv(load(args.xmatch, XMATCH_URL, "xmatch.csv"))

    tces = tces_by_star(tce_rows, federation(koi_rows))
    orphans, missing = unrelated_orphans(orphan_rows, koi_rows)
    rows = annotate(scan(orphans, tces), robo, xmatch)
    rows.sort(key=lambda r: (STATUSES.index(r["status"]), r.get("p_chance", 2.0), r["kepoi_name"]))
    null_mean, _ = null_tallies(orphans, tces)
    shared = [r for r in rows if r["status"] == "shared_event"]
    rv = {}
    for r in shared:
        key = "rogue" if r.get("tce_rogue") == "1" else ("federated" if r.get("tce_koi") else r.get("rv_disp", ""))
        rv[key] = rv.get(key, 0) + 1
    summary = {
        "version": VERSION, "span_bkjd": [T_START, T_END], "p_max": P_MAX,
        "orphan_rows": len(orphan_rows), "unrelated": len(orphans), "missing_from_cumulative": missing,
        "koi_rows": len(koi_rows), "tce_rows": len(tce_rows), "robovetter_rows": len(robo),
        "counts": tally(rows), "null_mean": null_mean, "null_shuffles": N_SHUFFLES, "seed": SEED,
        "shared_tce_kind": rv,
        "shared_event": [
            f"{r['kepoi_name']} P={r['p_orphan']} ~ TCE {r['tce_plnt_num']} P={r['p_tce']} k={r['k']} "
            f"at {r['shared_at']} p={r['p_chance']:.4g} RV {r.get('rv_disp', '')} {r.get('rv_score', '')} "
            f"{r.get('rv_flags', '')} rogue={r.get('tce_rogue', '')} KOI={r.get('tce_koi') or '-'} "
            f"Lissauer {r['lissauer_status'] or '-'} {r['lissauer_period'] or ''}" for r in shared],
        "sources": {"orphans": args.orphans or ORPHANS_URL, "xmatch": args.xmatch or XMATCH_URL,
                    "robovetter": args.robovetter or ROBOVETTER_URL, "koi": args.koi_csv or tap(KOI_QUERY),
                    "tce": args.tce_csv or tap(TCE_QUERY),
                    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
    }
    with open(os.path.join(args.out_dir, "shared_events.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ROW_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    json.dump(summary, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
