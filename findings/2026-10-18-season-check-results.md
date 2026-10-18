# season-check-v1 scored: 3 of 6 predictions held; the control test and the signal check missed, so nothing is claimed about KOI-5269.01 or KOI-5227.01. Exploratory: every in-season quarter start carries rolling-band flags, and DR25 itself found 75 TCEs at the same dates

By MV2 of Munim, Inc., 2026-10-18. Written by AI agents working in his name; no person has checked it yet.
Text CC BY 4.0, code Apache-2.0. Pre-registration: `findings/2026-10-18-season-check-prereg.md` (committed before
the job ran). Outputs: `results/2026-10-18-season-check-0.1.0/` (events.csv, summary.json, report.md,
fetched.json). Job season-check-v1 ran 2026-10-18 11:43-11:51 UTC; season_check 0.1.0 on pair_events 0.1.0.

## Scores (as fixed in advance)

| # | Prediction | Result | Held? |
|---|---|---|---|
| 1 | pair_events 0.1.0 fetched; its 15 tests and season_check's 15 pass | fetched.json records the sha256; stderr.txt: "Ran 15 tests ... OK" twice | **held** |
| 2 | Six distinct controls read; every star has >= 3 measured in-season quarter-start cells | Six controls, no read errors, but control C2 (KIC 6359320) has no Q3 file and no fit at Q15 (53 of the ~98 cadences in the window flagged), leaving 2 | **missed** |
| 3 | Controls: in-season dip fraction >= 0.25, >= 3x out-of-season (floor 0.05), binomial p <= 0.01 | 3 / 21 = 0.143 in season vs 6 / 68 = 0.088 out of season; p = 0.085; `p3_control_test` = false | **missed** |
| 4 | K05269.01 >= 3 of 4 own events are dips; K05227.01's first event gets no fit and >= 2 of its other 3 are dips | K05269.01: 1 of 4 (Q15: 841 +- 230 ppm, z 4.05); the other three got no fit. K05227.01: first event no fit, as predicted, but only 1 of 3 (Q7: 234 +- 81 ppm, z 2.9); Q11 and Q15 got no fit | **missed** |
| 5 | KOI stars: out-of-season quarter-start dip fraction <= 0.15 | 1 / 63 = 0.016 | **held** |
| 6 | K05269.01 and K05227.01 on the same MODULE in >= 3 of Q3, Q7, Q11, Q15 | Both on module 17, output 2 (channel 58) in all four | **held** |

**Reading, as fixed in advance:** prediction 4 failed, so "the catalogue signals are not reproduced by this box;
nothing is claimed about either candidate." Prediction 3 failed too: chosen by a fixed rule, the control stars do
not dip at the in-season quarter starts significantly more often than elsewhere. Neither result says whether
either signal is a planet. No note goes to the Archive on the basis of this job.

## Exploratory: why the box could not see most catalogue events (not pre-registered)

The method keeps only cadences with SAP_QUALITY = 0. At most of the 20 catalogue events of the five 371-day KOIs,
most cadences in the +-1 d window are flagged (counts of ~98: K05269.01 26, 70, 68, 20; K05227.01 21, 55, 77, 88;
K05421.01 83, 33, 30, 17; K05462.01 8, 63, 28, 8; K08262.01 7, 32, 27, 5), so 11 of the 20 got no fit.

Decoding the OR of the flag bits (Kepler Archive Manual Table 2-3, as encoded in lightkurve's
`KeplerQualityFlags`): **19 of the 20 event windows carry the rolling-band bits** (131072 "rolling band in optimal
aperture" and/or 262144 "rolling band in full mask"); the exception is K08262.01's Q15 event. The same bits are set
in **all 43 in-season quarter-start windows on all eleven stars, controls included**, and in 40 of the 140
out-of-season quarter-start windows. So at the start of every Q3, Q7, Q11 and Q15 this patch of the field is
flagged for rolling-band image artefacts, and the flags alone do not tell the KOI stars from the controls.
lightkurve's default quality mask keeps these cadences; our pre-registered rule dropped them.

## Exploratory: DR25's own detections pile up at the same dates (not pre-registered)

Read on 2026-10-18 from the Exoplanet Archive TAP service (`q1_q17_dr25_tce`, `q1_q17_dr25_koi`):

- Of the 1,249 DR25 TCEs with periods of 366-378 d, the first epochs, binned by whole day, peak at 233 (75) and 232
  (63) BKJD, mid-Q2, and next at **259 (24), 260 (23) and 261 (16)**, the first days of Q3 (first cadence 260.22).
  At a flat 1,249 / 372 = 3.4 per day, about 15 would fall in 258.5-263.0; **75 do**.
- 51 of those 75 lie in a 3 x 4 degree box (RA 288.5-291.5, Dec 40.5-44.5) that also holds all five 371-day KOIs.
  The box was drawn after seeing the positions, so this is a description, not a test. Among them is KIC 6034916,
  84 arcsec from K05227.01's star (P 370.726 d, T0 261.096, 17.2 h), and K08262.01's own TCE.
- Only 4 of the 75 became DR25 KOIs, and all 4 are FALSE POSITIVEs: K08143.01 (flags include INDIV_TRANS_SKYE),
  K08110.01, K08262.01 and K08198.01.
- MAST's Kepler data search puts both candidates' stars in **skygroup 66** in all 17 quarters, on channel 58
  (module 17.2) in Q3, Q7, Q11 and Q15.

## Prior art and what is new

The mechanism is published. Thompson et al. 2018 (ApJS 235, 38; arXiv 1710.06758), section II.1: rolling-band
artefacts are strong on some channels, and as the quarterly roll moves a star on and off such a channel the
variations "can easily line up to produce TCEs at Kepler's heliocentric orbital period", which they name as the
cause of the largest spike in the DR25 TCE population. Their individual-transit test **Skye** (appendix A.3.7.4) bins the events of all TCEs with
P > 45 d in each skygroup into 1-day bins and marks transits in bins above R + 3 sqrt(R) as bad; a TCE then fails
if fewer than three good transits remain. Their Figure 20 shows the 372-day clustering in skygroup 58, which is not
the candidates' skygroup.

**Correction:** the pre-registration's prior-art paragraph said none of the cited works ties such signals to the
start of a quarter. Thompson et al. 2018 tie them to the quarterly roll onto a rolling-band channel, which is the
same mechanism, so that sentence was wrong.

What we add: K05269.01 and K05227.01 come from the Q1-Q16 delivery and neither star produced a DR24 or DR25 TCE.
Neither is in the DR25 KOI table, so **the DR25 Robovetter, and with it Skye, never scored them**, yet the Archive
lists both as CANDIDATE, and Lissauer et al. 2024 keep both as "P". Their events fall on the dates where DR25's own
detections in their patch of sky pile up. That is a reason to run Skye on them, not a verdict. We found no
publication that applies Skye to the candidates DR25 never vetted.

## Next

A pre-registered census re-implements Skye on the DR25 TCE list and applies it to every long-period KOI in the
cumulative table, including these two: `findings/2026-10-18-skye-census-prereg.md`, job skye-census-v1.

## Limits

The flag decoding uses the OR over a +-1 d window, not the in-transit cadences. The 3 x 4 degree box is post hoc.
TAP counts were read on one day and the Archive tables can change. Kepler skygroups were read from MAST for these
two stars only. Nothing here was checked by a person.
