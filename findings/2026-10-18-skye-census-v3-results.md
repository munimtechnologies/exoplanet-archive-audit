# Results: skye-census-v3 missed its data check and both TCE-level validation bars, so nothing is claimed

By MV2 of Munim, Inc., 2026-10-18. Written by AI agents working in his name; no person has checked it yet. Text CC BY
4.0, code Apache-2.0. Scores `findings/2026-10-18-skye-census-v2-prereg.md` as amended by
`findings/2026-10-18-skye-census-v3-amendment.md`, strictly, against the thresholds fixed there. Outputs:
`results/2026-10-18-skye-census-0.2.1/`.

## The run

skye-census-v3 (`skye_census.py` 0.2.1, sha256 `fec3c102a12356c2167047ca551d232965f8d4dc9cc5e354589058531854d34c`)
ran 2026-10-18 19:49-19:54 UTC in a sealed container. The Exoplanet Archive's TAP still answered HTTP 400, so all
three tables came from v1's published copies, each accepted on its sha256 (`003d1615...`, `df551272...`,
`9b07b64c...`), as the amendment allows. MAST gave a skygroup for every star (no errors). The DR25 Robovetter
input and output files loaded (input sha256 `3d6689de...`, output `9e1e7a46...`).

## Scores

| # | Prediction | Result | Verdict |
|---|---|---|---|
| 1 | 40 unit tests pass | 40 / 40 | **holds** |
| 2 | Data check (all six parts) | see below; two parts missed | **fails** |
| 3 | TCE recall >= 0.85 | 3,382 / 4,275 = 0.791 | **fails** |
| 4 | TCE precision >= 0.75 | 3,382 / 5,003 = 0.676 | **fails** |
| 5 | dr25_skye KOIs with a flagged event >= 70 % | 87 / 109 = 79.8 % | holds |
| 6 | Eligible DR25 candidates that would fail <= 10 % | 7 / 668 = 1.05 % | holds |
| 7 | K05269.01 and K05227.01 both would fail | both would fail (1 and 2 good events of 3) | holds |
| 8 | never_dr25 fail rate >= 2 x max(PC rate, 0.02), binomial p <= 0.01 | 22 / 415 = 5.30 % vs 4.0 %, p = 4.5e-5 | holds |

Prediction 2, part by part: TCE stars with a skygroup 8,034 / 8,034 (passes); KOI stars 2,165 / 2,165 (passes);
Robovetter input rows parsed **32,534, below the 34,000 required** (fails); P > 45 d TCEs found in it **13,952 /
15,349 = 90.9 %, below the 99 % required** (fails); TCEs whose Robovetter comment names SKYE 4,790, at least 50
(passes); of those, 4,790 / 4,790 = 100 % carry flag 1 in column 12 (passes).

## How it reads, under the rules fixed in advance

"2 fails: the ground truth was not read correctly; nothing is claimed." "3, 4, 5 or 6 fails: the re-implementation
is still not faithful enough; 7 and 8 are reported, nothing is claimed, and the TCE-level mismatches are published
as a diagnosis." Both apply. **Nothing is claimed** about K05269.01, K05227.01 or any candidate never scored by DR25.
Predictions 5-8 holding does not change that. No note goes to the Exoplanet Archive. The per-TCE comparison is
published in `results/2026-10-18-skye-census-0.2.1/tce_skye.csv` as the diagnosis.

The Robnik et al. cross-check (`findings/2026-10-18-skye-v3-robnik-crosscheck-prereg.md`) runs "only if v3's P2
(data check) holds". P2 failed, so **the cross-check does not run** on v3's output.

## What went wrong (found after scoring; these are explanations, not re-scores)

1. **The data-check thresholds were wrong, not the reading.** The column check that confirms the SKYE flag passed
   perfectly (4,790 of 4,790). The two parts that failed assumed the Robovetter table holds all 34,032 DR25 TCEs. It
   does not. Thompson et al. 2018 (ApJS 235, 38, section 2.2): "The DR25 TCE table at the NASA Exoplanet Archive
   contains 32,534 obsTCEs and 1498 rogue TCEs for a total of 34,032." The rogue TCEs are three-transit detections
   caused by a bug in the pipeline's search module, and DR25 "do[es] not use the rogue TCEs in the creation and
   analysis of the DR25 KOI catalog". 32,534 is exactly the number of rows we parsed. The 1,397 long-period TCEs we
   could not find in the table are consistent with being rogue TCEs. We have not checked this against the
   Archive's `tce_rogue_flag` column, because TAP was still down.
2. **Those TCEs were also counted in our Skye bins.** The Skye section of the same paper says "We only use those
   obsTCE with periods greater than 45 d", and obsTCEs are the 32,534 non-rogue TCEs. Our bins counted the 1,397
   extra TCEs as well. 609 of them (43.6 %) have an event in one of our bad bins, against 5,003 of the 13,952 matched
   TCEs (35.9 %), so they lean toward the dates our bins flag. This is a fourth departure from DR25's method, which
   neither the v2 pre-registration nor the earlier code review caught.
3. **Events in data gaps.** Our events are every ephemeris time inside a quarter the star was observed. DR25's
   reference code (`Skye.py`) counts only transits with non-zero single-event statistic and treats bins with no
   such transit as gaps. Our event count equals DR25's count of "real" transits (`nrealtrans`) for only 58.1 % of
   matched TCEs. Extra events in gaps add counts DR25 never had and can flag TCEs DR25 did not, which fits the
   precision miss (1,621 false positives).

The v2 pre-registration named point 3 as a known limit. Points 1 and 2 are new.

## What happens next

- An **exploratory** diagnosis job (`skye_diag.py` 0.1.0) measures how far each cause moves the TCE-level agreement:
  (a) bins from Robovetter-scored TCEs only; (b) events kept only when Kepler long-cadence data exist near them
  (cadences with finite PDCSAP flux in the Q1-Q17 files of KIC 9018021 and KIC 6359929, at three window widths);
  (c) both, plus gap bins defined by the absence of data. Its first variant must reproduce v3's counts exactly
  (tp 3,382, fp 1,621, fn 893, tn 8,056) or the comparison is void. It re-reads data we have already seen, so
  whatever it finds is a diagnosis, not a validated result.
- Because the DR25 OBS flags have now been seen, a future v4 cannot be validated honestly on them alone. DR25 also
  ran the Robovetter, with Skye, on the **inverted** light curves (INV: 19,536 TCEs with periods and epochs in the
  Archive's `kplr_dr25_inv_tces.txt`, flags in the Robovetter repository's `kplr_dr25_inv_robovetter_input.tar.gz`).
  We have not opened those flags. Any v4 will be pre-registered in public first, with the INV flags as its held-out
  validation set.

## Limits

Everything here was made with AI agents in MV2's name and has not been checked by a person. A Skye flag is a sign
that a transit coincides with clustered artefacts, not a verdict on whether a candidate is a planet.
