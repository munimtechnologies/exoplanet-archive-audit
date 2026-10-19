# Results: the open Skye variant applied to long-period KOIs (skye_apply 0.1.0)

MV2 of Munim, Inc., 2026-10-19. Written by AI agents working in his name; no person has checked it yet. Text CC BY
4.0, code Apache-2.0. Scores `findings/2026-10-19-skye-apply-prereg.md` strictly, against the thresholds fixed there
before the job ran. Outputs: `results/2026-10-19-skye-apply-0.1.0/`.

## The run

skye-apply-v1 (`skye_apply.py` 0.1.0, sha256 `9e098dafb7929804e8cd384178717789d02ae6dc2c79530fa48fd8cc4761164f`) ran
2026-10-19 07:24-07:26 UTC in a sealed container. In order:

1. **Gate: open.** The pre-registration was live on `main` and the published `skye_apply.py` matched the code that
   ran (`"prereg_live": true, "code_matches": true`).
2. **OBS reproduction: passed, both routes.** `run_variant` and the `frozen_bins` route each gave tp 3,829, fp 1,364,
   fn 446, tn 8,313 (skye_diag 0.1.0's counts), from 128,918 valid cadences in the same 34 light-curve files.
3. Only then were the 2,257 KOIs scored and the Robnik et al. cross-check attempted.

## Scores

| # | Prediction | Result | Verdict |
|---|---|---|---|
| A0 | Unit tests pass | 20 / 20, `OK` | **holds** |
| A1 | OBS reproduction, both routes | 3,829 / 1,364 / 446 / 8,313 twice | **holds** |
| A2 | KOI data check | rows 2,257; with skygroup 2,257; events and skygroup equal v3's 2,257; valid cadences 128,918 | **holds** |
| A5 | dr25_pc fail fraction <= 0.10 | 4 / 668 = 0.006 (4 x 10 = 40 <= 668) | **holds** |
| A6 | dr25_skye flagged >= 70 % | 101 / 109 = 0.927 (1,010 >= 7 x 109 = 763) | **holds** |
| A3 | K05269.01 and K05227.01 both fail | both pass: 3 kept events each, **0 flagged** | **fails** |
| A4 | never_dr25 fail fraction >= 2 x max(pc, 0.02), tail p <= 0.01 | 19 / 414 = 0.0459 vs 2 x 0.02 = 0.04 (1,900 >= 1,656); p = 0.00084 at rate 0.02 | **holds** |
| Q1-Q3 | Robnik et al. cross-check | data check failed (see below) | **void, nothing claimed** |

Every count above was re-counted by hand from the published `koi_frozen.csv` (never_dr25: 414 eligible, 19 fail;
dr25_pc: 668, 4 fail; dr25_skye: 101 of 109 with a flagged kept event, 65 fail; events_match = 1 on all 2,257 rows).

Our forecast, written before the run, called A3 a coin flip leaning "both still fail". It failed.

## A3 fails: the KOI-5269.01 / KOI-5227.01 lead is withdrawn

Under v3 (`skye_census` 0.2.1), both candidates (skygroup 66, P = 371.5 d, three events each) would have failed
Skye: v3 flagged their events near BKJD 631.6 and 1003.0. Under the variant validated on DR25's inverted run, none of
their six events falls in a bad bin. Whatever v3 saw there came from parts of v3 that validation replaced (rogue
TCEs in the bins, events without data, or the rate over empty bins); these outputs do not say which. **We withdraw
the earlier suggestion that these two candidates' transits coincide with Skye artefacts.** No note about them was
ever sent to the Exoplanet Archive, and none will be.

## How it reads, under the rule fixed in advance

A2, A5 and A6 hold, so the per-KOI results are published as **leads, not verdicts**. A4 holds: candidates that DR25
never scored fail this Skye test more often (19 / 414 = 4.6 %) than DR25's own candidates (4 / 668 = 0.6 %), and
more than twice the 2 % floor. That is what one expects if some later cumulative-table candidates rest on events
that DR25's Skye test would have removed, but it is a census-level statement, not a finding about any one KOI.

## The 19 leads (never_dr25 KOIs that would fail)

| KOI | period (d) | skygroup | kept | flagged | good |
|---|---|---|---|---|---|
| K00682.01 | 562.17 | 58 | 3 | 1 | 2 |
| K04426.01 | 369.13 | 58 | 4 | 4 | 0 |
| K05291.01 | 525.56 | 66 | 3 | 1 | 2 |
| K05228.01 | 546.53 | 66 | 3 | 1 | 2 |
| K05237.01 | 380.39 | 66 | 3 | 1 | 2 |
| K05649.01 | 426.94 | 22 | 3 | 1 | 2 |
| K05408.01 | 415.75 | 60 | 3 | 1 | 2 |
| K05423.01 | 366.56 | 58 | 3 | 2 | 1 |
| K05434.01 | 581.87 | 58 | 3 | 1 | 2 |
| K05570.01 | 574.65 | 42 | 3 | 2 | 1 |
| K05578.01 | 388.05 | 28 | 3 | 2 | 1 |
| K05467.01 | 502.84 | 58 | 3 | 2 | 1 |
| K05618.01 | 318.49 | 55 | 3 | 1 | 2 |
| K05380.01 | 369.93 | 62 | 3 | 1 | 2 |
| K05385.01 | 331.71 | 60 | 3 | 1 | 2 |
| K05398.01 | 551.22 | 58 | 3 | 3 | 0 |
| K05973.01 | 419.93 | 4 | 3 | 1 | 2 |
| K07136.01 | 441.17 | 43 | 3 | 1 | 2 |
| K07592.01 | 381.98 | 42 | 3 | 2 | 1 |

Flagged event times (BKJD) are in `summary.json` (`leads`) and `koi_frozen.csv`. Observed after the run (not tested):

- **Skygroup 58 holds 6 of the 19**, and several of them share bad bins: K00682.01 and K05398.01 at BKJD ~185.8-186.0;
  K04426.01 and K05423.01 at ~604.7; K05467.01 and K05398.01 at ~737.0; K05423.01 and K05434.01 at ~971.3-971.7.
  Their flagged "transits" may be the same artefact events seen by several ephemerides.
- 6 of the 19 have periods within 340-400 d, near Kepler's 372.5 d orbit, where seasonal artefacts recur.
- Only two (K04426.01, K05398.01) have no unflagged event left; the other 17 keep one or two.
- K04426.01, K05423.01 and K05398.01 were looked up by hand in earlier runs (they are in the cross-check's exclusion
  list), so they are not independent of what we had already seen.

## The Robnik et al. 2026 cross-check is void (a parsing bug, found after the run)

Its pre-registered data check required 406 data rows in `unrecovered_candidates.csv` (Robnik et al. 2026,
github.com/JakobRobnik/exo-probability). The job read **431 rows and 0 KOI names**, so Q1-Q3 were not scored and
nothing is claimed. Cause, found after the run: the file opens with 25 comment lines starting with `#`; the parser
(`read_table`, copied unchanged from `robnik_crosscheck` 0.1.0) took the first comment line as the header, so no
`KOI` column existed. The file itself matches what we counted on 2026-10-18 (406 data rows under a tab-separated
header with a `KOI` column). The all-zero "listed" columns in `crosscheck.csv` and the p = 1.0 values in `report.md`
are artefacts of this bug, not results. The population and its fail/pass split (640 KOIs: 20 fail, 620 pass; 340-400 d:
6 / 77; in DR25: 4 / 271) do not depend on that file. A fix will be pre-registered as a separate amendment before any
re-run; the join of these KOIs with Robnik et al.'s list has still not been seen.

## What the numbers do not say

1. On OBS this variant's precision against DR25's Skye flags is 0.737 (false-positive rate 0.141); on DR25's inverted
   run the false-positive rate was 0.204 at a higher base rate (42.9 % vs 30.6 %). Any single lead may be a false
   alarm of this re-implementation.
2. Only Skye is modelled. DR25's other individual-transit tests and its MES re-check are not, so `would_fail` is a
   Skye-only count rule, not a disposition.
3. "Valid cadence" is a two-star proxy (KIC 9018021, 6359929); module outages are not seen.
4. A DR25 TCE's own events are in the bins; a never_dr25 KOI's are not, which works against A4, not for it.
5. No person has looked at any of these light curves. Nothing here goes to the Exoplanet Archive or to any author
   unless a person has checked them.

## Files (`results/2026-10-19-skye-apply-0.1.0/`)

- `summary.json`: the run record (gate, OBS reproduction, checks, groups, named KOIs, changes vs v3, tests, leads).
- `report.md`: the run's own report (its Robnik table is void, see above).
- `koi_frozen.csv`: one row per KOI (2,257): ephemeris, skygroup, events, kept / flagged / good, would_fail, v3's
  would_fail, group membership, flagged and kept times.
- `crosscheck.csv`: the 640-KOI cross-check population; its `robnik_listed` column is void (all 0 from the bug).

Changes vs v3 (would_fail): dr25_pc 3 fail-to-pass, 0 pass-to-fail; dr25_skye 3 / 18; never_dr25 4 / 1.
