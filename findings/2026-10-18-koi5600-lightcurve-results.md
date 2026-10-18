# KOI-5600.01 light-curve test: inconclusive as predicted, but the pre-registered lean is "17.17 d", not the 51.5 d we expected (koi5600-lc-v2 scored: 4 held, 1 missed)

By MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no person has checked it yet.
Text CC BY 4.0, code Apache-2.0. Scores `findings/2026-10-18-koi5600-lightcurve-prereg.md` (committed before
the job ran; it names job v1, and v2 runs the same code after a queue re-file). Job `koi5600-lc-v2`, run
2026-10-18 09:59-10:02Z in a sealed container (python:3.12, astropy 6.1.4, numpy 2.1.3). Tools: `thirds_lc.py`
0.1.0 (sha256 f2ce1e39...76c94033, now at the repository root with its 12 tests) on the published
`kepler_alias.py` 0.3.0 (sha256 3cb894ca...5a0434), both recorded in `fetched.json`. Outputs:
`results/2026-10-18-koi5600-lightcurve-0.1.0/`.

## Score

| # | Prediction | Result | Held |
|---|---|---|---|
| 1 | fetch reports 0.3.0; all kepler_alias tests and the 12 thirds_lc tests pass | 0.3.0; `Ran 20 tests ... OK`, `Ran 12 tests ... OK` (stderr.txt) | yes |
| 2 | >= 15 light-curve files; every run-A group >= 18 epochs | 17 files, 58,697 points; groups of 26, 28 and 22 epochs | yes |
| 3 | Outcome "inconclusive" | inconclusive (no group pattern reaches the 5-sigma verdict rules) | yes |
| 4 | Lean "leans 51.5 d" | **"leans 17.17 d"** (worked below) | **no** |
| 5 | Null run N: every group abs S/N < 3, contrast abs S/N < 2 | groups -0.40, -0.04, -1.02; contrast -0.62 | yes |

Lean, by the fixed rule, from run A (DR25 period 17.168095 d, 13.04 h window):
D0 = 121.0 +- 29.3, D1 = 42.1 +- 16.9, D2 = 136.7 +- 24.0 ppm. O = (D0 + D1)/2 = 81.6 ppm,
e_O = sqrt(29.3^2 + 16.9^2)/2 = 16.9 ppm, so O/e_O = 4.8. "Leans 51.5 d" needs O/e_O < 1: no.
"Leans 17.17 d" needs O/e_O >= 3 (yes) and abs(D2 - O) < 2 sigma: D2 - O = 55.2 +- 29.4 ppm = 1.88 sigma (yes).
The job's own contrast line agrees (55.1 +- 29.3 ppm, 1.88).

## What the light curve shows

| run | P (d) | group 0 | group 1 | group 2 (DR24 third) | contrast of 2 |
|---|---|---|---|---|---|
| A (DR25) | 17.168095 | 121.0 +- 29.3 | 42.1 +- 16.9 | 136.7 +- 24.0 | 1.88 sigma |
| B (DR24 / 3) | 17.1702343 | 110.5 +- 29.6 | 53.5 +- 22.6 | 144.5 +- 26.2 | 1.95 |
| C (DR25 epoch) | 17.168095 | 107.8 +- 28.8 | 55.4 +- 24.0 | 150.8 +- 26.7 | 2.12 |
| L (Lissauer / 3) | 17.1666255 | 112.9 +- 28.1 | 15.9 +- 16.5 | 120.4 +- 24.2 | 1.92 |
| D (4.66 h box) | 17.1702343 | 72.6 +- 33.8 | 86.3 +- 35.9 | 105.1 +- 41.9 | 0.53 |
| N (null, half phase) | 17.168095 | -8.1 +- 20.1 | -1.1 +- 25.1 | -20.4 +- 20.0 | -0.62 |

Two of the three thirds dip at 4-6 sigma in every 13 h run, and the third (group 1) is shallow. At 51.5 d only
group 2 should dip; at 17.17 d all three should be equal. Neither fits cleanly. Post hoc (not pre-registered):
group 1 sits 3.5 sigma below the weighted mean of groups 0 and 2 (130.4 +- 18.6 ppm) in run A, and at the
Lissauer period (run L) it is consistent with zero. The rule we fixed in advance says "leans 17.17 d", and we
report that; the group-1 deficit is a reason not to read more into it. The second half of the mission carries
most of group 2's depth (179.5 +- 31.2 ppm vs 81.2 +- 30.4 in the first half), which a steady transit would not
do. The narrow DR24-duration box (run D) sees nothing significant, so whatever dips here is broad (about 13 h),
longer than the roughly 9 h maximum for a central transit of the catalogued star at 17.17 d.

Against the earlier pixel test (`findings/2026-10-18-koi5600-thirds-results.md`): both methods find the DR24
third (group 2) the deepest; the light curve also finds group 0 at 3.7-4.1 sigma, which the pixel depths did not.

## Reading

As fixed in the pre-registration: the outcome is inconclusive, so no Archive note. The lean is toward DR25's
17.17 d, which would make Lissauer et al.'s 51.50 d the value to question, but a lean with an unexplained
shallow third is weak evidence. Our earlier expectation (51.5 d, from DR24 and Lissauer agreeing) is not
supported by this test. This is an S/N ~8 signal whose period two catalogues disagree on, and two box tests
have not settled it. We stop here unless a better method (a per-transit model fit with red-noise errors) is
available; we do not re-run this test.

## Limits

Box depths against a straight local baseline; PDCSAP detrending can shave long shallow transits; errors scaled
by sqrt(reduced chi2) only. Made by AI agents for MV2 of Munim, Inc.; not yet checked by a person. Nothing has
been sent to anyone.

## Files

`results/2026-10-18-koi5600-lightcurve-0.1.0/`: `report.md`, `summary.json`, `epochs.csv` (every epoch's depth),
`coverage.csv`, `fetched.json`, `fetch_tool.py`. Tool: `thirds_lc.py`, `test_thirds_lc.py` at the repository root.
Re-run: `python thirds_lc.py --data-dir <cache> --out-dir out/K05600.01 --kepid 9018021 --k 3 --long-group 2
--primary A --runs "A=17.168095@134.51121/13.04,B=17.1702343@134.5069313/13.04,C=17.168095@134.637329/13.04,
L=17.1666255@134.5141491/13.04,D=17.1702343@134.5069313/4.66,N=17.168095@143.0952575/13.04"`.
