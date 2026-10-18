"""ttv_times: trapezoid mid-times for the five KOI-1209.01 transits from the published event_check cutouts,
a weighted linear-ephemeris fit with O-C, and the Holczer et al. 2016 (ApJS 225, 9) table rows for KOI 1209.01.

MV2 of Munim, Inc. Made with AI agents working in his name. Apache-2.0. Standard library only.
Pre-registration: findings/2026-10-18-koi1209-times-prereg.md in munimtechnologies/exoplanet-archive-audit.

Model per event (pure Python, no numpy): flux = a + b (t - tc) - c s(t), where s is a trapezoid of total
duration t14 (first to fourth contact) with ingress fraction frac (0.5 = V shape). For each (tc, t14, frac) on
a grid the three linear coefficients are solved by least squares; the best grid point is kept. Noise sigma is
set from the best fit's residuals (reduced chi-square 1), and the 1-sigma interval on tc is where the profile
(minimum over t14 and frac) rises by one. Depth = c / a.

Usage: python ttv_times.py --out-dir /out [--cutouts <file or URL>] [--events 378.17,650.23,...] [--no-holczer]
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import re
import sys
import urllib.request

VERSION = "0.1.0"
UA = f"ttv-times/{VERSION} (Munim, Inc.; mv2@munimtech.com)"
CUTOUTS_URL = ("https://raw.githubusercontent.com/munimtechnologies/exoplanet-archive-audit/main/"
               "results/2026-10-18-koi1209-events-0.1.0/cutouts.csv")
HOLCZER = {
    "t2": "https://content.cld.iop.org/journals/0067-0049/225/1/9/revision1/apjsaa25b0t2_mrt.txt",
    "t3": "https://content.cld.iop.org/journals/0067-0049/225/1/9/revision1/apjsaa25b0t3_mrt.txt",
}
HOLCZER_KOI = "1209.01"
BJD_OFFSET = 67.0          # Holczer times are BJD - 2454900; BKJD = BJD - 2454833
DEFAULT_EVENTS = [378.17, 650.23, 922.51, 1194.96, 1466.47]
WINDOW = 1.0               # days either side of the guess used in the fit
SPAN = 0.3                 # tc search half-range (days)
STEP = 0.002               # tc grid step (days)
T14_HOURS = (2.0, 5.0, 0.2)
FRACS = (0.2, 0.5)
P_GUESS = 272.1


def fetch(url, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def read_cutouts(src):
    """Rows (event_key, bkjd, flux) from a local cutouts.csv path or a URL."""
    if re.match(r"^https?://", src):
        text = fetch(src).decode("utf-8", "replace")
    else:
        with open(src, encoding="utf-8") as f:
            text = f.read()
    rows = []
    for rec in csv.DictReader(io.StringIO(text)):
        try:
            rows.append((rec["event"], float(rec["bkjd"]), float(rec["flux"])))
        except (KeyError, ValueError):
            continue
    return rows


def collect_window(rows, guess, window=WINDOW):
    """Unique (bkjd, flux) points within +-window of guess, from every event key, sorted by time."""
    seen = {}
    for _key, t, f in rows:
        if abs(t - guess) <= window:
            seen.setdefault(round(t, 5), f)
    pts = sorted(seen.items())
    return [p[0] for p in pts], [p[1] for p in pts]


def trapezoid(t, tc, t14, frac):
    """Dimming shape: 1 at full depth, 0 outside; ingress and egress each last frac * t14."""
    x = abs(t - tc)
    half = t14 / 2.0
    if x >= half:
        return 0.0
    tau = frac * t14
    if tau <= 0:
        return 1.0
    flat = half - tau
    if x <= flat:
        return 1.0
    return (half - x) / tau


def solve3(A, b):
    """Solve a 3x3 linear system by Gaussian elimination with partial pivoting; None if singular."""
    M = [list(A[i]) + [b[i]] for i in range(3)]
    for c in range(3):
        p = max(range(c, 3), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-300:
            return None
        M[c], M[p] = M[p], M[c]
        for r in range(3):
            if r != c:
                f = M[r][c] / M[c][c]
                for k in range(c, 4):
                    M[r][k] -= f * M[c][k]
    return [M[i][3] / M[i][i] for i in range(3)]


def fit_shape(times, fluxes, tc, t14, frac):
    """Least squares of flux ~ a + b (t - tc) - c s(t). Returns dict or None (no in-transit points)."""
    cols = [(1.0, t - tc, -trapezoid(t, tc, t14, frac)) for t in times]
    if all(x[2] == 0.0 for x in cols):
        return None
    A = [[0.0] * 3 for _ in range(3)]
    bb = [0.0] * 3
    for xs, f in zip(cols, fluxes):
        for i in range(3):
            bb[i] += xs[i] * f
            for j in range(3):
                A[i][j] += xs[i] * xs[j]
    sol = solve3(A, bb)
    if sol is None:
        return None
    a, b, c = sol
    ss = 0.0
    for xs, f in zip(cols, fluxes):
        ss += (f - (a * xs[0] + b * xs[1] + c * xs[2])) ** 2
    inv_col = solve3(A, [0.0, 0.0, 1.0])
    var_c_unit = inv_col[2] if inv_col else float("nan")
    return {"ss": ss, "a": a, "b": b, "c": c, "var_c_unit": var_c_unit}


def fit_event(times, fluxes, guess, span=SPAN, step=STEP, t14_hours=T14_HOURS, fracs=FRACS):
    """Grid fit; returns dict with tc, tc_lo, tc_hi, tc_err, depth_ppm, depth_err_ppm, t14_h, frac, sigma, n."""
    n = len(times)
    if n < 10:
        return None
    t14_grid = []
    h = t14_hours[0]
    while h <= t14_hours[1] + 1e-9:
        t14_grid.append(h / 24.0)
        h += t14_hours[2]
    ntc = int(round(2 * span / step)) + 1
    profile = []   # (tc, best ss at this tc, best fit at this tc)
    for i in range(ntc):
        tc = guess - span + i * step
        best = None
        for t14 in t14_grid:
            for frac in fracs:
                r = fit_shape(times, fluxes, tc, t14, frac)
                if r is None:
                    continue
                if best is None or r["ss"] < best[0]["ss"]:
                    best = (r, t14, frac)
        if best is not None:
            profile.append((tc, best[0]["ss"], best))
    if not profile:
        return None
    tc_best, ss_best, (fit, t14, frac) = min(profile, key=lambda p: p[1])
    dof = max(n - 3, 1)
    sigma = math.sqrt(ss_best / dof)
    var_unit = sigma ** 2
    # 1-sigma interval: contiguous region around the best tc where delta chi2 <= 1
    idx = [k for k, p in enumerate(profile) if p[0] == tc_best][0]
    lo = idx
    while lo - 1 >= 0 and (profile[lo - 1][1] - ss_best) / var_unit <= 1.0:
        lo -= 1
    hi = idx
    while hi + 1 < len(profile) and (profile[hi + 1][1] - ss_best) / var_unit <= 1.0:
        hi += 1
    tc_lo, tc_hi = profile[lo][0], profile[hi][0]
    at_edge = lo == 0 or hi == len(profile) - 1
    tc_err = max((tc_hi - tc_lo) / 2.0, step / 2.0)
    a = fit["a"]
    depth = fit["c"] / a if a else float("nan")
    depth_err = math.sqrt(max(fit["var_c_unit"], 0.0) * var_unit) / abs(a) if a else float("nan")
    return {"guess": guess, "tc": round(tc_best, 4), "tc_lo": round(tc_lo, 4), "tc_hi": round(tc_hi, 4),
            "tc_err": round(tc_err, 4), "at_edge": at_edge, "depth_ppm": round(depth * 1e6, 1),
            "depth_err_ppm": round(depth_err * 1e6, 1), "t14_h": round(t14 * 24, 2), "frac": frac,
            "sigma_ppm": round(sigma * 1e6, 1), "n": n,
            "n_in": sum(1 for t in times if trapezoid(t, tc_best, t14, frac) > 0)}


def linear_fit(times, errs, p_guess=P_GUESS):
    """Weighted linear ephemeris t = T0 + P n. Epoch numbers from the first time and p_guess."""
    if len(times) < 2:
        return None
    t0 = times[0]
    ns = [int(round((t - t0) / p_guess)) for t in times]
    ws = [1.0 / (e * e) if e and e > 0 else 1.0 for e in errs]
    Sw = sum(ws)
    Sn = sum(w * n for w, n in zip(ws, ns))
    St = sum(w * t for w, t in zip(ws, times))
    Snn = sum(w * n * n for w, n in zip(ws, ns))
    Snt = sum(w * n * t for w, n, t in zip(ws, ns, times))
    D = Sw * Snn - Sn * Sn
    if D == 0:
        return None
    P = (Sw * Snt - Sn * St) / D
    T0 = (Snn * St - Sn * Snt) / D
    oc = [t - (T0 + P * n) for t, n in zip(times, ns)]
    chi2 = sum(w * r * r for w, r in zip(ws, oc))
    return {"P": P, "T0": T0, "P_err": math.sqrt(Sw / D), "T0_err": math.sqrt(Snn / D), "n": ns,
            "oc": oc, "chi2": chi2, "dof": len(times) - 2,
            "max_abs_oc": max(abs(r) for r in oc),
            "max_abs_oc_sigma": max(abs(r) / e if e and e > 0 else 0.0 for r, e in zip(oc, errs))}


def parse_bbb(text):
    """Column specs (start, end, format, units, label) from a CDS byte-by-byte header."""
    specs = []
    pat = re.compile(r"^\s*(\d+)(?:\s*-\s*(\d+))?\s+([AIFE]\d+(?:\.\d+)?)\s+(\S+)\s+(\S+)")
    for line in text.splitlines():
        m = pat.match(line)
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else start
            specs.append((start, end, m.group(3), m.group(4), m.group(5)))
    return specs


def slice_row(line, specs):
    return {label: line[start - 1:end].strip() for start, end, _fmt, _units, label in specs}


def extract_koi(text, koi):
    """Lines of a CDS table whose first whitespace token equals koi."""
    out = []
    for line in text.splitlines():
        toks = line.split()
        if toks and toks[0] == koi:
            out.append(line)
    return out


def header_block(text):
    """Everything up to and including the last dashed line (the CDS header)."""
    lines = text.splitlines()
    last = -1
    for i, line in enumerate(lines):
        if re.match(r"^-{10,}\s*$", line):
            last = i
    return "\n".join(lines[:last + 1]) if last >= 0 else ""


def holczer(out_dir, koi=HOLCZER_KOI, our_tcs=None):
    res = {}
    for key, url in HOLCZER.items():
        try:
            raw = fetch(url)
        except Exception as exc:  # noqa: BLE001 - record and go on
            res[key] = {"url": url, "error": repr(exc)}
            continue
        text = raw.decode("utf-8", "replace")
        specs = parse_bbb(header_block(text))
        lines = extract_koi(text, koi)
        rows = [slice_row(l, specs) for l in lines] if specs else []
        with open(os.path.join(out_dir, f"holczer_{key}_header.txt"), "w", encoding="utf-8") as f:
            f.write(header_block(text))
        with open(os.path.join(out_dir, f"holczer_{key}_{koi}.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        if rows:
            with open(os.path.join(out_dir, f"holczer_{key}_{koi}.csv"), "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=[s[4] for s in specs])
                w.writeheader()
                w.writerows(rows)
        res[key] = {"url": url, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                    "columns": [s[4] for s in specs], "units": [s[3] for s in specs],
                    "rows_for_koi": len(lines), "rows": rows}
    # direct comparison where a column holds a mid-time (BJD - 2454900) near one of our centres
    compare = []
    if our_tcs and res.get("t3", {}).get("rows"):
        for row in res["t3"]["rows"]:
            for label, val in row.items():
                try:
                    v = float(val)
                except ValueError:
                    continue
                t = v + BJD_OFFSET
                for tc in our_tcs:
                    if abs(t - tc) <= 0.5:
                        compare.append({"column": label, "holczer_bkjd": round(t, 4), "our_tc": tc,
                                        "diff_d": round(tc - t, 4)})
    res["compare"] = compare
    with open(os.path.join(out_dir, "holczer_compare.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["column", "holczer_bkjd", "our_tc", "diff_d"])
        w.writeheader()
        w.writerows(compare)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--cutouts", default=CUTOUTS_URL)
    ap.add_argument("--events", default=",".join(str(e) for e in DEFAULT_EVENTS))
    ap.add_argument("--no-holczer", action="store_true")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    rows = read_cutouts(args.cutouts)
    guesses = [float(x) for x in args.events.split(",") if x.strip()]
    fits = []
    for g in guesses:
        times, fluxes = collect_window(rows, g)
        r = fit_event(times, fluxes, g)
        if r is None:
            r = {"guess": g, "tc": None, "n": len(times)}
        fits.append(r)
        print(json.dumps(r), file=sys.stderr)
    good = [r for r in fits if r.get("tc") is not None]
    lin = linear_fit([r["tc"] for r in good], [r["tc_err"] for r in good]) if len(good) >= 2 else None
    lin_unw = linear_fit([r["tc"] for r in good], [1.0] * len(good)) if len(good) >= 2 else None
    with open(os.path.join(args.out_dir, "times.csv"), "w", newline="", encoding="utf-8") as f:
        fields = ["guess", "tc", "tc_lo", "tc_hi", "tc_err", "at_edge", "depth_ppm", "depth_err_ppm", "t14_h",
                  "frac", "sigma_ppm", "n", "n_in", "epoch", "oc_weighted_d", "oc_unweighted_d"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        k = 0
        for r in fits:
            row = {key: r.get(key, "") for key in fields}
            if r.get("tc") is not None and lin:
                row["epoch"] = lin["n"][k]
                row["oc_weighted_d"] = round(lin["oc"][k], 4)
                row["oc_unweighted_d"] = round(lin_unw["oc"][k], 4)
                k += 1
            w.writerow(row)
    hol = None if args.no_holczer else holczer(args.out_dir, our_tcs=[r["tc"] for r in good])
    summary = {"version": VERSION, "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
               "cutouts": args.cutouts, "cutout_rows": len(rows), "fits": fits,
               "linear_weighted": lin, "linear_unweighted": lin_unw,
               "holczer": None if hol is None else {k: ({kk: vv for kk, vv in v.items() if kk != "rows"}
                                                        if isinstance(v, dict) else v) for k, v in hol.items()}}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    lines = [f"# ttv_times {VERSION}: KOI-1209.01 mid-times", "",
             f"Run {summary['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0.", "",
             "| guess | tc | 1-sigma | depth (ppm) | T14 (h) | frac | n (in) | O-C weighted (d) | O-C unweighted (d) |",
             "|---|---|---|---|---|---|---|---|---|"]
    k = 0
    for r in fits:
        if r.get("tc") is None:
            lines.append(f"| {r['guess']} | no fit | | | | | {r['n']} | | |")
            continue
        lines.append(f"| {r['guess']} | {r['tc']} | {r['tc_lo']}-{r['tc_hi']}{' (edge)' if r['at_edge'] else ''} | "
                     f"{r['depth_ppm']} +- {r['depth_err_ppm']} | {r['t14_h']} | {r['frac']} | {r['n']} ({r['n_in']}) | "
                     f"{round(lin['oc'][k], 4) if lin else ''} | {round(lin_unw['oc'][k], 4) if lin_unw else ''} |")
        k += 1
    if lin:
        lines += ["", f"Weighted linear fit: P = {lin['P']:.5f} +- {lin['P_err']:.5f} d, T0 = {lin['T0']:.4f} +- {lin['T0_err']:.4f} BKJD, "
                  f"chi2 = {lin['chi2']:.1f} for {lin['dof']} dof, max |O-C| = {lin['max_abs_oc']:.3f} d ({lin['max_abs_oc_sigma']:.1f} sigma).",
                  f"Unweighted linear fit: P = {lin_unw['P']:.5f} d, T0 = {lin_unw['T0']:.4f} BKJD, max |O-C| = {lin_unw['max_abs_oc']:.3f} d."]
    if hol:
        lines += ["", "## Holczer et al. 2016 rows for KOI " + HOLCZER_KOI, ""]
        for key in ("t2", "t3"):
            h = hol.get(key, {})
            if "error" in h:
                lines.append(f"- {key}: fetch failed: {h['error']}")
            else:
                lines.append(f"- {key}: {h['bytes']} bytes, sha256 {h['sha256'][:12]}..., {h['rows_for_koi']} rows for the KOI; columns {h['columns']}")
                for row in h.get("rows", []):
                    lines.append("  - " + ", ".join(f"{a}={b}" for a, b in row.items()))
        lines.append("")
        lines.append(f"Direct time matches (column value + {BJD_OFFSET} within 0.5 d of one of our centres): {len(hol['compare'])}")
        for c in hol["compare"]:
            lines.append(f"- {c['column']}: Holczer {c['holczer_bkjd']} vs ours {c['our_tc']} (ours - theirs = {c['diff_d']} d)")
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "fits"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
