# SBDB mixed-reference results (M1, M2 both hold): 98 of 3,979 sampled NEOWISE-diameter rows (2.5 %) pair a diameter and an albedo from two different NEOWISE papers, and 52 % of those have dH < 0, against 12 % of single-reference rows

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-10-20 ~08:00 UTC by AI agents working in his name; scored
strictly against `findings/2026-10-20-sbdb-mixed-prereg.md` and re-counted by text search, but not checked by a
person. CC BY 4.0 text and data; code (`sbdb_mixed.py` 0.1.0) Apache-2.0. Outputs:
`results/2026-10-20-sbdb-mixed-0.1.0/`. Lane C3 of the SBDB served-catalog series (follows C1 and C2).

## Run

Job `sbdb-mixed-v1` (python:3.12, 1 CPU, host blade), 2026-10-20 05:12 to 06:41 UTC: 9 unit tests passed;
`fetch_published.py` fetched `sbdb_mixed.py` 0.1.0, its tests, the pre-registration (text "SBDB mixed-reference
pre-registration") and the three seen-row files before anything was downloaded. `sbdb_mixed.py` then read the
bulk table (SBDB Query API, 7 pages, count 138,086; 3 probe rows excluded, 138,083 ok), dropped the 1,840 seen
rows (pool 136,240), drew 4,000 rows with `random.Random(2026102000)` and requested each from the single-object
SBDB API with `phys-par=1`. Integrity checks, all true: gate passed; 1,840 seen rows loaded; count stable on every
page; rows = count; no duplicate spkid; all 4,000 single-object requests returned (status "fetched").

## Decisions (as pre-registered; no re-scoring)

| | Rule | Counts | Decision |
|---|---|---|---|
| M1 mixed share | n >= 3,000; n <= 100 k <= 5 n | n = 3,979 NEOWISE-diameter rows, k = 98 mixed (2.46 %) | **holds** |
| M2 sign difference | each group >= 50; 4 (neg_m n_s - neg_s n_m) >= n_m n_s | mixed 51 / 98 (52.0 %), same 468 / 3,881 (12.1 %); difference 0.400 | **holds** |

Both came out as expected. Hand arithmetic for M1: 100 x 98 = 9,800 lies between 3,979 and 5 x 3,979 = 19,895.
For M2: 51 x 3,881 = 197,931; 468 x 98 = 45,864; 4 x (197,931 - 45,864) = 608,268 >= 98 x 3,881 = 380,338.

The pilot (31 mixed rows in the 1,500-row C2 sample, seen before this note's pre-registration) gave 2.1 % and a
difference of about 0.50; the fresh sample gives 2.5 % and 0.40.

## Hand checks (text search over the job's `mixed.csv`, 4,000 rows)

- Rows whose `group` is `mixed`: 98; `same`: 3,881; the remaining 21 are `other` (diameter not NEOWISE), so
  every NEOWISE-diameter row is either same or mixed. Matches `descriptive.json`.
- Mixed rows with a negative `dh_e4`: 51; same rows with a negative `dh_e4`: 468. Matches `decisions.json`.
- `mixed_rows.csv` in the results folder holds the 98 mixed rows with 11 of the 19 columns (the long reference
  strings are reduced to their bibcodes). It was copied out of the job's file by the agents and re-checked by text
  search: 98 rows, 51 with dH < 0, 29 with |dH| > 0.5 mag, 22 with the pair 2011ApJ...741...68M ->
  2012ApJ...759L...8M, all equal to the job's own counts. The full 4,000-row table (about 1.4 MB, mostly
  repeated reference strings) is over the size this repository takes per file; it is reproducible from the
  seed and the published code.

## Descriptive, not scored

- **Mixed rows spread both ways, single-reference rows drift one way.** dH quantiles (mag), 5/25/50/75/95 %:
  mixed -0.957 / -0.405 / -0.011 / +0.234 / +0.718; same -0.148 / +0.136 / +0.270 / +0.381 / +0.634. |dH| > 0.5 mag
  in 29 of 98 mixed rows (29.6 %) against 444 of 3,881 same rows (11.4 %). A diameter and an albedo from two
  different thermal fits carry the gap between the fits on top of the H revision, which fits the wider and
  centred mixed distribution; this was not tested.
- **Rough uncertainty (normal approximation, not pre-registered):** mixed share 2.46 % +- 0.48 % (95 %);
  sign difference 0.40 +- 0.10 (95 %).
- **Which papers are paired.** 23 distinct diameter -> albedo pairs among the 98 rows (`descriptive.json`). The
  albedo comes from 2012ApJ...759L...8M (Masiero et al. 2012, NEOWISE cryogenic/post-cryogenic main belt) in 50
  of the 98. Pairs are not symmetric: 2011ApJ...741...68M -> 2012ApJ...759L...8M 22 times, the reverse 6;
  2014ApJ...791..121M -> 2012ApJ...759L...8M 15 times, the reverse 3. Two mixed rows are NEO-bundle rows
  (spkids 20356394 and 20464798); the rest are main-belt.
- **Served values agree across the two APIs.** For all 4,000 rows the single-object API served the same diameter
  and albedo as the bulk table (`detail_value_mismatch` = 0).
- **H references.** 1,865 of the 4,000 served H values cite an MPC circular reference (MPO..., no year parsed);
  the other 2,135 cite references carrying a year (such as E2025-UI6), dated 2015-2026, 1,572 of them from 2025 or 2026 (`h_ref_year`). So at
  least 39 % of the served H values were set in 2025-2026, while the NEOWISE fits date from 2011-2017.

## What it means

About one in forty asteroids that SBDB serves with a NEOWISE diameter takes its albedo from a different NEOWISE
paper. For those rows the served triplet cannot be read as one fit: half of them sit on the bright side of the
size relation (dH < 0), where the stale-H drift that dominates the database (C1) would put almost none. A user
who needs a consistent D, p and H should check that the diameter and albedo references match before using
both, and for the 2.5 % that do not, take both from one NEOWISE paper (the PDS bundle lists every fit).

## Limits

One snapshot, one random sample of 4,000 from 136,240 unseen rows. A reference string names where SBDB took a
value from, not which fit or H produced it; the sign test says nothing about which of the two values is better.
The 21 non-NEOWISE rows are too few to say anything about other sources. No one is being contacted about single
objects.

## Files

- this note
- `results/2026-10-20-sbdb-mixed-0.1.0/`: `summary.json` (pages, checks, pool, sample, decisions),
  `decisions.json`, `descriptive.json` (groups, pairs, dH quantiles in units of 1e-4 mag, |dH| > 0.5 mag counts,
  H reference years, value mismatches), `mixed_rows.csv` (the 98 mixed rows).

MV2, Munim, Inc., mv2@munimtech.com
