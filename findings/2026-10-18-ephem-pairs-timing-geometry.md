# Cross-star ephemeris pairs: not at data gaps, not on a ghost line, and three shared events each

MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no human has checked this yet.
Text and data CC BY 4.0. Follow-up to findings/2026-10-18-cross-star-ephemeris-pairs.md (the three pairs
A, B, C). Every number below was worked by hand and is re-checked by the unit tests of pair_context 0.1.0
(this repository). No light curves or pixels were read.

## 1. Correction: each pair shares three observed events, not four

The first note said every event "inside Q1-Q17" agrees. Two of those predicted events were never searched by
both members:

- **Pair B, event 4 (BKJD 1478.15 = 2013-01-18 ~15:30 UTC)** falls 0.83 d after the last cadence before
  Kepler's ten-day reaction-wheel rest (science stopped 2013-01-17 and restarted about 2013-01-27 to 29;
  reports differ on the day). No data exist at that time on either star.
- **Pair A, event 4 (BKJD 1576.14, Q17)** lies after the Q1-Q16 data that produced K05660.01. Only K08259.01
  (DR25, Q1-Q17) was searched there, and DR25 produced no TCE at all on K05660.01's star (KIC 9363944).

So pairs A, B and C each share **three** events that both members' searches covered. The post-hoc chance
estimate in the first note used only epoch agreement, so it does not change; the pre-registered census
(ephem_pairs 0.1.0) counts events in the Q1-Q17 span on both sides and is unaffected as a test.

## 2. Timing: no event sits at a data gap

Kepler paused at every monthly downlink and quarterly roll, and pointing and thermal systematics cluster in
the day or two after each restart. MAST light-curve file names (`kplr<KIC>-<YYYYDDDHHMMSS>_llc/slc.fits`)
stamp each segment with the end of its last cadence in US Pacific local time. Converted to UTC, the long-cadence
stamps reproduce the MAST quarter end times (archive.stsci.edu/missions-and-data/kepler/field) to within
0.0102 d for Q0-Q16, so the short-cadence monthly stamps (KIC 11446443, 6541920, 11904151) date every
monthly gap. Times are MJD - 54832.5 (BKJD within minutes).

| Event | BKJD | Quarter | Previous dated boundary | Days after | Next boundary | Days before |
|---|---|---|---|---|---|---|
| A1 | 369.51 | Q4 | Q4 start | 17.13 | Q4 m1 end | 14.00 |
| A2 | 771.72 | Q8 | Q8 m1 end | 18.67 | Q8 m2 end | 10.49 |
| A3 | 1173.93 | Q12 | Q12 m2 end | 19.93 | Q12 end | 8.10 |
| A4 | 1576.14 | Q17 | Q17 start | 16.91 | Q17 m1 end | 6.45 |
| B1 | 227.51 | Q2 | Q2 m1 end | 27.21 | Q2 m2 end | 2.79 |
| B2 | 644.39 | Q7 | Q7 start | 14.22 | Q7 m1 end | 15.89 |
| B3 | 1061.27 | Q11 | Q11 m1 end | 28.99 | Q11 m2 end | 1.96 |
| B4 | 1478.15 | Q16 | wheel-rest start | 0.83 | (no data) | - |
| C1 | 162.91 | Q1 | Q1 start | 31.40 | Q1 end | 2.07 |
| C2 | 665.12 | Q7 | Q7 m1 end | 4.84 | Q7 m2 end | 25.12 |
| C3 | 1167.33 | Q12 | Q12 m2 end | 13.33 | Q12 end | 14.70 |

(Event times from each pair's first member; partners differ by up to 0.36 d. "m1 end" is the stop of
month 1. The restart after each monthly stop is about a day later and is not dated here, so "days after"
a month end overstates the time since data resumed by about one day.)

- No observed event lies within 4.8 d after a stop (so no closer than ~3.8 d after a restart) or within
  14 d after a quarter start, where post-gap thermal settling sits. A gap-edge systematic does not explain the shared events.
- Three events (B1, B3, C1) fall 2-3 d **before** a stop. For random times about one of ten would
  (3 d of each ~30 d month); Poisson P(>= 3 | 1.0) = 0.08, chosen after looking. Not significant.
- **No shared dates across pairs.** The closest events of different pairs are A3 and C3, 6.60 d apart. One
  spacecraft date list does not explain all three pairs.
- The shared events of pair C fall in Q1, Q7 and Q12: three different roll orientations (quarter mod 4 =
  1, 3, 0). Pair B's observed events are in Q2, Q7, Q11 (two orientations); pair A's in Q4, Q8, Q12 (one).
  Each roll moves both stars to a different CCD module, so for pair C an electronic path tied to one module
  pair (crosstalk, a shared readout) would have to be different hardware at each event.

## 3. Geometry: no pair lies on a line through the field centre

Kepler rolls 90 deg about the field centre (RA 290.6667, Dec +44.5) each quarter. A ghost from rotationally
symmetric optics (the antipodal reflection DR25 tests is one case) maps a star to a point on the same line
through the centre, at the same or the opposite azimuth, in every season. Gnomonic positions about the centre
(x east, y north, degrees):

| Pair | Member | x | y | r | Azimuth | Azimuth gap |
|---|---|---|---|---|---|---|
| A | K05660.01 | 5.839 | 1.676 | 6.08 | 16.0 | |
| A | K08259.01 | -0.162 | -3.278 | 3.28 | 267.2 | 108.8 |
| B | K05935.01 | 2.284 | 5.617 | 6.06 | 67.9 | |
| B | K05446.01 | 6.291 | -0.528 | 6.31 | 355.2 | 72.7 |
| C | K07040.01 | 3.850 | 0.088 | 3.85 | 1.3 | |
| C | K07932.01 | 0.159 | 1.217 | 1.23 | 82.6 | 81.3 |

Azimuth gaps of 73-109 deg are far from 0 or 180, so no rotationally symmetric ghost links any pair.
All three gaps happen to be near 90 deg, but a 90-deg rotation would also need equal radii, and pairs A
(6.08 vs 3.28) and C (3.85 vs 1.23) are far from equal. We note it and claim nothing.

## 4. Prior art on far-apart matches

- Coughlin et al. 2014 (AJ 147, 119) name four contamination paths: direct PRF, column anomaly, video
  crosstalk and antipodal reflection. Their flag "3" marks column-anomaly-like matches on different CCDs of
  the **same module** with no named mechanism. Our pairs are on different modules.
- The Certified False Positive Table notes (Bryson, KSCI-19093-003, as summarised by a web search; we could
  not open the PDF) say several ephemeris matches come from bright eclipsing binaries very distant on the
  focal plane. Abdul-Masih et al. 2016
  (Kepler EB VIII, arXiv 1602.05932) attribute widely separated matches to optical cross-talk (scattered
  light) from bright binaries (V < 10).
- So far matches have precedent, but each known case has a **bright parent** at the same ephemeris. The
  Q1-Q16, DR24 and DR25 TCE tables hold no other star at the 402 d or 417 d ephemerides (first note, section
  "Other stars"). An unobserved bright parent cannot be ruled out from catalogues alone. It would have to
  reach two stars degrees apart, in more than one roll orientation, by paths that are not rotationally
  symmetric.

## What this changes

The three pairs are not at data gaps, do not share dates with each other, and are not on a symmetric ghost
line. That rules out the three simplest instrumental explanations we could test without pixels. The open
explanations are: (i) chance (the pre-registered phase-shuffle census decides this), (ii) an unobserved
bright parent reaching both stars by a non-symmetric path, (iii) one real signal copied by an unknown path.
The next real test is per-transit light curves and pixel images at the three shared events of each pair.

## Sources

- MAST Kepler quarter times: https://archive.stsci.edu/missions-and-data/kepler/field
- MAST light-curve directories (file names only): archive.stsci.edu/missions/kepler/lightcurves/0114/011446443/,
  .../0065/006541920/, .../0119/011904151/
- Wheel rest, Jan 2013: https://exoplanets.nasa.gov/exep/newsletters/issue10/keplerUpdate/
- Coughlin et al. 2014: https://arxiv.org/abs/1401.1240
- KSCI-19093-003: https://exoplanetarchive.ipac.caltech.edu/docs/KSCI-19093-003.pdf
- Abdul-Masih et al. 2016: https://arxiv.org/html/1602.05932
