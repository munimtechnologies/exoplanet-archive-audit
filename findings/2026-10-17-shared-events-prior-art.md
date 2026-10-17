# Prior art and hand checks for the shared-events controls (written before shared-events-v1 ran)

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no person has checked this.
Text and data CC BY 4.0. Companion to findings/2026-10-17-shared-events-prereg.md (shared_events 0.1.0).
The job shared-events-v1 was still queued when this was written; nothing below uses its output. Every number
here was read from the Archive's cumulative and q1_q17_dr25_tce tables (copies in
results/2026-10-17-koi-orphans-0.1.0/), the DR25 Robovetter output file (github.com/nasa/kepler-robovetter),
or the arXiv HTML of the papers named, and the arithmetic was done by hand with the prereg's formulas.

## Summary

1. Four of the 146 "unrelated" orphans have exactly one predicted transit inside Q1-Q17 (BKJD 131.5-1591.0):
   KOI-99.01, KOI-1032.01, KOI-1421.01 and KOI-435.02. All four are listed as single transit events (STEs) by
   Uehara et al. 2016; KOI-99.01 and KOI-435.02 are also single-transit candidates in Foreman-Mackey et al.
   2016, and KOI-99.01, KOI-1421.01 and KOI-435.02 in Herman, Zhu & Wu 2019. Their Archive periods
   (2190.7, 1500.1, 1693.7 and 934.1 d) are therefore not measured periods; Herman et al. say so in a table
   footnote for KOI-99 and KOI-1421. The cumulative table's koi_num_transits field is empty for all of them,
   so a reader of the table cannot tell.
2. KOI-435.02 (Kepler-154, five confirmed inner planets) is a **sixth shared-event case found by hand**,
   not among the five prereg controls: its single transit at 657.269 BKJD is one of the seven events of the
   DR25 TCE 011709124-03 (207.656 d), Robovetter 0.000 FP, NT = 1, CO = 1, INCONSISTENT_TRANS. Hand p = 0.0134.
3. KOI-682.01's 1.1 d drift against the rogue TCE at 563.276 d is a published transit timing variation
   (Wang et al. 2015: the first two intervals differ by about 27 hours). It is the same planet at the same
   period, not a wrong period.
4. KOI-1192.01 (the disjoint control) is already called a likely false positive by Wang et al. 2015 (video
   crosstalk from a saturated star); both DR25 TCEs on its star carry EPHEM_MATCH, which agrees.
5. KOI-1356.01 appears in none of the four long-period surveys. It stays the clean worked example.
6. The five control p-values of the prereg (0.0069, 0.0101, 0.0144, 0.0244, 0.0125) were re-derived by hand
   here and agree.

What is new, then, is narrower than the prereg's wording and should be scored that way: the single-transit
nature of 99.01, 1421.01 and 435.02 is well known, and 1032.01 is a suspected crosstalk false positive.
What the literature does not record is that for each of these the DR25 pipeline produced a TCE that
contains the real dip plus two to six empty slots at a shorter period, that the Robovetter rejected it, and
that the Archive row then kept a Q1-Q16 placeholder period with no transit count.

## Table 1. The six prereg controls plus KOI-435.02

Archive = cumulative table (provenance q1_q16_koi for all seven). TCE = q1_q17_dr25_tce. n_o, n_t = events
inside BKJD 131.5-1591.0; w = (D_o + D_t)/24 d; lam = n_o n_t 2w/1459.5; p = P(Poisson(lam) >= k).

| KOI | Archive P (d), T0, D (h) | DR25 TCE: P (d), T0, D (h), depth (ppm), SNR | shared event | n_o x n_t, w, k, p | Robovetter (score disp NT SS CO EC; minor flags) |
|---|---|---|---|---|---|
| K00099.01 | 2190.701, 140.048, 19.89 | -01: 627.765, 140.063, 20.53, 258, 8.3 | 140.05 | 1x3, 1.684, 1, 0.0069 | 0.000 FP 1 0 0 0; INDIV_TRANS_MARSHALL, LPP_DV, MOD_NONUNIQ_DV, MOD_POS_DV, MOD_NONUNIQ_ALT, MOD_TER_ALT, MOD_POS_ALT, INCONSISTENT_TRANS, CENT_FEW_DIFFS |
| K01421.01 | 1693.664, 524.280, 22.60 | -01: 327.155, 197.119, 21.48, 552, 8.0 | 524.27 | 1x5, 1.837, 1, 0.0125 | 0.000 FP 1 0 0 0; INDIV_TRANS_MARSHALL, LPP_DV, LPP_ALT, MOD_NONUNIQ_ALT, MOD_TER_ALT, MOD_POS_ALT, INCONSISTENT_TRANS, CENT_FEW_DIFFS |
| K01032.01 | 1500.141, 176.082, 25.73 | -01: 293.805, 176.09, 25.12, 1596, 26.3 | 176.09 | 1x5, 2.119, 1, 0.0144 | 0.000 FP 1 0 1 0; INDIV_TRANS_MARSHALL_SKYE_ZUMA, LPP_DV, MOD_NONUNIQ_ALT, INCONSISTENT_TRANS, CENT_UNRESOLVED_OFFSET, HALO_GHOST |
| K00435.02 | 934.094, 657.269, 17.49 | -03: 207.656, 241.824, 16.32, 130.5, 2.3 | 657.14 vs 657.27 | 1x7, 1.409, 1, 0.0134 | 0.000 FP 1 0 1 0; INDIV_TRANS_MARSHALL_SKYE_ZUMA, LPP_DV, LPP_ALT, MOD_NONUNIQ_DV, MOD_TER_DV, MOD_POS_DV, MOD_NONUNIQ_ALT, MOD_TER_ALT, MOD_POS_ALT, INCONSISTENT_TRANS, CENT_FEW_DIFFS, HALO_GHOST |
| K01356.01 | 384.026, 335.816, 14.56 | -01: 393.719, 335.817, 12.51, 6367, 82.3 | 335.82 (first of 4) | 4x4, 1.128, 1, 0.0244 | 0.000 FP 1 0 0 0; INDIV_TRANS_MARSHALL_SKYE, INCONSISTENT_TRANS, CENT_FEW_DIFFS |
| K00682.01 | 562.173, 185.969, 9.88 | -01 (rogue): 563.276, 184.864, 9.93, 5507, 113.5 | 748.14 (middle of 3; outer two miss by 1.10 d) | 3x3, 0.825, 1, 0.0101 | rogue TCEs are not in the Robovetter file; -02 (472.466 d) shares nothing and is 0.000 FP 1 0 0 0; INDIV_TRANS_SKYE, CENT_FEW_DIFFS |
| K01192.01 | 1295.362, 176.106, 28.30 | -01: 359.047, 295.777, 32.21, 5675, 111.7; -02: 359.039, 274.227, 15.58, 4408, 92.0 | none | 2x4 twice, k = 0 | -01: 0.000 FP 1 0 0 1; INDIV_TRANS_MARSHALL_SKYE, INCONSISTENT_TRANS, CENT_FEW_DIFFS, EPHEM_MATCH. -02: 0.000 FP 1 0 1 1; INDIV_TRANS_SKYE, SAME_NTL_PERIOD, CENT_FEW_DIFFS, HALO_GHOST, EPHEM_MATCH |

KOI-435.02 detail: the other five TCEs on KIC 11709124 are Kepler-154 b-f (Robovetter PC, scores 0.884-1.000).
Kepler-154 e (3.933 d) and b (33.04 d) each have an event within w of 657.27, but with 371 and 45 events
their p are 0.35 and 0.052, so TCE-03 (p 0.0134) decides and the status is shared_event. KOI-435.02's second
Archive event would fall at 1591.36 BKJD, 0.36 d after the Q17 end used here, which is why n_o = 1.

Thompson et al. 2018 Appendix B defines INCONSISTENT_TRANS as a TCE with period over 90 d whose largest
single-event statistic dominates its multiple-event statistic: one big dip carries the detection. That is
the signature expected if a TCE is one real transit plus empty slots, and all five non-rogue deciding TCEs
above carry it.

## Table 2. What the long-period surveys say

Sources: Uehara et al. 2016 (arXiv:1602.07848, visual STE search of 7,557 KOIs), Foreman-Mackey et al. 2016
(arXiv:1607.08237, automated 1-2 transit search), Herman, Zhu & Wu 2019 (arXiv:1901.01974, re-fit with Gaia
DR2), Wang et al. 2015 (arXiv:1512.02559, Planet Hunters VIII). Checked by KIC and by KOI in each paper's
HTML tables and text.

| KOI (KIC) | Uehara 2016 | Foreman-Mackey 2016 | Herman 2019 | Wang 2015 |
|---|---|---|---|---|
| 99.01 (8505215) | Table 1, "1CS+1F", Tc 140.0473, depth 1874.2, PKep,min 1450.95 d; not fitted | Table 2, t0 140.0492, P 9.1 (+9.5/-3.4) yr, worked example of the paper | Table 1, t0 140.0488, P 2608 (+196/-114) d; footnote: "misidentified by the Kepler pipeline as shorter period candidates ... only transit once" | not present |
| 1421.01 (11342550) | Tables 1-2, "1CS", Tc 524.2844, depth 9515.3; fit P 2230 (+960/-740) d, "consistent with the value given in the KOI catalog" | not present | Table 1, t0 524.2814, P 1632 (+151/-111) d; same footnote | not present |
| 1032.01 (2162635) | Table 1, "1CS+2S": three STEs at Tc 176.0986, 992.3180, 1351.3427 (depths 4129.9, 1500, 1750 ppm); excluded from fits for "signatures of the CCD cross talk"; footnote: possible false positive on CFOP | not present | not present | not present |
| 435.02 (11709124) | Tables 1-2, "5C+1CS", Tc 657.2698, depth 8709.6; fit P 910 (+210/-230) d, "consistent with those in the catalog" | Table 2, t0 657.2674, P 4.3 (+4.7/-1.3) yr | Table 1, t0 657.2675, P 1184 (+148/-89) d, the "five inner planets" case | not present |
| 1356.01 (7363829) | not present | not present | not present | not present |
| 682.01 (7619236) | not present | not present | not present | Table 3, triple transit, P 562.709 d, epoch 185.997, "TTV": first two intervals differ by about 27 h |
| 1192.01 (3644071) | not present | not present | not present | sec. IV.5 Notable False Positives: single event matches KOI-1192.01's epoch; video crosstalk from a saturated star on an adjacent readout channel; "KOI-1192.01 is also likely to be a false positive" |

Twicken et al. 2016 Table 3 (golden KOIs vs DR25 TCEs) contains none of the seven (checked in run 71).
Thompson et al. 2018 does not discuss any of them by name.

## Hand-counted events for every "unrelated" orphan with P > 170 d (35 of 146)

Events = Archive T0 + nP inside BKJD 131.5-1591.0, from the cumulative rows in results/2026-10-17-koi-orphans-0.1.0/.
This is the n_o the job should report for each; a mismatch would mean a bug in one of us.

| n_o | KOIs |
|---|---|
| 1 | K00099.01, K01032.01, K01421.01, K00435.02 |
| 2 | K01192.01 |
| 3 | K00682.01, K05835.01, K05344.01, K05365.01, K03456.02, K06108.01, K06118.01, K04396.04, K02281.02, K03028.02, K07180.01 |
| 4 | K01356.01, K04247.01, K05165.01, K05385.01, K05893.01, K02086.04, K00423.02 |
| 5 | K01209.01, K00492.02, K06097.03, K02869.02 |
| 6 | K06111.01 |
| 7 | K01739.01, K02311.01, K06120.02, K06238.01, K06242.01, K06173.01 |
| 9 | K05801.01 |

Edge cases: K00435.02's second event at 1591.36 and K07180.01's third at 1581.80 and K05801.01's ninth at
1588.09 sit near the Q17 end; if the job uses a different T_END they move.

## KOI-1032.01: what the DR25 TCE actually joined

Uehara's three dips are at 176.10, 992.32 and 1351.34 BKJD. The DR25 TCE at 293.805 d from 176.09 predicts
176.09, 469.90, 763.70, 1057.51 and 1351.31: it links the first and third dips (1351.3427 - 176.0986 =
1175.244 d = 4 x 293.811 d) and fills three slots where Uehara saw nothing; the 992.32 dip is 2.78 periods
from the first and is not on that ephemeris. So no single period fits all three dips, which is consistent
with Uehara's crosstalk reading, and the Robovetter's CO = 1 (CENT_UNRESOLVED_OFFSET) and HALO_GHOST flags
point the same way. The Archive still lists KOI-1032.01 as a CANDIDATE with P = 1500.14 d. Whether it should
is a question for a person who has looked at the pixels; this note only records what the tables say.

## How this changes the reading of the prereg

- Prediction 3 (controls) stands as written; nothing here changes the expected statuses or p-values.
- Prediction 4 (>= 10 shared_event) now has six hand-confirmed cases, so at least four more are needed from
  the remaining 139. KOI-435.02 must be counted as a hand-found case, not as a "new" one, when the job lands.
- Three sub-types should be reported separately in the results note, because "DR25 kept one real transit at
  a wrong period" is only honest for the second:
  (a) **single-transit placeholder**: n_o = 1 and the Archive period is a lower bound or a fit artefact
      (99.01, 1421.01, 1032.01, 435.02; all known STEs). Here a shared_event flag says only that DR25's one
      TCE on the star went through the real dip. Expected whenever such a TCE exists.
  (b) **multi-event orphan, non-ratio TCE period sharing one event**: 1356.01 (and any new case with n_o >= 2).
      This is the class the prereg is really about.
  (c) **same period, drift from TTVs**: 682.01. A ratio-test false negative, not a period disagreement.
- Prediction 5 (>= 60% of new shared_event orphans have P > 100 d): 35 of 146 have P > 170 d and 4 of those
  are single-event; a job result dominated by sub-type (a) would pass 5 for a reason the prereg did not state.
- For any helpdesk note later: the concrete, checkable Archive issue is that koi_num_transits is empty for
  all seven rows, so single-transit KOIs with placeholder periods are indistinguishable from measured ones in
  the cumulative table. A person must check this before anything is sent.

## Limits

- Robovetter lines were read through a summarising fetch of the raw file in 100,000-character chunks; the
  ids and flag digits were quoted verbatim, minor-flag lists for the longest lines were relayed as token
  lists. Paper tables were read the same way. Nothing was re-derived from light curves.
- Event counts ignore data gaps, as the prereg does. Durations are the Archive's and the TCE's as listed.
- "Not present" means the KIC and KOI strings were not found in the paper's HTML tables or text, as read by
  the summariser; it is not a line-by-line human check.
