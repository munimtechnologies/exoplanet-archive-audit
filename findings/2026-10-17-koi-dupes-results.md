# Results: KOIs listed twice on one star (koi_dupes 0.1.0): three stale CANDIDATEs found

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Code Apache-2.0, text and data CC BY 4.0. Predictions: findings/2026-10-17-koi-dupes-prereg.md
(committed before the run). Outputs: results/2026-10-17-koi-dupes-0.1.0/ (flags.csv, summary.json).
Run: compete job koi-dupes-v1, 2026-10-17 07:44Z, python 3.12.15, live TAP queries.

## Short version

Of the 1,977 KOIs the cumulative table lists as CANDIDATE, three look like leftovers. Each first appeared
in an early KOI table, was never carried into DR25, and repeats the transits of a confirmed planet on
the same star:

- **K01101.02** is Kepler-768 b listed a second time: same period (11.3911 vs 11.3910 d) and mid-times
  17 minutes apart.
- **K02167.02** (6.958 d) puts one transit in every 11 on Kepler-1129 c's (76.537 d; period ratio
  11.00006). Its catalogued model SNR is 1.8.
- **K01922.02** (15.095 d) puts one transit in every 7 on Kepler-1016 c's (105.655 d; ratio 6.9993). It
  has no catalogued depth or radius.

Both alias KOIs were catalogued before their sibling had a KOI of its own, which is the pattern of a
pipeline detection of one planet folded at a fraction of its period. A pixel test of the two alias
KOIs is pre-registered (findings/2026-10-17-orphan-pixels-prereg.md). Six of the eight predictions
held. The two misses (6 and 7) came from setting the chance rate too low. They are explained below.

## Scoring

| # | Prediction | Result | |
|---|---|---|---|
| 1 | All 11 unit tests pass | 11 of 11 | held |
| 2 | 9,500-9,700 KOI rows, 2,700-2,800 pscomppars rows | 9,564 and 2,755 | held |
| 3 | Kepler-289 d / K01353.03 flagged same_events, k = 5 | yes, offset 0.279 d | held |
| 4 | koi mode: <= 25 same_events | 21 | held |
| 5 | >= half include a FALSE POSITIVE | 17 of 21 | held |
| 6 | <= 3 same_events with both CANDIDATE/CONFIRMED | 4 | **missed** |
| 7 | Chance rate <= 3 (koi) and <= 1 (cross) | 7.0 (koi), 0 (cross) | **missed** (koi) |
| 8 | cross: <= 3 same_events besides Kepler-289 | 1 | held |

Counts, real vs null (epoch of the long signal shifted by a fraction of the short period):

| | same_events | offset |
|---|---|---|
| real | 21 | 16 |
| null 0.25 | 8 | 29 |
| null 0.5 | 10 | 27 |
| null 0.75 | 6 | 31 |

All 37 commensurate pairs are the same in every run; only the phase test changes. The window
(sum of the two durations) is wide, so 7 of 37 pass by chance, not the 3 we predicted. The real run
has 14 more same_events pairs than chance; 17 of the 21 include a FALSE POSITIVE, mostly eclipsing
binaries listed at P and 2P, which the vetting already handles.

## Hand checks of every same_events pair without a FALSE POSITIVE member

### Cross mode

- Kepler-289 d / K01353.03 (= Kepler-289 e): the known duplicate, positive control
  (findings/2026-10-16-kepler-289.md).
- K01833.02 / "KOI-1833 d": **not a duplicate**. The Archive's alias service lists K01833.02,
  KOI-1833.02, Kepler-968 d and KOI-1833 d as one object, with KOI-1833 d as the default name. The
  cumulative table calls it Kepler-968 d, so the tool's name match missed it. This is a tool limit
  (0.2.0 should match through aliases), not a catalogue error.

### koi mode

**1. K01101.02 = Kepler-768 b (K01101.01). Duplicate.**

| table | K01101.01 P (d) | K01101.02 P (d) | note |
|---|---|---|---|
| Q1-Q6 | 2.847739 | (none) | .01 at a quarter of the true period |
| Q1-Q8 | 2.84796 | 11.39094 | .02 added at the true period |
| Q1-Q12 | 11.3910025 | 11.39110963 | .01 corrected (Ofir & Dreizler 2012, sec. 4.11: "four times the published period"); .02 CANDIDATE |
| Q1-Q16 | 11.3910025 | 11.39110963 | .02 NOT DISPOSITIONED |
| DR25 | 11.39102358 | (none) | .01 CONFIRMED as Kepler-768 b (Morton et al. 2016) |
| cumulative | 11.39102358, T0 137.70864 | 11.39110963, T0 137.69665 | .02 CANDIDATE (DR25 supplemental), parameters from Q1-Q16 |

Same period within 9e-5 d and mid-times 0.012 d apart, against a 2.3 h duration. Depths 449 vs 593 ppm
and radii 1.67 vs 1.90 Re differ by about what the fits from different data sets differ for .01 itself
(556 ppm in Q1-Q16). Once .01's period was corrected, both KOIs described one signal.

**2. K02167.02 and Kepler-1129 c (K02167.03). Likely a 1/11 alias.**

| table | K02167.02 P (d) | depth (ppm) | dur (h) | K02167.03 |
|---|---|---|---|---|
| Q1-Q6 | 6.95746 | 191 | 4.66 | not yet a KOI |
| Q1-Q8 | 6.95756 | 19 | 1.51 | not yet a KOI |
| Q1-Q12, Q1-Q16 | 6.95787 | 182.3 | 4.537 | 76.5369586 d, 712 ppm, CONFIRMED later |
| cumulative | 6.95787, T0 359.007 | 182.3, model SNR 1.8 | 4.537 | Kepler-1129 c, 76.5369531 d |

11 x 6.95787 = 76.53657 d, 0.0004 d from Kepler-1129 c's period, and Kepler-1129 c's mid-time falls
0.030 d from a K02167.02 event (window 0.42 d). Not in DR25; cumulative disposition CANDIDATE from the
DR25 supplemental table, with no score or SNR there.

**3. K01922.02 and Kepler-1016 c (K01922.03). Likely a 1/7 alias.**

| table | K01922.02 P (d) | depth (ppm) | dur (h) | K01922.03 |
|---|---|---|---|---|
| Q1-Q6 | 15.09557 | 382 | 4.33 | not yet a KOI |
| Q1-Q8 | 15.0952 | 85 | 3.41 | not yet a KOI |
| Q1-Q12, Q1-Q16 | 15.09521323 | none | 3.41 | 105.6551369 d, 1351 ppm |
| cumulative | 15.09521323, T0 139.474359 | none | 3.41 | Kepler-1016 c, 105.6552651 d |

7 x 15.09521 = 105.6665 d, 0.011 d from Kepler-1016 c's period (drift 0.16 d over the mission, inside
c's 9.4 h transit), and c's mid-time falls 0.053 d from a K01922.02 event. Not in DR25; CANDIDATE from
the supplemental table; no depth, radius, score or SNR.

**4. Kepler-342 e (K01955.03, 1.644 d) and Kepler-342 d (K01955.02, 39.458 d), k = 24. Chance.**
The window (0.52 d) covers 63 % of e's 1.64 d period, so a phase match is likely by chance; the offset
is 0.21 d. A 1/24 alias of d (245 ppm) would be about 10 ppm deep, not e's 48 ppm. Both are confirmed
planets, and nothing here suggests either is wrong.

How unlikely are leads 2 and 3 by chance? These figures are post hoc, so treat them as a rough guide.
A random period ratio is this close to a whole number with probability 2 x 0.000055 = 1.1e-4 (K02167)
and 2 x 0.00074 = 1.5e-3 (K01922). A random epoch lands this close to a sibling transit with
probability 2 x 0.030 / 6.958 = 0.009 and 2 x 0.053 / 15.095 = 0.007. That is about 1e-6 and 1e-5
per pair, against one to a few thousand KOI pairs on multi-KOI stars (9,564 KOIs on 8,214 stars). The same estimate for Kepler-342
e/d gives 1e-3 per pair, which fits chance.

Also flagged and already handled: K02768.03 (FALSE POSITIVE) repeats Kepler-404 b at the same period,
depth and radius.

## Context: orphan KOIs in the cumulative table

The cumulative table takes parameters from older activity tables for KOIs that DR25 did not deliver
("orphans"; Archive documentation, PurposeOfKOITable). Their disposition comes from the DR25
supplemental table, which used the FPWG disposition "if one existed, else the (non-disputed)
disposition from past KOI catalogs". On 2026-10-17, 600 of the 1,977 CANDIDATE rows are orphans of
this kind: 461 with Q1-Q16 parameters and 139 with DR24 parameters. All three leads are Q1-Q16 orphans.

## Prior art

- DR25 federation (Thompson et al. 2018, sec. VI.2) matches TCEs to known KOIs at 1x and 2x periods
  within DR25 only. These three KOIs were not delivered in DR25.
- Coughlin et al. 2014 (ephemeris matching) allows any integer period ratio but says "The two objects
  could not have the same KIC ID", so it never compares KOIs on the same star.
- Ofir & Dreizler 2012 corrected KOI-1101.01's period to 4x but do not mention .02.
- Web searches for KOI-1101.02, KOI-2167.02 and KOI-1922.02 (2026-10-17) found no note calling them
  duplicates or aliases. If one exists, this is a replication.

## Limits and what next

- A flag plus a catalogue history is a strong lead, not proof. For K02167.02 and K01922.02 the
  pre-registered pixel test (orphan-pixels) checks whether anything remains at their ephemeris once the
  sibling's transits are masked.
- The scan covers KOI pairs on one star and KOI vs Kepler-named planets; it does not cover TCEs that
  never became KOIs, or planets named only by KOI number.
- koi_dupes 0.2.0 should match names through the alias service and report the chance rate per pair,
  not only in aggregate.
