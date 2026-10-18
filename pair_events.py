"""pair_events: what each star's own light curve shows at the shared transit times of the three cross-star
Kepler ephemeris pairs (findings/2026-10-18-cross-star-ephemeris-pairs.md).

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library; astropy reads the FITS files.

Pairs (stars 3.9-7.8 deg apart, each sharing three observed events within 0.37 d):
  A  K05660.01 (KIC 9363944)  ~ K08259.01 (KIC 5956171)   402 d
  B  K05935.01 (KIC 11818566) ~ K05446.01 (KIC 7917068)   417 d
  C  K07040.01 (KIC 8442795)  ~ K07932.01 (KIC 9278575)   502 d
  plus KIC 7049486 (eclipsing binary K06815.01), whose DR25 TCE 3 (250.981 d) hits pair C's dates.
Pre-registration: findings/2026-10-18-pair-events-prereg.md in munimtechnologies/exoplanet-archive-audit.

Method. Every star is measured at the events of every ephemeris in HYPS that fall in its data, so each
star's own events sit next to controls (the other pairs' dates). Quality-0 long-cadence points only.
For one event and one column, a straight line is fitted to points 1 to 3 durations from the centre and
the mean residual of the central 70 % of the duration is taken (the kepler_alias 0.3.0 box):
  pdc_ppm   PDCSAP deficit, sap_ppm  SAP deficit (both per-quarter normalised, ppm of the baseline)
  bkg_ppm   excess of SAP_BKG in units of the quarter's median SAP_FLUX: SAP = raw - background, so an
            over-estimated background makes a SAP dip of the same size
  c1_mpix, c2_mpix   MOM_CENTR1/2 shift (millipixels, column / row)
  flags     cadences with SAP_QUALITY != 0 within +-1 d, and the OR of their bits
Null. The PDCSAP deficit at NULL_N evenly spaced times across the star's data, skipping +-2 d of every
event measured on it, gives the star's empirical distribution: pct (fraction of null deficits below the
event's) and z (deficit / 1.4826 MAD of the null).
A "dip" (pre-registered) is pdc_ppm > 0 with pct >= 0.95. Read the results as leads, not dispositions.

Usage: python pair_events.py --data-dir /data --out-dir /out/pairs
"""
import argparse
import bisect
import csv
import datetime as dt
import hashlib
import json
import math
import os
import re
import statistics
import sys
import tempfile
import urllib.request

VERSION = "0.1.0"
MAST = "https://archive.stsci.edu/missions/kepler/lightcurves/{d4}/{d9}/"
UA = f"pair-events/{VERSION} (Munim, Inc.; mv2@munimtech.com)"
ERR_FLOOR = 1e-9
NULL_N = 300
NULL_AVOID = 2.0
FLAG_HALF = 1.0
DIP_PCT = 0.95

# name: (period d, T0 BKJD); catalogue rows quoted in the pairs note (NASA Exoplanet Archive, 2026-10-18)
HYPS = {
    "K05660.01": (402.20969, 369.5086),
    "K08259.01": (402.27493, 369.6734),
    "K05935.01": (416.87893, 227.5107),
    "K05446.01": (416.9504, 227.392),
    "K07040.01": (502.20642, 162.9131),
    "K07932.01": (502.25648, 162.5842),
    "EB-TCE3": (250.981, 163.411),
}
# label: (kepid, duration h used for every box on this star, masks [(P, T0, dur_h)] removed first)
STARS = {
    "K05660.01": (9363944, 5.30, []),
    "K08259.01": (5956171, 15.67, []),
    "K05935.01": (11818566, 4.45, []),
    "K05446.01": (7917068, 4.03, []),
    "K07040.01": (8442795, 9.39, []),
    "K07932.01": (9278575, 14.84, []),
    "EB-TCE3": (7049486, 8.777, [(26.7184, 138.054, 8.212), (26.7184, 156.04, 9.53)]),
}
PAIRS = [("A", "K05660.01", "K08259.01"), ("B", "K05935.01", "K05446.01"), ("C", "K07040.01", "K07932.01")]
COLUMNS = ("pdc", "sap", "bkg", "c1", "c2")


def line_fit(pts):
    """(a, b, rms) of y = a + b x by least squares."""
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


def box_fit(times, values, tc, dur_h):
    """(mean in-core residual, err, baseline at tc, n_in, n_out) or None; times sorted.

    In-core: |t - tc| < 0.35 duration. Baseline: a line through points with duration <= |t - tc| <= w,
    w = max(3 durations, duration + 0.25 d); at least 2 in-core and 3 on each side."""
    dur = dur_h / 24.0
    half_in = 0.35 * dur
    w = max(3 * dur, dur + 0.25)
    i, j = bisect.bisect_left(times, tc - w), bisect.bisect_right(times, tc + w)
    inn, before, after = [], [], []
    for q in range(i, j):
        d = times[q] - tc
        if abs(d) < half_in:
            inn.append((d, values[q]))
        elif abs(d) >= dur:
            (before if d < 0 else after).append((d, values[q]))
    if len(inn) < 2 or len(before) < 3 or len(after) < 3:
        return None
    oot = before + after
    a, b, rms = line_fit(oot)
    resid = sum(v - (a + b * d) for d, v in inn) / len(inn)
    err = max(rms * math.sqrt(1 / len(inn) + 1 / len(oot)), ERR_FLOOR)
    return resid, err, a, len(inn), len(oot)


def deficit_ppm(fit):
    """(deficit, err) in ppm of the baseline for a flux column, or None."""
    if fit is None or fit[2] == 0:
        return None
    return -fit[0] / fit[2] * 1e6, fit[1] / abs(fit[2]) * 1e6


def in_mask(t, masks):
    """True within one full duration of an epoch of any (P, T0, dur_h) in masks."""
    return any(abs(((t - t0 + p / 2) % p) - p / 2) < dur_h / 24.0 for p, t0, dur_h in masks)


def events_in(p, t0, t_first, t_last):
    """Event times t0 + n p inside [t_first, t_last]."""
    return [t0 + n * p for n in range(math.ceil((t_first - t0) / p), math.floor((t_last - t0) / p) + 1)]


def null_times(times, avoid_at, n=NULL_N, avoid=NULL_AVOID):
    """n evenly spaced times over [times[0], times[-1]], minus those within avoid days of avoid_at."""
    if not times:
        return []
    step = (times[-1] - times[0]) / n
    grid = [times[0] + (k + 0.5) * step for k in range(n)]
    return [t for t in grid if all(abs(t - e) >= avoid for e in avoid_at)]


def percentile_rank(x, xs):
    """Fraction of xs strictly below x."""
    return sum(1 for v in xs if v < x) / len(xs) if xs else None


def robust_sigma(xs):
    m = statistics.median(xs)
    return 1.4826 * statistics.median(abs(v - m) for v in xs)


def flag_summary(all_times, quality, tc, half=FLAG_HALF):
    """(count of cadences with quality != 0 within tc +- half, OR of their bits); all_times sorted."""
    i, j = bisect.bisect_left(all_times, tc - half), bisect.bisect_right(all_times, tc + half)
    bits = [quality[q] for q in range(i, j) if quality[q]]
    out = 0
    for b in bits:
        out |= b
    return len(bits), out


def measure(series, tc, dur_h):
    """Every column at one event: dict of ppm / millipixel values with errors ('' where no fit)."""
    row = {}
    for col in ("pdc", "sap"):
        r = deficit_ppm(box_fit(*series[col], tc, dur_h))
        row[col + "_ppm"], row[col + "_err"] = ("", "") if r is None else (round(r[0], 1), round(r[1], 1))
    f = box_fit(*series["bkg"], tc, dur_h)
    row["bkg_ppm"], row["bkg_err"] = ("", "") if f is None else (round(f[0] * 1e6, 1), round(f[1] * 1e6, 1))
    for col in ("c1", "c2"):
        f = box_fit(*series[col], tc, dur_h)
        row[col + "_mpix"], row[col + "_err"] = ("", "") if f is None else (round(f[0] * 1e3, 2),
                                                                            round(f[1] * 1e3, 2))
    return row


def build_series(quarters, masks):
    """quarters: [{time, pdc, sap, bkg, c1, c2, quality}] (lists per cadence) -> (series, all_times, quality).

    series[col] = (times, values) of quality-0, unmasked cadences where that column is finite; pdc and sap
    divided by their quarter medians, bkg by the quarter's median SAP_FLUX."""
    rows = {c: [] for c in COLUMNS}
    flags = []
    for q in quarters:
        good = [k for k, t in enumerate(q["time"]) if math.isfinite(t)]
        flags += [(q["time"][k], int(q["quality"][k])) for k in good]
        keep = [k for k in good if int(q["quality"][k]) == 0 and not in_mask(q["time"][k], masks)]
        sap_vals = [q["sap"][k] for k in keep if math.isfinite(q["sap"][k])]
        pdc_vals = [q["pdc"][k] for k in keep if math.isfinite(q["pdc"][k])]
        scale = {"pdc": statistics.median(pdc_vals) if pdc_vals else 0.0,
                 "sap": statistics.median(sap_vals) if sap_vals else 0.0}
        scale["bkg"] = scale["sap"]
        for col in COLUMNS:
            s = scale.get(col, 1.0)
            if not s:
                continue
            rows[col] += [(q["time"][k], q[col][k] / s) for k in keep if math.isfinite(q[col][k])]
    series = {}
    for col in COLUMNS:
        rows[col].sort()
        series[col] = ([t for t, _ in rows[col]], [v for _, v in rows[col]])
    flags.sort()
    return series, [t for t, _ in flags], [b for _, b in flags]


def http_bytes(url, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def lightcurve_files(kepid, cache):
    """Every long-cadence file of one star from MAST, cached under cache/kepler/<kepid>/."""
    d9 = f"{int(kepid):09d}"
    url = MAST.format(d4=d9[:4], d9=d9)
    names = sorted(set(re.findall(r"kplr\d{9}-\d{13}_llc\.fits", http_bytes(url).decode("utf-8", "replace"))))
    paths = []
    for name in names:
        path = os.path.join(cache, "kepler", d9, name)
        if not (os.path.exists(path) and os.path.getsize(path) > 10000):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = http_bytes(url + name)
            with open(path + ".part", "wb") as f:
                f.write(data)
            os.replace(path + ".part", path)
        paths.append(path)
    return paths


def read_quarter(path):
    from astropy.io import fits
    with fits.open(path, memmap=False) as h:
        d = h[1].data
        cols = {"time": "TIME", "pdc": "PDCSAP_FLUX", "sap": "SAP_FLUX", "bkg": "SAP_BKG",
                "c1": "MOM_CENTR1", "c2": "MOM_CENTR2", "quality": "SAP_QUALITY"}
        return {k: [float(x) for x in d[v]] for k, v in cols.items()}


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


EVENT_FIELDS = ["star", "kepid", "hypothesis", "own", "time", "pdc_ppm", "pdc_err", "pct", "z", "dip",
                "sap_ppm", "sap_err", "bkg_ppm", "bkg_err", "c1_mpix", "c1_err", "c2_mpix", "c2_err",
                "flag_cadences", "flag_bits"]


def star_rows(label, series, flag_t, flag_q):
    """(event rows, null summary) for one star at every hypothesis's events inside its data."""
    _, dur_h, _ = STARS[label]
    times = series["pdc"][0]
    if not times:
        return [], {"star": label, "null_n": 0}
    events = [(name, tc) for name, (p, t0) in HYPS.items() for tc in events_in(p, t0, times[0], times[-1])]
    nulls = []
    for t in null_times(times, [tc for _, tc in events]):
        r = deficit_ppm(box_fit(*series["pdc"], t, dur_h))
        if r is not None:
            nulls.append(r[0])
    sig = robust_sigma(nulls) if len(nulls) >= 10 else None
    rows = []
    for name, tc in events:
        row = {"star": label, "kepid": STARS[label][0], "hypothesis": name, "own": int(name == label),
               "time": round(tc, 4)}
        row.update(measure(series, tc, dur_h))
        n_flag, bits = flag_summary(flag_t, flag_q, tc)
        row["flag_cadences"], row["flag_bits"] = n_flag, bits
        if row["pdc_ppm"] != "" and nulls:
            pct = percentile_rank(row["pdc_ppm"], nulls)
            row["pct"] = round(pct, 3)
            row["z"] = round(row["pdc_ppm"] / sig, 2) if sig else ""
            row["dip"] = int(row["pdc_ppm"] > 0 and pct >= DIP_PCT)
        else:
            row["pct"] = row["z"] = row["dip"] = ""
        rows.append(row)
    summary = {"star": label, "dur_h": dur_h, "points": len(times), "span": [round(times[0], 3),
               round(times[-1], 3)], "null_n": len(nulls),
               "null_median_ppm": round(statistics.median(nulls), 1) if nulls else None,
               "null_sigma_ppm": round(sig, 1) if sig else None,
               "null_p95_ppm": round(sorted(nulls)[int(DIP_PCT * len(nulls))], 1) if nulls else None}
    return rows, summary


def pair_table(rows):
    """For each pair: its first member's events matched (within 1 d) to the second member's, with both dips."""
    own = {}
    for r in rows:
        if r["own"]:
            own.setdefault(r["star"], []).append(r)
    out = []
    for pair, a, b in PAIRS:
        for ra in own.get(a, []):
            rb = [r for r in own.get(b, []) if abs(r["time"] - ra["time"]) < 1.0]
            rb = rb[0] if rb else None
            out.append({"pair": pair, "time_a": ra["time"], "dip_a": ra["dip"], "pdc_a": ra["pdc_ppm"],
                        "time_b": "" if rb is None else rb["time"], "dip_b": "" if rb is None else rb["dip"],
                        "pdc_b": "" if rb is None else rb["pdc_ppm"]})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-dir", default="")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    cache = args.data_dir or tempfile.mkdtemp()
    rows, nulls, files = [], [], {}
    for label, (kepid, _, masks) in STARS.items():
        paths = lightcurve_files(kepid, cache)
        files[label] = [os.path.basename(p) for p in paths]
        series, flag_t, flag_q = build_series([read_quarter(p) for p in paths], masks)
        r, s = star_rows(label, series, flag_t, flag_q)
        rows += r
        nulls.append(s)
        print(json.dumps(s), flush=True)
    write_csv(os.path.join(args.out_dir, "events.csv"), rows, EVENT_FIELDS)
    pairs = pair_table(rows)
    write_csv(os.path.join(args.out_dir, "pairs.csv"), pairs,
              ["pair", "time_a", "dip_a", "pdc_a", "time_b", "dip_b", "pdc_b"])
    controls = [r for r in rows if not r["own"] and r["dip"] != ""]
    with open(os.path.abspath(__file__), "rb") as f:
        own_sha = hashlib.sha256(f.read()).hexdigest()
    stats = {"version": VERSION, "pair_events_sha256": own_sha,
             "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "stars": nulls, "files": files, "pairs": pairs,
             "control_events": len(controls), "control_dips": sum(r["dip"] for r in controls)}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)
    lines = [f"# pair-events {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY "
             "4.0. Leads to check by eye, not dispositions.", "",
             "## Pairs (own ephemerides; dip = PDCSAP deficit > 0 at or above the star's null 95th percentile)", "",
             "| pair | time A | dip A | PDC A (ppm) | time B | dip B | PDC B (ppm) |", "|---|---|---|---|---|---|---|"]
    lines += [f"| {p['pair']} | {p['time_a']} | {p['dip_a']} | {p['pdc_a']} | {p['time_b']} | {p['dip_b']} | "
              f"{p['pdc_b']} |" for p in pairs]
    lines += ["", f"Control events (a star at another ephemeris's dates): {stats['control_events']}, dips "
              f"{stats['control_dips']}", "", "## Null per star", "",
              "| star | dur (h) | points | null n | median | sigma | p95 (ppm) |", "|---|---|---|---|---|---|---|"]
    lines += [f"| {s['star']} | {s.get('dur_h')} | {s.get('points')} | {s['null_n']} | {s.get('null_median_ppm')} | "
              f"{s.get('null_sigma_ppm')} | {s.get('null_p95_ppm')} |" for s in nulls]
    lines += ["", "## Every event", "",
              "| star | hyp | own | time | PDC (ppm) | pct | z | dip | SAP (ppm) | BKG (ppm) | c1 (mpix) | c2 (mpix) "
              "| flags | bits |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {r['star']} | {r['hypothesis']} | {r['own']} | {r['time']} | {r['pdc_ppm']} +- {r['pdc_err']} | "
              f"{r['pct']} | {r['z']} | {r['dip']} | {r['sap_ppm']} +- {r['sap_err']} | {r['bkg_ppm']} +- "
              f"{r['bkg_err']} | {r['c1_mpix']} +- {r['c1_err']} | {r['c2_mpix']} +- {r['c2_err']} | "
              f"{r['flag_cadences']} | {r['flag_bits']} |" for r in rows]
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps({k: v for k, v in stats.items() if k != "files"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
