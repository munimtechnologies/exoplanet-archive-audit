# Results: are orphans on stars where DR25 found nothing rejected more often? (orphan_reject 0.1.0)

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no person has checked this yet.
Text and data CC BY 4.0, code Apache-2.0. Scores findings/2026-10-17-orphan-reject-prereg.md, misses included.

The job orphan-reject-v1 ran on 2026-10-17 from 22:58 to 23:11 UTC (python:3.12, 1 CPU). Its outputs are in
results/2026-10-17-orphan-reject-0.1.0/ (orphan_reject.csv, one row per orphan, and summary.json).

## Score: 4 of 5 held; the one real test failed

| # | Prediction | Observed | Held? |
|---|---|---|---|
| 1 | All 11 unit tests pass | 11 of 11 passed | yes |
| 2 | 600 orphans joined, none missing; 316 rejected; 1,498 rogue TCEs | 600 joined, 0 missing; 316 rejected; 1,498 rogue TCEs | yes |
| 3 | no_tce orphans rejected more often than orphans with a DR25 TCE on the star, one-sided Fisher p < 0.05 | no_tce 221/437 = 50.6%; with a TCE 95/163 = 58.3%; one-sided p (greater) = 0.96 | **no** |
| 4 | same_events_on_rogue_tce is exactly K00600.02, K03401.02, K04333.01, K05126.01, K05423.01, K05613.01, K06151.01 | exactly those seven | yes |
| 5 | Exploratory: 8-30 orphans have a rogue TCE on their star | 16 | yes |

Prediction 3 failed in the opposite direction: orphans on stars where DR25 found nothing at all were
rejected by Lissauer et al. 2024 *less* often, not more. The pre-registered reading applies: DR25's
silence on the whole star does not, by itself, mark a weaker orphan.

## Rates by census status (from summary.json)

| Census status | n | Rejected | Rate |
|---|---|---|---|
| no_tce | 437 | 221 | 50.6% |
| unrelated | 146 | 88 | 60.3% |
| offset | 3 | 1 | 33.3% |
| same_events | 14 | 6 | 42.9% |

By provenance: Q1-Q16 orphans 269/461 = 58.4% rejected; DR24 orphans 47/139 = 33.8%.
Of the seven orphans whose events DR25 re-detected as rogue TCEs, Lissauer keep six as P; K03401.02 is R.

## After the fact (exploratory, not a test)

Counted by hand from orphan_reject.csv after the job ran, so this is a description, not a result:

| Provenance | no_tce rejected | with-TCE rejected |
|---|---|---|
| q1_q16_koi | 185/333 = 55.6% | 84/128 = 65.6% |
| q1_q17_dr24_koi | 36/104 = 34.6% | 11/35 = 31.4% |

The reversal sits in the Q1-Q16 orphans and does not come from mixing the two provenances. A normal
approximation for the Q1-Q16 difference gives z of about 1.96, which is borderline and was not
pre-registered. One possible reason, not tested: a star where DR25 found an *unrelated* signal often
has a stronger signal of its own (an eclipsing binary or variability), and an orphan on such a star is
more likely to be part of it. Among unrelated orphans, 77 of 146 (52.7%) carry Lissauer's first letter S,
against 197 of 437 (45.1%) for no_tce. Testing this needs a new pre-registration.

## Limits

- This describes how Lissauer et al. 2024 vetted these KOIs. It makes no new dispositions.
- "With a TCE" is mostly the 146 "unrelated" stars; the offset and same_events groups are small (3 and 14).
- Seven of the 600 orphans are single-transit KOIs whose Archive period is a placeholder; see
  findings/2026-10-17-zero-error-periods.md. Removing them does not change the direction (they are
  four with-TCE and three no_tce, two of them rejected).
