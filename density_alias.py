"""density_alias: which of two whole-ratio periods does the host star's own density allow?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

A transit's shape fixes a/R*, the impact parameter b and Rp/R*; with the period P that gives the star's
mean density, rho = 3 pi (a/R*)^3 / (G P^2) (Seager & Mallen-Ornelas 2003). Fitting the same transits
at P' instead of P keeps the duration and so changes a/R*; for a/R* >> 1 the fitted density scales as
P'/P. A star whose density is known independently (here Berger et al. 2020, Gaia-Kepler isochrone
masses and radii, J/AJ/159/280) can therefore say which of two periods related by a whole number k is
physical. The idea is old (it is how duo-transit aliases are ranked); this script applies it to the
246 DR25 KOIs whose matched TCE has a whole-multiple period (dv_alias 0.1.0 census), and calibrates it
on confirmed planets whose period is not in question.

Inputs: koi_srho (+err1/err2), koi_dor, koi_impact, koi_ror, koi_period from q1_q17_dr25_koi.

For each period X: r_X = rho_fit(X) / rho_star. Eccentricity e <= 0.1 can move r by up to 1.35x either
way, so only the part of |ln r_X| beyond ln 1.35 counts, in units of the combined log error (the fit's
error on the side toward the star, and the star's): t_X.
  favors_koi    t_koi <= 1 and t_alt >= 2
  favors_alt    t_alt <= 1 and t_koi >= 2
  both_tense    both >= 2 (eclipsing binary, blend, wrong star, or high e)
  ambiguous     anything else
  unconstrained fit density spans more than 4x (1 sigma), or a needed value is missing
A verdict is evidence about the period, not a period correction.

Usage: python density_alias.py --out-dir /out [--census census.csv]
"""
import argparse
import csv
import datetime as dt
import json
import math
import os
import statistics
import sys
import time
import urllib.parse
import urllib.request

VERSION = "0.1.0"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
VIZIER = ("https://vizier.cds.unistra.fr/viz-bin/asu-tsv", "https://vizier.cfa.harvard.edu/viz-bin/asu-tsv")
CENSUS_URL = ("https://raw.githubusercontent.com/munimtechnologies/exoplanet-archive-audit/main/"
              "results/2026-10-17-dv-alias-0.1.0/census.csv")
UA = f"density-alias/{VERSION} (Munim, Inc.; mv2@munimtech.com)"
G_CGS = 6.674e-8
RHO_SUN = 1.4098  # g/cm^3
DAY = 86400.0
BAND = math.log(1.35)  # e <= 0.1
MAX_SPAN = math.log(4.0)
BATCH = 50

DR25 = ("select kepoi_name, kepid, koi_period, koi_dor, koi_srho, koi_srho_err1, koi_srho_err2, koi_impact, "
        "koi_ror, koi_smass, koi_smass_err1, koi_smass_err2, koi_srad, koi_srad_err1, koi_srad_err2 "
        "from q1_q17_dr25_koi")
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


def rho_star(m, r):
    """Mean density in g/cm^3 for mass and radius in solar units."""
    return RHO_SUN * m / r ** 3


def sigma_ln_star(m, em, r, er):
    return math.hypot(em / m, 3 * er / r)


def rho_from_dor(dor, p_days):
    return 3 * math.pi * dor ** 3 / (G_CGS * (p_days * DAY) ** 2)


def period_scale(dor, b, ror, p, p_new):
    """Factor on the fitted density when the same transit (duration, b, Rp/R*) is fit at p_new instead of
    p, circular orbit. None if the geometry has no solution."""
    if not dor or b is None or ror is None or not p or not p_new or dor <= b:
        return None
    l2 = (1 + ror) ** 2 - b ** 2
    if l2 <= 0:
        return None
    s = math.sqrt(l2) / math.sqrt(dor ** 2 - b ** 2)
    if s >= 1:
        return None
    ang = math.asin(s) * p / p_new
    if ang >= math.pi / 2:
        return None
    dor_new = math.sqrt(b ** 2 + l2 / math.sin(ang) ** 2)
    return (dor_new / dor) ** 3 * (p / p_new) ** 2


def fit_sigmas(rho, e1, e2):
    """(sigma_up, sigma_dn) of ln rho_fit; either may be None."""
    if not rho or rho <= 0:
        return None, None
    up = math.log((rho + e1) / rho) if e1 is not None and e1 > 0 else None
    dn = math.log(rho / (rho + e2)) if e2 is not None and e2 < 0 and rho + e2 > 0 else None
    return up, dn


def tension(ratio, s_up, s_dn, s_star, band=BAND):
    d = math.log(ratio)
    s_fit = s_dn if d > 0 else s_up
    if s_fit is None:
        return None
    return max(0.0, abs(d) - band) / math.hypot(s_fit, s_star)


def verdict(t_koi, t_alt, s_up, s_dn):
    if t_koi is None or t_alt is None or s_up is None or s_dn is None or s_up + s_dn > MAX_SPAN:
        return "unconstrained"
    if t_koi <= 1 and t_alt >= 2:
        return "favors_koi"
    if t_alt <= 1 and t_koi >= 2:
        return "favors_alt"
    if t_koi >= 2 and t_alt >= 2:
        return "both_tense"
    return "ambiguous"


def parse_vizier_tsv(text):
    """{kic: {col: value}} from a VizieR asu-tsv response (comments, header, units line, dashes line)."""
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    if not lines:
        return {}
    head = [h.strip() for h in lines[0].split("\t")]
    out = {}
    for ln in lines[1:]:
        f = [x.strip() for x in ln.split("\t")]
        if not f or not f[0].isdigit():
            continue  # units and dashes lines
        out[f[0]] = dict(zip(head, f))
    return out


def berger(kics, errors):
    """Berger et al. 2020 table2 rows for the given KICs."""
    kics = sorted({str(int(k)) for k in kics if k})
    out = {}
    for i in range(0, len(kics), BATCH):
        q = urllib.parse.urlencode({"-source": "J/AJ/159/280/table2", "-out": "KIC,Mass,E_Mass,e_Mass,Rad,E_Rad,e_Rad",
                                    "-out.max": "unlimited", "KIC": ",".join(kics[i:i + BATCH])})
        for host in VIZIER:
            try:
                out.update(parse_vizier_tsv(http_text(host + "?" + q, timeout=120)))
                break
            except Exception as exc:
                errors.append(f"VizieR {host} batch {i // BATCH}: {type(exc).__name__}: {exc}"[:300])
        time.sleep(0.5)
    return out


def star_for(kic, fit, ber):
    """(rho, sigma_ln, source) from Berger 2020 if present, else the DR25 KOI table's stellar values."""
    b = ber.get(str(int(kic))) if kic else None
    if b:
        m, r = num(b, "Mass"), num(b, "Rad")
        em = (abs(num(b, "E_Mass") or 0) + abs(num(b, "e_Mass") or 0)) / 2
        er = (abs(num(b, "E_Rad") or 0) + abs(num(b, "e_Rad") or 0)) / 2
        if m and r:
            return rho_star(m, r), sigma_ln_star(m, em, r, er), "berger2020"
    m, r = num(fit, "koi_smass"), num(fit, "koi_srad")
    if m and r:
        em = (abs(num(fit, "koi_smass_err1") or 0) + abs(num(fit, "koi_smass_err2") or 0)) / 2
        er = (abs(num(fit, "koi_srad_err1") or 0) + abs(num(fit, "koi_srad_err2") or 0)) / 2
        return rho_star(m, r), sigma_ln_star(m, em, r, er), "dr25"
    return None, None, "none"


def assess(fit, p_alt, star):
    """Density verdict for one KOI fit against an alternative period."""
    rho_s, s_star, src = star
    p = num(fit, "koi_period")
    rho = num(fit, "koi_srho")
    out = {"stellar_src": src, "rho_star": rho_s, "rho_fit": rho, "p_alt": p_alt}
    dor = num(fit, "koi_dor")
    if p and dor:
        out["dor_check"] = rho_from_dor(dor, p) / rho if rho else None
    scale = period_scale(dor, num(fit, "koi_impact"), num(fit, "koi_ror"), p, p_alt)
    s_up, s_dn = fit_sigmas(rho, num(fit, "koi_srho_err1"), num(fit, "koi_srho_err2"))
    out.update({"scale_alt": scale, "s_up": s_up, "s_dn": s_dn, "s_star": s_star})
    if not rho_s or not rho or scale is None or s_star is None:
        out.update({"r_koi": None, "r_alt": None, "t_koi": None, "t_alt": None, "density_verdict": "unconstrained"})
        return out
    r_koi, r_alt = rho / rho_s, rho * scale / rho_s
    t_koi, t_alt = tension(r_koi, s_up, s_dn, s_star), tension(r_alt, s_up, s_dn, s_star)
    out.update({"r_koi": r_koi, "r_alt": r_alt, "t_koi": t_koi, "t_alt": t_alt,
                "density_verdict": verdict(t_koi, t_alt, s_up, s_dn)})
    return out


FIELDS = ["kepoi_name", "kepid", "kepler_name", "koi_disposition", "kind", "k", "koi_period", "p_alt", "verdict",
          "stellar_src", "rho_star", "rho_fit", "dor_check", "scale_alt", "s_up", "s_dn", "s_star", "r_koi", "r_alt",
          "t_koi", "t_alt", "density_verdict"]


def fmt(x, nd=3):
    if x is None or x == "":
        return ""
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def read_census(src):
    text = http_text(src) if src.startswith("http") else open(src, encoding="utf-8").read()
    return list(csv.DictReader(text.splitlines()))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--census", default=CENSUS_URL)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    errors = []
    census = read_census(args.census)
    fits = {r["kepoi_name"]: r for r in tap_rows(DR25)}
    cum = {r["kepoi_name"]: r for r in tap_rows(CUMULATIVE)}
    in_census = {r["kepoi_name"] for r in census}
    calib_names = [n for n, r in cum.items() if r.get("koi_disposition") == "CONFIRMED" and n in fits
                   and n not in in_census]
    ber = berger([fits[n]["kepid"] for n in calib_names] + [r["kepid"] for r in census], errors)

    rows = []
    for c in census:
        fit = fits.get(c["kepoi_name"])
        if not fit:
            continue
        a = assess(fit, num(c, "tce_period"), star_for(c["kepid"], fit, ber))
        rows.append({**{k: c.get(k, "") for k in ("kepoi_name", "kepid", "kepler_name", "koi_disposition", "kind", "k",
                                                  "verdict")}, "koi_period": num(c, "koi_period"), **a})
    rows.sort(key=lambda r: (r["kind"], r["density_verdict"], r["kepoi_name"]))
    with open(os.path.join(args.out_dir, "density.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # Calibration: confirmed planets outside the census, tested against 2P and P/2 as if those were aliases.
    calib = []
    for n in calib_names:
        fit = fits[n]
        star = star_for(fit["kepid"], fit, ber)
        if star[2] != "berger2020":
            continue
        p = num(fit, "koi_period")
        lo, hi = assess(fit, p / 2 if p else None, star), assess(fit, 2 * p if p else None, star)
        calib.append({"kepoi_name": n, "kepler_name": cum[n].get("kepler_name", ""), "koi_period": p,
                      "r_koi": lo["r_koi"], "t_koi": lo["t_koi"], "verdict_half": lo["density_verdict"],
                      "verdict_double": hi["density_verdict"], "s_up": lo["s_up"], "s_dn": lo["s_dn"],
                      "s_star": lo["s_star"]})
    with open(os.path.join(args.out_dir, "calibration.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(calib[0]) if calib else ["kepoi_name"])
        w.writeheader()
        w.writerows(calib)
    cons = [c for c in calib if c["verdict_half"] != "unconstrained" and c["t_koi"] is not None]
    lnr = sorted(math.log(c["r_koi"]) for c in cons)
    med = statistics.median(lnr) if lnr else None
    mad = statistics.median(abs(x - med) for x in lnr) * 1.4826 if lnr else None
    tk = [c["t_koi"] for c in cons]
    k1301 = next((r for r in rows if r["kepoi_name"] == "K02643.01"), None)
    t1301 = k1301["t_koi"] if k1301 else None
    calib_stats = {
        "confirmed_outside_census": len(calib_names), "berger_matched": len(calib), "constrained": len(cons),
        "median_ln_r": med, "mad_sigma_ln_r": mad,
        "frac_t_koi_ge_2": sum(t >= 2 for t in tk) / len(tk) if tk else None,
        "frac_t_koi_ge_kepler1301b": (sum(t >= t1301 for t in tk) / len(tk)) if tk and t1301 is not None else None,
        "false_favors_alt_half": sum(c["verdict_half"] == "favors_alt" for c in cons),
        "false_favors_alt_double": sum(c["verdict_double"] == "favors_alt" for c in cons),
        "false_favors_alt_either": sum("favors_alt" in (c["verdict_half"], c["verdict_double"]) for c in cons),
        "correct_favors_koi_half": sum(c["verdict_half"] == "favors_koi" for c in cons),
        "correct_favors_koi_double": sum(c["verdict_double"] == "favors_koi" for c in cons),
    }

    counts = {}
    for r in rows:
        key = f"{r['kind']}|{r['verdict']}|{r['koi_disposition']}|{r['density_verdict']}"
        counts[key] = counts.get(key, 0) + 1
    stats = {"version": VERSION, "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "census_rows": len(census), "assessed": len(rows),
             "berger_rows": sum(r["stellar_src"] == "berger2020" for r in rows),
             "dor_check_off_5pct": sum(1 for r in rows if r.get("dor_check") and abs(r["dor_check"] - 1) > 0.05),
             "calibration": calib_stats, "counts": dict(sorted(counts.items())), "errors": errors}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

    cols = ["kepoi_name", "kepler_name", "koi_disposition", "kind", "k", "koi_period", "p_alt", "verdict",
            "stellar_src", "rho_star", "r_koi", "r_alt", "t_koi", "t_alt", "density_verdict"]
    lines = [f"# density-alias {VERSION}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0.",
             "", f"{len(rows)} of {len(census)} dv_alias census rows assessed; {stats['berger_rows']} with Berger et al. "
             "2020 stellar densities. A verdict is evidence about the period, not a period correction.", "",
             "## Calibration (confirmed planets outside the census, tested against 2P and P/2)", ""]
    lines += [f"- {k}: {fmt(v, 4)}" for k, v in calib_stats.items()]
    lines += ["", "## Counts (kind | dv_alias verdict | disposition | density verdict)", ""]
    lines += [f"- {k}: {v}" for k, v in stats["counts"].items()]
    pick = [r for r in rows if r["koi_disposition"] in ("CONFIRMED", "CANDIDATE")]
    lines += ["", "## Every confirmed or candidate row", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(fmt(r.get(c)) for c in cols) + " |" for r in pick]
    fa = [r for r in rows if r["density_verdict"] == "favors_alt"]
    lines += ["", "## Every row whose density favours the other period", "", "| " + " | ".join(cols) + " |",
              "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(fmt(r.get(c)) for c in cols) + " |" for r in fa]
    if errors:
        lines += ["", "## Errors", ""] + [f"- {e}" for e in errors[:50]]
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
