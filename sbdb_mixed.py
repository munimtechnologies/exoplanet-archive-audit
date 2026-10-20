#!/usr/bin/env python3
# Apache-2.0. sbdb_mixed 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
"""Follow-up to sbdb_source 0.1.0: how often does JPL's Small-Body Database serve a NEOWISE diameter and an albedo
taken from two different NEOWISE papers, and do such mixed rows drift negatively (served H brighter than the
albedo implies) more often than rows whose diameter and albedo share one reference?

In sbdb_source's sample (published, and excluded here) 31 of 1,497 NEOWISE rows were mixed and 19 of those 31 had
dH < 0, against 157 of the 1,466 single-reference rows. This draws a fresh seeded sample of 4,000 rows that were not
seen before pre-registration and asks the single-object SBDB API for the references, one request at a time.

Pre-registered in findings/2026-10-20-sbdb-mixed-prereg.md; decisions M1-M2 are integer rules (decide_*).
Pure stdlib; needs sbdb_triplet.py 0.1.0 and sbdb_source.py 0.1.0 next to it."""
import argparse
import csv
import json
import os
import re
import sys
import time

import sbdb_source as ss
import sbdb_triplet as st

VERSION = "0.1.0"
GATE_TEXT = "SBDB mixed-reference pre-registration"
SAMPLE_SEED = 2026102000
SAMPLE_SIZE = 4000
PAUSE_S = 1.0
SEEN_ROWS_EXPECTED = 1840  # 40 sample.csv + 300 outliers.csv (sbdb_triplet) + 1,500 sources.csv (sbdb_source)
# Probe rows of the close-approach preparation (sbdb_cad 0.1.0); excluded to be safe, never scored here.
EXTRA_EXCLUDED = {20000433, 20000719, 20000887, 20099942}
OUT_HEADER = ss.OUT_HEADER + ["group", "d_bib", "p_bib"]


def bibcode(ref):
    """ADS bibcode inside a NEOWISE PDS reference string ('... (http://adsabs.harvard.edu/abs/<bibcode>)'); else None."""
    m = re.search(r"/abs/([^)\s]+)\)", ref or "")
    return m.group(1) if m else None


def ref_year(ref):
    """Year of a JPL-style H reference ('E2026L10', 'E2026-EA1') or of an ADS bibcode in a reference; else None.

    Replaces sbdb_source.ref_year, which read MPC references such as 'MPO190119' as the year 1901."""
    s = (ref or "").strip()
    m = re.match(r"E((?:19|20)\d\d)", s)
    if m:
        return int(m.group(1))
    b = bibcode(s)
    if b and re.match(r"(?:19|20)\d\d", b):
        return int(b[:4])
    return None


def group(rec):
    """'same', 'mixed' or 'other' for one output record.

    same: fetched, NEOWISE diameter, albedo reference string equal to the diameter's.
    mixed: fetched, NEOWISE diameter, albedo reference non-empty, NEOWISE too, and different from the diameter's.
    other: everything else (not fetched, non-NEOWISE diameter, missing or non-NEOWISE albedo reference)."""
    if rec["status"] != "fetched" or rec["d_class"] != "neowise":
        return "other"
    if rec["p_ref"] == rec["d_ref"]:
        return "same"
    if rec["p_ref"] and ss.source_class(rec["p_ref"]) == "neowise":
        return "mixed"
    return "other"


def decide_m1(n_nw, n_mixed):
    """M1: mixed rows are between 1 % and 5 % of NEOWISE-diameter rows (same + mixed + other NEOWISE)."""
    if n_nw < 3000:
        return "underpowered"
    return "holds" if n_nw <= 100 * n_mixed <= 5 * n_nw else "fails"


def decide_m2(neg_m, n_m, neg_s, n_s):
    """M2: share of dH < 0 among mixed rows exceeds that among same rows by at least 0.25 (integer form)."""
    if n_m < 50 or n_s < 50:
        return "underpowered"
    return "holds" if 4 * (neg_m * n_s - neg_s * n_m) >= n_m * n_s else "fails"


def score(records):
    """Decisions and descriptive tallies from output records (dicts with OUT_HEADER keys)."""
    nw = [r for r in records if r["status"] == "fetched" and r["d_class"] == "neowise"]
    same = [r for r in records if r["group"] == "same"]
    mixed = [r for r in records if r["group"] == "mixed"]
    neg_s = sum(1 for r in same if r["dh_e4"] < 0)
    neg_m = sum(1 for r in mixed if r["dh_e4"] < 0)
    decisions = {
        "M1": {"n_neowise": len(nw), "n_mixed": len(mixed), "decision": decide_m1(len(nw), len(mixed))},
        "M2": {"n_mixed": len(mixed), "neg_mixed": neg_m, "n_same": len(same), "neg_same": neg_s,
               "decision": decide_m2(neg_m, len(mixed), neg_s, len(same))},
    }
    desc = {"status": {}, "group": {}, "mixed_pairs": {}, "by_group_dh_quantiles_e4": {},
            "by_group_abs_dh_over_0p5mag": {}, "h_ref_year": {}}
    for r in records:
        desc["status"][r["status"]] = desc["status"].get(r["status"], 0) + 1
        desc["group"][r["group"]] = desc["group"].get(r["group"], 0) + 1
        if r["status"] == "fetched":
            y = str(r["h_ref_year"])
            desc["h_ref_year"][y] = desc["h_ref_year"].get(y, 0) + 1
    for r in mixed:
        key = "%s -> %s" % (r["d_bib"], r["p_bib"])
        desc["mixed_pairs"][key] = desc["mixed_pairs"].get(key, 0) + 1
    for g in sorted(desc["group"]):
        vals = [r["dh_e4"] for r in records if r["group"] == g and r["status"] == "fetched"]
        desc["by_group_dh_quantiles_e4"][g] = st.quantiles_e4(vals)
        desc["by_group_abs_dh_over_0p5mag"][g] = sum(1 for v in vals if abs(v) > 5000)
    desc["detail_value_mismatch"] = sum(1 for r in records if r["status"] == "fetched" and
                                        (r["detail_diameter"] != r["diameter"] or r["detail_albedo"] != r["albedo"]))
    return decisions, desc


def record(r, m, status, refs):
    rec = ss.record(r, m, status, refs)
    rec["h_ref_year"] = ref_year(rec["h_ref"])
    rec["d_bib"] = bibcode(rec["d_ref"])
    rec["p_bib"] = bibcode(rec["p_ref"])
    rec["group"] = group(rec)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-note", required=True)
    ap.add_argument("--seen", nargs="+", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--n", type=int, default=SAMPLE_SIZE)
    ap.add_argument("--pause", type=float, default=PAUSE_S)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    summary = {"version": VERSION, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        with open(args.gate_note, "rb") as f:
            summary["gate"] = GATE_TEXT.encode("utf-8") in f.read()
    except OSError:
        summary["gate"] = False
    try:
        seen = ss.load_seen(args.seen)
    except (OSError, KeyError, ValueError):
        seen = None
    summary["seen_rows"] = None if seen is None else len(seen)
    if not summary["gate"] or seen is None or len(seen) != SEEN_ROWS_EXPECTED:
        summary["error"] = "gate note or seen-row files missing or wrong; nothing downloaded"
        with open(os.path.join(args.out_dir, "summary.json"), "w") as f:
            json.dump(summary, f, indent=1)
        print(json.dumps(summary))
        return 2
    rows, pages, counts = ss.download_all()
    spkids = [r.get("spkid") for r in rows]
    summary["pages"] = pages
    summary["checks"] = {"count_stable": len(set(counts)) == 1, "rows_equal_count": len(rows) == counts[0],
                         "no_duplicate_spkid": len(set(spkids)) == len(spkids)}
    summary["api_count"] = counts[0]
    scored, status, _, _ = st.analyse(rows)
    pool = ss.make_pool(scored, seen | st.EXCLUDED_SPKIDS | EXTRA_EXCLUDED)
    sample = ss.draw_sample(pool, args.n, seed=SAMPLE_SEED)
    summary["bulk_status"] = status
    summary["pool"] = len(pool)
    summary["sample"] = len(sample)
    records = []
    for r, m in sample:
        try:
            st_, refs = ss.phys_refs(st.fetch_bytes(ss.detail_url(r["spkid"]), tries=3, timeout=60))
        except Exception:
            st_, refs = "fetch_error", {}
        records.append(record(r, m, st_, refs))
        time.sleep(args.pause)
    decisions, desc = score(records)
    summary["decisions"] = decisions
    summary["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(args.out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    with open(os.path.join(args.out_dir, "decisions.json"), "w") as f:
        json.dump(decisions, f, indent=1)
    with open(os.path.join(args.out_dir, "descriptive.json"), "w") as f:
        json.dump(desc, f, indent=1)
    with open(os.path.join(args.out_dir, "mixed.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_HEADER)
        w.writeheader()
        w.writerows(records)
    print(json.dumps({"sample": len(sample), "decisions": decisions, "checks": summary["checks"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
