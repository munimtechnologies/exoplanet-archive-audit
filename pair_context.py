"""pair_context: where in Kepler's data stream, and where on the focal plane, do the three cross-star
ephemeris pairs fall?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

Two checks on the pairs in findings/2026-10-18-cross-star-ephemeris-pairs.md:

1. Timing. Kepler stopped collecting data at every monthly downlink and quarterly roll. The MAST light-curve
   file names (kplr<KIC>-<YYYYDDDHHMMSS>_llc/slc.fits) stamp each segment with the end of its last cadence
   in US Pacific local time. Converted to UTC they reproduce the MAST quarter end times to 0.011 d for
   Q0-Q16, so the short-cadence stamps date every monthly gap. Each event gets the nearest boundary before
   and after it. Thermal and pointing systematics sit just after a gap; an event far from every boundary
   is not explained by one.
2. Geometry. The spacecraft rolls 90 deg about the field centre each quarter, so any ghost made by
   rotationally symmetric optics maps a star to a point on the same line through the centre (same or
   opposite azimuth). Positions are projected gnomonically about the centre; a pair whose azimuths differ
   by far from 0 or 180 deg is not linked by such a ghost.

Times are MJD - 54832.5, which equals BKJD to within the barycentric correction (minutes).

    python pair_context.py --out-dir out
"""
import argparse
import csv
import json
import math
import os
from datetime import date, datetime, timedelta

VERSION = "0.1.0"
FIELD_RA, FIELD_DEC = 290.6667, 44.5
BKJD_ZERO = datetime(2009, 1, 1, 12)
SPAN = (131.5, 1591.0)

# Quarter starts, MJD of the first long cadence (archive.stsci.edu/missions-and-data/kepler/field).
QUARTER_START_MJD = {
    0: 54953.03815, 1: 54964.01099, 2: 55002.01748, 3: 55092.72221, 4: 55184.87774, 5: 55275.99115,
    6: 55371.94733, 7: 55462.67251, 8: 55567.86468, 9: 55641.01696, 10: 55739.34343, 11: 55833.70579,
    12: 55931.90966, 13: 56015.23787, 14: 56106.63736, 15: 56205.98550, 16: 56304.59804, 17: 56391.72690,
}
# Quarter ends, MJD of the last long cadence (same page), used to check the file-name stamps.
QUARTER_END_MJD = {
    0: 54962.74411, 1: 54997.48122, 2: 55090.96492, 3: 55181.99660, 4: 55274.70384, 5: 55370.66003,
    6: 55461.79386, 7: 55552.04909, 8: 55634.84602, 9: 55738.42395, 10: 55832.76587, 11: 55930.82669,
    12: 56014.52273, 13: 56105.55441, 14: 56203.81957, 15: 56303.63768, 16: 56390.46005, 17: 56423.50115,
}
# Segment ends from MAST file names: LC quarter files (all stars) and SC monthly files of KIC 11446443,
# 6541920 and 11904151. The Q17 file stamp is not used (data stopped with the wheel failure; the MAST
# end time is used instead).
SEGMENT_END_STAMPS = [
    ("Q0 end", "2009131105131"), ("Q1 end", "2009166043257"),
    ("Q2 m1 end", "2009201121230"), ("Q2 m2 end", "2009231120729"), ("Q2 end", "2009259160929"),
    ("Q3 m1 end", "2009291181958"), ("Q3 m2 end", "2009322144938"), ("Q3 end", "2009350155506"),
    ("Q4 m1 end", "2010019161129"), ("Q4 m2 end", "2010049094358"), ("Q4 end", "2010078095331"),
    ("Q5 m1 end", "2010111051353"), ("Q5 m2 end", "2010140023957"), ("Q5 end", "2010174085026"),
    ("Q6 m1 end", "2010203174610"), ("Q6 m2 end", "2010234115140"), ("Q6 end", "2010265121752"),
    ("Q7 m1 end", "2010296114515"), ("Q7 m2 end", "2010326094124"), ("Q7 end", "2010355172524"),
    ("Q8 m1 end", "2011024051157"), ("Q8 m2 end", "2011053090032"), ("Q8 end", "2011073133259"),
    ("Q9 m1 end", "2011116030358"), ("Q9 m2 end", "2011145075126"), ("Q9 end", "2011177032512"),
    ("Q10 m1 end", "2011208035123"), ("Q10 m2 end", "2011240104155"), ("Q10 end", "2011271113734"),
    ("Q11 m1 end", "2011303113607"), ("Q11 m2 end", "2011334093404"), ("Q11 end", "2012004120508"),
    ("Q12 m1 end", "2012032013838"), ("Q12 m2 end", "2012060035710"), ("Q12 end", "2012088054726"),
    ("Q13 m1 end", "2012121044856"), ("Q13 m2 end", "2012151031540"), ("Q13 end", "2012179063303"),
    ("Q14 m1 end", "2012211050319"), ("Q14 m2 end", "2012242122129"), ("Q14 end", "2012277125453"),
    ("Q15 m1 end", "2012310112549"), ("Q15 m2 end", "2012341132017"), ("Q15 end", "2013011073258"),
    ("Q16 wheel-rest start", "2013017113907"), ("Q16 m2 end", "2013065031647"), ("Q16 end", "2013098041711"),
    ("Q17 m1 end", "2013121191144"),
]
LC_QUARTER_STAMPS = {int(label[1:].split()[0]): s for label, s in SEGMENT_END_STAMPS if label.endswith(" end")
                     and " m" not in label}

# The six KOIs (NASA Exoplanet Archive cumulative table, read 2026-10-18).
PAIRS = {
    "A": [("K05660.01", 9363944, 402.20969, 369.5086, 299.035280, 45.869289),
          ("K08259.01", 5956171, 402.27493, 369.6734, 290.451900, 41.225510)],
    "B": [("K05935.01", 11818566, 416.87893121, 227.5106644, 294.206300, 50.045399),
          ("K05446.01", 7917068, 416.9504, 227.392, 299.341030, 43.643162)],
    "C": [("K07040.01", 8442795, 502.20642, 162.9131, 296.057280, 44.461079),
          ("K07932.01", 9278575, 502.25648, 162.5842, 290.893950, 45.716640)],
}


def _nth_sunday(year, month, n):
    first = 1 + (6 - date(year, month, 1).weekday()) % 7
    return datetime(year, month, first + 7 * (n - 1), 2)


def pacific_is_dst(local):
    """US rules from 2007: second Sunday of March 02:00 to first Sunday of November 02:00, local time."""
    return _nth_sunday(local.year, 3, 2) <= local < _nth_sunday(local.year, 11, 1)


def stamp_to_utc(stamp):
    year, doy = int(stamp[0:4]), int(stamp[4:7])
    local = datetime(year, 1, 1) + timedelta(days=doy - 1, hours=int(stamp[7:9]), minutes=int(stamp[9:11]),
                                             seconds=int(stamp[11:13]))
    return local + timedelta(hours=7 if pacific_is_dst(local) else 8)


def utc_to_bkjd(utc):
    return (utc - BKJD_ZERO).total_seconds() / 86400.0


def stamp_to_bkjd(stamp):
    return utc_to_bkjd(stamp_to_utc(stamp))


def mjd_to_bkjd(mjd):
    return mjd - 54832.5


def boundaries():
    """Sorted (bkjd, label) of every dated data start and stop."""
    out = [(mjd_to_bkjd(m), "Q%d start" % q) for q, m in QUARTER_START_MJD.items()]
    out += [(stamp_to_bkjd(s), label) for label, s in SEGMENT_END_STAMPS]
    out.append((mjd_to_bkjd(QUARTER_END_MJD[17]), "Q17 end"))
    return sorted(out)


def quarter_of(t):
    q = None
    for k in sorted(QUARTER_START_MJD):
        if mjd_to_bkjd(QUARTER_START_MJD[k]) <= t:
            q = k
    return q


def events(period, t0, span=SPAN):
    n = math.ceil((span[0] - t0) / period)
    out = []
    while t0 + n * period <= span[1]:
        out.append(t0 + n * period)
        n += 1
    return out


def context(t, bounds=None):
    """Nearest dated boundary before and after t, with distances in days."""
    bounds = boundaries() if bounds is None else bounds
    before = [b for b in bounds if b[0] <= t]
    after = [b for b in bounds if b[0] > t]
    prev = before[-1] if before else (None, None)
    nxt = after[0] if after else (None, None)
    return {"t": round(t, 4), "quarter": quarter_of(t), "season": quarter_of(t) % 4,
            "prev": prev[1], "days_after_prev": None if prev[0] is None else round(t - prev[0], 3),
            "next": nxt[1], "days_before_next": None if nxt[0] is None else round(nxt[0] - t, 3)}


def gnomonic(ra, dec, ra0=FIELD_RA, dec0=FIELD_DEC):
    """Tangent-plane (x east, y north) in degrees about (ra0, dec0)."""
    a, d, a0, d0 = map(math.radians, (ra, dec, ra0, dec0))
    cosc = math.sin(d0) * math.sin(d) + math.cos(d0) * math.cos(d) * math.cos(a - a0)
    x = math.cos(d) * math.sin(a - a0) / cosc
    y = (math.cos(d0) * math.sin(d) - math.sin(d0) * math.cos(d) * math.cos(a - a0)) / cosc
    return math.degrees(x), math.degrees(y)


def polar(x, y):
    return math.hypot(x, y), math.degrees(math.atan2(y, x)) % 360.0


def azimuth_gap(az1, az2):
    """Angle between two azimuths, 0-180 deg; 0 = same side of the centre, 180 = opposite."""
    d = abs(az1 - az2) % 360.0
    return min(d, 360.0 - d)


def pair_geometry(m1, m2):
    x1, y1 = gnomonic(m1[4], m1[5])
    x2, y2 = gnomonic(m2[4], m2[5])
    r1, az1 = polar(x1, y1)
    r2, az2 = polar(x2, y2)
    gap = azimuth_gap(az1, az2)
    return {"members": [m1[0], m2[0]], "xy": [[round(x1, 3), round(y1, 3)], [round(x2, 3), round(y2, 3)]],
            "r_deg": [round(r1, 3), round(r2, 3)], "az_deg": [round(az1, 2), round(az2, 2)],
            "azimuth_gap_deg": round(gap, 2), "collinear_within_10deg": min(gap, 180.0 - gap) <= 10.0}


def cross_pair_min_gap(pairs=PAIRS):
    """Smallest time between events of different pairs (first members' ephemerides)."""
    trains = {k: events(v[0][2], v[0][3]) for k, v in pairs.items()}
    best = None
    keys = sorted(trains)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            for ta in trains[a]:
                for tb in trains[b]:
                    d = abs(ta - tb)
                    if best is None or d < best[0]:
                        best = (round(d, 3), a, round(ta, 3), b, round(tb, 3))
    return best


def run(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    bounds = boundaries()
    with open(os.path.join(out_dir, "segment_boundaries.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bkjd_approx", "label"])
        for t, label in bounds:
            w.writerow(["%.4f" % t, label])
    rows = []
    for key, (m1, m2) in sorted(PAIRS.items()):
        for t in events(m1[2], m1[3]):
            c = context(t, bounds)
            c["pair"] = key
            rows.append(c)
    with open(os.path.join(out_dir, "event_context.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pair", "t", "quarter", "season", "prev", "days_after_prev", "next",
                                          "days_before_next"])
        w.writeheader()
        w.writerows(rows)
    summary = {"version": VERSION, "geometry": {k: pair_geometry(*v) for k, v in sorted(PAIRS.items())},
               "cross_pair_min_gap": cross_pair_min_gap(),
               "stamp_check_days": {q: round(stamp_to_bkjd(s) - mjd_to_bkjd(QUARTER_END_MJD[q]), 4)
                                    for q, s in sorted(LC_QUARTER_STAMPS.items())}}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    return summary, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args()
    summary, rows = run(args.out_dir)
    for r in rows:
        print(r)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
