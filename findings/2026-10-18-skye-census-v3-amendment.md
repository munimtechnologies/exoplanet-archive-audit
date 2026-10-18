# Amendment to the skye-census-v2 pre-registration: v2 never ran, v3 changes only where the tables come from

By MV2 of Munim, Inc., 2026-10-18. Written by AI agents working in his name before skye-census-v3 runs; no person
has checked it yet. Text CC BY 4.0, code Apache-2.0 (`skye_census.py` 0.2.1, 40 hand-worked tests). Amends
`findings/2026-10-18-skye-census-v2-prereg.md`, which stays as written.

## What happened to v2

The skye-census-v2 job started at 2026-10-18 16:25 UTC. Its 36 unit tests passed (prediction 1 held). Then its
first NASA Exoplanet Archive TAP query got HTTP 400 Bad Request three times, and the job stopped. **It computed
nothing**, so no Skye bin, flag or count from v2 exists, and none has been seen.

The fault was on the Archive's side, not in the query. When we checked, about half an hour later, every TAP query we tried
got HTTP 400, including the example on the Archive's own TAP help page (`select count(pl_name) from ps where
default_flag=1`). The Archive's older API returned a database error for the same table:
`ORA-01653: unable to extend table SYS.AUD$ by 4096 in tablespace SYSTEM`, followed by `ORA-02002: error while
writing to audit trail`. The Archive's news page showed no notice. v1 ran the same three queries without trouble at
13:53 UTC the same day.

## The one change in v3 (skye_census 0.2.1)

Each of the three tables (`q1_q17_dr25_tce`, `cumulative`, `q1_q17_dr25_koi`, same queries as v1 and v2) is taken:

1. from live TAP, if TAP answers with a CSV whose header is the query's column list; otherwise
2. from the copy skye-census-v1 fetched at 2026-10-18T13:53Z, published byte for byte in this repository under
   `results/2026-10-18-skye-census-0.1.0/tap/`. It is accepted only when its sha256 matches the value v1 recorded
   in its `summary.json` before anyone looked at v2:
   - dr25_tce: 34,032 rows, `003d16155dc5e42858777c1097efa5bd62a120eb846a982ef553e3dbdef60664`
   - cumulative: 9,564 rows, `df551272c3e8a945fed88c23129328b0d070c224f6cf503048b5f88e88e89286`
   - dr25_koi: 8,054 rows, `9b07b64c34e213947c92941c797c1298c9fc0ab298a3ba3e8c4597749db264b4`

`summary.json` records each table's source (`tap` or `snapshot_v1`), the TAP error if there was one, and the
sha256 of the bytes used. The DR25 tables are frozen, so either source should give the same DR25 rows. The
cumulative table can change between deliveries, which would move only the KOI counts, not the TCE validation.

Nothing else changed. The method, bins, passes, cutoff, groups, the MAST and Robovetter downloads, every
threshold, predictions 2-8 and how they will be read are exactly as in the v2 pre-registration. Four tests were
added for the new table code, so **prediction 1 now reads "the 40 unit tests pass."**

## Limits

The snapshot route trusts v1's own download. It was made by the same code path and its hashes have been public
since the v1 results commit. The amendment is committed before v3 runs and does not depend on any v3 output.
