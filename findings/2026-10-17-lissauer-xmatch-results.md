# Results: where the Exoplanet Archive still disagrees with Lissauer et al. 2024 (lissauer_xmatch 0.1.0): 7 of 9 held

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Code Apache-2.0, text and data CC BY 4.0. Pre-registration: findings/2026-10-17-lissauer-xmatch-prereg.md
(committed before the job ran). Raw outputs: results/2026-10-17-lissauer-xmatch-0.1.0/. Job
lissauer-xmatch-v1 ran 2026-10-17 16:20-16:24 UTC, Python 3.12. Inputs: Lissauer et al. 2024 (PSJ 5, 152)
Table 1 from IOP's machine-readable file (CC BY 4.0; 6,991,129 bytes, sha256 1fe13603...0521) and the
Archive's cumulative table, fetched 2026-10-17 16:22 UTC.

## Score

| # | Prediction | Result | Held? |
|---|---|---|---|
| 1 | All 16 unit tests pass | 16 OK | yes |
| 2 | Header KIC 1-8, KOI 10-16, Status 548-551; 9,600-9,800 Lissauer rows; 9,564 +- 5 Archive rows; <= 10 unmatched; <= 5 KIC mismatches; 40-150 Lissauer-only | as predicted; 9,693; 9,564; 0; 0; 129 | yes |
| 3 | K01101.02 FPNN, K01922.02 SPNN, K02167.02 SPNN; K00001.01 starts with P | FPNN, SPNN, SPNN, PPPP | yes |
| 4 | Among matched KOIs: P 4,330-4,380; S 300-345; R 90-105; M 10-14 | **P 4,293**; S 319; R 99; M 13 | **no** (P) |
| 5 | 300-500 Archive CANDIDATEs rejected | 431 | yes |
| 6 | Orphans rejected >= 2x as often as DR25-parameter CANDIDATEs | 316 / 600 = 52.7 % vs 115 / 1,377 = 8.4 % (6.3x) | yes |
| 7 | DR25-supplemental letter agrees with the Archive for >= 98 % | 9,554 / 9,564 = 99.9 % | yes |
| 8 | 3-25 CONFIRMED rejected, incl. K03032.01, K01416.01, K01450.01, K00245.04, K00129.01 (M) | 9; all five (FFPP, FFPP, FFFP, FFNN, MFPP) | yes |
| 9 | K04777.01 and K06262.01 at 1/2, K01353.03 at 1/5; 5-300 period flags | **K04777.01 at 1/1**; K06262.01 1/2; K01353.03 1/5; 72 flags | **no** (4777) |

Why 4 missed: we took the paper's count of 4,376 planet candidates and forgot that it includes the 129
KOIs that are not in the Archive's cumulative table (KOI-8298 to 8394 and 32 others). The 4,376 - 4,293 = 83
difference sits there. Why 9 missed: the table row for K04777.01 still carries 0.82400164 d although the
paper's text (sec. 2.3) halves it to 0.412 d; we found and published this before the run
(findings/2026-10-17-lissauer-4777-note.md), so this part was a known risk and is scored as a miss.

## Main result

Of the Archive's 1,977 CANDIDATE KOIs (cumulative table, 2026-10-17), **431 (21.8 %) are rejected by
Lissauer et al. 2024**: 319 for S/N below 7.1 (S), 98 for a radius too large to be a planet (R), 8 for a
mass above 13 Jupiter masses (M) and 6 as false positives (F). The list, with Lissauer's status and both
periods, is results/2026-10-17-lissauer-xmatch-0.1.0/candidates_rejected.csv.

Split by where the Archive's parameters come from (koi_parm_prov):

| parameters from | CANDIDATEs | rejected | rate | of which S |
|---|---|---|---|---|
| DR25 (q1_q17_dr25_koi) | 1,377 | 115 | 8.4 % | 41 |
| DR24 (q1_q17_dr24_koi) | 139 | 47 | 33.8 % | 42 |
| Q1-Q16 (q1_q16_koi) | 461 | 269 | 58.4 % | 236 |
| all orphans (not DR25) | 600 | 316 | 52.7 % | 278 |

So the "orphans", the CANDIDATEs whose parameters predate the final pipeline run, make up 30 % of the
Archive's CANDIDATE list but 73 % of what the 2024 catalogue rejects, mostly for low S/N. This supports,
with an independent and peer-reviewed vetting, the reason we gave for singling them out. It is not a
surprise: DR25 did not re-detect these signals above its own 7.1 threshold, and Lissauer et al. apply a
similar S/N cut. The point is practical. Anyone who takes the Archive's CANDIDATE list as it stands
today gets 431 objects that the latest catalogue does not count, and a Q1-Q16-parameter CANDIDATE is more
likely than not to be one of them. Lissauer et al. (App. A) already warn against adding non-DR25
candidates to occurrence-rate samples; we found no published join of their table to the Archive's current
table, nor this split by provenance.

## Other disagreements (disagreements_other.csv)

- 9 CONFIRMED planets are rejected: 4 by mass (Kepler-39 b, 470 b, 486 b, 492 b), 4 as false positives or a
  false alarm (Kepler-37 e, 840 b, 854 b, 1415 b) and 1 by radius (Kepler-164 e). The Archive's own
  inclusion rule allows masses up to 30 Jupiter masses, so the M cases are a difference of definition, not
  an Archive error.
- 8 Archive FALSE POSITIVEs are planet candidates in Lissauer (K00082.06, 198.01, 242.01, 1693.01, 1796.01,
  1902.01, 2306.01, 2307.01). The paper reports 11 FP -> PC changes. At least one goes the other way in
  time: K00242.01 (Kepler-503 b) is PPPP in the 2024 table but FALSE POSITIVE in the Archive, which may
  reflect later follow-up. Here the Archive may be the more current one, so this list is not a list of
  Archive errors.
- 72 KOIs are period-flagged. Most are small mean-period changes or the placeholder periods of single-
  transit KOIs (negative or 1,500 d values). Whole-ratio changes besides the pre-registered three:
  K00521.02 (1/2, already in the paper), K05600.01 (3/1: 17.168 -> 51.500 d, PPPP), K01356.01 (~2/1:
  384.0 -> 787.4 d), K04030.02 (~5/4) and several FALSE POSITIVEs (K04305.01 1/4, K04872.01 1/5, K04692.01
  2/3, K03773.01 6/1). We have not checked which of these the paper's text discusses.

## Limits

Lissauer's S cut uses their own S/N, so "rejected" means "rejected by Lissauer et al. 2024", not shown
false. CONFIRMED planets validated after 2022 can legitimately differ. The join is by KOI number; KIC
numbers matched in all 9,564 rows.
