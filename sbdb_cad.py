#!/usr/bin/env python3
# Apache-2.0. sbdb_cad 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
"""Are JPL's served Earth close-approach table (CAD API) and its served orbit table (SBDB Query API) consistent
with each other for near-Earth asteroids?

G1: the orbit-solution ID behind each listed close approach is the one the orbit table serves for that object.
G2: for an object's first listed Earth approach after its orbit epoch (within a year), the two-body impact
    parameter b = dist * v_rel / v_inf (the unperturbed miss distance, from angular momentum about Earth) is not
    below the served Earth MOID by more than TOL au. The nominal distance itself may be below the MOID, because
    Earth's gravity bends the path inward, so dist < moid is NOT a contradiction; b < moid - TOL is.
G3: the served 3-sigma range contains the nominal distance (dist_min <= dist <= dist_max).

Served numbers are read as decimal strings and compared with decimal.Decimal, never floats; dist and moid are read
as the interval of their last digit, so G2 flags a row only when the whole intervals disagree.
Pre-registered in findings/2026-10-19-sbdb-cad-prereg.md; decisions G1-G3 are integer rules (decide_*).
Pure stdlib; the job downloads both tables itself and keeps tallies, the G2 rows and capped flagged lists."""
import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

VERSION = "0.1.0"
SBDB_API = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
CAD_API = "https://ssd-api.jpl.nasa.gov/cad.api"
SBDB_FIELDS = ["spkid", "pdes", "orbit_id", "epoch", "moid", "condition_code", "data_arc", "n_obs_used",
               "last_obs", "soln_date"]
CAD_FIELDS = ["des", "orbit_id", "jd", "cd", "dist", "dist_min", "dist_max", "v_rel", "v_inf", "t_sigma_f", "h"]
CAD_DATE_MIN, CAD_DATE_MAX = "2024-01-01", "2028-01-01"
CAD_DIST_MAX = "0.2"
JD_MIN = Decimal("2460310.5")  # 2024-01-01.0 TDB
JD_MAX = Decimal("2461771.5")  # 2028-01-01.0 TDB
YEAR = Decimal("365.25")
TOL = Decimal("0.001")  # au, G2 allowance for MOID drift and approximation
PAGE = 20000
PAUSE_S = 1.0
GATE_TEXT = "SBDB close-approach pre-registration"
# Rows looked at before pre-registering: Ceres, Pallas, Juno (sbdb_triplet format probe); 433 Eros, 719 Albert,
# 887 Alinda (3-row Query API probe for this lane); 99942 Apophis (CAD format probe for this lane).
PROBE_SPKIDS = {20000001, 20000002, 20000003, 20000433, 20000719, 20000887, 20099942}
NEO_PROBES_EXPECTED = 4  # of the probe spkids, these four are NEO asteroids and must be found in the table
SEEN_ROWS_EXPECTED = 340  # 40 in sbdb_triplet's sample.csv + 300 in its outliers.csv
MAX_LIST = 5000
FLAGGED_HEADER = ["check", "des", "cad_orbit_id", "sbdb_orbit_id", "jd", "cd", "dist", "dist_min", "dist_max",
                  "v_rel", "v_inf", "epoch", "moid", "detail"]
G2_HEADER = ["des", "orbit_id", "jd", "epoch", "dt_days", "dist", "v_rel", "v_inf", "b", "moid", "b_minus_moid",
             "dist_minus_moid", "status", "condition_code", "data_arc"]
BINS = [(Decimal("-0.01"), "<-0.01"), (Decimal("-0.001"), "[-0.01,-0.001)"), (Decimal("0"), "[-0.001,0)"),
        (Decimal("0.001"), "[0,0.001)"), (Decimal("0.01"), "[0.001,0.01)"), (Decimal("0.1"), "[0.01,0.1)")]
DT_BINS = [(Decimal(30), "[0,30]"), (Decimal(90), "(30,90]"), (Decimal(180), "(90,180]"), (YEAR, "(180,365.25]")]


def parse_value(s, exact=False):
    """(value, half_unit) as Decimals from a served number string ('0.090' -> half 0.0005); half_unit is 0 when
    exact. None if missing or not a finite number."""
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    try:
        v = Decimal(s)
    except InvalidOperation:
        return None
    if not v.is_finite():
        return None
    if exact:
        return v, Decimal(0)
    return v, Decimal(5).scaleb(v.as_tuple().exponent - 1)


def bounds(x):
    """(lo, hi) of an interval (value, half)."""
    return x[0] - x[1], x[0] + x[1]


def fmt(d):
    return format(d, "f")


def norm_orbit_id(s):
    """Orbit-solution ID without a leading 'JPL' ('JPL 732' -> '732', '659' -> '659'); None if empty."""
    if s is None:
        return None
    s = str(s).strip()
    if s.upper().startswith("JPL"):
        s = s[3:].strip()
    return s or None


def orbit_id_order(cad_id, sbdb_id):
    """'same', or for two integer IDs 'cad_older' / 'cad_newer', else 'differ'."""
    if cad_id == sbdb_id:
        return "same"
    if cad_id.isdigit() and sbdb_id.isdigit():
        return "cad_older" if int(cad_id) < int(sbdb_id) else "cad_newer"
    return "differ"


def impact_parameter(dist, v_rel, v_inf):
    """b = dist * v_rel / v_inf as (lo, hi) from dist's interval (speeds exact); None if missing or non-positive."""
    if dist is None or v_rel is None or v_inf is None:
        return None
    if v_inf[0] <= 0 or v_rel[0] <= 0:
        return None
    lo, hi = bounds(dist)
    f = v_rel[0] / v_inf[0]
    return lo * f, hi * f


def g2_status(b, moid):
    """'flagged' if b's upper bound is below moid's lower bound minus TOL, else 'ok'; None if missing."""
    if b is None or moid is None:
        return None
    return "flagged" if b[1] < bounds(moid)[0] - TOL else "ok"


def g3_status(dist_s, min_s, max_s):
    """'ok' if dist_min <= dist <= dist_max (all read exactly), 'violation' otherwise; None if any is missing."""
    d, lo, hi = (parse_value(s, exact=True) for s in (dist_s, min_s, max_s))
    if d is None or lo is None or hi is None:
        return None
    return "ok" if lo[0] <= d[0] <= hi[0] else "violation"


def first_after_epoch(rows, epoch):
    """The row with the smallest jd_dec >= epoch, or None."""
    best = None
    for r in rows:
        if r["jd_dec"] >= epoch and (best is None or r["jd_dec"] < best["jd_dec"]):
            best = r
    return best


def last_before_epoch(rows, epoch):
    """The row with the largest jd_dec < epoch, or None."""
    best = None
    for r in rows:
        if r["jd_dec"] < epoch and (best is None or r["jd_dec"] > best["jd_dec"]):
            best = r
    return best


def epoch_window_ok(epoch):
    """True if the whole year after the epoch lies inside the downloaded close-approach window."""
    return JD_MIN <= epoch and epoch + YEAR <= JD_MAX


def bin_label(x):
    for edge, label in BINS:
        if x < edge:
            return label
    return ">=0.1"


def dt_label(dt):
    for edge, label in DT_BINS:
        if dt <= edge:
            return label
    return ">365.25"


def decide_g1(n, k):
    """G1: the close-approach orbit ID differs from the served one for at most 1 in 100 matched rows."""
    if n < 5000:
        return "underpowered"
    return "holds" if 100 * k <= n else "fails"


def decide_g2(n, k):
    """G2: b is below moid - TOL for at most 1 in 1,000 eligible first-after-epoch approaches."""
    if n < 1000:
        return "underpowered"
    return "holds" if 1000 * k <= n else "fails"


def decide_g3(n, k):
    """G3: no listed approach has its nominal distance outside its own 3-sigma range."""
    if n < 5000:
        return "underpowered"
    return "holds" if k == 0 else "fails"


class Tally:
    """Counts, the G2 rows and capped flagged lists; feed every CAD row with add_cad, then call finish."""

    def __init__(self, sbdb_by_pdes, excluded_spkids=()):
        self.sbdb = sbdb_by_pdes
        self.excluded = set(excluded_spkids)
        self.counts = {}
        self.epochs = {}
        self.lists = {"g1": [], "g2": [], "g3": []}
        self.g2_rows = []
        self.groups = {}

    def bump(self, key, n=1):
        self.counts[key] = self.counts.get(key, 0) + n

    def keep(self, check, r, s, detail):
        if len(self.lists[check]) < MAX_LIST:
            self.lists[check].append([check, r.get("des"), r.get("orbit_id"), None if s is None else s.get("orbit_id"),
                                      r.get("jd"), r.get("cd"), r.get("dist"), r.get("dist_min"), r.get("dist_max"),
                                      r.get("v_rel"), r.get("v_inf"), None if s is None else s.get("epoch"),
                                      None if s is None else s.get("moid"), detail])

    def add_cad(self, r):
        self.bump("cad_rows")
        st = g3_status(r.get("dist"), r.get("dist_min"), r.get("dist_max"))
        self.bump("g3 " + (st or "missing"))
        if st == "violation":
            self.keep("g3", r, None, "dist outside [dist_min, dist_max]")
        jd = parse_value(r.get("jd"), exact=True)
        if jd is None:
            self.bump("cad jd_missing")
            return
        if not (JD_MIN <= jd[0] < JD_MAX):
            self.bump("cad outside_window")
            return
        s = self.sbdb.get(r.get("des"))
        if s is None:
            self.bump("join unmatched")
            return
        if int(s["spkid"]) in self.excluded:
            self.bump("join excluded_seen")
            return
        self.bump("join matched")
        cid, sid = norm_orbit_id(r.get("orbit_id")), norm_orbit_id(s.get("orbit_id"))
        if cid is None or sid is None:
            self.bump("g1 missing")
            return
        order = orbit_id_order(cid, sid)
        self.bump("g1 " + ("same" if order == "same" else "differ"))
        self.bump("g1_order " + order)
        if order != "same":
            self.keep("g1", r, s, order)
            return
        row = dict(r)
        row["jd_dec"] = jd[0]
        self.groups.setdefault(r["des"], []).append(row)

    def _status(self, r, s, label):
        """G2 arithmetic for one approach row r of SBDB object s; tallies under label; returns (status, parts)."""
        dist = parse_value(r.get("dist"))
        v_rel = parse_value(r.get("v_rel"), exact=True)
        v_inf = parse_value(r.get("v_inf"), exact=True)
        moid = parse_value(s.get("moid"))
        b = impact_parameter(dist, v_rel, v_inf)
        st = g2_status(b, moid)
        self.bump(label + " " + (st or "missing"))
        if st is None:
            return None, None
        b_nom = dist[0] * v_rel[0] / v_inf[0]
        self.bump(label + "_naive " + ("dist<moid" if dist[0] < moid[0] else "dist>=moid"))
        self.bump(label + "_b " + ("b<moid" if b_nom < moid[0] else "b>=moid"))
        self.bump(label + "_bin b-moid " + bin_label(b_nom - moid[0]))
        self.bump(label + "_bin dist-moid " + bin_label(dist[0] - moid[0]))
        return st, (dist, v_rel, v_inf, moid, b_nom)

    def finish(self):
        for des, rows in self.groups.items():
            s = self.sbdb[des]
            epoch = parse_value(s.get("epoch"), exact=True)
            if epoch is None:
                self.bump("g2 epoch_missing")
                continue
            e = epoch[0]
            key = fmt(e) if len(self.epochs) < 1000 or fmt(e) in self.epochs else "other"
            self.epochs[key] = self.epochs.get(key, 0) + 1
            if not epoch_window_ok(e):
                self.bump("g2 epoch_outside_window")
                continue
            first = first_after_epoch(rows, e)
            if first is None:
                self.bump("g2 no_approach_after_epoch")
                continue
            dt = first["jd_dec"] - e
            if dt > YEAR:
                self.bump("g2 first_approach_later_than_year")
                continue
            for f in ("dist", "v_rel", "v_inf"):
                x = parse_value(first.get(f))
                self.bump("precision %s %s" % (f, "none" if x is None else x[0].as_tuple().exponent))
            x = parse_value(s.get("moid"))
            self.bump("precision moid %s" % ("none" if x is None else x[0].as_tuple().exponent))
            st, parts = self._status(first, s, "g2")
            if st is None:
                continue
            dist, v_rel, v_inf, moid, b_nom = parts
            self.bump("g2_dt_bin " + dt_label(dt))
            self.g2_rows.append([des, first.get("orbit_id"), first.get("jd"), s.get("epoch"), fmt(dt), first.get("dist"),
                                 first.get("v_rel"), first.get("v_inf"), fmt(b_nom), s.get("moid"),
                                 fmt(b_nom - moid[0]), fmt(dist[0] - moid[0]), st, s.get("condition_code"),
                                 s.get("data_arc")])
            if st == "flagged":
                self.keep("g2", first, s, "b=%s < moid-%s" % (fmt(b_nom), fmt(TOL)))
            last = last_before_epoch(rows, e)
            if last is not None and e - last["jd_dec"] <= YEAR:
                self._status(last, s, "g2_before")


def decisions(t):
    c = lambda key: t.counts.get(key, 0)
    n1, k1 = c("g1 same") + c("g1 differ"), c("g1 differ")
    n2, k2 = c("g2 ok") + c("g2 flagged"), c("g2 flagged")
    n3, k3 = c("g3 ok") + c("g3 violation"), c("g3 violation")
    return {
        "G1": {"n_matched": n1, "n_differ": k1, "decision": decide_g1(n1, k1)},
        "G2": {"n_eligible": n2, "n_flagged": k2, "decision": decide_g2(n2, k2)},
        "G3": {"n_rows": n3, "n_violation": k3, "decision": decide_g3(n3, k3)},
    }


def check_gate(note_path):
    try:
        with open(note_path, "rb") as f:
            return GATE_TEXT.encode("utf-8") in f.read()
    except OSError:
        return False


def load_seen(paths):
    seen = set()
    for path in paths:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                seen.add(int(row["spkid"]))
    return seen


def sbdb_url(offset, limit=PAGE):
    q = {"fields": ",".join(SBDB_FIELDS), "sb-group": "neo", "sb-kind": "a", "sort": "spkid", "limit": str(limit),
         "limit-from": str(offset), "full-prec": "true"}
    return SBDB_API + "?" + urllib.parse.urlencode(q)


def cad_url():
    q = {"date-min": CAD_DATE_MIN, "date-max": CAD_DATE_MAX, "dist-max": CAD_DIST_MAX, "nea": "true", "sort": "date"}
    return CAD_API + "?" + urllib.parse.urlencode(q)


def fetch_bytes(url, tries=4, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": "sbdb_cad/" + VERSION + " (mv2@munimtech.com)"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(30 * (i + 1))


def parse_page(body):
    """(count, fields, rows as dicts of strings) from one JSON page of either API."""
    j = json.loads(body.decode("utf-8"))
    fields = j.get("fields", [])
    rows = []
    for rec in j.get("data", []):
        rows.append({f: (None if v is None else str(v)) for f, v in zip(fields, rec)})
    return int(j.get("count", 0)), fields, rows


def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-note", required=True)
    ap.add_argument("--seen", nargs="+", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--pause", type=float, default=PAUSE_S)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    summary = {"version": VERSION, "sbdb_api": SBDB_API, "cad_api": CAD_API, "sbdb_fields": SBDB_FIELDS,
               "cad_fields": CAD_FIELDS, "cad_query": cad_url(), "tol_au": fmt(TOL),
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    summary["gate"] = check_gate(args.gate_note)
    try:
        seen = load_seen(args.seen)
    except (OSError, KeyError, ValueError):
        seen = None
    summary["seen_rows"] = None if seen is None else len(seen)
    if not summary["gate"] or seen is None or len(seen) != SEEN_ROWS_EXPECTED:
        summary["error"] = "gate note or seen-row files missing or wrong; nothing downloaded"
        write_json(os.path.join(args.out_dir, "summary.json"), summary)
        print(json.dumps(summary))
        return 2
    excluded = seen | PROBE_SPKIDS
    # 1. The orbit table: every NEO asteroid.
    by_pdes, pages, counts = {}, [], []
    offset, last, sorted_ok, dup_pdes, probes_found = 0, None, True, 0, 0
    while True:
        body = fetch_bytes(sbdb_url(offset))
        count, fields, rows = parse_page(body)
        pages.append({"offset": offset, "rows": len(rows), "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
        counts.append(count)
        if fields != SBDB_FIELDS:
            summary["error"] = "unexpected SBDB fields %r" % fields
            break
        for r in rows:
            k = int(r["spkid"])
            if last is not None and k <= last:
                sorted_ok = False
            last = k
            if k in PROBE_SPKIDS:
                probes_found += 1
            if r["pdes"] in by_pdes:
                dup_pdes += 1
            by_pdes[r["pdes"]] = r
        offset += len(rows)
        if not rows or offset >= count:
            break
        time.sleep(args.pause)
    summary["sbdb"] = {"pages": pages, "api_count": counts[0] if counts else None, "rows_read": offset,
                       "count_stable": len(set(counts)) == 1, "rows_equal_count": bool(counts) and offset == counts[0],
                       "sorted_by_spkid_no_duplicates": sorted_ok, "duplicate_pdes": dup_pdes,
                       "probe_rows_found": probes_found}
    if "error" in summary:
        write_json(os.path.join(args.out_dir, "summary.json"), summary)
        print(json.dumps(summary))
        return 3
    time.sleep(args.pause)
    # 2. The close-approach table for the window, one request.
    body = fetch_bytes(cad_url())
    cad_count, cad_fields, cad_rows = parse_page(body)
    summary["cad"] = {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "api_count": cad_count,
                      "rows_read": len(cad_rows), "fields_as_requested": cad_fields == CAD_FIELDS,
                      "rows_equal_count": cad_count == len(cad_rows)}
    if cad_fields != CAD_FIELDS:
        summary["error"] = "unexpected CAD fields %r" % cad_fields
        write_json(os.path.join(args.out_dir, "summary.json"), summary)
        print(json.dumps(summary))
        return 4
    # 3. Tally.
    t = Tally(by_pdes, excluded)
    for r in cad_rows:
        t.add_cad(r)
    t.finish()
    dec = decisions(t)
    summary["checks"] = {
        "sbdb_fields_as_requested": True,
        "sbdb_count_stable": summary["sbdb"]["count_stable"],
        "sbdb_rows_equal_count": summary["sbdb"]["rows_equal_count"],
        "sbdb_sorted_no_duplicates": sorted_ok,
        "sbdb_no_duplicate_pdes": dup_pdes == 0,
        "neo_probe_rows_found": probes_found == NEO_PROBES_EXPECTED,
        "cad_fields_as_requested": True,
        "cad_rows_equal_count": summary["cad"]["rows_equal_count"],
        "cad_all_in_window": t.counts.get("cad outside_window", 0) == 0,
        "join_matched_at_least_99pct": 100 * t.counts.get("join matched", 0) >= 99 * (
            t.counts.get("join matched", 0) + t.counts.get("join unmatched", 0)),
    }
    summary["decisions"] = dec
    summary["flagged_rows_listed"] = {k: len(v) for k, v in t.lists.items()}
    summary["g2_rows"] = len(t.g2_rows)
    summary["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_json(os.path.join(args.out_dir, "summary.json"), summary)
    write_json(os.path.join(args.out_dir, "decisions.json"), dec)
    write_json(os.path.join(args.out_dir, "counts.json"), t.counts)
    write_json(os.path.join(args.out_dir, "epochs.json"), t.epochs)
    write_csv(os.path.join(args.out_dir, "flagged.csv"), FLAGGED_HEADER,
              t.lists["g1"] + t.lists["g2"] + t.lists["g3"])
    write_csv(os.path.join(args.out_dir, "g2_rows.csv"), G2_HEADER, t.g2_rows)
    print(json.dumps({"decisions": dec, "checks": summary["checks"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
