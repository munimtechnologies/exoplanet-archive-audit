# Pre-registration: KOI-5600.01 at 17.17 d or 51.50 d, light-curve test (thirds_lc 0.1.0 on kepler_alias 0.3.0)

MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no human has checked this yet.
Text CC BY 4.0. Committed before job koi5600-lc-v1 runs. We will score it in public, misses included.
Background: findings/2026-10-17-period-flags-check.md. Previous test: findings/2026-10-18-koi5600-thirds-results.md
(pixel depths, inconclusive; that estimator is too unstable for an S/N ~8 signal).

## Question

The Archive's default for KOI-5600.01 (KIC 9018021) is DR25's 17.168095 d (13.04 h, 143 ppm, S/N 8.1, impact
0.999). DR24 gives 51.510703 +- 0.004772 d, epoch BKJD 168.8474 +- 0.0175, 4.66 h, 310.7 ppm, S/N 7.6.
Lissauer et al. 2024 give 51.4998764 d (no epoch in their table). If the period is 51.5 d, only DR25 events
n = 2 mod 3 (counting from the DR24 epoch) hold a transit. If it is 17.17 d, all three groups do.

## Method

thirds_lc 0.1.0 (new, 12 unit tests on synthetic light curves; published with the results) calls the
published kepler_alias 0.3.0. It fetches that tool from this repository's main branch and records its sha256.
It reads the Kepler long-cadence PDCSAP light curves (quality 0) from MAST. For each run name=P@T0/duration
it measures every epoch's box depth: the mean deficit of the central 70 % of the duration below a line
fitted to points 1-3 durations from the centre. It then combines the epochs of each group n mod 3, with the
error scaled by sqrt(reduced chi2) when that exceeds 1, and applies kepler_alias.verdict with the long group 2.
That verdict is long_period_real if group 2 is >= 5 sigma and groups 0 and 1 are within 3 sigma of zero, and
short_period_real if all three are >= 5 sigma and agree pairwise within 3 sigma. No other KOI is on this star,
so nothing is masked.

| run | P (d) | T0 (BKJD) | duration (h) | role |
|---|---|---|---|---|
| **A** | 17.168095 (DR25) | 134.51121 (DR24 epoch - 2 P) | 13.04 | **primary** |
| B | 17.1702343 (DR24 / 3) | 134.5069313 | 13.04 | descriptive |
| C | 17.168095 | 134.637329 (DR25's own) | 13.04 | descriptive (the pixel test's ephemeris) |
| L | 17.1666255 (Lissauer / 3) | 134.5141491 | 13.04 | descriptive |
| D | 17.1702343 | 134.5069313 | 4.66 | descriptive (narrow, DR24's duration) |
| N | 17.168095 | 143.0952575 (A + P / 2) | 13.04 | null |

Why A is the primary. DR25's period sits between the two long-period values (3 P is 0.0064 d per cycle
shorter than DR24's and 0.0044 d longer than Lissauer's). With the well-measured DR24 epoch, the worst drift by
the last cycle (27) is 4.2 h. In the 13.04 h window a 4.66 h transit that far off still has >= 58 % of its
length in the core, and nothing in the baseline (which starts 13.04 h out). The narrow window D has a core of
only +-1.63 h, so drift can empty it. That is why D only describes. If the period is 17.17 d with DR25's 13 h
transit, A's centres are 3.0 h before DR25's. So 88 % of A's 9.13 h core lies inside each transit, and the
baseline stays clear of it.

Expected sizes (our estimate from the catalogue S/N; actual noise may differ). One epoch's error in A is about
150-200 ppm, so one group of ~25 epochs is ~30-40 ppm. If 51.5 d: group 2 is ~110-160 ppm, groups 0 and 1 ~0.
If 17.17 d: all three are ~110-135 ppm. **So the 5 sigma verdict will probably not decide.** The mean of
groups 0 and 1 (O, error e_O = sqrt(e0^2 + e1^2) / 2) separates the two models by ~4 sigma. So we also fix
a "lean" rule now.

## Decision rules (fixed now)

- **Outcome** = A's verdict: long_period_real -> "51.5 d", short_period_real -> "17.17 d", else "inconclusive".
- **Lean** (from A, worked by hand from its group depths and errors; reported even if the outcome decides):
  - "leans 51.5 d": O / e_O < 1, D2 / e2 >= 2.5, and the contrast D2 - O >= 2 sigma (sqrt(e2^2 + e_O^2));
  - "leans 17.17 d": O / e_O >= 3 and |D2 - O| < 2 sigma;
  - "no lean": anything else.

## Predictions

1. fetch_tool reports 0.3.0. All kepler_alias tests and all 12 thirds_lc tests pass.
2. At least 15 light-curve files are read. Every group of run A has at least 18 epochs.
3. Outcome **"inconclusive"** (our prior ~70 %; "51.5 d" ~15 %, "17.17 d" ~15 %).
4. Lean **"leans 51.5 d"** (prior ~55 %; "leans 17.17 d" ~25 %, "no lean" ~20 %). Reasons: DR24 and Lissauer
   agree; at 17.17 d a 13 h transit is longer than the ~9 h maximum for a central transit of a 0.18 g/cm3
   star; the pixel test's only group above 3 sigma was the DR24 one. Against it: DR25's depth x duration
   per event (1,395 ppm h) is close to DR24's (1,448 ppm h), as if every 17.17 d event held a dip.
5. Null run N: every group |S/N| < 3 and its contrast |S/N| < 2.
6. Exploratory, no prediction: runs B, C, L and D; first and second halves; per-epoch depths.

## Interpretation, fixed now

- "51.5 d", or "inconclusive" with "leans 51.5 d": the light curve supports DR24 and Lissauer et al., and the
  Archive's default 17.168 d looks like a one-third alias. Only the outcome "51.5 d" would go into a
  correction note for the Archive (held for Sheehan's approval). A lean is reported as a lean.
- "17.17 d" or "leans 17.17 d": the light curve supports DR25. Lissauer et al.'s table period would then be
  the one to question.
- Otherwise we claim nothing.
- None of these says whether the signal is a planet. It stays an S/N ~8 candidate.

Limits: PDCSAP detrending can shave long, shallow transits. The 1-3 duration baseline is a straight line.
Red noise is handled only through the reduced-chi2 scaling. The expected sizes above are our estimates,
not measurements.
