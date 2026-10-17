# Results: Kepler pixel test of three period leads (kepler_pixels 0.2.0): 12 of 12 predictions held

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Code Apache-2.0, text and data CC BY 4.0. Predictions: findings/2026-10-17-pixels-dupes-prereg.md
(committed before the run). Outputs: results/2026-10-17-kepler-pixels-0.2.0/.

Run: compete job kepler-pixels-v3, 2026-10-17 07:33-07:36Z, python 3.12, numpy 2.1.3, astropy 6.1.4
(versions printed by the job). The earlier attempt (v2) measured nothing because numpy 2.5 broke
astropy's FITS reader; v3 ran identical code with pinned versions. Errors are 1 sigma.

## Kepler-1301 b (KOI-2643.01, KIC 6933567), catalogued 9.0823 d

| phase | quarters | events | depth (ppm) | offset E (") | offset N (") | chi2 vs 0 | chi2 vs neighbour | verdict |
|---|---|---|---|---|---|---|---|---|
| 0 | 17 | 146 | 227.9 +- 10.6 | +0.21 +- 0.16 | +0.33 +- 0.23 | 3.8 | 66.8 | on_target |
| 0.5 | 17 | 143 | 204.9 +- 9.7 | +0.38 +- 0.28 | -0.14 +- 0.28 | 2.0 | 37.0 | on_target |
| 0.25 | 17 | 137 | -28.8 +- 11.1 | | | | | no_signal |
| 0.75 | 17 | 139 | +20.5 +- 10.3 | | | | | no_signal |

Neighbour calibration (Gaia DR3 source at +2.69" E, -1.85" N): (+2.19, -1.95)" = 2.93".

| # | Prediction | Result | |
|---|---|---|---|
| 1 | All unit tests pass | 15 of 15 | held |
| 2 | >= 14 quarterly files read without error | 17, no errors | held |
| 3 | Phase 0: 200-350 ppm, SNR >= 5, on_target | 228 ppm, SNR 21.4, on_target | held |
| 4 | Phase 0.5: 120-300 ppm, on_target | 205 ppm, SNR 21.1, on_target | held |
| 5 | Nulls 0.25 / 0.75 no_signal | -2.6 and +2.0 sigma | held |
| 6 | Calibration offset 2.0-3.5" | 2.93" | held |

The dips halfway between Kepler-1301 b's catalogued transits come from the target's pixels, not from
the 3.3"-away neighbour, and are as deep as the catalogued ones: ratio 0.90 +- 0.06 (difference
23 +- 14 ppm, 1.6 sigma). The two nulls are a little wide (chi2 10.8 for 2 values), so the quoted errors
may be about 2x too small; with them doubled, both dips are still about 10 sigma and their depths agree.

What this means: the transit signal of Kepler-1301 b repeats every **4.541 d**, half the 9.0823 d the
Archive lists, and both sets of dips come from the target star's pixels. This agrees with the Kepler
pipeline's own DR25 detection (TCE 1 of KIC 6933567: 4.54116 d, 235 ppm; Thompson et al. 2018), the
light-curve test (kepler_alias 0.2.0) and the stellar-density test (density_alias), which leaned toward
half the period. Earlier work used 9.08 d: the validation by Morton et al. 2016, and ExoMiner's TCE
list (Valizadegan et al. 2022) as we read it in an earlier run. What it does not
exclude: an eclipsing binary blended within about 1" of the target, with two equal eclipses at 9.08 d.
The planet's validation at 9.08 d would need redoing at 4.54 d; we have not done that.

## KOI-4893.01 (KIC 11970050), catalogued 6.5875 d, tested at 2 x = 13.1751 d

| phase | quarters | events | depth (ppm) | offset E (") | offset N (") | chi2 vs 0 | chi2 vs 1 px N | verdict |
|---|---|---|---|---|---|---|---|---|
| 0 | 16 | 92 | 275.4 +- 20.5 | -0.27 +- 0.28 | +0.38 +- 0.36 | 2.0 | 25.9 | on_target |
| 0.5 | 17 | 93 | -2.5 +- 23.2 | | | | | no_signal |
| 0.25 | 17 | 97 | +25.0 +- 19.6 | | | | | no_signal |
| 0.75 | 17 | 94 | +11.7 +- 20.2 | | | | | no_signal |

| # | Prediction | Result | |
|---|---|---|---|
| 7 | Exactly one of 0 / 0.5 at SNR >= 3 and 150-450 ppm; the other SNR < 3 and < 1/3 of it | 0: 275 ppm, 13.5 sigma; 0.5: -2 ppm, -0.1 sigma | held |
| 8 | Deep group on_target | on_target | held |
| 9 | Nulls no_signal | +1.3 and +0.6 sigma | held |

Every other catalogued transit of KOI-4893.01 is missing: the difference between the two groups is
278 +- 31 ppm (9 sigma). The signal repeats every **13.175 d** (or a multiple; 26.35 d was not tested),
not 6.5875 d, and it is on the target's pixels. The light-curve test gave the same split (314 +- 47
vs 22 +- 43 ppm), and the DV secondary census (findings/2026-10-17-dv-alias-census.md) had already
flagged this KOI. With half its catalogued events empty, the catalogued depth and radius are also too
small, by roughly a factor of 2 in depth.

## KOI-4711.01 (KIC 8355131), catalogued 4.3638 d, tested at 2 x = 8.7277 d

| phase | quarters | events | depth (ppm) | offset E (") | offset N (") | chi2 vs 0 | chi2 vs 1 px N | verdict |
|---|---|---|---|---|---|---|---|---|
| 0 | 17 | 136 | 45.3 +- 15.0 | +1.9 +- 2.5 | -2.5 +- 2.6 | 1.5 | 8.2 | unclear |
| 0.5 | 17 | 145 | 224.9 +- 14.4 | +0.47 +- 0.43 | +0.13 +- 0.41 | 1.3 | 37.4 | on_target |
| 0.25 | 17 | 148 | +3.4 +- 14.4 | | | | | no_signal |
| 0.75 | 17 | 147 | -13.3 +- 15.0 | | | | | no_signal |

| # | Prediction | Result | |
|---|---|---|---|
| 10 | One of 0 / 0.5 at SNR >= 3 and 130-400 ppm; the other below half of it | 0.5: 225 ppm, 15.7 sigma; 0: 45 ppm (0.20 of it) | held |
| 11 | Deep group on_target | on_target | held |
| 12 | Nulls no_signal | +0.2 and -0.9 sigma | held |

Alternate events differ by 180 +- 21 ppm (8.7 sigma), so the catalogued 4.3638 d is not the period;
the signal repeats every **8.728 d**, and the deep events are on the target's pixels. The shallow group
is not empty: 45 +- 15 ppm (3.0 sigma), as the light-curve test also hinted (69 +- 29 ppm). If that is
real, the pattern is a deep and a shallow eclipse alternating, which is what an eclipsing binary at
8.728 d looks like. Either way, the catalogued period is wrong; whether KOI-4711.01 is a planet is open.

## Limits

- An `on_target` verdict says where the light comes from, within about 1"; it is not a disposition.
- For KOI-4893.01 and KOI-4711.01 no real neighbour was modelled; the reference is a nominal one pixel
  north.
- Pixel depths are measured against all light in the stamp and are not crowding-corrected, so they are
  smaller than catalogue depths (here 0.6-0.8 of the expected value).
- These are results of code written and run by AI agents; nobody outside has checked them yet.

## What next

The three period corrections (Kepler-1301 b to 4.541 d, KOI-4893.01 to 13.175 d, KOI-4711.01 to
8.728 d) are now supported by two independent kinds of evidence: the light curve and the pixels. A
correction note to the NASA Exoplanet Archive has been drafted and waits for a person at Munim, Inc.
to review it before it is sent.
