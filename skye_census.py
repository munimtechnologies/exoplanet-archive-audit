"""skye_census: DR25's Skye test, re-run on every long-period KOI, including the candidates DR25 never vetted.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.
Pre-registration: findings/2026-10-18-skye-census-v2-prereg.md in munimtechnologies/exoplanet-archive-audit, with
the amendment findings/2026-10-18-skye-census-v3-amendment.md (0.2.1 changes only where the tables come from)
(v1: findings/2026-10-18-skye-census-prereg.md, scored in findings/2026-10-18-skye-census-results.md).

Thompson et al. 2018 (ApJS 235, 38; appendix A.3.7.4, "Skye") flag individual transits that coincide with
clusters of other TCE events in the same skygroup. 0.2.0 follows the reference code, Skye.py in
github.com/JeffLCoughlin/skye (calcSkye(1.0, 3.0, 45.0)):
  bins     1.0 d, edges at 131.5 + k (np.arange(131.5, 1591 + 1, 1)), so bin centres fall on whole days;
  counts   events of every DR25 obsTCE with P > 45 d, per skygroup;
  rate     R = events / non-gap bins; cutoff R + 3 sqrt(R); then five passes that drop bins above the cutoff
           and recompute R and the cutoff from the bins kept; every bin above the final cutoff is bad.
This re-implementation has no per-event SES, so:
  events   t0 + n P inside the quarters the star was observed in long cadence (MAST data_search), with the
           quarter spans below (intra-quarter gaps are not removed);
  gaps     a skygroup's non-gap bins are those whose centre lies in a quarter in which at least one of its
           stars was observed in long cadence.
Validation against DR25 itself: the DR25 Robovetter input table (github.com/nasa/kepler-robovetter, OBS) holds,
per TCE, a 1/0 flag "at least one individual transit failed Skye" (column 12, as Kepler-RoboVetter-DR25.cpp
reads it); the Robovetter output holds each TCE's comments.
KOIs: every cumulative-table KOI with P > 45 d: events, events in a bad bin of its own skygroup ("flagged"),
good = events - flagged; eligible = events >= 3; would_fail = eligible and good < 3.
Groups: dr25_pc (in the DR25 KOI table as CANDIDATE), dr25_skye (DR25 KOI table, SKYE among the INDIV_TRANS
flags of koi_comment), never_dr25 (cumulative CANDIDATE, absent from the DR25 KOI table, so never scored by DR25).
Tables (0.2.1): live TAP first; if TAP fails, the same queries as skye-census-v1 fetched them, published in the
repository and accepted only when their sha256 matches v1's record.

Usage: python skye_census.py --out-dir /out/skye [--cache-dir /data] [--in-dir dir-with-cached-tap-csvs]
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
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request

VERSION = "0.2.1"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={}&format=csv"
MAST = ("https://archive.stsci.edu/kepler/data_search/search.php?action=Search&ktc_kepler_id={}"
        "&ktc_target_type=LC&outputformat=CSV&max_records={}"
        "&selectedColumnsCsv=ktc_kepler_id,sci_data_quarter,sci_skygroup_id,ktc_target_type")
RV = "https://raw.githubusercontent.com/nasa/kepler-robovetter/master/{}"
RV_MEDIA = "https://media.githubusercontent.com/media/nasa/kepler-robovetter/master/{}"
RV_INPUT = "kplr_dr25_obs_robovetter_input.tar.gz"
RV_OUTPUT = "kplr_dr25_obs_robovetter_output.txt"
QUERIES = {
    "dr25_tce": "select kepid,tce_plnt_num,tce_period,tce_time0bk from q1_q17_dr25_tce",
    "cumulative": "select kepoi_name,kepid,koi_disposition,koi_period,koi_time0bk from cumulative",
    "dr25_koi": "select kepoi_name,kepid,koi_pdisposition,koi_period,koi_time0bk,koi_comment from q1_q17_dr25_koi",
}
# Fallback for a TAP outage (on 2026-10-18 from ~16:25Z every TAP query got HTTP 400 and the Archive's older API
# reported ORA-01653): the QUERIES as skye-census-v1 fetched them at 2026-10-18T13:53Z, published byte for byte,
# with the sha256 values from v1's summary.json.
SNAPSHOT = ("https://raw.githubusercontent.com/munimtechnologies/exoplanet-archive-audit/main/"
            "results/2026-10-18-skye-census-0.1.0/tap/{}.csv")
SNAPSHOT_SHA256 = {
    "dr25_tce": "003d16155dc5e42858777c1097efa5bd62a120eb846a982ef553e3dbdef60664",
    "cumulative": "df551272c3e8a945fed88c23129328b0d070c224f6cf503048b5f88e88e89286",
    "dr25_koi": "9b07b64c34e213947c92941c797c1298c9fc0ab298a3ba3e8c4597749db264b4",
}
# Long-cadence spans (BKJD) of quarters 1-17: first and last cadences of KIC 9018021 and KIC 6359929
QUARTERS = {1: (131.51, 164.98), 2: (169.52, 258.47), 3: (260.22, 349.50), 4: (352.38, 442.20),
            5: (443.49, 538.16), 6: (539.47, 629.30), 7: (630.20, 719.55), 8: (735.38, 802.34),
            9: (808.54, 905.93), 10: (906.87, 1000.27), 11: (1001.23, 1098.33), 12: (1099.43, 1182.02),
            13: (1182.76, 1273.00), 14: (1274.20, 1371.32), 15: (1373.51, 1471.14), 16: (1472.12, 1557.96),
            17: (1559.25, 1591.00)}
P_MIN = 45.0
BIN0 = 131.5
BIN0_V1 = 131.0
N_SIGMA = 3.0
PASSES = 5
MIN_GOOD = 3
CHUNK = 100
NAMED = ("K05269.01", "K05227.01")
RV_SKYE_COL = 11  # 0-based: data_set tce kic pn num_planets nitrans nrealtrans ngoodtrans RUBBLE CHASES MARSHALL SKYE
# Pre-registered thresholds
RV_ROWS_MIN = 34000
RV_JOIN_MIN = 0.99
RV_COMMENT_MIN = 0.99
RV_COMMENT_N_MIN = 50
TCE_RECALL_MIN = 0.85
TCE_PRECISION_MIN = 0.75
SKYE_RECALL_MIN = 0.70
PC_FAIL_MAX = 0.10
CENSUS_RATIO = 2.0
CENSUS_FLOOR = 0.02
CENSUS_P = 0.01

KOI_FIELDS = ["kepoi_name", "kepid", "disposition", "period", "t0", "skygroup", "status", "n_events",
              "n_flagged", "good", "eligible", "would_fail", "in_dr25", "dr25_pc", "dr25_skye", "never_dr25",
              "flagged_times", "event_times"]
TCE_FIELDS = ["kepid", "pn", "period", "t0", "skygroup", "n_events", "n_flagged", "n_flagged_v1bins",
              "rv_found", "rv_nitrans", "rv_nrealtrans", "rv_ngoodtrans", "rv_skye", "rv_comment_skye"]


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


def has_skye(comment):
    """True when SKYE is among the INDIV_TRANS flags of a DR25 comment (INDIV_TRANS_MARSHALL_SKYE---...)."""
    for part in (comment or "").split("---"):
        if part.startswith("INDIV_TRANS_"):
            return "SKYE" in part[len("INDIV_TRANS_"):].split("_")
    return False


def binom_tail(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(max(k, 0), n + 1))


def confusion(pairs):
    """Counts for (ours, DR25) pairs of 0/1 flags; recall = tp / (tp + fn), precision = tp / (tp + fp)."""
    tp = sum(1 for a, b in pairs if a and b)
    fp = sum(1 for a, b in pairs if a and not b)
    fn = sum(1 for a, b in pairs if not a and b)
    tn = sum(1 for a, b in pairs if not a and not b)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "recall": round(tp / (tp + fn), 4) if tp + fn else None,
            "precision": round(tp / (tp + fp), 4) if tp + fp else None}


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


def parse_rv_input(lines):
    """{(kic, pn): (nitrans, nrealtrans, ngoodtrans, skye flag)} from rows of the DR25 Robovetter input table,
    by position as Kepler-RoboVetter-DR25.cpp reads them. Header and malformed lines are skipped."""
    out = {}
    for line in lines:
        f = line.split()
        if len(f) <= RV_SKYE_COL or line.lstrip().startswith("#"):
            continue
        try:
            kic, pn = int(f[2]), int(f[3])
            nit, nreal, ngood = (int(float(x)) for x in f[5:8])
            skye = int(float(f[RV_SKYE_COL]))
        except ValueError:
            continue
        out[(kic, pn)] = (nit, nreal, ngood, skye)
    return out


def tce_key(s):
    """(kic, pn) from a TCE id such as 001026032-01, or None."""
    m = re.fullmatch(r"(\d+)\D+(\d+)", (s or "").strip())
    return (int(m.group(1)), int(m.group(2))) if m else None


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


def koi_row(name, kid, disp, p, t0, mast, skye, dr25, spans=QUARTERS):
    """One KOI's Skye result. mast: kepid -> (skygroup, quarters); skye: skygroup -> set of bad bins;
    dr25: kepoi_name -> DR25 KOI row."""
    d = dr25.get(name)
    row = {"kepoi_name": name, "kepid": kid, "disposition": disp, "period": p, "t0": t0,
           "in_dr25": int(d is not None),
           "dr25_pc": int(d is not None and d.get("koi_pdisposition") == "CANDIDATE"),
           "dr25_skye": int(d is not None and has_skye(d.get("koi_comment"))),
           "never_dr25": int(d is None and disp == "CANDIDATE")}
    if kid not in mast:
        row.update({"skygroup": "", "status": "no_skygroup", "n_events": "", "n_flagged": "", "good": "",
                    "eligible": "", "would_fail": "", "flagged_times": "", "event_times": ""})
        return row
    sg, quarters = mast[kid]
    evs = events(p, t0, quarters, spans)
    bad = skye.get(sg, set())
    flagged = [t for t in evs if bin_index(t) in bad]
    good = len(evs) - len(flagged)
    eligible = int(len(evs) >= MIN_GOOD)
    row.update({"skygroup": sg, "status": "ok", "n_events": len(evs), "n_flagged": len(flagged), "good": good,
                "eligible": eligible, "would_fail": int(eligible and good < MIN_GOOD),
                "flagged_times": " ".join(f"{t:.4f}" for t in flagged),
                "event_times": " ".join(f"{t:.4f}" for t in evs)})
    return row


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


def build_skye(tces, mast, bin0=BIN0, per_skygroup_gaps=True):
    """(skygroup -> bad bins, skygroup -> info, bad-bin rows) from (kepid, period, t0) TCEs with P > P_MIN.
    per_skygroup_gaps: non-gap bins are those in quarters the skygroup was observed in (else every quarter)."""
    counts, sg_q = {}, {}
    for sg, qs in mast.values():
        sg_q.setdefault(sg, set()).update(qs)
    for kid, p, t0 in tces:
        if kid not in mast:
            continue
        sg, quarters = mast[kid]
        c = counts.setdefault(sg, {})
        for t in events(p, t0, quarters):
            k = bin_index(t, bin0)
            c[k] = c.get(k, 0) + 1
    skye, info, rows = {}, {}, []
    for sg in sorted(counts):
        spans = {q: QUARTERS[q] for q in sg_q.get(sg, ()) if q in QUARTERS} if per_skygroup_gaps else QUARTERS
        bins = rate_bins(spans, bin0)
        bad, r, thr = skye_bins(counts[sg], bins)
        skye[sg] = bad
        info[sg] = {"events": sum(counts[sg].values()), "rate_bins": len(bins), "rate": round(r, 4),
                    "threshold": round(thr, 4), "skye_bins": len(bad)}
        rows += [{"skygroup": sg, "bin": k, "start": bin0 + k, "count": counts[sg][k], "rate": round(r, 4),
                  "threshold": round(thr, 4)} for k in sorted(bad)]
    return skye, info, rows


def http_bytes(url, tries=3, timeout=180, wait=5):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mv2-skye-census/0.2 (Munim, Inc.; "
                                                                     "mv2@munimtech.com)"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # retried, then raised
            last = e
            time.sleep(wait * (k + 1))
    raise last


def looks_like_table(data, query):
    """True when the first line of data is the query's column list, as the header of TAP's CSV is."""
    cols = query.split(" from ")[0][len("select "):].strip()
    return data.split(b"\n", 1)[0].strip().decode("utf-8", "replace") == cols


def snapshot_bytes(name, data):
    """data, or data with CRLF line ends undone, when its sha256 is v1's record for name; else None."""
    for d in (data, data.replace(b"\r\n", b"\n")):
        if hashlib.sha256(d).hexdigest() == SNAPSHOT_SHA256.get(name):
            return d
    return None


def fetch_table(name, query, in_dir=""):
    """(bytes, source, TAP error): an --in-dir copy, else live TAP, else the published v1 snapshot."""
    cached = os.path.join(in_dir, name + ".csv") if in_dir else ""
    if cached and os.path.isfile(cached):
        with open(cached, "rb") as f:
            return f.read(), "in_dir", ""
    try:
        data = http_bytes(TAP.format(urllib.parse.quote_plus(query)))
        if looks_like_table(data, query):
            return data, "tap", ""
        tap_error = "TAP answered without the expected header: " + data[:200].decode("utf-8", "replace")
    except Exception as e:  # TAP was down when v2 ran; the snapshot below is the fallback
        tap_error = repr(e)
    print(json.dumps({name: {"tap_error": tap_error}}), flush=True)
    # waits up to about 12 minutes, in case the snapshot commit lands after the job starts
    data = snapshot_bytes(name, http_bytes(SNAPSHOT.format(name), tries=8, wait=20))
    if data is None:
        raise RuntimeError(f"{name}: the snapshot's sha256 does not match skye-census-v1's record")
    return data, "snapshot_v1", tap_error


def fetch_skygroups(kepids, chunk=CHUNK, pause=0.5):
    """MAST skygroup and long-cadence quarters for each kepid, in chunks; failed chunks are reported."""
    out, errors = {}, []
    for i in range(0, len(kepids), chunk):
        ids = kepids[i:i + chunk]
        url = MAST.format(",".join(str(k) for k in ids), 100 * len(ids))
        try:
            out.update(parse_mast(http_bytes(url).decode("utf-8", "replace")))
        except Exception as e:  # one failed chunk must not sink the census; it is reported
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


def http_to_file(url, path, tries=3, timeout=600):
    """Stream url to path (large files never sit in memory whole)."""
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mv2-skye-census/0.2 (Munim, Inc.; "
                                                                     "mv2@munimtech.com)"})
            with urllib.request.urlopen(req, timeout=timeout) as r, open(path, "wb") as f:
                for block in iter(lambda: r.read(1 << 20), b""):
                    f.write(block)
            return
        except Exception as e:  # retried, then raised
            last = e
            time.sleep(5 * (k + 1))
    raise last


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_robovetter(cache_dir, out_dir):
    """(input table, output comments, provenance); the first 223 lines of the input are saved as its header."""
    in_path = fetch_rv(RV_INPUT, cache_dir)
    out_path = fetch_rv(RV_OUTPUT, cache_dir)
    with tarfile.open(in_path, "r:gz") as tf:
        member = max((m for m in tf.getmembers() if m.isfile()), key=lambda m: m.size)
        stream = io.TextIOWrapper(tf.extractfile(member), encoding="utf-8", errors="replace")
        header = [next(stream, "") for _ in range(223)]  # the C++ reader skips 223 header lines
        table = parse_rv_input(stream)
    with open(os.path.join(out_dir, "rv_input_header.txt"), "w", encoding="utf-8") as f:
        f.writelines(header)
    with open(out_path, encoding="utf-8", errors="replace") as f:
        comments = parse_rv_output(f)
    prov = {"input": {"url": RV.format(RV_INPUT), "sha256": sha256_file(in_path), "member": member.name,
                      "member_bytes": member.size, "rows": len(table)},
            "output": {"url": RV.format(RV_OUTPUT), "sha256": sha256_file(out_path), "rows": len(comments)}}
    return table, comments, prov


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
    ap.add_argument("--in-dir", default="")
    ap.add_argument("--cache-dir", default="")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    cache_dir = writable_dir(args.cache_dir) if args.cache_dir else tempfile.gettempdir()
    tables, fetched = {}, {}
    for name, q in QUERIES.items():
        data, source, tap_error = fetch_table(name, q, args.in_dir)
        with open(os.path.join(args.out_dir, name + ".csv"), "wb") as f:
            f.write(data)
        tables[name] = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
        fetched[name] = {"query": q, "source": source, "tap_error": tap_error, "rows": len(tables[name]),
                         "sha256": hashlib.sha256(data).hexdigest()}
        print(json.dumps({name: fetched[name]}), flush=True)
    try:
        rv_table, rv_comments, rv_prov = load_robovetter(cache_dir, args.out_dir)
        rv_error = ""
    except Exception as e:  # the KOI census still runs; the validation tests then fail
        rv_table, rv_comments, rv_prov, rv_error = {}, {}, {}, repr(e)
    print(json.dumps({"robovetter": rv_prov, "error": rv_error}), flush=True)

    tces = []
    for r in tables["dr25_tce"]:
        p, t0 = fnum(r.get("tce_period")), fnum(r.get("tce_time0bk"))
        if (p is not None and t0 is not None and p > P_MIN and (r.get("kepid") or "").isdigit()
                and (r.get("tce_plnt_num") or "").isdigit()):
            tces.append((int(r["kepid"]), int(r["tce_plnt_num"]), p, t0))
    kois = []
    for r in tables["cumulative"]:
        p, t0 = fnum(r.get("koi_period")), fnum(r.get("koi_time0bk"))
        if p is not None and t0 is not None and p > P_MIN and (r.get("kepid") or "").isdigit():
            kois.append((r["kepoi_name"], int(r["kepid"]), r.get("koi_disposition", ""), p, t0))
    tce_stars = sorted({t[0] for t in tces})
    koi_stars = sorted({k[1] for k in kois})
    mast, mast_errors = fetch_skygroups(sorted(set(tce_stars) | set(koi_stars)))
    with open(os.path.join(args.out_dir, "skygroups.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kepid", "skygroup", "lc_quarters"])
        for kid in sorted(mast):
            w.writerow([kid, mast[kid][0], " ".join(str(q) for q in sorted(mast[kid][1]))])

    triples = [(kid, p, t0) for kid, _, p, t0 in tces]
    skye, sg_info, bin_rows = build_skye(triples, mast)
    skye_v1, _, _ = build_skye(triples, mast, BIN0_V1, per_skygroup_gaps=False)

    tce_rows = []
    for kid, pn, p, t0 in tces:
        if kid not in mast:
            continue
        sg, quarters = mast[kid]
        evs = events(p, t0, quarters)
        rv = rv_table.get((kid, pn))
        tce_rows.append({"kepid": kid, "pn": pn, "period": p, "t0": t0, "skygroup": sg, "n_events": len(evs),
                         "n_flagged": sum(1 for t in evs if bin_index(t) in skye.get(sg, ())),
                         "n_flagged_v1bins": sum(1 for t in evs if bin_index(t, BIN0_V1) in skye_v1.get(sg, ())),
                         "rv_found": int(rv is not None),
                         "rv_nitrans": rv[0] if rv else "", "rv_nrealtrans": rv[1] if rv else "",
                         "rv_ngoodtrans": rv[2] if rv else "", "rv_skye": rv[3] if rv else "",
                         "rv_comment_skye": int(has_skye(rv_comments.get((kid, pn), "")))})

    dr25 = {r["kepoi_name"]: r for r in tables["dr25_koi"]}
    rows = [koi_row(n, kid, disp, p, t0, mast, skye, dr25) for n, kid, disp, p, t0 in kois]
    rows_v1 = [koi_row(n, kid, disp, p, t0, mast, skye_v1, dr25) for n, kid, disp, p, t0 in kois]
    for r in rows_v1:  # koi_row bins with BIN0; redo the v1-origin flags with BIN0_V1
        if r["status"] == "ok":
            evs = [float(t) for t in r["event_times"].split()]
            fl = [t for t in evs if bin_index(t, BIN0_V1) in skye_v1.get(r["skygroup"], ())]
            r.update({"n_flagged": len(fl), "good": len(evs) - len(fl),
                      "would_fail": int(r["eligible"] and len(evs) - len(fl) < MIN_GOOD)})
    write_outputs(args.out_dir, rows, rows_v1, tce_rows, rv_table, rv_comments, rv_prov, rv_error, bin_rows,
                  sg_info, fetched, mast_errors,
                  {"tce_rows": len(tces), "tce_stars": len(tce_stars),
                   "tce_stars_with_skygroup": sum(1 for k in tce_stars if k in mast), "tces_used": len(tce_rows),
                   "koi_rows": len(kois), "koi_stars": len(koi_stars),
                   "koi_stars_with_skygroup": sum(1 for k in koi_stars if k in mast)})
    return 0


def validation(tce_rows, rv_table, rv_comments):
    """Data checks and the TCE-level comparison with DR25's own Skye flags."""
    found = [r for r in tce_rows if r["rv_found"]]
    commented = [k for k, c in rv_comments.items() if has_skye(c)]
    commented_flag1 = sum(1 for k in commented if k in rv_table and rv_table[k][3] == 1)
    return {
        "rv_rows": len(rv_table),
        "tces_with_skygroup": len(tce_rows),
        "tces_found_in_rv": len(found),
        "join_fraction": round(len(found) / len(tce_rows), 4) if tce_rows else None,
        "rv_skye_flag_1_all_periods": sum(1 for v in rv_table.values() if v[3] == 1),
        "comment_skye_tces": len(commented),
        "comment_skye_with_flag_1": commented_flag1,
        "comment_flag_fraction": round(commented_flag1 / len(commented), 4) if commented else None,
        "events_equal_nrealtrans": round(sum(1 for r in found if r["n_events"] == r["rv_nrealtrans"])
                                         / len(found), 4) if found else None,
        "primary": confusion([(int(r["n_flagged"] > 0), r["rv_skye"]) for r in found]),
        "v1_bins": confusion([(int(r["n_flagged_v1bins"] > 0), r["rv_skye"]) for r in found]),
    }


def write_outputs(out_dir, rows, rows_v1, tce_rows, rv_table, rv_comments, rv_prov, rv_error, bin_rows, sg_info,
                  fetched, mast_errors, cov):
    groups = {k: group_stats(rows, k) for k in ("dr25_pc", "dr25_skye", "never_dr25")}
    groups_v1 = {k: group_stats(rows_v1, k) for k in ("dr25_pc", "dr25_skye", "never_dr25")}
    named = {n: next(({k: r[k] for k in ("skygroup", "n_events", "n_flagged", "good", "would_fail",
                                         "flagged_times", "event_times")} for r in rows if r["kepoi_name"] == n),
                     None) for n in NAMED}
    val = validation(tce_rows, rv_table, rv_comments)
    pc, nv = groups["dr25_pc"], groups["never_dr25"]
    census, census_p = census_test((nv["fails"], nv["eligible"]), (pc["fails"], pc["eligible"]))
    tsf = cov["tce_stars_with_skygroup"] / cov["tce_stars"] if cov["tce_stars"] else 0.0
    ksf = cov["koi_stars_with_skygroup"] / cov["koi_stars"] if cov["koi_stars"] else 0.0
    prim = val["primary"]
    tests = {
        "p2_data": bool(tsf >= 0.99 and ksf >= 0.99 and val["rv_rows"] >= RV_ROWS_MIN
                        and (val["join_fraction"] or 0.0) >= RV_JOIN_MIN
                        and val["comment_skye_tces"] >= RV_COMMENT_N_MIN
                        and (val["comment_flag_fraction"] or 0.0) >= RV_COMMENT_MIN),
        "p3_tce_recall": (prim["recall"] or 0.0) >= TCE_RECALL_MIN,
        "p4_tce_precision": (prim["precision"] or 0.0) >= TCE_PRECISION_MIN,
        "p5_koi_skye_recall": (groups["dr25_skye"]["flagged_fraction"] or 0.0) >= SKYE_RECALL_MIN,
        "p6_pc_fail_fraction": pc["fail_fraction"] is not None and pc["fail_fraction"] <= PC_FAIL_MAX,
        "p7_named_fail": all(v is not None and v["would_fail"] == 1 for v in named.values()),
        "p8_census": census, "p8_p": census_p}
    with open(os.path.abspath(__file__), "rb") as f:
        own_sha = hashlib.sha256(f.read()).hexdigest()
    stats = {"version": VERSION, "skye_census_sha256": own_sha,
             "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "params": {"p_min": P_MIN, "bin0": BIN0, "n_sigma": N_SIGMA, "passes": PASSES, "min_good": MIN_GOOD,
                        "rv_skye_col": RV_SKYE_COL},
             "fetched": fetched, "robovetter": rv_prov, "robovetter_error": rv_error,
             "coverage": dict(cov, tce_star_fraction=round(tsf, 4), koi_star_fraction=round(ksf, 4)),
             "mast_errors": mast_errors, "skygroups": len(sg_info),
             "skygroups_with_skye_bins": sum(1 for v in sg_info.values() if v["skye_bins"]),
             "validation": val, "groups": groups, "groups_v1_bins": groups_v1, "named": named, "tests": tests,
             "skygroup_info": {str(k): v for k, v in sg_info.items()}}
    with open(os.path.join(out_dir, "koi_skye.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KOI_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(out_dir, "tce_skye.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=TCE_FIELDS)
        w.writeheader()
        w.writerows(tce_rows)
    with open(os.path.join(out_dir, "skye_bins.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["skygroup", "bin", "start", "count", "rate", "threshold"])
        w.writeheader()
        w.writerows(bin_rows)
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)
    lines = [f"# skye-census {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY "
             "4.0. A re-implementation of DR25's Skye test (Thompson et al. 2018, A.3.7.4; Skye.py); leads, not "
             "dispositions.", "",
             "Tables: " + ", ".join(f"{k} from {v['source']} ({v['rows']} rows)" for k, v in fetched.items()) + ".",
             "",
             f"Skygroups: {stats['skygroups']}, with Skye bins: {stats['skygroups_with_skye_bins']}. "
             f"DR25 TCE stars with a skygroup: {cov['tce_stars_with_skygroup']} / {cov['tce_stars']}; KOI stars: "
             f"{cov['koi_stars_with_skygroup']} / {cov['koi_stars']}. MAST errors: {len(mast_errors)}. "
             f"Robovetter: {rv_error or 'loaded'}.", "",
             "## Validation against DR25's per-TCE Skye flags (P > 45 d)", "",
             "| bins | tp | fp | fn | tn | recall | precision |", "|---|---|---|---|---|---|---|"]
    lines += [f"| {k} | {v['tp']} | {v['fp']} | {v['fn']} | {v['tn']} | {v['recall']} | {v['precision']} |"
              for k, v in (("primary (Skye.py)", val["primary"]), ("v1 bins (exploratory)", val["v1_bins"]))]
    lines += ["", "Data checks: " + ", ".join(f"{k} = {val[k]}" for k in
                                             ("rv_rows", "tces_found_in_rv", "join_fraction", "comment_skye_tces",
                                              "comment_skye_with_flag_1", "comment_flag_fraction",
                                              "events_equal_nrealtrans")), "",
              "## KOI groups", "",
              "| bins | group | KOIs | with a flagged event | fraction | eligible (>= 3 events) | would fail | fraction |",
              "|---|---|---|---|---|---|---|---|"]
    for label, gs in (("primary", groups), ("v1 bins", groups_v1)):
        lines += [f"| {label} | {k} | {v['n']} | {v['with_flagged']} | {v['flagged_fraction']} | {v['eligible']} | "
                  f"{v['fails']} | {v['fail_fraction']} |" for k, v in gs.items()]
    lines += ["", "Tests: " + ", ".join(f"{k} = {v}" for k, v in tests.items()), "", "## Named", ""]
    lines += [f"- {n}: {v}" for n, v in named.items()]
    lines += ["", "## Candidates never scored by DR25 that would fail", "",
              "| KOI | P (d) | skygroup | events | flagged | flagged times |", "|---|---|---|---|---|---|"]
    lines += [f"| {r['kepoi_name']} | {r['period']} | {r['skygroup']} | {r['n_events']} | {r['n_flagged']} | "
              f"{r['flagged_times']} |" for r in rows if r["never_dr25"] == 1 and r["would_fail"] == 1]
    lines += ["", "## Candidates never scored by DR25 with at least one flagged event but enough good events", "",
              "| KOI | P (d) | skygroup | events | flagged | flagged times |", "|---|---|---|---|---|---|"]
    lines += [f"| {r['kepoi_name']} | {r['period']} | {r['skygroup']} | {r['n_events']} | {r['n_flagged']} | "
              f"{r['flagged_times']} |" for r in rows
              if r["never_dr25"] == 1 and r["status"] == "ok" and r["n_flagged"] and not r["would_fail"]]
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps({k: v for k, v in stats.items() if k != "skygroup_info"}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
