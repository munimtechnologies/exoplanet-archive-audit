# Results: do Kepler's 600 "orphan" candidates match anything DR25 found? (koi_orphans 0.1.0): 6 of 8 held

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Code Apache-2.0, text and data CC BY 4.0. Pre-registration: findings/2026-10-17-orphan-census-prereg.md
(committed before the job ran). Raw outputs: results/2026-10-17-koi-orphans-0.1.0/. Job orphan-census-v1
ran 2026-10-17 15:59-16:03 UTC, Python 3.12, live Archive TAP queries.

## Score

| # | Prediction | Result | Held? |
|---|---|---|---|
| 1 | All 18 unit tests pass | 18 OK | yes |
| 2 | 600 +- 5 orphans (461 / 139), 163 +- 3 with a DR25 TCE, 343 +- 5 pairs, 34,032 TCE rows | 600 (461 / 139), 163, 343, 34,032 | yes |
| 3 | Control: >= 95 % same_events at 1:1, >= 98 % same_events of any kind | 1,350 / 1,377 = 98.0 % at 1:1; 1,370 / 1,377 = 99.5 % any kind | yes |
| 4 | K02167.02 at 1/11 vs K02167.03's TCE; K01922.02 at 1/7 vs K01922.03's; K01101.02 at 1:1 vs K01101.01's | all three, as predicted | yes |
| 5 | Null averages <= 1.5 same_events orphans per shuffle | 0.79 (100 shuffles) | yes |
| 6 | 3-15 same_events orphans, >= 2 above the null | 14 (null 0.79) | yes |
| 7 | <= 6 orphans same_events at 1:1, each on a TCE federated to another KOI | **9 at 1:1; only K01101.02's TCE belongs to a KOI** | **no** |
| 8 | >= half of the same_events orphans match a TCE federated to a CONFIRMED KOI | **4 of 14** (K01101.02, K01922.02, K02167.02, K02261.02) | **no** |

Control misses (27 of 1,377) are mostly 1/2 or 2/1 matches, the 2x/0.5x federation Thompson et al. 2018
describe; they include KOI-4711.01 and 4893.01, whose TCEs sit at twice the catalogued period (our earlier
period findings), and the known KOI-521.02 case.

## Why 7 and 8 failed (post hoc, not pre-registered)

Prediction 7 assumed that a DR25 TCE at an orphan's period would either belong to another KOI (a duplicate)
or show that federation had missed it. There is a third case we did not think of: **rogue TCEs**. Thompson
et al. 2018 (arXiv:1710.06758) say the DR25 TCE table holds 1,498 rogue TCEs, three-transit events returned only
because of a bug in the pipeline's TPS module, and that "the creation and analysis of this KOI catalog only
rely on the non-rogue TCEs". A rogue TCE is never vetted and never carries a KOI forward.

Seven of the eight 1:1 TCEs with no KOI have `tce_rogue_flag = 1`:

| orphan | KIC | catalogued P (d) | rogue TCE P (d) | mid-time offset (d) | depth orphan / TCE (ppm) | TCE S/N | p_phase | Lissauer 2024 |
|---|---|---|---|---|---|---|---|---|
| K00600.02 | 10718726 | 294.0553 | 294.054 (TCE 2) | -0.005 | 770 / 829 | 15.3 | 0.008 | PPNN |
| K03401.02 | 9966219 | 326.6708 | 326.667 (TCE 2) | -0.015 | 386 / 432 | 11.6 | 0.007 | RPNN |
| K04333.01 | 2576962 | 309.2558 | 309.235 | -0.025 | 421 / 382 | 10.1 | 0.007 | PPNN |
| K05126.01 | 5110453 | 418.0436 | 418.033 | -0.018 | 482 / 486 | 5.1 | 0.003 | PPNN |
| K05423.01 | 7762153 | 366.5571 | 366.563 | +0.010 | 583 / 666 | 8.6 | 0.005 | PPNN |
| K05613.01 | 9097470 | 346.4174 | 346.402 | -0.018 | 662 / 707 | 7.6 | 0.005 | PPNN |
| K06151.01 | 6946708 | 431.7856 | 431.781 | -0.005 | 333 / 324 | 9.1 | 0.004 | PPNN |

Each match is at the same period (drift over the mission <= 0.10 d), the same epoch (within 0.025 d,
against windows of 0.6-1.2 d) and the same depth (TCE / orphan 0.91-1.14). The shuffled-star null gave
0.00 same_events at 1:1 per shuffle. The eighth 1:1 case, K05156.01 (1.68 d), is not rogue, but its
phase test is weak (p_phase 0.76) and its catalogued depth (51,633 ppm) is 400 times the TCE's (116 ppm),
so we read it as chance and claim nothing. Prediction 8 failed for the same reason: rogue TCEs have no
KOI, so they cannot point to a CONFIRMED one.

So the 14 same_events orphans split into:

- **3 aliases of a confirmed sibling** (K01101.02, K01922.02, K02167.02), all already rejected by
  Lissauer et al. 2024 (FPNN, SPNN, SPNN). Our earlier notes give the reasons.
- **7 long-period candidates (294-432 d) that DR25 did detect, as rogue TCEs**, which is why they were
  never re-delivered. Lissauer et al. 2024 keep six as planet candidates (PPNN) and reject K03401.02 for
  its radius (RPNN).
- **4 weak matches** (K05156.01, K06542.01, K02261.02, K06600.01; p_phase 0.29-1.0) that the
  pre-registered rule (same or integer kind with p_phase <= 0.2) does not let us claim.

## What is new, and what is not

- New, as far as we can find: for six long-period Kepler candidates that the 2024 catalogue keeps
  (KOI-600.02, 4333.01, 5126.01, 5423.01, 5613.01, 6151.01) and one it rejects for radius (3401.02), the
  final pipeline run independently re-detected the signal at the catalogued period, epoch and depth. Their
  Lissauer status ends in "NN" (not in DR25 or DR24), and the Archive still shows Q1-Q16 parameters for all
  seven. Thompson et al. 2018 (App. A.6) ran ephemeris matching on all TCEs, rogue ones included, but used it
  only to flag contamination, and they invite others to study the rogue list. Lissauer et al. 2024 do not mention rogue
  TCEs in the first 300,000 of the 318,000 characters of their arXiv HTML (arXiv:2311.00238; the last
  18,000 were not read). We found no publication that lists these matches.
- An independent re-detection is supporting evidence, not a validation: a rogue TCE was never vetted, and
  three transits of a few hundred ppm can still be systematics. It does say the Q1-Q16 signal was not a
  one-off of that data release.
- Not new: the three sibling aliases are already rejected by Lissauer et al. 2024 (findings/2026-10-17-lissauer-check.md).
- The unscored CONFIRMED run found one same_events orphan, K01236.03 (Kepler-279 d, 54.42 d) at 1/4 of a
  TCE with no KOI (217.7 d), i.e. every fourth transit of a known planet. Nothing to claim.

## Limits

Periods, epochs and durations are catalogue values; the 0.5 d drift cut may miss aliases whose old period
is imprecise; the null shuffles TCE sets between orphan stars only. The rogue explanation was found after
the scores, by reading the TCE rows; it is not part of the pre-registration.

## Next

orphan_reject 0.1.0 (pre-registered in findings/2026-10-17-orphan-reject-prereg.md) joins this census with
the Lissauer cross-match to ask whether orphans on stars where DR25 found nothing are rejected more often.
