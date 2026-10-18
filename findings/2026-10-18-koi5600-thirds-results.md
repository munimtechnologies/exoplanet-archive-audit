# Results: KOI-5600.01 pixel test of 17.17 d against 51.50 d is inconclusive (one prediction missed)

MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no human has checked this yet.
Text and data CC BY 4.0. Scores findings/2026-10-17-koi5600-thirds-prereg.md (committed before the job ran)
against job koi5600-thirds-v1, which ran 2026-10-18 02:04-02:06 UTC. Raw output:
results/2026-10-18-koi5600-thirds-kepler_pixels-0.4.0/.

## Score against the pre-registration

| # | prediction | result | held? |
|---|---|---|---|
| 1 | fetch_tool reports 0.4.0; all 18 unit tests pass | 0.4.0 (kepler_pixels.py sha256 699c7a72...); 18 tests OK | yes |
| 2 | >= 15 of 17 quarter files read; groups 0, 1/3, 2/3 have 18-30 events each | 17 of 17, no errors; 23, 27 and 22 events | yes |
| 3 | outcome "51.5 d", in group 2/3 (prior ~60 %) | **inconclusive** (see below) | **no** |
| 4 | null groups 1/6, 1/2, 5/6 each \|D\| / s < 3 | 1.77, 1.29, 0.62 | yes |

Depths at 3 x 17.168095 = 51.504285 d (DR25 epoch BKJD 134.637329, DR25 duration 13.04 h). The error is
the tool's Birge-scaled one (`depth_err_scaled_ppm`); every group had 14 or more quarters.

| group | role | quarters | events | depth (ppm) | scaled error (ppm) | D / s | Birge |
|---|---|---|---|---|---|---|---|
| 0 | DR25 events n = 0 mod 3 | 17 | 23 | 107.5 | 74.6 | 1.44 | 5.43 |
| 1/3 | n = 1 mod 3 | 16 | 27 | -37.3 | 63.9 | -0.58 | 4.41 |
| 2/3 | n = 2 mod 3 (holds the DR24 epoch) | 15 | 22 | 192.2 | 43.7 | 4.40 | 4.38 |
| 1/6 | null | 14 | 22 | 102.6 | 57.9 | 1.77 | 4.72 |
| 1/2 | null | 16 | 26 | -54.9 | 42.4 | -1.29 | 4.07 |
| 5/6 | null | 16 | 25 | 35.2 | 56.5 | 0.62 | 4.89 |

Outcome rule, worked by hand:

- **"51.5 d"** needs D2 / s2 >= 3 (4.40, met), D0 / s0 < 2 (1.44, met), D1 / s1 < 2 (-0.58, met), and the contrast
  D2 - (D0 + D1) / 2 >= 3 sqrt(s2^2 + (s0^2 + s1^2) / 4). The contrast is 192.2 - 35.1 = 157.1 ppm; its
  error is sqrt(1906.2 + (5559.6 + 4088.7) / 4) = sqrt(4318.3) = 65.7 ppm, so the contrast is **2.39 sigma, below 3**. Not met.
- **"17.17 d"** needs the inverse-variance mean of the three groups >= 3 sigma (116.99 +- 32.46 ppm = 3.60 sigma,
  met), every pair to agree within 2 sigma (groups 1/3 and 2/3 differ by 229.5 ppm against 2 x 77.4 = 154.9; not met),
  and at least two groups >= 2 sigma (only one; not met). Not met.
- So the outcome is **"inconclusive"**. That was the alternative we named, not the outcome we predicted.
  Prediction 3 missed.

Per the pre-registration we claim nothing about the period. The pixels do not support the Archive's 17.17 d
over Lissauer et al.'s 51.50 d, or the reverse, at the thresholds we set.

## What else the output shows (exploratory, not scored)

- The only group above 3 sigma is 2/3, the one holding the DR24 epoch. Its dip centroid is on the target:
  0.21 +- 0.64" east, 0.26 +- 0.69" north of the out-of-transit light (chi2 vs zero 0.25). The neighbour
  test was a placeholder and is not read.
- Run B, at the catalogued 17.168 d period itself, finds **16.8 +- 37.6 ppm** at phase 0 (0.45 sigma), and
  23.0, 1.9 and -49.8 ppm at the null phases 0.5, 0.25 and 0.75. If every 17.17 d event held DR25's 143 ppm dip,
  phase 0 should be near 143 ppm, 3.4 scaled sigma above what was measured.
- **This estimator is not stable enough for an S/N ~8 signal.** Run B's phase 0 uses the same events as the
  three thirds groups together, yet gives 17 ppm where the thirds' inverse-variance mean is 117 ppm. The
  quarter depths scatter 4-5 times more than their formal errors (Birge 4.1-5.4 in every group, nulls
  included). Single quarters swing from -4,622 to +2,935 ppm. The weights come from how well each quarter's
  difference image fits a shifted copy of the star. That measures spatial residuals, not the time-series
  noise. So the weighted combination depends on which quarters happen to fit well. kepler_pixels was built
  for centroid offsets of clear signals (Kepler-1301 b at ~265 ppm, 6 sigma per half). It is not a
  substitute for a light-curve depth.

## What this changes

- The KOI-5600.01 question stays open. Nothing goes to the Archive helpdesk.
- The next test is photometric. We use the Kepler PDCSAP light curve with the published kepler_alias 0.3.0
  per-epoch box depth, on the DR24 ephemeris and at both catalogued durations. Pre-registered in
  findings/2026-10-18-koi5600-lightcurve-prereg.md before it runs.
- Lesson kept for this repo: do not use kepler_pixels depths to decide periods for signals below ~10 sigma.
  Use them only for the centroid of a group that is already detected in the light curve.
