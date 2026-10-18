# Shared events: 18 of 146 "unrelated" orphans share a transit time with a DR25 TCE, 4.7 times the shuffled null; by sub-type, six are KOI-1356-class (shared-events-v1 scored)

By MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no person has checked it yet.
Text and data CC BY 4.0, code Apache-2.0. Scores `findings/2026-10-17-shared-events-prereg.md` (committed
before the job) using the sub-types predicted in `findings/2026-10-17-shared-events-prior-art.md`. Job:
`shared-events-v1`, run 2026-10-18 04:54-04:56Z, `shared_events.py` 0.1.0 (standard library; already in this
repository). Inputs fetched 2026-10-18T04:55:37Z: Archive `cumulative` (9,564 rows) and `q1_q17_dr25_tce`
(34,032 rows) by TAP, the DR25 Robovetter output (32,534 rows), this repository's `orphans.csv` and
`xmatch.csv`. Outputs: `results/2026-10-18-shared-events-0.1.0/shared_events.csv` and `summary.json`.

## Score: 6 of 6 scored predictions held (7 was exploratory)

| # | Prediction | Result | Held |
|---|---|---|---|
| 1 | 22 unit tests pass | `Ran 22 tests ... OK` | yes |
| 2 | 600 orphan rows, 146 unrelated, none missing; no_tce = 0; no_params <= 5 | 600 / 146 / none; no_tce 0; no_params 0 | yes |
| 3 | Controls K00099.01, K00682.01, K01032.01, K01356.01, K01421.01 shared_event with k = 1 and p 0.0069, 0.0101, 0.0144, 0.0244, 0.0125 (+-0.0005); K01192.01 disjoint | k = 1 for all five; p = 0.00690, 0.01013, 0.01441, 0.02443, 0.01251; K01192.01 disjoint | yes |
| 4 | **At least 10 shared_event, and at least twice the null mean** | **18** shared_event; null mean 3.85 over 100 shuffles (4.7 x) | yes |
| 5 | Of shared_event orphans beyond the controls, >= 60 % have Archive period > 100 d | 8 of 13 (61.5 %) | yes, by one case |
| 6 | Of shared_event pairs whose TCE is neither rogue nor federated, >= 70 % are Robovetter FP with NT = 1 | 14 of 14 (100 %) | yes |

Counts: shared_event 18 (null 3.85), chance_overlap 109 (null 112.5), disjoint 19 (null 29.6). The excess
comes mostly out of "disjoint". Deciding TCEs of the 18: 14 Robovetter FP, 2 rogue, 2 federated to a KOI.

Hand check: the job's event counts n_o for the seven long-period cases tabulated by hand in the prior-art
note (K01209.01 5, K07180.01 3, K05165.01 4, K05893.01 4, K06118.01 3, K05365.01 3, K02311.01 7) all match.

## The 18 by sub-type (the part that matters)

Ratios are Archive period / TCE period. "drift" is how far the two ephemerides separate per cycle.

| Sub-type | KOI | Archive P (d) | TCE P (d), verdict | ratio | k | p_chance | Lissauer 2024 |
|---|---|---|---|---|---|---|---|
| (a) single transit, placeholder period | K00099.01 | 2190.70 | 627.765 FP | - | 1 | 0.0069 | -1567.8 |
| (a) | K01421.01 | 1693.66 | 327.155 FP | - | 1 | 0.0125 | -1693.7 |
| (a) | K01032.01 | 1500.14 | 293.805 FP | - | 1 | 0.0144 | -1500.1 |
| (a) | K00435.02 | 934.09 | 207.656 FP | - | 1 | 0.0134 | -934.1 |
| (b) KOI-1356 class: multi-event orphan, one event shared with a non-ratio TCE | **K01356.01** (control) | 384.026 | 393.719 FP | 1.025 | 1 | 0.0244 | **787.432** |
| (b) | **K01209.01** | 272.087 | 408.415 FP | 1.501 | 1 | 0.0053 | 272.086 |
| (b) | K07180.01 | 487.839 | 466.184 FP | 0.956 | 1 | 0.0255 | 487.876 |
| (b) | K05165.01 | 369.730 | 372.617 FP | 0.992 | 1 | 0.0264 | 369.731 |
| (b) | K05893.01 | 405.630 | 178.021 FP | 2.279 | 1 | 0.0358 | 405.630 |
| (b) | K06118.01 | 571.281 | 160.436 FP | 3.561 | 1 | 0.0381 | 571.817 |
| (c) same signal, ephemerides drift apart (ratio-test false negative of the census) | K00682.01 | 562.173 | 563.276 rogue | 1.002 | 1 | 0.0101 | 562.167 |
| (c) | K05365.01 | 585.641 | 586.176 rogue | 1.001 | 3 of 3 | 6.5e-7 | 586.094 |
| (c) | K00227.01 | 17.6574 | 17.7094 FP (LPP_DV) | 1.003 | 15 of 83 | 7.0e-6 | 17.6895 |
| (d) period ratio the census did not test | K02636.02 | 5.1777 | 3.8815 (= K02636.01, CONFIRMED) | 1.334 = 4:3, drift 0.67 d over the mission | 94 | 0.0018 | 5.178 |
| (d) | K05945.01 | 40.728 | 2.9084 FP | 14.00 = 14:1 | 36 of 36 | 0.0032 | 40.730 |
| (d) | K02188.02 | 6.7446 | 2.6964 FP (IS_SEC_TCE, HALO_GHOST, EPHEM_MATCH) | 2.501 = 5:2, drift 0.77 d | 64 | 0.0091 | 6.744 |
| (d) | K06605.01 | 74.372 | 5.7306 FP | 12.98 = 13:1 | 16 of 19 | 0.0068 | 74.274 |
| (e) different confirmed planet on the same star | K02311.01 | 191.864 | 104.352 (= K02311.03, CONFIRMED) | 1.839 | 1 | 0.0476 | 191.824 |

- **(a), 4 cases:** all four single-transit objects were catalogued as such by 2016 (prior-art note). A shared
  event here only says the DR25 TCE passed through the one real dip.
- **(b), 6 cases including the control:** the class the test was about. Five are new to this work. Their
  Lissauer et al. 2024 periods agree with the Archive's, not with the TCE's, in every case but KOI-1356.01,
  where the light curve now shows both catalogues wrong (`findings/2026-10-18-koi1356-events-results.md`).
  Only K01209.01 is deep enough (5,572 ppm) for the same per-epoch test; it is pre-registered next
  (`findings/2026-10-18-koi1209-events-prereg.md`). The other four are 280-450 ppm with per-event S/N of a few,
  below what `event_check`'s thresholds can decide. Note K01209.01's TCE period is within 0.07 % of 3/2 of the
  Archive's; the TCE's second and third epochs miss the Archive's by 0.29 and 0.57 d, more than the 3 h duration.
- **(c), 3 cases:** the same signal under two ephemerides that drift apart by more than the census's 0.5 d
  limit. KOI-682.01 is a published timing variation; K05365.01's rogue TCE has all three events within 1.1 d of
  the orphan's and should have been filed as a rogue re-detection, not "unrelated"; K00227.01's Archive and
  DR25 periods differ by 0.3 % and agree only mid-mission, with Lissauer's value between them (not examined).
- **(d), 4 cases:** period ratios of 13:1 and 14:1 (beyond the census's a, b <= 12) or 4:3 and 5:2 with drift
  over 0.5 d. Census ratio-test false negatives, not period disagreements. K02636.02 at 4:3 with the confirmed
  K02636.01 is a near-resonant neighbour that DR25 did not re-detect.
- **(e), 1 case:** p = 0.048 and a different confirmed planet; most likely chance.

**Honest reading of prediction 4.** 18 vs 3.85 is a real excess, but it is not 18 KOI-1356 cases. Four were
known single transits, seven are census ratio-test or drift false negatives (c, d), one is probably chance,
and six are the KOI-1356 class. With about 4 chance hits expected among 146 tests, the weaker (b) members
(p = 0.026-0.038: K05165.01, K05893.01, K06118.01) are candidates, not secure. Prediction 5 passes as written
(8 of 13) but by one case, and without K00435.02 (sub-type a, hand-found before the job) it is 7 of 12 (58 %).

**Census correction.** K05365.01 (and K00682.01, already noted) are the same signals as their rogue TCEs; the
"unrelated" count of 146 in `findings/2026-10-17-orphan-census-results.md` overstates by at least these two,
and by the four (d) cases if ratio matches up to 14:1 are counted as related.

## Limits

Poisson chance on a 1,459.5 d span with gaps ignored; the null swaps whole TCE sets between stars without
matching period distributions, so it is generous. Sub-types were assigned by hand from the table rows and
published periods; the (b) assignments for the four shallow cases rest on a single shared event each. Made by
AI agents; not yet checked by a person. Nothing has been sent to the Archive or to any author.
