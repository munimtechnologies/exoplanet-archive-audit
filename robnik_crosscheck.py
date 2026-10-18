"""Cross-check skye_census KOI results against the unrecovered-candidate table of Robnik, Seljak, Jenkins & Bryson
2026 (MNRAS, doi:10.1093/mnras/stag419; arXiv:2601.07465; github.com/JakobRobnik/exo-probability, MIT).

Two independent tests of long-period Kepler candidates: Skye (same-time events across one skygroup, re-implemented
in skye_census.py) and Robnik et al.'s single-star pipeline. Do the candidates Skye would fail show up more often in
the list Robnik et al. could not recover? Pre-registration: findings/2026-10-18-skye-v3-robnik-crosscheck-prereg.md.

Apache-2.0. MV2 of Munim, Inc.; written by AI agents working in his name. Standard library only.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
import urllib.request

VERSION = "0.1.0"
ROBNIK_URL = "https://raw.githubusercontent.com/JakobRobnik/exo-probability/main/results/unrecovered_candidates.csv"
CUMULATIVE_URL = ("https://raw.githubusercontent.com/munimtechnologies/exoplanet-archive-audit/main/"
                  "results/2026-10-18-skye-census-0.1.0/tap/cumulative.csv")
# Looked up by hand before the pre-registration was written, so left out of every scored group.
EXCLUDED = {"K05269.01", "K05227.01", "K04426.01", "K05423.01", "K05398.01", "K01209.01", "K01356.01",
            "K05600.01", "K07894.01", "K08063.01", "K08107.01", "K08242.01", "K07915.01"}
P_MIN = 45.0
WINDOW = (340.0, 400.0)
N_FAIL_MIN = 10
RATIO_MIN = 2.0
P_MAX = 0.01


def koi_name(s):
    """Robnik et al.'s KOI number ('5269.01') as an Archive kepoi_name ('K05269.01')."""
    return "K%08.2f" % float(s)


def read_table(text):
    """Rows of a CSV or tab-separated table."""
    head = text.split("\n", 1)[0]
    return list(csv.DictReader(io.StringIO(text), delimiter="\t" if "\t" in head else ","))


def robnik_names(rows):
    return {koi_name(r["KOI"]) for r in rows if (r.get("KOI") or "").strip()}


def planets_per_star(cum_rows):
    """kepid -> number of cumulative KOIs dispositioned CANDIDATE or CONFIRMED (any period)."""
    n = {}
    for r in cum_rows:
        if r.get("koi_disposition") in ("CANDIDATE", "CONFIRMED"):
            n[r["kepid"]] = n.get(r["kepid"], 0) + 1
    return n


def population(koi_rows, per_star, excluded=EXCLUDED):
    """Scored KOIs: Skye-eligible CANDIDATEs with P > 45 d, alone on their star, not looked up beforehand."""
    out = []
    for r in koi_rows:
        if (r.get("status") == "ok" and str(r.get("eligible")) == "1" and r.get("disposition") == "CANDIDATE"
                and float(r["period"]) > P_MIN and per_star.get(str(r["kepid"]), 0) == 1
                and r["kepoi_name"] not in excluded):
            out.append(r)
    return out


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


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--koi-csv", required=True, help="koi_skye.csv from skye_census (a path, or an https URL)")
    ap.add_argument("--cumulative-csv", help="local cumulative table (default: fetch the published snapshot)")
    ap.add_argument("--robnik-csv", help="local Robnik table (default: fetch from GitHub)")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    src = {}
    for key, path, url in (("robnik", args.robnik_csv, ROBNIK_URL), ("cumulative", args.cumulative_csv, CUMULATIVE_URL)):
        raw = open(path, "rb").read() if path else fetch(url)
        with open(os.path.join(args.out_dir, key + ".csv"), "wb") as f:
            f.write(raw)
        src[key] = {"source": path or url, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                    "text": raw.decode("utf-8")}
    koi_raw = fetch(args.koi_csv) if args.koi_csv.startswith("https://") else open(args.koi_csv, "rb").read()
    rob_rows = read_table(src["robnik"]["text"])
    cum_rows = read_table(src["cumulative"]["text"])
    koi_rows = list(csv.DictReader(io.StringIO(koi_raw.decode("utf-8"))))
    listed = robnik_names(rob_rows)
    pop = population(koi_rows, planets_per_star(cum_rows))
    main_cmp = compare(pop, listed)
    win_cmp = compare(pop, listed, *WINDOW)
    in_dr25 = compare([r for r in pop if str(r.get("in_dr25")) == "1"], listed)
    cum_disp = {r["kepoi_name"]: r.get("koi_disposition", "") for r in cum_rows}
    listed_disp = {}
    for n in listed:
        k = cum_disp.get(n, "absent")
        listed_disp[k] = listed_disp.get(k, 0) + 1
    koi_sha = hashlib.sha256(koi_raw).hexdigest()
    with open(os.path.abspath(__file__), "rb") as f:
        own_sha = hashlib.sha256(f.read()).hexdigest()
    summary = {"version": VERSION, "robnik_crosscheck_sha256": own_sha, "koi_csv_sha256": koi_sha,
               "inputs": {k: {x: v[x] for x in ("source", "sha256", "bytes")} for k, v in src.items()},
               "robnik_rows": len(rob_rows), "robnik_listed_by_cumulative_disposition": listed_disp,
               "population": len(pop), "main": main_cmp, "window_340_400": win_cmp, "in_dr25_only": in_dr25,
               "tests": scored(main_cmp, win_cmp)}
    with open(os.path.join(args.out_dir, "crosscheck.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kepoi_name", "kepid", "period", "in_dr25", "would_fail", "robnik_listed"])
        for r in pop:
            w.writerow([r["kepoi_name"], r["kepid"], r["period"], r.get("in_dr25", ""), r["would_fail"],
                        int(r["kepoi_name"] in listed)])
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
