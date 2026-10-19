# SBDB triplet results (P1-P3 all hold): most diameter/albedo/H triplets JPL's Small-Body Database serves no longer agree

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-10-19 ~17:40 UTC by AI agents working in his name; scored
strictly against `findings/2026-10-19-sbdb-triplet-prereg.md` and re-counted by hand, but not checked by a person.
CC BY 4.0 text; code (`sbdb_triplet.py` 0.1.0) Apache-2.0. Outputs: `results/2026-10-19-sbdb-triplet-0.1.0/`.

## Run

Job `sbdb-triplet-v1` (2026-10-19 16:21-16:23 UTC, python:3.12): 18 unit tests passed; `fetch_published.py`
fetched the pre-registration from its public raw URL (6,131 bytes, sha256 `282e4fb7...d386b`) before anything was
downloaded; `sbdb_triplet.py` then read 7 pages of the SBDB Query API (16:22:22-16:22:37 UTC, sha256 of each page in
`summary.json`). One correction to the pre-registration: it says it was written "~16:30 UTC"; the gate log shows it
was already public at 16:21 UTC, so that time was an over-estimate. What matters, that the note was public before
the data were read, is confirmed by the gate step.

Integrity checks, all true: fields as requested; API count stable on every page (138,086); rows = count; no
duplicate spkid; spkids strictly increasing. Status: 138,083 `ok`, 3 `excluded_probe` (the rows seen before
pre-registration), no `unparsed`, `nonpositive` or `too_coarse` rows.

## Decisions (as pre-registered; no re-scoring)

| | Rule | Counts | Decision |
|---|---|---|---|
| P1 prevalence | 2k >= n, n >= 1000 | n = 138,083, k = 133,163 shifted (96.4 %); 266,326 >= 138,083 | **holds** |
| P2 direction | 5 pos >= 3k, k >= 100 | pos = 116,925 of 133,163 (87.8 %); 584,625 >= 399,489 | **holds** |
| P3 size | lower-median dH(H >= 14) - dH(H < 10) >= 0.1 mag, both >= 100 | 0.2705 - 0.0781 = 0.1924 mag (n 118,573 and 763) | **holds** |

All three came out as expected before the run. P2, called the least certain, holds clearly.

## Hand checks

- Counts re-done by text search on the local `rows.csv` (not published, ~14 MB): rows with `shifted` = 1: 133,163;
  = 0: 4,920 (sum 138,083); shifted with dh_e4 > 0: 116,925. No row contains a quote character, so the
  comma-column search is exact. 75,088 + 41,300 + 2,185 = 118,573 = n(H >= 14) from the descriptive bins.
- H_fit recomputed by hand from the served strings for five `sample.csv` rows: 1544 Vinterhansenia (11.94, 24.561,
  0.058) -> 11.7578; 8605 (13.66, 5.637, 0.266) -> 13.3002; 13290 (12.16, 8.836, 0.272) -> 12.2999, dH -0.1399;
  833158 (16.12, 3.533, 0.025) -> 16.8821; 129774 (15.82, 2.102, 0.191) -> 15.8019, dH 0.0181 against a
  tolerance of 0.0184 (0.0005 km and 0.0005 in p move H_fit by 0.00052 and 0.00284; plus 0.005 for H; ceil + 0.01
  -> 184), so not shifted. All match the job's output to the last digit.

## What it means

Of the 138,083 asteroids for which SBDB serves a diameter, an albedo and an H, 96 % carry an albedo that does not
reproduce today's H within rounding, and in 88 % of those the served H is fainter than the albedo implies, so the
served albedo is too high for the H served next to it. The median shift is +0.27 mag overall, +0.08 mag for
H < 10 and +0.27 mag for H >= 14. Recomputing the albedo with today's H (`p_now` in the CSVs) lowers it by a
factor 10^(-0.4 dH), about 22 % at the median.

## Prior art, including one the pre-registration missed

The pre-registration cited Pravec et al. 2012, Masiero et al. 2017 and SsODNet (Berthier et al. 2023). It missed
**Myhrvold 2018, "An empirical examination of WISE/NEOWISE asteroid analysis and results", Icarus 314, 64-97
(doi:10.1016/j.icarus.2018.05.004)**. As summarised in sources we could read (the paper itself was not accessible
to us), it reports that the H values in the NEOWISE PDS tables are rounded to 0.1 mag, apparently MPC values from
before publication, and that updating them to 2017 MPC values changes p by 10 % or more for over half of the
NEOWISE results. The NEOWISE team's reply is Wright et al. 2018 (arXiv:1811.01454). So the mechanism, and its size
for the NEOWISE tables, were already known.

What this run adds: the measurement is of what JPL's SBDB *serves* in October 2026 (the source many tools and
people read), across every asteroid with all three values, with a per-row rounding-aware tolerance, and with the
direction and size dependence decided by pre-registered integer rules. It is a data-quality measurement, not a new
physical claim.

## Descriptive only (not scored; patterns seen after the data)

- Histogram (0.05-mag bins): one main mode at +0.30 to +0.35 mag (15,753 rows), close to the ~0.26-0.3 mag
  MPC -> Pan-STARRS offset reported by Vereš et al. 2015 and Masiero et al. 2017. 3,313 rows (2.4 %) have |dH| > 1 mag.
- NEOs drift much less: median dH +0.012 mag (n 1,202) against +0.270 mag for non-NEOs (n 136,881); Apollo +0.008,
  Amor +0.017, Aten +0.047, Jupiter Trojans +0.192, inner/main/outer belt +0.31/+0.27/+0.26 mag.
- In the 40-row random sample, 19 rows have H_fit within 0.002 mag of a multiple of 0.1 mag (about 1.6 expected if
  H_fit's last digits were uniform), consistent with the 0.1-mag rounded H Myhrvold reported for NEOWISE. Seen in
  40 rows only; not tested.
- Rows to look at, not proven errors: 4 rows serve albedo 0.001 (e.g. 2408 Astapovich, D 31.285 km), giving
  |dH| of 2.3-3.5 mag; 2 rows serve albedo 1.000 (4440 Tchantches, 4765 Wasserburg); for (2015 JF11), D 0.170 km
  with p 0.203 implies H 21.20 against a served 17.60, and its recomputed albedo would be 5.6, which is impossible,
  so either the diameter or H belongs to something else. The 300 largest |dH| rows are in `outliers.csv`.
- Rows without `diameter_sigma` (94) are the only group with a median near zero (-0.008 mag); these are likely
  non-thermal diameters (radar, occultation, spacecraft), but SBDB's bulk query does not say.

## Limits

SBDB's bulk query does not give the H each albedo was computed with, or each diameter's source, so dH mixes H
revisions with any albedo set by other means; a large |dH| is a flag, not proof of an error. The constant 1329 km
and the 0.01-mag slack follow the pre-registration. The data are a 2026-10-19 snapshot (page hashes in
`summary.json`); SBDB changes daily.

## Next

No one will be contacted about individual objects without Sheehan's approval. Any follow-up (the diameter-source
split from single-object `sbdb.api` references, or a test of the 0.1-mag grid on rows not yet seen) needs its own
pre-registration first.

## Files

- this note
- `results/2026-10-19-sbdb-triplet-0.1.0/`: `summary.json`, `decisions.json`, `descriptive.json`, `histogram.csv`,
  `outliers.csv` (300 rows), `sample.csv` (40 rows, seed 2026101916). `rows.csv` stays local (too large).

MV2, Munim, Inc., mv2@munimtech.com
