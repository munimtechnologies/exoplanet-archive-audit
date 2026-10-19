# SBDB diameter-source results (S1, S2 hold; S3 underpowered): 1,497 of 1,500 served asteroid diameters are NEOWISE's

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-10-19 ~23:30 UTC by AI agents working in his name; scored
strictly against `findings/2026-10-20-sbdb-source-prereg.md` and re-counted by hand, but not checked by a person.
CC BY 4.0 text; code (`sbdb_source.py` 0.1.0, with `sbdb_triplet.py` 0.1.0) Apache-2.0. Outputs:
`results/2026-10-19-sbdb-source-0.1.0/`. Follows `findings/2026-10-19-sbdb-triplet-results.md`.

## Run

Job `sbdb-source-v1` (python:3.12, 1 CPU): 13 unit tests passed; `fetch_published.py` fetched the pre-registration
(text "SBDB diameter-source pre-registration") and the two seen-row files from their public raw URLs before anything
was downloaded; `sbdb_source.py` then read the SBDB Query API (7 pages, 2026-10-19 21:41 UTC) and made 1,500
single-object `sbdb.api?spk=...&phys-par=1` requests, one at a time with a 1 s pause, finishing 22:12 UTC. One
correction to the pre-registration: its filename carries the planned run date, 2026-10-20; the job actually ran on
2026-10-19 (UTC). The gate step confirms the note was public before the data were read, which is what matters.

Integrity checks, all true: gate passed; 340 seen rows loaded; API count stable on every page (138,086); rows =
count; no duplicate spkid. 138,083 rows `ok`, 3 `excluded_probe`; pool after removing the 340 seen rows 137,743;
sample 1,500 (seed 2026101917). All 1,500 requests returned a diameter (status `fetched` 1,500; no `no_diameter`,
`no_phys_par`, `bad_json` or `fetch_error`). In none of them did the single-object API serve a diameter or albedo
string different from the bulk table (`detail_value_mismatch` 0).

## Decisions (as pre-registered; no re-scoring)

| | Rule | Counts | Decision |
|---|---|---|---|
| S1 NEOWISE share | 10 nw >= 8 m, m >= 1000 | m = 1,500, nw = 1,497 (99.8 %); 14,970 >= 12,000 | **holds** |
| S2 same source | 20 same >= 19 m, m >= 1000 | same = 1,469 (97.9 %); 29,380 >= 28,500 | **holds** |
| S3 drift by source | lower-median difference >= 0.1 mag, each group >= 30 | NEOWISE 1,497 rows (median +0.2653 mag); others 3 rows | **underpowered** (no decision) |

S1 and S2 came out as expected. S3 was the uncertain one (we leaned "fails"); it cannot be decided from a random
sample, because non-NEOWISE diameters are too rare: 3 of 1,500, a share between about 0.04 % and 0.58 % (exact
Poisson 95 % interval), so at most roughly 800 of the 138,083 served rows. The pre-registered powering rule is what
stops a decision on 3 rows; we report that rather than any reading of the 3 values.

## Hand checks

- By text search on `sources.csv` (one row has quoted fields, the Asbolus reference below; the searches were
  written around it): 1,500 data rows; `fetched,neowise` 1,497; the 3 others are 279 Thule and 19732 (IRAS,
  `IRAS-A-FPA-3-RDR-IMPS-V6.0`) and 8405 Asbolus (other, "Earth, Moon, and Planets, v. 89, Issue 1, p. 117-134
  (2002)"). No AKARI reference appears.
- S2 re-counted per reference: diameter and albedo strings equal in 1,280 + 28 + 68 + 14 + 22 + 13 = 1,425 of the
  1,456 rows whose diameter comes from the NEOWISE main-belt bundle, in all 41 rows from the Trojan, Hilda and NEO
  bundles, and in all 3 non-NEOWISE rows: 1,469. The 31 others are listed below.
- dH recomputed by hand from the served strings (H_fit = 5 log10(1329 km / (D sqrt p))): 279 Thule (8.58, 126.59,
  0.0412) -> 8.5684, dH 0.0116 mag (116 e-4, within its tolerance of 165, not shifted); 8405 Asbolus (9.20, 66,
  0.13) -> 8.7350, dH 0.4650 mag. Both match the job's output.
- 1,450 of the 1,500 sampled rows are shifted beyond rounding (96.7 %), consistent with 96.4 % for the full table.

## What it means

The diameters and albedos SBDB serves are, in practice, the NEOWISE catalog: 99.8 % of a random sample, taken
from the cryogenic main-belt fits (Masiero et al. 2011: 1,292 rows), later main-belt papers (2012-2017: 164), the
Trojan and Hilda papers (30), and the NEO papers (11). So the drift measured in the triplet study (median +0.27
mag) is, for nearly every row, a property of the NEOWISE values as served next to today's H; this matches the
mechanism Myhrvold 2018 described for the NEOWISE tables. Whether other sources drift less cannot be learned by
random sampling.

## Descriptive only (not scored; patterns seen after the data)

- **31 rows (2.1 %) pair a diameter and an albedo from different NEOWISE papers** (e.g. 446 Aeternitas: diameter
  Masiero et al. 2014, albedo Masiero et al. 2012). These rows look different: dH is negative in 19 of 31 (61 %)
  against 157 of 1,466 (10.7 %) for NEOWISE rows whose two references agree, their median dH is -0.062 mag and
  their median |dH| is 0.256 mag. A diameter and an albedo taken from two separate fits need not satisfy the size
  relation with any single H, which would explain it, but this is seen in 31 rows only and not tested.
- H references: 765 rows have a JPL-style H reference ("E2026L10", "E2024-XR3"; year 2026: 150, 2025: 422, 2024:
  169, 2023: 15, 2022: 7, 2021: 1, 2018: 1) and 735 an MPC Orbit Supplement one ("MPO964292"). The descriptive
  `h_ref_year` counts 734 MPC rows as no year and, through a quirk in `ref_year`, reads one MPC reference
  (`MPO190119`, for 2010 YD) as the year 1901. That quirk touches only this descriptive count, never a decision; it
  will be fixed in the next version of the code.
- dH quantiles for NEOWISE rows (5/25/50/75/95 %): -0.171, +0.131, +0.265, +0.382, +0.649 mag.

## Limits

1,500 rows are a sample. A reference names where SBDB took a value from, not which H the albedo was computed with.
The class rule rests on reference wording; no AKARI wording was seen, but S3 pools all non-NEOWISE classes, so a
misclassification there cannot change any decision. The data are a 2026-10-19 snapshot; SBDB changes daily.

## Next

A targeted test of non-NEOWISE drift would need a way to find those rows without reading the references first;
the bulk query has no reference field, so this is left open. The mixed-reference pattern could be tested on a fresh
sample (it needs its own pre-registration first, with the 1,500 rows here excluded). No one will be contacted about
individual objects without Sheehan's approval.

## Files

- this note
- `results/2026-10-19-sbdb-source-0.1.0/`: `summary.json`, `decisions.json`, `descriptive.json`, `sources.csv`
  (1,500 rows: served values, dH, tolerance, class and the three reference strings).

MV2, Munim, Inc., mv2@munimtech.com
