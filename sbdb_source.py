#!/usr/bin/env python3
# Apache-2.0. sbdb_source 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
"""Follow-up to sbdb_triplet 0.1.0: where do the diameters and albedos JPL's Small-Body Database serves come from,
and does the drift dH = H - H_fit depend on that source?

The bulk SBDB Query API has no reference field, so this draws a seeded random sample of scored rows that were not
seen before pre-registration (the 3 probe rows, plus every spkid in the published sample.csv and outliers.csv of
sbdb_triplet 0.1.0) and asks the single-object SBDB API (spk=..., phys-par=1) for the reference of each row's
diameter, albedo and H, one request at a time with a pause.

Pre-registered in findings/2026-10-20-sbdb-source-prereg.md; decisions S1-S3 are integer rules (decide_*).
Pure stdlib; needs sbdb_triplet.py 0.1.0 next to it."""
import argparse
import csv
import json
import os
import random
import re
import sys
import time

import sbdb_triplet as st

VERSION = "0.1.0"
DETAIL_API = "https://ssd-api.jpl.nasa.gov/sbdb.api"
GATE_TEXT = "SBDB diameter-source pre-registration"
SAMPLE_SEED = 2026101917
SAMPLE_SIZE = 1500
PAUSE_S = 1.0
SEEN_ROWS_EXPECTED = 340  # 40 in sample.csv + 300 in outliers.csv
OUT_HEADER = ["spkid", "pdes", "H", "diameter", "albedo", "dh_e4", "tol_e4", "shifted", "status", "d_class",
              "d_ref", "p_ref", "h_ref", "h_ref_year", "detail_diameter", "detail_albedo"]


def source_class(ref):
    """Coarse source of a diameter reference string: neowise, akari, iras, other or none."""
    s = (ref or "").strip().lower()
    if not s:
        return "none"
    if "wise" in s:
        return "neowise"
    if "akari" in s or "usui" in s:
        return "akari"
    if "iras" in s or "simps" in s or "tedesco" in s:
        return "iras"
    return "other"


def ref_year(ref):
    """First 4-digit year 1900-2099 in a reference string, as int; None if there is none."""
    m = re.search(r"(?<!\d)(19|20)(\d\d)", ref or "")
    return int(m.group(1) + m.group(2)) if m else None


def detail_url(spkid):
    return DETAIL_API + "?spk=%d&phys-par=1" % int(spkid)


def phys_refs(body):
    """(status, {name: (value, ref)}) from one single-object SBDB API payload."""
    try:
        j = json.loads(body.decode("utf-8"))
    except Exception:
        return "bad_json", {}
    pars = j.get("phys_par")
    if not isinstance(pars, list):
        return "no_phys_par", {}
    out = {}
    for p in pars:
        if isinstance(p, dict) and p.get("name") in ("H", "diameter", "albedo"):
            out[p["name"]] = (p.get("value"), p.get("ref"))
    return ("fetched" if "diameter" in out else "no_diameter"), out


def load_seen(paths):
    """Set of int spkids in the given CSV files (column 'spkid')."""
    seen = set()
    for path in paths:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                seen.add(int(row["spkid"]))
    return seen


def make_pool(scored, seen):
    """Scored (row, metrics) pairs whose spkid is not in seen, in spkid order."""
    pool = [(r, m) for r, m in scored if int(r["spkid"]) not in seen]
    return sorted(pool, key=lambda rm: int(rm[0]["spkid"]))


def draw_sample(pool, n=SAMPLE_SIZE, seed=SAMPLE_SEED):
    rng = random.Random(seed)
    return [pool[i] for i in sorted(rng.sample(range(len(pool)), min(n, len(pool))))]


def decide_s1(m, nw):
    """S1: at least 80 % of fetched rows have a NEOWISE diameter. m fetched, nw NEOWISE."""
    if m < 1000:
        return "underpowered"
    return "holds" if 10 * nw >= 8 * m else "fails"


def decide_s2(m, same):
    """S2: for at least 95 % of fetched rows the albedo reference equals the diameter reference."""
    if m < 1000:
        return "underpowered"
    return "holds" if 20 * same >= 19 * m else "fails"


def decide_s3(nw_dh_e4, non_dh_e4):
    """S3: lower-median dH of NEOWISE rows exceeds that of AKARI/IRAS/other rows by at least 0.1 mag."""
    if len(nw_dh_e4) < 30 or len(non_dh_e4) < 30:
        return "underpowered"
    return "holds" if st.lower_median(nw_dh_e4) - st.lower_median(non_dh_e4) >= 1000 else "fails"


def score(records):
    """Decisions and descriptive tallies from the per-row output records (dicts with OUT_HEADER keys)."""
    fetched = [r for r in records if r["status"] == "fetched"]
    m = len(fetched)
    nw = [r for r in fetched if r["d_class"] == "neowise"]
    non = [r for r in fetched if r["d_class"] in ("akari", "iras", "other")]
    same = sum(1 for r in fetched if r["p_ref"] == r["d_ref"])
    decisions = {
        "S1": {"n_fetched": m, "n_neowise": len(nw), "decision": decide_s1(m, len(nw))},
        "S2": {"n_fetched": m, "n_same_ref": same, "decision": decide_s2(m, same)},
        "S3": {"n_neowise": len(nw), "n_other_sources": len(non),
               "median_neowise_e4": st.lower_median([r["dh_e4"] for r in nw]),
               "median_other_e4": st.lower_median([r["dh_e4"] for r in non]),
               "decision": decide_s3([r["dh_e4"] for r in nw], [r["dh_e4"] for r in non])},
    }
    desc = {"status": {}, "d_class": {}, "d_ref": {}, "h_ref_year": {}, "by_class_dh_quantiles_e4": {}}
    for r in records:
        desc["status"][r["status"]] = desc["status"].get(r["status"], 0) + 1
    for r in fetched:
        for key, val in (("d_class", r["d_class"]), ("d_ref", r["d_ref"] or ""), ("h_ref_year", str(r["h_ref_year"]))):
            desc[key][val] = desc[key].get(val, 0) + 1
    for cls in sorted(desc["d_class"]):
        desc["by_class_dh_quantiles_e4"][cls] = st.quantiles_e4([r["dh_e4"] for r in fetched if r["d_class"] == cls])
    desc["detail_value_mismatch"] = sum(1 for r in fetched if r["detail_diameter"] != r["diameter"]
                                        or r["detail_albedo"] != r["albedo"])
    return decisions, desc


def record(r, m, status, refs):
    d_val, d_ref = refs.get("diameter", (None, None))
    p_val, p_ref = refs.get("albedo", (None, None))
    _, h_ref = refs.get("H", (None, None))
    return {"spkid": int(r["spkid"]), "pdes": r.get("pdes"), "H": r.get("H"), "diameter": r.get("diameter"),
            "albedo": r.get("albedo"), "dh_e4": m["dh_e4"], "tol_e4": m["tol_e4"], "shifted": int(m["shifted"]),
            "status": status, "d_class": source_class(d_ref) if status == "fetched" else "",
            "d_ref": d_ref, "p_ref": p_ref, "h_ref": h_ref, "h_ref_year": ref_year(h_ref),
            "detail_diameter": d_val, "detail_albedo": p_val}


def download_all():
    """(rows, pages, counts) of the whole bulk query, as in sbdb_triplet.main."""
    rows, pages, counts = [], [], []
    offset = 0
    while True:
        body = st.fetch_bytes(st.page_url(offset))
        count, fields, page_rows = st.parse_page(body)
        pages.append({"offset": offset, "rows": len(page_rows), "bytes": len(body)})
        counts.append(count)
        if fields != st.FIELDS:
            raise ValueError("unexpected fields %r" % fields)
        rows.extend(page_rows)
        offset += len(page_rows)
        if not page_rows or offset >= count:
            return rows, pages, counts


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
        seen = load_seen(args.seen)
    except (OSError, KeyError, ValueError):
        seen = None
    summary["seen_rows"] = None if seen is None else len(seen)
    if not summary["gate"] or seen is None or len(seen) != SEEN_ROWS_EXPECTED:
        summary["error"] = "gate note or seen-row files missing or wrong; nothing downloaded"
        with open(os.path.join(args.out_dir, "summary.json"), "w") as f:
            json.dump(summary, f, indent=1)
        print(json.dumps(summary))
        return 2
    rows, pages, counts = download_all()
    spkids = [r.get("spkid") for r in rows]
    summary["pages"] = pages
    summary["checks"] = {"count_stable": len(set(counts)) == 1, "rows_equal_count": len(rows) == counts[0],
                         "no_duplicate_spkid": len(set(spkids)) == len(spkids)}
    summary["api_count"] = counts[0]
    scored, status, _, _ = st.analyse(rows)
    pool = make_pool(scored, seen | st.EXCLUDED_SPKIDS)
    sample = draw_sample(pool, args.n)
    summary["bulk_status"] = status
    summary["pool"] = len(pool)
    summary["sample"] = len(sample)
    records = []
    for r, m in sample:
        try:
            st_, refs = phys_refs(st.fetch_bytes(detail_url(r["spkid"]), tries=3, timeout=60))
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
    with open(os.path.join(args.out_dir, "sources.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_HEADER)
        w.writeheader()
        w.writerows(records)
    print(json.dumps({"sample": len(sample), "decisions": decisions, "checks": summary["checks"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
