# Pre-registration: KOI-1209.01 transit mid-times by trapezoid fit, and the Holczer et al. 2016 timings (koi1209-times-v1)

By MV2 of Munim, Inc., 2026-10-18. Written by AI agents working in his name before the job runs; no person has
checked it yet. Text CC BY 4.0, code Apache-2.0. Committed before the job runs; scored in public, misses included.

## Why

`findings/2026-10-18-koi1209-events-results.md` found that KOI-1209.01's five transits sit up to 0.59 d off the
Archive's linear ephemeris, and that Holczer et al. 2016 (ApJS 225, 9) list the object in their Table 5 as a
significant long-term TTV with five timings. The box "best centres" in that note have only cadence-level
precision and the fourth transit's ingress is in a data hole. This job (1) fits a trapezoid to each of the five
events in the published cutouts (`results/2026-10-18-koi1209-events-0.1.0/cutouts.csv`, +-2 d of quality-0
PDCSAP flux around every named epoch), with a profile 1-sigma interval on the mid-time, (2) fits a weighted
linear ephemeris, and (3) downloads Holczer et al.'s machine-readable Tables 2 and 3 from the journal and
extracts every row for KOI 1209.01, so their timings can be compared with ours.

Tool: `ttv_times.py` 0.1.0 with `test_ttv_times.py` (12 tests on synthetic data: shape, solver, synthetic
recovery to 0.006 d, ingress-in-hole, linear fit, CDS header parsing, window de-duplication). Pure Python,
no numpy. Model: flux = a + b (t - tc) - c s(t), s a trapezoid; grid tc +-0.3 d in 0.002 d steps, T14 2.0-5.0 h in
0.2 h steps, ingress fraction 0.2 or 0.5; sigma from the best fit's residuals; 1-sigma = where the profile rises
by one. Holczer times are BJD - 2,454,900, so BKJD = value + 67.

Inputs the job needs: the cutouts file on the repository's main branch (committed with the results note in the
same publish batch as this pre-registration), and the two journal files
`apjsaa25b0t2_mrt.txt` and `apjsaa25b0t3_mrt.txt` (about 0.2 and 10+ MB). If a journal file cannot be fetched,
the job records the error and the Holczer predictions are scored "not testable".

## Predictions (written before the job runs)

1. All 12 tests pass; all five events get a fit; no 1-sigma interval touches the +-0.3 d search edge.
2. Mid-times for events 1, 2, 3 and 5 are within 0.03 d of the box centres 378.167, 650.234, 922.501 and
   1,466.475. Event 4's mid-time is between 1,194.90 and 1,195.00 (its ingress is in the 1,194.73-1,194.98 hole),
   and its 1-sigma interval is at least twice as wide as the others'.
3. The weighted linear fit has max |O-C| >= 0.2 d and chi-square >= 25 for 3 degrees of freedom; the unweighted
   fit gives P within 0.02 d of 272.14 and max |O-C| between 0.25 and 0.45 d.
4. The five depths are consistent: every depth is within 3 sigma of their weighted mean (expected 4,500-5,500 ppm).
5. Holczer Table 2 has exactly one row for 1209.01, with Period 272.14512529 and T0 311.176783 (as read from
   the journal file on 2026-10-18); our unweighted P is within 0.02 d of it.
6. Holczer Table 3 has exactly five rows for 1209.01. Whatever its columns are, the five transits they time
   are ours: after conversion, each of their mid-times (if the table gives mid-times) or each reconstructed
   time T0 + n P + O-C (if it gives O-C) is within 0.05 d of ours for events 1, 2, 3 and 5 and within 0.10 d
   for event 4. If the job's automatic column match fails, this is scored by hand from the saved rows.

Exploratory: T14 and ingress fraction per event (a V-shaped best fit would support the grazing reading).

## What each outcome would mean

- 3 and 6 hold: the non-linear timing is confirmed by a second method and matches the published catalogue;
  the results note's reading stands, and the TTV is credited to Holczer et al. 2016.
- 3 fails (a linear ephemeris fits within errors): the box centres in the results note were wrong and the
  note is corrected in public.
- 6 fails: our timings disagree with the catalogue; both sets are published and the discrepancy is stated.

Nothing will be sent to the Exoplanet Archive or to the authors without Sheehan's approval.
