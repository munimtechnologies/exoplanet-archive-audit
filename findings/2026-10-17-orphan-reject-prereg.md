# Pre-registration: are orphans on stars where DR25 found nothing rejected more often? (orphan_reject 0.1.0)

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Code Apache-2.0, text and data CC BY 4.0. Committed **before** the job runs; scored in public, misses included.

## Why

findings/2026-10-17-lissauer-xmatch-results.md found that Lissauer et al. 2024 reject 316 of the Archive's
600 "orphan" CANDIDATEs (parameters from Q1-Q16 or DR24, not DR25). findings/2026-10-17-orphan-census-results.md
sorted the same 600 by what DR25 found on their star: 437 stars with no DR25 TCE at all (no_tce), and 163
with at least one (unrelated, offset or same_events). This joins the two. If DR25 seeing nothing at all on
a star goes with a weaker signal, no_tce orphans should be rejected more often.

## Method (orphan_reject 0.1.0)

- Inputs: results/2026-10-17-koi-orphans-0.1.0/orphans.csv and results/2026-10-17-lissauer-xmatch-0.1.0/xmatch.csv
  (fetched from this repository), and the rogue TCEs of q1_q17_dr25_tce (tce_rogue_flag = 1, live TAP).
- Rejected = Lissauer's first Status letter is F, S, M or R. Rates by census status and by provenance;
  no_tce vs with-TCE compared with a one-sided Fisher exact test (pure Python).
- Flags whether each orphan's matched TCE is rogue and whether any rogue TCE sits on its star.

11 unit tests on real rows (KOI-600.02, 1101.02, 2433.06, 364.01, 823.01, 1096.01) with hand-worked values.

## Predictions

1. All 11 unit tests pass.
2. Consistency: 600 orphans joined, none missing; 316 rejected; 1,498 rogue TCEs.
3. no_tce orphans are rejected at a higher rate than orphans with a DR25 TCE on the star, one-sided
   Fisher p < 0.05.
4. Consistency: same_events_on_rogue_tce lists exactly K00600.02, K03401.02, K04333.01, K05126.01,
   K05423.01, K05613.01 and K06151.01 (read by hand from the census outputs before this job).
5. Exploratory: 8-30 orphans have at least one rogue TCE on their star.

## How it will be read

Only 3 is a test; 2 and 4 check the plumbing. If 3 fails, the reading is that DR25's silence on the whole
star does not, by itself, mark a weaker orphan. Either way it describes Lissauer's vetting, not new
dispositions.
