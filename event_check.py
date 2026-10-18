"""event_check: depths at the transit times each candidate period predicts on one Kepler star, which
periods two transits allow, and a blind single-event search.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library plus the published
kepler_alias 0.3.0 (light-curve download, quality-0 PDCSAP reader, box depth); astropy reads the FITS.

Written for KOI-1356.01 (KIC 7363829), where three catalogues agree only on the first transit (335.82
BKJD): Q1-Q16 and the Archive give 384.026 d, the DR25 TCE 393.719 d (3 transits, S/N 82, never
catalogued) and Lissauer et al. 2024 787.432 d. Pre-registration:
findings/2026-10-17-koi1356-events-prereg.md in munimtechnologies/exoplanet-archive-audit.

Method. One event's depth is kepler_alias.epoch_depths on a single epoch: the mean deficit of the
central 70 % of the duration below a straight line fitted to points 1 to 3 durations from the centre.
1. Coverage: each quarter's first and last quality-0 cadence, and every gap of 0.5 d or more.
2. Hypotheses (name=P@T0): every epoch inside the data span is measured. Status against the
   reference event (the first anchor), depth D_ref:
     deep     D >= 0.5 D_ref and D / err >= 7
     absent   D < 0.3 D_ref and (D_ref - D) / hypot(err, err_ref) >= 5
     no_data  too few points in the core or on either side
     unclear  otherwise
   A hypothesis is excluded if any epoch is absent, supported if at least two epochs have data and
   all of those are deep, untested if fewer than two have data, unclear otherwise.
3. Two-transit aliases: P = (T2 - T1) / n through the two anchors, n = 1..max-n, judged the same way.
4. Blind search: the box stepped every --step d over the whole light curve. S/N is also divided by
   1.4826 x the median |S/N| (a robust scale that absorbs red noise). The 25 highest-S/N dips at
   least 1 d apart are listed.
A verdict is a lead to check by eye, not a published correction.

Usage: python event_check.py --out-dir /out/K01356.01 --data-dir /data --kepid 7363829 --dur-h 13.5
         --hypotheses "Q1-Q16=384.02570682@335.816169,..." --anchors 335.817,1123.255 [--max-n 12]
"""
import argparse
import bisect
import csv
import datetime as dt
import hashlib
import json
import math
import os
import statistics
import sys
import tempfile

sys.path.insert(0, os.environ.get("KEPLER_ALIAS_DIR", "/out/tool"))
import kepler_alias as ka  # noqa: E402  the published copy, fetched by fetch_tool.py

VERSION = "0.1.0"
SINGLE = 1e7  # a period longer than the mission, so epoch_depths measures one epoch
DEEP_FRAC, ABSENT_FRAC = 0.5, 0.3
SIG_DEEP, SIG_ABSENT = 7.0, 5.0
MIN_GAP = 0.5
CUTOUT = 2.0


def parse_hypotheses(text):
    """'a=1.5@2,b=3@4.5' -> [('a', 1.5, 2.0), ('b', 3.0, 4.5)]"""
    out = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        name, rest = part.split("=", 1)
        p, t0 = rest.split("@", 1)
        out.append((name.strip(), float(p), float(t0)))
    return out


def one_event(times, fluxes, tc, dur_h):
    """(depth, err, n_in, n_out) of one event centred at tc, or None if there are too few points."""
    rows = ka.epoch_depths(times, fluxes, SINGLE, tc, dur_h)
    if not rows:
        return None
    _, d, e, a, b = rows[0]
    return d, e, a, b


def core_points(times, tc, dur_h):
    """Cadences strictly inside the central 70 % of the duration."""
    half = 0.35 * dur_h / 24.0
    return max(0, bisect.bisect_left(times, tc + half) - bisect.bisect_right(times, tc - half))


def best_centre(times, fluxes, tc, dur_h, span=0.5, step=0.01):
    """(centre, depth, err) with the highest S/N within tc +- span, or None."""
    best = None
    n = int(round(span / step))
    for i in range(-n, n + 1):
        t = tc + i * step
        ev = one_event(times, fluxes, t, dur_h)
        if ev and (best is None or ev[0] / ev[1] > best[1] / best[2]):
            best = (t, ev[0], ev[1])
    return best


def status(ev, ref):
    """deep / absent / no_data / unclear for ev = (depth, err, ...) against the reference event."""
    if ev is None:
        return "no_data"
    if ref is None or ref[0] <= 0:
        return "unclear"
    d, e = ev[0], ev[1]
    if d >= DEEP_FRAC * ref[0] and d / e >= SIG_DEEP:
        return "deep"
    if d < ABSENT_FRAC * ref[0] and (ref[0] - d) / math.hypot(e, ref[1]) >= SIG_ABSENT:
        return "absent"
    return "unclear"


def judge(statuses):
    if "absent" in statuses:
        return "excluded"
    with_data = [s for s in statuses if s != "no_data"]
    if len(with_data) < 2:
        return "untested"
    return "supported" if all(s == "deep" for s in with_data) else "unclear"


def epochs_in(p, t0, t_first, t_last):
    """Epoch numbers n with t0 + n p inside [t_first, t_last]."""
    return list(range(math.ceil((t_first - t0) / p), math.floor((t_last - t0) / p) + 1))


def check_hypothesis(times, fluxes, name, p, t0, dur_h, ref, refine=False):
    """(rows, verdict) for one period hypothesis."""
    rows = []
    for n in epochs_in(p, t0, times[0], times[-1]):
        tc = t0 + n * p
        ev = one_event(times, fluxes, tc, dur_h)
        row = {"hypothesis": name, "period": p, "epoch": n, "time": round(tc, 4),
               "core_points": core_points(times, tc, dur_h),
               "depth_ppm": "" if ev is None else round(ev[0] * 1e6, 1),
               "err_ppm": "" if ev is None else round(ev[1] * 1e6, 1),
               "snr": "" if ev is None else round(ev[0] / ev[1], 2),
               "status": status(ev, ref), "best_centre": "", "best_depth_ppm": "", "best_snr": ""}
        if refine and ev is not None:
            b = best_centre(times, fluxes, tc, dur_h)
            if b:
                row.update({"best_centre": round(b[0], 3), "best_depth_ppm": round(b[1] * 1e6, 1),
                            "best_snr": round(b[1] / b[2], 2)})
        rows.append(row)
    return rows, judge([r["status"] for r in rows])


def dip_search(times, fluxes, dur_h, step=0.05, keep=25, sep=1.0):
    """(the keep highest-S/N dips at least sep days apart, robust S/N scale)."""
    grid = []
    i = 0
    while times and times[0] + i * step <= times[-1]:
        t = times[0] + i * step
        ev = one_event(times, fluxes, t, dur_h)
        if ev:
            grid.append((ev[0] / ev[1], t, ev[0], ev[1]))
        i += 1
    if not grid:
        return [], None
    scale = 1.4826 * statistics.median(abs(s) for s, _, _, _ in grid)
    picked = []
    for s, t, d, e in sorted(grid, reverse=True):
        if len(picked) >= keep:
            break
        if all(abs(t - q[1]) >= sep for q in picked):
            picked.append((s, t, d, e))
    return [{"rank": i + 1, "time": round(t, 3), "depth_ppm": round(d * 1e6, 1), "err_ppm": round(e * 1e6, 1),
             "snr": round(s, 2), "snr_robust": round(s / scale, 2) if scale else ""}
            for i, (s, t, d, e) in enumerate(picked)], scale


def gaps(times, min_gap=MIN_GAP):
    """[(last time before, first time after, length)] for every gap of at least min_gap days."""
    return [(a, b, b - a) for a, b in zip(times, times[1:]) if b - a >= min_gap]


def quarter_of(path):
    try:
        from astropy.io import fits
        return fits.getheader(path, 0).get("QUARTER", "")
    except Exception:  # the label is a convenience; the times are what count
        return ""


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


HYP_FIELDS = ["hypothesis", "period", "epoch", "time", "core_points", "depth_ppm", "err_ppm", "snr", "status",
              "best_centre", "best_depth_ppm", "best_snr"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-dir", default="")
    ap.add_argument("--kepid", type=int, required=True)
    ap.add_argument("--dur-h", type=float, required=True)
    ap.add_argument("--hypotheses", required=True)
    ap.add_argument("--anchors", required=True)
    ap.add_argument("--max-n", type=int, default=12)
    ap.add_argument("--step", type=float, default=0.05)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    cache = args.data_dir or tempfile.mkdtemp()

    coverage, pts = [], []
    for path in ka.lightcurve_files(args.kepid, cache):
        q = ka.read_llc(path)
        ts = [t for t, _ in q]
        coverage.append({"file": os.path.basename(path), "quarter": quarter_of(path), "points": len(q),
                         "first": round(min(ts), 4) if ts else "", "last": round(max(ts), 4) if ts else ""})
        pts.extend(q)
    pts.sort()
    times, fluxes = [t for t, _ in pts], [f for _, f in pts]
    write_csv(os.path.join(args.out_dir, "coverage.csv"), coverage, ["file", "quarter", "points", "first", "last"])
    gap_rows = [{"before": round(a, 4), "after": round(b, 4), "days": round(g, 3)} for a, b, g in gaps(times)]
    write_csv(os.path.join(args.out_dir, "gaps.csv"), gap_rows, ["before", "after", "days"])

    t1, t2 = (float(x) for x in args.anchors.split(","))
    ref = one_event(times, fluxes, t1, args.dur_h)
    anchors = [{"time": t, "event": one_event(times, fluxes, t, args.dur_h),
                "best": best_centre(times, fluxes, t, args.dur_h)} for t in (t1, t2)]

    named, verdicts = [], {}
    for name, p, t0 in parse_hypotheses(args.hypotheses):
        rows, v = check_hypothesis(times, fluxes, name, p, t0, args.dur_h, ref, refine=True)
        named += rows
        verdicts[name] = v
    write_csv(os.path.join(args.out_dir, "hypotheses.csv"), named, HYP_FIELDS)

    alias_rows, alias_verdicts = [], {}
    for n in range(1, args.max_n + 1):
        p = (t2 - t1) / n
        rows, v = check_hypothesis(times, fluxes, f"two-transit n={n}", p, t1, args.dur_h, ref)
        alias_rows += rows
        alias_verdicts[n] = {"period": round(p, 4), "verdict": v,
                             "statuses": "".join(r["status"][0] for r in rows)}
    write_csv(os.path.join(args.out_dir, "aliases.csv"), alias_rows, HYP_FIELDS)

    dips, scale = dip_search(times, fluxes, args.dur_h, args.step)
    write_csv(os.path.join(args.out_dir, "dips.csv"), dips, ["rank", "time", "depth_ppm", "err_ppm", "snr", "snr_robust"])

    cut_times = sorted({r["time"] for r in named} | {t1, t2})
    cutouts = []
    for tc in cut_times:
        i, j = bisect.bisect_left(times, tc - CUTOUT), bisect.bisect_right(times, tc + CUTOUT)
        cutouts += [{"event": tc, "bkjd": round(times[q], 5), "flux": round(fluxes[q], 7)} for q in range(i, j)]
    write_csv(os.path.join(args.out_dir, "cutouts.csv"), cutouts, ["event", "bkjd", "flux"])

    def ev_dict(ev):
        return None if ev is None else {"depth_ppm": round(ev[0] * 1e6, 1), "err_ppm": round(ev[1] * 1e6, 1),
                                        "snr": round(ev[0] / ev[1], 2), "n_in": ev[2], "n_out": ev[3]}

    best = [a["best"] for a in anchors]
    with open(os.path.abspath(__file__), "rb") as f:
        own_sha = hashlib.sha256(f.read()).hexdigest()
    stats = {
        "version": VERSION, "kepler_alias_version": ka.VERSION, "event_check_sha256": own_sha,
        "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "kepid": args.kepid, "dur_h": args.dur_h, "points": len(times),
        "span": [round(times[0], 4), round(times[-1], 4)] if times else None,
        "quarters": len(coverage), "gaps_over_0.5d": len(gap_rows),
        "anchors": [{"time": a["time"], "event": ev_dict(a["event"]),
                     "best_centre": None if a["best"] is None else round(a["best"][0], 3)} for a in anchors],
        "two_transit_period_from_best_centres": (round(best[1][0] - best[0][0], 3)
                                                 if best[0] and best[1] else None),
        "hypotheses": verdicts, "aliases": alias_verdicts,
        "dip_scale": None if scale is None else round(scale, 3), "top_dips": dips[:5],
    }
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

    lines = [f"# event-check {VERSION}: KIC {args.kepid}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0. "
             "A verdict is a lead to check by eye, not a published correction.", "",
             f"- points: {len(times)}; quarters: {len(coverage)}; span: {stats['span']}; duration used: {args.dur_h} h",
             f"- reference (first anchor): {ev_dict(ref)}",
             f"- anchors: {stats['anchors']}",
             f"- two-transit period from best centres: {stats['two_transit_period_from_best_centres']}", "",
             "## Hypotheses", "", "| hypothesis | verdict |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in verdicts.items()]
    lines += ["", "| hypothesis | n | time | core pts | depth (ppm) | S/N | status | best centre | best S/N |",
              "|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {r['hypothesis']} | {r['epoch']} | {r['time']} | {r['core_points']} | {r['depth_ppm']} +- "
              f"{r['err_ppm']} | {r['snr']} | {r['status']} | {r['best_centre']} | {r['best_snr']} |" for r in named]
    lines += ["", "## Two-transit aliases (statuses per epoch: d deep, a absent, n no data, u unclear)", "",
              "| n | P (d) | verdict | epochs |", "|---|---|---|---|"]
    lines += [f"| {n} | {v['period']} | {v['verdict']} | {v['statuses']} |" for n, v in alias_verdicts.items()]
    lines += ["", f"## Blind search (robust S/N scale {stats['dip_scale']})", "",
              "| rank | time | depth (ppm) | S/N | robust S/N |", "|---|---|---|---|---|"]
    lines += [f"| {d['rank']} | {d['time']} | {d['depth_ppm']} +- {d['err_ppm']} | {d['snr']} | {d['snr_robust']} |"
              for d in dips]
    lines += ["", "## Coverage", "", "| file | quarter | points | first | last |", "|---|---|---|---|---|"]
    lines += [f"| {c['file']} | {c['quarter']} | {c['points']} | {c['first']} | {c['last']} |" for c in coverage]
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
