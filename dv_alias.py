"""dv_alias: where does the Kepler pipeline's own secondary search put the "missing" events of a KOI
whose TCE was found at a whole multiple of its period?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

When a DR25 TCE is found at k times a known KOI's period it is still federated to that KOI
(Thompson et al. 2018, arXiv:1710.06758 Sec. VI.2), and the KOI tables keep the shorter period. If
the shorter period is right, the other k - 1 events in each TCE orbit are real transits, so DV's
weak-secondary search (tce_maxmesd: the phase, in days, of the strongest event outside the primary)
should land at a phase j/k of the TCE orbit. If the strongest secondary lies elsewhere, the
pipeline's own data do not support the shorter period.

Built after KOI-4893.01 (KOI 6.58754 d, TCE 13.1751 d; strongest secondary at phase 0.650 in both
DR24 and DR25), the only one of 15 such DR25 candidates whose secondary is not at phase 1/k.

For the reverse case (TCE at P/k, KOI at P: vetting lengthened the period) DV's odd-even depth
statistic tce_bin_oedp_stat is reported; a small value means alternate TCE events look alike.

Verdicts for tce_long rows:
  secondary_at_alias   strongest secondary within one transit duration (at least one 29.4-min
                       cadence) of a phase j/k
  no_alias_secondary   strongest secondary elsewhere
  no_secondary_data    tce_maxmesd missing
A verdict points at rows worth a light-curve check. It is not a period correction.

Usage: python dv_alias.py --out-dir /out
"""
import argparse
import csv
import datetime as dt
import json
import math
import os
import sys
import urllib.parse
import urllib.request

VERSION = "0.1.0"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
UA = f"dv-alias/{VERSION} (Munim, Inc.; mv2@munimtech.com)"
CADENCE_D = 0.0204  # Kepler long cadence, 29.4 min
TOL = 1e-3  # relative tolerance on the period ratio
KMAX = 10

DR25 = ("select k.kepoi_name, k.kepid, k.koi_period, k.koi_duration, k.koi_pdisposition, "
        "k.koi_tce_plnt_num, t.tce_period, t.tce_duration, t.tce_depth, t.tce_model_snr, t.tce_maxmes, "
        "t.tce_maxmesd, t.wst_depth, t.tce_bin_oedp_stat from q1_q17_dr25_koi k join q1_q17_dr25_tce t "
        "on k.kepid = t.kepid and k.koi_tce_plnt_num = t.tce_plnt_num")
DR24 = ("select k.kepoi_name, k.koi_period, t.tce_period, t.tce_maxmes, t.tce_maxmesd "
        "from q1_q17_dr24_koi k join q1_q17_dr24_tce t "
        "on k.kepid = t.kepid and k.koi_tce_plnt_num = t.tce_plnt_num")
CUMULATIVE = "select kepoi_name, kepler_name, koi_disposition from cumulative"


def http_text(url, timeout=600):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def tap_rows(query):
    return list(csv.DictReader(http_text(TAP + "?" + urllib.parse.urlencode({"query": query, "format": "csv"}))
                               .splitlines()))


def num(row, key):
    v = (row.get(key) or "").strip()
    try:
        x = float(v)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def alias_factor(p_koi, p_tce, tol=TOL, kmax=KMAX):
    """("tce_long", k) if p_tce = k p_koi, ("koi_long", k) if p_koi = k p_tce (k >= 2, within tol), else
    (None, 1)."""
    if not p_koi or not p_tce or p_koi <= 0 or p_tce <= 0:
        return None, 1
    for kind, r in (("tce_long", p_tce / p_koi), ("koi_long", p_koi / p_tce)):
        if r >= 1.5:
            k = round(r)
            if 2 <= k <= kmax and abs(r / k - 1) < tol:
                return kind, k
    return None, 1


def alias_offset(maxmesd, p_tce, k):
    """(j, days): the alias phase j p_tce / k (j = 1 .. k - 1) nearest the strongest secondary, and the
    distance to it."""
    ph = maxmesd % p_tce
    return min(((j, abs(ph - j * p_tce / k)) for j in range(1, k)), key=lambda x: x[1])


def secondary_verdict(maxmesd, p_tce, k, dur_h):
    if maxmesd is None or not p_tce:
        return "no_secondary_data"
    tol = max((dur_h or 0) / 24.0, CADENCE_D)
    return "secondary_at_alias" if alias_offset(maxmesd, p_tce, k)[1] <= tol else "no_alias_secondary"


def classify(row, dr24=None, cum=None):
    """Output dict for one DR25 KOI-TCE row with an alias factor, or None."""
    p_koi, p_tce = num(row, "koi_period"), num(row, "tce_period")
    kind, k = alias_factor(p_koi, p_tce)
    if not kind:
        return None
    cum = cum or {}
    out = {"kepoi_name": row.get("kepoi_name", ""), "kepid": row.get("kepid", ""),
           "kepler_name": cum.get("kepler_name", ""), "koi_disposition": cum.get("koi_disposition", ""),
           "koi_pdisposition": row.get("koi_pdisposition", ""), "kind": kind, "k": k,
           "koi_period": p_koi, "tce_period": p_tce, "tce_duration_h": num(row, "tce_duration"),
           "tce_depth_ppm": num(row, "tce_depth"), "tce_model_snr": num(row, "tce_model_snr"),
           "sec_mes": num(row, "tce_maxmes"), "sec_phase_d": num(row, "tce_maxmesd"),
           "wst_depth_ppm": num(row, "wst_depth"), "oedp_stat": num(row, "tce_bin_oedp_stat")}
    if kind == "tce_long":
        md = out["sec_phase_d"]
        if md is not None:
            j, d = alias_offset(md, p_tce, k)
            out.update({"sec_phase": round((md % p_tce) / p_tce, 5), "nearest_alias_phase": f"{j}/{k}",
                        "offset_d": round(d, 5)})
        out["verdict"] = secondary_verdict(md, p_tce, k, out["tce_duration_h"])
        if dr24:
            p24, md24 = num(dr24, "tce_period"), num(dr24, "tce_maxmesd")
            if p24 and md24 is not None and alias_factor(p_koi, p24) == (kind, k):
                out["dr24_sec_phase"] = round((md24 % p24) / p24, 5)
                out["dr24_sec_mes"] = num(dr24, "tce_maxmes")
                out["dr24_verdict"] = secondary_verdict(md24, p24, k, out["tce_duration_h"])
    else:
        out["verdict"] = "koi_long"
    return out


FIELDS = ["kepoi_name", "kepid", "kepler_name", "koi_disposition", "koi_pdisposition", "kind", "k", "koi_period",
          "tce_period", "tce_duration_h", "tce_depth_ppm", "tce_model_snr", "sec_mes", "sec_phase_d", "sec_phase",
          "nearest_alias_phase", "offset_d", "wst_depth_ppm", "oedp_stat", "verdict", "dr24_sec_phase",
          "dr24_sec_mes", "dr24_verdict"]


def fmt(x, nd=3):
    if x is None or x == "":
        return ""
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    errors = []
    rows = tap_rows(DR25)
    try:
        dr24 = {r["kepoi_name"]: r for r in tap_rows(DR24)}
    except Exception as exc:  # DR24 is a consistency column only
        dr24 = {}
        errors.append(f"DR24 query: {type(exc).__name__}: {exc}"[:300])
    try:
        cum = {r["kepoi_name"]: r for r in tap_rows(CUMULATIVE)}
    except Exception as exc:
        cum = {}
        errors.append(f"cumulative query: {type(exc).__name__}: {exc}"[:300])

    out = [c for c in (classify(r, dr24.get(r.get("kepoi_name")), cum.get(r.get("kepoi_name"))) for r in rows) if c]
    out.sort(key=lambda r: (r["kind"], r["verdict"], r["kepoi_name"]))
    with open(os.path.join(args.out_dir, "census.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)

    counts = {}
    for r in out:
        key = f"{r['kind']}|{r['verdict']}|{r['koi_disposition'] or r['koi_pdisposition']}"
        counts[key] = counts.get(key, 0) + 1
    stats = {"version": VERSION, "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "dr25_rows": len(rows), "dr24_rows": len(dr24), "cumulative_rows": len(cum), "alias_rows": len(out),
             "tce_long": sum(r["kind"] == "tce_long" for r in out), "koi_long": sum(r["kind"] == "koi_long" for r in out),
             "counts": dict(sorted(counts.items())), "errors": errors}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

    cols = ["kepoi_name", "kepler_name", "koi_disposition", "k", "koi_period", "tce_period", "tce_depth_ppm",
            "sec_mes", "sec_phase", "offset_d", "verdict", "dr24_sec_phase", "dr24_verdict"]
    lines = [f"# dv-alias {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0.",
             "", f"{len(rows)} DR25 KOI-TCE rows; {len(out)} with a whole-number period ratio "
             f"({stats['tce_long']} TCE longer, {stats['koi_long']} KOI longer). A verdict points at rows worth a "
             "light-curve check; it is not a period correction.", "", "## Counts (kind | verdict | disposition)", ""]
    lines += [f"- {k}: {v}" for k, v in stats["counts"].items()]
    pick = [r for r in out if r["kind"] == "tce_long" and r["verdict"] != "secondary_at_alias"]
    lines += ["", "## TCE at k x the KOI period, strongest secondary not at an alias phase", "",
              "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(fmt(r.get(c)) for c in cols) + " |" for r in pick]
    conf = [r for r in out if r["koi_disposition"] == "CONFIRMED"]
    lines += ["", "## Every confirmed planet with a whole-number KOI/TCE period ratio", "",
              "| " + " | ".join(cols + ["oedp_stat"]) + " |", "|" + "---|" * (len(cols) + 1)]
    lines += ["| " + " | ".join(fmt(r.get(c)) for c in cols + ["oedp_stat"]) + " |" for r in conf]
    if errors:
        lines += ["", "## Errors", ""] + [f"- {e}" for e in errors]
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
