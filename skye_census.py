"""skye_census: DR25's Skye test, re-run on every long-period KOI, including the candidates DR25 never vetted.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.
Pre-registration: findings/2026-10-18-skye-census-prereg.md in munimtechnologies/exoplanet-archive-audit.

Thompson et al. 2018 (ApJS 235, 38; appendix A.3.7.4, "Skye") flag individual transits that coincide with
clusters of other TCE events in the same skygroup: every DR25 obsTCE with P > 45 d contributes its individual
events, each skygroup's events go into 1.0 d bins, and with R the mean events per bin (recomputed after rejecting
bins above R + 3 sqrt(R) until stable) the bins above the final threshold are bad. A TCE fails when fewer than
three good events remain. This re-implementation:
  events   t0 + n P inside the quarters the star was observed in long cadence (MAST data_search), with the
           quarter spans below (intra-quarter gaps are not removed);
  bins     [BIN0 + k, BIN0 + k + 1) d; a bin enters the rate only if its centre lies in a quarter span;
  KOIs     every cumulative-table KOI with P > 45 d: events, events in a Skye bin of its own skygroup,
           good = events - flagged; eligible = events >= 3; would_fail = eligible and good < 3.
Groups: dr25_pc (in the DR25 KOI table as CANDIDATE), dr25_skye (DR25 KOI table, INDIV_TRANS_SKYE in
koi_comment), never_dr25 (cumulative CANDIDATE, absent from the DR25 KOI table, so never scored by DR25).

Usage: python skye_census.py --out-dir /out/skye [--in-dir dir-with-cached-tap-csvs]
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
import time
import urllib.parse
import urllib.request

VERSION = "0.1.0"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={}&format=csv"
MAST = ("https://archive.stsci.edu/kepler/data_search/search.php?action=Search&ktc_kepler_id={}"
        "&ktc_target_type=LC&outputformat=CSV&max_records={}"
        "&selectedColumnsCsv=ktc_kepler_id,sci_data_quarter,sci_skygroup_id,ktc_target_type")
QUERIES = {
    "dr25_tce": "select kepid,tce_plnt_num,tce_period,tce_time0bk from q1_q17_dr25_tce",
    "cumulative": "select kepoi_name,kepid,koi_disposition,koi_period,koi_time0bk from cumulative",
    "dr25_koi": "select kepoi_name,kepid,koi_pdisposition,koi_period,koi_time0bk,koi_comment from q1_q17_dr25_koi",
}
# Long-cadence spans (BKJD) of quarters 1-17: first and last cadences of KIC 9018021 and KIC 6359929
QUARTERS = {1: (131.51, 164.98), 2: (169.52, 258.47), 3: (260.22, 349.50), 4: (352.38, 442.20),
            5: (443.49, 538.16), 6: (539.47, 629.30), 7: (630.20, 719.55), 8: (735.38, 802.34),
            9: (808.54, 905.93), 10: (906.87, 1000.27), 11: (1001.23, 1098.33), 12: (1099.43, 1182.02),
            13: (1182.76, 1273.00), 14: (1274.20, 1371.32), 15: (1373.51, 1471.14), 16: (1472.12, 1557.96),
            17: (1559.25, 1591.00)}
P_MIN = 45.0
BIN0 = 131.0
N_SIGMA = 3.0
MIN_GOOD = 3
CHUNK = 100
NAMED = ("K05269.01", "K05227.01")
# Pre-registered thresholds
COVERAGE_MIN = 0.99
SKYE_RECALL_MIN = 0.70
PC_FAIL_MAX = 0.10
CENSUS_RATIO = 2.0
CENSUS_FLOOR = 0.02
CENSUS_P = 0.01

KOI_FIELDS = ["kepoi_name", "kepid", "disposition", "period", "t0", "skygroup", "status", "n_events",
              "n_flagged", "good", "eligible", "would_fail", "in_dr25", "dr25_pc", "dr25_skye", "never_dr25",
              "flagged_times", "event_times"]


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
    lo = min(a for a, _ in spans.values())
    hi = max(b for _, b in spans.values())
    return [k for k in range(bin_index(lo, bin0), bin_index(hi, bin0) + 1)
            if any(a <= bin0 + k + 0.5 <= b for a, b in spans.values())]


def skye_bins(counts, bins, n_sigma=N_SIGMA):
    """(Skye bins, final rate, final threshold). counts: bin -> events; bins: the bins that enter the rate.

    The rate is the mean count over the rate bins not rejected; bins above rate + n_sigma sqrt(rate) are
    rejected and the rate recomputed until the rejected set stops changing. Every bin with a count above the
    final threshold is a Skye bin, inside the rate bins or not."""
    rejected = set()
    r = thr = 0.0
    for _ in range(1000):
        kept = [k for k in bins if k not in rejected]
        r = sum(counts.get(k, 0) for k in kept) / len(kept) if kept else 0.0
        thr = r + n_sigma * math.sqrt(r)
        new = {k for k in bins if counts.get(k, 0) > thr}
        if new == rejected:
            break
        rejected = new
    return {k for k, c in counts.items() if c > thr}, r, thr


def binom_tail(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(max(k, 0), n + 1))


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


def koi_row(name, kid, disp, p, t0, mast, skye, dr25, spans=QUARTERS):
    """One KOI's Skye result. mast: kepid -> (skygroup, quarters); skye: skygroup -> set of Skye bins;
    dr25: kepoi_name -> DR25 KOI row."""
    d = dr25.get(name)
    row = {"kepoi_name": name, "kepid": kid, "disposition": disp, "period": p, "t0": t0,
           "in_dr25": int(d is not None),
           "dr25_pc": int(d is not None and d.get("koi_pdisposition") == "CANDIDATE"),
           "dr25_skye": int(d is not None and "INDIV_TRANS_SKYE" in (d.get("koi_comment") or "")),
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


def http_bytes(url, tries=3, timeout=180):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mv2-skye-census/0.1 (Munim, Inc.; "
                                                                     "mv2@munimtech.com)"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # retried, then raised
            last = e
            time.sleep(5 * (k + 1))
    raise last


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


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--in-dir", default="")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    tables, fetched = {}, {}
    for name, q in QUERIES.items():
        cached = os.path.join(args.in_dir, name + ".csv") if args.in_dir else ""
        if cached and os.path.isfile(cached):
            with open(cached, "rb") as f:
                data = f.read()
        else:
            data = http_bytes(TAP.format(urllib.parse.quote_plus(q)))
        with open(os.path.join(args.out_dir, name + ".csv"), "wb") as f:
            f.write(data)
        tables[name] = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
        fetched[name] = {"query": q, "rows": len(tables[name]), "sha256": hashlib.sha256(data).hexdigest()}
        print(json.dumps({name: fetched[name]}), flush=True)

    tces = []
    for r in tables["dr25_tce"]:
        p, t0 = fnum(r.get("tce_period")), fnum(r.get("tce_time0bk"))
        if p is not None and t0 is not None and p > P_MIN and (r.get("kepid") or "").isdigit():
            tces.append((int(r["kepid"]), p, t0))
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

    counts, tces_used = {}, 0
    for kid, p, t0 in tces:
        if kid not in mast:
            continue
        sg, quarters = mast[kid]
        tces_used += 1
        c = counts.setdefault(sg, {})
        for t in events(p, t0, quarters):
            k = bin_index(t)
            c[k] = c.get(k, 0) + 1
    bins = rate_bins()
    skye, bin_rows, sg_info = {}, [], {}
    for sg in sorted(counts):
        flagged, r, thr = skye_bins(counts[sg], bins)
        skye[sg] = flagged
        sg_info[sg] = {"events": sum(counts[sg].values()), "rate": round(r, 4), "threshold": round(thr, 4),
                       "skye_bins": len(flagged)}
        bin_rows += [{"skygroup": sg, "bin": k, "start": BIN0 + k, "count": counts[sg][k], "rate": round(r, 4),
                      "threshold": round(thr, 4)} for k in sorted(flagged)]

    dr25 = {r["kepoi_name"]: r for r in tables["dr25_koi"]}
    rows = [koi_row(n, kid, disp, p, t0, mast, skye, dr25) for n, kid, disp, p, t0 in kois]
    write_outputs(args.out_dir, rows, bin_rows, sg_info, fetched, mast_errors,
                  {"tce_rows": len(tces), "tce_stars": len(tce_stars),
                   "tce_stars_with_skygroup": sum(1 for k in tce_stars if k in mast), "tces_used": tces_used,
                   "koi_rows": len(kois), "koi_stars": len(koi_stars),
                   "koi_stars_with_skygroup": sum(1 for k in koi_stars if k in mast)})
    return 0


def write_outputs(out_dir, rows, bin_rows, sg_info, fetched, mast_errors, cov):
    groups = {k: group_stats(rows, k) for k in ("dr25_pc", "dr25_skye", "never_dr25")}
    named = {n: next(({k: r[k] for k in ("skygroup", "n_events", "n_flagged", "good", "would_fail",
                                         "flagged_times", "event_times")} for r in rows if r["kepoi_name"] == n),
                     None) for n in NAMED}
    pc, nv = groups["dr25_pc"], groups["never_dr25"]
    p6, p6_p = census_test((nv["fails"], nv["eligible"]), (pc["fails"], pc["eligible"]))
    tsf = cov["tce_stars_with_skygroup"] / cov["tce_stars"] if cov["tce_stars"] else 0.0
    ksf = cov["koi_stars_with_skygroup"] / cov["koi_stars"] if cov["koi_stars"] else 0.0
    tests = {
        "p2_coverage": bool(tsf >= COVERAGE_MIN and ksf >= COVERAGE_MIN),
        "p3_skye_recall": (groups["dr25_skye"]["flagged_fraction"] or 0.0) >= SKYE_RECALL_MIN,
        "p4_pc_fail_fraction": pc["fail_fraction"] is not None and pc["fail_fraction"] <= PC_FAIL_MAX,
        "p5_named_fail": all(v is not None and v["would_fail"] == 1 for v in named.values()),
        "p6_census": p6, "p6_p": p6_p}
    with open(os.path.abspath(__file__), "rb") as f:
        own_sha = hashlib.sha256(f.read()).hexdigest()
    stats = {"version": VERSION, "skye_census_sha256": own_sha,
             "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "params": {"p_min": P_MIN, "bin0": BIN0, "n_sigma": N_SIGMA, "min_good": MIN_GOOD},
             "fetched": fetched, "coverage": dict(cov, tce_star_fraction=round(tsf, 4),
                                                  koi_star_fraction=round(ksf, 4)),
             "mast_errors": mast_errors, "skygroups": len(sg_info),
             "skygroups_with_skye_bins": sum(1 for v in sg_info.values() if v["skye_bins"]),
             "groups": groups, "named": named, "tests": tests,
             "skygroup_info": {str(k): v for k, v in sg_info.items()}}
    with open(os.path.join(out_dir, "koi_skye.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KOI_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(out_dir, "skye_bins.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["skygroup", "bin", "start", "count", "rate", "threshold"])
        w.writeheader()
        w.writerows(bin_rows)
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)
    lines = [f"# skye-census {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY "
             "4.0. A re-implementation of DR25's Skye test (Thompson et al. 2018, A.3.7.4); leads, not "
             "dispositions.", "",
             f"Skygroups: {stats['skygroups']}, with Skye bins: {stats['skygroups_with_skye_bins']}. "
             f"DR25 TCE stars with a skygroup: {cov['tce_stars_with_skygroup']} / {cov['tce_stars']}; KOI stars: "
             f"{cov['koi_stars_with_skygroup']} / {cov['koi_stars']}. MAST errors: {len(mast_errors)}.", "",
             "| group | KOIs | with a flagged event | fraction | eligible (>= 3 events) | would fail | fraction |",
             "|---|---|---|---|---|---|---|"]
    lines += [f"| {k} | {v['n']} | {v['with_flagged']} | {v['flagged_fraction']} | {v['eligible']} | "
              f"{v['fails']} | {v['fail_fraction']} |" for k, v in groups.items()]
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
