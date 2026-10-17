# Results: the Kepler pixel results with empirical error bars (kepler_pixels 0.4.0): 7 of 7 held

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Code Apache-2.0, text CC BY 4.0. Pre-registration: findings/2026-10-17-pixels-scatter-prereg.md (committed
before the job ran). Raw outputs: results/2026-10-17-kepler-pixels-0.4.0/. Job pixels-scatter-v1 ran
2026-10-17 12:43-12:46 UTC: numpy 2.1.3, astropy 6.1.4, Python 3.12, same cached target pixel files.

## Score

| # | Prediction | Result | Held? |
|---|---|---|---|
| 1 | All 18 unit tests pass | Ran 18 tests, OK | yes |
| 2 | Nine runs reproduce `depth_ppm`, `depth_err_ppm` (0.5 ppm) and `verdict` (exactly) | All 36 phase rows identical to kepler-pixels-v3 and orphan-pixels-v1 to the last printed digit | yes |
| 3 | `mean_ppm` within 2 ppm and `mean_err_ppm` within 15 % of the hand check | All 13 values agree within 0.1 ppm and 1 % (e.g. Kepler-1129 c phase 0: 320.66 +- 143.71 vs 320.7 +- 144; K01922.02 phase 0.25 mean -3.75 vs -3.8) | yes |
| 4 | Phase-0 Birge ratio > 2.0 for K02167.02 masked and Kepler-1129 c; 1.2-2.2 for K01922.02 masked and Kepler-1016 c | 2.77, 2.53; 1.61, 1.42 | yes |
| 5 | `verdict_scaled` = `no_signal` for Kepler-1129 c phases 0.25 and 0.5 and K01922.02 phase 0.25 (both runs) | scaled SNR 1.86, 2.27, 2.31, 2.31; all `no_signal` | yes |
| 6 | Period corrections survive: Kepler-1301 b phase 0.5 scaled SNR >= 5, `on_target`; KOI-4893.01 phase 0 >= 5, 0.5 `no_signal`; KOI-4711.01 phase 0.5 >= 5, 0 `no_signal` | 13.0 `on_target`; 8.76 and `no_signal`; 7.43 and `no_signal` (phase 0 scaled SNR 2.07) | yes |
| 7 | K01922.02 masked phase 0 at least 5 scaled sigma below 319 ppm | 32.2 +- 24.7 ppm: (319 - 32.2) / 24.7 = 11.6 sigma | yes |

Predictions 2 and 3 are consistency checks (same data, same code path; the hand values came from the same
quarters.csv files), so they test the code, not the sky. Predictions 4-7 are the substantive ones.

## The numbers we now report (Birge-scaled depth errors)

| Run | Phase 0 | Phase 0.5 | Phase 0.25 | Phase 0.75 |
|---|---|---|---|---|
| Kepler-1301 b, at 9.082 d | 227.9 +- 13.6, `on_target` | 204.9 +- 15.7, `on_target` | -28.8 +- 22.0 | 20.5 +- 28.1 |
| KOI-4893.01, at 2 x 6.588 d | 275.4 +- 31.5, `on_target` | -2.5 +- 23.2 | 25.0 +- 34.4 | 11.7 +- 32.7 |
| KOI-4711.01, at 2 x 4.364 d | 45.3 +- 21.9 | 224.9 +- 30.3, `on_target` | 3.4 +- 24.4 | -13.3 +- 30.1 |
| K01922.02 masked | 32.2 +- 24.7 | -7.3 +- 20.3 | 51.4 +- 22.2 | -27.2 +- 20.1 |
| K01922.02, Kepler-1016 c left in | 190.5 +- 35.1, `on_target` | (same as masked) | | |
| Kepler-1016 c (control) | 1143.3 +- 37.5, `on_target` | 60.1 +- 31.8 | -24.2 +- 35.4 | 2.1 +- 30.2 |
| K02167.02 masked | 8.9 +- 28.7 | 1.2 +- 15.2 | -20.6 +- 20.5 | -10.7 +- 28.4 |
| Kepler-1129 c (control) | 419.6 +- 87.5, `unclear` | 178.1 +- 78.4 | 181.0 +- 97.3 | -2.7 +- 101.5 |

Depths in ppm against all light in the stamp; unlabelled cells are `no_signal`.

## Reading, as pre-registered

5-7 held, so `verdict_scaled` is now the verdict we report.

- **Kepler-1301 b**: the events halfway between the catalogued ones are as deep as the catalogued ones
  (ratio 0.90 +- 0.09) and on the target, so the signal repeats at **4.541 d**, not 9.082 d.
- **KOI-4893.01**: alternate events differ by 278 +- 39 ppm (7.1 sigma); the period is **13.175 d** (or a
  multiple), not 6.588 d.
- **KOI-4711.01**: alternate events differ by 180 +- 37 ppm (4.8 sigma); the period is **8.728 d** with
  the deep events at the catalogued T0 + 4.364 d. The weak "alternate" events we mentioned earlier
  (45 ppm) are now only 2.1 sigma, so we no longer read them as a hint of an eclipsing binary.
- **K01922.02**: outside Kepler-1016 c's transits there is no dip at the catalogued 15.095 d ephemeris at
  the depth first reported (11.6 sigma below it), and with Kepler-1016 c left in, the dip matches every 7th
  event being a Kepler-1016 c transit (190.5 +- 35.1 ppm against 163.3 expected). We read it as a likely
  1/7 alias of Kepler-1016 c. Lissauer et al. 2024 (PSJ 5, 152) already reject it on S/N (status SPNN,
  S/N 4.1); this adds a reason, not a new rejection.
- **K02167.02**: still not claimed. Its control (Kepler-1129 c) stays `unclear`, as said in advance.
  Lissauer et al. 2024 also reject it on S/N (SPNN, S/N 1.9).

These three period readings are not in Lissauer et al. 2024 Table 1, which lists KOI-2643.01, 4711.01 and
4893.01 as PPPP at the catalogued periods (checked row by row; see findings/2026-10-17-lissauer-check.md).

## Not predicted (post hoc; not tested)

- Kepler-1129 c's phase-0 control is `unclear` because of the offset test, which 0.4.0 leaves at formal
  errors: chi2 against zero offset is 16.8 (limit 11.8). With the offset errors also scaled by its Birge
  ratio (2.53), chi2 would be about 2.6 and the control would pass, but its depth SNR would still be only
  4.8. With one transit per quarter this star is a poor control either way. If the control had passed,
  K02167.02's masked depth (8.9 +- 28.7) would sit only 2.8-3.8 sigma below the 89-117 ppm expected if it
  were real, short of the 5 sigma we would want, so it would still not be claimed.
- In the K01922.02 run with Kepler-1016 c left in, the phase-0 Birge ratio rises from 1.61 to 2.54. That
  fits the alias reading (quarters that contain a Kepler-1016 c transit are deep, the rest are not), but
  it was not pre-registered.

## Limits

The Birge ratio rests on 11-17 quarters and is itself uncertain by about 20 %. One scale factor per phase
assumes the extra scatter is the same in every quarter. Depths are not corrected for crowding. No blended
eclipsing binary is excluded for any of the three period readings. K01922.02 is ruled out at its
catalogued ephemeris at the Q1-Q6 depth (382 ppm), not at the 85 ppm of the Q1-Q8 table (1.6 sigma) or at
nearby periods.
