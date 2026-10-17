# Pre-registration: do the Kepler pixel results survive empirical error bars? (kepler_pixels 0.4.0)

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Code Apache-2.0, text CC BY 4.0. Committed **before** the job runs; scored in public, misses included.

## Why

The orphan-pixels test (findings/2026-10-17-orphan-pixels-results.md, 5 of 7 held) showed that the
per-quarter depths scatter more than their formal fit errors allow, by a star-dependent factor of about
1.4-2.8. Both misses (a 6.5 sigma "signal" at a null phase of Kepler-1129 c, a 3.5 sigma one for K01922.02)
went away when we checked them by hand with the quarters weighted equally. The same hand check kept all three
published period corrections (Kepler-1301 b 4.541 d, KOI-4893.01 13.175 d, KOI-4711.01 8.728 d) but at
lower significance. kepler_pixels 0.4.0 does this in code, so the hand numbers can be checked.

## Method

0.4.0 = 0.3.0 plus, per phase: the Birge ratio sqrt(chi2 / (n - 1)) of the quarter depths about their
weighted mean; the depth error scaled by max(1, Birge); the SNR and a `verdict_scaled` that use the scaled error
(offset tests unchanged); and the unweighted mean of the quarter depths with its standard error. All 0.3.0
fields are computed as before. Same cached target pixel files, same nine runs as kepler-pixels-v3 (K02643.01
x1; K04893.01 x2; K04711.01 x2) and orphan-pixels-v1 (K02167.02 masked and unmasked, Kepler-1129 c control,
K01922.02 masked and unmasked, Kepler-1016 c control).

## Predictions

1. All 18 unit tests pass (16 old, 2 new).
2. Reproducibility: in all nine runs, every phase's `depth_ppm`, `depth_err_ppm` and `verdict` match the
   earlier runs to within 0.5 ppm and exactly for verdicts.
3. The code agrees with the hand check: `mean_ppm` is within 2 ppm, and `mean_err_ppm` within 15 %, of these
   values: Kepler-1301 b phase 0 238.2 +- 16.6, 0.5 203.5 +- 15.2; KOI-4893.01 0 273.9 +- 36, 0.5 -13.1 +- 19.6;
   KOI-4711.01 0 44.0 +- 23.7, 0.5 208.9 +- 28; K02167.02 masked 0 11.5 +- 38; Kepler-1129 c 0 320.7 +- 144,
   0.25 -35.9 +- 100, 0.5 178.1 +- 120; K01922.02 masked 0 26.3 +- 30.6 (and 0.25 mean -3.8, within 2 ppm).
4. Birge ratio at phase 0 is above 2.0 for K02167.02 masked and Kepler-1129 c (hand: 2.8, 2.5), and between
   1.2 and 2.2 for K01922.02 masked and Kepler-1016 c (hand: 1.6, 1.4).
5. The two misses go away: `verdict_scaled` is `no_signal` for Kepler-1129 c phases 0.25 and 0.5, and for
   K01922.02 phase 0.25 in both .02 runs (hand: scaled SNR 1.9, 2.3, 2.3).
6. The three period corrections survive: Kepler-1301 b phase 0.5 has scaled SNR >= 5 and `verdict_scaled`
   `on_target`; KOI-4893.01 (x2) phase 0 scaled SNR >= 5, phase 0.5 `no_signal`; KOI-4711.01 (x2) phase 0.5
   scaled SNR >= 5, phase 0 `no_signal` (hand: scaled SNR about 2.0).
7. K01922.02 masked phase 0 sits at least 5 scaled sigma below 319 ppm (its Q1-Q6 depth of 382 ppm diluted by
   0.84, Kepler-1016 c's pixel / catalogue depth ratio). Hand: about 11.6 sigma.

How it will be read: if 5-7 hold, `verdict_scaled` becomes the verdict we report, the three period corrections
stand at their scaled significance, and K01922.02 is written up as a likely 1/7 alias of Kepler-1016 c. If 6
fails for a KOI, that correction is downgraded in public. If 3 fails, the hand check in the orphan-pixels
results is wrong and gets a correction. K02167.02 stays unclaimed whatever happens, because its control failed.

Limits known in advance: the Birge ratio is noisy with 11-17 quarters (its own fractional error is about
1 / sqrt(2 (n - 1)), roughly 20 %); scaling by one factor assumes the excess scatter is the same in every
quarter; depths are against all light in the stamp (not crowding-corrected); no blended binary is excluded.
