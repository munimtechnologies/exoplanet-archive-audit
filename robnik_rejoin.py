"""robnik_rejoin: the Robnik et al. 2026 cross-check of skye_apply 0.1.0, re-run with the comment-line fix only.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.
Pre-registration: findings/2026-10-19-robnik-rejoin-prereg.md in munimtechnologies/exoplanet-archive-audit. It amends
findings/2026-10-19-skye-apply-prereg.md, whose cross-check was void: Robnik et al.'s unrecovered_candidates.csv opens
with '#' comment lines, and read_table took the first of them as the header (431 rows, 0 KOI names).

Nothing about the KOIs is recomputed. The population and its would_fail values are read from skye_apply 0.1.0's
published crosscheck.csv (640 rows; its robnik_listed column is ignored) and must reproduce that run's fail/pass
counts. Robnik et al.'s file must be byte-identical to the one skye_apply read (sha256 below). Then Q1-Q3 are scored
exactly as pre-registered in findings/2026-10-18-skye-v3-robnik-crosscheck-prereg.md (as amended).
koi_name, read_table, robnik_names, fisher_greater, compare, scored, same_text and http_bytes are copied unchanged
from skye_apply 0.1.0, except the User-Agent string; strip_comments is new.

Usage: python robnik_rejoin.py --out-dir /out/rejoin
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
import urllib.request

VERSION = "0.1.0"
REPO = "https://raw.githubusercontent.com/munimtechnologies/exoplanet-archive-audit/main/{}"
PREREG = "findings/2026-10-19-robnik-rejoin-prereg.md"
SELF = "robnik_rejoin.py"
CROSSCHECK_URL = REPO.format("results/2026-10-19-skye-apply-0.1.0/crosscheck.csv")
CUMULATIVE_URL = REPO.format("results/2026-10-18-skye-census-0.1.0/tap/cumulative.csv")
CUMULATIVE_SHA256 = "df551272c3e8a945fed88c23129328b0d070c224f6cf503048b5f88e88e89286"
ROBNIK_URL = "https://raw.githubusercontent.com/JakobRobnik/exo-probability/main/results/unrecovered_candidates.csv"
ROBNIK_SHA256 = "151261a9522354db7de0ecc99556b19c8a824b68ebd2fac798d043ba281f8378"  # read by skye-apply-v1
ROBNIK_ROWS = 406
# skye_apply 0.1.0's population counts (results/2026-10-19-skye-apply-0.1.0/summary.json, robnik)
POPULATION = 640
EXPECTED = {"main": (20, 620), "window_340_400": (6, 77), "in_dr25_only": (4, 271)}
RB_WINDOW = (340.0, 400.0)
N_FAIL_MIN = 10
RATIO_MIN = 2.0
P_MAX = 0.01


def strip_comments(text):
    """text without its leading lines that start with '#'."""
    lines = text.split("\n")
    i = 0
    while i < len(lines) and lines[i].startswith("#"):
        i += 1
    return "\n".join(lines[i:])


def koi_name(s):
    """Robnik et al.'s KOI number ('5269.01') as an Archive kepoi_name ('K05269.01')."""
    return "K%08.2f" % float(s)


def read_table(text):
    """Rows of a CSV or tab-separated table."""
    head = text.split("\n", 1)[0]
    return list(csv.DictReader(io.StringIO(text), delimiter="\t" if "\t" in head else ","))


def robnik_names(rows):
    return {koi_name(r["KOI"]) for r in rows if (r.get("KOI") or "").strip()}


def fisher_greater(a, b, c, d):
    """One-sided Fisher exact p for [[a, b], [c, d]]: P(X >= a) with the margins fixed."""
    r1, c1, n = a + b, a + c, a + b + c + d
    total = math.comb(n, r1)
    return sum(math.comb(c1, x) * math.comb(n - c1, r1 - x) for x in range(a, min(r1, c1) + 1)) / total


def compare(rows, listed, lo=None, hi=None):
    """Listed fractions for Skye-fail (F) and Skye-pass (S) KOIs, optionally inside a period window."""
    g = [r for r in rows if (lo is None or float(r["period"]) >= lo) and (hi is None or float(r["period"]) <= hi)]
    f = [r for r in g if str(r["would_fail"]) == "1"]
    s = [r for r in g if str(r["would_fail"]) != "1"]
    a = sum(r["kepoi_name"] in listed for r in f)
    c = sum(r["kepoi_name"] in listed for r in s)
    ff = a / len(f) if f else None
    fs = c / len(s) if s else None
    return {"n_fail": len(f), "fail_listed": a, "n_pass": len(s), "pass_listed": c,
            "fail_fraction": ff, "pass_fraction": fs,
            "p_one_sided": fisher_greater(a, len(f) - a, c, len(s) - c) if f and s else None}


def scored(main, window):
    q1 = main["n_fail"] >= N_FAIL_MIN
    q2 = bool(q1 and main["fail_fraction"] and main["pass_fraction"] is not None
              and main["fail_fraction"] >= RATIO_MIN * main["pass_fraction"]
              and main["p_one_sided"] is not None and main["p_one_sided"] < P_MAX)
    q3 = bool(window["fail_fraction"] is not None and window["pass_fraction"] is not None
              and window["fail_fraction"] > window["pass_fraction"])
    return {"q1_enough_fails": q1, "q2_enrichment": q2, "q3_window_direction": q3}


def comparisons(pop, listed):
    """The three pre-registered comparisons: all, 340-400 d, and in-DR25 only (reported, not scored)."""
    return {"main": compare(pop, listed), "window_340_400": compare(pop, listed, *RB_WINDOW),
            "in_dr25_only": compare([r for r in pop if str(r["in_dr25"]) == "1"], listed)}


def population_ok(pop, cmp):
    """True when the population reproduces skye_apply 0.1.0's size and fail/pass counts."""
    return bool(len(pop) == POPULATION
                and all((cmp[k]["n_fail"], cmp[k]["n_pass"]) == v for k, v in EXPECTED.items()))


def robnik_ok(rows, sha):
    """Data check: the same file skye_apply read, 406 data rows, every row with a KOI value."""
    return bool(sha == ROBNIK_SHA256 and len(rows) == ROBNIK_ROWS
                and all((r.get("KOI") or "").strip() for r in rows))


def same_text(a, b):
    """True when two byte strings are equal once CRLF line ends are undone."""
    return a.replace(b"\r\n", b"\n") == b.replace(b"\r\n", b"\n")


def gate(own, fetch):
    """(open, detail): open when the pre-registration is live in the repository and the repository's
    robnik_rejoin.py matches own (this file's bytes). fetch: repository path -> bytes; it raises when missing."""
    detail = {}
    try:
        detail["prereg_live"] = len(fetch(PREREG)) > 0
        detail["code_matches"] = detail["prereg_live"] and same_text(fetch(SELF), own)
    except Exception as e:  # a missing file keeps the gate shut
        detail["error"] = repr(e)
    return bool(detail.get("prereg_live") and detail.get("code_matches")), detail


def http_bytes(url, tries=12, timeout=180, wait=20):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mv2-robnik-rejoin/0.1 (Munim, Inc.; "
                                                                     "mv2@munimtech.com)"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # retried, then raised
            last = e
            time.sleep(wait * (k + 1))
    raise last


def source(url):
    """(text, sha256) of url."""
    data = http_bytes(url)
    return data.decode("utf-8"), hashlib.sha256(data).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.abspath(__file__), "rb") as f:
        own = f.read()
    stats = {"version": VERSION, "robnik_rejoin_sha256": hashlib.sha256(own).hexdigest(),
             "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")}

    stats["gate_open"], stats["gate"] = gate(own, lambda p: http_bytes(REPO.format(p)))
    if not stats["gate_open"]:
        return finish(args.out_dir, stats, "stopped at the gate (pre-registration not live or code differs)")

    cx_text, cx_sha = source(CROSSCHECK_URL)
    pop = read_table(cx_text)
    before = comparisons(pop, set())
    stats["population"] = {"crosscheck_sha256": cx_sha, "rows": len(pop),
                           "counts": {k: (v["n_fail"], v["n_pass"]) for k, v in before.items()},
                           "reproduced": population_ok(pop, before)}
    if not stats["population"]["reproduced"]:
        return finish(args.out_dir, stats, "stopped: the population did not reproduce skye_apply 0.1.0's counts")

    rob_text, rob_sha = source(ROBNIK_URL)
    cum_text, cum_sha = source(CUMULATIVE_URL)
    rob_rows, cum_rows = read_table(strip_comments(rob_text)), read_table(cum_text)
    listed = robnik_names(rob_rows)
    cum_disp = {r["kepoi_name"]: r.get("koi_disposition", "") for r in cum_rows}
    listed_disp = {}
    for n in listed:
        k = cum_disp.get(n, "absent")
        listed_disp[k] = listed_disp.get(k, 0) + 1
    data_ok = robnik_ok(rob_rows, rob_sha) and cum_sha == CUMULATIVE_SHA256
    cmp = comparisons(pop, listed)
    rb = scored(cmp["main"], cmp["window_340_400"])
    stats.update({"checks": {"robnik_sha256": rob_sha, "robnik_sha_ok": rob_sha == ROBNIK_SHA256,
                             "robnik_rows": len(rob_rows), "robnik_listed_names": len(listed),
                             "cumulative_sha256_ok": cum_sha == CUMULATIVE_SHA256, "data_ok": data_ok},
                  "listed_by_cumulative_disposition": listed_disp, "comparisons": cmp,
                  "tests": {k: bool(data_ok and v) for k, v in rb.items()}})
    with open(os.path.join(args.out_dir, "crosscheck_rejoined.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kepoi_name", "kepid", "period", "in_dr25", "would_fail", "robnik_listed"])
        for r in pop:
            w.writerow([r["kepoi_name"], r["kepid"], r["period"], r["in_dr25"], r["would_fail"],
                        int(r["kepoi_name"] in listed)])
    return finish(args.out_dir, stats, "done")


def finish(out_dir, stats, status):
    """Write summary.json and report.md; exit code 0 when the run went through, else 1."""
    stats["status"] = status
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)
    lines = [f"# robnik_rejoin {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Pre-registered in {PREREG}. Code "
             "Apache-2.0, results CC BY 4.0.", "", f"Status: {status}.", "", "Gate: " + json.dumps(stats.get("gate")),
             ""]
    if "population" in stats:
        lines += ["Population: " + json.dumps(stats["population"]), ""]
    if "comparisons" in stats:
        lines += ["Checks: " + json.dumps(stats["checks"]), "", "Tests: " + json.dumps(stats["tests"]), "",
                  "Listed KOIs by cumulative disposition: " + json.dumps(stats["listed_by_cumulative_disposition"]),
                  "", "| comparison | n_fail | fail_listed | n_pass | pass_listed | p_one_sided |",
                  "|---|---|---|---|---|---|"]
        lines += [f"| {k} | {v['n_fail']} | {v['fail_listed']} | {v['n_pass']} | {v['pass_listed']} | "
                  f"{v['p_one_sided']} |" for k, v in stats["comparisons"].items()]
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=1))
    return 0 if status == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
