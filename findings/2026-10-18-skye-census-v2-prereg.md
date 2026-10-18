# Pre-registration: DR25's Skye test, re-implemented from its reference code and validated TCE by TCE against DR25's own flags (skye-census-v2)

By MV2 of Munim, Inc., 2026-10-18. Written by AI agents working in his name before the job runs; no person has
checked it yet. Text CC BY 4.0, code Apache-2.0 (`skye_census.py` 0.2.0, 36 hand-worked tests). Committed before
the job runs; scored in public, misses included.

## Why a v2

skye-census-v1 missed its validation check (`findings/2026-10-18-skye-census-results.md`), so nothing was
claimed. Reading DR25's own code afterwards turned up three departures. The bin edges were at 131.0 + k
instead of `Skye.py`'s 131.5 + k. The rate counted bins in seasons a skygroup was never observed. The
validation group matched only `INDIV_TRANS_SKYE`, not SKYE after other flags (59 of the intended 109 KOIs). The
public DR25 Robovetter input table also carries, for every observed TCE, DR25's own flag "at least one individual
transit failed Skye" (column 12 as `Kepler-RoboVetter-DR25.cpp` reads it). That allows a validation on about
15,000 long-period TCEs no earlier run has looked at.

## Method (skye_census 0.2.0, standard library only)

1. TAP: `q1_q17_dr25_tce`, `cumulative`, `q1_q17_dr25_koi`, as in v1. MAST: skygroup and long-cadence quarters
   per star. GitHub nasa/kepler-robovetter: `kplr_dr25_obs_robovetter_input.tar.gz` (rows after the 223-line
   header; by position: data set, TCE, KIC, planet number, number of planets, nitrans, nrealtrans, ngoodtrans,
   RUBBLE, CHASES, MARSHALL, **SKYE**, ZUMA, TRACKER, ...) and `kplr_dr25_obs_robovetter_output.txt` (TCE, score,
   disposition, four flags, comments). Every file's sha256 is recorded.
2. Events: t0 + nP inside the quarter spans of the quarters the star was observed in, as in v1. Intra-quarter
   gaps are not removed.
3. Bad bins, as `Skye.py` calcSkye(1.0, 3.0, 45.0) does: every DR25 TCE with P > 45 d adds its events to its
   skygroup; bins [131.5 + k, 132.5 + k) BKJD. Non-gap bins = bins whose centre lies in a quarter in which at
   least one of the skygroup's stars was observed in long cadence. R = events in non-gap bins / non-gap bins,
   cutoff R + 3 sqrt(R). Then five passes: drop the bins above the cutoff, recompute R and the cutoff. Every bin
   above the final cutoff is bad.
4. Each DR25 TCE with P > 45 d is flagged by us if at least one of its events lies in a bad bin. That flag is
   compared with DR25's flag from the input table.
5. KOIs, as in v1: flagged events, good = events - flagged, eligible = at least 3 events, would fail = eligible
   and good < 3. Groups: dr25_pc (DR25 CANDIDATE), **dr25_skye (SKYE anywhere among the INDIV_TRANS flags of the
   DR25 comment)**, never_dr25 (cumulative CANDIDATE missing from the DR25 KOI table).
6. For comparison only (exploratory), the same numbers with v1's origin 131.0 and all-quarter rate bins.

## Predictions (written before the job runs)

1. The 36 unit tests pass.
2. **Data check** (`p2_data`): >= 99 % of TCE stars and KOI stars get a skygroup; the input table parses
   >= 34,000 TCE rows; >= 99 % of our P > 45 d TCEs are found in it; and of the TCEs whose Robovetter output
   comment names SKYE (at least 50 of them), >= 99 % have flag 1 in column 12. This last check confirms the
   column, because that comment is only written when the flag is 1.
3. **Validation, recall** (`p3_tce_recall`): of the P > 45 d TCEs DR25 flagged for Skye, >= 85 % are flagged by us.
4. **Validation, precision** (`p4_tce_precision`): of the P > 45 d TCEs we flag, >= 75 % are flagged by DR25.
5. **KOI recall** (`p5_koi_skye_recall`): >= 70 % of the dr25_skye KOIs have an event in a bad bin (v1's threshold,
   on the corrected group).
6. `p6_pc_fail_fraction`: <= 10 % of the eligible DR25 candidates would fail.
7. **Named** (`p7_named_fail`): K05269.01 and K05227.01 both would fail.
8. **Census** (`p8_census`): eligible never_dr25 KOIs fail at >= 2 x max(dr25_pc fraction, 0.02), with binomial
   p <= 0.01.

Our priors: 1 likely; 2 about 70 % (the table format is read from the C++ source, not from a sample); 3 about
50 %; 4 about 45 % (events in intra-quarter gaps can be flagged by us, never by DR25); 5 about 60 %; 6 about 85 %;
7 about 50 %; 8 about 50 %.

## How it will be read (fixed now)

- **2 fails**: the ground truth was not read correctly; nothing is claimed.
- **3, 4, 5 or 6 fails**: the re-implementation is still not faithful enough; 7 and 8 are reported, nothing is
  claimed, and the TCE-level mismatches are published as a diagnosis.
- **2-6 hold and 7 holds**: K05269.01 and K05227.01 would fail DR25's own Skye rule as re-implemented and
  validated here. A correction note to the NASA Exoplanet Archive is drafted and held for Sheehan's approval,
  not sent.
- **8 holds as well**: the never-scored candidates that would fail go out as leads for people to check one by one.
- Nothing here says whether any candidate is or is not a planet. A Skye flag means a transit coincides with
  clustered artefacts, and real transits can be flagged by mistake.

## Honest limits, fixed in advance

Predictions 5-8 reuse groups whose v1 numbers have been seen (with the old bins). Only 3 and 4 use data no
earlier run has looked at. Every v2 change was fixed by the reference code, the Robovetter source or the v1
pre-registration's own text, with no parameter chosen after seeing per-KOI results. Intra-quarter gaps are still
not removed, and we have no per-event SES. DR25's flag covers every TCE period; only P > 45 d is compared.
