"""thirds_lc: light-curve depth of each group of a Kepler candidate's events (epoch mod k), for named
ephemerides and durations, judged by kepler_alias's own verdict rule.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library plus the published
kepler_alias 0.3.0 (light-curve download, quality-0 PDCSAP reader, per-epoch box depth, group statistics,
verdict); astropy reads the FITS.

Written for KOI-5600.01 (KIC 9018021). The Archive's default period is DR25's 17.168 d (13.04 h); DR24 and
Lissauer et al. 2024 give 51.51 and 51.50 d (DR24: 4.66 h, 310.7 ppm). The pixel test koi5600-thirds-v1
was inconclusive (findings/2026-10-18-koi5600-thirds-results.md). Pre-registration of this test:
findings/2026-10-18-koi5600-lightcurve-prereg.md in munimtechnologies/exoplanet-archive-audit.

Method. Each run is name=P@T0/duration_h. kepler_alias.epoch_depths measures every epoch of (P, T0): the
mean deficit of the central 70 % of the duration below a straight line fitted to points 1 to 3 durations
from the centre. kepler_alias.group_stats combines the epochs of each group n mod k (error scaled up by
sqrt(reduced chi2) when above 1). kepler_alias.verdict judges them, with --long-group as the group that
holds the long period's phase:
  long_period_real   that group >= 5 sigma, every other group within 3 sigma of zero;
  short_period_real  every group >= 5 sigma and all pairs agree within 3 sigma;
  inconclusive       otherwise.
The same groups are also given for the first and second half of the epochs, with the contrast of the long
group over the mean of the others (error from the group errors). The outcome combines the run named by
--primary (wide window, fits either period) and, if given, the run named by --secondary:
  "long"         one of them long_period_real and neither short_period_real;
  "short"        primary short_period_real and secondary not long_period_real;
  "conflict"     one long_period_real and the other short_period_real;
  "inconclusive" otherwise.
A verdict is a lead to check by eye, not a published correction.

Usage: python thirds_lc.py --out-dir /out/K05600.01 --data-dir /data --kepid 9018021 --k 3 --long-group 2
         --runs "A=17.168095@134.51121/13.04,N=17.168095@143.0952575/13.04" --primary A [--secondary B]
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import sys
import tempfile

sys.path.insert(0, os.environ.get("KEPLER_ALIAS_DIR", "/out/tool"))
import kepler_alias as ka  # noqa: E402  the published copy, fetched by fetch_tool.py

VERSION = "0.1.0"


def parse_runs(text):
    """'A=17.1@134.5/13.04, B=...' -> [('A', 17.1, 134.5, 13.04), ...]"""
    out = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        name, rest = part.split("=", 1)
        p, rest = rest.split("@", 1)
        t0, dur = rest.split("/", 1)
        out.append((name.strip(), float(p), float(t0), float(dur)))
    return out


def run_groups(times, fluxes, p, t0, dur_h, k, long_group, mask=None):
    """(epochs, groups, verdict, (first-half groups, second-half groups)) for one ephemeris."""
    epochs = ka.epoch_depths(times, fluxes, p, t0, dur_h, mask)
    groups = ka.group_stats(epochs, k)
    return epochs, groups, ka.verdict(groups, long_group), ka.split_halves(epochs, k)


def contrast(groups, long_group):
    """Depth of the long group minus the mean depth of the others, with its error, or None if a group is empty."""
    lg = groups[long_group]
    others = [g for g in groups if g["group"] != long_group]
    if not others or lg["epochs"] == 0 or any(g["epochs"] == 0 for g in others):
        return None
    m = sum(g["depth"] for g in others) / len(others)
    err = math.sqrt(lg["err"] ** 2 + sum(g["err"] ** 2 for g in others) / len(others) ** 2)
    return {"contrast_ppm": round((lg["depth"] - m) * 1e6, 1), "err_ppm": round(err * 1e6, 1),
            "snr": round((lg["depth"] - m) / err, 2), "others_mean_ppm": round(m * 1e6, 1)}


def outcome(primary, secondary="inconclusive"):
    """Combined outcome of the primary (wide) and secondary runs' verdicts."""
    both = {primary, secondary}
    if both == {"long_period_real", "short_period_real"}:
        return "conflict"
    if "long_period_real" in both:
        return "long"
    if primary == "short_period_real":
        return "short"
    return "inconclusive"


def group_dicts(groups):
    def r(x, scale=1.0, nd=1):
        return None if x is None else round(x * scale, nd)
    return [{"group": g["group"], "epochs": g["epochs"], "depth_ppm": r(g["depth"], 1e6),
             "err_ppm": r(g["err"], 1e6), "snr": r(g["snr"], 1.0, 2)} for g in groups]


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-dir", default="")
    ap.add_argument("--kepid", type=int, required=True)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--long-group", type=int, required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--primary", required=True)
    ap.add_argument("--secondary", default="")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    cache = args.data_dir or tempfile.mkdtemp()

    coverage, pts = [], []
    for path in ka.lightcurve_files(args.kepid, cache):
        q = ka.read_llc(path)
        coverage.append({"file": os.path.basename(path), "points": len(q),
                         "first": round(q[0][0], 4) if q else "", "last": round(q[-1][0], 4) if q else ""})
        pts.extend(q)
    pts.sort()
    times, fluxes = [t for t, _ in pts], [f for _, f in pts]
    write_csv(os.path.join(args.out_dir, "coverage.csv"), coverage, ["file", "points", "first", "last"])

    runs, epoch_rows = {}, []
    for name, p, t0, dur_h in parse_runs(args.runs):
        epochs, groups, v, (first, second) = run_groups(times, fluxes, p, t0, dur_h, args.k, args.long_group)
        runs[name] = {"period": p, "t0_bkjd": t0, "dur_h": dur_h, "verdict": v,
                      "contrast": contrast(groups, args.long_group), "groups": group_dicts(groups),
                      "first_half": group_dicts(first), "second_half": group_dicts(second),
                      "contrast_first_half": contrast(first, args.long_group),
                      "contrast_second_half": contrast(second, args.long_group)}
        epoch_rows += [{"run": name, "epoch": n, "group": n % args.k, "time": round(t0 + n * p, 4),
                        "depth_ppm": round(d * 1e6, 1), "err_ppm": round(e * 1e6, 1), "snr": round(d / e, 2),
                        "n_in": a, "n_out": b} for n, d, e, a, b in epochs]
    write_csv(os.path.join(args.out_dir, "epochs.csv"), epoch_rows,
              ["run", "epoch", "group", "time", "depth_ppm", "err_ppm", "snr", "n_in", "n_out"])

    with open(os.path.abspath(__file__), "rb") as f:
        own_sha = hashlib.sha256(f.read()).hexdigest()
    stats = {
        "version": VERSION, "kepler_alias_version": ka.VERSION, "thirds_lc_sha256": own_sha,
        "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "kepid": args.kepid, "k": args.k, "long_group": args.long_group, "points": len(times),
        "span": [round(times[0], 4), round(times[-1], 4)] if times else None, "files": len(coverage),
        "runs": runs, "primary": args.primary, "secondary": args.secondary,
        "outcome": outcome(runs[args.primary]["verdict"],
                           runs[args.secondary]["verdict"] if args.secondary else "inconclusive"),
    }
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

    lines = [f"# thirds-lc {VERSION}: KIC {args.kepid}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0. "
             "A verdict is a lead to check by eye, not a published correction.", "",
             f"- points: {len(times)}; files: {len(coverage)}; span: {stats['span']}; k = {args.k}; "
             f"long group = {args.long_group}",
             f"- outcome (primary {args.primary}, secondary {args.secondary or 'none'}): **{stats['outcome']}**", ""]
    lines += [f"- contrast of group {args.long_group} over the others, run {name}: all {r['contrast']}; "
              f"first half {r['contrast_first_half']}; second half {r['contrast_second_half']}"
              for name, r in runs.items()]
    lines += ["", "| run | P (d) | T0 (BKJD) | duration (h) | part | group | epochs | depth (ppm) | S/N | verdict |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in runs.items():
        for part in ("groups", "first_half", "second_half"):
            for g in r[part]:
                lines.append(f"| {name} | {r['period']} | {r['t0_bkjd']} | {r['dur_h']} | {part} | {g['group']} | "
                             f"{g['epochs']} | {g['depth_ppm']} +- {g['err_ppm']} | {g['snr']} | "
                             f"{r['verdict'] if part == 'groups' else ''} |")
    lines += ["", "## Coverage", "", "| file | points | first | last |", "|---|---|---|---|"]
    lines += [f"| {c['file']} | {c['points']} | {c['first']} | {c['last']} |" for c in coverage]
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
