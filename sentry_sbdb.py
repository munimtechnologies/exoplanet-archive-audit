#!/usr/bin/env python3
# Apache-2.0. sentry_sbdb 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
"""Check what JPL's CNEOS Sentry impact-risk list serves for each object against itself and against JPL's
Small-Body Database (SBDB), from one snapshot of each.

D1: Sentry's diameter is documented as computed from H with an assumed albedo of 0.154 ("usually"; measured
    values are "sometimes" used). How many served diameters do not follow that rule beyond rounding?
D2: Does SBDB's current orbit use observations later than the last observation Sentry's analysis used?
D3: Does Sentry's H differ from SBDB's current H beyond rounding?

Pre-registered in findings/2026-10-20-sentry-sbdb-prereg.md; decisions D1-D3 are integer rules (decide_*).
Pure stdlib; the job downloads the Sentry list (one request) and the SBDB NEO table itself."""
import argparse
import csv
import datetime
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

VERSION = "0.1.0"
GATE_TEXT = "CNEOS Sentry vs SBDB pre-registration"
SENTRY_API = "https://ssd-api.jpl.nasa.gov/sentry.api"
SENTRY_VERSION = "2.0"
SBDB_API = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
SBDB_FIELDS = ["spkid", "pdes", "full_name", "kind", "H", "last_obs", "orbit_id", "soln_date", "producer"]
PAGE = 20000
ALBEDO = 0.154
D_CONST_KM = 1329.0 / math.sqrt(ALBEDO)
D_SLACK = 0.01           # 1 % relative, on top of the rounding of both served strings
H_SLACK = Decimal("0.01")  # mag, on top of the rounding of both served strings
N_MIN = 1000
# Seen before pre-registration: 1979 XB (example record of the Sentry API documentation), 2010 RF12 (its impact
# probability was read in a dataset card), 99942 Apophis (a close-approach probe row). Never scored.
EXCLUDED_DES = {"1979 XB", "2010 RF12", "99942"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
OUT_HEADER = ["des", "fullname", "s_h", "s_diameter", "s_last_obs", "s_ip", "s_ps_cum", "matched", "spkid",
              "kind", "b_H", "b_last_obs", "orbit_id", "soln_date", "producer", "d_status", "d_ratio",
              "obs_order", "obs_gap_days", "h_differs", "h_diff"]


def parse_dec(s):
    """(Decimal value, Decimal half of the last-digit unit) of a plain decimal string ('18.56' -> 0.005); else None."""
    if s is None:
        return None
    s = str(s).strip()
    body = s.lstrip("+-")
    if not body or body.count(".") > 1 or not body.replace(".", "").isdigit():
        return None
    try:
        v = Decimal(s)
    except InvalidOperation:
        return None
    return v, Decimal(5).scaleb(v.as_tuple().exponent - 1)


def d_rule(h):
    """Diameter in km for absolute magnitude h at albedo 0.154."""
    return D_CONST_KM * 10.0 ** (-h / 5.0)


def diameter_status(h_s, d_s):
    """'consistent' if the served diameter's interval meets the 0.154-albedo diameter of the served H's interval
    (widened by 1 % each way), 'inconsistent' if not, 'unparsed' if either string is not a plain decimal."""
    a, b = parse_dec(h_s), parse_dec(d_s)
    if a is None or b is None:
        return "unparsed"
    h, uh = float(a[0]), float(a[1])
    d, ud = float(b[0]), float(b[1])
    lo = d_rule(h + uh) * (1.0 - D_SLACK)
    hi = d_rule(h - uh) * (1.0 + D_SLACK)
    return "consistent" if d + ud >= lo and d - ud <= hi else "inconsistent"


def h_differs(h_sentry, h_sbdb):
    """True if the two served H differ by more than both roundings plus 0.01 mag, False if not, None if unparsed."""
    a, b = parse_dec(h_sentry), parse_dec(h_sbdb)
    if a is None or b is None:
        return None
    return abs(a[0] - b[0]) > a[1] + b[1] + H_SLACK


def obs_order(sentry_last, sbdb_last):
    """'later' if SBDB's last observation date is after Sentry's, 'same', 'earlier'; None unless both are
    full YYYY-MM-DD dates."""
    if not sentry_last or not sbdb_last:
        return None
    a, b = str(sentry_last).strip(), str(sbdb_last).strip()
    if not DATE_RE.match(a) or not DATE_RE.match(b):
        return None
    return "same" if a == b else ("later" if b > a else "earlier")


def gap_days(sentry_last, sbdb_last):
    """Days from Sentry's last observation to SBDB's (negative if earlier); None unless both parse as dates."""
    try:
        return (datetime.date.fromisoformat(str(sbdb_last).strip()) -
                datetime.date.fromisoformat(str(sentry_last).strip())).days
    except (TypeError, ValueError):
        return None


def decide_d1(n, k):
    """D1: at most 3 % of Sentry rows break the 0.154-albedo diameter rule. n parsed rows, k inconsistent."""
    if n < N_MIN:
        return "underpowered"
    return "holds" if 100 * k <= 3 * n else "fails"


def decide_d2(n, k, match_ok):
    """D2: at most 2 % of matched rows have an SBDB last observation after Sentry's. n comparable rows, k later."""
    if not match_ok:
        return "not_scored_low_match"
    if n < N_MIN:
        return "underpowered"
    return "holds" if 50 * k <= n else "fails"


def decide_d3(n, k, match_ok):
    """D3: at most 10 % of matched rows have an H that differs from SBDB's beyond rounding. n comparable, k differ."""
    if not match_ok:
        return "not_scored_low_match"
    if n < N_MIN:
        return "underpowered"
    return "holds" if 10 * k <= n else "fails"


def classify(sentry_rows, sbdb_rows):
    """One output record per Sentry row not in EXCLUDED_DES, joined to SBDB on des == pdes."""
    by_pdes = {}
    for r in sbdb_rows:
        if r.get("pdes"):
            by_pdes.setdefault(r["pdes"].strip(), r)
    records = []
    for s in sentry_rows:
        des = (s.get("des") or "").strip()
        if des in EXCLUDED_DES:
            continue
        b = by_pdes.get(des)
        rec = {"des": des, "fullname": (s.get("fullname") or "").strip(), "s_h": s.get("h"),
               "s_diameter": s.get("diameter"), "s_last_obs": s.get("last_obs"), "s_ip": s.get("ip"),
               "s_ps_cum": s.get("ps_cum"), "matched": int(b is not None)}
        for k in ("spkid", "kind", "orbit_id", "soln_date", "producer"):
            rec[k] = b.get(k) if b else None
        rec["b_H"] = b.get("H") if b else None
        rec["b_last_obs"] = b.get("last_obs") if b else None
        rec["d_status"] = diameter_status(rec["s_h"], rec["s_diameter"])
        rec["d_ratio"] = None
        if rec["d_status"] != "unparsed" and float(rec["s_diameter"]) > 0:
            rec["d_ratio"] = "%.4f" % (float(rec["s_diameter"]) / d_rule(float(rec["s_h"])))
        rec["obs_order"] = obs_order(rec["s_last_obs"], rec["b_last_obs"]) if b else None
        rec["obs_gap_days"] = gap_days(rec["s_last_obs"], rec["b_last_obs"]) if rec["obs_order"] else None
        rec["h_differs"] = h_differs(rec["s_h"], rec["b_H"]) if b else None
        rec["h_diff"] = None
        if rec["h_differs"] is not None:
            rec["h_diff"] = str(parse_dec(rec["b_H"])[0] - parse_dec(rec["s_h"])[0])
        records.append(rec)
    return records


def quantiles(values, qs=(5, 25, 50, 75, 95)):
    """Nearest-rank quantiles (None when empty)."""
    v = sorted(values)
    if not v:
        return {str(q): None for q in qs}
    return {str(q): v[max(0, (q * len(v) + 99) // 100 - 1)] for q in qs}


def score(records):
    """Decisions and descriptive tallies from classify() records."""
    n_all = len(records)
    matched = [r for r in records if r["matched"]]
    match_ok = 100 * len(matched) >= 95 * n_all
    d_rows = [r for r in records if r["d_status"] != "unparsed"]
    d_bad = [r for r in d_rows if r["d_status"] == "inconsistent"]
    o_rows = [r for r in matched if r["obs_order"] is not None]
    o_later = [r for r in o_rows if r["obs_order"] == "later"]
    h_rows = [r for r in matched if r["h_differs"] is not None]
    h_bad = [r for r in h_rows if r["h_differs"]]
    decisions = {
        "D1": {"n": len(d_rows), "inconsistent": len(d_bad), "decision": decide_d1(len(d_rows), len(d_bad))},
        "D2": {"n": len(o_rows), "sbdb_later": len(o_later), "match_ok": match_ok,
               "decision": decide_d2(len(o_rows), len(o_later), match_ok)},
        "D3": {"n": len(h_rows), "h_differs": len(h_bad), "match_ok": match_ok,
               "decision": decide_d3(len(h_rows), len(h_bad), match_ok)},
    }
    desc = {"n_sentry_scored": n_all, "n_matched": len(matched), "obs_order": {}, "h_vs_obs": {},
            "producer_of_later": {}, "kind": {}}
    for r in matched:
        o = str(r["obs_order"])
        desc["obs_order"][o] = desc["obs_order"].get(o, 0) + 1
        key = "h_differs=%s obs=%s" % (r["h_differs"], r["obs_order"])
        desc["h_vs_obs"][key] = desc["h_vs_obs"].get(key, 0) + 1
        kd = str(r["kind"])
        desc["kind"][kd] = desc["kind"].get(kd, 0) + 1
    for r in o_later:
        p = str(r["producer"])
        desc["producer_of_later"][p] = desc["producer_of_later"].get(p, 0) + 1
    desc["later_gap_days_quantiles"] = quantiles([r["obs_gap_days"] for r in o_later])
    desc["h_diff_quantiles"] = {k: (None if v is None else str(v)) for k, v in
                                quantiles([Decimal(r["h_diff"]) for r in h_bad]).items()}
    desc["d_ratio_of_inconsistent"] = sorted((r["des"], r["d_ratio"]) for r in d_bad)
    desc["unmatched_des"] = sorted(r["des"] for r in records if not r["matched"])[:200]
    return decisions, desc


def check_gate(note_path):
    """True if the fetched pre-registration note exists and carries GATE_TEXT."""
    try:
        with open(note_path, "rb") as f:
            return GATE_TEXT.encode("utf-8") in f.read()
    except OSError:
        return False


def fetch_bytes(url, tries=4, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": "sentry_sbdb/" + VERSION + " (mv2@munimtech.com)"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(30 * (i + 1))


def sbdb_page_url(offset, limit=PAGE):
    q = {"fields": ",".join(SBDB_FIELDS), "sb-group": "neo", "sort": "spkid", "limit": str(limit),
         "limit-from": str(offset)}
    return SBDB_API + "?" + urllib.parse.urlencode(q)


def parse_sbdb_page(body):
    """(count, fields, rows as dicts of strings) from one SBDB Query API JSON page."""
    j = json.loads(body.decode("utf-8"))
    fields = j.get("fields", [])
    rows = [{f: (None if v is None else str(v)) for f, v in zip(fields, rec)} for rec in j.get("data", [])]
    return int(j.get("count", 0)), fields, rows


def parse_sentry(body):
    """(signature version, count, rows) from the Sentry API's default summary (mode S) response."""
    j = json.loads(body.decode("utf-8"))
    return str(j.get("signature", {}).get("version")), int(j.get("count", -1)), j.get("data", [])


def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-note", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    summary = {"version": VERSION, "sentry_api": SENTRY_API, "sbdb_api": SBDB_API, "sbdb_fields": SBDB_FIELDS,
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    summary["gate"] = check_gate(args.gate_note)
    if not summary["gate"]:
        summary["error"] = "gate note missing or lacks '%s'; nothing downloaded" % GATE_TEXT
        write_json(os.path.join(args.out_dir, "summary.json"), summary)
        print(json.dumps(summary))
        return 2
    s_body = fetch_bytes(SENTRY_API)
    with open(os.path.join(args.out_dir, "sentry.json"), "wb") as f:
        f.write(s_body)
    s_version, s_count, s_rows = parse_sentry(s_body)
    summary["sentry"] = {"bytes": len(s_body), "sha256": hashlib.sha256(s_body).hexdigest(),
                         "version": s_version, "count": s_count, "rows": len(s_rows),
                         "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    rows, pages, counts = [], [], []
    offset = 0
    while True:
        time.sleep(1.0)
        body = fetch_bytes(sbdb_page_url(offset))
        count, fields, page_rows = parse_sbdb_page(body)
        pages.append({"offset": offset, "rows": len(page_rows), "bytes": len(body),
                      "sha256": hashlib.sha256(body).hexdigest()})
        counts.append(count)
        if fields != SBDB_FIELDS:
            summary["error"] = "unexpected SBDB fields %r" % fields
            break
        rows.extend(page_rows)
        offset += len(page_rows)
        if not page_rows or offset >= count:
            break
    summary["sbdb_pages"] = pages
    spkids = [r.get("spkid") for r in rows]
    pdes = [r.get("pdes") for r in rows]
    s_des = [(s.get("des") or "").strip() for s in s_rows]
    summary["checks"] = {
        "sentry_version_2_0": s_version == SENTRY_VERSION,
        "sentry_rows_equal_count": len(s_rows) == s_count,
        "sentry_no_duplicate_des": len(set(s_des)) == len(s_des),
        "sbdb_fields_as_requested": "error" not in summary,
        "sbdb_count_stable": len(set(counts)) == 1,
        "sbdb_rows_equal_count": bool(counts) and len(rows) == counts[0],
        "sbdb_no_duplicate_spkid": len(set(spkids)) == len(spkids),
        "sbdb_no_duplicate_pdes": len(set(pdes)) == len(pdes),
        "excluded_found": sorted(d for d in s_des if d in EXCLUDED_DES),
    }
    summary["sbdb_count"] = counts[0] if counts else None
    records = classify(s_rows, rows)
    decisions, desc = score(records)
    summary["decisions"] = decisions
    summary["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_json(os.path.join(args.out_dir, "summary.json"), summary)
    write_json(os.path.join(args.out_dir, "decisions.json"), decisions)
    write_json(os.path.join(args.out_dir, "descriptive.json"), desc)
    with open(os.path.join(args.out_dir, "rows.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_HEADER)
        w.writeheader()
        w.writerows(records)
    print(json.dumps({"sentry_rows": len(s_rows), "decisions": decisions, "checks": summary["checks"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
