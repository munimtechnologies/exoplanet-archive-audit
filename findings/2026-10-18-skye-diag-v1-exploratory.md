# Exploratory: why skye-census-v3 missed DR25's Skye flags (skye_diag 0.1.0)

MV2 of Munim, Inc., 2026-10-18. Written by AI agents working in his name; no person has checked it yet. Text CC BY
4.0, code Apache-2.0. Code: `skye_diag.py` 0.1.0 and `test_skye_diag.py` (11 tests, all passed in the run). Outputs:
`results/2026-10-18-skye-diag-v1/`.

**This is exploratory, not a validated result.** It re-reads DR25 OBS flags that the scored v3 run had already
compared against. It measures how much of v3's miss each suspected cause explains; the fix it points to is tested on
a held-out set in `findings/2026-10-18-skye-inv-prereg.md`.

## The run

skye-diag-v1 ran 2026-10-18 22:45-22:51 UTC in a sealed container. Its inputs were v3's published `tce_skye.csv`
(15,349 rows, sha256 `08229984...`) and `skygroups.csv` (8,887 rows, `df75339b...`), plus the 34 Q1-Q17 long-cadence
files of KIC 9018021 and KIC 6359929 from MAST (128,918 valid cadences, 1,391 one-day bins holding data). Its
first variant reproduced v3's counts exactly (tp 3,382, fp 1,621, fn 893, tn 8,056), so the comparison stands.

## Results (13,952 Robovetter-scored TCEs with P > 45 d)

| variant | tp | fp | fn | tn | recall | precision | F1 |
|---|---|---|---|---|---|---|---|
| v3 (as scored) | 3,382 | 1,621 | 893 | 8,056 | 0.791 | 0.676 | 0.729 |
| scored_only (bins without the 1,397 rogue TCEs) | 3,792 | 1,401 | 483 | 8,276 | 0.887 | 0.730 | 0.801 |
| real_events_w0.25 (events near data, rogues kept) | 3,639 | 1,778 | 636 | 7,899 | 0.851 | 0.672 | 0.751 |
| scored_only + real_events_w0.25 | 3,839 | 1,573 | 436 | 8,104 | 0.898 | 0.709 | 0.793 |
| **scored_only + real_events_w0.25 + data_bins** | 3,829 | 1,364 | 446 | 8,313 | 0.896 | 0.737 | **0.809** |
| scored_only + real_events_w0.1 + data_bins | 3,822 | 1,411 | 453 | 8,266 | 0.894 | 0.730 | 0.804 |
| scored_only + real_events_w0.5 + data_bins | 3,791 | 1,382 | 484 | 8,295 | 0.887 | 0.733 | 0.802 |

All 11 variants are in `results/2026-10-18-skye-diag-v1/report.md`. F1 = 2 tp / (2 tp + fp + fn), computed here from
the counts.

## What it shows

1. **Rogue TCEs were the main cause.** Leaving DR25's 1,397 long-period rogue TCEs out of the bins (DR25 left them out
   of the catalogue and of Skye; confirmed against the Archive's `tce_rogue_flag` in
   `findings/2026-10-18-v3-rogue-confirmation.md`) lifts recall from 0.791 to 0.887 and precision from 0.676 to 0.730.
   False negatives fall from 893 to 483.
2. **Events in data gaps matter less than expected.** Keeping only events within 0.25 d of a valid cadence and taking
   the rate over bins that hold data adds about one point of precision (0.730 to 0.737) and one of recall.
3. **The remaining false positives sit where our event count exceeds DR25's.** Split by v3's events against DR25's
   count of real transits (`nrealtrans`): where they are equal (8,111 TCEs) precision is 0.843; where ours is larger
   (5,564 TCEs) it is 0.488. DR25 counts only transits with a non-zero single-event statistic, from transit-times
   files that are not public; a valid-cadence proxy from two stars only partly stands in for that.
4. **No variant reaches both of v3's bars** (recall 0.85, precision 0.75). The best F1 variant is at 0.896 / 0.737.

## Limits

- Exploratory on seen data; the best variant was picked on the same data it is scored on, so its numbers are
  optimistic.
- "Valid cadences" come from two stars. Module-level outages (such as module 3 after Q4) are not modelled.
- Nothing here changes v3's scored predictions, and nothing is claimed about any candidate.

## Next

The best-F1 variant is frozen and tested on DR25's inverted-light-curve run (INV), whose Skye flags this project
has never opened: `findings/2026-10-18-skye-inv-prereg.md`.
