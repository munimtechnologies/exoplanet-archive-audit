"""season_check: do the 371-day Kepler candidates K05269.01 and K05227.01 sit on a start-of-quarter systematic?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library; astropy reads the FITS files.
Pre-registration: findings/2026-10-18-season-check-prereg.md in munimtechnologies/exoplanet-archive-audit.

Five KOIs have periods of 370.9-371.6 d, and all 20 of their catalogue events fall between 0.40 d before and
1.93 d after the first cadence of quarters 3, 7, 11 and 15, the quarters in which each star is back on the same
CCD. Two are Archive CANDIDATEs (K05269.01, K05227.01); three are FALSE POSITIVEs (K05421.01, K05462.01,
K08262.01). With the published pair_events 0.1.0 box (PDCSAP, quality 0) this measures:
  own     each KOI star at its own catalogue events;
  qstart  every star at OFFSET d after the first cadence of every quarter file it has;
on the five KOI stars and on control stars picked by a fixed rule: the CONTROLS_EACH nearest KOI hosts to each
candidate whose KOIs are all CANDIDATE or CONFIRMED with P < P_MAX_CONTROL d and Kp in KP_RANGE (their KOIs
masked). A dip is pair_events' rule: PDCSAP deficit > 0 at or above the star's null 95th percentile. The null
skips QS_AVOID days around every quarter start and +-2 d around the star's own events. Each file's primary
header gives QUARTER, SEASON, MODULE, OUTPUT and CHANNEL. In season means quarter % 4 == 3.

Usage: python season_check.py --data-dir /data --out-dir /out/season [--koi-csv cumulative.csv]
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import sys
import tempfile
import urllib.parse

# In the repository pair_events.py sits next to this file; the sealed job fetches the published copy to
# /out/tool first (fetch_pe.py).
for _d in (os.environ.get("PAIR_EVENTS_DIR", ""), "/out/tool"):
    if _d and os.path.isfile(os.path.join(_d, "pair_events.py")):
        sys.path.insert(0, _d)
        break
import pair_events as pe  # noqa: E402

VERSION = "0.1.0"
TAP = ("https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query="
       + urllib.parse.quote_plus("select kepid,kepoi_name,koi_disposition,koi_period,koi_time0bk,koi_duration,"
                                 "ra,dec,koi_kepmag from cumulative") + "&format=csv")

# label: (kepid, P d, T0 BKJD, duration h, ra, dec); NASA Exoplanet Archive cumulative table, 2026-10-18
KOIS = {
    "K05269.01": (6359929, 371.50631, 260.1243, 8.854, 290.397950, 41.750790),
    "K05227.01": (6034834, 371.56492, 259.8491, 14.736, 289.345150, 41.364780),
    "K05421.01": (7751133, 370.91308, 261.1884, 17.655, 291.136170, 43.476749),
    "K05462.01": (8025718, 371.18648, 260.7045, 19.929, 290.730900, 43.870090),
    "K08262.01": (6195669, 370.94353, 261.1772, 16.64, 288.813570, 41.555119),
}
CANDIDATES = ("K05269.01", "K05227.01")
OFFSET = 1.2            # d after a quarter's first cadence; median of the 20 catalogue offsets is 1.18
CONTROL_DUR_H = 12.0
CONTROLS_EACH = 3
P_MAX_CONTROL = 300.0
KP_RANGE = (12.0, 16.0)
SEASON_MOD = 3          # quarters 3, 7, 11, 15
QS_AVOID = (-0.5, 2.5)
NEAR = (-1.0, 3.0)
TEST_FRACTION = 0.25
TEST_RATIO = 3.0
TEST_FLOOR = 0.05
TEST_P = 0.01

EVENT_FIELDS = ["star", "group", "kepid", "kind", "time", "quarter", "in_season", "after_start_d", "season",
                "module", "output", "channel", "pdc_ppm", "pdc_err", "pct", "z", "dip", "sap_ppm", "sap_err",
                "bkg_ppm", "bkg_err", "c1_mpix", "c1_err", "c2_mpix", "c2_err", "flag_cadences", "flag_bits"]


def sep_deg(ra1, dec1, ra2, dec2):
    """Great-circle separation in degrees (haversine)."""
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    h = math.sin((d2 - d1) / 2) ** 2 + math.cos(d1) * math.cos(d2) * math.sin((r2 - r1) / 2) ** 2
    return math.degrees(2 * math.asin(min(1.0, math.sqrt(h))))


def in_season(quarter):
    return isinstance(quarter, int) and quarter % 4 == SEASON_MOD


def offsets_after_start(p, t0, starts):
    """For each quarter start s, the event of (p, t0) nearest s + 1 d if it lies within NEAR of s: (s, t, t - s)."""
    out = []
    for s in starts:
        t = t0 + round((s + 1.0 - t0) / p) * p
        if NEAR[0] <= t - s <= NEAR[1]:
            out.append((s, round(t, 4), round(t - s, 4)))
    return out


def locate(tc, metas):
    """(quarter whose data span holds tc or '', quarter whose first cadence is within NEAR of tc or '',
    tc minus that first cadence or '')."""
    q_in = next((m["quarter"] for m in metas if m["start"] is not None and m["start"] <= tc <= m["end"]), "")
    near = [(tc - m["start"], m["quarter"]) for m in metas
            if m["start"] is not None and NEAR[0] <= tc - m["start"] <= NEAR[1]]
    if not near:
        return q_in, "", ""
    d, q = min(near, key=lambda x: abs(x[0]))
    return q_in, q, round(d, 4)


def null_times(times, starts, events, n=pe.NULL_N):
    """n evenly spaced times over the data, minus QS_AVOID around quarter starts and +-NULL_AVOID d of events."""
    if not times:
        return []
    step = (times[-1] - times[0]) / n
    grid = [times[0] + (k + 0.5) * step for k in range(n)]
    return [t for t in grid
            if not any(QS_AVOID[0] <= t - s <= QS_AVOID[1] for s in starts)
            and all(abs(t - e) >= pe.NULL_AVOID for e in events)]


def masks_for(kepid, koi_rows, skip=""):
    """(P, T0, dur_h) of every KOI on one star except skip; rows with missing numbers are ignored."""
    out = []
    for r in koi_rows:
        if r.get("kepid") != str(kepid) or r.get("kepoi_name") == skip:
            continue
        try:
            out.append((float(r["koi_period"]), float(r["koi_time0bk"]), float(r["koi_duration"])))
        except (KeyError, ValueError):
            continue
    return out


def select_controls(koi_rows, centres, each=CONTROLS_EACH, exclude=()):
    """The `each` nearest eligible KOI host stars to each centre (ra, dec), distinct, in centre order.

    Eligible: every KOI on the star is CANDIDATE or CONFIRMED with 0 < P < P_MAX_CONTROL and full numbers, Kp
    in KP_RANGE, kepid not in exclude. Returns [(kepid, ra, dec, kp, masks, centre index, sep deg)]."""
    stars = {}
    for r in koi_rows:
        try:
            stars.setdefault(int(r["kepid"]), []).append(r)
        except (KeyError, ValueError):
            continue
    eligible = []
    for kid, rs in sorted(stars.items()):
        if kid in exclude:
            continue
        try:
            masks = [(float(r["koi_period"]), float(r["koi_time0bk"]), float(r["koi_duration"])) for r in rs]
            ra, dec, kp = float(rs[0]["ra"]), float(rs[0]["dec"]), float(rs[0]["koi_kepmag"])
        except (KeyError, ValueError):
            continue
        if any(r["koi_disposition"] not in ("CANDIDATE", "CONFIRMED") for r in rs):
            continue
        if not all(0 < p < P_MAX_CONTROL for p, _, _ in masks) or not KP_RANGE[0] <= kp <= KP_RANGE[1]:
            continue
        eligible.append((kid, ra, dec, kp, masks))
    chosen, seen = [], set()
    for ci, (cra, cdec) in enumerate(centres):
        ranked = sorted(eligible, key=lambda e: (sep_deg(cra, cdec, e[1], e[2]), e[0]))
        taken = 0
        for e in ranked:
            if taken >= each:
                break
            if e[0] in seen:
                continue
            seen.add(e[0])
            taken += 1
            chosen.append(e + (ci, round(sep_deg(cra, cdec, e[1], e[2]), 4)))
    return chosen


def binom_tail(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(k, n + 1))


def fractions(rows, groups):
    """Dips in the quarter-start cells of the given groups, in season and out of season."""
    out = {}
    for key, want in (("season", 1), ("other", 0)):
        cells = [r for r in rows if r["group"] in groups and r["kind"] == "qstart" and r["dip"] != ""
                 and r["in_season"] == want]
        d, n = sum(r["dip"] for r in cells), len(cells)
        out[key] = {"dips": d, "cells": n, "fraction": round(d / n, 3) if n else None,
                    "p_binom": round(binom_tail(d, n, 1 - pe.DIP_PCT), 6) if n else None}
    return out


def p3(frac):
    """The pre-registered test on one group's fractions: True, False, or None when no in-season cell exists."""
    s, o = frac["season"], frac["other"]
    if not s["cells"]:
        return None
    return bool(s["fraction"] >= TEST_FRACTION
                and s["fraction"] >= TEST_RATIO * max(o["fraction"] or 0.0, TEST_FLOOR)
                and s["p_binom"] <= TEST_P)


def file_meta(path):
    """QUARTER, SEASON, MODULE, OUTPUT, CHANNEL from the primary header; first and last finite TIME."""
    from astropy.io import fits
    with fits.open(path, memmap=False) as h:
        head = h[0].header
        meta = {k.lower(): (int(head[k]) if head.get(k) is not None else None)
                for k in ("QUARTER", "SEASON", "MODULE", "OUTPUT", "CHANNEL")}
        t = [float(x) for x in h[1].data["TIME"] if math.isfinite(float(x))]
    meta["start"] = round(t[0], 5) if t else None
    meta["end"] = round(t[-1], 5) if t else None
    meta["file"] = os.path.basename(path)
    return meta


def evaluate(label, group, kepid, dur_h, series, flag_t, flag_q, metas, own_events):
    """(rows, info) for one star: its own events and one quarter-start cell per quarter file."""
    times = series["pdc"][0]
    starts = [m["start"] for m in metas if m["start"] is not None]
    nulls = []
    for t in null_times(times, starts, own_events):
        r = pe.deficit_ppm(pe.box_fit(*series["pdc"], t, dur_h))
        if r is not None:
            nulls.append(r[0])
    sig = pe.robust_sigma(nulls) if len(nulls) >= 10 else None
    cells = [("own", t) for t in own_events] + [("qstart", s + OFFSET) for s in starts]
    rows = []
    for kind, tc in cells:
        q_in, q_near, after = locate(tc, metas)
        q = q_in if q_in != "" else q_near
        meta = next((m for m in metas if m["quarter"] == q), {}) if q != "" else {}
        row = {"star": label, "group": group, "kepid": kepid, "kind": kind, "time": round(tc, 4), "quarter": q,
               "in_season": int(in_season(q)), "after_start_d": after}
        row.update({k: meta.get(k, "") for k in ("season", "module", "output", "channel")})
        row.update(pe.measure(series, tc, dur_h))
        row["flag_cadences"], row["flag_bits"] = pe.flag_summary(flag_t, flag_q, tc)
        if row["pdc_ppm"] != "" and nulls:
            pct = pe.percentile_rank(row["pdc_ppm"], nulls)
            row["pct"] = round(pct, 3)
            row["z"] = round(row["pdc_ppm"] / sig, 2) if sig else ""
            row["dip"] = int(row["pdc_ppm"] > 0 and pct >= pe.DIP_PCT)
        else:
            row["pct"] = row["z"] = row["dip"] = ""
        rows.append(row)
    info = {"star": label, "group": group, "kepid": kepid, "dur_h": dur_h, "points": len(times),
            "null_n": len(nulls), "null_sigma_ppm": round(sig, 1) if sig else None,
            "null_p95_ppm": round(sorted(nulls)[int(pe.DIP_PCT * len(nulls))], 1) if nulls else None,
            "quarters": [{k: m.get(k) for k in ("quarter", "season", "module", "output", "channel", "start", "end",
                                                "file")} for m in metas]}
    return rows, info


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-dir", default="")
    ap.add_argument("--koi-csv", default="")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    cache = args.data_dir or tempfile.mkdtemp()
    if args.koi_csv:
        with open(args.koi_csv, encoding="utf-8") as f:
            text = f.read()
    else:
        text = pe.http_bytes(TAP).decode("utf-8")
    with open(os.path.join(args.out_dir, "cumulative.csv"), "w", encoding="utf-8", newline="") as f:
        f.write(text)
    koi_rows = list(csv.DictReader(io.StringIO(text)))
    controls = select_controls(koi_rows, [KOIS[c][4:6] for c in CANDIDATES], exclude={v[0] for v in KOIS.values()})
    stars = [(label, "candidate" if label in CANDIDATES else "fp", v[0], v[3], masks_for(v[0], koi_rows, label),
              (v[1], v[2])) for label, v in KOIS.items()]
    stars += [(f"C{i + 1}", "control", c[0], CONTROL_DUR_H, c[4], None) for i, c in enumerate(controls)]
    rows, infos, errors = [], [], []
    for label, group, kepid, dur_h, masks, eph in stars:
        try:
            paths = pe.lightcurve_files(kepid, cache)
            metas = sorted((file_meta(p) for p in paths), key=lambda m: (m["start"] is None, m["start"] or 0.0))
            series, flag_t, flag_q = pe.build_series([pe.read_quarter(p) for p in paths], masks)
        except Exception as e:  # one unreadable star must not sink the others; it is reported
            errors.append({"star": label, "kepid": kepid, "error": repr(e)})
            print(json.dumps(errors[-1]), flush=True)
            continue
        times = series["pdc"][0]
        own = pe.events_in(eph[0], eph[1], times[0], times[-1]) if eph and times else []
        r, info = evaluate(label, group, kepid, dur_h, series, flag_t, flag_q, metas, own)
        info["masks"] = masks
        if group == "control":
            c = controls[int(label[1:]) - 1]
            info.update({"ra": c[1], "dec": c[2], "kepmag": c[3], "nearest_to": CANDIDATES[c[5]], "sep_deg": c[6]})
        rows += r
        infos.append(info)
        print(json.dumps({k: v for k, v in info.items() if k != "quarters"}), flush=True)
    write_outputs(args.out_dir, rows, infos, controls, errors)
    return 0


def write_outputs(out_dir, rows, infos, controls, errors):
    groups = {"candidate": ("candidate",), "fp": ("fp",), "koi": ("candidate", "fp"), "control": ("control",)}
    frac = {k: fractions(rows, g) for k, g in groups.items()}
    own = {}
    for label in KOIS:
        o = [r for r in rows if r["star"] == label and r["kind"] == "own"]
        own[label] = {"events": len(o), "fitted": sum(1 for r in o if r["dip"] != ""),
                      "dips": sum(r["dip"] for r in o if r["dip"] != ""), "times": [r["time"] for r in o]}
    modules = {i["star"]: {str(m["quarter"]): [m["module"], m["output"], m["channel"]] for m in i["quarters"]
                           if in_season(m["quarter"])} for i in infos}
    with open(os.path.abspath(__file__), "rb") as f:
        own_sha = hashlib.sha256(f.read()).hexdigest()
    with open(os.path.abspath(pe.__file__), "rb") as f:
        pe_sha = hashlib.sha256(f.read()).hexdigest()
    stats = {"version": VERSION, "season_check_sha256": own_sha, "pair_events_version": pe.VERSION,
             "pair_events_sha256": pe_sha, "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "offset_d": OFFSET, "control_dur_h": CONTROL_DUR_H,
             "controls": [{"kepid": c[0], "ra": c[1], "dec": c[2], "kepmag": c[3], "kois": len(c[4]),
                           "nearest_to": CANDIDATES[c[5]], "sep_deg": c[6]} for c in controls],
             "fractions": frac, "p3_control_test": p3(frac["control"]), "own_events": own,
             "in_season_modules": modules, "errors": errors, "stars": infos}
    pe.write_csv(os.path.join(out_dir, "events.csv"), rows, EVENT_FIELDS)
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)
    lines = [f"# season-check {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0. "
             "Leads to check by eye, not dispositions.", "",
             f"Quarter-start cells at first cadence + {OFFSET} d. Dip = PDCSAP deficit > 0 at or above the star's "
             "null 95th percentile. In season = quarters 3, 7, 11, 15.", "",
             "## Quarter-start dips by group", "",
             "| group | in-season dips / cells | fraction | p (binomial, 0.05) | other dips / cells | fraction | p |",
             "|---|---|---|---|---|---|---|"]
    for k, v in frac.items():
        s, o = v["season"], v["other"]
        lines.append(f"| {k} | {s['dips']} / {s['cells']} | {s['fraction']} | {s['p_binom']} | {o['dips']} / "
                     f"{o['cells']} | {o['fraction']} | {o['p_binom']} |")
    lines += ["", f"Pre-registered control test (P3): **{stats['p3_control_test']}**", "",
              "## Own catalogue events", "", "| KOI | events | fitted | dips | times |", "|---|---|---|---|---|"]
    lines += [f"| {k} | {v['events']} | {v['fitted']} | {v['dips']} | {v['times']} |" for k, v in own.items()]
    lines += ["", "## Module / output / channel in quarters 3, 7, 11, 15", "", "| star | quarters |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in modules.items()]
    lines += ["", "## Controls", "", "| kepid | ra | dec | Kp | KOIs | nearest to | sep (deg) |", "|---|---|---|---|---|---|---|"]
    lines += [f"| {c['kepid']} | {c['ra']} | {c['dec']} | {c['kepmag']} | {c['kois']} | {c['nearest_to']} | "
              f"{c['sep_deg']} |" for c in stats["controls"]]
    if errors:
        lines += ["", "## Errors", ""] + [f"- {e['star']} (KIC {e['kepid']}): {e['error']}" for e in errors]
    lines += ["", "## Every cell", "",
              "| star | kind | time | Q | in season | after start | ch | PDC (ppm) | pct | z | dip | SAP (ppm) | "
              "BKG (ppm) | c1 (mpix) | c2 (mpix) | flags | bits |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {r['star']} | {r['kind']} | {r['time']} | {r['quarter']} | {r['in_season']} | {r['after_start_d']} | "
              f"{r['channel']} | {r['pdc_ppm']} +- {r['pdc_err']} | {r['pct']} | {r['z']} | {r['dip']} | "
              f"{r['sap_ppm']} +- {r['sap_err']} | {r['bkg_ppm']} +- {r['bkg_err']} | {r['c1_mpix']} +- "
              f"{r['c1_err']} | {r['c2_mpix']} +- {r['c2_err']} | {r['flag_cadences']} | {r['flag_bits']} |"
              for r in rows]
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps({k: v for k, v in stats.items() if k != "stars"}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
