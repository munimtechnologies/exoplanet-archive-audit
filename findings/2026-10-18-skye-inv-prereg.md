# Pre-registration: a held-out test of the open Skye re-implementation on DR25's inverted run (INV)

MV2 of Munim, Inc., 2026-10-18 ~23:50Z. Written by AI agents working in his name; no person has checked it yet. Text
CC BY 4.0, code Apache-2.0. Code: `skye_inv.py` 0.1.0 and `test_skye_inv.py`, committed together with this file.

## Why

skye-census-v3 failed its pre-registered bars against DR25's own per-TCE Skye flags on the observed (OBS) TCEs
(`findings/2026-10-18-skye-census-v3-results.md`). The exploratory diagnosis `skye_diag` 0.1.0
(`findings/2026-10-18-skye-diag-v1-exploratory.md`) found the main cause (DR25's rogue TCEs had been counted in the
sky bins) and tried gap rules. All of that re-used OBS flags we had already seen, so none of it is validated. This
pre-registration fixes, before any of it is opened, a test on a set we have **never opened**: the Robovetter input of
DR25's INV run (`kplr_dr25_inv_robovetter_input.tar.gz` and `kplr_dr25_inv_robovetter_output.txt` in
github.com/nasa/kepler-robovetter). DR25 ran its Skye test separately on the INV TCEs (Thompson et al. 2018, ApJS 235,
38; Skye.py reads a separate INV transit-times file), and INV uses the same cadences as OBS with the flux inverted.

## What is tested (fixed now; chosen on OBS, not tuned on INV)

The skye_diag variant with the highest F1 on OBS, `scored_only_real_events_w0.25_data_bins` (OBS: tp 3,829, fp 1,364,
fn 446, tn 8,313; recall 0.8957, precision 0.7373, F1 0.8088). It was chosen on OBS out of 11 variants by that one
criterion; we say so plainly. Applied to INV unchanged:

- TCEs: rows of the Archive's `kplr_dr25_inv_tces.txt` (IPAC table, `\nrows = 19536`) with period > 45 d.
- Bins: per skygroup, the events of those TCEs that are in the INV Robovetter input. Skygroups and long-cadence
  quarters come from v3's published `skygroups.csv`, plus MAST lookups for INV stars not in it (published as
  `inv_skygroups.csv`).
- Events: t0 + nP inside the star's long-cadence quarters, kept only within 0.25 d of a valid cadence (finite TIME and
  PDCSAP_FLUX) in the Q1-Q17 files of KIC 9018021 or KIC 6359929.
- Rate: over the bins of the skygroup's quarters that hold a valid cadence; Skye.py's cutoff R + 3 sqrt(R), five passes.
- A TCE is flagged when one of its kept events lies in a bad bin of its skygroup; it is compared with DR25's iflag3
  ("at least one transit event failed SKYE"), 0-based column 11 of the Robovetter input.

Reported alongside, not tested: `scored_only` (no light curves) and `all_tces`.

## Safeguards built into the job

1. **Gate.** Before opening anything from the INV Robovetter files, the job fetches this file and `skye_inv.py` from
   the repository's main branch. If this file is not live, or the published `skye_inv.py` differs from the code the
   job runs, it stops.
2. **OBS reproduction.** It then re-runs the chosen variant on OBS from v3's published outputs and must reproduce
   skye_diag 0.1.0's counts exactly (tp 3,829, fp 1,364, fn 446, tn 8,313). Otherwise it stops, still without opening
   the INV flags.

## Predictions (thresholds fixed here)

| # | Prediction | Threshold |
|---|---|---|
| 1 | Unit tests pass | all of `test_skye_inv.py` |
| 2 | Data check, every part | INV TCE rows parsed >= 0.99 x 19,536; INV Robovetter input rows >= 0.99 x 19,536; its header names columns 2, 3, 5, 6, 7, 11 KIC, pn, ntrans, nrealt, ngoodt, iflag3 (as in OBS); >= 99 % of INV stars with P > 45 d TCEs get a skygroup; >= 99 % of INV TCEs with P > 45 d are in the Robovetter input; >= 50 INV TCEs whose Robovetter comment names SKYE, and >= 99 % of them carry iflag3 = 1; valid cadences = 128,918 (as skye_diag) |
| 3 | TCE recall of the chosen variant on INV | tp / (tp + fn) >= 0.85 |
| 4 | TCE precision of the chosen variant on INV | tp / (tp + fp) >= 0.75 |
| 5 | The light-curve gap rule helps on INV | F1(chosen) > F1(scored_only), strictly |

Bars 3 and 4 are the same as v2/v3's, unchanged. Prediction 2's row bars derive from the table's stated 19,536 rows
(Thompson et al. 2018 §II.2: rogue TCEs were removed from every population, so the INV table is the Robovetter-scored
set).

**Our forecast, stated before seeing anything:** on OBS the chosen variant meets bar 3 (0.896) but misses bar 4
(0.737). We expect P3 to hold and P4 more likely than not to fail; P5's OBS gain was small (F1 0.8088 vs 0.8010) and
could go either way.

## What each outcome means

- Gate or OBS reproduction fails: void; nothing from INV was opened. A fixed run needs a public amendment first.
- P2 fails: the ground truth was not read correctly; nothing is claimed about agreement.
- P3 and P4 hold: the open re-implementation reaches the pre-set agreement with DR25 on a set it was not tuned on.
  Only then will a **separate** pre-registration apply it to KOI-5269.01, KOI-5227.01 and the candidates DR25 never
  scored.
- P3 or P4 fails: the Skye arc closes with a negative-result note quantifying the remaining gap (an open
  re-implementation without the per-transit transit-times files that DR25's Skye.py read, which are not public,
  did not reach these bars). No claims about any candidate.
- P5 is reported either way; it does not gate anything.

## Limits known now

- "Valid cadence" is a proxy built from two stars; module-level outages (for example module 3 after Q4) are not seen.
- INV TCEs are by construction false alarms, so INV's Skye flags may be more frequent than OBS's; the bars are about
  agreement with DR25's flags, not about planets.
- A Skye flag marks a transit that coincides with clustered artefacts. It is not a verdict on whether a candidate is a
  planet.
