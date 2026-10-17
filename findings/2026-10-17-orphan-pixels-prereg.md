# Pre-registration: are two stale Kepler candidates just echoes of a sibling planet? (kepler_pixels 0.3.0)

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Code Apache-2.0, text CC BY 4.0. Committed **before** the job runs; scored in public, misses included.

## Why

koi_dupes 0.1.0 (findings/2026-10-17-koi-dupes-results.md) flagged two CANDIDATE KOIs whose catalogued
ephemeris puts one transit in every k on the transits of a confirmed planet on the same star:

| KOI (CANDIDATE) | P (d) | T0 (BKJD) | dur (h) | depth (ppm) | sibling | P (d) | depth (ppm) | k | P ratio | offset (d) |
|---|---|---|---|---|---|---|---|---|---|---|
| K02167.02 | 6.95787 | 359.007 | 4.537 | 182.3 | Kepler-1129 c (K02167.03) | 76.5369531 | 652.2 | 11 | 11.000055 | -0.030 |
| K01922.02 | 15.09521323 | 139.474359 | 3.41 | none (382 in Q1-Q6, 85 in Q1-Q8) | Kepler-1016 c (K01922.03) | 105.6552651 | 1366.9 | 7 | 6.99926 | +0.053 |

Both .02 KOIs first appear in the Q1-Q6 KOI table, before their sibling had a KOI of its own, and both
are "orphans": not in DR25, parameters still from the Q1-Q16 table, CANDIDATE inherited by the DR25
supplemental table with no score or SNR. Our reading: each was the pipeline's detection of the
sibling's transits folded at 1/k of the true period. If so, outside the sibling's transits there is
nothing at the .02 ephemeris.

## Method

kepler_pixels 0.3.0 = 0.2.0 plus `--unmask` (KOIs left out of the mask; with no `--unmask` the output is
that of 0.2.0). Long-cadence target pixel files, Q1-Q17, phases 0, 0.5 and nulls 0.25, 0.75. The
reference is a nominal one pixel (3.98") north, so `on_target` means "consistent with no shift and not
with a one-pixel shift". Six runs:

- **masked**: the .02 KOI with every other KOI on the star masked (default), so the sibling's transits
  are cut out.
- **control**: the sibling (K02167.03, K01922.03) with the .02 KOI unmasked (otherwise the .02 ephemeris
  would mask the sibling's own transits).
- **unmasked**: the .02 KOI with the sibling not masked.

Sensitivity, worked out before the run: the depth SNR of a box signal scales as depth x
sqrt(events x duration). If K02167.02 were real at 182.3 ppm with ~180 events of 4.54 h, its expected
SNR is about 0.85 x that of Kepler-1129 c (652 ppm, 16 transits of 5.57 h). For K01922.02 at its Q1-Q6
depth of 382 ppm (~85 events of 3.41 h), it is about 0.45 x that of Kepler-1016 c (1367 ppm, 12 transits
of 9.39 h); at 85 ppm the test could not tell, so for K01922.02 only the Q1-Q6 depth level is tested.

## Predictions

1. All 16 unit tests pass.
2. At least 14 quarterly files are read for each star, with no file errors in any run.
3. Controls: Kepler-1129 c and Kepler-1016 c at phase 0 have depth SNR >= 10 and verdict `on_target`;
   their null phases 0.25 and 0.75 are `no_signal`.
4. K02167.02 masked: phase 0 is `no_signal` (SNR < 3) with depth below 61 ppm (a third of 182.3).
5. K01922.02 masked: phase 0 is `no_signal` (SNR < 3) with depth below 127 ppm (a third of 382).
6. Mechanism: in the unmasked runs, the .02 phase-0 depth is between 0.5 and 2.0 times the control's
   phase-0 depth divided by k (11 for K02167.02, 7 for K01922.02).
7. Null phases 0.25 and 0.75 are `no_signal` in all four .02 runs.

How it will be read: if 3, 4 and 5 hold, the two KOIs show no signal of their own in the pixels outside
the sibling's transits, and they will be written up as likely period aliases of Kepler-1129 c and
Kepler-1016 c whose CANDIDATE label is stale. If a masked .02 run gives SNR >= 5 and `on_target`, that
KOI has a signal of its own and the alias reading is wrong for it. If a control fails, the test says
nothing about that star.

Limits known in advance: pixel depths are against all light in the stamp (diluted, not crowding-corrected);
the .02 ephemerides come from old, short data sets, and K01922.02's drifts by about 0.16 d against the
sibling over the mission; a null result rules out a signal at the catalogued ephemeris, not at every
nearby period.
