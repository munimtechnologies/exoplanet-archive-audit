# Three period disagreements between the Archive and Lissauer et al. 2024, checked against the paper and the pipeline tables

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Text CC BY 4.0. Inputs: results/2026-10-17-lissauer-xmatch-0.1.0/period_flags.csv (72 KOIs whose Archive
period and Lissauer et al. 2024 Table 1 period differ), and the Archive's TAP tables q1_q16_koi,
q1_q17_dr24_koi, q1_q17_dr25_koi, q1_q17_dr25_sup_koi, q1_q17_dr25_tce and cumulative, read 2026-10-17 ~17:45Z.

## What we checked

The three flags that are not 1:1 and not already explained in an earlier note: KOI-5600.01 (ratio 3/1),
KOI-1356.01 (~2/1) and KOI-4030.02 (~5/4). We read all of Lissauer et al.'s arXiv HTML
(arXiv:2311.00238, 317,735 characters, in four passes) looking for these KOIs, their KIC numbers, the seven
long-period orphans matched to rogue TCEs in findings/2026-10-17-orphan-census-results.md, and the word
"rogue". **None of them appears.** The paper's text does explain other period changes (KOI-1353.03, 3349.02,
6262.01, 4777.01, 4305.01, 4872.01, 521.02, 730.03, 2248.02, 375.01). Limit: the passes were read through a
summarising fetch tool, so a passing mention could have been missed.

## KOI-5600.01 (KIC 9018021): the Archive's period is one third of Lissauer's

| source | P (d) | epoch (BKJD) | depth (ppm) | duration (h) | S/N | disposition |
|---|---|---|---|---|---|---|
| Q1-Q16 KOI | 51.510703 | 168.8474 | 310.7 | 4.66 | | FALSE POSITIVE |
| DR24 KOI | 51.510703 | 168.8474 | 310.7 | 4.66 | 7.6 | CANDIDATE |
| DR25 TCE 1 | 17.1696 | 134.582 | 97.1 | 14.37 | 9.3 (81 transits) | (TCE) |
| DR25 KOI = Archive `cumulative` | 17.168095 +- 0.003415 | 134.637329 | 143.1 | 13.04 | 8.1 | CANDIDATE, score 0.992 |
| Lissauer et al. 2024 Table 1 | 51.4999 | | | | 8.1 | P (status PPPP) |

- 3 x 17.168095 = 51.5043 d. The DR24 epoch is the DR25 epoch plus two DR25 periods (168.9735) to within
  0.126 d (3.0 h), inside both durations. So the DR24 transits are every third DR25 event.
- The Archive's default parameters for this candidate are DR25's, at 17.168 d. Lissauer et al. list 51.50 d
  and say nothing about it in their text.
- The DR25 fit is strained: impact parameter 0.999, a fitted stellar density of 0.0020 g/cm3 against
  0.18 g/cm3 from the same row's mass and radius (0.885 Msun, 1.907 Rsun). With the largest radius on
  the Archive's overview page (3.42 Rsun) the star's density is about 0.031 g/cm3, still 15 times the fit's.
- The catalogue values cannot decide between the two periods. DR24's depth over 3 (104 ppm) matches the
  DR25 TCE depth (97 ppm), as it would if only one event in three had a transit. But depth x duration per event
  is 1,448 ppm h (DR24) against 1,395 ppm h (DR25 TCE), as it would be if every 17.17 d event had one. A
  duration test does not settle it either: the Archive's overview page shows stellar radii from 1.68 to
  3.42 Rsun for this star, and a 13 h transit at 17.17 d is possible for the larger ones.
- Likely way it happened (our inference, not stated in Thompson et al. 2018): DR25 federation also accepts
  a TCE whose in-transit cadences cover >= 70 % of an old KOI's. A 17.17 d, 14 h TCE covers every 51.5 d
  event, so it could take over KOI-5600.01's number at a third of its period.

Because the catalogues cannot decide, we pre-registered a pixel test (findings/2026-10-17-koi5600-thirds-prereg.md):
split the 81 DR25 events into the three groups n mod 3 and measure each group's depth.

## KOI-1356.01 (KIC 7363829): a deep signal DR25 found but never catalogued

| source | P (d) | epoch (BKJD) | depth (ppm) | duration (h) | S/N | disposition |
|---|---|---|---|---|---|---|
| Q1-Q16 KOI = Archive `cumulative` | 384.02570682 | 335.816169 | | 14.56 | | NOT DISPOSITIONED in Q1-Q16; CANDIDATE in `cumulative` |
| DR25 TCE 1 | 393.719 | 335.817 | 6,367 | 12.51 | 82.3 (3 transits) | rogue flag 0 |
| DR24 KOI, DR25 KOI | none on this star | | | | | |
| Lissauer et al. 2024 Table 1 | 787.43235 | | | | 83.9 | P (status PPNN) |

- The DR25 TCE has the same first transit as the KOI (335.82), but its period is 2.5 % longer. DR25
  federation needs a period match within 0.2 % (or 2x / 0.5x), so the TCE could not take the KOI's number.
  Under DR25's rule a non-federated TCE becomes a new KOI unless the Robovetter calls it not transit-like
  with a score below 0.1. There is no DR25 KOI on this star, so the TCE was presumably dropped that way.
  We have not read its Robovetter flags.
- Lissauer's 787.43 d is twice the TCE period (2 x 393.719 = 787.438). From 335.82 the TCE's events fall
  at 729.54, 1,123.26 and 1,516.98; the Q1-Q16 period puts them at 719.84, 1,103.87 and 1,487.90. **So the
  three catalogues agree only on the first transit.** Lissauer's period keeps the 1,123.26 event and
  means the TCE's other counted event is not a transit of this object, or falls in a gap. Their text does not say which.
- The Archive keeps the Q1-Q16 period of 384.03 d, which matches none of the later events in DR25 or in
  Lissauer's table. We claim nothing about the true period. A per-event look at the light curve is the
  natural next check. Not checked: single-transit and long-period catalogues that may list this star.

## KOI-4030.02 (KIC 9551430)

The Archive (Q1-Q16 values) gives 163.515 d and Lissauer et al. give 203.299 d. These are not commensurate
(the 5/4 flag is loose: 5/4 x 163.515 = 204.39 d). DR25's only TCE on the star is KOI-4030.01 (7.755 d, a
false positive). Lissauer et al. reject KOI-4030.02 anyway (status S, S/N 4.0). Nothing to claim.

## Summary

Two of the three flags point at real, undocumented differences. For KOI-5600.01 the Archive's default
period is DR25's, a third of the period in DR24 and in Lissauer et al. 2024. For KOI-1356.01 an S/N 82
DR25 detection was never federated or catalogued, and three catalogues give three periods. Neither is
explained in Lissauer et al.'s text. We found no publication discussing either.
