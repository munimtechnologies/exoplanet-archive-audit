"""skye_diag: an exploratory look at why skye-census-v3 missed its pre-registered validation bars.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library, plus astropy and numpy to read the
Kepler light curves.
Scored v3 results: findings/2026-10-18-skye-census-v3-results.md in munimtechnologies/exoplanet-archive-audit.

Exploratory, not pre-registered: it re-reads data already seen (v3's DR25 OBS TCEs and their Robovetter Skye
flags), so nothing here is a validated result. It measures how much of v3's mismatch each suspected cause explains:
  unscored  v3's bins counted the 1,397 P > 45 d TCEs absent from the DR25 Robovetter input (consistent with DR25's
            rogue TCEs, which Thompson et al. 2018 left out of the catalogue and of Skye);
  gaps      v3 counts every ephemeris event inside a quarter, while Skye.py counts only transits with non-zero SES
            and treats bins without such transits as gaps. Here an event is "real" when a long-cadence cadence with
            finite TIME and PDCSAP_FLUX in the Q1-Q17 files of KIC 9018021 or KIC 6359929 lies within w days of it.
Variant "v3" must reproduce v3's confusion counts exactly, or the comparison is void.
events, bin_index, rate_bins, skye_bins and confusion are copied unchanged from skye_census 0.2.1.

Usage: python skye_diag.py --out-dir /out/diag [--cache-dir /data] [--tce-csv URL|path] [--skygroups-csv URL|path]
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
RESULTS = ("https://raw.githubusercontent.com/munimtechnologies/exoplanet-archive-audit/main/"
           "results/2026-10-18-skye-census-0.2.1/{}")
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
WINDOWS = (0.1, 0.25, 0.5)
V3_CONFUSION = {"tp": 3382, "fp": 1621, "fn": 893, "tn": 8056}


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


def by_event_count(rows):
    """Confusion counts split by how a TCE's event count compares with DR25's nrealtrans."""
    groups = {"more": [], "equal": [], "fewer": []}
    for n, _, nreal, ours, dr in rows:
        groups["more" if n > nreal else "equal" if n == nreal else "fewer"].append((ours, dr))
    return {k: dict(confusion(v), n=len(v)) for k, v in groups.items()}


def http_to_file(url, path, tries=3, timeout=600, wait=5):
    """Stream url to path (large files never sit in memory whole)."""
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mv2-skye-diag/0.1 (Munim, Inc.; "
                                                                     "mv2@munimtech.com)"})
            with urllib.request.urlopen(req, timeout=timeout) as r, open(path, "wb") as f:
                for block in iter(lambda: r.read(1 << 20), b""):
                    f.write(block)
            return
        except Exception as e:  # retried, then raised
            last = e
            time.sleep(wait * (k + 1))
    raise last


def read_source(src, cache_dir):
    """(text, sha256) of a local path or a URL (downloaded into cache_dir). A URL is retried for about 26 minutes,
    in case the results commit lands after the job starts."""
    path = src
    if src.startswith("http"):
        path = os.path.join(cache_dir, "dl-" + hashlib.sha256(src.encode()).hexdigest()[:16])
        http_to_file(src, path, tries=12, wait=20)
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
    ap.add_argument("--tce-csv", default=RESULTS.format("tce_skye.csv"))
    ap.add_argument("--skygroups-csv", default=RESULTS.format("skygroups.csv"))
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    cache_dir = writable_dir(args.cache_dir) if args.cache_dir else tempfile.gettempdir()
    tce_text, tce_sha = read_source(args.tce_csv, cache_dir)
    sg_text, sg_sha = read_source(args.skygroups_csv, cache_dir)
    tces, mast = load_tces(tce_text), load_skygroups(sg_text)

    variants, rows = {}, {}
    variants["v3"], rows["v3"] = run_variant(tces, mast)
    reproduced = all(variants["v3"][k] == v for k, v in V3_CONFUSION.items())
    variants["scored_only"], _ = run_variant(tces, mast, use_all=False)
    try:
        valid, lc_info = lc_valid_times(cache_dir)
        lc_error = ""
    except Exception as e:  # the variants without light curves are still reported
        valid, lc_info, lc_error = [], [], repr(e)
    if valid:
        dbins = data_bins(valid)
        for w in WINDOWS:
            keep = lambda t, w=w: near(t, valid, w)
            variants[f"real_events_w{w}"], _ = run_variant(tces, mast, keep=keep)
            variants[f"scored_only_real_events_w{w}"], _ = run_variant(tces, mast, use_all=False, keep=keep)
            variants[f"scored_only_real_events_w{w}_data_bins"], _ = run_variant(tces, mast, use_all=False,
                                                                                 keep=keep, only_bins=dbins)
    stats = {"version": VERSION, "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "inputs": {"tce_csv": {"source": args.tce_csv, "sha256": tce_sha, "rows": len(tces)},
                        "skygroups_csv": {"source": args.skygroups_csv, "sha256": sg_sha, "rows": len(mast)}},
             "unscored_tces": sum(1 for r in tces if not r["rv_found"]),
             "reproduced_v3": reproduced, "light_curves": lc_info, "light_curve_error": lc_error,
             "valid_cadences": len(valid), "data_bins": len(data_bins(valid)) if valid else 0,
             "variants": variants, "v3_by_event_count": by_event_count(rows["v3"])}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)
    cols = ("tp", "fp", "fn", "tn", "recall", "precision", "bad_bins", "bin_events", "events_equal_nitrans",
            "events_equal_nrealtrans")
    lines = [f"# skye_diag {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Exploratory diagnosis of "
             "skye-census-v3 on data already seen; not a validated result. Code Apache-2.0, results CC BY 4.0.", "",
             f"Reproduced v3's confusion counts: {reproduced}. TCEs: {len(tces)} (not in the Robovetter input: "
             f"{stats['unscored_tces']}). Valid cadences: {len(valid)}. Light-curve error: {lc_error or 'none'}.",
             "", "| variant | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    lines += [f"| {k} | " + " | ".join(str(v.get(c)) for c in cols) + " |" for k, v in variants.items()]
    lines += ["", "## v3 split by event count against DR25's nrealtrans", "",
              "| events vs nrealtrans | n | tp | fp | fn | tn | recall | precision |", "|---|---|---|---|---|---|---|---|"]
    lines += [f"| {k} | {v['n']} | {v['tp']} | {v['fp']} | {v['fn']} | {v['tn']} | {v['recall']} | {v['precision']} |"
              for k, v in stats["v3_by_event_count"].items()]
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps({k: v for k, v in stats.items() if k != "light_curves"}, indent=1))
    return 0 if reproduced else 1


if __name__ == "__main__":
    sys.exit(main())
