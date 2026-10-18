"""skye_inv: a held-out test of MV2's open re-implementation of DR25's Skye test, on DR25's inverted run (INV).

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library, plus astropy and numpy to read the
Kepler light curves.
Pre-registration: findings/2026-10-18-skye-inv-prereg.md in munimtechnologies/exoplanet-archive-audit.

skye_diag 0.1.0 (findings/2026-10-18-skye-diag-v1-exploratory.md) tried fixes for skye-census-v3's misses against
DR25's OBS Skye flags, which had already been seen. Its variant with the highest F1 on OBS,
scored_only_real_events_w0.25_data_bins, is tested here unchanged on flags this project has never opened: the
Robovetter input of DR25's INV run (Thompson et al. 2018, ApJS 235, 38; github.com/nasa/kepler-robovetter), for which
DR25 ran Skye on the INV TCEs alone.
  bins    per skygroup, the events of the INV TCEs with P > 45 d that are in the INV Robovetter input;
  events  t0 + n P inside the star's long-cadence quarters (MAST), kept only within 0.25 d of a valid cadence (finite
          TIME and PDCSAP_FLUX) in the Q1-Q17 files of KIC 9018021 or KIC 6359929 (INV uses the same cadences);
  rate    over the bins of the skygroup's quarters that hold a valid cadence; Skye.py's cutoff R + 3 sqrt(R), 5 passes.
A TCE is flagged when one of its kept events lies in a bad bin of its skygroup, and compared with DR25's iflag3 ("at
least one transit event failed SKYE").
Order of work: (1) the pre-registration must be live on GitHub and the repository's skye_inv.py must match this
file; (2) the chosen variant is re-run on OBS and must reproduce skye_diag's counts exactly; only then (3) are the
INV Robovetter files opened. A failure at (1) or (2) stops the job before (3).
events, bin_index, rate_bins, skye_bins, confusion, near, data_bins, run_variant, by_event_count, load_tces,
load_skygroups and lc_valid_times are copied unchanged from skye_diag 0.1.0; fnum, tce_key, has_skye, parse_mast and
parse_rv_output from skye_census 0.2.1.

Usage: python skye_inv.py --out-dir /out/inv [--cache-dir /data]
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
import re
import sys
import tarfile
import tempfile
import time
import urllib.request

VERSION = "0.1.0"
REPO = "https://raw.githubusercontent.com/munimtechnologies/exoplanet-archive-audit/main/{}"
PREREG = "findings/2026-10-18-skye-inv-prereg.md"
SELF = "skye_inv.py"
OBS_TCES = REPO.format("results/2026-10-18-skye-census-0.2.1/tce_skye.csv")
OBS_SKYGROUPS = REPO.format("results/2026-10-18-skye-census-0.2.1/skygroups.csv")
INV_TCES = "https://exoplanetarchive.ipac.caltech.edu/data/KeplerData/Simulated/kplr_dr25_inv_tces.txt"
MAST = ("https://archive.stsci.edu/kepler/data_search/search.php?action=Search&ktc_kepler_id={}"
        "&ktc_target_type=LC&outputformat=CSV&max_records={}"
        "&selectedColumnsCsv=ktc_kepler_id,sci_data_quarter,sci_skygroup_id,ktc_target_type")
RV = "https://raw.githubusercontent.com/nasa/kepler-robovetter/master/{}"
RV_MEDIA = "https://media.githubusercontent.com/media/nasa/kepler-robovetter/master/{}"
RV_INPUT = "kplr_dr25_inv_robovetter_input.tar.gz"
RV_OUTPUT = "kplr_dr25_inv_robovetter_output.txt"
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
CHUNK = 100
RV_SKYE_COL = 11
# Robovetter input columns this code reads, by 0-based position, as named in the OBS header
RV_NAMES = {2: "KIC", 3: "pn", 5: "ntrans", 6: "nrealt", 7: "ngoodt", 11: "iflag3"}
# skye_diag 0.1.0's counts for the chosen variant on OBS (results/2026-10-18-skye-diag-v1/summary.json)
OBS_CHOSEN = {"tp": 3829, "fp": 1364, "fn": 446, "tn": 8313}
# Pre-registered thresholds
INV_ROWS = 19536  # \nrows of kplr_dr25_inv_tces.txt
ROWS_MIN = 0.99
STAR_MIN = 0.99
JOIN_MIN = 0.99
COMMENT_N_MIN = 50
COMMENT_MIN = 0.99
VALID_CADENCES = 128918  # skye_diag 0.1.0, same 34 files
TCE_RECALL_MIN = 0.85
TCE_PRECISION_MIN = 0.75

TCE_FIELDS = ["kepid", "pn", "period", "t0", "skygroup", "rv_nitrans", "rv_nrealtrans", "rv_ngoodtrans", "rv_skye",
              "rv_comment_skye", "events_chosen", "flag_chosen", "events_scored_only", "flag_scored_only"]


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


def by_event_count(rows):
    """Confusion counts split by how a TCE's event count compares with DR25's nrealtrans."""
    groups = {"more": [], "equal": [], "fewer": []}
    for n, _, nreal, ours, dr in rows:
        groups["more" if n > nreal else "equal" if n == nreal else "fewer"].append((ours, dr))
    return {k: dict(confusion(v), n=len(v)) for k, v in groups.items()}


def tce_key(s):
    """(kic, pn) from a TCE id such as 001026032-01, or None."""
    m = re.fullmatch(r"(\d+)\D+(\d+)", (s or "").strip())
    return (int(m.group(1)), int(m.group(2))) if m else None


def has_skye(comment):
    """True when SKYE is among the INDIV_TRANS flags of a DR25 comment (INDIV_TRANS_MARSHALL_SKYE---...)."""
    for part in (comment or "").split("---"):
        if part.startswith("INDIV_TRANS_"):
            return "SKYE" in part[len("INDIV_TRANS_"):].split("_")
    return False


def parse_inv_tces(lines):
    """[(kepid, pn, period, epoch)] from the IPAC INV TCE table (TCE_ID, KIC, Disp, Score, NTL, SS, CO, EM, period,
    epoch, ...). Header lines (a backslash or | first), rows whose KIC differs from their TCE_ID and rows without a
    finite period and epoch are skipped."""
    out = []
    for line in lines:
        f = line.split()
        if len(f) < 10 or f[0][0] in "\\|":
            continue
        k = tce_key(f[0])
        p, t0 = fnum(f[8]), fnum(f[9])
        if k is None or f[1] != str(k[0]) or p is None or t0 is None:
            continue
        out.append((k[0], k[1], p, t0))
    return out


def parse_rv_input(lines):
    """{(kic, pn): (nitrans, nrealtrans, ngoodtrans, skye flag)} from rows of a DR25 Robovetter input table, by
    position as Kepler-RoboVetter-DR25.cpp reads them. Header (#, backslash or | first) and malformed lines are
    skipped."""
    out = {}
    for line in lines:
        f = line.split()
        if len(f) <= RV_SKYE_COL or f[0][0] in "#\\|":
            continue
        try:
            kic, pn = int(f[2]), int(f[3])
            nit, nreal, ngood = (int(float(x)) for x in f[5:8])
            skye = int(float(f[RV_SKYE_COL]))
        except ValueError:
            continue
        out[(kic, pn)] = (nit, nreal, ngood, skye)
    return out


def rv_names(header):
    """Column names from the first |-delimited line of an IPAC header, or []."""
    for line in header:
        s = line.strip()
        if s.startswith("|"):
            return [x.strip() for x in s.strip("|").split("|")]
    return []


def names_ok(names):
    """True when every column this code reads by position carries the name it has in the OBS header."""
    return all(i < len(names) and names[i] == n for i, n in RV_NAMES.items())


def parse_rv_output(lines):
    """{(kic, pn): comments} from the DR25 Robovetter output (TCE, score, disposition, four flags, comments)."""
    out = {}
    for line in lines:
        f = line.split()
        if not f or f[0].startswith("#"):
            continue
        k = tce_key(f[0])
        if k is not None:
            out[k] = f[7] if len(f) > 7 else ""
    return out


def parse_mast(text):
    """{kepid: (skygroup, set of long-cadence quarters)} from MAST data_search CSV (label line, type line, rows)."""
    out = {}
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 4:
            continue
        kid, q, sg, kind = (x.strip() for x in row[:4])
        if not (kid.isdigit() and q.isdigit() and sg.isdigit()) or kind != "LC":
            continue
        g, qs = out.get(int(kid), (int(sg), set()))
        qs.add(int(q))
        out[int(kid)] = (g, qs)
    return out


def tce_dicts(tces, rv_table):
    """skye_diag-style TCE dicts for (kepid, pn, period, t0) TCEs, with their Robovetter counts and Skye flag."""
    out = []
    for kid, pn, p, t0 in tces:
        rv = rv_table.get((kid, pn))
        out.append({"kepid": kid, "pn": pn, "period": p, "t0": t0, "rv_found": rv is not None,
                    "nitrans": rv[0] if rv else None, "nrealtrans": rv[1] if rv else None,
                    "ngoodtrans": rv[2] if rv else None, "skye": rv[3] if rv else None})
    return out


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
    """Pre-registered prediction 2: every part of the data check holds. c: the checks dict of main."""
    n_min = ROWS_MIN * INV_ROWS
    return bool(c["inv_rows"] >= n_min and c["rv_rows"] >= n_min and c["rv_names_ok"]
                and c["inv_long_stars"] and c["stars_with_skygroup"] >= STAR_MIN * c["inv_long_stars"]
                and c["inv_long_rows"] and c["rv_found"] >= JOIN_MIN * c["inv_long_rows"]
                and c["comment_skye_tces"] >= COMMENT_N_MIN
                and c["comment_skye_with_flag_1"] >= COMMENT_MIN * c["comment_skye_tces"]
                and c["valid_cadences"] == VALID_CADENCES)


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


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


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


def fetch_skygroups(kepids, chunk=CHUNK, pause=0.5):
    """MAST skygroup and long-cadence quarters for each kepid, in chunks; failed chunks are reported."""
    out, errors = {}, []
    for i in range(0, len(kepids), chunk):
        ids = kepids[i:i + chunk]
        url = MAST.format(",".join(str(k) for k in ids), 100 * len(ids))
        try:
            out.update(parse_mast(http_bytes(url).decode("utf-8", "replace")))
        except Exception as e:  # one failed chunk must not sink the run; it is reported
            errors.append({"first_kepid": ids[0], "n": len(ids), "error": repr(e)})
        time.sleep(pause)
    return out, errors


def fetch_rv(name, cache_dir):
    """Path of a cached copy of a kepler-robovetter file, downloaded once (git-lfs pointers are followed)."""
    path = os.path.join(cache_dir, name)
    if not (os.path.isfile(path) and os.path.getsize(path) > 1000):
        http_to_file(RV.format(name), path)
        with open(path, "rb") as f:
            lfs = f.read(40).startswith(b"version https://git-lfs")
        if lfs:
            http_to_file(RV_MEDIA.format(name), path)
    return path


def load_robovetter(cache_dir):
    """(input table, output comments, input header lines, provenance) of the INV Robovetter files."""
    in_path = fetch_rv(RV_INPUT, cache_dir)
    out_path = fetch_rv(RV_OUTPUT, cache_dir)
    table, header = {}, []
    with tarfile.open(in_path, "r:gz") as tf:
        member = max((m for m in tf.getmembers() if m.isfile()), key=lambda m: m.size)
        for line in io.TextIOWrapper(tf.extractfile(member), encoding="utf-8", errors="replace"):
            if line.lstrip()[:1] in ("\\", "|"):
                header.append(line)
            else:
                table.update(parse_rv_input([line]))
    with open(out_path, encoding="utf-8", errors="replace") as f:
        comments = parse_rv_output(f)
    prov = {"input": {"url": RV.format(RV_INPUT), "sha256": sha256_file(in_path), "member": member.name,
                      "member_bytes": member.size, "rows": len(table), "header_lines": len(header)},
            "output": {"url": RV.format(RV_OUTPUT), "sha256": sha256_file(out_path), "rows": len(comments)}}
    return table, comments, header, prov


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
    stats = {"version": VERSION, "skye_inv_sha256": hashlib.sha256(own).hexdigest(),
             "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "params": {"p_min": P_MIN, "bin0": BIN0, "n_sigma": N_SIGMA, "passes": PASSES, "window": WINDOW,
                        "rv_skye_col": RV_SKYE_COL}}

    # (1) the pre-registration is live and this is the published code
    stats["gate_open"], stats["gate"] = gate(own, lambda p: http_bytes(REPO.format(p), tries=12, wait=20))
    if not stats["gate_open"]:
        return finish(args.out_dir, stats, "stopped at the gate (pre-registration not live or code differs)")

    # (2) the chosen variant reproduces skye_diag 0.1.0 on OBS
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
    obs_mast = load_skygroups(sg_text)
    obs, _ = run_variant(load_tces(obs_text), obs_mast, use_all=False, keep=keep, only_bins=dbins)
    reproduced = bool(valid) and all(obs[k] == v for k, v in OBS_CHOSEN.items())
    stats["obs"] = {"tce_skye_sha256": obs_sha, "skygroups_sha256": sg_sha, "chosen": obs, "reproduced": reproduced}
    if not reproduced:
        return finish(args.out_dir, stats, "stopped: the chosen variant did not reproduce skye_diag's OBS counts")

    # (3) INV
    inv_text, inv_sha = read_source(INV_TCES, cache_dir)
    inv_all = parse_inv_tces(inv_text.splitlines())
    inv_long = [t for t in inv_all if t[2] > P_MIN]
    stars = sorted({t[0] for t in inv_long})
    mast = dict(obs_mast)
    looked, mast_errors = fetch_skygroups([k for k in stars if k not in mast])
    mast.update(looked)
    with open(os.path.join(args.out_dir, "inv_skygroups.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kepid", "skygroup", "lc_quarters"])
        for kid in sorted(looked):
            w.writerow([kid, looked[kid][0], " ".join(str(q) for q in sorted(looked[kid][1]))])
    try:
        rv_table, rv_comments, rv_header, rv_prov = load_robovetter(cache_dir)
        rv_error = ""
    except Exception as e:  # the data check then fails
        rv_table, rv_comments, rv_header, rv_prov, rv_error = {}, {}, [], {}, repr(e)
    with open(os.path.join(args.out_dir, "rv_input_header.txt"), "w", encoding="utf-8") as f:
        f.writelines(rv_header)
    names = rv_names(rv_header)
    tces = tce_dicts(inv_long, rv_table)
    variants, rows = {}, {}
    variants["chosen"], rows["chosen"] = run_variant(tces, mast, use_all=False, keep=keep, only_bins=dbins)
    variants["scored_only"], rows["scored_only"] = run_variant(tces, mast, use_all=False)
    variants["all_tces"], _ = run_variant(tces, mast)
    f1s = {k: f1(v) for k, v in variants.items()}
    for k, v in variants.items():
        v["f1"] = round(f1s[k], 4) if f1s[k] is not None else None

    commented = {k for k, c in rv_comments.items() if has_skye(c)}
    checks = {"inv_rows": len(inv_all), "inv_long_rows": len(inv_long), "inv_long_stars": len(stars),
              "stars_looked_up": len(looked), "mast_errors": len(mast_errors),
              "stars_with_skygroup": sum(1 for k in stars if k in mast),
              "rv_rows": len(rv_table), "rv_names": names[:14], "rv_names_ok": names_ok(names),
              "rv_found": sum(1 for r in tces if r["rv_found"]),
              "rv_skye_flag_1_all_periods": sum(1 for v in rv_table.values() if v[3] == 1),
              "comment_skye_tces": len(commented),
              "comment_skye_with_flag_1": sum(1 for k in commented if k in rv_table and rv_table[k][3] == 1),
              "valid_cadences": len(valid)}
    ch = variants["chosen"]
    tests = {"p2_data": data_check(checks),
             "p3_tce_recall": bool(ch["tp"] + ch["fn"]) and ch["tp"] >= TCE_RECALL_MIN * (ch["tp"] + ch["fn"]),
             "p4_tce_precision": bool(ch["tp"] + ch["fp"])
                                 and ch["tp"] >= TCE_PRECISION_MIN * (ch["tp"] + ch["fp"]),
             "p5_f1_gain": f1s["chosen"] is not None and f1s["scored_only"] is not None
                           and f1s["chosen"] > f1s["scored_only"]}
    stats.update({"inv_tces": {"url": INV_TCES, "sha256": inv_sha}, "robovetter": rv_prov,
                  "robovetter_error": rv_error, "mast_error_list": mast_errors, "checks": checks,
                  "variants": variants, "tests": tests,
                  "chosen_by_event_count": by_event_count(rows["chosen"])})

    compared = [r for r in tces if r["kepid"] in mast and r["rv_found"]]
    with open(os.path.join(args.out_dir, "inv_tce_skye.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(TCE_FIELDS)
        for r, a, b in zip(compared, rows["chosen"], rows["scored_only"]):
            w.writerow([r["kepid"], r["pn"], r["period"], r["t0"], mast[r["kepid"]][0], r["nitrans"],
                        r["nrealtrans"], r["ngoodtrans"], r["skye"], int((r["kepid"], r["pn"]) in commented),
                        a[0], a[3], b[0], b[3]])
    return finish(args.out_dir, stats, "done")


def finish(out_dir, stats, status):
    """Write summary.json and report.md; exit code 0 when the run went through, else 1."""
    stats["status"] = status
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)
    lines = [f"# skye_inv {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Held-out test pre-registered in "
             f"{PREREG}. Code Apache-2.0, results CC BY 4.0. Skye flags are signs of clustered artefacts, not "
             "dispositions.", "", f"Status: {status}.", "", "Gate: " + json.dumps(stats.get("gate")), ""]
    if "obs" in stats:
        o = stats["obs"]["chosen"]
        lines += [f"OBS re-run of the chosen variant reproduces skye_diag 0.1.0: {stats['obs']['reproduced']} "
                  f"(tp {o['tp']}, fp {o['fp']}, fn {o['fn']}, tn {o['tn']}). Valid cadences: "
                  f"{stats['valid_cadences']}. Light-curve error: {stats['light_curve_error'] or 'none'}.", ""]
    if "variants" in stats:
        cols = ("tp", "fp", "fn", "tn", "recall", "precision", "f1", "tces_compared", "bad_bins", "bin_events")
        lines += ["## INV against DR25's iflag3 (SKYE), P > 45 d", "",
                  "| variant | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
        lines += [f"| {k} | " + " | ".join(str(v.get(c)) for c in cols) + " |" for k, v in stats["variants"].items()]
        lines += ["", "Data checks: " + ", ".join(f"{k} = {v}" for k, v in stats["checks"].items()), "",
                  "Robovetter: " + (stats["robovetter_error"] or "loaded") + ".", "",
                  "Tests: " + ", ".join(f"{k} = {v}" for k, v in stats["tests"].items()), "",
                  "## Chosen variant split by event count against DR25's nrealtrans", "",
                  "| events vs nrealtrans | n | tp | fp | fn | tn | recall | precision |",
                  "|---|---|---|---|---|---|---|---|"]
        lines += [f"| {k} | {v['n']} | {v['tp']} | {v['fp']} | {v['fn']} | {v['tn']} | {v['recall']} | "
                  f"{v['precision']} |" for k, v in stats["chosen_by_event_count"].items()]
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps({k: v for k, v in stats.items() if k not in ("light_curves", "mast_error_list")}, indent=1))
    return 0 if status == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
