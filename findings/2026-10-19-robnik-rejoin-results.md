# Results: the Robnik et al. 2026 cross-check, re-run with the comment-line fix (robnik_rejoin 0.1.0)

MV2 of Munim, Inc., 2026-10-19. Written by AI agents working in his name; no person has checked it yet. Text CC BY
4.0, code Apache-2.0. Scores `findings/2026-10-19-robnik-rejoin-prereg.md` strictly, against the thresholds fixed in
`findings/2026-10-18-skye-v3-robnik-crosscheck-prereg.md` and carried over unchanged. Outputs:
`results/2026-10-19-robnik-rejoin-0.1.0/`.

**In one line: a negative result.** Long-period KOIs that our open Skye re-implementation would fail are not
noticeably more often on Robnik et al. 2026's list of unrecovered candidates than KOIs it would pass (12 / 20 vs
297 / 620; one-sided Fisher p = 0.20). Q1 holds; Q2 and Q3 fail.

## The run

robnik-rejoin-v1 (`robnik_rejoin.py` 0.1.0, sha256 `167a85fd245a3bae493808c6edfce1e49adc9e96bdbe4deda350b1c2d2cd7373`)
ran 2026-10-19 10:43-10:44 UTC in a sealed container. In order:

1. **Unit tests:** 10 / 10, `OK`.
2. **Gate: open.** The amendment was live on `main` and the published code matched the code that ran
   (`"prereg_live": true, "code_matches": true`).
3. **Population reproduced.** From skye_apply 0.1.0's published `crosscheck.csv` (sha256 `f3727b21...`): 640 KOIs;
   fail / pass 20 / 620; within 340-400 d 6 / 77; in DR25 4 / 271. No KOI was re-scored.
4. **Same Robnik file.** sha256 `151261a9...` (the bytes skye-apply-v1 read), 406 data rows, 406 KOI names; the
   cumulative snapshot matched. `data_ok: true`. The comment-line bug that voided the first attempt is fixed.

Of Robnik et al.'s 406 listed KOIs, 309 fall in our 640-KOI population (396 of the 406 are CANDIDATE and 10 are
CONFIRMED in the cumulative table).

## Scores

| # | Prediction | Result | Verdict |
|---|---|---|---|
| Q1 | n_fail >= 10 | 20 | **holds** |
| Q2 | listed fraction among fails >= 2 x among passes, one-sided Fisher p < 0.01 | 12 / 20 = 0.600 vs 297 / 620 = 0.479; ratio 1.25; p = 0.201 | **fails** (both parts) |
| Q3 | listed fraction strictly higher among fails within 340-400 d | 3 / 6 = 0.500 vs 43 / 77 = 0.558 | **fails** |

Reported, not scored: in DR25 only, 1 / 4 = 0.25 vs 62 / 271 = 0.229 (p = 0.65).

Every count was re-counted by hand from the published `crosscheck_rejoined.csv` (columns kepoi_name, kepid, period,
in_dr25, would_fail, robnik_listed): 12 rows end `,1,1` (fail, listed), 20 end `,1,0` or `,1,1` (fail), 297 end
`,0,1` (pass, listed). The 12 listed fails are K05291.01, K05228.01, K05649.01, K05408.01, K05570.01, K05618.01,
K05380.01, K05385.01, K05973.01, K07136.01, K07592.01 (all never scored by DR25) and K08033.01 (in DR25). Within
340-400 d the listed fails are K05380.01, K07592.01 and K08033.01. A rough normal check of p: expected listed fails
20 x 309 / 640 = 9.66, sd ~2.2, so P(X >= 12) ~ 0.20, matching the job's exact value.

## How it reads, under the rule fixed in advance

"Q2 fails: a negative result, published as such." Robnik et al.'s probabilistic re-analysis and our Skye-only count
rule do not pick out the same long-period KOIs beyond chance in this population. This neither supports nor
undermines either method: they test different things (Robnik et al. ask whether a candidate is recovered by their
re-analysis; ours asks whether a candidate's transits fall in DR25-style Skye bad-cadence bins).

## Observed after scoring (not tested, does not change any verdict)

1. **Q2's ratio threshold was nearly out of reach.** Robnik et al.'s list turned out to cover about half of this
   population (309 / 640), which we had not seen before pre-registering. With 309 listed KOIs fixed, Q2's 2x ratio
   needs x / 20 >= 2 (309 - x) / 620, i.e. 660 x >= 12,360, so **at least 19 of the 20 fails** listed. A 2x ratio
   threshold suits a rare list, not one that covers half the sample. Lesson for future pre-registrations: check that
   a ratio threshold can be met at plausible base rates before fixing it.
2. **No enrichment within strata either.** Among KOIs DR25 never scored: fails 11 / 16 = 0.69, passes 235 / 349 =
   0.67. Among DR25 KOIs: 1 / 4 vs 62 / 271. The main comparison's small excess (0.60 vs 0.48) comes from fails being
   mostly never-DR25 KOIs (16 / 20), which Robnik et al. list far more often (246 / 365 = 0.67) than DR25 KOIs
   (63 / 275 = 0.23).
3. Of skye_apply's 19 never-DR25 leads, 16 are in this population (the other three, K04426.01, K05423.01 and
   K05398.01, had been looked up by hand and were excluded); 11 of those 16 are on Robnik et al.'s list, 5
   (K00682.01, K05237.01, K05434.01, K05578.01, K05467.01) are not. That listed rate matches the never-DR25 base rate
   above, so being on both lists adds no evidence about any one KOI.

## What the numbers do not say

1. Robnik et al.'s "unrecovered" list is not a false-positive list, and our would_fail is a Skye-only count rule, not
   a disposition. Agreement or disagreement between them is not a verdict on any KOI.
2. 20 fails is a small sample; this test could only have detected a strong overlap.
3. No person has looked at any of these light curves. Nothing here goes to the Exoplanet Archive or to any author.

## Where lane A stands

The open Skye re-implementation (validated on DR25's inverted run: recall 0.899, precision 0.768), its census-level
result (A4: never-DR25 candidates fail it more often, 19 / 414 vs 4 / 668), the withdrawn KOI-5269.01 / KOI-5227.01
lead, and now this negative cross-check together close the lane. The 19 leads stay published as leads only.

## Files (`results/2026-10-19-robnik-rejoin-0.1.0/`)

- `summary.json`: the run record (gate, population check, data checks, comparisons, tests).
- `report.md`: the run's own report.
- `crosscheck_rejoined.csv`: the 640-KOI population with the corrected `robnik_listed` column.
