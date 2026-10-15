"""lum_check: stellar luminosities in the NASA Exoplanet Archive stored on a
linear scale in the log10 column st_lum, and the Archive's own calculated values
(pscomppars "Calculated Value") recomputed from the same row's inputs with the
formulas the Archive documents (docs/pscp_calc.html).

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

Found by hand first (2026-10-15): Fischer et al. 2012 print L* = 0.19 L_sun for
HIP 57274, and the Archive stores st_lum = 0.19 in a column documented as
log10(L/L_sun). The composite table then computes pl_insol = 10**0.19 / a**2,
8 times too high, for all three planets.

Usage: python lum_check.py --out-dir /out [--data-dir /data]
"""
import argparse
import csv
import datetime as dt
import json
import math
import os
import re
import statistics
import sys
import urllib.parse
import urllib.request

VERSION = "0.1.0"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
UA = f"lum-check/{VERSION} (Munim, Inc.; munimversion2@gmail.com)"
TSUN = 5772.0
RSUN_AU = 0.00465047
RHO_EARTH = 5.514     # g/cm3
OFF_DEX = 0.15        # st_lum this far from log10(R^2 (T/Tsun)^4) is flagged
LIN_DEX = 0.10        # ... and called linear-in-log if log10(st_lum) lands this close (TOI-3568: 0.065)
CALC = "Calculated Value"

PS_COLS = ["pl_name", "hostname", "default_flag", "st_refname", "st_lum", "st_lumerr1", "st_lumerr2",
           "st_rad", "st_teff"]
PC_LUM = ["pl_name", "hostname", "st_lum", "st_lum_reflink", "st_rad", "st_rad_reflink", "st_teff",
          "st_teff_reflink", "pl_orbsmax", "pl_orbsmax_reflink", "pl_insol", "pl_insol_reflink"]
# optional checks, one query each so a missing column cannot stop the run
PC_EXTRA = {
    "pl_eqt": ["pl_name", "pl_eqt", "pl_eqt_reflink", "st_teff", "st_rad", "pl_orbsmax"],
    "pl_dens": ["pl_name", "pl_dens", "pl_dens_reflink", "pl_bmasse", "pl_rade"],
    "pl_angsep": ["pl_name", "pl_angsep", "pl_angsep_reflink", "pl_orbsmax", "sy_dist"],
}


def fetch(query, path):
    if path and os.path.exists(path) and os.path.getsize(path) > 1000:
        with open(path, encoding="utf-8") as f:
            return f.read()
    url = TAP + "?" + urllib.parse.urlencode({"query": query, "format": "csv"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=900) as r:
        text = r.read().decode("utf-8")
    if path:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return text


def num(row, key):
    v = (row.get(key) or "").strip()
    if not v:
        return None
    try:
        x = float(v)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def ref_text(html):
    if not html:
        return ""
    m = re.search(r">([^<]+)<", html)
    return (m.group(1) if m else html).replace("&amp;", "&").strip()


def logl_rt(r, t):
    """log10(L/L_sun) from radius (R_sun) and Teff (K) by Stefan-Boltzmann."""
    if not r or not t or r <= 0 or t <= 0:
        return None
    return 2 * math.log10(r) + 4 * math.log10(t / TSUN)


def lum_class(st_lum, pred):
    """'ok', 'linear_in_log' (st_lum is L/L_sun, not its log) or 'mismatch'; None if untestable."""
    if st_lum is None or pred is None:
        return None
    if abs(st_lum - pred) <= OFF_DEX:
        return "ok"
    if st_lum > 0 and abs(math.log10(st_lum) - pred) <= LIN_DEX:
        return "linear_in_log"
    return "mismatch"


def lum_rows(rows, ref_key, table):
    """Every testable row whose st_lum is off, with its class."""
    out = []
    for r in rows:
        lum, pred = num(r, "st_lum"), logl_rt(num(r, "st_rad"), num(r, "st_teff"))
        c = lum_class(lum, pred)
        if c in (None, "ok"):
            continue
        out.append({"table": table, "pl_name": r.get("pl_name", ""), "hostname": r.get("hostname", ""),
                    "default_flag": r.get("default_flag", ""), "reference": ref_text(r.get(ref_key, "")),
                    "st_lum": lum, "st_rad": r.get("st_rad", ""), "st_teff": r.get("st_teff", ""),
                    "logL_from_RT": round(pred, 4), "diff_dex": round(lum - pred, 3), "class": c})
    out.sort(key=lambda x: (x["class"] != "linear_in_log", -abs(x["diff_dex"])))
    return out


def lum_refs(rows, ref_key):
    """Per reference: rows tested, linear-in-log and other mismatches, median offset."""
    by = {}
    for r in rows:
        c = lum_class(num(r, "st_lum"), logl_rt(num(r, "st_rad"), num(r, "st_teff")))
        if c is None:
            continue
        ref = ref_text(r.get(ref_key, ""))
        e = by.setdefault(ref, {"reference": ref, "rows": 0, "linear_in_log": 0, "mismatch": 0, "d": []})
        e["rows"] += 1
        e[c] = e.get(c, 0) + 1
        e["d"].append(num(r, "st_lum") - logl_rt(num(r, "st_rad"), num(r, "st_teff")))
    out = []
    for e in by.values():
        e.pop("ok", None)
        d = e.pop("d")
        if not e["linear_in_log"] and not e["mismatch"]:
            continue
        e["median_diff_dex"] = round(statistics.median(d), 3)
        out.append(e)
    out.sort(key=lambda e: (-e["linear_in_log"], -e["mismatch"]))
    return out


def predict(param, r):
    """The Archive's documented formula for a calculated parameter, from the same row."""
    g = lambda k: num(r, k)
    if param == "pl_insol":
        lum, a = g("st_lum"), g("pl_orbsmax")
        return None if lum is None or not a or a <= 0 else 10 ** lum / a ** 2
    if param == "pl_eqt":
        t, rs, a = g("st_teff"), g("st_rad"), g("pl_orbsmax")
        return None if not t or not rs or not a or a <= 0 else t * math.sqrt(rs * RSUN_AU / (2 * a))
    if param == "pl_dens":
        m, rp = g("pl_bmasse"), g("pl_rade")
        return None if not m or not rp or rp <= 0 else RHO_EARTH * m / rp ** 3
    if param == "pl_angsep":
        a, d = g("pl_orbsmax"), g("sy_dist")
        return None if not a or not d or d <= 0 else 1000 * a / d
    raise ValueError(param)


TOL = {"pl_insol": (0.03, 0.0002), "pl_eqt": (0.02, 1.5), "pl_dens": (0.03, 0.006), "pl_angsep": (0.03, 0.006)}


def calc_rows(rows, param):
    """Calculated values of one parameter: 'ok', 'differs' or 'inputs_missing'."""
    out = []
    rel, floor = TOL[param]
    for r in rows:
        if ref_text(r.get(param + "_reflink", "")) != CALC:
            continue
        obs, pred = num(r, param), predict(param, r)
        if obs is None:
            continue
        if pred is None:
            status = "inputs_missing"
        else:
            status = "ok" if abs(obs - pred) <= max(rel * abs(pred), floor) else "differs"
        e = {"param": param, "pl_name": r.get("pl_name", ""), "observed": obs,
             "predicted": "" if pred is None else round(pred, 6),
             "ratio": "" if not pred else round(obs / pred, 4), "status": status, "st_lum_class": "",
             "st_lum_reference": "", "insol_if_linear": ""}
        if param == "pl_insol":
            lum, a = num(r, "st_lum"), num(r, "pl_orbsmax")
            c = lum_class(lum, logl_rt(num(r, "st_rad"), num(r, "st_teff")))
            e["st_lum_class"] = c or ""
            e["st_lum_reference"] = ref_text(r.get("st_lum_reflink", ""))
            if c == "linear_in_log" and a:
                e["insol_if_linear"] = round(lum / a ** 2, 6)
        out.append(e)
    return out


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-dir", default="")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    dd = args.data_dir
    path = lambda name: os.path.join(dd, name) if dd else None
    ps = list(csv.DictReader(fetch("select " + ",".join(PS_COLS) + " from ps", path("ps-lum.csv")).splitlines()))
    pc = list(csv.DictReader(fetch("select " + ",".join(PC_LUM) + " from pscomppars",
                                   path("pc-lum.csv")).splitlines()))

    flagged = lum_rows(ps, "st_refname", "ps") + lum_rows(pc, "st_lum_reflink", "pscomppars")
    refs = lum_refs(ps, "st_refname")
    calc = calc_rows(pc, "pl_insol")
    errors = {}
    for param, cols in PC_EXTRA.items():
        try:
            rows = list(csv.DictReader(fetch("select " + ",".join(cols) + " from pscomppars",
                                             path(f"pc-{param}.csv")).splitlines()))
            calc += calc_rows(rows, param)
        except Exception as ex:  # noqa: BLE001 - one optional check failing must not stop the others
            errors[param] = str(ex)[:300]

    write_csv(os.path.join(args.out_dir, "lum_rows.csv"), flagged,
              ["table", "pl_name", "hostname", "default_flag", "reference", "st_lum", "st_rad", "st_teff",
               "logL_from_RT", "diff_dex", "class"])
    write_csv(os.path.join(args.out_dir, "lum_refs.csv"), refs,
              ["reference", "rows", "linear_in_log", "mismatch", "median_diff_dex"])
    write_csv(os.path.join(args.out_dir, "calc_rows.csv"), [c for c in calc if c["status"] != "ok"],
              ["param", "pl_name", "observed", "predicted", "ratio", "status", "st_lum_class",
               "st_lum_reference", "insol_if_linear"])

    tested = lambda rows: sum(lum_class(num(r, "st_lum"), logl_rt(num(r, "st_rad"), num(r, "st_teff"))) is not None
                              for r in rows)
    count = lambda table, c: sum(1 for f in flagged if f["table"] == table and f["class"] == c)
    calc_stats = {}
    for c in calc:
        s = calc_stats.setdefault(c["param"], {"calculated": 0, "ok": 0, "differs": 0, "inputs_missing": 0})
        s["calculated"] += 1
        s[c["status"]] += 1
    propagated = [c for c in calc if c["param"] == "pl_insol" and c["st_lum_class"] == "linear_in_log"]
    stats = {
        "version": VERSION, "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "ps_rows": len(ps), "ps_rows_tested": tested(ps),
        "ps_linear_in_log": count("ps", "linear_in_log"), "ps_other_mismatch": count("ps", "mismatch"),
        "ps_default_linear_in_log": sum(1 for f in flagged if f["table"] == "ps" and f["class"] == "linear_in_log"
                                        and f["default_flag"] == "1"),
        "references_with_linear_in_log": sum(1 for e in refs if e["linear_in_log"]),
        "pscomppars_rows": len(pc), "pscomppars_rows_tested": tested(pc),
        "pscomppars_linear_in_log": count("pscomppars", "linear_in_log"),
        "pscomppars_other_mismatch": count("pscomppars", "mismatch"),
        "calculated_values": calc_stats,
        "calculated_insol_from_linear_lum": len(propagated),
        "query_errors": errors,
    }
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

    lines = [f"# lum-check {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0. "
             "Each row is a candidate to check against the source paper, not a confirmed error.", ""]
    lines += [f"- {k}: {v}" for k, v in stats.items() if k not in ("version", "run_at")]
    lines += ["", "## References with luminosities that look linear (first 40)", "",
              "| reference | rows tested | linear in log | other mismatch | median st_lum - logL(R,T) |",
              "|---|---|---|---|---|"]
    for e in refs[:40]:
        lines.append(f"| {e['reference']} | {e['rows']} | {e['linear_in_log']} | {e['mismatch']} | "
                     f"{e['median_diff_dex']} |")
    lines += ["", "## Calculated insolation built on a linear luminosity", "",
              "| planet | stored pl_insol | if st_lum is linear | st_lum from |", "|---|---|---|---|"]
    for c in propagated:
        lines.append(f"| {c['pl_name']} | {c['observed']} | {c['insol_if_linear']} | {c['st_lum_reference']} |")
    lines += ["", "## Calculated values that do not follow the Archive's own formula (first 80)", "",
              "| parameter | planet | stored | formula, same row | ratio | status |", "|---|---|---|---|---|---|"]
    for c in [c for c in calc if c["status"] != "ok"][:80]:
        lines.append(f"| {c['param']} | {c['pl_name']} | {c['observed']} | {c['predicted']} | {c['ratio']} | "
                     f"{c['status']} |")
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
