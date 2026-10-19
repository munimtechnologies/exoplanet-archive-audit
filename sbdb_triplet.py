#!/usr/bin/env python3
# Apache-2.0. sbdb_triplet 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
"""Check the diameter D, geometric albedo p and absolute magnitude H that JPL's Small-Body Database (SBDB) serves
for each asteroid against the identity D[km] = 1329 / sqrt(p) * 10^(-H/5).

An albedo is usually computed from a measured diameter and the H known at the time. Solving the identity for H
gives H_fit = -5 log10(D sqrt(p) / 1329), the H the served albedo implies, and dH = H - H_fit is how far the
served H has moved since. A row is "shifted" when |dH| exceeds what rounding of the three served strings
(worst case over the corners of their last-digit intervals) plus 0.01 mag allows.

Pre-registered in findings/2026-10-19-sbdb-triplet-prereg.md; decisions P1-P3 are integer rules (decide_*).
Pure stdlib; the job downloads the SBDB Query API pages itself."""
import argparse
import csv
import hashlib
import json
import math
import os
import random
import sys
import time
import urllib.parse
import urllib.request

VERSION = "0.1.0"
API = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
FIELDS = ["spkid", "pdes", "full_name", "class", "neo", "H", "diameter", "albedo", "diameter_sigma"]
CDATA = '{"AND":["diameter|DF","albedo|DF","H|DF"]}'
PAGE = 20000
CONST_KM = 1329.0
SLACK_E4 = 100  # 0.01 mag, in units of 1e-4 mag
GATE_TEXT = "SBDB triplet pre-registration"
# Seen in a 3-row format probe before pre-registration (Ceres, Pallas, Juno); never scored.
EXCLUDED_SPKIDS = {20000001, 20000002, 20000003}
SAMPLE_SEED = 2026101916
SAMPLE_SIZE = 40
H_BINS = [(-99.0, 10.0), (10.0, 12.0), (12.0, 14.0), (14.0, 16.0), (16.0, 18.0), (18.0, 99.0)]


def half_unit(s):
    """Half of the last-digit unit of a plain decimal string ('0.090' -> 0.0005, '939' -> 0.5); None otherwise."""
    s = s.strip()
    if not s or "e" in s or "E" in s:
        return None
    body = s.lstrip("+-")
    if body.count(".") > 1 or not body.replace(".", "").isdigit():
        return None
    if "." in body:
        return 0.5 * 10.0 ** -len(body.split(".")[1])
    return 0.5


def h_fit(d_km, p):
    """H implied by diameter d_km and geometric albedo p."""
    return -5.0 * math.log10(d_km * math.sqrt(p) / CONST_KM)


def row_metrics(h_s, d_s, p_s):
    """dict with status, and for status 'ok' also h, d, p, h_fit, dh_e4, tol_e4, shifted, p_now."""
    uh, ud, up = half_unit(h_s), half_unit(d_s), half_unit(p_s)
    if uh is None or ud is None or up is None:
        return {"status": "unparsed"}
    h, d, p = float(h_s), float(d_s), float(p_s)
    if d <= 0 or p <= 0:
        return {"status": "nonpositive"}
    if d - ud <= 0 or p - up <= 0:
        return {"status": "too_coarse"}
    hf = h_fit(d, p)
    dev = max(abs(h_fit(dd, pp) - hf) for dd in (d - ud, d + ud) for pp in (p - up, p + up))
    tol_e4 = math.ceil((dev + uh) * 1e4) + SLACK_E4
    dh_e4 = int(round((h - hf) * 1e4))
    return {"status": "ok", "h": h, "d": d, "p": p, "h_fit": hf, "dh_e4": dh_e4, "tol_e4": tol_e4,
            "shifted": abs(dh_e4) > tol_e4, "p_now": p * 10.0 ** (-0.4 * (h - hf))}


def lower_median(values):
    v = sorted(values)
    return v[(len(v) - 1) // 2] if v else None


def quantiles_e4(values, qs=(5, 25, 50, 75, 95)):
    """Nearest-rank quantiles of integer values (None when empty)."""
    v = sorted(values)
    if not v:
        return {str(q): None for q in qs}
    return {str(q): v[max(0, (q * len(v) + 99) // 100 - 1)] for q in qs}


def decide_p1(n, k):
    """P1: at least half of the scored rows are shifted. n scored, k shifted."""
    if n < 1000:
        return "underpowered"
    return "holds" if 2 * k >= n else "fails"


def decide_p2(k, pos):
    """P2: at least 60 % of shifted rows have dH > 0 (served H fainter than the H the albedo implies)."""
    if k < 100:
        return "underpowered"
    return "holds" if 5 * pos >= 3 * k else "fails"


def decide_p3(faint_dh_e4, bright_dh_e4):
    """P3: lower-median dH of rows with H >= 14 exceeds that of rows with H < 10 by at least 0.1 mag."""
    if len(faint_dh_e4) < 100 or len(bright_dh_e4) < 100:
        return "underpowered"
    return "holds" if lower_median(faint_dh_e4) - lower_median(bright_dh_e4) >= 1000 else "fails"


def check_gate(note_path):
    """True if the fetched pre-registration note exists and carries GATE_TEXT."""
    try:
        with open(note_path, "rb") as f:
            return GATE_TEXT.encode("utf-8") in f.read()
    except OSError:
        return False


def page_url(offset, limit=PAGE):
    q = {"fields": ",".join(FIELDS), "sb-kind": "a", "sb-cdata": CDATA, "sort": "spkid",
         "limit": str(limit), "limit-from": str(offset)}
    return API + "?" + urllib.parse.urlencode(q)


def fetch_bytes(url, tries=4, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": "sbdb_triplet/" + VERSION + " (mv2@munimtech.com)"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(30 * (i + 1))


def parse_page(body):
    """(count, fields, rows as dicts of strings) from one SBDB Query API JSON page."""
    j = json.loads(body.decode("utf-8"))
    fields = j.get("fields", [])
    rows = []
    for rec in j.get("data", []):
        rows.append({f: (None if v is None else str(v)) for f, v in zip(fields, rec)})
    return int(j.get("count", 0)), fields, rows


def h_bin(h):
    for lo, hi in H_BINS:
        if lo <= h < hi:
            return "%g-%g" % (lo, hi) if lo > -99 and hi < 99 else ("<%g" % hi if lo <= -99 else ">=%g" % lo)
    return "none"


def analyse(rows):
    """Score every row; returns (scored list of (row, metrics), status counts, decisions, descriptive)."""
    status = {}
    scored = []
    for r in rows:
        if r.get("spkid") is not None and int(r["spkid"]) in EXCLUDED_SPKIDS:
            status["excluded_probe"] = status.get("excluded_probe", 0) + 1
            continue
        if not r.get("H") or not r.get("diameter") or not r.get("albedo"):
            m = {"status": "missing"}
        else:
            m = row_metrics(r["H"], r["diameter"], r["albedo"])
        status[m["status"]] = status.get(m["status"], 0) + 1
        if m["status"] == "ok":
            scored.append((r, m))
    n = len(scored)
    shifted = [m for _, m in scored if m["shifted"]]
    k = len(shifted)
    pos = sum(1 for m in shifted if m["dh_e4"] > 0)
    faint = [m["dh_e4"] for _, m in scored if m["h"] >= 14.0]
    bright = [m["dh_e4"] for _, m in scored if m["h"] < 10.0]
    decisions = {
        "P1": {"n_scored": n, "n_shifted": k, "decision": decide_p1(n, k)},
        "P2": {"n_shifted": k, "n_positive": pos, "decision": decide_p2(k, pos)},
        "P3": {"n_faint": len(faint), "n_bright": len(bright), "median_faint_e4": lower_median(faint),
               "median_bright_e4": lower_median(bright), "decision": decide_p3(faint, bright)},
    }
    groups = {}
    for r, m in scored:
        for key in ("all", "H " + h_bin(m["h"]), "neo " + str(r.get("neo")), "class " + str(r.get("class")),
                    "diameter_sigma " + ("defined" if r.get("diameter_sigma") else "missing")):
            g = groups.setdefault(key, {"dh": [], "shifted": 0})
            g["dh"].append(m["dh_e4"])
            g["shifted"] += 1 if m["shifted"] else 0
    desc = {key: {"n": len(g["dh"]), "shifted": g["shifted"], "dh_quantiles_e4": quantiles_e4(g["dh"])}
            for key, g in sorted(groups.items())}
    desc["abs_dh_over_1mag"] = sum(1 for _, m in scored if abs(m["dh_e4"]) > 10000)
    return scored, status, decisions, desc


def row_out(r, m):
    return [r.get("spkid"), r.get("pdes"), r.get("full_name", "").strip() if r.get("full_name") else "",
            r.get("class"), r.get("neo"), r.get("H"), r.get("diameter"), r.get("albedo"), r.get("diameter_sigma"),
            "%.4f" % m["h_fit"], m["dh_e4"], m["tol_e4"], int(m["shifted"]), "%.4f" % m["p_now"]]


ROW_HEADER = ["spkid", "pdes", "full_name", "class", "neo", "H", "diameter", "albedo", "diameter_sigma",
              "h_fit", "dh_e4", "tol_e4", "shifted", "p_now"]


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(ROW_HEADER)
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-note", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    summary = {"version": VERSION, "api": API, "fields": FIELDS, "cdata": CDATA,
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    summary["gate"] = check_gate(args.gate_note)
    if not summary["gate"]:
        summary["error"] = "gate note missing or lacks '%s'; nothing downloaded" % GATE_TEXT
        with open(os.path.join(args.out_dir, "summary.json"), "w") as f:
            json.dump(summary, f, indent=1)
        print(json.dumps(summary))
        return 2
    rows, pages, counts = [], [], []
    offset = 0
    while True:
        body = fetch_bytes(page_url(offset))
        count, fields, page_rows = parse_page(body)
        pages.append({"offset": offset, "rows": len(page_rows), "bytes": len(body),
                      "sha256": hashlib.sha256(body).hexdigest()})
        counts.append(count)
        if fields != FIELDS:
            summary["error"] = "unexpected fields %r" % fields
            break
        rows.extend(page_rows)
        offset += len(page_rows)
        if not page_rows or offset >= count:
            break
    summary["pages"] = pages
    spkids = [r.get("spkid") for r in rows]
    summary["checks"] = {
        "fields_as_requested": "error" not in summary,
        "count_stable": len(set(counts)) == 1,
        "rows_equal_count": bool(counts) and len(rows) == counts[0],
        "no_duplicate_spkid": len(set(spkids)) == len(spkids),
        "sorted_by_spkid": all(int(a) < int(b) for a, b in zip(spkids, spkids[1:])),
    }
    summary["api_count"] = counts[0] if counts else None
    summary["rows"] = len(rows)
    scored, status, decisions, desc = analyse(rows)
    summary["status_counts"] = status
    summary["decisions"] = decisions
    summary["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(args.out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    with open(os.path.join(args.out_dir, "decisions.json"), "w") as f:
        json.dump(decisions, f, indent=1)
    with open(os.path.join(args.out_dir, "descriptive.json"), "w") as f:
        json.dump(desc, f, indent=1)
    write_csv(os.path.join(args.out_dir, "rows.csv"), [row_out(r, m) for r, m in scored])
    by_abs = sorted(scored, key=lambda rm: (-abs(rm[1]["dh_e4"]), int(rm[0]["spkid"])))
    write_csv(os.path.join(args.out_dir, "outliers.csv"), [row_out(r, m) for r, m in by_abs[:300]])
    rng = random.Random(SAMPLE_SEED)
    pick = sorted(rng.sample(range(len(scored)), min(SAMPLE_SIZE, len(scored))))
    write_csv(os.path.join(args.out_dir, "sample.csv"), [row_out(*scored[i]) for i in pick])
    hist = {}
    for _, m in scored:
        b = max(-41, min(40, math.floor(m["dh_e4"] / 500.0)))  # 0.05 mag bins, clipped at +-2 mag
        hist[b] = hist.get(b, 0) + 1
    with open(os.path.join(args.out_dir, "histogram.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dh_lo_mag", "dh_hi_mag", "n"])
        for b in range(-41, 41):  # first and last rows are the overflow bins
            lo = "-inf" if b == -41 else "%.2f" % (b * 0.05)
            hi = "inf" if b == 40 else "%.2f" % ((b + 1) * 0.05)
            w.writerow([lo, hi, hist.get(b, 0)])
    print(json.dumps({"rows": len(rows), "status": status, "decisions": decisions, "checks": summary["checks"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
