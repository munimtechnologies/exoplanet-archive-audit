# skye-census-v3: the 1,397 unmatched long-period TCEs are DR25's rogue TCEs (confirmed)

MV2 of Munim, Inc. — 2026-10-18 ~22:35Z. Made with AI agents working in his name. CC BY 4.0.

The skye-census-v3 results note (findings/2026-10-18-skye-census-v3-results.md) said, by row
matching only, that the 1,397 TCEs with P > 45 d that had no Robovetter input row were DR25's
"rogue" TCEs (Thompson et al. 2018, ApJS 235, 38, §II.2). The Exoplanet Archive TAP service came
back after its outage, so this was checked against the archive's own `tce_rogue_flag` column.

## Checks (NASA Exoplanet Archive TAP, table q1_q17_dr25_tce, queried 2026-10-18 ~22:30Z)

| Query | Result | Expected |
|---|---|---|
| `count(*) where tce_rogue_flag=1` | 1,498 | 1,498 (Thompson et al. 2018 §II.2) |
| `count(*) where tce_rogue_flag=1 and tce_period>45` | 1,397 | 1,397 (v3 unmatched, P > 45) |
| `count(*) where tce_period>45` | 15,349 | 13,952 scored (3,382+1,621+893+8,056) + 1,397 = 15,349 |

In v3's out/skye/tce_skye.csv, the rows with rv_found = 0 number exactly 1,397.

Row-level check on 3 stars and 12 sampled unmatched rows (KIC 7901766, 7910731, 7832446, 7960484,
7832978, 7870746, 7833139, 7882390, 7838958, 7954276, 7885309; every P > 45 TCE of these stars,
23 rows): every row with tce_rogue_flag = 1 has rv_found = 0 in v3, and every row with
tce_rogue_flag = 0 has rv_found = 1. 23 of 23 agree.

## What this means

- Diagnosis (a) of v3 is confirmed: v3's sky bins counted 1,397 rogue TCEs that DR25's Skye
  never saw (Thompson et al. remove rogues from all populations before vetting).
- The counts close exactly (15,349 = 13,952 + 1,397), so no other TCEs were dropped or
  duplicated in v3's matching.
- Limit: the row-level check covers 23 rows; the full-set identity rests on the exact count
  match plus that sample. The skye-diag-v1 "scored_only" variant (queued) removes these rows
  from the bins and measures the effect.

Nothing in v3's scoring changes: its pre-registered predictions P2-P4 still failed.
