"""kepler_coverage: Kepler planets whose period Kepler's own data coverage cannot pin down.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library plus astropy for FITS.

Found by hand first (2026-10-16): Kepler-1633 b (KOI-5568.01, KIC 8745553). The DR25 KOI table gives
62.134919 d; Morton et al. 2016, Holczer et al. 2016, Gajdos et al. 2019 and the Archive's default give
186.404 d, three times longer. The star was observed only in the even quarters (Q2, Q4, ..., Q16;
st_quarters 01010101010101010). Two quarters last about 186 d, so every 62.13 d epoch that is not also a
186.4 d epoch falls in an unobserved quarter (kepler_alias 0.2.0 found data at 7 epochs, all with the
same epoch number mod 3). Kepler's data alone cannot tell 62.13, 93.20 and 186.40 d apart.

Method:
1. Reference segments. The quality-0 long-cadence times of one star observed in every quarter
   (KIC 8105398), split at gaps longer than 0.25 d, give each quarter's stretches of data.
2. A star's coverage is the union of the segments of the quarters that its st_quarters string
   (keplerstellar, Q1..Q17; the row with the most observed quarters) marks as observed. Q0 is not in
   that string and is left out.
3. An epoch is covered if at least half of its transit window (the catalogue duration) lies inside the
   coverage. For a period P with covered epochs E:
     P/k (k = 2..5) is unconstrained if none of the epochs P/k adds to P's is covered;
     k*P is unconstrained if E has at least two epochs and all of them have the same n mod k.
   "no_coverage" if E is empty; "one_epoch" if E has one epoch (then k*P is not tested).
4. Census: every DR25 KOI not dispositioned FALSE POSITIVE, on its KOI ephemeris; and every confirmed
   Kepler planet whose composite (Archive default) period differs from its KOI period by more than
   0.2 %, on the composite ephemeris (pl_tranmid, pl_trandur).
5. Light-curve check: for the flagged rows, and for control planets, the same test on the star's own
   quality-0 cadences from MAST (all quarters it has, Q0 included).
A flag means Kepler's coverage alone cannot exclude that alias. Other data (TESS, radial velocities,
transit timing, the transit's duration and shape) may still decide it.

Usage: python kepler_coverage.py --out-dir /out [--data-dir /data] [--max-targets 40]
"""
import argparse
import bisect
import csv
import datetime as dt
import json
import math
import os
import sys
import tempfile

import kepler_alias as ka

VERSION = "0.1.0"
REF_KEPID = "8105398"
MAX_GAP = 0.25
HALF_CADENCE = 0.0102
MIN_FRAC = 0.5
MAX_K = 5
CONTROLS = ("K05568.01", "K05475.01", "K02174.03")  # Kepler-1633 b, Kepler-1632 b, Kepler-1802 b
STELLAR = "select kepid, st_quarters from keplerstellar where kepid in (select kepid from q1_q17_dr25_koi)"
KOIS = ("select kepid, kepoi_name, kepler_name, koi_disposition, koi_period, koi_time0bk, koi_duration, "
        "koi_num_transits from q1_q17_dr25_koi")
COMP = "select pl_name, pl_orbper, pl_orbper_reflink, pl_tranmid, pl_trandur from pscomppars"


def merge(segs):
    """Sorted, non-overlapping union of (start, end) segments."""
    out = []
    for a, b in sorted(segs):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def segments_from_times(times, max_gap=MAX_GAP, pad=HALF_CADENCE):
    """[(start, end)] stretches of sorted times with no gap longer than max_gap, padded by half a cadence."""
    segs = []
    for t in times:
        if segs and t - segs[-1][1] <= max_gap:
            segs[-1][1] = t
        else:
            segs.append([t, t])
    return [(a - pad, b + pad) for a, b in segs]


class Coverage:
    def __init__(self, segs):
        self.segs = merge(segs)
        self.starts = [a for a, _ in self.segs]
        self.lo = self.segs[0][0] if self.segs else 0.0
        self.hi = self.segs[-1][1] if self.segs else 0.0

    def overlap(self, a, b):
        """Length of [a, b] inside the coverage."""
        i = max(0, bisect.bisect_right(self.starts, a) - 1)
        tot = 0.0
        while i < len(self.segs) and self.segs[i][0] < b:
            s, e = self.segs[i]
            tot += max(0.0, min(e, b) - max(s, a))
            i += 1
        return tot


def covered_epochs(cov, p, t0, dur_h, min_frac=MIN_FRAC):
    """Epoch numbers n of (p, t0) whose transit window is at least min_frac inside the coverage."""
    if not cov.segs or not p or p <= 0 or not dur_h or dur_h <= 0 or t0 is None:
        return []
    half = 0.5 * dur_h / 24.0
    out = []
    for n in range(math.ceil((cov.lo - t0) / p), math.floor((cov.hi - t0) / p) + 1):
        tc = t0 + n * p
        if cov.overlap(tc - half, tc + half) >= min_frac * 2 * half:
            out.append(n)
    return out


def alias_flags(cov, p, t0, dur_h, max_k=MAX_K, min_frac=MIN_FRAC):
    """{"observed": covered epochs of P, "short": {k: covered extra epochs of P/k},
    "long": {k: True if k*P is unconstrained}, "flags": [...]}."""
    obs = covered_epochs(cov, p, t0, dur_h, min_frac)
    short = {k: sum(1 for m in covered_epochs(cov, p / k, t0, dur_h, min_frac) if m % k)
             for k in range(2, max_k + 1)}
    long_ = {k: len(obs) >= 2 and len({n % k for n in obs}) == 1 for k in range(2, max_k + 1)}
    if not obs:
        flags = ["no_coverage"]
    else:
        flags = [f"P/{k}" for k in range(2, max_k + 1) if short[k] == 0]
        flags += ["one_epoch"] if len(obs) == 1 else [f"{k}P" for k in range(2, max_k + 1) if long_[k]]
    return {"observed": obs, "short": short, "long": long_, "flags": flags}


def quarters_from_string(s):
    """Quarters marked '1' in a Q1..Q17 st_quarters string."""
    return [i + 1 for i, ch in enumerate((s or "").strip()) if ch == "1"]


def best_quarters(rows):
    """kepid -> the st_quarters string with the most observed quarters (empty strings ignored)."""
    best = {}
    for r in rows:
        s = (r.get("st_quarters") or "").strip()
        if s and s.count("1") > best.get(r["kepid"], "").count("1"):
            best[r["kepid"]] = s
    return best


def star_coverage(qsegs, quarters):
    return Coverage([s for q in quarters for s in qsegs.get(q, [])])


def read_quarter(path):
    """(quarter, sorted quality-0 times) of one long-cadence file."""
    from astropy.io import fits
    with fits.open(path, memmap=False) as h:
        q = int(h[0].header.get("QUARTER", -1))
        d = h[1].data
        ts = sorted(float(t) for t, f, qual in zip(d["TIME"], d["PDCSAP_FLUX"], d["SAP_QUALITY"])
                    if int(qual) == 0 and math.isfinite(float(t)) and math.isfinite(float(f)))
    return q, ts


def quarter_segments(paths):
    """quarter -> segments, from a list of long-cadence files."""
    by_q = {}
    for path in paths:
        q, ts = read_quarter(path)
        by_q.setdefault(q, []).extend(ts)
    return {q: segments_from_times(sorted(ts)) for q, ts in by_q.items() if ts}


def short_text(short):
    return ";".join(f"{k}:{v}" for k, v in sorted(short.items()))


def epochs_text(obs, limit=12):
    return " ".join(str(n) for n in obs) if len(obs) <= limit else f"{obs[0]}..{obs[-1]} ({len(obs)})"


def census_rows(kois, comp, best, qsegs):
    """One row per non-FALSE-POSITIVE KOI on its KOI ephemeris, and one per confirmed planet whose
    composite period differs from the KOI period, on the composite ephemeris."""
    rows, no_quarters = [], 0
    for koi in kois:
        if koi.get("koi_disposition") == "FALSE POSITIVE":
            continue
        s = best.get(koi.get("kepid", ""))
        if not s:
            no_quarters += 1
            continue
        cov = star_coverage(qsegs, quarters_from_string(s))
        p, t0, dur = ka.num(koi, "koi_period"), ka.num(koi, "koi_time0bk"), ka.num(koi, "koi_duration")
        eph = [("koi", p, t0, dur, "Q1-Q17 DR25 KOI Table")]
        c = comp.get(koi.get("kepler_name", "")) if koi.get("koi_disposition") == "CONFIRMED" else None
        if c:
            pa, tm = ka.num(c, "pl_orbper"), ka.num(c, "pl_tranmid")
            if pa and p and tm is not None and abs(pa / p - 1) > ka.TOL:
                eph.append(("archive", pa, tm - ka.BKJD, ka.num(c, "pl_trandur") or dur,
                            ka.ref_text(c.get("pl_orbper_reflink", ""))))
        for source, pp, tt, dd, ref in eph:
            f = alias_flags(cov, pp, tt, dd)
            rows.append({"source": source, "kepid": koi.get("kepid", ""), "kepoi_name": koi.get("kepoi_name", ""),
                         "kepler_name": koi.get("kepler_name", ""), "koi_disposition": koi.get("koi_disposition", ""),
                         "period": pp, "period_ref": ref, "t0_bkjd": tt, "duration_h": dd, "st_quarters": s,
                         "n_quarters": s.count("1"), "koi_num_transits": ka.num(koi, "koi_num_transits"),
                         "n_observed": len(f["observed"]), "observed": epochs_text(f["observed"]),
                         "short_covered": short_text(f["short"]), "flags": ";".join(f["flags"])})
    return rows, no_quarters


def lightcurve_check(row, cache):
    """The same test on the star's own cadences."""
    paths = ka.lightcurve_files(row["kepid"], cache)
    quarters, times = set(), []
    for path in paths:
        q, ts = read_quarter(path)
        if ts:
            quarters.add(q)
            times.extend(ts)
    times.sort()
    f = alias_flags(Coverage(segments_from_times(times)), row["period"], row["t0_bkjd"], row["duration_h"])
    flags = ";".join(f["flags"])
    return {"lc_quarters": " ".join(str(q) for q in sorted(quarters)), "lc_n_observed": len(f["observed"]),
            "lc_observed": epochs_text(f["observed"]), "lc_short_covered": short_text(f["short"]),
            "lc_flags": flags, "agrees": "yes" if flags == row["flags"] else "no"}


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-dir", default="")
    ap.add_argument("--max-targets", type=int, default=40)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    cache = args.data_dir or tempfile.mkdtemp()
    p = (lambda n: os.path.join(args.data_dir, n)) if args.data_dir else (lambda n: None)
    best = best_quarters(csv.DictReader(ka.fetch(STELLAR, p("keplerstellar-quarters.csv")).splitlines()))
    kois = list(csv.DictReader(ka.fetch(KOIS, p("dr25-koi-coverage.csv")).splitlines()))
    comp = {r["pl_name"]: r for r in csv.DictReader(ka.fetch(COMP, p("pc-coverage.csv")).splitlines())}
    qsegs = quarter_segments(ka.lightcurve_files(REF_KEPID, cache))

    rows, no_quarters = census_rows(kois, comp, best, qsegs)
    fields = list(rows[0].keys()) if rows else []
    write_csv(os.path.join(args.out_dir, "census.csv"), rows, fields)

    order = {"CONFIRMED": 0, "CANDIDATE": 1}
    flagged = [r for r in rows if r["flags"] and r["flags"] != "no_coverage"]
    flagged.sort(key=lambda r: (order.get(r["koi_disposition"], 2), -r["period"]))
    controls = [r for r in rows if r["kepoi_name"] in CONTROLS and r not in flagged]
    checks = []
    for r in (flagged[:args.max_targets] + controls):
        out = dict(r)
        try:
            out.update(lightcurve_check(r, cache))
            out["error"] = ""
        except Exception as exc:  # one star's download or file problem must not stop the others
            out.update({"lc_quarters": "", "lc_n_observed": "", "lc_observed": "", "lc_short_covered": "",
                        "lc_flags": "", "agrees": "", "error": f"{type(exc).__name__}: {exc}"[:300]})
        checks.append(out)
        print(json.dumps({k: out[k] for k in ("kepoi_name", "source", "period", "flags", "lc_flags", "error")}),
              flush=True)
    check_fields = fields + ["lc_quarters", "lc_n_observed", "lc_observed", "lc_short_covered", "lc_flags",
                             "agrees", "error"]
    write_csv(os.path.join(args.out_dir, "lightcurve_checks.csv"), checks, check_fields)

    def count(rs, disp):
        return sum(1 for r in rs if r["koi_disposition"] == disp)

    by_flag = {}
    for r in rows:
        for fl in (r["flags"].split(";") if r["flags"] else []):
            by_flag.setdefault(fl, {"CONFIRMED": 0, "CANDIDATE": 0})
            if r["koi_disposition"] in by_flag[fl]:
                by_flag[fl][r["koi_disposition"]] += 1
    stats = {
        "version": VERSION, "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "reference_kepid": REF_KEPID, "reference_quarters": sorted(qsegs),
        "reference_segments": sum(len(v) for v in qsegs.values()),
        "stars_with_quarters": len(best), "koi_rows": len(kois), "kois_without_quarters": no_quarters,
        "census_rows": len(rows), "koi_ephemeris_rows": sum(1 for r in rows if r["source"] == "koi"),
        "archive_ephemeris_rows": sum(1 for r in rows if r["source"] == "archive"),
        "flagged_rows": len(flagged), "flagged_confirmed": count(flagged, "CONFIRMED"),
        "flagged_candidate": count(flagged, "CANDIDATE"), "by_flag": by_flag,
        "lightcurve_checked": len(checks), "lightcurve_agree": sum(1 for c in checks if c["agrees"] == "yes"),
        "lightcurve_disagree": sum(1 for c in checks if c["agrees"] == "no"),
        "lightcurve_error": sum(1 for c in checks if c["error"]),
        "controls": {c["kepoi_name"] + " " + c["source"]: {"flags": c["flags"], "lc_flags": c["lc_flags"]}
                     for c in checks if c["kepoi_name"] in CONTROLS},
    }
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

    lines = [f"# kepler-coverage {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY "
             "4.0. A flag means Kepler's own data coverage cannot exclude that alias of the period; it is not a "
             "claim that the catalogued period is wrong. P/k: none of the extra epochs of P/k has data; kP: every "
             "epoch with data has the same epoch number mod k.", ""]
    lines += [f"- {k}: {v}" for k, v in stats.items() if k not in ("version", "run_at")]
    lines += ["", "## Light-curve checks (flagged confirmed planets and candidates first, then controls)", "",
              "| KOI | planet | disposition | ephemeris | P (ref) | quarters | epochs with data | flags "
              "(quarters) | flags (light curve) | agree |", "|---|---|---|---|---|---|---|---|---|---|"]
    for c in checks:
        lines.append(f"| {c['kepoi_name']} | {c['kepler_name']} | {c['koi_disposition']} | {c['source']} | "
                     f"{c['period']} ({c['period_ref']}) | {c['st_quarters']} | {c['lc_observed'] or c['observed']} | "
                     f"{c['flags']} | {c['lc_flags'] or c['error']} | {c['agrees']} |")
    lines += ["", "## All flagged rows (first 300)", "",
              "| KOI | planet | disposition | ephemeris | P (ref) | quarters | epochs with data | P/k extra epochs "
              "with data | flags |", "|---|---|---|---|---|---|---|---|---|"]
    for r in flagged[:300]:
        lines.append(f"| {r['kepoi_name']} | {r['kepler_name']} | {r['koi_disposition']} | {r['source']} | "
                     f"{r['period']} ({r['period_ref']}) | {r['st_quarters']} | {r['observed']} | "
                     f"{r['short_covered']} | {r['flags']} |")
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
