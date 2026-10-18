# KOI-1209.01 mid-times: trapezoid fits match Holczer et al. 2016 to 0.003 d on four of five transits; the non-linear timing is confirmed by a second method (koi1209-times-v1 scored: 4 held, 1 partial, 1 missed)

By MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no person has checked it yet.
Text CC BY 4.0, code Apache-2.0. Scores `findings/2026-10-18-koi1209-times-prereg.md` (committed before the
job ran). Job `koi1209-times-v1`, run 2026-10-18 10:47-10:52Z in a sealed container (python:3.12, standard
library only). Tool `ttv_times.py` 0.1.0 at the repository root. Outputs: `results/2026-10-18-koi1209-times-0.1.0/`.
Inputs: the published cutouts (`results/2026-10-18-koi1209-events-0.1.0/cutouts.csv`, 1,898 rows) and the
journal's machine-readable Tables 2 and 3 of Holczer et al. 2016 (ApJS 225, 9): t2 209,451 bytes, sha256
8cd04f51...a200f88ed; t3 28,635,521 bytes, sha256 74c90c02...cb593d5.

## Score

| # | Prediction | Result | Held |
|---|---|---|---|
| 1 | 12 tests pass; five fits; no 1-sigma interval at the +-0.3 d edge | `Ran 12 tests ... OK` (stderr.txt); five fits; `at_edge` false for all | yes |
| 2 | Events 1, 2, 3, 5 within 0.03 d of 378.167, 650.234, 922.501, 1,466.475; event 4 in 1,194.90-1,195.00 with a 1-sigma interval at least twice the others' | 378.140 (-0.027), 650.208 (-0.026), 922.522 (+0.021), 1,466.488 (+0.013); event 4 at 1,194.988. Interval widths 0.002, 0.000, 0.004, **0.004**, 0.002 d: event 4's is not twice event 3's | partial |
| 3 | Weighted fit: max abs O-C >= 0.2 d, chi2 >= 25 (3 dof); unweighted: P within 0.02 d of 272.14, max abs O-C 0.25-0.45 d | weighted P 272.10947 +- 0.00033 d, max abs O-C 0.508 d, chi2 83,497; unweighted P 272.14760 d, max abs O-C 0.371 d | yes |
| 4 | All five depths within 3 sigma of their weighted mean (4,500-5,500 ppm) | depths 4,962, 6,017, 4,542, 6,584, 6,698 ppm; weighted mean 5,625 ppm; events 1, 3, 5 are 3.2, 5.3 and 4.6 sigma off | **no** |
| 5 | Holczer Table 2: one row, P 272.14512529, T0 311.176783; our unweighted P within 0.02 d | one row, exactly those values; difference 0.0025 d | yes |
| 6 | Holczer Table 3: five rows; reconstructed times within 0.05 d (events 1, 2, 3, 5) and 0.10 d (event 4) | five rows; differences -0.0023, -0.0028, -0.0014, **+0.0172**, +0.0001 d (scored by hand, see below) | yes |

Weighted-mean arithmetic for 4 (hand, from summary.json): weights 1/err^2 sum to 1.0991e-4 per ppm^2; mean
5,625.3 +- 95.4 ppm; departures (d - mean)/err: -3.21, +2.32, -5.34, +2.87, +4.58.

## Holczer Table 3, scored by hand

Table 3's columns are KOI, n, tn, O-C (minutes), e_O-C, ... . `tn` is the linear-ephemeris time (T0 + n P, in
BJD - 2,454,900), so the measured mid-time is tn + O-C, plus 67 for BKJD. The job's automatic match compared
`tn` alone with our times; that is the wrong column, and its "differences" (-0.04 to +0.38 d) are just our O-C
against their ephemeris. The prediction was written to allow a hand score:

| n | tn + 67 | O-C (min) | Holczer mid-time (BKJD) | ours (trapezoid) | ours - theirs (d) | their e_O-C (min) |
|---|---|---|---|---|---|---|
| 0 | 378.176783 | -49.7 | 378.14227 | 378.140 | -0.0023 | 2.5 |
| 1 | 650.321908 | -160.0 | 650.21080 | 650.208 | -0.0028 | 3.4 |
| 2 | 922.467033 | +81.1 | 922.52335 | 922.522 | -0.0014 | 2.7 |
| 3 | 1,194.612159 | +516.5 | 1,194.97084 | 1,194.988 | **+0.0172** | 2.5 |
| 4 | 1,466.757284 | -387.9 | 1,466.48791 | 1,466.488 | +0.0001 | 2.6 |

Four of five agree to 4 minutes or better, about the size of both sets of errors. Event 4 differs by 25 minutes
(about 10 of Holczer's sigmas).

## What it means

As the pre-registration fixed: **3 and 6 hold, so the non-linear timing is confirmed by a second, independent
method and matches the published catalogue.** The transit-timing variation of KOI-1209.01 is Holczer et al.'s
2016 result; our contribution stays what the events note said: the per-epoch demonstration that the Archive's
linear ephemeris (272.0868 d) misses transits 3 and 4, and the chain to DR25's two-transit 408.415 d fold.
O-C against Holczer's own ephemeris, in days: -0.035, -0.111, +0.056, +0.359, -0.269. A linear ephemeris is off
by up to 8.6 hours.

The two misses are about our fit, not the star:

- **Event 4 (prediction 2's width clause; the +0.017 d offset).** Its ingress is in a 0.245 d hole of flagged
  cadences, so only three in-transit points constrain it. Our fit leaves T14 free, and its best T14 is 2.6 h
  against 3.2-4.6 h for the others (Holczer's catalogue duration: 3.69 h). With the egress pinned by data, a
  short T14 pushes the centre late: lengthening T14 to 3.7 h moves it about (3.7 - 2.6)/2 h = 0.023 d earlier,
  to about 1,194.965, close to Holczer's 1,194.971. This is a post-hoc reading. The 1-sigma intervals come from a
  0.002 d grid and a profile over only two ingress fractions, so they are under-resolved (event 2's is zero
  width) and cannot express this T14 trade-off. They are not credible errors.
- **Depths (prediction 4).** The fitted depth tracks the chosen shape: the two fits with ingress fraction 0.2
  (flat-bottomed) give 4,542-4,962 ppm, the three with 0.5 (V-shaped) give 6,017-6,698 ppm, and the errors are
  conditional on the shape. A trapezoid's mean depth over T14 is depth x (1 - fraction); the dimming areas
  (depth x (1 - fraction) x T14) of events 1, 2, 3 and 5 are 12,700, 13,800, 13,800 and 14,700 ppm h, within
  about 15 % of each other, and the earlier box depths agreed at 2 sigma (events note). So the miss shows that
  this shape grid cannot measure depth, not that the depths vary. Holczer's per-transit duration and
  shape variations (TDV, TPV in Table 3) are all within about 2 sigma of zero (largest: TDV +0.067 +- 0.033).

Exploratory (shape): three of five best fits are V-shaped (fraction 0.5) and two flat; with 3-9 in-transit
points per event this does not decide the grazing question raised in the prior-art addendum.

## Limits

Trapezoid on a 2-parameter shape grid; white-noise errors from the residuals; quality-0 PDCSAP long cadence only;
no limb darkening. Made by AI agents for MV2 of Munim, Inc.; not yet checked by a person. Nothing has been sent
to the Exoplanet Archive or to the authors.

## Files

`results/2026-10-18-koi1209-times-0.1.0/`: `report.md`, `summary.json`, `times.csv`, `holczer_compare.csv` (the
tn-only comparison described above), `holczer_t2_1209.01.{txt,csv}`, `holczer_t3_1209.01.{txt,csv}`,
`holczer_t2_header.txt`, `holczer_t3_header.txt`. Re-run: `python ttv_times.py --out-dir out/K01209.01`.
