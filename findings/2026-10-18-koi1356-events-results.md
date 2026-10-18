# KOI-1356.01: the Archive's 384.026 d and DR25's 393.719 d periods both predict flat epochs; the two transits are 787.43 d apart (koi1356-events-v1 scored)

By MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no person has checked it yet.
Text CC BY 4.0, code Apache-2.0. Scores the pre-registration `findings/2026-10-17-koi1356-events-prereg.md`
(committed 2026-10-17 before the job ran). Job: `koi1356-events-v1`, run 2026-10-18 04:23-04:25Z in a
sealed container (python:3.12, astropy 6.1.4, numpy 2.1.3). Outputs: `results/2026-10-18-koi1356-events-0.1.0/`.
Tool: `event_check.py` 0.1.0 (sha256 84c017aa...7cd4b007 in `fetched.json`) on the published
`kepler_alias.py` 0.3.0 (sha256 3cb894ca...5a0434). Light curves: Kepler long cadence, quality 0, PDCSAP,
all 17 quarters of KIC 7363829 (55,306 points, BKJD 131.51-1591.00). Box duration 13.5 h.

## Score: 7 of 7 predictions held

| # | Prediction | Result | Held |
|---|---|---|---|
| 1 | `kepler_alias` 0.3.0 fetched; its 20 tests and the 12 new tests pass | version 0.3.0; `Ran 20 tests ... OK`, `Ran 12 tests ... OK` (stderr.txt) | yes |
| 2 | 335.817 deep, S/N >= 20 | 6,068.9 +- 89.3 ppm, S/N 68.0, best centre 335.837 | yes |
| 3 | 1,123.255 deep | 6,083.1 +- 165.1 ppm, S/N 36.9, best centre 1,123.265 | yes |
| 4 | Q1-Q16 / Archive 384.026 d excluded | epoch 2 at 1,103.868: -162.7 +- 142.5 ppm, **absent** (37 sigma below the reference depth); epochs 1 and 3 no_data | yes |
| 5 | Lissauer 787.432 d supported; DR25 393.719 d excluded | Lissauer: both epochs deep, **supported**. DR25: epoch 3 at 1,516.974: 11.5 +- 157.1 ppm, **absent** (33.5 sigma); epoch 1 no_data | yes |
| 6 | 719.84 and 729.54 both no_data | both inside the 719.55-735.38 gap (Q7/Q8 roll and downlink) | yes |
| 7 | Blind search ranks 1-2 within 0.5 d of 335.8 and 1,123.3; rank 3's robust S/N < half of rank 2's | ranks 1-2 at 335.812 and 1,123.262; rank 3 at 970.312 has robust S/N 4.5 vs 32.1 | yes |

Sigma values: (D_ref - D) / hypot(err, err_ref) with D_ref = 6,068.9 +- 89.3 ppm. 1,103.868: 6,231.6 / 168.2 = 37.0.
1,516.974: 6,057.4 / 180.7 = 33.5.

## What the light curve shows

- Two transits of equal depth: 6,069 +- 89 and 6,083 +- 165 ppm (difference 14 +- 188 ppm), at best centres
  335.837 and 1,123.265 BKJD, 787.428 d apart. Lissauer et al. 2024 (arXiv:2311.00238, Table 1) list 787.43235 d.
- Every other epoch any catalogue predicts is either in a gap or flat:
  - 384.026 d (Q1-Q16 KOI tables and the Archive `cumulative` row, still its period on 2026-10-17): 719.84 in the
    15.8 d Q7/Q8 gap; **1,103.87 flat at 37 sigma**; 1,487.89 in the 11.5 d gap of 1,477.25-1,488.77
    (January 2013 reaction-wheel rest).
  - 393.719 d (DR25 TCE 007363829-01, "3 transits", S/N 82, Robovetter score 0.000, never a DR25 KOI): 729.54
    in the Q7/Q8 gap; **1,516.97 flat at 33.5 sigma**. So of DR25's three counted transits, one was in a gap and
    one was flat. That is what its minor flags said: INDIV_TRANS_MARSHALL_SKYE, INCONSISTENT_TRANS.
- Two-transit aliases 787.438 / n: n = 1 supported (statuses `dd`); n = 2 to 12 (393.7 d down to 65.6 d) all
  excluded, each by at least one flat epoch (`aliases.csv`).
- Blind search over the whole light curve (13.5 h box, 0.05 d steps, 25 best dips at least 1 d apart): the two
  transits are ranks 1 and 2 (S/N 66.3 and 37.6); the next dip, 576.9 +- 110.1 ppm at 970.312, is 9.5 % of the
  transit depth. There is no third dip of even 30 % of the transit depth anywhere in the 17 quarters.

**Reading.** If the two dips are the same body, its period is 787.43 d (the n >= 2 aliases are excluded, and
periods below 65.6 d would put more than 22 epochs in a light curve that holds no third dip). The Archive's
default row for KOI-1356.01 (384.02570682 d, CANDIDATE) and the DR25 TCE (393.719 d) are both wrong by a
factor of about two. The alternative, two unrelated single transits of equal depth 787 d apart, is not
excluded by box depths alone.

## What is new, and what is not

Lissauer et al. 2024 already give 787.43235 d, so the period itself is not new. New here, as far as we can
find (web search for KOI-1356, K01356 and KIC 7363829 on 2026-10-17 and 2026-10-18 finds only the Archive's
pages): the per-epoch light-curve demonstration that both catalogued periods predict a flat epoch with data,
at 37 and 33.5 sigma; the fact that the Archive's `cumulative` table still carries 384.026 d two years after
that paper; and a reproducible open tool and data for anyone to repeat it. Context only, from the
pre-registration, not re-derived here: at 787 d the Archive's star (1.71 Rsun, 5,719 K) gives roughly
0.9-1.2 times Earth's insolation, and Rp/R* 0.072-0.083 makes the body Jupiter-sized. We claim only the
period mismatch.

## Limits

- Box depths against a straight local baseline; no transit-shape fit, no limb darkening, no centroid or
  pixel test. "deep" and "absent" use the thresholds fixed in the pre-registration.
- Quality-0 PDCSAP only. Epochs in gaps are no_data, not evidence either way.
- Made by AI agents for MV2 of Munim, Inc.; not yet checked by a person. Nothing has been sent to the
  Exoplanet Archive or to the authors; a short helpdesk draft is held for Sheehan's review.

## Files

`results/2026-10-18-koi1356-events-0.1.0/`: `report.md`, `summary.json`, `hypotheses.csv`, `aliases.csv`,
`dips.csv`, `coverage.csv`, `gaps.csv`, `cutouts.csv` (+-2 d of flux around every named epoch), `fetched.json`
(sha256 of every file the job ran) and `fetch_tool.py`. The tool is `event_check.py` with `test_event_check.py`
at the repository root; run the tests with `KEPLER_ALIAS_DIR=. python -m unittest -v test_event_check`.
Re-run: `python event_check.py --data-dir <cache> --out-dir out --kepid 7363829 --dur-h 13.5 --hypotheses
"Q1-Q16=384.02570682@335.816169,DR25-TCE=393.719@335.817,Lissauer2024=787.43235205@335.817" --anchors
335.817,1123.255 --max-n 12 --step 0.05`.
