"""kepler_alias: Kepler planets whose periods in different catalogues differ by a whole factor, and a
light-curve test of which one is real.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library plus astropy for FITS.

Found by hand first (2026-10-16): Kepler-1802 b (KOI-2174.03). Every KOI table lists 7.72513619 d and
382 ppm, but its DR25 TCE (number 2) is 15.4502 d and 739 ppm, and the Archive's default (Valizadegan
et al. 2022) is 15.4502 d. If transits came every 7.725 d, folding on 15.45 d would not double the
depth; if they come every 15.45 d, folding on 7.725 d averages each one with an empty orbit and halves
it. So the depth ratio points to 15.45 d. Either way the composite row pairs the 15.45 d period with
a = 0.0662 AU, a/R* = 10.88, insolation 26.9 and Teq 581 K from the 7.725 d KOI fit.
0.1.0 (2026-10-16T12:41Z) found Kepler-1802 b long_period_real (649 +- 55 ppm against -67 +- 49), and
two planets whose Archive period is twice the light curve's: Kepler-1604 b (0.684 d against DR25's
0.342 d) and Kepler-1301 b (9.082 d against its DR25 TCE's 4.541 d). 0.2.0 adds a second census that
compares the Archive's composite period with the DR25 KOI period directly (the route that finds
Kepler-1604 b), and splits each group's depth into the first and second half of the mission.
0.2.0 (2026-10-16T16:01Z) added Kepler-1632 b: all six 224.15 d epochs are deep, so the Archive's
448.30 d (Morton et al. 2016) is twice the real period. 0.3.0 tests DR25 candidates too (--dispositions),
and adds the pipeline's odd-even statistic, the KOI's transit count and a flag for counts the KOI
period cannot allow (Kepler-1301 b: 298 transits listed, at most 161 at 9.08 d).

Method:
1. TCE census. Join the DR25 TCE and KOI tables on (kepid, TCE number). k is the whole number 2..5
   with P_long / P_short = k within 0.2 %; "tce_long" if the TCE period is the longer, "koi_long" if
   the KOI period is. depth_ratio = depth at the longer period / depth at the shorter; about k if the
   long period is real, about 1 if the short one is.
2. Archive census. The same test between the composite pl_orbper and the DR25 KOI period of each
   Kepler planet; "archive_long" or "koi_long". The fold always uses the KOI ephemeris: P_short is the
   KOI period, or the KOI period / k if the Archive's is the shorter. The long period's phase comes
   from pl_tranmid (BJD - 2454833 = BKJD), or is the KOI epoch itself.
3. Light curves (Kepler long cadence PDCSAP, quality 0) for the chosen dispositions from the TCE census
   (and, for CONFIRMED, the Archive census), Kepler-1802 b first. Epochs on the short period are split
   into k groups (epoch mod k). Each epoch's depth is the mean deficit of the central 70 % of the KOI
   duration below a straight line fitted to points 1 to 3 durations from mid-transit (at least
   0.25 d), with the star's other KOIs masked.
     long_period_real   one group >= 5 sigma deep, at the long period's phase, the others within 3
                        sigma of zero;
     short_period_real  every group >= 5 sigma deep and all agree within 3 sigma;
     inconclusive       otherwise.
   The same group depths are also given for the first and second half of the epochs.
4. Compare with the Archive's composite pl_orbper and pl_orbsmax (Kepler's law with st_mass).
5. Transit count. max_transits = floor(1459.5 / koi_period) + 1 (Q1-Q17 span BKJD 131.5-1591.0);
   impossible_count = "yes" if koi_num_transits is larger.
A verdict is a candidate to check by eye, not a published correction. A short_period_real verdict
also fits an eclipsing binary at the long period with two equal eclipses.

Usage: python kepler_alias.py --out-dir /out [--data-dir /data] [--max-targets 40]
                              [--dispositions CONFIRMED,CANDIDATE]
"""
import argparse
import bisect
import csv
import datetime as dt
import json
import math
import os
import re
import statistics
import sys
import tempfile
import urllib.parse
import urllib.request

VERSION = "0.3.0"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
MAST = "https://archive.stsci.edu/missions/kepler/lightcurves/{d4}/{d9}/"
UA = f"kepler-alias/{VERSION} (Munim, Inc.; mv2@munimtech.com)"
TOL = 0.002
MAX_K = 5
SIG_DEEP, SIG_EMPTY = 5.0, 3.0
ERR_FLOOR = 1e-6
BKJD = 2454833.0
MISSION_DAYS = 1459.5
CHECK = "K02174.03"
JOIN = ("select t.kepid, t.tce_plnt_num, t.tce_period, t.tce_time0bk, t.tce_depth, t.tce_duration, "
        "t.tce_bin_oedp_stat, k.kepoi_name, k.kepler_name, k.koi_period, k.koi_time0bk, k.koi_depth, "
        "k.koi_duration, k.koi_disposition, k.koi_prad, k.koi_num_transits from q1_q17_dr25_tce t "
        "join q1_q17_dr25_koi k on t.kepid = k.kepid and t.tce_plnt_num = k.koi_tce_plnt_num")
KOIS = ("select kepid, kepoi_name, kepler_name, koi_disposition, koi_period, koi_time0bk, koi_depth, "
        "koi_duration, koi_prad, koi_num_transits from q1_q17_dr25_koi")
COMP = ("select pl_name, pl_orbper, pl_orbper_reflink, pl_tranmid, pl_orbsmax, pl_orbsmax_reflink, st_mass "
        "from pscomppars")


def http_bytes(url, timeout=600):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch(query, path):
    if path and os.path.exists(path) and os.path.getsize(path) > 1000:
        with open(path, encoding="utf-8") as f:
            return f.read()
    text = http_bytes(TAP + "?" + urllib.parse.urlencode({"query": query, "format": "csv"}), 900).decode("utf-8")
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


def alias_factor(p_tce, p_koi):
    """(k, which): k = 2..5 if one period is k times the other, which = 'tce_long' or 'koi_long';
    (1, 'same') if equal within TOL; (0, 'other') otherwise."""
    if not p_tce or not p_koi or p_tce <= 0 or p_koi <= 0:
        return 0, "other"
    r = p_tce / p_koi
    for k in range(2, MAX_K + 1):
        if abs(r / k - 1) <= TOL:
            return k, "tce_long"
        if abs(1 / (r * k) - 1) <= TOL:
            return k, "koi_long"
    return (1, "same") if abs(r - 1) <= TOL else (0, "other")


def kepler_smax(m_star, p_days):
    if not m_star or not p_days or m_star <= 0 or p_days <= 0:
        return None
    return (m_star * (p_days / 365.25) ** 2) ** (1 / 3)


def max_transits(p_days):
    """Most transits a period can have in the Q1-Q17 span, or None."""
    if not p_days or p_days <= 0:
        return None
    return math.floor(MISSION_DAYS / p_days) + 1


def count_columns(row, p_koi):
    """The odd-even statistic, the KOI's transit count, its ceiling and the impossible-count flag."""
    n, m = num(row, "koi_num_transits"), max_transits(p_koi)
    return {"oedp_stat": num(row, "tce_bin_oedp_stat"), "koi_num_transits": n, "max_transits": m,
            "impossible_count": "yes" if n is not None and m is not None and n > m else ""}


def add_archive(out, c, p_long, p_short):
    """Fill the Archive comparison columns of a census row from composite row c (may be None)."""
    if not c:
        return out
    p_a = num(c, "pl_orbper")
    out["archive_period"] = "" if p_a is None else p_a
    out["archive_period_ref"] = ref_text(c.get("pl_orbper_reflink", ""))
    if p_a:
        out["archive_matches"] = ("long" if abs(p_a / p_long - 1) <= TOL else
                                  "short" if abs(p_a / p_short - 1) <= TOL else "neither")
    a, a_k = num(c, "pl_orbsmax"), kepler_smax(num(c, "st_mass"), p_a)
    out["archive_smax"] = "" if a is None else a
    out["archive_smax_ref"] = ref_text(c.get("pl_orbsmax_reflink", ""))
    if a and a_k:
        out["smax_kepler_ratio"] = round(a / a_k, 4)
    return out


def census_row(row, comp=None):
    """One TCE-census row for a joined TCE/KOI row with k >= 2, else None."""
    p_tce, p_koi = num(row, "tce_period"), num(row, "koi_period")
    k, which = alias_factor(p_tce, p_koi)
    if k < 2:
        return None
    if which == "tce_long":
        p_long, t0_long, d_long = p_tce, num(row, "tce_time0bk"), num(row, "tce_depth")
        p_short, t0_short, d_short = p_koi, num(row, "koi_time0bk"), num(row, "koi_depth")
    else:
        p_long, t0_long, d_long = p_koi, num(row, "koi_time0bk"), num(row, "koi_depth")
        p_short, t0_short, d_short = p_tce, num(row, "tce_time0bk"), num(row, "tce_depth")
    ratio = d_long / d_short if d_long and d_short and d_short > 0 else None
    hint = "" if ratio is None else ("long" if ratio >= (1 + k) / 2 else "short")
    long_group = round((t0_long - t0_short) / p_short) % k if t0_long is not None and t0_short is not None else ""
    out = {"census": "tce", "kepid": row.get("kepid", ""), "kepoi_name": row.get("kepoi_name", ""),
           "kepler_name": row.get("kepler_name", ""), "koi_disposition": row.get("koi_disposition", ""),
           "k": k, "which_long": which, "tce_period": p_tce, "koi_period": p_koi,
           "p_short": p_short, "t0_short": t0_short, "p_long": p_long, "long_group": long_group,
           "tce_depth_ppm": num(row, "tce_depth"), "koi_depth_ppm": num(row, "koi_depth"),
           "depth_ratio": "" if ratio is None else round(ratio, 4), "depth_hint": hint,
           "koi_duration_h": num(row, "koi_duration"), "koi_prad": num(row, "koi_prad"),
           "archive_period": "", "archive_period_ref": "", "archive_matches": "", "archive_smax": "",
           "archive_smax_ref": "", "smax_kepler_ratio": ""}
    out.update(count_columns(row, p_koi))
    return add_archive(out, (comp or {}).get(row.get("kepler_name", "")), p_long, p_short)


def archive_row(koi, comp):
    """One Archive-census row for a DR25 KOI whose composite period is k = 2..5 times its KOI period
    (or 1/k of it), else None. The fold uses the KOI ephemeris."""
    c = (comp or {}).get(koi.get("kepler_name", ""))
    if not c:
        return None
    p_a, p_k, t0_k = num(c, "pl_orbper"), num(koi, "koi_period"), num(koi, "koi_time0bk")
    k, which = alias_factor(p_a, p_k)
    if k < 2:
        return None
    tm = num(c, "pl_tranmid")
    if which == "tce_long":  # the Archive's period is the longer
        which, p_short, p_long, t0_short = "archive_long", p_k, p_a, t0_k
        long_group = round((tm - BKJD - t0_k) / p_k) % k if tm is not None and t0_k is not None else ""
    else:
        p_short, p_long, t0_short, long_group = p_k / k, p_k, t0_k, 0
    out = {"census": "archive", "kepid": koi.get("kepid", ""), "kepoi_name": koi.get("kepoi_name", ""),
           "kepler_name": koi.get("kepler_name", ""), "koi_disposition": koi.get("koi_disposition", ""),
           "k": k, "which_long": which, "tce_period": "", "koi_period": p_k,
           "p_short": p_short, "t0_short": t0_short, "p_long": p_long, "long_group": long_group,
           "tce_depth_ppm": "", "koi_depth_ppm": num(koi, "koi_depth"), "depth_ratio": "", "depth_hint": "",
           "koi_duration_h": num(koi, "koi_duration"), "koi_prad": num(koi, "koi_prad"),
           "archive_period": "", "archive_period_ref": "", "archive_matches": "", "archive_smax": "",
           "archive_smax_ref": "", "smax_kepler_ratio": ""}
    out.update(count_columns(koi, p_k))
    return add_archive(out, c, p_long, p_short)


def select_targets(census, arch, dispositions, max_targets):
    """Census rows to test: the TCE census rows with a chosen disposition, then (for CONFIRMED) the
    Archive census; one per KOI, only those with an ephemeris, a duration and a long-period phase."""
    pool = [c for c in census if c["koi_disposition"] in dispositions]
    if "CONFIRMED" in dispositions:
        pool += arch
    seen, targets = set(), []
    for c in pool:
        if c["kepoi_name"] in seen or c["t0_short"] is None or not c["koi_duration_h"] or c["long_group"] == "":
            continue
        seen.add(c["kepoi_name"])
        targets.append(c)
    return targets[:max_targets]


def mask_others(times, others):
    """True where a point falls within 0.75 durations of another KOI's transit; others = [(P, t0, dur_h)]."""
    mask = []
    for t in times:
        hit = False
        for p, t0, dur_h in others:
            if p and t0 is not None and dur_h:
                if abs(((t - t0 + p / 2) % p) - p / 2) < 0.75 * dur_h / 24.0:
                    hit = True
                    break
        mask.append(hit)
    return mask


def line_fit(pts):
    n = len(pts)
    sx = sum(x for x, _ in pts)
    sy = sum(y for _, y in pts)
    sxx = sum(x * x for x, _ in pts)
    sxy = sum(x * y for x, y in pts)
    den = n * sxx - sx * sx
    b = (n * sxy - sx * sy) / den if den else 0.0
    a = (sy - b * sx) / n
    res = [y - (a + b * x) for x, y in pts]
    rms = math.sqrt(sum(r * r for r in res) / max(1, n - 2))
    return a, b, rms


def epoch_depths(times, fluxes, p, t0, dur_h, mask=None):
    """[(n, depth, err, n_in, n_out)] for each epoch n of (p, t0) with enough points; times sorted."""
    dur = dur_h / 24.0
    half_in = 0.35 * dur
    w = max(3 * dur, dur + 0.25)
    out = []
    if not times:
        return out
    n0 = math.ceil((times[0] - w - t0) / p)
    n1 = math.floor((times[-1] + w - t0) / p)
    for n in range(n0, n1 + 1):
        tc = t0 + n * p
        i, j = bisect.bisect_left(times, tc - w), bisect.bisect_right(times, tc + w)
        inn, before, after = [], [], []
        for q in range(i, j):
            if mask and mask[q]:
                continue
            d = times[q] - tc
            if abs(d) < half_in:
                inn.append((d, fluxes[q]))
            elif abs(d) >= dur:
                (before if d < 0 else after).append((d, fluxes[q]))
        if len(inn) < 2 or len(before) < 3 or len(after) < 3:
            continue
        oot = before + after
        a, b, rms = line_fit(oot)
        depth = sum(1 - f / (a + b * d) for d, f in inn) / len(inn)
        err = max(rms * math.sqrt(1 / len(inn) + 1 / len(oot)), ERR_FLOOR)
        out.append((n, depth, err, len(inn), len(oot)))
    return out


def group_stats(epochs, k):
    """Weighted mean depth per group n mod k, error scaled up by sqrt(reduced chi2) when above 1."""
    groups = []
    for g in range(k):
        rows = [(d, e) for n, d, e, _, _ in epochs if n % k == g]
        if not rows:
            groups.append({"group": g, "epochs": 0, "depth": None, "err": None, "snr": None})
            continue
        ws = [1 / e ** 2 for _, e in rows]
        sw = sum(ws)
        mean = sum(d * wi for (d, _), wi in zip(rows, ws)) / sw
        err = 1 / math.sqrt(sw)
        if len(rows) > 1:
            chi2 = sum(((d - mean) / e) ** 2 for d, e in rows) / (len(rows) - 1)
            err *= math.sqrt(max(1.0, chi2))
        groups.append({"group": g, "epochs": len(rows), "depth": mean, "err": err, "snr": mean / err})
    return groups


def split_halves(epochs, k):
    """(groups of the first half of the epochs, groups of the second half), split at the middle epoch."""
    if not epochs:
        return group_stats([], k), group_stats([], k)
    ordered = sorted(epochs)
    cut = ordered[len(ordered) // 2][0]
    return (group_stats([e for e in ordered if e[0] < cut], k),
            group_stats([e for e in ordered if e[0] >= cut], k))


def verdict(groups, long_group):
    if not groups or any(g["epochs"] == 0 for g in groups):
        return "inconclusive"
    deep = [g for g in groups if g["snr"] >= SIG_DEEP]
    empty = [g for g in groups if abs(g["snr"]) < SIG_EMPTY]
    if len(deep) == 1 and len(empty) == len(groups) - 1:
        return "long_period_real" if deep[0]["group"] == long_group else "inconclusive"
    if len(deep) == len(groups):
        agree = all(abs(a["depth"] - b["depth"]) / math.hypot(a["err"], b["err"]) < SIG_EMPTY
                    for i, a in enumerate(groups) for b in groups[i + 1:])
        return "short_period_real" if agree else "inconclusive"
    return "inconclusive"


def lightcurve_files(kepid, cache):
    d9 = f"{int(kepid):09d}"
    url = MAST.format(d4=d9[:4], d9=d9)
    names = sorted(set(re.findall(r"kplr\d{9}-\d{13}_llc\.fits", http_bytes(url, 300).decode("utf-8", "replace"))))
    paths = []
    for name in names:
        path = os.path.join(cache, "kepler", d9, name)
        if not (os.path.exists(path) and os.path.getsize(path) > 10000):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = http_bytes(url + name, 300)
            with open(path + ".part", "wb") as f:
                f.write(data)
            os.replace(path + ".part", path)
        paths.append(path)
    return paths


def read_llc(path):
    """[(BKJD, normalised PDCSAP flux)] for quality-0 cadences of one quarter."""
    from astropy.io import fits
    with fits.open(path, memmap=False) as h:
        d = h[1].data
        good = [(float(t), float(f)) for t, f, q in zip(d["TIME"], d["PDCSAP_FLUX"], d["SAP_QUALITY"])
                if int(q) == 0 and math.isfinite(float(t)) and math.isfinite(float(f))]
    if not good:
        return []
    med = statistics.median(f for _, f in good)
    return [(t, f / med) for t, f in good] if med > 0 else []


def test_target(c, koi_rows, cache):
    pts = []
    for path in lightcurve_files(c["kepid"], cache):
        pts.extend(read_llc(path))
    pts.sort()
    times, fluxes = [t for t, _ in pts], [f for _, f in pts]
    others = [(num(r, "koi_period"), num(r, "koi_time0bk"), num(r, "koi_duration")) for r in koi_rows
              if r.get("kepid") == c["kepid"] and r.get("kepoi_name") != c["kepoi_name"]]
    mask = mask_others(times, others)
    epochs = epoch_depths(times, fluxes, c["p_short"], c["t0_short"], c["koi_duration_h"], mask)
    groups = group_stats(epochs, c["k"])
    return len(times), epochs, groups, verdict(groups, c["long_group"]), split_halves(epochs, c["k"])


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def fmt(x, scale=1.0, nd=1):
    return "" if x is None or x == "" else f"{x * scale:.{nd}f}"


def groups_text(groups):
    return "; ".join(f"g{g['group']}: n={g['epochs']} depth={fmt(g['depth'], 1e6)}"
                     f"+-{fmt(g['err'], 1e6)} ppm snr={fmt(g['snr'])}" for g in groups)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-dir", default="")
    ap.add_argument("--max-targets", type=int, default=40)
    ap.add_argument("--dispositions", default="CONFIRMED")
    args = ap.parse_args(argv)
    dispositions = {d.strip() for d in args.dispositions.split(",") if d.strip()}
    os.makedirs(args.out_dir, exist_ok=True)
    cache = args.data_dir or tempfile.mkdtemp()
    p = (lambda n: os.path.join(args.data_dir, n)) if args.data_dir else (lambda n: None)
    joined = list(csv.DictReader(fetch(JOIN, p("dr25-tce-koi-v3.csv")).splitlines()))
    kois = list(csv.DictReader(fetch(KOIS, p("dr25-koi-v3.csv")).splitlines()))
    comp = {r["pl_name"]: r for r in csv.DictReader(fetch(COMP, p("pc-alias-v2.csv")).splitlines())}

    census = [c for c in (census_row(r, comp) for r in joined) if c]
    census.sort(key=lambda c: (c["kepoi_name"] != CHECK, c["koi_disposition"] != "CONFIRMED", c["kepoi_name"]))
    fields = list(census[0].keys()) if census else []
    write_csv(os.path.join(args.out_dir, "census.csv"), census, fields)
    arch = sorted((c for c in (archive_row(r, comp) for r in kois) if c), key=lambda c: c["kepoi_name"])
    write_csv(os.path.join(args.out_dir, "archive_census.csv"), arch, fields or (list(arch[0].keys()) if arch else []))

    targets = select_targets(census, arch, dispositions, args.max_targets)
    tests, epoch_rows = [], []
    for c in targets:
        row = {"census": c["census"], "kepoi_name": c["kepoi_name"], "kepler_name": c["kepler_name"],
               "koi_disposition": c["koi_disposition"], "k": c["k"],
               "which_long": c["which_long"], "p_short": c["p_short"], "p_long": c["p_long"],
               "long_group": c["long_group"], "depth_ratio": c["depth_ratio"], "depth_hint": c["depth_hint"],
               "oedp_stat": c["oedp_stat"], "koi_num_transits": c["koi_num_transits"],
               "max_transits": c["max_transits"], "impossible_count": c["impossible_count"],
               "archive_period": c["archive_period"], "archive_period_ref": c["archive_period_ref"],
               "archive_matches": c["archive_matches"], "smax_kepler_ratio": c["smax_kepler_ratio"]}
        try:
            n_pts, epochs, groups, v, (h1, h2) = test_target(c, kois, cache)
            row.update({"points": n_pts, "epochs": len(epochs), "verdict": v, "error": "",
                        "groups": groups_text(groups), "first_half": groups_text(h1), "second_half": groups_text(h2)})
            epoch_rows += [{"kepoi_name": c["kepoi_name"], "epoch": n, "group": n % c["k"],
                            "depth_ppm": round(d * 1e6, 1), "err_ppm": round(e * 1e6, 1), "n_in": a, "n_out": b}
                           for n, d, e, a, b in epochs]
        except Exception as exc:  # one target's download or file problem must not stop the others
            row.update({"points": "", "epochs": "", "verdict": "error", "groups": "", "first_half": "",
                        "second_half": "", "error": f"{type(exc).__name__}: {exc}"[:300]})
        tests.append(row)
        print(json.dumps({k: row[k] for k in ("kepoi_name", "kepler_name", "verdict", "groups", "error")}),
              flush=True)
    test_fields = ["census", "kepoi_name", "kepler_name", "koi_disposition", "k", "which_long", "p_short",
                   "p_long", "long_group", "depth_ratio", "depth_hint", "oedp_stat", "koi_num_transits",
                   "max_transits", "impossible_count", "archive_period", "archive_period_ref", "archive_matches",
                   "smax_kepler_ratio", "points", "epochs", "verdict", "groups", "first_half", "second_half",
                   "error"]
    write_csv(os.path.join(args.out_dir, "lightcurve_tests.csv"), tests, test_fields)
    write_csv(os.path.join(args.out_dir, "epochs.csv"), epoch_rows,
              ["kepoi_name", "epoch", "group", "depth_ppm", "err_ppm", "n_in", "n_out"])

    conf = [c for c in census if c["koi_disposition"] == "CONFIRMED"]
    check = next((t for t in tests if t["kepoi_name"] == CHECK), None)
    stats = {
        "version": VERSION, "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "dispositions": sorted(dispositions),
        "joined_rows": len(joined), "koi_rows": len(kois), "composite_rows": len(comp),
        "alias_pairs": len(census), "tce_long": sum(1 for c in census if c["which_long"] == "tce_long"),
        "koi_long": sum(1 for c in census if c["which_long"] == "koi_long"),
        "confirmed_alias_pairs": len(conf),
        "confirmed_depth_hint_long": sum(1 for c in conf if c["depth_hint"] == "long"),
        "confirmed_archive_long": sum(1 for c in conf if c["archive_matches"] == "long"),
        "confirmed_archive_short": sum(1 for c in conf if c["archive_matches"] == "short"),
        "archive_alias_pairs": len(arch),
        "archive_alias_archive_long": sum(1 for c in arch if c["which_long"] == "archive_long"),
        "impossible_count_pairs": sum(1 for c in census if c["impossible_count"]),
        "tested": len(tests), "verdicts": {v: sum(1 for t in tests if t["verdict"] == v) for v in
                                           ("long_period_real", "short_period_real", "inconclusive", "error")},
        "check_kepler_1802_b": None if not check else {k: check[k] for k in ("verdict", "groups", "error")},
    }
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

    lines = [f"# kepler-alias {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY "
             "4.0. A verdict is a candidate to check by eye, not a published correction. short_period_real also "
             "fits an eclipsing binary at the long period with two equal eclipses.", ""]
    lines += [f"- {k}: {v}" for k, v in stats.items() if k not in ("version", "run_at")]
    lines += ["", "## Light-curve tests", "",
              "| census | KOI | planet | disposition | k | longer | P short | P long | depth ratio (hint) | odd-even "
              "| transits / max | Archive P (ref) | verdict | groups | first half | second half |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in tests:
        lines.append(f"| {t['census']} | {t['kepoi_name']} | {t['kepler_name']} | {t['koi_disposition']} | {t['k']} | "
                     f"{t['which_long']} | {t['p_short']} | {t['p_long']} | {t['depth_ratio']} ({t['depth_hint']}) | "
                     f"{t['oedp_stat'] if t['oedp_stat'] is not None else ''} | "
                     f"{fmt(t['koi_num_transits'], nd=0)} / {t['max_transits'] or ''}"
                     f"{' IMPOSSIBLE' if t['impossible_count'] else ''} | "
                     f"{t['archive_period']} ({t['archive_period_ref']}) | {t['verdict']} | "
                     f"{t['groups'] or t['error']} | {t['first_half']} | {t['second_half']} |")
    lines += ["", "## Archive census: composite period k times the DR25 KOI period, or 1/k", "",
              "| KOI | planet | disposition | k | longer | KOI P | Archive P (ref) | a / Kepler a |",
              "|---|---|---|---|---|---|---|---|"]
    for c in arch:
        lines.append(f"| {c['kepoi_name']} | {c['kepler_name']} | {c['koi_disposition']} | {c['k']} | "
                     f"{c['which_long']} | {c['koi_period']} | {c['archive_period']} ({c['archive_period_ref']}) | "
                     f"{c['smax_kepler_ratio']} |")
    lines += ["", "## TCE census rows whose transit count the KOI period cannot allow", "",
              "| KOI | planet | disposition | k | TCE P | KOI P | transits | max at KOI P | odd-even |",
              "|---|---|---|---|---|---|---|---|---|"]
    for c in census:
        if c["impossible_count"]:
            lines.append(f"| {c['kepoi_name']} | {c['kepler_name']} | {c['koi_disposition']} | {c['k']} | "
                         f"{c['tce_period']} | {c['koi_period']} | {fmt(c['koi_num_transits'], nd=0)} | "
                         f"{c['max_transits']} | {c['oedp_stat'] if c['oedp_stat'] is not None else ''} |")
    lines += ["", "## Confirmed planets in the TCE census (first 100)", "",
              "| KOI | planet | k | longer | TCE P | KOI P | depth ratio | hint | Archive P (ref) | a / Kepler a |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for c in conf[:100]:
        lines.append(f"| {c['kepoi_name']} | {c['kepler_name']} | {c['k']} | {c['which_long']} | {c['tce_period']} | "
                     f"{c['koi_period']} | {c['depth_ratio']} | {c['depth_hint']} | {c['archive_period']} "
                     f"({c['archive_period_ref']}) | {c['smax_kepler_ratio']} |")
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
