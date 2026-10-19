#!/usr/bin/env python3
# Apache-2.0. probe_rubble 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
"""Probe for an open re-derivation of DR25's Rubble metric (Thompson et al. 2018, ApJS 235, 38, A.3.7.1).

Rubble, per transit event: the number of Kepler cadences available in the DV time series divided by the number
expected across two transit durations (29.42 min cadence, DV-fit duration); an event with Rubble < 0.75 is not a
valid transit. The DR25 Robovetter input (github.com/nasa/kepler-robovetter, OBS) carries per TCE the counts
ntrans, nrealt, ngoodt and iflag0 = 1 when at least one event failed Rubble.

This probe does NOT test a hypothesis. It settles format questions before a pre-registration:
  1. Aggregate statistics of the OBS input: how common iflag0 is, by planet number, period and transit count, and
     how it sits against ntrans > nrealt and ngoodt < nrealt (which events Rubble is applied to).
  2. The public DV time-series files (*_dvt.fits): URL stamp, extensions, columns, where the gaps are (NaN),
     and whether later TCEs' extensions have earlier TCEs' transits removed.
  3. For five stars, per-event Rubble under three cadence sources (long-cadence PDCSAP, DVT LC_INIT,
     DVT LC_DETREND), next to the input's counts and flags. These five stars are thereby looked up and must be
     excluded from any later scored sample.
  4. A self-check: the two stars of skye_apply 0.1.0 must give 128,918 valid long-cadence cadences again.

Outputs (--out-dir): summary.json, obs_iflag_stats.json, dvt_probe.json, events.csv, report.md.
Pure Python plus numpy/astropy for FITS. Network: MAST and raw/media GitHub only.
"""
import argparse
import bisect
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
import tarfile
import tempfile
import time
import traceback
import urllib.request

VERSION = "0.1.0"
UA = "mv2-probe-rubble/0.1 (Munim, Inc.; mv2@munimtech.com)"
RV = "https://raw.githubusercontent.com/nasa/kepler-robovetter/master/{}"
RV_MEDIA = "https://media.githubusercontent.com/media/nasa/kepler-robovetter/master/{}"
RV_INPUT = "kplr_dr25_obs_robovetter_input.tar.gz"
RV_HEADER_LINES = 223
LC = "https://archive.stsci.edu/missions/kepler/lightcurves/{0}/{1}/kplr{1}-{2}_llc.fits"
DVT_DIR = "https://archive.stsci.edu/missions/kepler/dv_files/{0}/{1}/"
DVT_STAMP = "20160209194854"  # DR25 DV products (to be confirmed by this probe)
LC_STAMPS = ("2009166043257", "2009259160929", "2009350155506", "2010078095331", "2010174085026", "2010265121752",
             "2010355172524", "2011073133259", "2011177032512", "2011271113734", "2012004120508", "2012088054726",
             "2012179063303", "2012277125453", "2013011073258", "2013098041711", "2013131215648")
SELFCHECK_STARS = ("009018021", "006359929")
SELFCHECK_VALID = 128918  # skye_diag 0.1.0, skye_inv 0.1.0 and skye_apply 0.1.0: the same 34 files
PROBE_STARS = ("006359929", "006034834", "011446443", "011442793", "006922244")
CADENCE_MIN = 29.4244  # Kepler long cadence in minutes (Thompson et al. 2018 quote 29.42)
RUBBLE_THRESHOLD = 0.75
# 0-based columns of the Robovetter input, as Kepler-RoboVetter-DR25.cpp reads them
COL = {"kic": 2, "pn": 3, "n_plan": 4, "ntrans": 5, "nrealt": 6, "ngoodt": 7, "iflag0": 8, "period": 26,
       "epoch": 28, "duration": 30, "mes": 39, "new_mes": 41}
N_IFLAGS = 6
PERIOD_BINS = ((0.0, 10.0, "P<10d"), (10.0, 45.0, "10-45d"), (45.0, 200.0, "45-200d"), (200.0, 1e9, "P>200d"))
NTRANS_BINS = ((0, 5, "ntrans3-5"), (6, 20, "ntrans6-20"), (21, 100, "ntrans21-100"), (101, 10 ** 9, "ntrans>100"))


# ---------- pure functions (tested) ----------

def expected_cadences(duration_hours, n_durations=2.0, cadence_min=CADENCE_MIN):
    """Cadences expected across n_durations transit durations."""
    return n_durations * duration_hours * 60.0 / cadence_min


def count_within(valid, t, half_width):
    """Number of sorted times in valid with |x - t| <= half_width."""
    lo = bisect.bisect_left(valid, t - half_width)
    hi = bisect.bisect_right(valid, t + half_width)
    return hi - lo


def rubble(valid, t_mid, duration_hours, n_durations=2.0):
    """Available cadences within n_durations/2 durations either side of t_mid, over those expected."""
    half = n_durations * duration_hours / 24.0 / 2.0
    exp = expected_cadences(duration_hours, n_durations)
    return count_within(valid, t_mid, half) / exp if exp > 0 else float("nan")


def events_in_span(t0, period, t_min, t_max):
    """Mid-times t0 + n*period inside [t_min, t_max], in order."""
    if period <= 0:
        return []
    n0 = math.ceil((t_min - t0) / period)
    out = []
    n = n0
    while t0 + n * period <= t_max:
        out.append(t0 + n * period)
        n += 1
    return out


def trans_gapped(nrealt, ntrans):
    """DR25's TRANS_GAPPED rule: nrealt/ntrans <= 0.5 (Kepler-RoboVetter-DR25.cpp)."""
    return ntrans > 0 and nrealt / ntrans <= 0.5


def label(value, bins):
    for lo, hi, name in bins:
        if lo <= value <= hi if isinstance(lo, int) else lo < value <= hi:
            return name
    return "other"


def parse_rv_line(line):
    """One data row of the IPAC Robovetter input -> dict, or None for header / malformed lines."""
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


def iflag_stats(rows):
    """Aggregate counts over parsed input rows (integers only; ratios are left to the reader)."""
    n = len(rows)
    st = {"rows": n, "iflag_any": [0] * N_IFLAGS, "iflag0_by_pn": {"pn1": [0, 0], "pn>1": [0, 0]},
          "iflag0_by_period": {}, "iflag0_by_ntrans": {}, "ntrans_gt_nrealt": [0, 0], "ngoodt_lt_nrealt": [0, 0],
          "ngoodt_lt_nrealt_no_iflag": 0, "ngoodt_gt_nrealt": 0, "trans_gapped": 0,
          "rubble_only_flag": {"tces": 0, "removed_hist": {}}, "ngoodt_lt3": 0, "new_mes_lt_7p1": 0,
          "indiv_trans_fail": 0, "iflag0_and_ntrans_eq_nrealt": 0}
    for r in rows:
        fl = r["iflags"]
        for i in range(N_IFLAGS):
            st["iflag_any"][i] += fl[i]
        key = "pn1" if r["pn"] == 1 else "pn>1"
        st["iflag0_by_pn"][key][0] += fl[0]
        st["iflag0_by_pn"][key][1] += 1
        pl = label(r["period"], PERIOD_BINS)
        st["iflag0_by_period"].setdefault(pl, [0, 0])
        st["iflag0_by_period"][pl][0] += fl[0]
        st["iflag0_by_period"][pl][1] += 1
        nl = label(r["ntrans"], NTRANS_BINS)
        st["iflag0_by_ntrans"].setdefault(nl, [0, 0])
        st["iflag0_by_ntrans"][nl][0] += fl[0]
        st["iflag0_by_ntrans"][nl][1] += 1
        gap = r["ntrans"] > r["nrealt"]
        st["ntrans_gt_nrealt"][0] += fl[0] if gap else 0
        st["ntrans_gt_nrealt"][1] += 1 if gap else 0
        if fl[0] and not gap:
            st["iflag0_and_ntrans_eq_nrealt"] += 1
        lost = r["ngoodt"] < r["nrealt"]
        st["ngoodt_lt_nrealt"][0] += fl[0] if lost else 0
        st["ngoodt_lt_nrealt"][1] += 1 if lost else 0
        if lost and not any(fl):
            st["ngoodt_lt_nrealt_no_iflag"] += 1
        if r["ngoodt"] > r["nrealt"]:
            st["ngoodt_gt_nrealt"] += 1
        if trans_gapped(r["nrealt"], r["ntrans"]):
            st["trans_gapped"] += 1
        if fl[0] == 1 and sum(fl) == 1:
            st["rubble_only_flag"]["tces"] += 1
            k = str(r["nrealt"] - r["ngoodt"])
            st["rubble_only_flag"]["removed_hist"][k] = st["rubble_only_flag"]["removed_hist"].get(k, 0) + 1
        if r["ngoodt"] < 3:
            st["ngoodt_lt3"] += 1
        if r["new_mes"] < 7.1:
            st["new_mes_lt_7p1"] += 1
        if r["ngoodt"] < 3 or r["new_mes"] < 7.1:
            st["indiv_trans_fail"] += 1
    return st


def dvt_names_from_listing(html):
    """DVT file names found in a MAST directory listing."""
    return sorted(set(re.findall(r"kplr\d{9}-\d{14}_dvt\.fits", html)))


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
    """Cached kepler-robovetter file (git-lfs pointers are followed), as skye_census 0.2.1 did."""
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


def lc_valid_times(star, cache_dir):
    """(sorted valid cadence times, per-file info) for one star: finite TIME and PDCSAP_FLUX; missing files skipped."""
    import numpy as np
    from astropy.io import fits
    times, info = set(), []
    for stamp in LC_STAMPS:
        url = LC.format(star[:4], star, stamp)
        path = os.path.join(cache_dir, os.path.basename(url))
        if not (os.path.isfile(path) and os.path.getsize(path) > 10000):
            try:
                http_to_file(url, path, tries=2)
            except Exception as e:
                info.append({"file": os.path.basename(url), "error": repr(e)[:200]})
                continue
        with fits.open(path, memmap=False) as h:
            d = h[1].data
            t = np.asarray(d["TIME"], dtype=float)
            f = np.asarray(d["PDCSAP_FLUX"], dtype=float)
            ok = np.isfinite(t) & np.isfinite(f)
            times.update(round(float(x), 5) for x in t[ok])
            info.append({"file": os.path.basename(url), "quarter": h[0].header.get("QUARTER"),
                         "cadences": int(len(t)), "valid": int(ok.sum())})
    return sorted(times), info


def fetch_dvt(star, cache_dir):
    """(path, how) of the star's DVT file: the DR25 stamp first, then the directory listing."""
    url = DVT_DIR.format(star[:4], star) + "kplr{}-{}_dvt.fits".format(star, DVT_STAMP)
    path = os.path.join(cache_dir, os.path.basename(url))
    if os.path.isfile(path) and os.path.getsize(path) > 10000:
        return path, "cached"
    try:
        http_to_file(url, path, tries=2)
        return path, "stamp"
    except Exception as e:
        first = repr(e)[:120]
    html = http_bytes(DVT_DIR.format(star[:4], star), tries=2).decode("utf-8", "replace")
    names = dvt_names_from_listing(html)
    if not names:
        raise RuntimeError("no DVT file in listing for {} (stamp attempt: {})".format(star, first))
    name = names[-1]
    path = os.path.join(cache_dir, name)
    http_to_file(DVT_DIR.format(star[:4], star) + name, path, tries=2)
    return path, "listing:" + name


def dvt_probe(path):
    """Structure of a DVT file and, per extension with TIME, sorted finite-time lists for each float column."""
    import numpy as np
    from astropy.io import fits
    out = {"file": os.path.basename(path), "bytes": os.path.getsize(path), "extensions": []}
    series = {}
    with fits.open(path, memmap=False) as h:
        for i, hdu in enumerate(h):
            ext = {"index": i, "name": hdu.name, "type": type(hdu).__name__}
            hdr = hdu.header
            for key in ("TCE_NUM", "TCEPLNUM", "TPERIOD", "TEPOCH", "TDUR", "TDEPTH", "TSNR", "NTRANS",
                        "MAXMES", "MAXSES", "NUMTCES", "DATA_REL", "QUARTER", "KEPLERID"):
                if key in hdr:
                    ext[key] = hdr[key] if isinstance(hdr[key], (int, float, str)) else str(hdr[key])
            cols = getattr(hdu, "columns", None)
            if cols is not None and "TIME" in cols.names:
                ext["columns"] = list(cols.names)
                d = hdu.data
                t = np.asarray(d["TIME"], dtype=float)
                ext["rows"] = int(len(t))
                ext["time_finite"] = int(np.isfinite(t).sum())
                ext["time_min"] = float(np.nanmin(t)) if ext["time_finite"] else None
                ext["time_max"] = float(np.nanmax(t)) if ext["time_finite"] else None
                ext["finite"] = {}
                per_col = {}
                for c in cols.names:
                    if c == "TIME":
                        continue
                    try:
                        v = np.asarray(d[c], dtype=float)
                    except (TypeError, ValueError):
                        continue
                    if v.ndim != 1:
                        continue
                    ok = np.isfinite(t) & np.isfinite(v)
                    ext["finite"][c] = int(ok.sum())
                    if c in ("LC_INIT", "LC_DETREND", "LC_WHITE"):
                        per_col[c] = sorted(round(float(x), 5) for x in t[ok])
                series[(i, hdu.name)] = per_col
            out["extensions"].append(ext)
    return out, series


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--cache-dir", default="cache")
    args = ap.parse_args(argv)
    out_dir = writable_dir(args.out_dir)
    cache_dir = writable_dir(args.cache_dir)
    summary = {"tool": "probe_rubble", "version": VERSION, "status": "running", "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        rows, prov = load_rv_input(cache_dir)
        summary["robovetter_input"] = prov
        stats = iflag_stats(rows)
        with open(os.path.join(out_dir, "obs_iflag_stats.json"), "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=1)
        summary["obs_rows"] = len(rows)
        summary["iflag_any"] = stats["iflag_any"]
        by_star = {}
        for r in rows:
            by_star.setdefault(r["kic"], []).append(r)
        print(json.dumps({"input": prov, "iflag_any": stats["iflag_any"]}), flush=True)

        # self-check: the two stars of skye_apply 0.1.0
        lc = {}
        total = 0
        lc_info = {}
        for star in SELFCHECK_STARS:
            lc[star], lc_info[star] = lc_valid_times(star, cache_dir)
            total += len(lc[star])
        summary["selfcheck"] = {"valid_cadences": total, "expected": SELFCHECK_VALID, "ok": total == SELFCHECK_VALID}
        print(json.dumps({"selfcheck": summary["selfcheck"]}), flush=True)

        # DVT probe and per-event Rubble for the probe stars
        dvt = {}
        event_rows = []
        for star in PROBE_STARS:
            kic = int(star)
            entry = {"kic": kic, "input_tces": sorted((r["pn"], r["ntrans"], r["nrealt"], r["ngoodt"], r["iflags"][0])
                                                     for r in by_star.get(kic, []))}
            try:
                path, how = fetch_dvt(star, cache_dir)
                entry["fetched"] = how
                structure, series = dvt_probe(path)
                entry["structure"] = structure
            except Exception as e:
                entry["error"] = repr(e)[:300]
                dvt[star] = entry
                continue
            if star not in lc:
                lc[star], lc_info[star] = lc_valid_times(star, cache_dir)
            # map DVT extensions to planet numbers by order of TIME-bearing extensions (TCE_1, TCE_2, ...)
            tce_exts = [(k, v) for k, v in series.items() if v]
            tce_exts.sort(key=lambda kv: kv[0][0])
            entry["tce_extensions"] = [k[1] for k, _ in tce_exts]
            for j, (key, per_col) in enumerate(tce_exts, start=1):
                inp = next((r for r in by_star.get(kic, []) if r["pn"] == j), None)
                if inp is None:
                    continue
                sources = {"llc": lc[star]}
                sources.update({"dvt_" + c.lower(): v for c, v in per_col.items()})
                span_src = sources.get("dvt_lc_init") or lc[star]
                if not span_src:
                    continue
                t_min, t_max = span_src[0], span_src[-1]
                mids = events_in_span(inp["epoch"], inp["period"], t_min, t_max)
                good = {name: 0 for name in sources}
                for m, t in enumerate(mids, start=1):
                    rec = {"kic": kic, "pn": j, "event": m, "t_mid": round(t, 5), "period": inp["period"],
                           "duration_h": inp["duration"], "ntrans": inp["ntrans"], "nrealt": inp["nrealt"],
                           "ngoodt": inp["ngoodt"], "iflag0": inp["iflags"][0]}
                    for name, valid in sources.items():
                        r2 = rubble(valid, t, inp["duration"], 2.0)
                        r1 = rubble(valid, t, inp["duration"], 1.0)
                        rec["rubble2_" + name] = round(r2, 4)
                        rec["intransit_" + name] = round(r1, 4)
                        good[name] += 1 if r2 >= RUBBLE_THRESHOLD else 0
                    event_rows.append(rec)
                entry.setdefault("per_tce", []).append({"pn": j, "ext": key[1], "events_in_span": len(mids),
                                                        "good_by_source": good, "input": {k: inp[k] for k in
                                                        ("ntrans", "nrealt", "ngoodt", "period", "epoch", "duration")},
                                                        "iflags": inp["iflags"]})
            dvt[star] = entry
            print(json.dumps({"star": star, "fetched": how, "tces": len(tce_exts)}), flush=True)
        with open(os.path.join(out_dir, "dvt_probe.json"), "w", encoding="utf-8") as f:
            json.dump({"dvt": dvt, "lc_files": lc_info}, f, indent=1, default=str)
        fields = sorted({k for r in event_rows for k in r}, key=lambda k: (k not in ("kic", "pn", "event", "t_mid"), k))
        with open(os.path.join(out_dir, "events.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(event_rows)
        summary["event_rows"] = len(event_rows)
        summary["dvt_fetched"] = {s: dvt[s].get("fetched", dvt[s].get("error", "")) for s in dvt}
        summary["status"] = "done"
    except Exception as e:
        summary["status"] = "error"
        summary["error"] = repr(e)[:500]
        summary["traceback"] = traceback.format_exc()[-3000:]
    summary["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, default=str)
    write_report(out_dir, summary)
    print(json.dumps({"status": summary["status"]}), flush=True)
    return 0 if summary["status"] == "done" else 1


def write_report(out_dir, summary):
    lines = ["# probe_rubble {} report".format(VERSION), "",
             "Status: {}.".format(summary.get("status")), ""]
    if "iflag_any" in summary:
        lines += ["OBS input rows: {}. TCEs with at least one event failing each metric (Rubble, Chases, Marshall, "
                  "Skye, Zuma, Tracker): {}.".format(summary.get("obs_rows"), summary["iflag_any"]), ""]
    if "selfcheck" in summary:
        lines += ["Self-check (two stars of skye_apply 0.1.0): {} valid cadences, expected {}, ok = {}.".format(
            summary["selfcheck"]["valid_cadences"], summary["selfcheck"]["expected"], summary["selfcheck"]["ok"]), ""]
    if "dvt_fetched" in summary:
        lines += ["DVT files: " + json.dumps(summary["dvt_fetched"]), ""]
    if "error" in summary:
        lines += ["Error: " + summary["error"], ""]
    lines += ["Details: obs_iflag_stats.json, dvt_probe.json, events.csv. Made with AI agents; "
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
