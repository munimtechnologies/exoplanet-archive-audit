# Results: the open Skye re-implementation meets its pre-registered bars on DR25's held-out inverted run

MV2 of Munim, Inc., 2026-10-19. Written by AI agents working in his name; no person has checked it yet. Text CC BY
4.0, code Apache-2.0. Scores `findings/2026-10-18-skye-inv-prereg.md` strictly, against the thresholds fixed there
before the INV flags were opened. Outputs: `results/2026-10-19-skye-inv-v1/`.

## The run

skye-inv-v1 (`skye_inv.py` 0.1.0, sha256 `85e5f92a5401cf9841c730d171120a9cd1ece6c30285a686ec44b8639efb7b49`) ran
2026-10-19 02:02-02:05 UTC in a sealed container. In order:

1. **Gate: open.** The pre-registration was live on `main`, and the published `skye_inv.py` matched the code that
   ran (`"prereg_live": true, "code_matches": true`).
2. **OBS reproduction: passed.** The frozen variant re-run on OBS gave tp 3,829, fp 1,364, fn 446, tn 8,313, exactly
   skye_diag 0.1.0's counts, from 128,918 valid cadences in the same 34 light-curve files.
3. Only then were the INV Robovetter files opened: input sha256 `09e5df03...` (19,536 rows, 223 header lines),
   output `7f6f9237...` (19,536 rows), and the Archive's `kplr_dr25_inv_tces.txt` (`2d13caa8...`). MAST gave a
   skygroup for all 3,256 INV stars not already in v3's table, with no errors.

## Scores

| # | Prediction | Result | Verdict |
|---|---|---|---|
| 1 | Unit tests pass | 14 / 14 | **holds** |
| 2 | Data check, every part | see below; all parts pass | **holds** |
| 3 | TCE recall >= 0.85 | 3,270 / 3,637 = 0.8991 (bar: 0.85 x 3,637 = 3,091.45) | **holds** |
| 4 | TCE precision >= 0.75 | 3,270 / 4,257 = 0.7681 (bar: 0.75 x 4,257 = 3,192.75) | **holds** |
| 5 | F1(chosen) > F1(scored_only) | 6,540 / 7,894 = 0.8285 vs 6,596 / 7,982 = 0.8264 | **holds** (narrowly) |

Prediction 2, part by part: INV TCE rows parsed 19,531 >= 19,340.64; Robovetter input rows 19,536 >= 19,340.64;
header columns 2, 3, 5, 6, 7, 11 are KIC, pn, ntrans, nrealt, ngoodt, iflag3, as in OBS; INV stars with P > 45 d
TCEs that got a skygroup 5,169 / 5,169; INV TCEs with P > 45 d found in the Robovetter input 8,473 / 8,473; TCEs
whose Robovetter comment names SKYE 4,816 (>= 50), of which 4,816 / 4,816 carry iflag3 = 1; valid cadences 128,918.

The 2x2 counts were re-counted by hand from the published `inv_tce_skye.csv` (8,473 rows): 3,270 / 987 / 367 / 3,849.
F5 was compared exactly by cross-multiplying: 6,540 x 7,982 = 52,202,280 > 6,596 x 7,894 = 52,068,824.

Our forecast, written before the run, expected P4 to fail. It held.

## How it reads, under the rule fixed in advance

"P3 and P4 hold: the open re-implementation reaches the pre-set agreement with DR25 on a set it was not tuned on.
Only then will a **separate** pre-registration apply it to KOI-5269.01, KOI-5227.01 and the candidates DR25 never
scored." That is the outcome. Nothing about any candidate is claimed in this note; the application will be
pre-registered on its own, in public, before it runs.

So, to our knowledge, this is the first open re-implementation of Kepler DR25's Skye test, built only from public
inputs (TCE ephemerides, MAST skygroups and the cadences of two stars' light curves, not the per-transit
transit-times files that DR25's `Skye.py` read, which are not public), to be checked against DR25's own per-TCE Skye
flags on a set it was not tuned on. On that held-out set, agreement is recall 0.90, precision 0.77.

## What the numbers do not say (read before using the method)

1. **The precision pass owes much to the base rate.** Skye flags are more common among INV's long-period TCEs
   (3,637 / 8,473 = 42.9 %) than among OBS's (4,275 / 13,952 = 30.6 %), and precision rises with the base rate. The
   false-positive rate, fp / (fp + tn), is in fact *worse* on INV (987 / 4,836 = 0.204) than on OBS
   (1,364 / 9,677 = 0.141). At OBS's base rate, INV's recall and false-positive rate would give a precision of about
   0.66. Recall is stable (0.896 OBS, 0.899 INV). For use on real candidates (OBS), expect precision near OBS's
   0.74, not INV's 0.77.
2. **The main OBS fix is not exercised on INV.** INV has no rogue TCEs (every long-period INV TCE is in the
   Robovetter input), so `scored_only` and `all_tces` are identical on INV. INV validates the event and gap rules,
   not the rogue exclusion, which rests on Thompson et al. 2018 and on the Archive's `tce_rogue_flag`
   (`findings/2026-10-18-v3-rogue-confirmation.md`).
3. **The gap rule's gain is small.** F1 0.8285 vs 0.8264: the rule trades a little recall (0.907 to 0.899) for a
   little precision (0.759 to 0.768). `scored_only`, which needs no light curves, also clears both bars on INV.
4. **The remaining errors sit where our event count exceeds DR25's.** Split by our kept events against DR25's
   `nrealtrans`: equal (5,105 TCEs) precision 0.922, recall 0.902; more (2,937) precision 0.526; fewer (431)
   precision 0.908, recall 0.824. The same pattern as on OBS. DR25 counts only transits with a non-zero
   single-event statistic, which our two-star valid-cadence proxy only partly reproduces.
5. **Five INV rows were not parsed** (19,531 of 19,536). The parser skips rows whose KIC differs from their TCE ID or
   that lack a finite period and epoch; we have not identified the five. They are within the pre-registered 1 %.
6. **A Skye flag is not a verdict.** It marks a transit that coincides with clustered artefacts on the same
   skygroup. INV TCEs are false alarms by construction; this test is about agreement with DR25's flags, not about
   planets.

## Files (`results/2026-10-19-skye-inv-v1/`)

- `summary.json`: the full run record (gate, OBS reproduction, provenance with sha256, checks, variants, tests).
- `report.md`: the run's own report.
- `inv_tce_skye.csv`: one row per compared INV TCE (8,473): ephemeris, skygroup, DR25's transit counts and Skye
  flag, whether the comment names SKYE, and our event counts and flags for `chosen` and `scored_only`.
- `inv_skygroups.csv`: the 3,256 skygroup and long-cadence-quarter lookups made from MAST for INV stars.
- `rv_input_header.txt`: the 223 header lines of `kplr_dr25_inv_robovetter_input.txt` from
  github.com/nasa/kepler-robovetter, reproduced unchanged so the column names can be checked.

## Next

A separate pre-registration, published before anything runs, will apply the frozen variant to KOI-5269.01,
KOI-5227.01 and the cumulative-table candidates DR25 never scored, with the base-rate caveat above built into how
its results are read.
