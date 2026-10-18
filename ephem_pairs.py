"""ephem_pairs: which Kepler KOIs on different stars share a transit train, far beyond any known way
one star can contaminate another?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

DR25 ephemeris matching (Thompson et al. 2018, App. A.6) only counts a match when a contamination
geometry allows it: direct PRF / field-flattener (separation <= 55 sqrt(1e6 10^(-0.4 m) + 1) arcsec,
m of the brighter star), antipodal reflection (opposite sides of the field centre, equidistant within
100"), or column anomaly / video crosstalk (same CCD module). The Skye metric only counts coincident
events inside one skygroup. A pair of stars degrees apart on different modules is seen by neither.
By hand (findings/2026-10-18-cross-star-ephemeris-pairs.md) three such pairs of long-period
CANDIDATEs share every event to within 0.36 d. This tool runs the same test on every KOI.

Per pair of KOIs on different stars, times in BKJD, periods in days:
1. Events: every T0 + n P inside the Q1-Q17 span [T_START, T_END]; both need >= 2 events.
2. Offset: for each event of one, the distance to the nearest predicted event of the other (from its
   ephemeris, not limited to the span); max_offset = the largest over both directions. A match is
   max_offset <= W (1:1 period ratio only).
3. Geometry: near (separation <= d_max), antipodal (B within 100" of A mirrored through the field
   centre, gnomonic), module (separation <= MODULE_DEG, the same module is possible), else far.
Null: every KOI's epoch is redrawn uniformly within its period (fixed seed); the far-match count with
at least one CANDIDATE is recounted. A far match is a lead (shared systematic or an unknown path), not
a disposition.

    python ephem_pairs.py --out-dir out                    # live: Archive TAP, GitHub raw
    python ephem_pairs.py --out-dir out --koi-csv k.csv --xmatch x.csv
"""
import argparse
import csv
import io
import json
import math
import os
import random
import statistics
import sys
import time
import urllib.parse
import urllib.request

VERSION = "0.1.0"
RAW = "https://raw.githubusercontent.com/munimtechnologies/exoplanet-archive-audit/main/"
XMATCH_URL = RAW + "results/2026-10-17-lissauer-xmatch-0.1.0/xmatch.csv"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
KOI_QUERY = ("select kepid,kepoi_name,koi_disposition,koi_pdisposition,koi_period,koi_time0bk,koi_duration,"
             "koi_depth,koi_model_snr,koi_kepmag,ra,dec,koi_fpflag_ec,koi_tce_delivname from cumulative")
UA = f"ephem_pairs/{VERSION} (MV2 of Munim, Inc.; mv2@munimtech.com)"
T_START = 131.5  # Q1 start, BKJD
T_END = 1591.0  # Q17 end, BKJD
P_MIN = 50.0
W = 0.5  # days
FOV_RA, FOV_DEC = 290.6667, 44.5  # Kepler field centre, degrees
ANTI_ARCSEC = 100.0
MODULE_DEG = 3.4  # a Kepler module is about 2.4 x 2.3 deg; farther apart cannot share one
N_SHUFFLES = 1000
SEED = 20261018
GEOMS = ["near", "antipodal", "module", "far"]
ROW_FIELDS = ["geom", "kepoi_a", "kepid_a", "disp_a", "p_a", "t_a", "dur_a", "depth_a", "snr_a", "kepmag_a",
              "ec_a", "lissauer_a", "kepoi_b", "kepid_b", "disp_b", "p_b", "t_b", "dur_b", "depth_b", "snr_b",
              "kepmag_b", "ec_b", "lissauer_b", "max_offset", "n_a", "n_b", "sep_deg", "d_max_arcsec",
              "anti_arcsec", "events_a"]


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


def events(p, t0, lo=T_START, hi=T_END):
    """Every t0 + n p in [lo, hi]."""
    if not p or p <= 0 or t0 is None:
        return []
    n0, n1 = math.ceil((lo - t0) / p), math.floor((hi - t0) / p)
    return [t0 + n * p for n in range(n0, n1 + 1)]


def nearest(t, p, t0):
    """Distance from t to the nearest t0 + n p, any n."""
    return abs(t - (t0 + round((t - t0) / p) * p))


def max_offset(pa, ta, pb, tb, lo=T_START, hi=T_END):
    """Largest distance from an event of either train (inside the span) to the other's nearest event."""
    ea, eb = events(pa, ta, lo, hi), events(pb, tb, lo, hi)
    if len(ea) < 2 or len(eb) < 2:
        return None
    return max(max(nearest(a, pb, tb) for a in ea), max(nearest(b, pa, ta) for b in eb))


def sep_deg(ra1, dec1, ra2, dec2):
    """Great-circle separation in degrees (haversine)."""
    p1, p2 = math.radians(dec1), math.radians(dec2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(ra2 - ra1) / 2) ** 2
    return math.degrees(2 * math.asin(min(1.0, math.sqrt(h))))


def gnomonic(ra, dec, ra0=FOV_RA, dec0=FOV_DEC):
    """Tangent-plane (x, y) in degrees about (ra0, dec0)."""
    a, d, d0 = math.radians(ra - ra0), math.radians(dec), math.radians(dec0)
    c = math.sin(d0) * math.sin(d) + math.cos(d0) * math.cos(d) * math.cos(a)
    x = math.cos(d) * math.sin(a) / c
    y = (math.cos(d0) * math.sin(d) - math.sin(d0) * math.cos(d) * math.cos(a)) / c
    return math.degrees(x), math.degrees(y)


def d_max_arcsec(kepmag):
    """DR25 direct-PRF match radius for the brighter star's Kepler magnitude."""
    return 55.0 * math.sqrt(1e6 * 10 ** (-0.4 * kepmag) + 1)


def geometry(a, b):
    """(label, separation deg, d_max arcsec, antipodal miss arcsec); None values if a position is missing."""
    if None in (a["ra"], a["dec"], b["ra"], b["dec"]):
        return "far", None, None, None
    s = sep_deg(a["ra"], a["dec"], b["ra"], b["dec"])
    mags = [m for m in (a["kepmag"], b["kepmag"]) if m is not None]
    dm = d_max_arcsec(min(mags)) if mags else 55.0
    (xa, ya), (xb, yb) = gnomonic(a["ra"], a["dec"]), gnomonic(b["ra"], b["dec"])
    anti = math.hypot(xa + xb, ya + yb) * 3600
    if s * 3600 <= dm:
        g = "near"
    elif anti <= ANTI_ARCSEC:
        g = "antipodal"
    elif s <= MODULE_DEG:
        g = "module"
    else:
        g = "far"
    return g, s, dm, anti


def kois(rows, p_min=P_MIN):
    """Cumulative rows with P >= p_min, a mid-time and >= 2 events in the span, as dicts."""
    out = []
    for r in rows:
        p, t = num(r, "koi_period"), num(r, "koi_time0bk")
        if p is None or t is None or p < p_min or len(events(p, t)) < 2:
            continue
        out.append({"kepoi_name": r["kepoi_name"].strip(), "kepid": (r.get("kepid") or "").strip(),
                    "disp": (r.get("koi_disposition") or "").strip(), "p": p, "t": t,
                    "dur": num(r, "koi_duration"), "depth": num(r, "koi_depth"), "snr": num(r, "koi_model_snr"),
                    "kepmag": num(r, "koi_kepmag"), "ra": num(r, "ra"), "dec": num(r, "dec"),
                    "ec": (r.get("koi_fpflag_ec") or "").strip()})
    out.sort(key=lambda k: (k["p"], k["kepoi_name"]))
    return out


def candidate_pairs(ks, w=W):
    """Index pairs (i, j) on different stars whose periods are close enough to ever match: with at least
    n_min = floor(span / P_max) events, a 1:1 match needs |dP| (n_min - 1) <= 2 w."""
    out, span = [], T_END - T_START
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            dp = ks[j]["p"] - ks[i]["p"]
            if dp > 2 * w:
                break
            if ks[i]["kepid"] == ks[j]["kepid"]:
                continue
            n_min = max(2, math.floor(span / ks[j]["p"]))
            if dp * (n_min - 1) <= 2 * w:
                out.append((i, j))
    return out


def matches(ks, pairs, epochs=None, w=W):
    """[(i, j, max_offset)] for pairs that match; epochs overrides each KOI's t (the null)."""
    out = []
    for i, j in pairs:
        ta = epochs[i] if epochs else ks[i]["t"]
        tb = epochs[j] if epochs else ks[j]["t"]
        m = max_offset(ks[i]["p"], ta, ks[j]["p"], tb)
        if m is not None and m <= w:
            out.append((i, j, m))
    return out


def has_cand(ks, i, j):
    return "CANDIDATE" in (ks[i]["disp"], ks[j]["disp"])


def null_counts(ks, pairs, geoms, n=N_SHUFFLES, seed=SEED, w=W):
    """Far matches with >= 1 CANDIDATE per shuffle; epochs redrawn uniformly within one period."""
    rng = random.Random(seed)
    far = [pq for pq in pairs if geoms[pq][0] == "far" and has_cand(ks, *pq)]
    runs = []
    for _ in range(n):
        ep = [T_START + rng.random() * k["p"] for k in ks]
        runs.append(len(matches(ks, far, ep, w)))
    return runs


def build_rows(ks, found, geoms, lis):
    rows = []
    for i, j, m in found:
        a, b = ks[i], ks[j]
        g, s, dm, anti = geoms[(i, j)]
        row = {"geom": g, "max_offset": round(m, 4), "n_a": len(events(a["p"], a["t"])),
               "n_b": len(events(b["p"], b["t"])), "sep_deg": None if s is None else round(s, 4),
               "d_max_arcsec": None if dm is None else round(dm, 1),
               "anti_arcsec": None if anti is None else round(anti, 1),
               "events_a": [round(e, 3) for e in events(a["p"], a["t"])][:30]}
        for tag, k in (("a", a), ("b", b)):
            row.update({f"kepoi_{tag}": k["kepoi_name"], f"kepid_{tag}": k["kepid"], f"disp_{tag}": k["disp"],
                        f"p_{tag}": k["p"], f"t_{tag}": k["t"], f"dur_{tag}": k["dur"], f"depth_{tag}": k["depth"],
                        f"snr_{tag}": k["snr"], f"kepmag_{tag}": k["kepmag"], f"ec_{tag}": k["ec"],
                        f"lissauer_{tag}": lis.get(k["kepoi_name"], "")})
        rows.append(row)
    rows.sort(key=lambda r: (GEOMS.index(r["geom"]), r["p_a"]))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--koi-csv")
    ap.add_argument("--xmatch")
    ap.add_argument("--shuffles", type=int, default=N_SHUFFLES)
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

    tap = TAP + "?" + urllib.parse.urlencode({"query": KOI_QUERY, "format": "csv"})
    koi_rows = read_csv(load(args.koi_csv, tap, "cumulative.csv"))
    xmatch = read_csv(load(args.xmatch, XMATCH_URL, "xmatch.csv"))
    lis = {r["kepoi_name"]: r.get("lissauer_now", "") for r in xmatch}

    ks = kois(koi_rows)
    pairs = candidate_pairs(ks)
    geoms = {pq: geometry(ks[pq[0]], ks[pq[1]]) for pq in pairs}
    found = matches(ks, pairs)
    rows = build_rows(ks, found, geoms, lis)
    runs = null_counts(ks, pairs, geoms, args.shuffles)

    far_c = [r for r in rows if r["geom"] == "far" and "CANDIDATE" in (r["disp_a"], r["disp_b"])]
    in_far = {r[f"kepoi_{t}"] for r in far_c for t in "ab" if r[f"disp_{t}"] == "CANDIDATE"}
    snr_far = [k["snr"] for k in ks if k["kepoi_name"] in in_far and k["snr"] is not None]
    snr_rest = [k["snr"] for k in ks if k["disp"] == "CANDIDATE" and k["kepoi_name"] not in in_far
                and k["snr"] is not None]
    by_geom = {g: sum(r["geom"] == g for r in rows) for g in GEOMS}
    by_geom_c = {g: sum(r["geom"] == g and "CANDIDATE" in (r["disp_a"], r["disp_b"]) for r in rows) for g in GEOMS}
    null_mean = statistics.fmean(runs) if runs else None
    summary = {
        "version": VERSION, "span_bkjd": [T_START, T_END], "p_min": P_MIN, "w_days": W,
        "koi_rows": len(koi_rows), "kois_used": len(ks), "candidate_pairs": len(pairs),
        "matches": len(rows), "matches_by_geom": by_geom, "matches_with_candidate_by_geom": by_geom_c,
        "far_candidate_matches": len(far_c),
        "null": {"shuffles": len(runs), "seed": SEED, "mean": null_mean,
                 "max": max(runs) if runs else None,
                 "p_ge_observed": (1 + sum(x >= len(far_c) for x in runs)) / (1 + len(runs)) if runs else None},
        "far_candidate_p_gt_200": sum(r["p_a"] > 200 for r in far_c),
        "snr_median_far_candidates": statistics.median(snr_far) if snr_far else None,
        "snr_median_other_candidates": statistics.median(snr_rest) if snr_rest else None,
        "n_snr_far": len(snr_far), "n_snr_other": len(snr_rest),
        "far_candidate": [
            f"{r['kepoi_a']} ({r['disp_a']}, P={r['p_a']}, Lissauer {r['lissauer_a'] or '-'}) ~ "
            f"{r['kepoi_b']} ({r['disp_b']}, P={r['p_b']}, Lissauer {r['lissauer_b'] or '-'}) "
            f"max_offset={r['max_offset']} d sep={r['sep_deg']} deg" for r in far_c],
        "sources": {"koi": args.koi_csv or tap, "xmatch": args.xmatch or XMATCH_URL,
                    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
    }
    with open(os.path.join(args.out_dir, "ephem_pairs.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=ROW_FIELDS, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    json.dump(summary, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
