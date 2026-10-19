#!/usr/bin/env python3
# Apache-2.0. scan_rubble 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
"""Exploratory development scan for an open re-derivation of DR25's Rubble metric (Thompson et al. 2018, A.3.7.1).

rubble-probe-v1 (probe_rubble 0.1.0) found on nine TCEs that events with any finite DVT LC_INIT cadence in transit
reproduce the Robovetter input's nrealt for 6 of 9 TCEs, but the literal Rubble rule (cadences in two durations over
those expected, below 0.75) flags 3 of the 7 TCEs whose iflag0 is 0. This scan does NOT test a hypothesis. On a
seeded development sample of OBS stars it tabulates, per TCE, how well each candidate variant reproduces nrealt,
iflag0 and, for TCEs whose only per-event flag is Rubble, nrealt - ngoodt. One variant is then fixed in writing
and pre-registered before the reserve stars are scored; this tool lists the reserve but never downloads it.

Variants: cadence source x window x threshold.
  sources     init   finite LC_INIT of the TCE's own DVT extension (earlier TCEs' transits removed)
              white  finite MODEL_WHITE of the same extension (more cadences than LC_INIT; possibly gap-filled ones)
              pdc    finite PDCSAP_FLUX of the DVT Statistics extension (per star)
              resid  finite RESIDUAL_LC of the Statistics extension (per star)
  windows     1 or 2 transit durations centred on mid-transit
  thresholds  0.25, 0.5, 0.75 (DR25's stated value)
For every variant, a real event has at least one finite LC_INIT cadence within half a duration of mid-transit.

Outputs (--out-dir): summary.json, sample.json, tces.csv, events.csv (events with partial coverage), variants.json,
report.md. Pure Python plus numpy/astropy for FITS. Network: MAST and raw/media GitHub only.
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

VERSION = "0.1.0"
UA = "mv2-scan-rubble/0.1 (Munim, Inc.; mv2@munimtech.com)"
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


def score(rows):
    """Agreement with DR25 over scored TCE rows (dicts with pn, nrealt, ngoodt, iflags and the tce_counts keys)."""
    res = {"n": len(rows), "nreal": {}, "variants": {}}
    for s in SOURCES:
        d = [r["nreal_" + s] - r["nrealt"] for r in rows]
        res["nreal"][s] = {"exact": sum(1 for x in d if x == 0), "within1": sum(1 for x in d if abs(x) <= 1),
                           "over": sum(1 for x in d if x > 1), "under": sum(1 for x in d if x < -1)}
    for v in variant_names():
        conf = {"all": [0, 0, 0, 0], "pn1": [0, 0, 0, 0], "pn>1": [0, 0, 0, 0]}  # tp, fp, fn, tn
        ro = [0, 0, 0]  # Rubble-only TCEs: n, exact, within 1
        for r in rows:
            pred = r["fail_" + v] > 0
            truth = r["iflags"][0] == 1
            k = 0 if pred and truth else 1 if pred else 2 if truth else 3
            conf["all"][k] += 1
            conf["pn1" if r["pn"] == 1 else "pn>1"][k] += 1
            if truth and sum(r["iflags"]) == 1:
                diff = r["fail_" + v] - (r["nrealt"] - r["ngoodt"])
                ro[0] += 1
                ro[1] += 1 if diff == 0 else 0
                ro[2] += 1 if abs(diff) <= 1 else 0
        res["variants"][v] = {key: dict(zip(("tp", "fp", "fn", "tn"), val)) for key, val in conf.items()}
        res["variants"][v]["rubble_only"] = {"n": ro[0], "exact": ro[1], "within1": ro[2]}
    return res


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
            "mes": r["mes"], "new_mes": r["new_mes"], "status": "", "tperiod": "", "events_in_span": ""}


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
            row.update({"status": "ok", "tperiod": ext["tperiod"], "events_in_span": len(mids)})
            for m, (t, e) in enumerate(zip(mids, events), start=1):
                if is_real(e) and min(e["cov2"].values()) < PARTIAL_BELOW:
                    rec = {"kic": kic, "pn": r["pn"], "event": m, "t_mid": round(t, 5), "iflag0": r["iflags"][0]}
                    for w in WINDOWS:
                        for s in SOURCES:
                            rec["cov{}_{}".format(w, s)] = round(e["cov{}".format(w)][s], 4)
                    partial_rows.append(rec)
        out.append(row)
    return out, how


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--cache-dir", default="cache")
    args = ap.parse_args(argv)
    out_dir = writable_dir(args.out_dir)
    cache_dir = writable_dir(args.cache_dir)
    summary = {"tool": "scan_rubble", "version": VERSION, "status": "running", "hypothesis": "none (exploratory)",
               "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
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

        # regression controls (looked up by the probe; not part of the development statistics)
        controls = []
        for kic, pn, real_exp, fail_exp in CONTROLS:
            got, how = scan_star(kic, [r for r in by_star.get(kic, []) if r["pn"] == pn], cache_dir, [])
            g = got[0] if got else {}
            controls.append({"kic": kic, "pn": pn, "status": g.get("status"), "real": g.get("nreal_init"),
                             "real_expected": real_exp, "fails": g.get("fail_init_2_0.75"), "fails_expected": fail_exp,
                             "ok": g.get("nreal_init") == real_exp and g.get("fail_init_2_0.75") == fail_exp})
        print(json.dumps({"controls": controls}), flush=True)

        tce_rows, partial_rows, fetched = [], [], {}
        for i, kic in enumerate(dev, start=1):
            got, how = scan_star(kic, by_star[kic], cache_dir, partial_rows)
            tce_rows.extend(got)
            fetched[str(kic)] = how
            print(json.dumps({"star": kic, "n": i, "tces": len(got), "fetched": how}), flush=True)
        scored = [r for r in tce_rows if r["status"] == "ok"]
        res = score(scored)
        with open(os.path.join(out_dir, "variants.json"), "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)

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
        summary.update({"dev_stars": len(dev), "reserve_stars": len(reserve), "tces": len(tce_rows),
                        "scored_tces": len(scored), "status_counts": statuses, "partial_events": len(partial_rows),
                        "iflag0_in_scored": sum(r["iflags"][0] for r in scored),
                        "rubble_only_in_scored": sum(1 for r in scored if r["iflags"][0] == 1 and sum(r["iflags"]) == 1),
                        "controls": controls, "fetched": fetched,
                        "checks": {"rv_rows_ok": prov["rows"] == RV_ROWS, "rv_sha256_ok": prov["sha256"] == RV_SHA256,
                                   "controls_ok": all(c["ok"] for c in controls), "dev_size_ok": len(dev) == N_DEV}})
        summary["status"] = "done"
    except Exception as e:
        summary["status"] = "error"
        summary["error"] = repr(e)[:500]
        summary["traceback"] = traceback.format_exc()[-3000:]
        res = None
    summary["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, default=str)
    write_report(out_dir, summary, res)
    print(json.dumps({"status": summary["status"], "checks": summary.get("checks")}), flush=True)
    return 0 if summary["status"] == "done" else 1


def write_report(out_dir, summary, res):
    lines = ["# scan_rubble {} report (exploratory, no hypothesis)".format(VERSION), "",
             "Status: {}.".format(summary.get("status")), ""]
    if "checks" in summary:
        lines += ["Checks: " + json.dumps(summary["checks"]), "",
                  "Development stars: {}; TCEs: {}; scored: {}; iflag0 among scored: {}; Rubble-only among scored: {}."
                  .format(summary["dev_stars"], summary["tces"], summary["scored_tces"], summary["iflag0_in_scored"],
                          summary["rubble_only_in_scored"]), ""]
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
    lines += ["Details: variants.json (also split by pn), tces.csv, events.csv, sample.json. Made with AI agents; "
              "MV2, Munim, Inc., mv2@munimtech.com."]
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
