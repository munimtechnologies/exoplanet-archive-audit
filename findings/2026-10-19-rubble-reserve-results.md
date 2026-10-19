# Rubble reserve results: P1 and P2 both hold on 200 untouched stars

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-10-19 ~15:30 UTC by AI agents working in his name; not
checked by a person. Apache-2.0 code, CC BY 4.0 text.

## Summary

Job `rubble-reserve-v1` (`scan_rubble.py` 0.2.0 `--reserve`) ran on 2026-10-19 from 14:35:55 to 14:42:10 UTC. Its
gate fetched the pre-registration (`findings/2026-10-19-rubble-reserve-prereg.md`) and the published
`results/2026-10-19-rubble-scan-0.1.0/sample.json` from this repository's raw URLs before any reserve star was
downloaded, and `check_gate` passed. It then scanned the 200 `reserve_never_downloaded` stars: 361 Kepler DR25
TCEs, all 361 scored (status `ok`). Both pre-registered decisions, read from `reserve.json` as written:

- **P1 (empty `MODEL_WHITE` iff half-hour-multiple duration): holds.** a/b/c/d = 18/0/0/343, skipped 0, n = 361.
  Powered (a + b = 18 >= 5); off-diagonal (b + c) = 0, and 0 x 50 <= 361.
- **P2 (`init_2_0.75` recall >= 0.9 and precision <= 0.8): holds.** tp/fp/fn/tn = 133/125/0/103. Powered
  (tp + fn = 133 >= 20); recall: 10 x 133 = 1330 >= 9 x 133 = 1197; precision: 5 x 133 = 665 <= 4 x 258 = 1032.

The outcome matches the one stated before the run ("P1 holds and P2 holds").

## Integrity checks (all true)

`rv_rows_ok` (32,534 Robovetter rows), `rv_sha256_ok` (3d6689de...c49655), `controls_ok` (KIC 6922244.01: 384
real events / 4 fails; KIC 11442793.05: 7 / 2, both as hand-counted in the probe), `sample_size_ok`,
`no_dev_star_scanned`. The unit tests of `scan_rubble.py` and `fetch_published.py` passed in the same job.

Hand check: counting `tces.csv` rows by `iflags` first digit and `fail_init_2_0.75` gives the same 133/125/0/103,
and all 18 rows with `half_hour` = 1 have `white_cadences` = 0 while no row with `half_hour` = 0 does.

Expected sizes stated in the pre-registration were rough: about 400 TCEs (361 came), about 25 half-hour durations
(18), about 200 Rubble-flagged (133). Both tests were powered regardless.

## Confirm job for the development decision

`pick-variant-dev-v1` re-ran the published `pick_variant.py` 0.1.0 on the published development `variants.json`
(14:28:34-14:29:58 UTC). It returned `negative`, best error rate 0.224 (`init_2_0.75`), the same as the hand
application in `findings/2026-10-19-rubble-scan-results.md`. Its `decision.json` and `decision.md` are added to
`results/2026-10-19-rubble-scan-0.1.0/`. No disagreement.

## What this means

- **P1** is now a tested statement about the public DV time-series files: in the 486 DR25 TCEs scanned so far
  (125 development + 361 reserve), a TCE's `MODEL_WHITE` series is empty in every transit exactly when its
  Robovetter duration is a whole multiple of 0.5 h (26 such TCEs, 1.5 to 15 h). Anyone using `MODEL_WHITE` from
  these files should check for this. This test does not show the cause; see the prior-art paragraph below for the
  most likely one.
- **P2** shows that the over-flagging found on the development stars is not sample-specific: DR25's Rubble
  settings as Thompson et al. (2018) word them, applied to the public `LC_INIT` series, catch every DR25 Rubble TCE
  (recall 133/133) but also flag more than half of the TCEs DR25 passed. Together with the development result this
  closes the lane: the per-TCE Rubble flag cannot be re-derived from the public DV files and the paper's wording.

## Descriptive only (not pre-registered, not scored)

1. **The gap is larger on the reserve.** `init_2_0.75` disagrees with DR25 on 125 of 361 TCEs (34.6 %, against
   22.4 % on development); precision 133/258 = 0.516 (development 0.702). It flags 125 of the 228 TCEs DR25 passed
   (55 %; development 28/59, 47 %).
2. **Over-flags are mostly not near-misses.** Among the 125 false positives, 40 have 1-2 real events failing the
   variant, 49 have 3-9 and 36 have 10 or more.
3. **Most over-flagged TCEs carry another per-event flag.** 107 of the 125 have DR25's Skye, Zuma or Tracker flag
   set (development: 26 of 28). That fits, without proving, DR25 having evaluated Rubble only on events not
   already removed by those metrics; the public per-TCE input has no per-event flags to test it.
4. **First TCEs on a star are over-flagged more often.** Planet number 1: fp 93 of 151 passed TCEs (62 %);
   planet number > 1: 32 of 77 (42 %). Recall is 47/47 and 86/86.
5. **Event counts.** Events with any finite `LC_INIT` cadence in transit match `nrealt` exactly for 167 of 361 TCEs
   and within one for 210 (over by more than one: 41; under: 110). `RESIDUAL_LC` again has no finite cadence near
   mid-transit for any TCE, so every `resid` variant flags every TCE.

## Why this is new, and its limits

No public code that we found derives DR25's Rubble flag or `nrealt` from the light curves and checks them per TCE
against the Robovetter input (searched 2026-10-19). This series of notes is, as far as we know, the first open
per-TCE attempt, with every decision rule published before its data were read.

P1 is less new than it looks, and we say so plainly. A prior-art search made after the run (2026-10-19 ~15:40 UTC)
found that the Exoplanet Archive's Kepler DV documentation already says, for the DR24 file format, that "If the DV
process fails to converge for a given TCE, the MODEL_LC_PL flux will be given as NaN"
(https://exoplanetarchive.ipac.caltech.edu/docs/KeplerDV.html). Thompson et al. (2018, Sec. II.4) also note that
"Sometimes the DV fitter fails to converge". The 10 distinct durations seen (1.5, 2.0, 3.0, 3.5, 6.0, 7.5, 9.0,
10.5, 12.5 and 15 h) look like trial-pulse widths of the Kepler transit search, which would fit failed DV fits
whose listed duration is the search's pulse width rather than a fitted value. We did not find a DR25 document saying
this, and did not check the pulse grid against a source in this run, so it remains the likely explanation, not a
shown one. What the test adds is narrower: an exact, held-out check that these empty-model TCEs can be picked out
from the Robovetter input's duration column alone (no false positives or misses in 486 TCEs).

Limits: 260 stars and 486 TCEs from one seed (20261019) out of DR25's 32,534 TCEs; agreement is measured against
DR25's flags, not against truth; a TCE agrees if any of its events fails, even if not the same event DR25 used;
`events.csv` (about 124,000 rows) is not in the repository but is rebuilt by re-running `scan_rubble.py` 0.2.0
(deterministic, public inputs). No clean Rubble sample remains from this seed: any further Rubble test needs a new
seed and must exclude all 268 stars looked up so far. Everything here was made with AI agents in MV2's name and
has not been checked by a person.

## Files

- `results/2026-10-19-rubble-reserve-0.2.0/`: `reserve.json` (decisions), `summary.json` (gate, checks,
  controls), `variants.json` (all 24 variants, split by planet number), `tces.csv`, `sample.json`, `report.md`
- `results/2026-10-19-rubble-scan-0.1.0/decision.json`, `decision.md` (confirm job)
- Code that ran: `scan_rubble.py`, `test_scan_rubble.py`, `fetch_published.py`, `test_fetch_published.py` (0.2.0,
  already in the repository)
- Prior notes: `findings/2026-10-19-rubble-probe-results.md`, `findings/2026-10-19-rubble-variant-rule-prereg.md`,
  `findings/2026-10-19-rubble-scan-results.md`, `findings/2026-10-19-rubble-reserve-prereg.md`

MV2, Munim, Inc., mv2@munimtech.com
