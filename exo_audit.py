"""exo_audit: physical self-consistency audit of the NASA Exoplanet Archive.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

For every parameter set (row) of the Planetary Systems table (ps), and for the
composite table (pscomppars), it tests relations that must hold within one
solution: Kepler's third law, bulk density, a/R*, Rp/R*, transit depth vs
(Rp/R*)^2, stellar density from the transit vs from M and R, st_dens and
log g vs M and R, and insolation vs Teff, R* and a. A row is flagged when the
mismatch exceeds a physical tolerance AND (when uncertainties are given) the
quoted errors. Mismatches equal to a common unit factor (100, 1e4, 317.8,
11.21, 109.1, 215.0, 1.41, ...) are labelled as likely unit slips.

v0.2 adds a per-reference test: when most rows from one reference are off by
the same factor, that is a catalog-level slip, not scatter (systematics.csv).

v0.3 applies each unit factor only to the checks it can explain (the 1.41
solar-density factor only to stellar densities, ppt-vs-percent only to
depths), and writes unit_groups.csv: every row, in both tables, of each
reference whose shared offset matches a unit factor, with its ADS bibcode and
the ratio after the fix, so each catalog-level finding can be checked row by row.

Usage: python exo_audit.py --out-dir /out [--data-dir /data] [--offline FILE]
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import re
import statistics
import sys
import urllib.parse
import urllib.request

VERSION = "0.3.0"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

# Nominal constants (IAU 2015 nominal values where they exist)
YEAR_D = 365.256363          # sidereal year, days (a^3 = M P^2 in au, yr, Msun)
MEARTH_MSUN = 3.003489e-6    # GM_earth / GM_sun
REARTH_RSUN = 1.0 / 109.076  # R_earth(eq) / R_sun
AU_RSUN = 215.032            # au / R_sun
RHO_EARTH = 5.514            # g/cm^3 (mean)
RHO_SUN = 1.4098             # g/cm^3 (M_sun / (4/3 pi R_sun^3), nominal)
LOGG_SUN = 4.438             # cgs
TEFF_SUN = 5772.0
G_SI = 6.67430e-11

PARAMS = [
    "pl_orbper", "pl_orbsmax", "pl_rade", "pl_bmasse", "pl_dens", "pl_ratdor",
    "pl_ratror", "pl_trandep", "pl_insol", "st_mass", "st_rad", "st_dens",
    "st_logg", "st_teff",
]
EXTRA = ["pl_orbeccen", "pl_orbeccenlim", "pl_bmassprov", "discoverymethod",
         "pl_controv_flag", "cb_flag", "pl_name", "hostname"]
PS_ONLY = ["default_flag", "pl_refname", "st_refname"]
# pscomppars names the source of each value; fetched in a separate query so a
# missing column cannot cost the main table
REFLINKS = ["pl_orbsmax_reflink", "pl_ratdor_reflink", "pl_ratror_reflink",
            "pl_trandep_reflink", "pl_insol_reflink", "st_dens_reflink",
            "st_logg_reflink", "st_mass_reflink", "st_rad_reflink"]

STAR_DENSITY_CHECKS = ("st_dens_vs_MR", "rhostar_transit_vs_MR")

# label, factor, checks it can explain (None: any check)
UNIT_FACTORS = [
    ("x100 (percent vs fraction)", 100.0, None),
    ("x1e4 (ppm vs percent)", 1e4, None),
    ("x1e6 (ppm vs fraction)", 1e6, None),
    ("x1000", 1000.0, None),
    ("x10 (ppt vs percent)", 10.0, ("depth_vs_k2",)),
    ("Jupiter vs Earth mass (317.8)", 317.83, None),
    ("Jupiter vs Earth radius (11.21)", 11.209, None),
    ("Sun vs Earth radius (109.1)", 109.076, None),
    ("Sun vs Jupiter radius (9.73)", 9.731, None),
    ("au vs solar radius (215.0)", 215.032, None),
    ("hours vs days (24)", 24.0, None),
    ("solar vs g/cm3 density (1.41)", RHO_SUN, STAR_DENSITY_CHECKS),
]
FACTOR = {label: f for label, f, _ in UNIT_FACTORS}

# the parameter whose value is being tested, so a flag is charged to its source
OBS_PARAM = {
    "kepler3_a": "pl_orbsmax", "bulk_density": "pl_dens", "a_over_rstar": "pl_ratdor",
    "rp_over_rstar": "pl_ratror", "depth_vs_k2": "pl_trandep",
    "rhostar_transit_vs_MR": "pl_ratdor", "st_dens_vs_MR": "st_dens",
    "logg_vs_MR": "st_logg", "insolation": "pl_insol",
}

SYS_MIN_ROWS = 5          # rows from one reference before a shared offset counts
SYS_MIN_OFFSET = 0.10     # median ratio at least 10% from 1
SYS_COHERENT = 0.5        # at least half the rows within 10% of that median


def columns(table):
    cols = []
    for p in PARAMS:
        cols += [p, p + "err1", p + "err2", p + "lim"]
    cols += EXTRA
    if table == "ps":
        cols += PS_ONLY
    return cols


def tap_url(query):
    return TAP + "?" + urllib.parse.urlencode({"query": query, "format": "csv"})


def table_query(table):
    return "select " + ",".join(columns(table)) + " from " + table


def reflink_query():
    return "select pl_name," + ",".join(REFLINKS) + " from pscomppars"


def fetch(query, name, cache_dir):
    """Download a TAP query as CSV text; the cache file name carries a hash of
    the query so a changed column list is never served from an old file."""
    tag = hashlib.sha1(query.encode()).hexdigest()[:8]
    path = os.path.join(cache_dir, f"{name}-{tag}.csv") if cache_dir else None
    if path and os.path.exists(path) and os.path.getsize(path) > 1000:
        with open(path, encoding="utf-8") as f:
            return f.read(), "cache"
    req = urllib.request.Request(tap_url(query), headers={"User-Agent": f"exo-audit/{VERSION} (Munim, Inc.; munimversion2@gmail.com)"})
    with urllib.request.urlopen(req, timeout=600) as r:
        text = r.read().decode("utf-8")
    if path:
        os.makedirs(cache_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return text, "download"


def num(row, key):
    v = row.get(key, "")
    if v is None or v == "":
        return None
    try:
        x = float(v)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def value(row, key):
    """Measured value only: drop upper/lower limits."""
    lim = row.get(key + "lim", "")
    if lim not in ("", "0", "0.0", None):
        return None
    x = num(row, key)
    if x is None or x <= 0:
        return None
    return x


def rel_sigma(row, key):
    x = value(row, key)
    e1, e2 = num(row, key + "err1"), num(row, key + "err2")
    if x is None or e1 is None or e2 is None:
        return None
    s = (abs(e1) + abs(e2)) / 2.0
    return s / x if s > 0 else None


def combine(*rels):
    """Quadrature sum of (relative sigma, weight) pairs; None if any is missing."""
    tot = 0.0
    for r, w in rels:
        if r is None:
            return None
        tot += (w * r) ** 2
    return math.sqrt(tot)


def ref_text(html):
    if not html:
        return ""
    m = re.search(r">([^<]+)<", html)
    return (m.group(1) if m else html).replace("&amp;", "&").strip()


def ref_bibcode(html):
    """ADS bibcode from the reference link, or '' if the link has none."""
    m = re.search(r"/abs/([^/\s\"'>]+)", html or "")
    return urllib.parse.unquote(m.group(1)).replace("&amp;", "&") if m else ""


def is_pipeline(ref):
    """Automated survey catalogs (Kepler KOI/TCE tables), not a paper's own fit."""
    return "KOI Table" in ref or "TCE" in ref


def unit_slip(ratio, check=None):
    if ratio is None or ratio <= 0:
        return ""
    for label, f, checks in UNIT_FACTORS:
        if checks is not None and check not in checks:
            continue
        for r in (ratio, 1.0 / ratio):
            if abs(r / f - 1.0) < 0.03:
                return label
    return ""


def unit_fixed(ratio, label):
    """The ratio once the unit factor is removed (multiplied or divided, whichever lands nearer 1)."""
    f = FACTOR[label]
    return min((ratio * f, ratio / f), key=lambda x: abs(math.log(x)))


def circularish(row):
    e = num(row, "pl_orbeccen")
    return e is None or e <= 0.1


def source_html(row, table, check):
    p = OBS_PARAM[check]
    if table == "ps":
        return row.get("st_refname" if p.startswith("st_") else "pl_refname", "") or ""
    return row.get(p + "_reflink", "") or ""


def source_ref(row, table, check):
    return ref_text(source_html(row, table, check))


# Physical predictions -------------------------------------------------------

def kepler_a_au(period_d, mstar_msun, mp_earth=None):
    m = mstar_msun + (mp_earth or 0.0) * MEARTH_MSUN
    return (m * (period_d / YEAR_D) ** 2) ** (1.0 / 3.0)


def bulk_density(mass_earth, radius_earth):
    return RHO_EARTH * mass_earth / radius_earth ** 3


def star_density_from_transit(ratdor, period_d):
    p = period_d * 86400.0
    return 3.0 * math.pi * ratdor ** 3 / (G_SI * p ** 2) / 1000.0  # g/cm^3


def star_density(mass_msun, radius_rsun):
    return RHO_SUN * mass_msun / radius_rsun ** 3


def logg(mass_msun, radius_rsun):
    return LOGG_SUN + math.log10(mass_msun) - 2.0 * math.log10(radius_rsun)


def insolation(teff, rstar_rsun, a_au):
    return rstar_rsun ** 2 * (teff / TEFF_SUN) ** 4 / a_au ** 2


# Checks: each returns (observed, predicted, rel_sigma_or_None) or None -----

def chk_kepler(r):
    if (r.get("discoverymethod") or "") in ("Microlensing", "Imaging"):
        return None
    if (r.get("cb_flag") or "") == "1":  # circumbinary: the host mass is the binary's
        return None
    p, a, m = value(r, "pl_orbper"), value(r, "pl_orbsmax"), value(r, "st_mass")
    if None in (p, a, m):
        return None
    pred = kepler_a_au(p, m, value(r, "pl_bmasse"))
    s = combine((rel_sigma(r, "pl_orbsmax"), 1.0), (rel_sigma(r, "st_mass"), 1 / 3), (rel_sigma(r, "pl_orbper"), 2 / 3))
    return a, pred, s


def chk_density(r):
    if (r.get("pl_bmassprov") or "") != "Mass":
        return None
    m, rad, d = value(r, "pl_bmasse"), value(r, "pl_rade"), value(r, "pl_dens")
    if None in (m, rad, d):
        return None
    s = combine((rel_sigma(r, "pl_dens"), 1.0), (rel_sigma(r, "pl_bmasse"), 1.0), (rel_sigma(r, "pl_rade"), 3.0))
    return d, bulk_density(m, rad), s


def chk_ratdor(r):
    if not circularish(r):
        return None
    q, a, rs = value(r, "pl_ratdor"), value(r, "pl_orbsmax"), value(r, "st_rad")
    if None in (q, a, rs):
        return None
    s = combine((rel_sigma(r, "pl_ratdor"), 1.0), (rel_sigma(r, "pl_orbsmax"), 1.0), (rel_sigma(r, "st_rad"), 1.0))
    return q, a * AU_RSUN / rs, s


def chk_ratror(r):
    k, rp, rs = value(r, "pl_ratror"), value(r, "pl_rade"), value(r, "st_rad")
    if None in (k, rp, rs):
        return None
    s = combine((rel_sigma(r, "pl_ratror"), 1.0), (rel_sigma(r, "pl_rade"), 1.0), (rel_sigma(r, "st_rad"), 1.0))
    return k, rp * REARTH_RSUN / rs, s


def chk_depth(r):
    d, k = value(r, "pl_trandep"), value(r, "pl_ratror")
    if None in (d, k):
        return None
    return d, 100.0 * k ** 2, None  # limb darkening and grazing: no sigma test


def chk_rhostar_transit(r):
    if not circularish(r):
        return None
    q, p, m, rs = value(r, "pl_ratdor"), value(r, "pl_orbper"), value(r, "st_mass"), value(r, "st_rad")
    if None in (q, p, m, rs):
        return None
    s = combine((rel_sigma(r, "pl_ratdor"), 3.0), (rel_sigma(r, "st_mass"), 1.0), (rel_sigma(r, "st_rad"), 3.0))
    return star_density_from_transit(q, p), star_density(m, rs), s


def chk_stdens(r):
    d, m, rs = value(r, "st_dens"), value(r, "st_mass"), value(r, "st_rad")
    if None in (d, m, rs):
        return None
    s = combine((rel_sigma(r, "st_dens"), 1.0), (rel_sigma(r, "st_mass"), 1.0), (rel_sigma(r, "st_rad"), 3.0))
    return d, star_density(m, rs), s


def chk_logg(r):
    g, m, rs = value(r, "st_logg"), value(r, "st_mass"), value(r, "st_rad")
    if None in (g, m, rs):
        return None
    e1, e2 = num(r, "st_loggerr1"), num(r, "st_loggerr2")
    sg = (abs(e1) + abs(e2)) / 2 if None not in (e1, e2) else None
    sm, sr = rel_sigma(r, "st_mass"), rel_sigma(r, "st_rad")
    s = None
    if None not in (sg, sm, sr):
        # in natural-log units of g, to match ln(ratio)
        s = math.sqrt((sg * math.log(10)) ** 2 + sm ** 2 + (2 * sr) ** 2)
    return 10 ** g, 10 ** logg(m, rs), s


def chk_insol(r):
    f, t, rs, a = value(r, "pl_insol"), value(r, "st_teff"), value(r, "st_rad"), value(r, "pl_orbsmax")
    if None in (f, t, rs, a):
        return None
    s = combine((rel_sigma(r, "pl_insol"), 1.0), (rel_sigma(r, "st_teff"), 4.0), (rel_sigma(r, "st_rad"), 2.0), (rel_sigma(r, "pl_orbsmax"), 2.0))
    return f, insolation(t, rs, a), s


# name, function, relative tolerance (on the ratio), z threshold
CHECKS = [
    ("kepler3_a", chk_kepler, 0.10, 3.0),
    ("bulk_density", chk_density, 0.10, 3.0),
    ("a_over_rstar", chk_ratdor, 0.10, 3.0),
    ("rp_over_rstar", chk_ratror, 0.05, 3.0),
    ("depth_vs_k2", chk_depth, None, None),
    ("rhostar_transit_vs_MR", chk_rhostar_transit, 0.25, 3.0),
    ("st_dens_vs_MR", chk_stdens, 0.10, 3.0),
    ("logg_vs_MR", chk_logg, 0.26, 3.0),   # 0.1 dex
    ("insolation", chk_insol, 0.20, 3.0),
]


def evaluate(row, name, fn, tol, zmin):
    res = fn(row)
    if res is None:
        return None
    obs, pred, s = res
    if pred <= 0 or obs <= 0:
        return None
    ratio = obs / pred
    lr = math.log(ratio)
    z = lr / s if s else None
    if tol is None:  # depth: limb darkening raises depth up to ~1.3 k^2, grazing lowers it
        flagged = not (0.6 <= ratio <= 1.6)
    else:
        flagged = abs(lr) > math.log(1 + tol) and (z is None or abs(z) >= zmin)
    gross = not (0.5 <= ratio <= 2.0)
    return {"check": name, "observed": obs, "predicted": pred, "ratio": ratio,
            "z": z, "flagged": flagged, "gross": gross, "unit_slip": unit_slip(ratio, name) if gross else ""}


def audit(rows, table, groups=None):
    """Test every row. If groups is a dict, it collects ln(ratio) and the row
    itself for every tested row under (table, check, source reference), for
    systematics() and unit_group_rows()."""
    stats = {name: {"tested": 0, "flagged": 0, "gross": 0, "unit_slip": 0,
                    "flagged_same_ref": 0, "flagged_default": 0} for name, *_ in CHECKS}
    flags = []
    for r in rows:
        same_ref = None
        if table == "ps":
            same_ref = (r.get("pl_refname") or "") == (r.get("st_refname") or "")
        for name, fn, tol, zmin in CHECKS:
            try:
                ev = evaluate(r, name, fn, tol, zmin)
            except (ValueError, ZeroDivisionError, OverflowError):
                ev = None
            if ev is None:
                continue
            st = stats[name]
            st["tested"] += 1
            src = source_ref(r, table, name)
            if groups is not None and src:
                g = groups.setdefault((table, name, src), {"lr": [], "flagged": 0, "rows": []})
                g["lr"].append(math.log(ev["ratio"]))
                g["flagged"] += int(ev["flagged"])
                g["rows"].append({"pl_name": r.get("pl_name", ""), "hostname": r.get("hostname", ""),
                                  "default_flag": r.get("default_flag", "") if table == "ps" else "composite",
                                  "observed": ev["observed"], "predicted": ev["predicted"], "ratio": ev["ratio"],
                                  "st_mass": r.get("st_mass", ""), "st_rad": r.get("st_rad", ""),
                                  "bibcode": ref_bibcode(source_html(r, table, name))})
            if not ev["flagged"]:
                continue
            st["flagged"] += 1
            st["gross"] += int(ev["gross"])
            st["unit_slip"] += int(bool(ev["unit_slip"]))
            st["flagged_same_ref"] += int(bool(same_ref))
            st["flagged_default"] += int(r.get("default_flag") == "1")
            flags.append({
                "table": table, "pl_name": r.get("pl_name", ""), "hostname": r.get("hostname", ""),
                "check": name, "observed": f"{ev['observed']:.6g}", "predicted": f"{ev['predicted']:.6g}",
                "ratio": f"{ev['ratio']:.4g}", "z": "" if ev["z"] is None else f"{ev['z']:.2f}",
                "gross": int(ev["gross"]), "likely_unit_slip": ev["unit_slip"],
                "default_flag": r.get("default_flag", ""), "same_ref": "" if same_ref is None else int(same_ref),
                "source_ref": src, "pipeline": int(is_pipeline(src)),
                "pl_ref": ref_text(r.get("pl_refname", "")), "st_ref": ref_text(r.get("st_refname", "")),
                "discoverymethod": r.get("discoverymethod", ""), "controversial": r.get("pl_controv_flag", ""),
            })
    return stats, flags


def systematics(groups):
    """References whose rows share one offset for a check: median ratio at
    least 10% from 1, with most rows close to that median."""
    out = []
    for (table, check, ref), g in groups.items():
        lr = g["lr"]
        if len(lr) < SYS_MIN_ROWS:
            continue
        med = statistics.median(lr)
        if abs(med) <= math.log(1 + SYS_MIN_OFFSET):
            continue
        near = sum(1 for x in lr if abs(x - med) <= math.log(1 + SYS_MIN_OFFSET)) / len(lr)
        if near < SYS_COHERENT:
            continue
        ratio = math.exp(med)
        label = unit_slip(ratio, check)
        corrected = f"{unit_fixed(ratio, label):.4g}" if label else ""
        out.append({"table": table, "check": check, "reference": ref, "pipeline": int(is_pipeline(ref)),
                    "rows": len(lr), "median_ratio": f"{ratio:.4g}", "within_10pct_of_median": f"{near:.3f}",
                    "flagged_rows": g["flagged"], "unit_pattern": label, "median_after_unit_fix": corrected})
    out.sort(key=lambda d: (not d["unit_pattern"], -d["rows"] * abs(math.log(float(d["median_ratio"])))))
    return out


UNIT_GROUP_FIELDS = ["reference", "check", "unit_pattern", "table", "pl_name", "hostname", "default_flag",
                     "bibcode", "st_mass", "st_rad", "observed", "predicted", "ratio", "ratio_after_fix",
                     "fix_within_10pct"]


def unit_group_rows(groups, sys_rows):
    """Every row, in both tables, of each (check, reference) whose shared offset
    matches a unit factor in either table. This also lists composite (default)
    values from that reference when they are too few to form a group alone."""
    patterns = {}
    for s in sys_rows:
        if s["unit_pattern"] and not s["pipeline"]:
            patterns.setdefault((s["check"], s["reference"]), s["unit_pattern"])
    out = []
    for (table, check, ref), g in groups.items():
        label = patterns.get((check, ref))
        if not label:
            continue
        for r in g["rows"]:
            fixed = unit_fixed(r["ratio"], label)
            out.append({"reference": ref, "check": check, "unit_pattern": label, "table": table,
                        "pl_name": r["pl_name"], "hostname": r["hostname"], "default_flag": r["default_flag"],
                        "bibcode": r["bibcode"], "st_mass": r["st_mass"], "st_rad": r["st_rad"],
                        "observed": f"{r['observed']:.6g}", "predicted": f"{r['predicted']:.6g}",
                        "ratio": f"{r['ratio']:.4g}", "ratio_after_fix": f"{fixed:.4g}",
                        "fix_within_10pct": int(abs(math.log(fixed)) <= math.log(1 + SYS_MIN_OFFSET))})
    out.sort(key=lambda d: (d["reference"], d["check"], d["table"], d["pl_name"]))
    return out


def unit_group_summary(rows):
    """Per (reference, check): rows in ps, ps default rows, composite rows, share fixed, bibcodes."""
    out = {}
    for r in rows:
        s = out.setdefault((r["reference"], r["check"]), {"reference": r["reference"], "check": r["check"],
                                                          "unit_pattern": r["unit_pattern"], "ps_rows": 0,
                                                          "ps_default_rows": 0, "composite_rows": 0,
                                                          "fixed_within_10pct": 0, "bibcodes": set()})
        if r["table"] == "ps":
            s["ps_rows"] += 1
            s["ps_default_rows"] += int(r["default_flag"] == "1")
        else:
            s["composite_rows"] += 1
        s["fixed_within_10pct"] += r["fix_within_10pct"]
        if r["bibcode"]:
            s["bibcodes"].add(r["bibcode"])
    res = []
    for s in out.values():
        s["bibcodes"] = " ".join(sorted(s["bibcodes"]))
        res.append(s)
    res.sort(key=lambda d: -(d["ps_rows"] + d["composite_rows"]))
    return res


def by_reference(rows, flags):
    total, flagged = {}, {}
    for r in rows:
        ref = ref_text(r.get("pl_refname", ""))
        total[ref] = total.get(ref, 0) + 1
    for f in flags:
        if f["table"] == "ps":
            flagged[f["pl_ref"]] = flagged.get(f["pl_ref"], 0) + 1
    out = [{"reference": k, "ps_rows": v, "flags": flagged.get(k, 0),
            "flags_per_row": round(flagged.get(k, 0) / v, 3), "pipeline": int(is_pipeline(k))}
           for k, v in total.items()]
    out.sort(key=lambda d: (-d["flags"], d["reference"]))
    return out


def strength(f):
    try:
        return abs(float(f["z"])) if f["z"] else abs(math.log(float(f["ratio"]))) * 10
    except ValueError:
        return 0.0


def write_report(path, meta, stats_all, flags, sys_rows, ug_summary=()):
    lines = ["# NASA Exoplanet Archive self-consistency audit (exo_audit " + VERSION + ")", "",
             f"Downloaded {meta['downloaded_utc']} from {TAP}. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. "
             "Each flag is a candidate for checking against the source paper, not a confirmed error.", ""]
    lines += ["## Systematic offsets by reference", "",
              f"A reference is listed when at least {SYS_MIN_ROWS} of its rows were tested, their median ratio "
              f"(observed / predicted) is more than {int(SYS_MIN_OFFSET * 100)}% from 1, and at least half of them lie "
              "within 10% of that median. Pipeline catalogs (Kepler KOI tables) are marked: their a/R* and "
              "stellar densities are free transit-fit parameters, so offsets there are expected physics, not slips.", "",
              "| table | check | reference | pipeline | rows | median ratio | within 10% | unit pattern | median after fix |",
              "|---|---|---|---|---|---|---|---|---|"]
    for s in sys_rows[:60]:
        lines.append(f"| {s['table']} | {s['check']} | {s['reference']} | {'yes' if s['pipeline'] else ''} | {s['rows']} | "
                     f"{s['median_ratio']} | {s['within_10pct_of_median']} | {s['unit_pattern']} | {s['median_after_unit_fix']} |")
    lines.append("")
    if ug_summary:
        lines += ["## References whose shared offset matches a unit factor (all their rows, both tables)", "",
                  "Row-by-row evidence is in `unit_groups.csv`. `composite rows` are values the composite table "
                  "(pscomppars) takes from that reference.", "",
                  "| reference | check | unit pattern | ps rows | ps default rows | composite rows | rows within 10% after fix | bibcodes |",
                  "|---|---|---|---|---|---|---|---|"]
        for s in ug_summary:
            lines.append(f"| {s['reference']} | {s['check']} | {s['unit_pattern']} | {s['ps_rows']} | {s['ps_default_rows']} | "
                         f"{s['composite_rows']} | {s['fixed_within_10pct']} | {s['bibcodes']} |")
        lines.append("")
    for table, stats in stats_all.items():
        same = "flagged, same ref for planet and star" if table == "ps" else "same ref (n/a)"
        lines += [f"## Table `{table}` ({meta['rows'][table]} rows)", "",
                  f"| check | rows tested | flagged | gross (x2) | unit-slip pattern | {same} | flagged default rows |",
                  "|---|---|---|---|---|---|---|"]
        for name, s in stats.items():
            if table == "ps":
                lines.append(f"| {name} | {s['tested']} | {s['flagged']} | {s['gross']} | {s['unit_slip']} | {s['flagged_same_ref']} | {s['flagged_default']} |")
            else:
                lines.append(f"| {name} | {s['tested']} | {s['flagged']} | {s['gross']} | {s['unit_slip']} | n/a | n/a |")
        lines.append("")
    slips = [f for f in flags if f["likely_unit_slip"] and not f["pipeline"]]
    lines += ["## Likely unit slips in single rows, excluding pipeline catalogs (first 60)", "",
              "| table | planet | check | observed | predicted | ratio | pattern | source |", "|---|---|---|---|---|---|---|---|"]
    for f in slips[:60]:
        lines.append(f"| {f['table']} | {f['pl_name']} | {f['check']} | {f['observed']} | {f['predicted']} | {f['ratio']} | {f['likely_unit_slip']} | {f['source_ref']} |")
    strong = sorted([f for f in flags if f["table"] == "ps" and f["same_ref"] == 1 and f["default_flag"] == "1"
                     and not f["pipeline"]], key=strength, reverse=True)
    lines += ["", "## Strongest flags in default rows whose planet and star parameters share one reference, excluding pipeline catalogs (first 60)", "",
              "| planet | check | observed | predicted | ratio | z | reference |", "|---|---|---|---|---|---|---|"]
    for f in strong[:60]:
        lines.append(f"| {f['pl_name']} | {f['check']} | {f['observed']} | {f['predicted']} | {f['ratio']} | {f['z']} | {f['pl_ref']} |")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def merge_reflinks(rows, text):
    links = {r.get("pl_name", ""): r for r in csv.DictReader(io.StringIO(text))}
    n = 0
    for r in rows:
        extra = links.get(r.get("pl_name", ""))
        if extra:
            n += 1
            for k in REFLINKS:
                r[k] = extra.get(k, "")
    return n


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    ap.add_argument("--data-dir", default="")
    ap.add_argument("--offline", default="", help="audit this local ps-format CSV instead of downloading")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    meta = {"version": VERSION, "downloaded_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "queries": {}, "rows": {}, "source": {}}
    stats_all, all_flags, ps_rows, groups = {}, [], [], {}
    tables = ["ps", "pscomppars"] if not args.offline else ["ps"]
    for table in tables:
        if args.offline:
            with open(args.offline, encoding="utf-8") as f:
                text, how = f.read(), "offline"
        else:
            try:
                text, how = fetch(table_query(table), table, args.data_dir or None)
            except Exception as exc:  # network or TAP error: record and continue
                meta["source"][table] = f"error: {exc}"
                print(f"{table}: fetch failed: {exc}", file=sys.stderr)
                continue
            meta["queries"][table] = tap_url(table_query(table))
        rows = list(csv.DictReader(io.StringIO(text)))
        if rows and "pl_name" not in rows[0]:
            meta["source"][table] = "error: unexpected response: " + text[:300]
            continue
        meta["source"][table] = how
        meta["rows"][table] = len(rows)
        if table == "pscomppars":
            try:
                ltext, _ = fetch(reflink_query(), "pscomppars-reflinks", args.data_dir or None)
                meta["reflink_rows_merged"] = merge_reflinks(rows, ltext)
                meta["queries"]["pscomppars_reflinks"] = tap_url(reflink_query())
            except Exception as exc:
                meta["reflink_rows_merged"] = f"error: {exc}"
                print(f"pscomppars reflinks: fetch failed: {exc}", file=sys.stderr)
        stats, flags = audit(rows, table, groups)
        stats_all[table] = stats
        all_flags += flags
        if table == "ps":
            ps_rows = rows
        print(f"{table}: {len(rows)} rows, {len(flags)} flags")
    if not stats_all:
        print("no table could be audited", file=sys.stderr)
        return 2
    fields = ["table", "pl_name", "hostname", "check", "observed", "predicted", "ratio", "z", "gross",
              "likely_unit_slip", "default_flag", "same_ref", "source_ref", "pipeline", "pl_ref", "st_ref",
              "discoverymethod", "controversial"]
    with open(os.path.join(args.out_dir, "flags.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(all_flags)
    sys_rows = systematics(groups)
    with open(os.path.join(args.out_dir, "systematics.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["table", "check", "reference", "pipeline", "rows", "median_ratio",
                                          "within_10pct_of_median", "flagged_rows", "unit_pattern", "median_after_unit_fix"])
        w.writeheader()
        w.writerows(sys_rows)
    ug_rows = unit_group_rows(groups, sys_rows)
    with open(os.path.join(args.out_dir, "unit_groups.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=UNIT_GROUP_FIELDS)
        w.writeheader()
        w.writerows(ug_rows)
    ug_summary = unit_group_summary(ug_rows)
    if ps_rows:
        refs = by_reference(ps_rows, all_flags)
        with open(os.path.join(args.out_dir, "by_reference.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["reference", "ps_rows", "flags", "flags_per_row", "pipeline"])
            w.writeheader()
            w.writerows(refs)
    summary = {"meta": meta, "stats": stats_all, "flags_total": len(all_flags),
               "systematics": len(sys_rows), "systematics_with_unit_pattern": sum(1 for s in sys_rows if s["unit_pattern"]),
               "unit_groups": ug_summary}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    write_report(os.path.join(args.out_dir, "report.md"), meta, stats_all, all_flags, sys_rows, ug_summary)
    print(json.dumps({"rows": meta["rows"], "flags_total": len(all_flags), "unit_groups": ug_summary,
                      "systematics_top": sys_rows[:25]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
