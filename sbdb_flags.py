#!/usr/bin/env python3
# Apache-2.0. sbdb_flags 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
"""Are the NEO flag, PHA flag and orbit-class code that JPL's Small-Body Database (SBDB) serves for each asteroid
the functions of its own served elements that their published definitions say they are?

NEO: q < 1.3 au (CNEOS). PHA: Earth MOID <= 0.05 au and H <= 22.0 (CNEOS). Orbit classes: the boundaries in the
SBDB filter documentation (ssd-api.jpl.nasa.gov/doc/sbdb_filter.html). Served q, moid, a, e and ad are rounded
strings, so each is read as the interval of its last digit, and a rule is decided only when the whole interval
falls on one side of a boundary ("boundary" otherwise). H is read as exact, since the PHA definition is stated on
the catalogued H. All comparisons use decimal.Decimal, never floats.

Pre-registered in findings/2026-10-20-sbdb-flags-prereg.md; decisions F1-F3 are integer rules (decide_*).
Pure stdlib; the job downloads the SBDB Query API pages itself and keeps only tallies and mismatch rows."""
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
API = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
FIELDS = ["spkid", "pdes", "class", "neo", "pha", "H", "moid", "q", "a", "e", "ad"]
PAGE = 20000
PAUSE_S = 1.0
GATE_TEXT = "SBDB flag-consistency pre-registration"
# Seen in the 3-row format probe of sbdb_triplet 0.1.0 (Ceres, Pallas, Juno).
PROBE_SPKIDS = {20000001, 20000002, 20000003}
SEEN_ROWS_EXPECTED = 340  # 40 in sbdb_triplet's sample.csv + 300 in its outliers.csv
MAX_LIST = 5000  # mismatch rows kept per check; the counts are always complete
NEO_Q = Decimal("1.3")
PHA_MOID = Decimal("0.05")
PHA_H = Decimal("22.0")
MISMATCH_HEADER = ["check"] + FIELDS + ["expected", "detail"]


def parse_value(s, exact=False):
    """(value, half_unit) as Decimals from a served number string ('0.090' -> half 0.0005, '1.2e-05' -> 5e-7);
    half_unit is 0 when exact. None if missing or not a finite number."""
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


def lt(x, t):
    """x < t for an interval x = (value, half): True, False, or None when the interval straddles t."""
    v, h = x
    if v + h < t:
        return True
    if v - h >= t:
        return False
    return None


def gt(x, t):
    v, h = x
    if v - h > t:
        return True
    if v + h <= t:
        return False
    return None


def le(x, t):
    v, h = x
    if v + h <= t:
        return True
    if v - h > t:
        return False
    return None


def all3(*conds):
    """Three-valued AND: False if any is False, True if all are True, else None."""
    if any(c is False for c in conds):
        return False
    if all(c is True for c in conds):
        return True
    return None


def neo_rule(q):
    return lt(q, NEO_Q)


def pha_rule(moid, h):
    return all3(le(moid, PHA_MOID), le(h, PHA_H))


def pha_reason(moid, h):
    """Which PHA conditions fail ('H>22', 'moid>0.05', both joined by '+'), or 'both_met'."""
    parts = []
    if le(h, PHA_H) is False:
        parts.append("H>22")
    if le(moid, PHA_MOID) is False:
        parts.append("moid>0.05")
    return "+".join(parts) or "both_met"


def class_conditions(a, e, q, ad):
    """{code: True/False/None} for the bound-orbit asteroid classes of the SBDB filter documentation."""
    d = Decimal
    return {
        "IEO": lt(ad, d("0.983")),
        "ATE": all3(lt(a, d("1.0")), gt(ad, d("0.983"))),
        "APO": all3(gt(a, d("1.0")), lt(q, d("1.017"))),
        "AMO": all3(gt(q, d("1.017")), lt(q, d("1.3"))),
        "MCA": all3(gt(q, d("1.3")), lt(q, d("1.666")), lt(a, d("3.2"))),
        "IMB": all3(lt(a, d("2.0")), gt(q, d("1.666"))),
        "MBA": all3(gt(a, d("2.0")), lt(a, d("3.2")), gt(q, d("1.666"))),
        "OMB": all3(gt(a, d("3.2")), lt(a, d("4.6"))),
        "TJN": all3(gt(a, d("4.6")), lt(a, d("5.5")), lt(e, d("0.3"))),
        "CEN": all3(gt(a, d("5.5")), lt(a, d("30.1"))),
        "TNO": gt(a, d("30.1")),
    }


def class_check(served, a, e, q, ad):
    """(status, matches): status consistent, inconsistent, boundary or missing; matches is the sorted tuple of
    classes whose definition the elements meet. AST is consistent only when no other definition is met."""
    if not served or e is None:
        return "missing", ()
    if e[0] == 1:
        matches = ("PAA",)
    elif gt(e, Decimal(1)) is True:
        matches = ("HYA",)
    elif lt(e, Decimal(1)) is True:
        if a is None or q is None or ad is None:
            return "missing", ()
        conds = class_conditions(a, e, q, ad)
        if any(c is None for c in conds.values()):
            return "boundary", ()
        matches = tuple(sorted(k for k, c in conds.items() if c))
    else:
        return "boundary", ()
    ok = served in matches or (served == "AST" and not matches)
    return ("consistent" if ok else "inconsistent"), matches


class Tally:
    """Counts and capped mismatch lists over all rows, one row at a time."""

    def __init__(self, seen=()):
        self.seen = set(seen)
        self.counts = {}
        self.mismatches = {"neo": [], "pha": [], "class": []}

    def bump(self, key, n=1):
        self.counts[key] = self.counts.get(key, 0) + n

    def keep(self, check, r, expected, detail):
        if len(self.mismatches[check]) < MAX_LIST:
            self.mismatches[check].append([check] + [r.get(f) for f in FIELDS] + [expected, detail])

    def add(self, r):
        if int(r["spkid"]) in self.seen:
            self.bump("excluded_seen")
            return
        self.bump("rows")
        q = parse_value(r.get("q"))
        moid = parse_value(r.get("moid"))
        h = parse_value(r.get("H"), exact=True)
        for f in ("H", "moid", "q"):
            x = parse_value(r.get(f))
            self.bump("precision %s %s" % (f, "none" if x is None else x[0].as_tuple().exponent))
        nr = None if q is None else neo_rule(q)

        flag = r.get("neo")
        if flag not in ("Y", "N"):
            st = "flag_other"
        elif q is None:
            st = "missing"
        elif nr is None:
            st = "boundary"
        else:
            st = "agree" if (flag == "Y") == nr else "mismatch"
            self.bump("neo_confusion flag=%s rule=%s" % (flag, "Y" if nr else "N"))
        self.bump("neo " + st)
        if st == "mismatch":
            self.keep("neo", r, "Y" if nr else "N", "rule q<1.3" if nr else "rule q>=1.3")

        flag = r.get("pha")
        rule = None
        if flag not in ("Y", "N"):
            st = "flag_other"
        elif moid is None or h is None:
            st = "missing"
        else:
            rule = pha_rule(moid, h)
            if rule is None:
                st = "boundary"
            else:
                st = "agree" if (flag == "Y") == rule else "mismatch"
                self.bump("pha_confusion flag=%s rule=%s" % (flag, "Y" if rule else "N"))
        self.bump("pha_all " + st)
        if nr is True:
            self.bump("pha_neo " + st)
        if st == "mismatch":
            reason = pha_reason(moid, h)
            self.bump("pha_reason " + reason)
            self.keep("pha", r, "Y" if rule else "N", reason)

        st, matches = class_check(r.get("class"), parse_value(r.get("a")), parse_value(r.get("e")), q,
                                  parse_value(r.get("ad")))
        self.bump("class " + st)
        if st in ("consistent", "inconsistent"):
            self.bump("class_matrix %s -> %s" % (r.get("class"), "+".join(matches) or "none"))
        if st == "inconsistent":
            self.keep("class", r, "+".join(matches) or "AST", "")


def decide_f1(n, k):
    """F1: the NEO flag disagrees with q < 1.3 au for at most 1 in 10,000 decidable rows."""
    if n < 100000:
        return "underpowered"
    return "holds" if 10000 * k <= n else "fails"


def decide_f2(n, k):
    """F2: among rows with q < 1.3 au, the PHA flag disagrees with the rule for at most 1 in 1,000 decidable rows."""
    if n < 10000:
        return "underpowered"
    return "holds" if 1000 * k <= n else "fails"


def decide_f3(n, k):
    """F3: the served class is inconsistent with the elements for at most 1 in 10,000 decidable rows."""
    if n < 100000:
        return "underpowered"
    return "holds" if 10000 * k <= n else "fails"


def decisions(t):
    c = lambda key: t.counts.get(key, 0)
    n1, k1 = c("neo agree") + c("neo mismatch"), c("neo mismatch")
    n2, k2 = c("pha_neo agree") + c("pha_neo mismatch"), c("pha_neo mismatch")
    n3, k3 = c("class consistent") + c("class inconsistent"), c("class inconsistent")
    return {
        "F1": {"n_decidable": n1, "n_mismatch": k1, "decision": decide_f1(n1, k1)},
        "F2": {"n_decidable": n2, "n_mismatch": k2, "decision": decide_f2(n2, k2)},
        "F3": {"n_decidable": n3, "n_inconsistent": k3, "decision": decide_f3(n3, k3)},
    }


def check_gate(note_path):
    """True if the fetched pre-registration note exists and carries GATE_TEXT."""
    try:
        with open(note_path, "rb") as f:
            return GATE_TEXT.encode("utf-8") in f.read()
    except OSError:
        return False


def load_seen(paths):
    """Set of int spkids in the given CSV files (column 'spkid')."""
    seen = set()
    for path in paths:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                seen.add(int(row["spkid"]))
    return seen


def page_url(offset, limit=PAGE):
    q = {"fields": ",".join(FIELDS), "sb-kind": "a", "sort": "spkid", "limit": str(limit),
         "limit-from": str(offset)}
    return API + "?" + urllib.parse.urlencode(q)


def fetch_bytes(url, tries=4, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": "sbdb_flags/" + VERSION + " (mv2@munimtech.com)"})
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


def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-note", required=True)
    ap.add_argument("--seen", nargs="+", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--pause", type=float, default=PAUSE_S)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    summary = {"version": VERSION, "api": API, "fields": FIELDS,
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
    tally = Tally(seen | PROBE_SPKIDS)
    pages, counts = [], []
    offset, last, sorted_ok = 0, None, True
    while True:
        body = fetch_bytes(page_url(offset))
        count, fields, rows = parse_page(body)
        pages.append({"offset": offset, "rows": len(rows), "bytes": len(body),
                      "sha256": hashlib.sha256(body).hexdigest()})
        counts.append(count)
        if fields != FIELDS:
            summary["error"] = "unexpected fields %r" % fields
            break
        for r in rows:
            k = int(r["spkid"])
            if last is not None and k <= last:
                sorted_ok = False
            last = k
            tally.add(r)
        offset += len(rows)
        if not rows or offset >= count:
            break
        time.sleep(args.pause)
    summary["pages"] = pages
    summary["api_count"] = counts[0] if counts else None
    summary["rows_read"] = offset
    summary["checks"] = {
        "fields_as_requested": "error" not in summary,
        "count_stable": len(set(counts)) == 1,
        "rows_equal_count": bool(counts) and offset == counts[0],
        "sorted_by_spkid_no_duplicates": sorted_ok,
        "all_seen_rows_found": tally.counts.get("excluded_seen", 0) == len(seen | PROBE_SPKIDS),
    }
    dec = decisions(tally)
    summary["decisions"] = dec
    summary["mismatch_rows_listed"] = {k: len(v) for k, v in tally.mismatches.items()}
    summary["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_json(os.path.join(args.out_dir, "summary.json"), summary)
    write_json(os.path.join(args.out_dir, "decisions.json"), dec)
    write_json(os.path.join(args.out_dir, "counts.json"), tally.counts)
    with open(os.path.join(args.out_dir, "mismatches.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(MISMATCH_HEADER)
        for check in ("neo", "pha", "class"):
            w.writerows(tally.mismatches[check])
    print(json.dumps({"rows_read": offset, "decisions": dec, "checks": summary["checks"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
