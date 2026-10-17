# Results: are two stale Kepler candidates echoes of a sibling planet? (kepler_pixels 0.3.0): 5 of 7 held

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Code Apache-2.0, text CC BY 4.0. Pre-registration: findings/2026-10-17-orphan-pixels-prereg.md (committed
before the job ran). Raw outputs: results/2026-10-17-kepler-pixels-0.3.0/. Job orphan-pixels-v1 ran
2026-10-17 08:39-08:42 UTC: numpy 2.1.3, astropy 6.1.4, Python 3.12.

## Score

| # | Prediction | Result | Held? |
|---|---|---|---|
| 1 | All 16 unit tests pass | 16 OK | yes |
| 2 | >= 14 quarterly files per star, no file errors | KIC 6041734: 14 (Q4-Q17); KIC 9411166: 17 (Q1-Q17); no errors | yes |
| 3 | Controls: phase 0 SNR >= 10 and `on_target`; nulls 0.25, 0.75 `no_signal` | Kepler-1016 c: 1143 +- 26 ppm, SNR 43.3, `on_target`, nulls `no_signal`. **Kepler-1129 c: 420 +- 35 ppm, SNR 12.1 but `unclear`** (offset -1.83 +- 0.46" E, +0.41 +- 0.43" N; chi2 vs 0 = 16.8 > 11.8), and **null 0.25 = 181 +- 28 ppm, SNR 6.5, `on_target`** | **no** |
| 4 | K02167.02 masked, phase 0: `no_signal`, < 61 ppm | 8.9 +- 10.4 ppm, SNR 0.86 | yes |
| 5 | K01922.02 masked, phase 0: `no_signal`, < 127 ppm | 32.2 +- 15.4 ppm, SNR 2.10 | yes |
| 6 | Unmasked .02 depth within 0.5-2.0 x control / k | K02167.02: 48.5 vs 419.6 / 11 = 38.1 (ratio 1.27); K01922.02: 190.5 vs 1143.3 / 7 = 163.3 (ratio 1.17) | yes |
| 7 | Nulls 0.25, 0.75 `no_signal` in all four .02 runs | K02167.02: yes. **K01922.02 phase 0.25: 51.4 +- 14.8 ppm, SNR 3.47, `unclear`** in both runs | **no** |

Not predicted: Kepler-1129 c phase 0.5 also came out 178 +- 26 ppm, `on_target`.

## Reading, as pre-registered

The rule was: if 3, 4 and 5 hold, both KOIs are written up as likely aliases; if a control fails, the test
says nothing about that star. Prediction 3 failed for Kepler-1129 c, so **this test says nothing about
K02167.02**, even though its masked run shows no dip. For **K01922.02** the control (Kepler-1016 c) and
prediction 5 held: outside Kepler-1016 c's transits there is no dip at the catalogued 15.095 d ephemeris at
the depth first reported (382 ppm in the Q1-Q6 table), and with Kepler-1016 c's transits left in, the
dip is the size expected from every 7th event being a Kepler-1016 c transit (prediction 6). That supports
reading K01922.02 as a 1/7 alias of Kepler-1016 c whose CANDIDATE label is stale. As stated in advance, it
cannot rule out a real signal near the 85 ppm of the Q1-Q8 table.

## Why the two misses happened (post hoc, not pre-registered)

The tool weights each quarter by 1 / var(a), where var(a) is the formal error of that quarter's image fit,
and its depth error is 1 / sqrt(sum of weights). The per-quarter depths in quarters.csv scatter more than
those formal errors allow. Hand-computed from quarters.csv (unweighted mean of quarter depths +- standard
error; Birge ratio = sqrt(chi2 / (n - 1)) of the quarter depths about the weighted mean):

| run, phase | weighted (tool) | unweighted mean +- SE | Birge ratio |
|---|---|---|---|
| Kepler-1129 c, 0 | 420 +- 35 | 321 +- 144 | ~2.5 |
| Kepler-1129 c, 0.25 | 181 +- 28 | -36 +- 100 | |
| Kepler-1129 c, 0.5 | 178 +- 26 | 178 +- 120 | |
| K02167.02 masked, 0 | 8.9 +- 10.4 | 11.5 +- 38 | ~2.8 |
| K01922.02 masked, 0 | 32.2 +- 15.4 | 26 +- 31 | ~1.6 |
| K01922.02 masked, 0.25 | 51.4 +- 14.8 | -4 (17 quarters) | |
| Kepler-1016 c, 0 | 1143 +- 26 | | ~1.4 |

- Kepler-1129 c transits about once per quarter, so each quarter's depth rests on one event. At its null
  phases the single-event depths run from -1003 to +1342 ppm (scatter ~360-450 ppm against formal errors
  of ~100 ppm), and the weighting leaned on a few quarters with small formal errors. With the quarters
  weighted equally, nothing is left at phases 0.25 and 0.5.
- An internal check agrees. Kepler-1129 c's period is 11.000055 times K02167.02's and its transits sit
  at K02167.02's phase 0, so c's phase-0.25 and 0.5 epochs are a subset of K02167.02's phase-0.75 and 0.5
  epochs. If 180 ppm were real there, the K02167.02 runs would show about +18 ppm at those phases; they
  show -10.7 +- 9.2 and +1.2 +- 11.1.
- K01922.02's phase-0.25 excess has the same cause: quarters with small formal errors happen to be
  positive; the unweighted mean is about -4 ppm.

So the formal depth errors are too small by a star-dependent factor of ~1.4-2.8. This was suspected
earlier (Kepler-1301 b's nulls sat at +-2-2.6 sigma) and is now measured.

With empirical errors: K01922.02's masked depth (unweighted 26 +- 31 ppm; weighted 32 +- 25 with the
Birge-scaled error) sits far below the 319 ppm expected if it were real at 382 ppm (diluted by the 0.84
measured on Kepler-1016 c: 1143 / 1367). K02167.02's (11.5 +- 38 ppm) sits about 3-5 sigma below the
117-153 ppm expected if it were real, depending on the dilution, which Kepler-1129 c's noisy control
pins down poorly. We do not claim K02167.02.

## The earlier pixel results, rechecked the same way

The same hand check on results/2026-10-17-kepler-pixels-0.2.0/*-quarters.csv (findings/2026-10-17-pixels-results.md):

| KOI | catalogued-phase depth | other-phase depth | published | with empirical errors |
|---|---|---|---|---|
| Kepler-1301 b (x1) | phase 0: 238 +- 17 | phase 0.5: 204 +- 15 | ratio 0.90 +- 0.06 | ratio 0.85 +- 0.09 |
| KOI-4893.01 (x2) | phase 0: 274 +- 36 | phase 0.5: -13 +- 20 | 275 +- 20 vs -2 +- 23 | difference 287 +- 41 (7 sigma) |
| KOI-4711.01 (x2) | phase 0: 44 +- 24 | phase 0.5: 209 +- 28 | 45 +- 15 vs 225 +- 14 | difference 165 +- 37 (4.5 sigma) |

All three period readings still hold (4.541 d, 13.175 d, 8.728 d), but the earlier write-up overstated
their significance by a factor of about 1.4-2. The earlier findings stay as published; this note corrects
their error bars.

## Next

kepler_pixels 0.4.0 reports Birge-scaled errors, unweighted means and a scaled verdict next to the 0.3.0
fields. A re-run of all nine pixel runs is pre-registered in findings/2026-10-17-pixels-scatter-prereg.md,
so the hand numbers above are checked by code.

Limits: pixel depths are against all light in the stamp (not crowding-corrected); hand-computed values are
rounded; the K01922.02 result rules out a signal at its catalogued ephemeris at the Q1-Q6 depth, not at
every nearby period; no blended binary is excluded.
