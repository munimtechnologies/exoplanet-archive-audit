# Pre-registration: DR25's Skye test, re-run on every long-period KOI, including the candidates DR25 never scored (skye-census-v1)

By MV2 of Munim, Inc., 2026-10-18. Written by AI agents working in his name before the job runs; no person has
checked it yet. Text CC BY 4.0, code Apache-2.0 (`skye_census.py`, 23 hand-worked tests). Committed before the
job runs; scored in public, misses included.

## Why

season-check-v1 (`findings/2026-10-18-season-check-results.md`) could not measure most events of the 371-day
Archive CANDIDATEs K05269.01 and K05227.01, because the windows are full of rolling-band flags. Exploration
showed that 75 DR25 TCEs with periods of 366-378 d have first epochs in 258.5-263.0 BKJD, the first days of
Q3, against about 15 expected, most of them in the candidates' patch of sky. Thompson et al. 2018 (ApJS 235, 38,
appendix A.3.7.4) built the **Skye** test for exactly this. Skye only ever ran on DR25 TCEs, and neither candidate
star produced one. As of 2026-10-18 every cumulative-table CANDIDATE with P > 45 d (749) carries the provenance
`q1_q17_dr25_sup_koi`, so provenance alone does not show which were scored by DR25. Membership in the DR25 KOI
table (`q1_q17_dr25_koi`) does.

## Method (skye_census 0.1.0, standard library only)

1. TAP: `q1_q17_dr25_tce` (kepid, period, T0), `cumulative` (KOI, kepid, disposition, period, T0) and
   `q1_q17_dr25_koi` (KOI, DR25 disposition, comment). MAST Kepler data search (`ktc_target_type=LC`): each star's
   skygroup and the long-cadence quarters it was observed in, 100 stars per request.
2. Events: t0 + nP inside the quarter spans (Q1-Q17 first and last cadences, in the code) of the quarters the
   star has. Intra-quarter gaps are not removed.
3. Skye bins, following Thompson et al.: every DR25 TCE with P > 45 d contributes its events to its star's
   skygroup. Events go into 1-day bins [131 + k, 132 + k) BKJD. R = mean count over the bins whose centre lies
   in a quarter; bins above R + 3 sqrt(R) are rejected and R recomputed until the rejected set is stable. Every
   bin above the final threshold is a Skye bin.
4. Each cumulative KOI with P > 45 d: events, events in Skye bins of its skygroup ("flagged"), good = events -
   flagged. **Eligible** = at least 3 events. **Would fail** = eligible and good < 3 (Thompson's rule; the MES
   recomputation is not done).
5. Groups: **dr25_pc** = in the DR25 KOI table as CANDIDATE (668 with DR25 P > 45 d); **dr25_skye** =
   INDIV_TRANS_SKYE in its DR25 comment (109 with DR25 P > 45 d, all FALSE POSITIVE); **never_dr25** =
   cumulative CANDIDATE absent from the DR25 KOI table. Group membership uses the cumulative-table period.

Hand-worked: with the code's quarter spans, K05269.01 (T0 260.1243, 0.10 d before Q3's first cadence) and
K05227.01 (T0 259.8491, in the Q2-Q3 gap) each have **three** events in data (631.63, 1003.14, 1374.64 and 631.41,
1002.98, 1374.54), so one flagged event makes either fail.

## Predictions (written before the job runs)

1. The 23 unit tests pass.
2. At least 99 % of the DR25 TCE stars with P > 45 d (8,034 on 2026-10-18) and at least 99 % of the KOI stars get
   a skygroup (`p2_coverage`).
3. **Validation:** at least 70 % of the dr25_skye KOIs have at least one event in a Skye bin (`p3_skye_recall`).
4. **Validation:** at most 10 % of the eligible dr25_pc KOIs would fail (`p4_pc_fail_fraction`).
5. **Named:** K05269.01 and K05227.01 both would fail (`p5_named_fail`).
6. **Census:** the eligible never_dr25 KOIs would fail at a fraction of at least 2 x max(dr25_pc fraction, 0.02),
   with binomial p <= 0.01 at that rate (`p6_census`).

Our priors: 1 likely; 2 about 85 %; 3 about 60 % (Thompson's events come from data, ours from ephemerides, and
the bin origin is not given); 4 about 75 %; 5 about 55 %; 6 about 35 %.

## How it will be read (fixed now)

- **3 or 4 fails**: the re-implementation is not faithful enough; 5 and 6 are reported but nothing is claimed.
- **3, 4 and 5 hold**: K05269.01 and K05227.01 would fail DR25's own Skye rule as re-implemented here. We would
  write that up; a correction note to the Archive would be drafted and held for Sheehan's approval, not sent.
- **6 holds as well**: candidates DR25 never scored carry Skye-type clustering more often than DR25's own
  candidates; the list goes out as leads for people to check, one by one.
- Nothing here says whether any candidate is or is not a planet. A Skye flag marks a transit as coinciding with
  clustered artefacts; real transits can be flagged by mistake (Thompson et al. lose Kepler-62f's Q12 transit
  this way).

## Limits fixed in advance

Intra-quarter gaps (safe modes, Q8 and Q12 losses) are not removed, so some events counted in bins have no data.
The bin origin (131.0) is ours. DR25 PCs' own TCE events are in the counts and never_dr25 KOIs have none, which
works against prediction 6. Cumulative-table ephemerides are used for every KOI.
