"""skye_apply: the open Skye re-implementation, validated on DR25's inverted run, applied to long-period KOIs.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library, plus astropy and numpy to read the
Kepler light curves.
Pre-registration: findings/2026-10-19-skye-apply-prereg.md in munimtechnologies/exoplanet-archive-audit. It also
amends findings/2026-10-18-skye-v3-robnik-crosscheck-prereg.md (the cross-check now uses this variant's would_fail).

skye_inv 0.1.0 tested the variant scored_only_real_events_w0.25_data_bins on DR25's inverted run (INV), whose Skye
flags had never been opened, and all five pre-registered predictions held (findings/2026-10-19-skye-inv-results.md).
This job freezes that variant and applies it to the KOIs of skye-census-v3:
  bins    per skygroup, the events of the DR25 OBS TCEs with P > 45 d that are in the DR25 Robovetter input
          (v3's published tce_skye.csv, rv_found = 1);
  events  t0 + n P inside the star's long-cadence quarters, kept only within 0.25 d of a valid cadence (finite TIME
          and PDCSAP_FLUX) in the Q1-Q17 files of KIC 9018021 or KIC 6359929;
  rate    over the bins of the skygroup's quarters that hold a valid cadence; Skye.py's cutoff R + 3 sqrt(R), 5 passes.
Per KOI (v3's koi_skye.csv, cumulative table, P > 45 d): kept events, kept events in a bad bin of its skygroup
("flagged"), good = kept - flagged, eligible = kept >= 3, would_fail = eligible and good < 3.
Order of work: (1) the pre-registration must be live on GitHub and the repository's skye_apply.py must match this
file; (2) the frozen variant is re-run on OBS and must reproduce skye_diag's counts exactly, both through
run_variant and through the bad bins this job applies to the KOIs; only then (3) are the KOIs scored and joined with
Robnik et al.'s list. A failure at (1) or (2) stops the job before (3).
fnum, events, bin_index, rate_bins, skye_bins, confusion, f1, load_tces, load_skygroups, near, data_bins,
run_variant, same_text, gate, http_bytes, http_to_file, read_source, lc_valid_times and writable_dir are copied
unchanged from skye_inv 0.1.0; binom_tail, group_stats and census_test from skye_census 0.2.1; koi_name, read_table,
robnik_names, planets_per_star, population, fisher_greater, compare and scored from robnik_crosscheck 0.1.0.

Usage: python skye_apply.py --out-dir /out/apply [--cache-dir /data]
"""
import argparse
import bisect
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import sys
import tempfile
import time
import urllib.request

VERSION = "0.1.0"
REPO = "https://raw.githubusercontent.com/munimtechnologies/exoplanet-archive-audit/main/{}"
PREREG = "findings/2026-10-19-skye-apply-prereg.md"
SELF = "skye_apply.py"
OBS_TCES = REPO.format("results/2026-10-18-skye-census-0.2.1/tce_skye.csv")
OBS_SKYGROUPS = REPO.format("results/2026-10-18-skye-census-0.2.1/skygroups.csv")
KOI_SKYE = REPO.format("results/2026-10-18-skye-census-0.2.1/koi_skye.csv")
CUMULATIVE_URL = REPO.format("results/2026-10-18-skye-census-0.1.0/tap/cumulative.csv")
CUMULATIVE_SHA256 = "df551272c3e8a945fed88c23129328b0d070c224f6cf503048b5f88e88e89286"
ROBNIK_URL = "https://raw.githubusercontent.com/JakobRobnik/exo-probability/main/results/unrecovered_candidates.csv"
LC = "https://archive.stsci.edu/missions/kepler/lightcurves/{0}/{1}/kplr{1}-{2}_llc.fits"
LC_STARS = ("009018021", "006359929")
# Q1-Q17 long-cadence file stamps, the same for both stars (MAST directory listings, read 2026-10-18)
LC_STAMPS = ("2009166043257", "2009259160929", "2009350155506", "2010078095331", "2010174085026", "2010265121752",
             "2010355172524", "2011073133259", "2011177032512", "2011271113734", "2012004120508", "2012088054726",
             "2012179063303", "2012277125453", "2013011073258", "2013098041711", "2013131215648")
# Long-cadence spans (BKJD) of quarters 1-17, as in skye_census 0.2.1
QUARTERS = {1: (131.51, 164.98), 2: (169.52, 258.47), 3: (260.22, 349.50), 4: (352.38, 442.20),
            5: (443.49, 538.16), 6: (539.47, 629.30), 7: (630.20, 719.55), 8: (735.38, 802.34),
            9: (808.54, 905.93), 10: (906.87, 1000.27), 11: (1001.23, 1098.33), 12: (1099.43, 1182.02),
            13: (1182.76, 1273.00), 14: (1274.20, 1371.32), 15: (1373.51, 1471.14), 16: (1472.12, 1557.96),
            17: (1559.25, 1591.00)}
BIN0 = 131.5
N_SIGMA = 3.0
PASSES = 5
P_MIN = 45.0
WINDOW = 0.25
MIN_GOOD = 3
NAMED = ("K05269.01", "K05227.01")
# skye_diag 0.1.0's counts for the frozen variant on OBS (results/2026-10-18-skye-diag-v1/summary.json)
OBS_CHOSEN = {"tp": 3829, "fp": 1364, "fn": 446, "tn": 8313}
# Pre-registered thresholds
KOI_ROWS = 2257  # data rows of v3's koi_skye.csv
VALID_CADENCES = 128918  # skye_diag 0.1.0 and skye_inv 0.1.0, same 34 files
ROBNIK_ROWS = 406  # data rows of unrecovered_candidates.csv, read 2026-10-18
PC_FAIL_MAX = 0.10
SKYE_RECALL_MIN = 0.70
CENSUS_RATIO = 2.0
CENSUS_FLOOR = 0.02
CENSUS_P = 0.01
# Robnik cross-check, unchanged from robnik_crosscheck 0.1.0: looked up by hand before its pre-registration
EXCLUDED = {"K05269.01", "K05227.01", "K04426.01", "K05423.01", "K05398.01", "K01209.01", "K01356.01",
            "K05600.01", "K07894.01", "K08063.01", "K08107.01", "K08242.01", "K07915.01"}
RB_WINDOW = (340.0, 400.0)
N_FAIL_MIN = 10
RATIO_MIN = 2.0
P_MAX = 0.01

KOI_FIELDS = ["kepoi_name", "kepid", "disposition", "period", "t0", "skygroup", "status", "n_events", "n_kept",
              "n_flagged", "good", "eligible", "would_fail", "v3_would_fail", "in_dr25", "dr25_pc", "dr25_skye",
              "never_dr25", "events_match", "flagged_times", "kept_times"]
GROUPS = ("dr25_pc", "dr25_skye", "never_dr25")


def fnum(s):
    """float(s), or None when s is blank or not a finite number."""
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def events(p, t0, quarters, spans=QUARTERS):
    """Times t0 + n p (any integer n) inside the spans of the given quarters, ascending, rounded to 4 d.p."""
    out = []
    if not p or p <= 0:
        return out
    for q in sorted(quarters):
        if q not in spans:
            continue
        a, b = spans[q]
        n = math.ceil((a - t0) / p)
        t = t0 + n * p
        while t <= b:
            out.append(round(t, 4))
            n += 1
            t = t0 + n * p
    return sorted(out)


def bin_index(t, bin0=BIN0):
    return math.floor(t - bin0)


def rate_bins(spans=QUARTERS, bin0=BIN0):
    """Indices of the 1-d bins whose centre lies in a quarter span."""
    if not spans:
        return []
    lo = min(a for a, _ in spans.values())
    hi = max(b for _, b in spans.values())
    return [k for k in range(bin_index(lo, bin0), bin_index(hi, bin0) + 1)
            if any(a <= bin0 + k + 0.5 <= b for a, b in spans.values())]


def skye_bins(counts, bins, n_sigma=N_SIGMA, passes=PASSES):
    """(bad bins, final rate, final cutoff), as Skye.py's calcSkye. counts: bin -> events; bins: the non-gap
    bins, which enter the rate.

    R is the mean count over the rate bins and the cutoff R + n_sigma sqrt(R); then, a fixed number of passes,
    bins above the cutoff are dropped and R and the cutoff recomputed from the bins kept. Every bin with a count
    above the final cutoff is bad, inside the rate bins or not."""
    vals = [counts.get(k, 0) for k in bins]
    r = sum(vals) / len(vals) if vals else 0.0
    thr = r + n_sigma * math.sqrt(r)
    for _ in range(passes):
        vals = [v for v in vals if v <= thr]
        r = sum(vals) / len(vals) if vals else 0.0
        thr = r + n_sigma * math.sqrt(r)
    return {k for k, c in counts.items() if c > thr}, r, thr


def confusion(pairs):
    """Counts for (ours, DR25) pairs of 0/1 flags; recall = tp / (tp + fn), precision = tp / (tp + fp)."""
    tp = sum(1 for a, b in pairs if a and b)
    fp = sum(1 for a, b in pairs if a and not b)
    fn = sum(1 for a, b in pairs if not a and b)
    tn = sum(1 for a, b in pairs if not a and not b)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "recall": round(tp / (tp + fn), 4) if tp + fn else None,
            "precision": round(tp / (tp + fp), 4) if tp + fp else None}


def f1(c):
    """2 tp / (2 tp + fp + fn) from a confusion dict, or None when undefined."""
    d = 2 * c["tp"] + c["fp"] + c["fn"]
    return 2 * c["tp"] / d if d else None


def load_tces(text):
    """Rows of v3's tce_skye.csv: kepid, pn, period, t0, rv_found, and the Robovetter counts and Skye flag (None
    when the TCE is not in the Robovetter input)."""
    out = []
    for r in csv.DictReader(io.StringIO(text)):
        found = r["rv_found"] == "1"
        out.append({"kepid": int(r["kepid"]), "pn": int(r["pn"]), "period": float(r["period"]),
                    "t0": float(r["t0"]), "rv_found": found,
                    "nitrans": int(r["rv_nitrans"]) if found else None,
                    "nrealtrans": int(r["rv_nrealtrans"]) if found else None,
                    "skye": int(r["rv_skye"]) if found else None})
    return out


def load_skygroups(text):
    """{kepid: (skygroup, set of long-cadence quarters)} from v3's skygroups.csv."""
    return {int(r["kepid"]): (int(r["skygroup"]), {int(q) for q in r["lc_quarters"].split()})
            for r in csv.DictReader(io.StringIO(text))}


def near(t, valid, w):
    """True when the sorted list valid holds a time within w of t."""
    i = bisect.bisect_left(valid, t)
    return any(abs(valid[j] - t) <= w for j in (i - 1, i) if 0 <= j < len(valid))


def data_bins(valid, bin0=BIN0):
    """Indices of the bins that hold at least one valid cadence."""
    return {bin_index(t, bin0) for t in valid}


def run_variant(tces, mast, use_all=True, keep=None, only_bins=None):
    """(comparison, rows) for one variant: Skye bins as skye_census 0.2.1 builds them, then each Robovetter-scored
    TCE flagged when one of its kept events lies in a bad bin of its skygroup, against DR25's flag.
    use_all: every TCE adds its events to the bins (as v3); else only TCEs found in the Robovetter input.
    keep: event filter (t -> bool), applied to the bin counts and to each TCE's own events alike.
    only_bins: if given, the rate bins are limited to these bins.
    rows: (kept events, nitrans, nrealtrans, ours, DR25) per compared TCE."""
    keep = keep or (lambda t: True)
    sg_q = {}
    for sg, qs in mast.values():
        sg_q.setdefault(sg, set()).update(qs)
    counts, evs = {}, []
    for r in tces:
        if r["kepid"] not in mast:
            evs.append(None)
            continue
        sg, quarters = mast[r["kepid"]]
        e = [t for t in events(r["period"], r["t0"], quarters) if keep(t)]
        evs.append((sg, e))
        if use_all or r["rv_found"]:
            c = counts.setdefault(sg, {})
            for t in e:
                k = bin_index(t)
                c[k] = c.get(k, 0) + 1
    bad = {}
    for sg in sorted(counts):
        bins = rate_bins({q: QUARTERS[q] for q in sg_q.get(sg, ()) if q in QUARTERS})
        if only_bins is not None:
            bins = [k for k in bins if k in only_bins]
        bad[sg] = skye_bins(counts[sg], bins)[0]
    rows = []
    for r, x in zip(tces, evs):
        if x is None or not r["rv_found"]:
            continue
        sg, e = x
        ours = int(any(bin_index(t) in bad.get(sg, ()) for t in e))
        rows.append((len(e), r["nitrans"], r["nrealtrans"], ours, r["skye"]))
    out = confusion([(ours, dr) for _, _, _, ours, dr in rows])
    n = len(rows)
    out.update({"tces_compared": n, "bad_bins": sum(len(b) for b in bad.values()),
                "bin_events": sum(sum(c.values()) for c in counts.values()),
                "events_equal_nitrans": round(sum(1 for x in rows if x[0] == x[1]) / n, 4) if n else None,
                "events_equal_nrealtrans": round(sum(1 for x in rows if x[0] == x[2]) / n, 4) if n else None})
    return out, rows


def frozen_bins(tces, mast, keep=None, only_bins=None):
    """{skygroup: bad bins} of the frozen variant: run_variant's bins with use_all=False, returned so they can be
    applied to KOIs. Same steps as run_variant; frozen_confusion checks that they give run_variant's counts."""
    keep = keep or (lambda t: True)
    sg_q = {}
    for sg, qs in mast.values():
        sg_q.setdefault(sg, set()).update(qs)
    counts = {}
    for r in tces:
        if r["kepid"] not in mast or not r["rv_found"]:
            continue
        sg, quarters = mast[r["kepid"]]
        c = counts.setdefault(sg, {})
        for t in events(r["period"], r["t0"], quarters):
            if keep(t):
                c[bin_index(t)] = c.get(bin_index(t), 0) + 1
    bad = {}
    for sg in sorted(counts):
        bins = rate_bins({q: QUARTERS[q] for q in sg_q.get(sg, ()) if q in QUARTERS})
        if only_bins is not None:
            bins = [k for k in bins if k in only_bins]
        bad[sg] = skye_bins(counts[sg], bins)[0]
    return bad


def frozen_confusion(tces, mast, bad, keep=None):
    """TCE-level comparison with DR25's flag when the given bad bins are applied to each scored TCE's kept events."""
    keep = keep or (lambda t: True)
    pairs = []
    for r in tces:
        if r["kepid"] not in mast or not r["rv_found"]:
            continue
        sg, quarters = mast[r["kepid"]]
        e = [t for t in events(r["period"], r["t0"], quarters) if keep(t)]
        pairs.append((int(any(bin_index(t) in bad.get(sg, ()) for t in e)), r["skye"]))
    return confusion(pairs)


def int_or_blank(s):
    return int(s) if str(s).strip() else ""


def apply_koi(r, mast, bad, keep=None):
    """One KOI row of v3's koi_skye.csv scored with the frozen variant's bad bins.
    events_match: the recomputed ephemeris times equal v3's event_times, and the skygroup equals v3's."""
    keep = keep or (lambda t: True)
    kid = int(r["kepid"])
    out = {"kepoi_name": r["kepoi_name"], "kepid": kid, "disposition": r["disposition"], "period": r["period"],
           "t0": r["t0"], "v3_would_fail": int_or_blank(r.get("would_fail", ""))}
    for k in ("in_dr25",) + GROUPS:
        out[k] = int_or_blank(r.get(k, ""))
    if kid not in mast:
        out.update({"skygroup": "", "status": "no_skygroup", "n_events": "", "n_kept": "", "n_flagged": "",
                    "good": "", "eligible": "", "would_fail": "", "events_match": 0, "flagged_times": "",
                    "kept_times": ""})
        return out
    sg, quarters = mast[kid]
    evs = events(float(r["period"]), float(r["t0"]), quarters)
    match = (" ".join(f"{t:.4f}" for t in evs) == (r.get("event_times") or "").strip()
             and str(sg) == str(r.get("skygroup", "")).strip())
    kept = [t for t in evs if keep(t)]
    flagged = [t for t in kept if bin_index(t) in bad.get(sg, ())]
    good = len(kept) - len(flagged)
    eligible = int(len(kept) >= MIN_GOOD)
    out.update({"skygroup": sg, "status": "ok", "n_events": len(evs), "n_kept": len(kept),
                "n_flagged": len(flagged), "good": good, "eligible": eligible,
                "would_fail": int(eligible and good < MIN_GOOD), "events_match": int(match),
                "flagged_times": " ".join(f"{t:.4f}" for t in flagged),
                "kept_times": " ".join(f"{t:.4f}" for t in kept)})
    return out


def binom_tail(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(max(k, 0), n + 1))


def group_stats(rows, key):
    """Counts for the KOIs with rows[key] == 1 and a skygroup."""
    g = [r for r in rows if r[key] == 1 and r["status"] == "ok"]
    el = [r for r in g if r["eligible"] == 1]
    fails = sum(r["would_fail"] for r in el)
    anyf = sum(1 for r in g if r["n_flagged"] > 0)
    return {"n": len(g), "with_flagged": anyf, "flagged_fraction": round(anyf / len(g), 4) if g else None,
            "eligible": len(el), "fails": fails, "fail_fraction": round(fails / len(el), 4) if el else None}


def census_test(never, pc, ratio=CENSUS_RATIO, floor=CENSUS_FLOOR, p_max=CENSUS_P):
    """never, pc: (fails, eligible). (passed, p): passed when never's fail fraction is at least ratio times
    max(pc's fail fraction, floor) and the binomial tail at that rate is <= p_max; (None, None) without data."""
    k, n = never
    kp, npc = pc
    if not n or not npc:
        return None, None
    p0 = max(kp / npc, floor)
    p = binom_tail(k, n, p0)
    return bool(k / n >= ratio * p0 and p <= p_max), round(p, 6)


def koi_name(s):
    """Robnik et al.'s KOI number ('5269.01') as an Archive kepoi_name ('K05269.01')."""
    return "K%08.2f" % float(s)


def read_table(text):
    """Rows of a CSV or tab-separated table."""
    head = text.split("\n", 1)[0]
    return list(csv.DictReader(io.StringIO(text), delimiter="\t" if "\t" in head else ","))


def robnik_names(rows):
    return {koi_name(r["KOI"]) for r in rows if (r.get("KOI") or "").strip()}


def planets_per_star(cum_rows):
    """kepid -> number of cumulative KOIs dispositioned CANDIDATE or CONFIRMED (any period)."""
    n = {}
    for r in cum_rows:
        if r.get("koi_disposition") in ("CANDIDATE", "CONFIRMED"):
            n[r["kepid"]] = n.get(r["kepid"], 0) + 1
    return n


def population(koi_rows, per_star, excluded=EXCLUDED):
    """Scored KOIs: Skye-eligible CANDIDATEs with P > 45 d, alone on their star, not looked up beforehand."""
    out = []
    for r in koi_rows:
        if (r.get("status") == "ok" and str(r.get("eligible")) == "1" and r.get("disposition") == "CANDIDATE"
                and float(r["period"]) > P_MIN and per_star.get(str(r["kepid"]), 0) == 1
                and r["kepoi_name"] not in excluded):
            out.append(r)
    return out


def fisher_greater(a, b, c, d):
    """One-sided Fisher exact p for [[a, b], [c, d]]: P(X >= a) with the margins fixed."""
    r1, c1, n = a + b, a + c, a + b + c + d
    total = math.comb(n, r1)
    return sum(math.comb(c1, x) * math.comb(n - c1, r1 - x) for x in range(a, min(r1, c1) + 1)) / total


def compare(rows, listed, lo=None, hi=None):
    """Listed fractions for Skye-fail (F) and Skye-pass (S) KOIs, optionally inside a period window."""
    g = [r for r in rows if (lo is None or float(r["period"]) >= lo) and (hi is None or float(r["period"]) <= hi)]
    f = [r for r in g if str(r["would_fail"]) == "1"]
    s = [r for r in g if str(r["would_fail"]) != "1"]
    a = sum(r["kepoi_name"] in listed for r in f)
    c = sum(r["kepoi_name"] in listed for r in s)
    ff = a / len(f) if f else None
    fs = c / len(s) if s else None
    return {"n_fail": len(f), "fail_listed": a, "n_pass": len(s), "pass_listed": c,
            "fail_fraction": ff, "pass_fraction": fs,
            "p_one_sided": fisher_greater(a, len(f) - a, c, len(s) - c) if f and s else None}


def scored(main, window):
    q1 = main["n_fail"] >= N_FAIL_MIN
    q2 = bool(q1 and main["fail_fraction"] and main["pass_fraction"] is not None
              and main["fail_fraction"] >= RATIO_MIN * main["pass_fraction"]
              and main["p_one_sided"] is not None and main["p_one_sided"] < P_MAX)
    q3 = bool(window["fail_fraction"] is not None and window["pass_fraction"] is not None
              and window["fail_fraction"] > window["pass_fraction"])
    return {"q1_enough_fails": q1, "q2_enrichment": q2, "q3_window_direction": q3}


def same_text(a, b):
    """True when two byte strings are equal once CRLF line ends are undone."""
    return a.replace(b"\r\n", b"\n") == b.replace(b"\r\n", b"\n")


def gate(own, fetch):
    """(open, detail): open when the pre-registration is live in the repository and the repository's skye_inv.py
    matches own (this file's bytes). fetch: repository path -> bytes; it raises when the path is missing."""
    detail = {}
    try:
        detail["prereg_live"] = len(fetch(PREREG)) > 0
        detail["code_matches"] = detail["prereg_live"] and same_text(fetch(SELF), own)
    except Exception as e:  # a missing file keeps the gate shut
        detail["error"] = repr(e)
    return bool(detail.get("prereg_live") and detail.get("code_matches")), detail


def data_check(c):
    """Pre-registered prediction A2: every part of the KOI data check holds. c: the checks dict of main."""
    return bool(c["koi_rows"] == KOI_ROWS and c["koi_with_skygroup"] == c["koi_rows"]
                and c["events_match"] == c["koi_rows"] and c["valid_cadences"] == VALID_CADENCES)


def robnik_check(c):
    """Data check of the Robnik cross-check (its Q1-Q3 count only when this holds)."""
    return bool(c["robnik_rows"] == ROBNIK_ROWS and c["cumulative_sha256_ok"])


def http_bytes(url, tries=3, timeout=180, wait=5):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mv2-skye-inv/0.1 (Munim, Inc.; "
                                                                     "mv2@munimtech.com)"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # retried, then raised
            last = e
            time.sleep(wait * (k + 1))
    raise last


def http_to_file(url, path, tries=3, timeout=600, wait=5):
    """Stream url to path (large files never sit in memory whole)."""
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mv2-skye-inv/0.1 (Munim, Inc.; "
                                                                     "mv2@munimtech.com)"})
            with urllib.request.urlopen(req, timeout=timeout) as r, open(path, "wb") as f:
                for block in iter(lambda: r.read(1 << 20), b""):
                    f.write(block)
            return
        except Exception as e:  # retried, then raised
            last = e
            time.sleep(wait * (k + 1))
    raise last


def read_source(url, cache_dir):
    """(text, sha256) of url, downloaded into cache_dir (retried for about 26 minutes)."""
    path = os.path.join(cache_dir, "dl-" + hashlib.sha256(url.encode()).hexdigest()[:16])
    http_to_file(url, path, tries=12, wait=20)
    with open(path, "rb") as f:
        data = f.read()
    return data.decode("utf-8"), hashlib.sha256(data).hexdigest()


def lc_valid_times(cache_dir):
    """(sorted valid cadence times, per-file info): cadences with finite TIME and PDCSAP_FLUX in the Q1-Q17
    long-cadence files of LC_STARS, merged."""
    import numpy as np
    from astropy.io import fits
    times, info = set(), []
    for star in LC_STARS:
        for stamp in LC_STAMPS:
            url = LC.format(star[:4], star, stamp)
            path = os.path.join(cache_dir, os.path.basename(url))
            if not (os.path.isfile(path) and os.path.getsize(path) > 10000):
                http_to_file(url, path)
            with fits.open(path, memmap=False) as h:
                d = h[1].data
                t = np.asarray(d["TIME"], dtype=float)
                f = np.asarray(d["PDCSAP_FLUX"], dtype=float)
                ok = np.isfinite(t) & np.isfinite(f)
                times.update(round(float(x), 5) for x in t[ok])
                info.append({"file": os.path.basename(url), "quarter": h[0].header.get("QUARTER"),
                             "cadences": int(len(t)), "valid": int(ok.sum())})
    return sorted(times), info


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


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--cache-dir", default="")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    cache_dir = writable_dir(args.cache_dir) if args.cache_dir else tempfile.gettempdir()
    with open(os.path.abspath(__file__), "rb") as f:
        own = f.read()
    stats = {"version": VERSION, "skye_apply_sha256": hashlib.sha256(own).hexdigest(),
             "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "params": {"p_min": P_MIN, "bin0": BIN0, "n_sigma": N_SIGMA, "passes": PASSES, "window": WINDOW,
                        "min_good": MIN_GOOD}}

    # (1) the pre-registration is live and this is the published code
    stats["gate_open"], stats["gate"] = gate(own, lambda p: http_bytes(REPO.format(p), tries=12, wait=20))
    if not stats["gate_open"]:
        return finish(args.out_dir, stats, "stopped at the gate (pre-registration not live or code differs)")

    # (2) the frozen variant reproduces skye_diag 0.1.0 on OBS, through run_variant and through frozen_bins
    try:
        valid, lc_info = lc_valid_times(cache_dir)
        lc_error = ""
    except Exception as e:  # reproduction then fails and the run stops
        valid, lc_info, lc_error = [], [], repr(e)
    stats.update({"light_curves": lc_info, "light_curve_error": lc_error, "valid_cadences": len(valid)})
    dbins = data_bins(valid)

    def keep(t):
        return near(t, valid, WINDOW)

    obs_text, obs_sha = read_source(OBS_TCES, cache_dir)
    sg_text, sg_sha = read_source(OBS_SKYGROUPS, cache_dir)
    mast = load_skygroups(sg_text)
    obs_tces = load_tces(obs_text)
    obs, _ = run_variant(obs_tces, mast, use_all=False, keep=keep, only_bins=dbins)
    bad = frozen_bins(obs_tces, mast, keep=keep, only_bins=dbins)
    via_bins = frozen_confusion(obs_tces, mast, bad, keep=keep)
    reproduced = bool(valid) and all(obs[k] == v and via_bins[k] == v for k, v in OBS_CHOSEN.items())
    stats["obs"] = {"tce_skye_sha256": obs_sha, "skygroups_sha256": sg_sha, "run_variant": obs,
                    "via_frozen_bins": via_bins, "bad_bins": sum(len(b) for b in bad.values()),
                    "reproduced": reproduced}
    if not reproduced:
        return finish(args.out_dir, stats, "stopped: the frozen variant did not reproduce skye_diag's OBS counts")

    # (3) KOIs
    koi_text, koi_sha = read_source(KOI_SKYE, cache_dir)
    rows = [apply_koi(r, mast, bad, keep) for r in csv.DictReader(io.StringIO(koi_text))]
    groups = {k: group_stats(rows, k) for k in GROUPS}
    pc, nv = groups["dr25_pc"], groups["never_dr25"]
    census, census_p = census_test((nv["fails"], nv["eligible"]), (pc["fails"], pc["eligible"]))
    named = {n: next(({k: r[k] for k in ("skygroup", "n_events", "n_kept", "n_flagged", "good", "would_fail",
                                         "v3_would_fail", "flagged_times", "kept_times")}
                      for r in rows if r["kepoi_name"] == n), None) for n in NAMED}
    changed = {k: {"v3_fail_now_pass": sum(1 for r in rows if r[k] == 1 and r["v3_would_fail"] == 1
                                           and r["would_fail"] != 1),
                   "v3_pass_now_fail": sum(1 for r in rows if r[k] == 1 and r["v3_would_fail"] != 1
                                           and r["would_fail"] == 1)} for k in GROUPS}

    # Robnik et al. cross-check (amended: the frozen variant's would_fail and eligible)
    rob_text, rob_sha = read_source(ROBNIK_URL, cache_dir)
    cum_text, cum_sha = read_source(CUMULATIVE_URL, cache_dir)
    rob_rows, cum_rows = read_table(rob_text), read_table(cum_text)
    listed = robnik_names(rob_rows)
    pop = population(rows, planets_per_star(cum_rows))
    main_cmp = compare(pop, listed)
    win_cmp = compare(pop, listed, *RB_WINDOW)
    in_dr25 = compare([r for r in pop if r["in_dr25"] == 1], listed)
    cum_disp = {r["kepoi_name"]: r.get("koi_disposition", "") for r in cum_rows}
    listed_disp = {}
    for n in listed:
        k = cum_disp.get(n, "absent")
        listed_disp[k] = listed_disp.get(k, 0) + 1

    checks = {"koi_rows": len(rows), "koi_with_skygroup": sum(1 for r in rows if r["status"] == "ok"),
              "events_match": sum(r["events_match"] for r in rows), "valid_cadences": len(valid),
              "robnik_rows": len(rob_rows), "robnik_listed_names": len(listed),
              "cumulative_sha256_ok": cum_sha == CUMULATIVE_SHA256}
    rob_ok = robnik_check(checks)
    rb = scored(main_cmp, win_cmp)
    tests = {"a1_reproduced": reproduced, "a2_data": data_check(checks),
             "a3_named_fail": all(v is not None and v["would_fail"] == 1 for v in named.values()),
             "a4_census": census, "a4_p": census_p,
             "a5_pc_fail_fraction": pc["fail_fraction"] is not None and pc["fail_fraction"] <= PC_FAIL_MAX,
             "a6_dr25_skye_flagged": groups["dr25_skye"]["flagged_fraction"] is not None
                                     and groups["dr25_skye"]["flagged_fraction"] >= SKYE_RECALL_MIN,
             "robnik_data": rob_ok,
             "q1_enough_fails": rob_ok and rb["q1_enough_fails"],
             "q2_enrichment": rob_ok and rb["q2_enrichment"],
             "q3_window_direction": rob_ok and rb["q3_window_direction"]}
    stats.update({"koi_skye_sha256": koi_sha, "checks": checks, "groups": groups, "named": named,
                  "changed_vs_v3": changed, "tests": tests,
                  "robnik": {"robnik_sha256": rob_sha, "cumulative_sha256": cum_sha,
                             "listed_by_cumulative_disposition": listed_disp, "population": len(pop),
                             "main": main_cmp, "window_340_400": win_cmp, "in_dr25_only": in_dr25}})

    with open(os.path.join(args.out_dir, "koi_frozen.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KOI_FIELDS)
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(args.out_dir, "crosscheck.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kepoi_name", "kepid", "period", "in_dr25", "would_fail", "robnik_listed"])
        for r in pop:
            w.writerow([r["kepoi_name"], r["kepid"], r["period"], r["in_dr25"], r["would_fail"],
                        int(r["kepoi_name"] in listed)])
    stats["leads"] = [{k: r[k] for k in ("kepoi_name", "period", "skygroup", "n_kept", "n_flagged", "good",
                                          "flagged_times", "kept_times")}
                      for r in rows if r["never_dr25"] == 1 and r["would_fail"] == 1]
    return finish(args.out_dir, stats, "done")


def finish(out_dir, stats, status):
    """Write summary.json and report.md; exit code 0 when the run went through, else 1."""
    stats["status"] = status
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)
    lines = [f"# skye_apply {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Pre-registered in {PREREG}. Code "
             "Apache-2.0, results CC BY 4.0. A Skye failure marks transits that coincide with clustered artefacts; "
             "it is a lead, not a disposition.", "", f"Status: {status}.", "", "Gate: " + json.dumps(stats.get("gate")),
             ""]
    if "obs" in stats:
        o, b = stats["obs"]["run_variant"], stats["obs"]["via_frozen_bins"]
        lines += [f"OBS reproduction of skye_diag 0.1.0: {stats['obs']['reproduced']} (run_variant tp {o['tp']}, fp "
                  f"{o['fp']}, fn {o['fn']}, tn {o['tn']}; via frozen bins tp {b['tp']}, fp {b['fp']}, fn {b['fn']}, "
                  f"tn {b['tn']}). Valid cadences: {stats['valid_cadences']}. Light-curve error: "
                  f"{stats['light_curve_error'] or 'none'}.", ""]
    if "groups" in stats:
        lines += ["## KOI groups (frozen variant)", "",
                  "| group | KOIs | with a flagged kept event | fraction | eligible (>= 3 kept) | would fail | fraction |",
                  "|---|---|---|---|---|---|---|"]
        lines += [f"| {k} | {v['n']} | {v['with_flagged']} | {v['flagged_fraction']} | {v['eligible']} | "
                  f"{v['fails']} | {v['fail_fraction']} |" for k, v in stats["groups"].items()]
        lines += ["", "Checks: " + ", ".join(f"{k} = {v}" for k, v in stats["checks"].items()), "",
                  "Tests: " + ", ".join(f"{k} = {v}" for k, v in stats["tests"].items()), "",
                  "Named: " + json.dumps(stats["named"]), "", "Changed vs v3: " + json.dumps(stats["changed_vs_v3"]),
                  "", "## Robnik et al. 2026 cross-check (amended)", "",
                  "| comparison | n_fail | fail_listed | n_pass | pass_listed | p_one_sided |", "|---|---|---|---|---|---|"]
        lines += [f"| {k} | {v['n_fail']} | {v['fail_listed']} | {v['n_pass']} | {v['pass_listed']} | "
                  f"{v['p_one_sided']} |" for k, v in ((k, stats["robnik"][k]) for k in
                                                       ("main", "window_340_400", "in_dr25_only"))]
        lines += ["", "## Leads: candidates DR25 never scored that the frozen variant would fail", "",
                  "| KOI | period | skygroup | kept | flagged | good | flagged times (BKJD) |", "|---|---|---|---|---|---|---|"]
        lines += [f"| {r['kepoi_name']} | {r['period']} | {r['skygroup']} | {r['n_kept']} | {r['n_flagged']} | "
                  f"{r['good']} | {r['flagged_times']} |" for r in stats["leads"]]
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps({k: v for k, v in stats.items() if k not in ("light_curves", "leads")}, indent=1))
    return 0 if status == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
