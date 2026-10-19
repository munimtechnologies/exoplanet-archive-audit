# Rubble scan results: the pre-registered rule returns NEGATIVE

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-10-19 ~13:40 UTC by AI agents working in his name; not
checked by a person. Apache-2.0 code, CC BY 4.0 text.

## Summary

Job `rubble-scan-v1` (`scan_rubble.py` 0.1.0, exploratory, seed 20261019) ran on 2026-10-19 from 12:58:55 to
13:00:21 UTC on 60 development stars (125 Kepler DR25 TCEs, all scored). It compared 24 public re-derivations of
DR25's Rubble metric (cadence source x window x threshold) with DR25's per-TCE `iflag0` (RUBBLE) from NASA's
Robovetter input file. The variant-selection rule was published before the scan started
(`findings/2026-10-19-rubble-variant-rule-prereg.md` and `pick_variant.py` 0.1.0, written ~10:20 UTC).

Applying that rule gives **negative**: the best variant disagrees with DR25 on 28 of 125 TCEs (22.4 %), above the
pre-registered 20 % floor (25 TCEs). No variant is chosen, and the planned held-out reserve test (200 stars listed
in `sample.json`, never downloaded) will **not** run. This is the result of the lane: with the public DV
time-series files and the rule as Thompson et al. (2018) word it, DR25's per-TCE Rubble flags are not reproduced
to within 20 %.

## Integrity checks (all true)

`rv_rows_ok` (32,534 Robovetter rows), `rv_sha256_ok` (3d6689de...c49655), `controls_ok` (two hand-counted
regression controls from the earlier probe reproduced exactly: KIC 6922244.01 384 real / 4 fails, KIC 11442793.05
7 real / 2 fails), `dev_size_ok` (60 stars). The 21 unit tests passed in the same job.

## The rule, applied step by step (integer arithmetic)

- **R1 power.** Scored TCEs with `iflag0` = 1: tp + fn = 66 (>= 20). Rubble-only TCEs: 17 (>= 8). Powered.
- **R2 floor.** error = fp + fn per variant, n = 125:

| source | w1 0.25 | w1 0.5 | w1 0.75 | w2 0.25 | w2 0.5 | w2 0.75 |
|---|---|---|---|---|---|---|
| init | 16+34=50 | 23+17=40 | 30+5=35 | 3+52=55 | 23+12=35 | **28+0=28** |
| white | 13+50=63 | 17+45=62 | 23+33=56 | 3+61=64 | 17+43=60 | 22+37=59 |
| pdc | 16+47=63 | 23+37=60 | 30+28=58 | 2+62=64 | 22+36=58 | 28+30=58 |
| resid | 59+0=59 | 59+0=59 | 59+0=59 | 59+0=59 | 59+0=59 | 59+0=59 |

  Minimum error = 28 (init, window 2 durations, threshold 0.75). Test 5 x 28 = 140 > 125, so every variant is
  above 20 % of n: **status negative**. R3-R6 do not apply.

Deviation from the pre-registration, stated plainly: the note said `pick_variant.py` would be run as a job and its
`decision.json` published in this same commit. The rule was applied by hand here (the arithmetic above is the whole
decision). A small job (`pick-variant-dev-v1`) re-runs the published `pick_variant.py` 0.1.0 on this commit's
`variants.json`; its output will be published as a follow-up and any disagreement reported, not hidden.

## What the numbers show (exploratory, after the fact; not scored)

1. **DR25's own settings come closest, and they over-flag.** The winning variant is the one the paper describes:
   two transit durations, threshold 0.75, on the TCE's own `LC_INIT` series. It finds every DR25 Rubble TCE
   (recall 66/66) but also flags 28 of the 59 TCEs DR25 passed (precision 66/94 = 0.702; agreement 97/125 =
   0.776). The earlier nine-TCE probe saw the same direction (TP 2, FP 3, FN 0, TN 4).
2. **The over-flags are not near-misses.** Among the 28 false positives, the number of real events failing the
   variant is 1-2 for 6 TCEs, 3-9 for 7, and 10 or more for 15 (median 11; up to 38 for KIC 7031753.01). So DR25's
   Rubble either saw different cadence availability than the exported `LC_INIT` series, or skipped events in a way
   the paper's wording does not state. 26 of the 28 carry another per-event flag (Skye, Zuma or Tracker); whether
   DR25 evaluated Rubble only on events not already removed by those metrics cannot be tested from the public
   per-TCE input, which has no per-event flags.
3. **Event counts are close but not exact.** Counting events with any finite `LC_INIT` cadence in transit matches
   DR25's `nrealt` exactly for 45/125 TCEs and within one for 59/125 (PDCSAP: 45 and 62). Earlier TCEs' transits
   removed from `LC_INIT` push counts both ways (`LC_INIT`: 27 TCEs over and 39 under by more than one).
4. **`RESIDUAL_LC` is gapped in transit.** For all 125 TCEs, no event had a finite `RESIDUAL_LC` cadence within
   half a duration of mid-transit, so every resid variant flags every TCE. That series cannot serve for Rubble.
5. **Empty `MODEL_WHITE` marks a different duration.** 8 TCEs have no finite `MODEL_WHITE` cadence in any
   transit (KIC 3458687.10, 4647763.03, 6356144.08, 6543674.01, 7138415.04, 9899153.04, 11140501.01,
   11597669.01). Those are exactly the 8 of 125 whose Robovetter duration is a whole multiple of 0.5 h (1.5, 2.0,
   3.0, 3.5, 7.5, 10.5 h); none of the other 117 has an empty `MODEL_WHITE`. This fits a DV fit that did not
   converge, leaving the search's trial pulse width as the duration, but that explanation is a guess here.

Points 2 and 5 are patterns noticed after looking at the data. They would need their own pre-registered test
before being claimed.

## Why this is new, and its limits

No public code that we found derives DR25's Rubble flag or `nrealt` from the light curves and checks them per TCE
against the Robovetter input (searched 2026-10-19). This is the first open, per-TCE attempt, and it says where the
paper's wording plus the public files stop being enough.

Limits: 60 stars, 125 TCEs, one seed; agreement is measured against DR25's flags, not against truth; a TCE counts as
agreeing if any event fails, even if it is a different event than DR25's; `events.csv` (about 4 MB) is not in the
repository but is rebuilt by re-running `scan_rubble.py` (deterministic, public inputs). Everything here was made
with AI agents in MV2's name and has not been checked by a person.

## Files

- `scan_rubble.py`, `test_scan_rubble.py` (0.1.0, the code that ran)
- `results/2026-10-19-rubble-scan-0.1.0/`: `summary.json`, `variants.json`, `tces.csv`, `sample.json`, `report.md`
- Prior notes: `findings/2026-10-19-rubble-probe-results.md`, `findings/2026-10-19-rubble-variant-rule-prereg.md`

MV2, Munim, Inc., mv2@munimtech.com
