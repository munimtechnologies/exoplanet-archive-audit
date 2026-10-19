#!/usr/bin/env python3
# Apache-2.0. pick_variant 0.1.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
"""Pre-specified rule that picks ONE Rubble variant from scan_rubble's development results and fixes the bars
for the held-out reserve test.

Written and published before rubble-scan-v1 had started (findings/2026-10-19-rubble-variant-rule-prereg.md),
so the choice of variant and the bars cannot be tuned after seeing the development numbers, and the reserve
stars (listed in the scan's sample.json, never downloaded by it) stay a clean test.

Input: variants.json written by scan_rubble 0.1.0:
  {"n": scored TCEs, "nreal": {source: {"exact", "within1", "over", "under"}},
   "variants": {"<source>_<window>_<threshold>": {"all": {"tp","fp","fn","tn"}, "pn1": {...}, "pn>1": {...},
                                                   "rubble_only": {"n", "exact", "within1"}}}}
  tp/fp/fn/tn compare "at least one real event fails the variant" with DR25's iflag0 (RUBBLE) per TCE.
  rubble_only counts TCEs whose only per-event flag is RUBBLE and whose variant fail count equals nrealt - ngoodt.

Rule R1-R6 (integer arithmetic wherever a comparison could sit on a float boundary):
  R1 power: the development scan is underpowered if scored TCEs with iflag0 = 1 (tp + fn, the same for every
     variant) < 20 or Rubble-only TCEs < 8. Then nothing is chosen.
  R2 floor: error = fp + fn over all scored TCEs. If every variant has error > 20 % of n (5 * error > n), the
     result is NEGATIVE: no public variant reproduces iflag0 well enough, and that is published as the result.
  R3 candidates: variants with error <= min_error + max(1, ceil(min_error / 10)).
  R4 DR25's value: if any candidate uses threshold 0.75, only those remain.
  R5 pick: the candidate with the most Rubble-only exact TCEs; ties go to the higher threshold, then window 2
     over 1, then the source order init, white, pdc, resid.
  R6 bars for the reserve, from the chosen variant's development rates: recall >= dev - 0.10; precision >=
     dev - 0.10; Rubble-only exact fraction >= dev - 0.15; nrealt exact fraction for the chosen source >=
     dev - 0.10. Bars are floored at 0 and rounded to 3 decimals; reserve rates are rounded to 3 decimals
     before comparing. The reserve is underpowered (reported, not scored) if its scored rows have < 30 iflag0
     TCEs or < 10 Rubble-only TCEs. PASS = every bar met; otherwise FAIL. Never re-scored.
"""
import argparse
import json
import os
import sys

VERSION = "0.1.0"
SOURCES = ("init", "white", "pdc", "resid")
WINDOWS = (1, 2)
THRESHOLDS = (0.25, 0.5, 0.75)
MIN_FLAGGED_DEV = 20
MIN_RUBBLE_ONLY_DEV = 8
ERROR_RATE_NUM, ERROR_RATE_DEN = 1, 5  # negative result if every variant has error / n > 1/5
TOL_DENOM = 10  # candidates: error <= min_error + max(1, ceil(min_error / 10))
PREFERRED_THRESHOLD = 0.75
MARGINS = {"recall": 0.10, "precision": 0.10, "rubble_only_exact": 0.15, "nreal_exact": 0.10}
MIN_FLAGGED_RESERVE = 30
MIN_RUBBLE_ONLY_RESERVE = 10


def variant_names():
    return ["{}_{}_{}".format(s, w, t) for s in SOURCES for w in WINDOWS for t in THRESHOLDS]


def parse_variant(name):
    """'white_2_0.75' -> ('white', 2, 0.75)."""
    s, w, t = name.rsplit("_", 2)
    return s, int(w), float(t)


def error(v):
    return v["all"]["fp"] + v["all"]["fn"]


def flagged(v):
    """Scored TCEs with iflag0 = 1; identical for every variant of the same scan."""
    return v["all"]["tp"] + v["all"]["fn"]


def tolerance(min_error):
    return max(1, -(-min_error // TOL_DENOM))


def ratio(a, b):
    return a / b if b else 0.0


def rates(res, name):
    v = res["variants"][name]
    a, ro = v["all"], v["rubble_only"]
    src = parse_variant(name)[0]
    return {"recall": ratio(a["tp"], a["tp"] + a["fn"]),
            "precision": ratio(a["tp"], a["tp"] + a["fp"]),
            "rubble_only_exact": ratio(ro["exact"], ro["n"]),
            "nreal_exact": ratio(res["nreal"][src]["exact"], res["n"])}


def candidates(variants):
    """(sorted candidate names, min_error) under R3."""
    errs = {name: error(v) for name, v in variants.items()}
    m = min(errs.values())
    return sorted(n for n, e in errs.items() if e <= m + tolerance(m)), m


def sort_key(name, variants):
    s, w, t = parse_variant(name)
    return (-variants[name]["rubble_only"]["exact"], -t, -w, SOURCES.index(s))


def choose(variants):
    """(chosen name, how) under R3-R5."""
    names, min_err = candidates(variants)
    pref = [n for n in names if parse_variant(n)[2] == PREFERRED_THRESHOLD]
    pool = pref if pref else names
    chosen = sorted(pool, key=lambda n: sort_key(n, variants))[0]
    return chosen, {"min_error": min_err, "tolerance": tolerance(min_err), "candidates": names,
                    "restricted_to_0.75": bool(pref)}


def bars_from(dev_rates):
    return {k: round(max(0.0, dev_rates[k] - MARGINS[k]), 3) for k in MARGINS}


def decide(res):
    """Apply R1-R6 to a scan's variants.json content."""
    variants = res.get("variants") or {}
    n = res.get("n", 0)
    out = {"tool": "pick_variant", "version": VERSION, "dev_n": n, "flagged": 0, "rubble_only_n": 0}
    if not variants or not n:
        out["status"] = "underpowered_dev"
        return out
    first = next(iter(variants.values()))
    out["flagged"], out["rubble_only_n"] = flagged(first), first["rubble_only"]["n"]
    if out["flagged"] < MIN_FLAGGED_DEV or out["rubble_only_n"] < MIN_RUBBLE_ONLY_DEV:
        out["status"] = "underpowered_dev"
        return out
    errs = {name: error(v) for name, v in variants.items()}
    out["error_rates"] = {name: round(e / n, 4) for name, e in errs.items()}
    best = min(errs.values())
    out["best_error_rate"] = round(best / n, 4)
    if best * ERROR_RATE_DEN > n * ERROR_RATE_NUM:
        out["status"] = "negative"
        return out
    chosen, how = choose(variants)
    dev = rates(res, chosen)
    out.update({"status": "chosen", "chosen": chosen, "how": how,
                "dev_rates": {k: round(x, 4) for k, x in dev.items()}, "bars": bars_from(dev),
                "reserve_min": {"flagged": MIN_FLAGGED_RESERVE, "rubble_only": MIN_RUBBLE_ONLY_RESERVE}})
    return out


def evaluate_reserve(decision, reserve_res):
    """Score a reserve scan (same variants.json layout) against the fixed bars. Never re-score."""
    name = decision["chosen"]
    v = reserve_res["variants"][name]
    out = {"variant": name, "reserve_n": reserve_res["n"], "flagged": flagged(v),
           "rubble_only_n": v["rubble_only"]["n"]}
    if out["flagged"] < MIN_FLAGGED_RESERVE or out["rubble_only_n"] < MIN_RUBBLE_ONLY_RESERVE:
        out["status"] = "underpowered_reserve"
        return out
    got = rates(reserve_res, name)
    checks = {}
    for k in MARGINS:
        g = round(got[k], 3)
        checks[k] = {"bar": decision["bars"][k], "got": g, "pass": g >= decision["bars"][k]}
    out["checks"] = checks
    out["status"] = "pass" if all(c["pass"] for c in checks.values()) else "fail"
    return out


def render(decision, reserve=None):
    lines = ["# pick_variant {} decision".format(VERSION), "", "Status: **{}**.".format(decision["status"]),
             "Development: n = {}, iflag0 TCEs = {}, Rubble-only TCEs = {}.".format(
                 decision["dev_n"], decision["flagged"], decision["rubble_only_n"]), ""]
    if "best_error_rate" in decision:
        lines.append("Best (fp + fn) / n over all variants: {}.".format(decision["best_error_rate"]))
    if decision["status"] == "chosen":
        how = decision["how"]
        lines += ["Candidates (error <= {} + {}): {}; restricted to threshold 0.75: {}.".format(
            how["min_error"], how["tolerance"], ", ".join(how["candidates"]), how["restricted_to_0.75"]),
            "Chosen variant: **{}**.".format(decision["chosen"]), "",
            "| rate | development | reserve bar |", "|---|---|---|"]
        for k in MARGINS:
            lines.append("| {} | {} | >= {} |".format(k, decision["dev_rates"][k], decision["bars"][k]))
        lines.append("")
    if reserve:
        lines += ["## Reserve", "", "Status: **{}** (n = {}, iflag0 = {}, Rubble-only = {}).".format(
            reserve["status"], reserve["reserve_n"], reserve["flagged"], reserve["rubble_only_n"]), ""]
        for k, c in reserve.get("checks", {}).items():
            lines.append("- {}: got {} vs bar {}: {}".format(k, c["got"], c["bar"], "pass" if c["pass"] else "FAIL"))
        lines.append("")
    lines.append("Made with AI agents; MV2, Munim, Inc., mv2@munimtech.com.")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", required=True, help="variants.json from the development scan")
    ap.add_argument("--reserve", default=None, help="variants.json from the reserve scan (scoring step)")
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    with open(args.variants, encoding="utf-8") as f:
        decision = decide(json.load(f))
    reserve = None
    if args.reserve and decision["status"] == "chosen":
        with open(args.reserve, encoding="utf-8") as f:
            reserve = evaluate_reserve(decision, json.load(f))
    with open(os.path.join(args.out_dir, "decision.json"), "w", encoding="utf-8") as f:
        json.dump({"decision": decision, "reserve": reserve}, f, indent=1)
    with open(os.path.join(args.out_dir, "decision.md"), "w", encoding="utf-8") as f:
        f.write(render(decision, reserve))
    print(json.dumps({"status": decision["status"], "chosen": decision.get("chosen"),
                      "reserve": reserve["status"] if reserve else None}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
