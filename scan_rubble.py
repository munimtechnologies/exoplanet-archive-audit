#!/usr/bin/env python3
# Apache-2.0. scan_rubble 0.2.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
"""Open re-derivation of DR25's Rubble metric (Thompson et al. 2018, A.3.7.1) from public Kepler DV files.

0.1.0 (rubble-scan-v1, 60 development stars, 125 TCEs) was an exploratory scan of 24 variants. Its pre-registered
selection rule returned NEGATIVE (findings/2026-10-19-rubble-scan-results.md), so no variant was chosen and the
reserve test of that rule was cancelled. Two patterns were noticed afterwards in the development data and are NOT
yet tested:
  P1  a TCE has no finite MODEL_WHITE cadence in any transit if and only if its Robovetter duration is a whole
      multiple of 0.5 h (8 of 8 vs 0 of 117 in development);
  P2  DR25's own settings (LC_INIT, two durations, threshold 0.75) find every DR25 Rubble TCE but over-flag:
      recall 66/66, precision 66/94 in development.
0.2.0 adds `--reserve`: a gated, pre-registered test of P1 and P2 on the 200 reserve stars that 0.1.0 listed in
sample.json and never downloaded (findings/2026-10-19-rubble-reserve-prereg.md). The gate: the job must hold the
published pre-registration note and the published sample.json, and the reserve list drawn here must equal the
published one, before any reserve star is downloaded. Decisions are integer arithmetic on counts (decide_p1,
decide_p2); the development scan (default mode) is unchanged apart from two descriptive columns.

Variants: cadence source x window x threshold.
  sources     init   finite LC_INIT of the TCE's own DVT extension (earlier TCEs' transits removed)
              white  finite MODEL_WHITE of the same extension (more cadences than LC_INIT; possibly gap-filled ones)
              pdc    finite PDCSAP_FLUX of the DVT Statistics extension (per star)
              resid  finite RESIDUAL_LC of the Statistics extension (per star)
  windows     1 or 2 transit durations centred on mid-transit
  thresholds  0.25, 0.5, 0.75 (DR25's stated value)
For every variant, a real event has at least one finite LC_INIT cadence within half a duration of mid-transit.

Outputs (--out-dir): summary.json, sample.json, tces.csv, events.csv (events with partial coverage), variants.json,
report.md and, in reserve mode, reserve.json (the P1 and P2 decisions). Pure Python plus numpy/astropy for FITS.
Network: MAST and raw/media GitHub only.
"""
import argparse
import bisect
import csv
import hashlib
import io
import json
import math
import os
import random
import re
import sys
import tarfile
import tempfile
import time
import traceback
import urllib.request

VERSION = "0.2.0"
UA = "mv2-scan-rubble/0.2 (Munim, Inc.; mv2@munimtech.com)"
RV = "https://raw.githubusercontent.com/nasa/kepler-robovetter/master/{}"
RV_MEDIA = "https://media.githubusercontent.com/media/nasa/kepler-robovetter/master/{}"
RV_INPUT = "kplr_dr25_obs_robovetter_input.tar.gz"
RV_SHA256 = "3d6689deb2fc76babdd9935f803f0395d5b73dfa4a7b2ac73aed53a731c49655"  # rubble-probe-v1
RV_ROWS = 32534
DVT_DIR = "https://archive.stsci.edu/missions/kepler/dv_files/{0}/{1}/"
DVT_STAMP = "20160128150956"  # in the MAST listing for all three probe stars that have a DVT file
SEED = 20261019
N_DEV = 60
N_RESERVE = 200
# looked up before this scan: the five probe stars and the stars of KOI-5600, 1356 and 1209 (earlier work)
LOOKED_UP = (6359929, 6034834, 11446443, 11442793, 6922244, 9018021, 7363829, 3534076)
# regression controls hand-counted from rubble-probe-v1 events.csv: (kic, pn, real events, fails of init_2_0.75)
CONTROLS = ((6922244, 1, 384, 4), (11442793, 5, 7, 2))
SOURCES = ("init", "white", "pdc", "resid")
WINDOWS = (1, 2)
THRESHOLDS = (0.25, 0.5, 0.75)
CADENCE_MIN = 29.4244  # Kepler long cadence in minutes (Thompson et al. 2018 quote 29.42)
PERIOD_RTOL = 1e-3
PARTIAL_BELOW = 0.9  # events.csv keeps real events whose two-duration coverage is below this in some source
# 0-based columns of the Robovetter input, as Kepler-RoboVetter-DR25.cpp reads them
COL = {"kic": 2, "pn": 3, "n_plan": 4, "ntrans": 5, "nrealt": 6, "ngoodt": 7, "iflag0": 8, "period": 26,
       "epoch": 28, "duration": 30, "mes": 39, "new_mes": 41}
N_IFLAGS = 6
# pre-registered reserve test (findings/2026-10-19-rubble-reserve-prereg.md)
HALF_HOUR_TOL = 1e-5     # on 2 x duration in hours
P1_MIN_HALF = 5          # P1 is powered if at least this many eligible TCEs have a half-hour-multiple duration
P1_OFF_PER_100 = 2       # P1 holds if off-diagonal TCEs are at most 2 per 100 eligible (off * 50 <= n)
P2_VARIANT = "init_2_0.75"
P2_MIN_FLAGGED = 20      # P2 is powered if at least this many scored TCEs carry DR25's Rubble flag (tp + fn)
P2_RECALL_NUM, P2_RECALL_DEN = 9, 10      # recall >= 0.9  <=>  10 tp >= 9 (tp + fn)
P2_PRECISION_NUM, P2_PRECISION_DEN = 4, 5  # precision <= 0.8  <=>  5 tp <= 4 (tp + fp)
GATE_TEXT = "Rubble reserve pre-registration"


# ---------- pure functions (tested) ----------

def expected_cadences(duration_hours, n_durations=2.0, cadence_min=CADENCE_MIN):
    """Cadences expected across n_durations transit durations."""
    return n_durations * duration_hours * 60.0 / cadence_min


def count_within(valid, t, half_width):
    """Number of sorted times in valid with |x - t| <= half_width."""
    lo = bisect.bisect_left(valid, t - half_width)
    hi = bisect.bisect_right(valid, t + half_width)
    return hi - lo


def coverage(valid, t_mid, duration_hours, n_durations=2.0):
    """Available cadences within n_durations/2 durations either side of t_mid, over those expected."""
    half = n_durations * duration_hours / 24.0 / 2.0
    exp = expected_cadences(duration_hours, n_durations)
    return count_within(valid, t_mid, half) / exp if exp > 0 else float("nan")


def events_in_span(t0, period, t_min, t_max):
    """Mid-times t0 + n*period inside [t_min, t_max], in order."""
    if period <= 0:
        return []
    n = math.ceil((t_min - t0) / period)
    out = []
    while t0 + n * period <= t_max:
        out.append(t0 + n * period)
        n += 1
    return out


def parse_rv_line(line):
    """One data row of the IPAC Robovetter input -> dict, or None for header, comment or malformed lines."""
    s = line.strip()
    if not s or s[0] in "\\|#":
        return None
    f = s.split()
    if len(f) <= COL["new_mes"]:
        return None
    try:
        row = {"kic": int(f[COL["kic"]]), "pn": int(f[COL["pn"]]), "n_plan": int(f[COL["n_plan"]]),
               "ntrans": int(f[COL["ntrans"]]), "nrealt": int(f[COL["nrealt"]]), "ngoodt": int(f[COL["ngoodt"]]),
               "iflags": [int(float(f[COL["iflag0"] + i])) for i in range(N_IFLAGS)],
               "period": float(f[COL["period"]]), "epoch": float(f[COL["epoch"]]),
               "duration": float(f[COL["duration"]]), "mes": float(f[COL["mes"]]),
               "new_mes": float(f[COL["new_mes"]])}
    except ValueError:
        return None
    return row


def draw_sample(kics, seed=SEED, n_dev=N_DEV, n_reserve=N_RESERVE, excluded=LOOKED_UP):
    """(development stars, reserve stars): a seeded shuffle of the distinct KICs not excluded, split in order."""
    pool = sorted(set(kics) - set(excluded))
    random.Random(seed).shuffle(pool)
    return sorted(pool[:n_dev]), sorted(pool[n_dev:n_dev + n_reserve])


def tce_number(ext_name):
    """Planet number of a DVT extension named TCE_n, else None."""
    m = re.fullmatch(r"TCE_(\d+)", ext_name.strip())
    return int(m.group(1)) if m else None


def variant_names():
    return ["{}_{}_{}".format(s, w, t) for s in SOURCES for w in WINDOWS for t in THRESHOLDS]


def event_coverage(sources, t, duration_hours):
    """{'cov1': {source: value}, 'cov2': {...}} for one event."""
    return {"cov{}".format(w): {s: coverage(v, t, duration_hours, float(w)) for s, v in sources.items()}
            for w in WINDOWS}


def is_real(ev):
    return ev["cov1"]["init"] > 0


def n_real(events, source):
    """Events with at least one cadence of the source within half a duration of mid-transit."""
    return sum(1 for e in events if e["cov1"][source] > 0)


def n_fail(events, source, window, threshold):
    """Real events whose coverage in the variant falls below the threshold."""
    return sum(1 for e in events if is_real(e) and e["cov{}".format(window)][source] < threshold)


def tce_counts(events):
    out = {"nreal_" + s: n_real(events, s) for s in SOURCES}
    for s in SOURCES:
        for w in WINDOWS:
            for t in THRESHOLDS:
                out["fail_{}_{}_{}".format(s, w, t)] = n_fail(events, s, w, t)
    return out


def confusion(rows, variant):
    """{'tp','fp','fn','tn'} of 'variant flags the TCE' (any failing real event) against DR25's iflag0."""
    c = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for r in rows:
        pred = r["fail_" + variant] > 0
        truth = r["iflags"][0] == 1
        c["tp" if pred and truth else "fp" if pred else "fn" if truth else "tn"] += 1
    return c


def score(rows):
    """Agreement with DR25 over scored TCE rows (dicts with pn, nrealt, ngoodt, iflags and the tce_counts keys)."""
    res = {"n": len(rows), "nreal": {}, "variants": {}}
    for s in SOURCES:
        d = [r["nreal_" + s] - r["nrealt"] for r in rows]
        res["nreal"][s] = {"exact": sum(1 for x in d if x == 0), "within1": sum(1 for x in d if abs(x) <= 1),
                           "over": sum(1 for x in d if x > 1), "under": sum(1 for x in d if x < -1)}
    for v in variant_names():
        res["variants"][v] = {"all": confusion(rows, v), "pn1": confusion([r for r in rows if r["pn"] == 1], v),
                              "pn>1": confusion([r for r in rows if r["pn"] != 1], v)}
        ro = [0, 0, 0]  # Rubble-only TCEs: n, exact, within 1
        for r in rows:
            if r["iflags"][0] == 1 and sum(r["iflags"]) == 1:
                diff = r["fail_" + v] - (r["nrealt"] - r["ngoodt"])
                ro[0] += 1
                ro[1] += 1 if diff == 0 else 0
                ro[2] += 1 if abs(diff) <= 1 else 0
        res["variants"][v]["rubble_only"] = {"n": ro[0], "exact": ro[1], "within1": ro[2]}
    return res


def is_half_hour(duration_hours, tol=HALF_HOUR_TOL):
    """True if a positive duration in hours is a whole multiple of 0.5 h (|2d - round(2d)| <= tol)."""
    if not duration_hours > 0:
        return False
    x = 2.0 * duration_hours
    return abs(x - round(x)) <= tol


def p1_table(rows):
    """Pre-registered P1 cells over scored rows with at least one real event.
    a: half-hour duration and no MODEL_WHITE cadence in any transit; b: half-hour, some; c: other duration, none;
    d: other duration, some. 'skipped' counts scored rows with no real event (nreal_init == 0)."""
    t = {"a": 0, "b": 0, "c": 0, "d": 0, "skipped": 0}
    for r in rows:
        if r["nreal_init"] <= 0:
            t["skipped"] += 1
            continue
        half = is_half_hour(r["duration"])
        empty = r["nreal_white"] == 0
        t["a" if half and empty else "b" if half else "c" if empty else "d"] += 1
    return t


def decide_p1(rows):
    """P1: empty MODEL_WHITE iff half-hour-multiple duration. Integer rule on the 2x2 table."""
    t = p1_table(rows)
    n = t["a"] + t["b"] + t["c"] + t["d"]
    half = t["a"] + t["b"]
    off = t["b"] + t["c"]
    if half < P1_MIN_HALF:
        status = "underpowered"
    elif off * (100 // P1_OFF_PER_100) <= n:
        status = "holds"
    else:
        status = "fails"
    return {"status": status, "table": t, "n": n, "half_hour": half, "off_diagonal": off,
            "rule": "powered if half_hour >= {}; holds if off_diagonal * {} <= n".format(P1_MIN_HALF,
                                                                                         100 // P1_OFF_PER_100)}


def decide_p2(rows, variant=P2_VARIANT):
    """P2: the variant's recall >= 0.9 and precision <= 0.8 against DR25's iflag0. Integer rule on counts."""
    c = confusion(rows, variant)
    flagged = c["tp"] + c["fn"]
    predicted = c["tp"] + c["fp"]
    recall_ok = P2_RECALL_DEN * c["tp"] >= P2_RECALL_NUM * flagged
    precision_ok = P2_PRECISION_DEN * c["tp"] <= P2_PRECISION_NUM * predicted
    if flagged < P2_MIN_FLAGGED:
        status = "underpowered"
    elif recall_ok and precision_ok:
        status = "holds"
    else:
        status = "fails"
    return {"status": status, "variant": variant, "confusion": c, "n": len(rows), "flagged": flagged,
            "predicted": predicted, "recall_ok": recall_ok, "precision_ok": precision_ok,
            "rule": "powered if tp + fn >= {}; holds if {} tp >= {} (tp + fn) and {} tp <= {} (tp + fp)".format(
                P2_MIN_FLAGGED, P2_RECALL_DEN, P2_RECALL_NUM, P2_PRECISION_DEN, P2_PRECISION_NUM)}


def check_gate(published_sample, dev, reserve, note_text):
    """(ok, reasons): the published sample must match the drawn split and the note must be the pre-registration."""
    reasons = []
    if not isinstance(published_sample, dict):
        reasons.append("published sample is not a JSON object")
    else:
        if published_sample.get("seed") != SEED:
            reasons.append("published seed differs")
        if list(published_sample.get("development", [])) != list(dev):
            reasons.append("published development list differs")
        if list(published_sample.get("reserve_never_downloaded", [])) != list(reserve):
            reasons.append("published reserve list differs")
    if GATE_TEXT not in (note_text or ""):
        reasons.append("note lacks the text '{}'".format(GATE_TEXT))
    if set(dev) & set(reserve):
        reasons.append("development and reserve overlap")
    return (not reasons), reasons


# ---------- network and files ----------

def http_bytes(url, tries=3, timeout=180, wait=5):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # retried, then raised
            last = e
            time.sleep(wait * (k + 1))
    raise last


def http_to_file(url, path, tries=3, timeout=600, wait=5):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r, open(path, "wb") as f:
                for block in iter(lambda: r.read(1 << 20), b""):
                    f.write(block)
            return
        except Exception as e:  # retried, then raised
            last = e
            time.sleep(wait * (k + 1))
    raise last


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch_rv(name, cache_dir):
    """Cached kepler-robovetter file (git-lfs pointers are followed), as probe_rubble 0.1.0 did."""
    path = os.path.join(cache_dir, name)
    if not (os.path.isfile(path) and os.path.getsize(path) > 1000):
        http_to_file(RV.format(name), path)
        with open(path, "rb") as f:
            lfs = f.read(40).startswith(b"version https://git-lfs")
        if lfs:
            http_to_file(RV_MEDIA.format(name), path)
    return path


def load_rv_input(cache_dir):
    """(rows, provenance) from the OBS Robovetter input."""
    path = fetch_rv(RV_INPUT, cache_dir)
    rows = []
    with tarfile.open(path, "r:gz") as tf:
        member = max((m for m in tf.getmembers() if m.isfile()), key=lambda m: m.size)
        stream = io.TextIOWrapper(tf.extractfile(member), encoding="utf-8", errors="replace")
        for line in stream:
            r = parse_rv_line(line)
            if r is not None:
                rows.append(r)
    return rows, {"url": RV.format(RV_INPUT), "sha256": sha256_file(path), "member": member.name,
                  "member_bytes": member.size, "rows": len(rows)}


def fetch_dvt(star, cache_dir):
    """(path, how) of the star's DVT file: the DR25 stamp first, then the directory listing."""
    name = "kplr{}-{}_dvt.fits".format(star, DVT_STAMP)
    path = os.path.join(cache_dir, name)
    if os.path.isfile(path) and os.path.getsize(path) > 10000:
        return path, "cached"
    try:
        http_to_file(DVT_DIR.format(star[:4], star) + name, path, tries=2)
        return path, "stamp"
    except Exception as e:
        first = repr(e)[:120]
    html = http_bytes(DVT_DIR.format(star[:4], star), tries=2).decode("utf-8", "replace")
    names = sorted(set(re.findall(r"kplr\d{9}-\d{14}_dvt\.fits", html)))
    if not names:
        raise RuntimeError("no DVT file in listing for {} (stamp attempt: {})".format(star, first))
    path = os.path.join(cache_dir, names[-1])
    if not (os.path.isfile(path) and os.path.getsize(path) > 10000):
        http_to_file(DVT_DIR.format(star[:4], star) + names[-1], path, tries=2)
    return path, "listing:" + names[-1]


def read_dvt(path):
    """({pn: {'tperiod', 'span', 'init', 'white'}}, {'pdc', 'resid'}): sorted finite times rounded to 1e-5 d."""
    import numpy as np
    from astropy.io import fits
    tces, stat = {}, {}
    with fits.open(path, memmap=False) as h:
        for hdu in h[1:]:
            cols = getattr(hdu, "columns", None)
            if cols is None or "TIME" not in cols.names:
                continue
            d = hdu.data
            t = np.asarray(d["TIME"], dtype=float)
            ft = np.isfinite(t)

            def times(col):
                if col not in cols.names:
                    return []
                v = np.asarray(d[col], dtype=float)
                return sorted(round(float(x), 5) for x in t[ft & np.isfinite(v)])

            n = tce_number(hdu.name)
            if n is not None:
                tces[n] = {"tperiod": float(hdu.header.get("TPERIOD", float("nan"))),
                           "span": (float(t[ft].min()), float(t[ft].max())) if ft.any() else None,
                           "init": times("LC_INIT"), "white": times("MODEL_WHITE")}
            elif hdu.name.strip().upper() == "STATISTICS":
                stat = {"pdc": times("PDCSAP_FLUX"), "resid": times("RESIDUAL_LC")}
    return tces, stat


def base_row(r):
    return {"kic": r["kic"], "pn": r["pn"], "n_plan": r["n_plan"], "period": r["period"], "duration": r["duration"],
            "ntrans": r["ntrans"], "nrealt": r["nrealt"], "ngoodt": r["ngoodt"], "iflags": list(r["iflags"]),
            "mes": r["mes"], "new_mes": r["new_mes"], "status": "", "tperiod": "", "events_in_span": "",
            "half_hour": int(is_half_hour(r["duration"])), "white_cadences": ""}


def scan_star(kic, star_rows, cache_dir, partial_rows):
    """Scored rows for one star's TCEs; partial-coverage events are appended to partial_rows."""
    star = "{:09d}".format(kic)
    out = []
    try:
        path, how = fetch_dvt(star, cache_dir)
        tces, stat = read_dvt(path)
    except Exception as e:
        for r in star_rows:
            row = base_row(r)
            row["status"] = "no_dvt"
            out.append(row)
        return out, repr(e)[:200]
    for r in sorted(star_rows, key=lambda x: x["pn"]):
        row = base_row(r)
        ext = tces.get(r["pn"])
        if ext is None or ext["span"] is None:
            row["status"] = "no_ext"
        elif not abs(ext["tperiod"] - r["period"]) <= PERIOD_RTOL * r["period"]:
            row["status"] = "period_mismatch"
            row["tperiod"] = ext["tperiod"]
        elif not stat:
            row["status"] = "no_statistics"
        else:
            sources = {"init": ext["init"], "white": ext["white"], "pdc": stat["pdc"], "resid": stat["resid"]}
            mids = events_in_span(r["epoch"], r["period"], ext["span"][0], ext["span"][1])
            events = [event_coverage(sources, t, r["duration"]) for t in mids]
            row.update(tce_counts(events))
            row.update({"status": "ok", "tperiod": ext["tperiod"], "events_in_span": len(mids),
                        "white_cadences": len(ext["white"])})
            for m, (t, e) in enumerate(zip(mids, events), start=1):
                if is_real(e) and min(e["cov2"].values()) < PARTIAL_BELOW:
                    rec = {"kic": kic, "pn": r["pn"], "event": m, "t_mid": round(t, 5), "iflag0": r["iflags"][0]}
                    for w in WINDOWS:
                        for s in SOURCES:
                            rec["cov{}_{}".format(w, s)] = round(e["cov{}".format(w)][s], 4)
                    partial_rows.append(rec)
        out.append(row)
    return out, how


def read_gate_files(sample_path, note_path):
    """(published sample object or None, note text or '') from the files the job fetched before this step."""
    sample, note = None, ""
    if sample_path and os.path.isfile(sample_path):
        with open(sample_path, "r", encoding="utf-8") as f:
            sample = json.load(f)
    if note_path and os.path.isfile(note_path):
        with open(note_path, "r", encoding="utf-8", errors="replace") as f:
            note = f.read()
    return sample, note


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--cache-dir", default="cache")
    ap.add_argument("--reserve", action="store_true", help="pre-registered P1/P2 test on the reserve stars")
    ap.add_argument("--published-sample", default="", help="reserve mode: the published sample.json (gate)")
    ap.add_argument("--gate-note", default="", help="reserve mode: the published pre-registration note (gate)")
    args = ap.parse_args(argv)
    out_dir = writable_dir(args.out_dir)
    cache_dir = writable_dir(args.cache_dir)
    mode = "reserve" if args.reserve else "development"
    summary = {"tool": "scan_rubble", "version": VERSION, "mode": mode, "status": "running",
               "hypothesis": "P1 and P2, pre-registered" if args.reserve else "none (exploratory)",
               "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    res, decisions = None, None
    try:
        rows, prov = load_rv_input(cache_dir)
        summary["robovetter_input"] = prov
        by_star = {}
        for r in rows:
            by_star.setdefault(r["kic"], []).append(r)
        dev, reserve = draw_sample(by_star.keys())
        with open(os.path.join(out_dir, "sample.json"), "w", encoding="utf-8") as f:
            json.dump({"seed": SEED, "eligible_stars": len(set(by_star) - set(LOOKED_UP)), "excluded": list(LOOKED_UP),
                       "development": dev, "reserve_never_downloaded": reserve}, f, indent=1)
        print(json.dumps({"input": prov, "dev": len(dev), "reserve": len(reserve)}), flush=True)

        if args.reserve:
            sample, note = read_gate_files(args.published_sample, args.gate_note)
            ok, reasons = check_gate(sample, dev, reserve, note)
            summary["gate"] = {"ok": ok, "reasons": reasons, "published_sample": args.published_sample,
                               "gate_note": args.gate_note}
            print(json.dumps({"gate": summary["gate"]}), flush=True)
            if not ok:
                raise RuntimeError("gate failed, no reserve star downloaded: " + "; ".join(reasons))
            stars = reserve
        else:
            stars = dev

        # regression controls (looked up by the probe; not part of the sample statistics)
        controls = []
        for kic, pn, real_exp, fail_exp in CONTROLS:
            got, how = scan_star(kic, [r for r in by_star.get(kic, []) if r["pn"] == pn], cache_dir, [])
            g = got[0] if got else {}
            controls.append({"kic": kic, "pn": pn, "status": g.get("status"), "real": g.get("nreal_init"),
                             "real_expected": real_exp, "fails": g.get("fail_init_2_0.75"), "fails_expected": fail_exp,
                             "ok": g.get("nreal_init") == real_exp and g.get("fail_init_2_0.75") == fail_exp})
        print(json.dumps({"controls": controls}), flush=True)

        tce_rows, partial_rows, fetched = [], [], {}
        for i, kic in enumerate(stars, start=1):
            got, how = scan_star(kic, by_star[kic], cache_dir, partial_rows)
            tce_rows.extend(got)
            fetched[str(kic)] = how
            print(json.dumps({"star": kic, "n": i, "tces": len(got), "fetched": how}), flush=True)
        scored = [r for r in tce_rows if r["status"] == "ok"]
        res = score(scored)
        with open(os.path.join(out_dir, "variants.json"), "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
        if args.reserve:
            decisions = {"tool": "scan_rubble", "version": VERSION, "mode": mode, "stars": len(stars),
                         "scored_tces": len(scored), "p1": decide_p1(scored), "p2": decide_p2(scored),
                         "pre_registration": "findings/2026-10-19-rubble-reserve-prereg.md"}
            with open(os.path.join(out_dir, "reserve.json"), "w", encoding="utf-8") as f:
                json.dump(decisions, f, indent=1)
            print(json.dumps({"p1": decisions["p1"]["status"], "p2": decisions["p2"]["status"]}), flush=True)

        fields = list(base_row(rows[0]).keys()) + ["nreal_" + s for s in SOURCES] + ["fail_" + v for v in variant_names()]
        with open(os.path.join(out_dir, "tces.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, restval="")
            w.writeheader()
            for r in tce_rows:
                w.writerow(dict(r, iflags="".join(str(x) for x in r["iflags"])))
        ev_fields = ["kic", "pn", "event", "t_mid", "iflag0"] + ["cov{}_{}".format(w, s) for w in WINDOWS for s in SOURCES]
        with open(os.path.join(out_dir, "events.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=ev_fields)
            w.writeheader()
            w.writerows(partial_rows)

        statuses = {}
        for r in tce_rows:
            statuses[r["status"]] = statuses.get(r["status"], 0) + 1
        summary.update({"dev_stars": len(dev), "reserve_stars": len(reserve), "scanned_stars": len(stars),
                        "tces": len(tce_rows), "scored_tces": len(scored), "status_counts": statuses,
                        "partial_events": len(partial_rows), "iflag0_in_scored": sum(r["iflags"][0] for r in scored),
                        "rubble_only_in_scored": sum(1 for r in scored if r["iflags"][0] == 1 and sum(r["iflags"]) == 1),
                        "controls": controls, "fetched": fetched,
                        "checks": {"rv_rows_ok": prov["rows"] == RV_ROWS, "rv_sha256_ok": prov["sha256"] == RV_SHA256,
                                   "controls_ok": all(c["ok"] for c in controls),
                                   "sample_size_ok": len(dev) == N_DEV and len(reserve) == N_RESERVE,
                                   "no_dev_star_scanned": not (set(stars) & set(dev)) if args.reserve else True}})
        if decisions:
            summary["decisions"] = {"p1": decisions["p1"]["status"], "p2": decisions["p2"]["status"]}
        summary["status"] = "done"
    except Exception as e:
        summary["status"] = "error"
        summary["error"] = repr(e)[:500]
        summary["traceback"] = traceback.format_exc()[-3000:]
    summary["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, default=str)
    write_report(out_dir, summary, res, decisions)
    print(json.dumps({"status": summary["status"], "checks": summary.get("checks")}), flush=True)
    return 0 if summary["status"] == "done" else 1


def write_report(out_dir, summary, res, decisions=None):
    lines = ["# scan_rubble {} report ({} mode)".format(VERSION, summary.get("mode")), "",
             "Status: {}.".format(summary.get("status")), ""]
    if "gate" in summary:
        lines += ["Gate: " + json.dumps(summary["gate"]), ""]
    if "checks" in summary:
        lines += ["Checks: " + json.dumps(summary["checks"]), "",
                  "Stars scanned: {}; TCEs: {}; scored: {}; iflag0 among scored: {}; Rubble-only among scored: {}."
                  .format(summary["scanned_stars"], summary["tces"], summary["scored_tces"],
                          summary["iflag0_in_scored"], summary["rubble_only_in_scored"]), ""]
    if decisions:
        p1, p2 = decisions["p1"], decisions["p2"]
        lines += ["## Pre-registered decisions", "",
                  "P1 (empty MODEL_WHITE iff half-hour duration): **{}**. Table a/b/c/d = {}/{}/{}/{}, skipped {}; "
                  "n = {}, half-hour = {}, off-diagonal = {}.".format(
                      p1["status"], p1["table"]["a"], p1["table"]["b"], p1["table"]["c"], p1["table"]["d"],
                      p1["table"]["skipped"], p1["n"], p1["half_hour"], p1["off_diagonal"]),
                  "P2 ({} recall >= 0.9 and precision <= 0.8): **{}**. tp/fp/fn/tn = {}/{}/{}/{}; "
                  "recall_ok = {}, precision_ok = {}.".format(
                      p2["variant"], p2["status"], p2["confusion"]["tp"], p2["confusion"]["fp"],
                      p2["confusion"]["fn"], p2["confusion"]["tn"], p2["recall_ok"], p2["precision_ok"]), ""]
    if res:
        lines += ["Real events vs nrealt (TCEs): " + json.dumps(res["nreal"]), "",
                  "| variant | tp | fp | fn | tn | Rubble-only exact / n |", "|---|---|---|---|---|---|"]
        for v in variant_names():
            a = res["variants"][v]["all"]
            ro = res["variants"][v]["rubble_only"]
            lines.append("| {} | {} | {} | {} | {} | {} / {} |".format(v, a["tp"], a["fp"], a["fn"], a["tn"],
                                                                     ro["exact"], ro["n"]))
        lines.append("")
    if "error" in summary:
        lines += ["Error: " + summary["error"], ""]
    lines += ["Details: variants.json (also split by pn), tces.csv, events.csv, sample.json"
              + (", reserve.json" if decisions else "") + ". Made with AI agents; MV2, Munim, Inc., mv2@munimtech.com."]
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def writable_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".probe")
        with open(probe, "w") as f:
            f.write("x")
        os.remove(probe)
        return path
    except OSError:
        return tempfile.gettempdir()


if __name__ == "__main__":
    sys.exit(main())
