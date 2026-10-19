# SBDB diameter-source pre-registration (S1-S3): where do the diameters and albedos SBDB serves come from, and does the drift depend on the source?

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-10-19 by AI agents working in his name, before any of the
decisive data are downloaded (the filename carries the planned run date); not checked by a person. Apache-2.0 code,
CC BY 4.0 text. Follows `findings/2026-10-19-sbdb-triplet-results.md` (P1-P3 all held: 133,163 of 138,083 served
triplets disagree beyond rounding, median dH +0.27 mag).

## Question

The triplet check could not say where each diameter and albedo came from: SBDB's bulk Query API has no reference
field. The single-object SBDB API (`sbdb.api?spk=...&phys-par=1`) does: it names a reference for each of H,
diameter and albedo (for example a NEOWISE PDS bundle and Masiero et al. 2014 for 1544 Vinterhansenia, a row
already seen). This follow-up asks, on a random sample: what share of the served diameters are NEOWISE's, whether
the albedo always comes from the same source as the diameter, and whether the drift differs between NEOWISE and
other sources (AKARI, IRAS, radar, occultations, spacecraft).

## Prior art

Myhrvold 2018 (Icarus 314, 64) reported that NEOWISE's PDS tables carry H rounded to 0.1 mag and that updating H
changes p by >= 10 % for over half of the NEOWISE results; Wright et al. 2018 (arXiv:1811.01454) replied. Usui et al.
2011 (AKARI) and Tedesco et al. 2002 (IRAS SIMPS) also computed albedos from the H of their time. SsODNet
(Berthier et al. 2023) recomputes albedos from current H. We found no published split of SBDB's *served* drift by
diameter source.

## What has been seen before this note

From the triplet run: the 3 probe rows; the 40 rows of `sample.csv`; the 300 rows of `outliers.csv`; the counts
and descriptive quantiles published with it (by H bin, NEO flag, orbit class and whether diameter_sigma is served:
the 94 rows without diameter_sigma had median dH -0.008 mag, which hints that non-thermal diameters drift less).

Reference payloads read so far, all of rows already in the seen set (a pilot of the classifier, nothing else):
1544 Vinterhansenia, 289 Nenetta and 1459 Magnya (diameter and albedo both
`urn:nasa:pds:neowise_diameters_albedos::2.0[mainbelt] (...)`, class neowise); 4179 Toutatis and 7335 (1989 JA)
(diameter "Hazards due to Comets and Asteroids (1994), Ed. T. Gehrels", class other; albedo from the NEOWISE
`[neos]` bundle, so diameter and albedo references differ). H references look like "E2026L10" or "E2024-XR3"
(year read by `ref_year`). No reference of any other row has been read. All 343 seen spkids are excluded from the
sample: the job reads `sample.csv` and `outliers.csv` from their published raw URLs and refuses to run unless they
hold 340 distinct spkids (plus the 3 probe rows coded in `sbdb_triplet.py`).

## Data and sample

The job re-downloads the full bulk table exactly as `sbdb_triplet.py` 0.1.0 does, scores every row with its
`row_metrics` (unchanged), drops seen rows, and draws 1,500 rows (`random.Random(2026101917).sample`, indices
sorted, pool in spkid order). For each it requests `sbdb.api?spk=<spkid>&phys-par=1`, one request at a time with a
1 s pause, and keeps the reference strings of H, diameter and albedo.

## Classes (`source_class` in `sbdb_source.py` 0.1.0, unit-tested)

Lower-cased diameter reference containing "wise" -> neowise; else "akari" or "usui" -> akari; else "iras",
"simps" or "tedesco" -> iras; else other; empty -> none. A row counts as fetched only if the payload lists a
diameter entry. AKARI and IRAS reference wording has not been seen; a miss there moves rows between akari, iras
and other, which S3 pools anyway, so it cannot change a decision.

## Decisions (integer arithmetic; `decide_s1`, `decide_s2`, `decide_s3`)

- **S1 (NEOWISE share).** m = fetched rows, nw = neowise rows. Powered if m >= 1000. **Holds** if 10 nw >= 8 m.
- **S2 (albedo and diameter share a source).** same = fetched rows whose albedo reference string equals the
  diameter reference string. Powered if m >= 1000. **Holds** if 20 same >= 19 m.
- **S3 (drift by source).** Lower median of dh_e4 over neowise rows minus that over akari + iras + other rows.
  Powered if each group has >= 30 rows. **Holds** if the difference is >= 1000 (0.1 mag).

Each decision is reported once as it comes out; no re-scoring. Everything else is descriptive: counts by status,
class, exact diameter reference and the year in the H reference; dH quantiles by class; and how many fetched rows
serve a diameter or albedo string different from the bulk table.

## Expected outcome, stated before the run

S1 holds (NEOWISE measured far more asteroids than any other survey). S2 holds, though the two seen NEOs above
show that mixed sources exist; we expect them to be rare outside NEOs. S3 is uncertain: AKARI and IRAS albedos
were also computed with older H, which argues for "fails"; the near-zero median of the 94 rows without
diameter_sigma argues for "holds". We lean "fails" but either result says something: whether SBDB's staleness is
a NEOWISE property or a general one.

## Integrity checks written to `summary.json`

Gate passed; 340 seen rows loaded; API count stable on every page; rows = count; no duplicate spkid; pool and
sample sizes; status counts of the single-object requests (fetched, no_diameter, no_phys_par, bad_json,
fetch_error). If the gate or the seen files fail, nothing is downloaded.

## Limits

1,500 rows are a sample; the classes rest on reference strings whose wording we have seen for five objects only;
a reference names where SBDB took the value from, not which H was used. No one will be contacted about individual
objects without Sheehan's approval.

## Job and files

`sbdb-source-v1`: fetches `sbdb_triplet.py` and `fetch_published.py` 0.2.0 from this repo, waits for
`sbdb_source.py` and its tests to be published and runs the tests, then fetches this note (text "SBDB
diameter-source pre-registration") and the two seen-row files, then runs
`sbdb_source.py --gate-note ... --seen ...`. Outputs `summary.json`, `decisions.json`, `descriptive.json`,
`sources.csv` (1,500 rows), published under `results/<date>-sbdb-source-0.1.0/` with a results note, whatever they
say. Files in this commit: `sbdb_source.py`, `test_sbdb_source.py` (0.1.0) and this note.

MV2, Munim, Inc., mv2@munimtech.com
