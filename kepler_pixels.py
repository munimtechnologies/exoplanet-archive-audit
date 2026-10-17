"""kepler_pixels: do a Kepler planet's dips at each part of its phase come from the same pixels?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library plus astropy for FITS.

Built for Kepler-1301 b (KOI-2643.01, KIC 6933567). The Archive lists 9.0823 d, but its DR25 TCE
is 4.541 d, and kepler_alias 0.2.0 found the half-phase dip 6.2 and 5.9 sigma deep in the two halves
of the mission (265 +- 20 ppm at the catalogued phase, 199 +- 23 ppm halfway). One Gaia DR3 source,
G = 19.95, sits 3.29" away (+2.69" east, -1.85" north of the G = 15.36 target). An eclipsing binary
there could make one of the two dips. This asks whether each dip comes from the target's pixels.

0.2.0 adds --period-mult: the ephemeris period is the catalogued one times this factor, so the
alternate events of a KOI suspected to orbit at twice its catalogued period (KOI-4893.01,
KOI-4711.01) fall in phase groups 0 and 0.5 and can be measured separately in the pixels.

0.3.0 adds --unmask: KOIs on the star that are left out of the mask, so a KOI whose transits fall on
a sibling's (koi_dupes 0.1.0: every 11th K02167.02 event is a Kepler-1129 c transit, every 7th
K01922.02 event a Kepler-1016 c transit) can be measured with and without the sibling's events, and the sibling itself can be
measured without the KOI's ephemeris masking its transits away.

0.4.0 adds between-quarter checks on the depth, because the quarter depths scatter more than their
formal fit errors allow (orphan-pixels-v1: by ~1.4-2.8 x, worst where a quarter holds one event): the
Birge ratio sqrt(chi2 / (n - 1)) of the quarter depths about the weighted mean, the depth error scaled
by max(1, Birge), the SNR and verdict with that error, and the unweighted mean of the quarter depths
with its standard error. Every 0.3.0 field is computed as before.

Method:
1. Kepler long-cadence target pixel files (FLUX, QUALITY = 0), one per quarter. Pixels finite in
   under 90 % of cadences are left out; cadences with any other pixel missing are dropped.
2. For each phase group (default 0, 0.5 and the null phases 0.25, 0.75 of the KOI ephemeris) and
   each event: difference image = mean out-of-transit frame (1 to 1 + max(2 dur, 0.25 d) from
   mid-event, both sides, >= 3 cadences each) minus mean in-transit frame (|dt| < dur / 2, >= 2
   cadences). Events are averaged per quarter, each with equal weight. Other KOIs are masked
   (except those given to --unmask).
3. The quarter's difference image D is fitted by least squares as a shifted copy of its mean
   out-of-transit image O: D ~ a O + b (-dO/dcol) + c (-dO/drow). a is the fractional depth and
   (b, c) / a the shift in pixels (first order in the shift). (b, c) go to arcsec east/north with
   the quarter's WCS, because the pixel grid turns each quarter.
4. Quarters are combined as ratios of weighted sums, offset = (sum w bE / sum w a, sum w bN / sum
   w a), w = 1 / var(a); errors by jackknife over quarters.
5. Calibration: the same fit on a synthetic D made by shifting O to the neighbour's position, so the
   expected offset if the dip came from the neighbour is measured through the same first-order
   estimator, not assumed.
Verdict per group (2 degrees of freedom, chi2 < 11.8 is "consistent", 99.73 %; the comparison with
the neighbour adds 15 % of the calibration offset in quadrature, since the shifted copy is smoother
than a real star image):
  no_signal    depth below 3 sigma (expected for the null phases);
  on_target    consistent with zero offset and not with the neighbour;
  neighbour    consistent with the neighbour and not with zero;
  unclear      otherwise.
verdict uses the formal depth error, verdict_scaled the Birge-scaled one (same offset tests).
A difference-image offset is evidence about where the light comes from, not a disposition.

Usage: python kepler_pixels.py --out-dir /out [--data-dir /data] [--koi K02643.01]
                               [--phases 0,0.5,0.25,0.75] [--neighbour 2.69,-1.85] [--period-mult 1]
                               [--unmask K02167.03,...]
"""
import argparse
import bisect
import csv
import datetime as dt
import json
import math
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request

VERSION = "0.4.0"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
MAST_TPF = "https://archive.stsci.edu/missions/kepler/target_pixel_files/{d4}/{d9}/"
UA = f"kepler-pixels/{VERSION} (Munim, Inc.; mv2@munimtech.com)"
CHI2_2DOF = 11.8
CAL_SYS = 0.15  # bilinear shifting smooths the calibration image (~8 % smaller offset for a 1.2 px PSF)
SIG_DEPTH = 3.0
MIN_VALID = 0.9


def http_bytes(url, timeout=600):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def tap_rows(query):
    text = http_bytes(TAP + "?" + urllib.parse.urlencode({"query": query, "format": "csv"}), 600).decode("utf-8")
    return list(csv.DictReader(text.splitlines()))


def num(row, key):
    v = (row.get(key) or "").strip()
    try:
        x = float(v)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def scaled_period(p, mult):
    """Ephemeris period: the catalogued period p times a positive whole factor mult (1 keeps it)."""
    if p is None or mult < 1 or mult != int(mult):
        raise ValueError(f"period {p} with multiplier {mult}: need a period and a whole factor >= 1")
    return p * int(mult)


def event_windows(times, p, t0, dur_h, mask=None):
    """[(n, in_idx, out_idx)] for each event n of (p, t0) with >= 2 in-transit cadences (|dt| < dur/2)
    and >= 3 out-of-transit cadences on each side (dur <= |dt| < dur + w, w = max(2 dur, 0.25 d));
    times sorted."""
    dur = dur_h / 24.0
    w = max(2 * dur, 0.25)
    out = []
    if not times:
        return out
    n0 = math.ceil((times[0] - dur - w - t0) / p)
    n1 = math.floor((times[-1] + dur + w - t0) / p)
    for n in range(n0, n1 + 1):
        tc = t0 + n * p
        i, j = bisect.bisect_left(times, tc - dur - w), bisect.bisect_right(times, tc + dur + w)
        inn, before, after = [], [], []
        for q in range(i, j):
            if mask and mask[q]:
                continue
            d = times[q] - tc
            if abs(d) < dur / 2:
                inn.append(q)
            elif dur <= abs(d) < dur + w:
                (before if d < 0 else after).append(q)
        if len(inn) >= 2 and len(before) >= 3 and len(after) >= 3:
            out.append((n, inn, before + after))
    return out


def mask_others(times, others):
    """True where a point falls within 0.75 durations of another KOI's transit; others = [(P, t0, dur_h)]."""
    mask = []
    for t in times:
        hit = False
        for p, t0, dur_h in others:
            if p and t0 is not None and dur_h:
                if abs(((t - t0 + p / 2) % p) - p / 2) < 0.75 * dur_h / 24.0:
                    hit = True
                    break
        mask.append(hit)
    return mask


def other_ephemerides(rows, koi, unmask=()):
    """[(P, t0, dur_h)] to mask: the star's KOI rows except koi itself and any named in unmask."""
    skip = {koi, *unmask}
    return [(num(r, "koi_period"), num(r, "koi_time0bk"), num(r, "koi_duration")) for r in rows
            if r["kepoi_name"] not in skip]


def mean_frame(frames, idx):
    s = [0.0] * len(frames[0])
    for q in idx:
        for k, v in enumerate(frames[q]):
            s[k] += v
    return [v / len(idx) for v in s]


def stack(frames, events):
    """(mean difference image out - in, mean out-of-transit image) over events [(n, in_idx, out_idx)],
    each event weighted equally."""
    npix = len(frames[0])
    d_img, o_img = [0.0] * npix, [0.0] * npix
    for _, inn, oot in events:
        fi, fo = mean_frame(frames, inn), mean_frame(frames, oot)
        for k in range(npix):
            d_img[k] += fo[k] - fi[k]
            o_img[k] += fo[k]
    m = len(events)
    return [v / m for v in d_img], [v / m for v in o_img]


def gradients(img, nrow, ncol, valid):
    """(d/dcol, d/drow) of a flat row-major image: central differences, one-sided next to an edge or an
    invalid pixel, 0 where neither neighbour is valid."""
    gx, gy = [0.0] * len(img), [0.0] * len(img)
    for r in range(nrow):
        for c in range(ncol):
            k = r * ncol + c
            if not valid[k]:
                continue
            for g, lo, hi in ((gx, (r, c - 1), (r, c + 1)), (gy, (r - 1, c), (r + 1, c))):
                ok_lo = 0 <= lo[0] < nrow and 0 <= lo[1] < ncol and valid[lo[0] * ncol + lo[1]]
                ok_hi = 0 <= hi[0] < nrow and 0 <= hi[1] < ncol and valid[hi[0] * ncol + hi[1]]
                v_lo = img[lo[0] * ncol + lo[1]] if ok_lo else img[k]
                v_hi = img[hi[0] * ncol + hi[1]] if ok_hi else img[k]
                span = (1 if ok_lo else 0) + (1 if ok_hi else 0)
                g[k] = (v_hi - v_lo) / span if span else 0.0
    return gx, gy


def invert(a):
    """Inverse of a small square matrix by Gauss-Jordan with partial pivoting, or None if singular."""
    n = len(a)
    m = [list(map(float, row)) + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(a)]
    scale = max(abs(a[i][i]) for i in range(n)) or 1.0
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12 * scale:
            return None
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        m[col] = [v / pv for v in m[col]]
        for r in range(n):
            if r != col and m[r][col]:
                f = m[r][col]
                m[r] = [v - f * w for v, w in zip(m[r], m[col])]
    return [row[n:] for row in m]


def lstsq(cols, y):
    """(coefficients, covariance scaled by the residual variance) for y ~ sum beta_i cols_i, or (None, None)."""
    n = len(cols)
    ata = [[sum(u * v for u, v in zip(cols[i], cols[j])) for j in range(n)] for i in range(n)]
    aty = [sum(u * v for u, v in zip(cols[i], y)) for i in range(n)]
    inv = invert(ata)
    if inv is None:
        return None, None
    beta = [sum(inv[i][j] * aty[j] for j in range(n)) for i in range(n)]
    res = [yk - sum(beta[i] * cols[i][k] for i in range(n)) for k, yk in enumerate(y)]
    s2 = sum(r * r for r in res) / max(1, len(y) - n)
    return beta, [[s2 * inv[i][j] for j in range(n)] for i in range(n)]


def fit_shift(d_img, o_img, nrow, ncol, valid):
    """(a, b, c, var_a): D ~ a O + b (-dO/dcol) + c (-dO/drow) over valid pixels, so a is the fractional
    depth and (b / a, c / a) the shift of D from O in (col, row) pixels; None if singular."""
    gx, gy = gradients(o_img, nrow, ncol, valid)
    idx = [k for k in range(len(o_img)) if valid[k]]
    cols = [[o_img[k] for k in idx], [-gx[k] for k in idx], [-gy[k] for k in idx]]
    beta, cov = lstsq(cols, [d_img[k] for k in idx])
    if beta is None:
        return None
    return beta[0], beta[1], beta[2], cov[0][0]


def shifted(img, nrow, ncol, drow, dcol):
    """img moved by (drow, dcol) pixels: the value at (r, c) is img at (r - drow, c - dcol), bilinear,
    clamped at the edges."""
    out = []
    for r in range(nrow):
        for c in range(ncol):
            y = min(max(r - drow, 0.0), nrow - 1.0)
            x = min(max(c - dcol, 0.0), ncol - 1.0)
            r0, c0 = int(math.floor(y)), int(math.floor(x))
            r1, c1 = min(r0 + 1, nrow - 1), min(c0 + 1, ncol - 1)
            fy, fx = y - r0, x - c0
            out.append((1 - fy) * (1 - fx) * img[r0 * ncol + c0] + (1 - fy) * fx * img[r0 * ncol + c1]
                       + fy * (1 - fx) * img[r1 * ncol + c0] + fy * fx * img[r1 * ncol + c1])
    return out


def to_sky(jac, dcol, drow):
    """(east, north) arcsec of a (col, row) pixel offset; jac = [[dE/dcol, dE/drow], [dN/dcol, dN/drow]]."""
    return jac[0][0] * dcol + jac[0][1] * drow, jac[1][0] * dcol + jac[1][1] * drow


def to_pix(jac, east, north):
    """(dcol, drow) of an (east, north) arcsec offset."""
    det = jac[0][0] * jac[1][1] - jac[0][1] * jac[1][0]
    return ((jac[1][1] * east - jac[0][1] * north) / det, (-jac[1][0] * east + jac[0][0] * north) / det)


def combine(rows):
    """(east, north) arcsec = (sum w bE / sum w a, sum w bN / sum w a) over rows (w, a, bE, bN)."""
    sa = sum(w * a for w, a, _, _ in rows)
    if not rows or sa == 0:
        return None
    return sum(w * e for w, _, e, _ in rows) / sa, sum(w * n for w, _, _, n in rows) / sa


def jackknife(rows):
    """(east, north, err_east, err_north) from combine() with leave-one-out errors, or None (< 3 rows)."""
    full = combine(rows)
    if full is None or len(rows) < 3:
        return None
    loo = [combine(rows[:i] + rows[i + 1:]) for i in range(len(rows))]
    if any(v is None for v in loo):
        return None
    n = len(loo)
    errs = []
    for axis in (0, 1):
        m = sum(v[axis] for v in loo) / n
        errs.append(math.sqrt((n - 1) / n * sum((v[axis] - m) ** 2 for v in loo)))
    return full[0], full[1], errs[0], errs[1]


def scatter(depths, variances):
    """(birge, mean, mean_err) of quarter depths with formal variances: birge = sqrt(chi2 / (n - 1)) about
    the weighted mean, mean and mean_err the unweighted mean and its standard error; None (< 3 quarters)."""
    n = len(depths)
    if n < 3:
        return None
    ws = [1 / v for v in variances]
    wmean = sum(w * a for w, a in zip(ws, depths)) / sum(ws)
    birge = math.sqrt(sum(w * (a - wmean) ** 2 for w, a in zip(ws, depths)) / (n - 1))
    mean = sum(depths) / n
    sd = math.sqrt(sum((a - mean) ** 2 for a in depths) / (n - 1))
    return birge, mean, sd / math.sqrt(n)


def chi2(e, n, ref_e, ref_n, err_e, err_n):
    if not err_e or not err_n:
        return None
    return ((e - ref_e) / err_e) ** 2 + ((n - ref_n) / err_n) ** 2


def verdict(depth_snr, chi_zero, chi_nb):
    if depth_snr is None:
        return "unclear"
    if depth_snr < SIG_DEPTH:
        return "no_signal"
    if chi_zero is None or chi_nb is None:
        return "unclear"
    if chi_zero < CHI2_2DOF <= chi_nb:
        return "on_target"
    if chi_nb < CHI2_2DOF <= chi_zero:
        return "neighbour"
    return "unclear"


def tpf_files(kepid, cache):
    d9 = f"{int(kepid):09d}"
    url = MAST_TPF.format(d4=d9[:4], d9=d9)
    names = sorted(set(re.findall(r"kplr\d{9}-\d{13}_lpd-targ\.fits\.gz",
                                  http_bytes(url, 300).decode("utf-8", "replace"))))
    paths = []
    for name in names:
        path = os.path.join(cache, "kepler-tpf", d9, name)
        if not (os.path.exists(path) and os.path.getsize(path) > 10000):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = http_bytes(url + name, 600)
            with open(path + ".part", "wb") as f:
                f.write(data)
            os.replace(path + ".part", path)
        paths.append(path)
    return paths


def read_tpf(path):
    """One quarter: dict(quarter, times, frames (flat row-major lists, invalid pixels 0), nrow, ncol,
    valid, jac (arcsec per pixel), scale)."""
    import numpy as np
    from astropy.io import fits
    from astropy.wcs import WCS
    with fits.open(path, memmap=False) as h:
        quarter = int(h[0].header.get("QUARTER", -1))
        d = h[1].data
        t = np.array(d["TIME"], dtype=float)
        flux = np.array(d["FLUX"], dtype=float)
        qual = np.array(d["QUALITY"], dtype=int)
        wcs = WCS(h[2].header)
    nrow, ncol = flux.shape[1], flux.shape[2]
    good = (qual == 0) & np.isfinite(t)
    t, flat = t[good], flux[good].reshape(int(good.sum()), nrow * ncol)
    if len(t) == 0:
        raise ValueError("no quality-0 cadences")
    valid = np.isfinite(flat).mean(axis=0) >= MIN_VALID
    keep = np.isfinite(flat[:, valid]).all(axis=1)
    t, flat = t[keep], np.where(valid, flat[keep], 0.0)
    order = np.argsort(t)
    x0, y0 = (ncol - 1) / 2.0, (nrow - 1) / 2.0
    (ra0, de0), (ra1, de1), (ra2, de2) = wcs.wcs_pix2world([[x0, y0], [x0 + 1, y0], [x0, y0 + 1]], 0)
    cosd = math.cos(math.radians(de0))
    wrap = lambda x: (x + 180.0) % 360.0 - 180.0
    jac = [[wrap(ra1 - ra0) * cosd * 3600, wrap(ra2 - ra0) * cosd * 3600],
           [(de1 - de0) * 3600, (de2 - de0) * 3600]]
    scale = math.sqrt(abs(jac[0][0] * jac[1][1] - jac[0][1] * jac[1][0]))
    if not 3.5 < scale < 4.5:
        raise ValueError(f"pixel scale {scale:.2f} arcsec is not Kepler's ~3.98")
    return {"quarter": quarter, "times": t[order].tolist(), "frames": flat[order].tolist(),
            "nrow": nrow, "ncol": ncol, "valid": [bool(v) for v in valid], "jac": jac, "scale": scale}


def quarter_fits(q, p, t0, dur_h, phases, others, neighbour):
    """Per-phase rows for one quarter dict q: event count, fit (a, b, c, var_a), sky products and the
    neighbour calibration."""
    mask = mask_others(q["times"], others)
    rows = []
    for ph in phases:
        events = event_windows(q["times"], p, t0 + ph * p, dur_h, mask)
        row = {"quarter": q["quarter"], "phase": ph, "events": len(events), "a": None}
        if events:
            d_img, o_img = stack(q["frames"], events)
            fit = fit_shift(d_img, o_img, q["nrow"], q["ncol"], q["valid"])
            if fit:
                a, b, c, var_a = fit
                be, bn = to_sky(q["jac"], b, c)
                dcol, drow = to_pix(q["jac"], *neighbour)
                cal = fit_shift(shifted(o_img, q["nrow"], q["ncol"], drow, dcol), o_img,
                                q["nrow"], q["ncol"], q["valid"])
                cal_e, cal_n = (to_sky(q["jac"], cal[1] / cal[0], cal[2] / cal[0]) if cal and cal[0]
                                else (None, None))
                row.update({"a": a, "var_a": var_a, "b_east": be, "b_north": bn,
                            "cal_east": cal_e, "cal_north": cal_n})
        rows.append(row)
    return rows


def summarise(rows, phase):
    """Combined depth, offset, calibration and verdict for one phase over all quarters."""
    use = [r for r in rows if r["phase"] == phase and r["a"] is not None and r.get("var_a")]
    out = {"phase": phase, "quarters": len(use), "events": sum(r["events"] for r in use)}
    if not use:
        out["verdict"] = "unclear"
        out["verdict_scaled"] = "unclear"
        return out
    ws = [1 / r["var_a"] for r in use]
    depth = sum(w * r["a"] for w, r in zip(ws, use)) / sum(ws)
    derr = 1 / math.sqrt(sum(ws))
    out.update({"depth_ppm": depth * 1e6, "depth_err_ppm": derr * 1e6, "depth_snr": depth / derr})
    sc = scatter([r["a"] for r in use], [r["var_a"] for r in use])
    if sc:
        birge, mean, mean_err = sc
        err_s = derr * max(1.0, birge)
        out.update({"birge": birge, "depth_err_scaled_ppm": err_s * 1e6, "depth_snr_scaled": depth / err_s,
                    "mean_ppm": mean * 1e6, "mean_err_ppm": mean_err * 1e6})
    jk = jackknife([(w, r["a"], r["b_east"], r["b_north"]) for w, r in zip(ws, use)])
    cal = [(w, r["cal_east"], r["cal_north"]) for w, r in zip(ws, use) if r["cal_east"] is not None]
    cal_e = sum(w * e for w, e, _ in cal) / sum(w for w, _, _ in cal) if cal else None
    cal_n = sum(w * n for w, _, n in cal) / sum(w for w, _, _ in cal) if cal else None
    out.update({"cal_east": cal_e, "cal_north": cal_n})
    c0 = cn = None
    if jk:
        e, n, se, sn = jk
        c0 = chi2(e, n, 0.0, 0.0, se, sn)
        cn = (chi2(e, n, cal_e, cal_n, math.hypot(se, CAL_SYS * cal_e), math.hypot(sn, CAL_SYS * cal_n))
              if cal_e is not None else None)
        out.update({"east": e, "north": n, "err_east": se, "err_north": sn, "chi2_zero": c0, "chi2_neighbour": cn})
    out["verdict"] = verdict(out["depth_snr"], c0, cn)
    out["verdict_scaled"] = verdict(out.get("depth_snr_scaled"), c0, cn)
    return out


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def fmt(x, nd=2):
    return "" if x is None else f"{x:.{nd}f}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-dir", default="")
    ap.add_argument("--koi", default="K02643.01")
    ap.add_argument("--phases", default="0,0.5,0.25,0.75")
    ap.add_argument("--neighbour", default="2.69,-1.85", help="east,north arcsec from the target")
    ap.add_argument("--period-mult", type=float, default=1.0, help="whole factor applied to the catalogued period")
    ap.add_argument("--unmask", default="", help="comma-separated KOIs on the star not to mask")
    args = ap.parse_args(argv)
    phases = [float(x) for x in args.phases.split(",") if x.strip()]
    neighbour = tuple(float(x) for x in args.neighbour.split(","))
    unmask = [x.strip() for x in args.unmask.split(",") if x.strip()]
    os.makedirs(args.out_dir, exist_ok=True)
    cache = args.data_dir or tempfile.mkdtemp()

    koi = tap_rows("select kepid, kepoi_name, kepler_name, koi_period, koi_time0bk, koi_duration, koi_depth "
                   f"from cumulative where kepoi_name = '{args.koi}'")[0]
    kepid, p_cat, t0, dur_h = koi["kepid"], num(koi, "koi_period"), num(koi, "koi_time0bk"), num(koi, "koi_duration")
    p = scaled_period(p_cat, args.period_mult)
    others = other_ephemerides(
        tap_rows(f"select kepoi_name, koi_period, koi_time0bk, koi_duration from cumulative where kepid = {kepid}"),
        args.koi, unmask)

    rows, errors = [], []
    for path in tpf_files(kepid, cache):
        try:
            q = read_tpf(path)
            rows += quarter_fits(q, p, t0, dur_h, phases, others, neighbour)
            print(json.dumps({"file": os.path.basename(path), "quarter": q["quarter"],
                              "cadences": len(q["times"]), "shape": [q["nrow"], q["ncol"]]}), flush=True)
        except Exception as exc:  # one quarter's file problem must not stop the others
            errors.append(f"{os.path.basename(path)}: {type(exc).__name__}: {exc}"[:300])
    summaries = [summarise(rows, ph) for ph in phases]

    for r in rows:
        a = r.get("a")
        r["depth_ppm"] = None if a is None else round(a * 1e6, 1)
        r["east"] = r["b_east"] / a if a and r.get("b_east") is not None else None
        r["north"] = r["b_north"] / a if a and r.get("b_north") is not None else None
    write_csv(os.path.join(args.out_dir, "quarters.csv"), rows,
              ["quarter", "phase", "events", "depth_ppm", "var_a", "east", "north", "cal_east", "cal_north"])
    stats = {"version": VERSION, "run_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "koi": args.koi, "kepler_name": koi.get("kepler_name", ""), "kepid": kepid, "period": p,
             "catalog_period": p_cat, "period_mult": int(args.period_mult),
             "t0_bkjd": t0, "duration_h": dur_h, "koi_depth_ppm": num(koi, "koi_depth"),
             "neighbour_east_north": list(neighbour), "other_kois": len(others), "unmasked": unmask,
             "errors": errors, "phases": summaries}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)

    lines = [f"# kepler-pixels {VERSION}: {args.koi} {koi.get('kepler_name', '')}", "",
             f"Run {stats['run_at']}. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY "
             "4.0. A difference-image offset is evidence about where the light comes from, not a disposition.", "",
             f"P = {p} d ({int(args.period_mult)} x catalogued {p_cat} d), T0 = BKJD {t0}, duration {dur_h} h. "
             f"Other KOIs masked: {len(others)}; not masked: {', '.join(unmask) or 'none'}. "
             f"Neighbour at {neighbour[0]:+.2f}\" E, "
             f"{neighbour[1]:+.2f}\" N. Offsets are arcsec east/north of the out-of-transit light, jackknife errors "
             "over quarters; 'if neighbour' is the same estimator run on a copy of the image moved to the neighbour.",
             "", "| phase | quarters | events | depth (ppm) | offset E | offset N | if neighbour E, N | chi2 vs 0 "
             "| chi2 vs neighbour | verdict |", "|---|---|---|---|---|---|---|---|---|---|"]
    for s in summaries:
        lines.append(f"| {s['phase']} | {s['quarters']} | {s['events']} | {fmt(s.get('depth_ppm'), 0)} +- "
                     f"{fmt(s.get('depth_err_ppm'), 0)} | {fmt(s.get('east'))} +- {fmt(s.get('err_east'))} | "
                     f"{fmt(s.get('north'))} +- {fmt(s.get('err_north'))} | {fmt(s.get('cal_east'))}, "
                     f"{fmt(s.get('cal_north'))} | {fmt(s.get('chi2_zero'), 1)} | {fmt(s.get('chi2_neighbour'), 1)} | "
                     f"{s['verdict']} |")
    lines += ["", "Between quarters: Birge ratio of the quarter depths about the weighted mean, the depth with its "
              "error scaled by max(1, Birge), and the unweighted mean of the quarter depths.", "",
              "| phase | Birge | depth, scaled error (ppm) | SNR scaled | unweighted mean (ppm) | verdict scaled |",
              "|---|---|---|---|---|---|"]
    for s in summaries:
        lines.append(f"| {s['phase']} | {fmt(s.get('birge'))} | {fmt(s.get('depth_ppm'), 0)} +- "
                     f"{fmt(s.get('depth_err_scaled_ppm'), 0)} | {fmt(s.get('depth_snr_scaled'), 1)} | "
                     f"{fmt(s.get('mean_ppm'), 0)} +- {fmt(s.get('mean_err_ppm'), 0)} | {s['verdict_scaled']} |")
    if errors:
        lines += ["", "## File errors", ""] + [f"- {e}" for e in errors]
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
