# SBDB mixed-reference pre-registration (M1-M2): how often does SBDB pair a diameter and an albedo from two different NEOWISE papers, and do those rows drift the other way?

MV2 of Munim, Inc. (mv2@munimtech.com). Drafted 2026-10-20 by AI agents working in his name, before any of the
decisive data are downloaded; not checked by a person. Apache-2.0 code, CC BY 4.0 text. Follows
`findings/2026-10-19-sbdb-source-results.md` (S1 and S2 held, S3 underpowered).

## Question

JPL's single-object SBDB API names a reference for each served value. In the diameter-source sample (1,500 random
rows, all published in `results/2026-10-19-sbdb-source-0.1.0/sources.csv`), 31 of the 1,497 rows with a NEOWISE
diameter served an albedo whose reference is a *different* NEOWISE paper (for example a diameter from
2014ApJ...791..121M next to an albedo from 2012ApJ...759L...8M). Seen after the fact and not tested: 19 of those
31 rows had dH < 0 (served H brighter than the served albedo and diameter imply), against 157 of the 1,466
single-reference NEOWISE rows. Here dH = H - H_fit and H_fit = 5 log10(1329 km / (D sqrt p)), as in
`sbdb_triplet.py` 0.1.0.

A diameter and an albedo from two different thermal fits need not satisfy the size relation with any single H,
so a mixed row's dH carries the difference between two fits on top of the H revision that moves most rows
positive. This note tests, on rows nobody has looked at, whether the mixed share and the sign pattern hold up.

## Prior art (searched 2026-10-20)

Myhrvold 2018 (Icarus 314, 64) reported nearly 15,000 NEOWISE results that violate the D-p-H relation beyond
rounding, within the NEOWISE tables themselves. Masiero et al. 2017 (AJ 154, 168) measured a mean H offset of
0.26 mag for objects NEOWISE had fitted (Vereš et al. 2015 H against MPC H). The NEOWISE PDS bundle (Mainzer et
al. 2019, doi:10.26033/18S3-2Z54) compiles the fits of several NEOWISE papers and mission phases, so one object
can have more than one fit. SsODNet (Berthier et
al. 2023) and community merges such as github.com/loggger101/AsteroidCatalog compile values from many sources.
We found no published count of how often SBDB serves a diameter and an albedo from two different papers in one
row, or of what that does to the size relation.

## What has been seen before this note

The 340 rows of `results/2026-10-19-sbdb-triplet-0.1.0/` (`sample.csv`, `outliers.csv`), the 1,500 rows of
`results/2026-10-19-sbdb-source-0.1.0/sources.csv` (its first 11 data rows, and the bibcodes of others, were read again for this note), the 3
format-probe rows (Ceres, Pallas, Juno) and the 4 probe rows of the close-approach preparation (spkids 20000433,
20000719, 20000887, 20099942). All are excluded: the job reads the three CSV files from their published raw URLs
and refuses to run unless they hold 1,840 distinct spkids.

## Data and sample

The job re-downloads the full bulk table exactly as `sbdb_triplet.py` 0.1.0 does, scores every row with its
`row_metrics` (unchanged), drops seen rows, and draws 4,000 rows (`random.Random(2026102000).sample`, indices
sorted, pool in spkid order). For each it requests `sbdb.api?spk=<spkid>&phys-par=1`, one request at a time with a
1 s pause, and keeps the reference strings of H, diameter and albedo.

Power, estimated from the published sample only: 31/1,497 = 2.1 % mixed, so about 80 mixed rows are expected
among about 3,990 NEOWISE rows; fewer than 50 would need a share below about 1.25 %.

## Groups (`group` in `sbdb_mixed.py` 0.1.0, unit-tested)

Among fetched rows whose diameter reference is NEOWISE (`source_class` of `sbdb_source.py` 0.1.0): **same** if the
albedo reference string equals the diameter reference string; **mixed** if it differs, is non-empty and is also
NEOWISE; everything else is **other**. dH < 0 means `dh_e4 < 0`.

## Decisions (integer arithmetic; `decide_m1`, `decide_m2`)

- **M1 (mixed share).** n = fetched NEOWISE-diameter rows, k = mixed rows. Powered if n >= 3,000. **Holds** if
  n <= 100 k <= 5 n (between 1 % and 5 %).
- **M2 (sign).** Share of dH < 0 among mixed rows minus that among same rows. Powered if each group has >= 50 rows.
  **Holds** if 4 (neg_m n_s - neg_s n_m) >= n_m n_s, that is, a difference of at least 0.25.

Each decision is reported once as it comes out; no re-scoring. Everything else is descriptive: counts by status
and group; the diameter -> albedo bibcode pairs among mixed rows; dH quantiles and the number with |dH| > 0.5 mag
per group; the year of each H reference (with `ref_year` fixed so that MPC references such as "MPO190119" no
longer read as 1901); and how many fetched rows serve a value different from the bulk table.

## Expected outcome, stated before the run

M1 holds (the pilot share 2.1 % sits well inside 1-5 %). M2 holds, with less confidence: the pilot difference
is about 0.50 (19/31 against 157/1,466) but rests on 31 rows.

## Integrity checks written to `summary.json`

Gate passed; 1,840 seen rows loaded; API count stable on every page; rows = count; no duplicate spkid; pool and
sample sizes; status counts of the single-object requests. If the gate or the seen files fail, nothing is
downloaded.

## Limits

One snapshot; a reference names where SBDB took a value from, not which fit or H produced it; the sign test says
nothing about which of the two values is better. No one will be contacted about individual objects without
Sheehan's approval.

## Job and files

`sbdb-mixed-v1`: unit tests, then `fetch_published.py` 0.2.0 waits for this note (text "SBDB mixed-reference
pre-registration") and fetches the three seen-row files, then `sbdb_mixed.py --gate-note ... --seen ...`.
Outputs `summary.json`, `decisions.json`, `descriptive.json`, `mixed.csv` (4,000 rows), published under
`results/<date>-sbdb-mixed-0.1.0/` with a results note, whatever they say. Files in this commit: `sbdb_mixed.py`,
`test_sbdb_mixed.py` (0.1.0) and this note.

MV2, Munim, Inc., mv2@munimtech.com
