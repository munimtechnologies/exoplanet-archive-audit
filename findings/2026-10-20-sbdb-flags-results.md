# SBDB flag-consistency results (F1 holds, F2 fails, F3 holds): 50 of 42,619 served PHA flags contradict the served MOID and H, all within 0.6 mag of the H = 22.0 line

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-10-20 ~05:40 UTC by AI agents working in his name; scored
strictly against `findings/2026-10-19-sbdb-flags-prereg.md` and re-counted by hand, but not checked by a person.
CC BY 4.0 text; code (`sbdb_flags.py` 0.1.0) Apache-2.0. Outputs: `results/2026-10-20-sbdb-flags-0.1.0/`.
Third note of the SBDB served-catalog series, after `findings/2026-10-19-sbdb-triplet-results.md` and
`findings/2026-10-19-sbdb-source-results.md`.

## Run

Job `sbdb-flags-v1` (python:3.12, 1 CPU, host blade): 18 unit tests passed; `fetch_published.py` fetched the
pre-registration (text "SBDB flag-consistency pre-registration") and the two seen-row files from their public raw
URLs before anything was downloaded; `sbdb_flags.py` then read every asteroid in the SBDB Query API (`sb-kind=a`,
79 pages of up to 20,000 rows, 2026-10-20 04:09 to 04:27 UTC). Integrity checks, all true: gate passed; 340 seen
rows loaded; fields as requested; API count stable on every page (1,575,465); rows read = count; spkids strictly
increasing; all 343 excluded spkids found. Rows scored: 1,575,122 (= 1,575,465 - 343).

## Decisions (as pre-registered; no re-scoring)

| | Rule | Counts | Decision |
|---|---|---|---|
| F1 NEO flag vs q < 1.3 au | 10,000 k <= n, n >= 100,000 | n = 1,575,084, k = 0 | **holds** |
| F2 PHA flag vs (MOID <= 0.05 au and H <= 22.0), among q < 1.3 au | 1,000 k <= n, n >= 10,000 | n = 42,619, k = 50; 50,000 > 42,619 | **fails** |
| F3 orbit class vs elements | 10,000 k <= n, n >= 100,000 | n = 1,572,241, k = 0 | **holds** |

F1 and F3 came out as expected: not one served NEO flag or orbit-class code disagrees with the served elements
in 1.57 million rows. F2 was the open one; we leaned "holds" with low confidence, and it fails: 50 of 42,619
decidable near-Earth rows (0.117 %, 1.17 per 1,000) carry a PHA flag that contradicts the served MOID and H. The
pre-registered threshold was 1 per 1,000. The exact 95 % Poisson interval for 50 events (37.1 to 65.9) puts the
rate between 0.087 % and 0.155 %, so the rate is not far from the line and a later snapshot could fall on either
side of it; the count rule as written fails, and that is what we report.

## Hand checks

- Decisions recomputed from `counts.json`: F1 n = `neo agree` 1,575,084 + `neo mismatch` 0; F2 n = `pha_neo
  agree` 42,569 + `pha_neo mismatch` 50 = 42,619; F3 n = `class consistent` 1,572,241 + `class inconsistent` 0.
- Row totals close: NEO 1,575,084 agree + 33 boundary + 5 flag_other = 1,575,122; PHA (all rows) 1,519,788 agree +
  12 boundary + 54,772 flag_other + 50 mismatch + 500 missing = 1,575,122; class 1,572,241 consistent + 2,881
  boundary = 1,575,122.
- `mismatches.csv` by text search: 50 data rows, all `check = pha`; 33 end in `H>22` and 17 in `both_met`; no row
  carries `moid>0.05`. `pha_reason H>22` 33 and `pha_reason both_met` 17 in `counts.json` agree.
- Confusion counts: flag Y / rule Y 2,510; flag Y / rule N 33; flag N / rule Y 17; flag N / rule N 1,517,278.

## What the 50 disagreements look like (descriptive, not scored)

Every one of the 50 rows has a served MOID of 0.049 au or less; the MOID condition is never the issue. All sit
close to the H = 22.0 cut:

- **33 rows are flagged PHA = Y with H > 22.0.** Served H runs from 22.01 to 22.57 (19 rows at 22.01-22.10, 14 at
  22.11-22.57; the largest is 2000 WC1 at 22.57). Among the 2,543 decidable rows served as PHA = Y, these are 1.3 %.
- **17 rows are flagged PHA = N although MOID <= 0.05 au and H <= 22.0.** In 10 of them the served H is exactly
  22.00; the other 7 have H from 21.70 (2019 KD7) to 21.99.

Two readings fit these numbers, and the data here cannot separate them. (a) Stale flags: if a PHA flag is set
when an orbit or H is first filed and not refreshed when H is later revised, objects whose H moved across 22.0
keep the old flag; the triplet and source notes showed H is revised often. (b) A boundary convention: if SBDB
applies the cut to an internal H with more digits than the served two decimals, or applies H < 22.0 rather than
H <= 22.0, the 10 rows served at exactly 22.00 would be consistent. Reading (b) explains at most those 10 rows;
had they been treated as boundary cases, k would have been 40 and 40,000 <= 42,619 would have held. So the
pre-registered decision rests on the equality case, and the 33 flagged-Y rows above 22.0 (and the 7 flagged-N
rows below) stand either way. CNEOS's wording is "an absolute magnitude (H) of 22.0 or less", which is what was
pre-registered.

Other patterns seen after the data (descriptive):

- 54,772 rows serve no MOID, and in every one of them the PHA flag is neither Y nor N (served empty); SBDB appears
  to leave the flag unset rather than N when the MOID is unknown.
- The class check could not be decided for 2,881 rows (an element sits on a class boundary within its rounding)
  and found no inconsistent row. Overlapping definitions occur: 138 AMO and 71 APO rows also meet the OMB
  definition (a between 3.2 and 4.6 au), 11 AMO and 5 APO rows meet CEN, 5 AMO rows meet TNO (a > 30.1 au); SBDB
  serves the near-Earth code in all of them. 161 AST rows meet no definition, as the rule expects.
- Served precision: H has two decimals in every row that has one (509 rows have no H); q has three decimals in
  every row; MOID is served with 0 to 9 decimals (1,028,901 rows with 2, 343,916 with 3, 106,792 with 1).

## What it means

For users of SBDB exports who treat the PHA flag as a deterministic label of (MOID, H), the label is right for
99.88 % of near-Earth asteroids and wrong, by the published definition, for about one in 850, always within 0.6 mag
of the H cut. Anyone recomputing PHA status from served MOID and H will disagree with the served flag on these
rows; machine-learning work that learns the flag from MOID and H (see the pre-registration) has a label noise of
this size built in. The NEO flag and the orbit class, by contrast, are exact functions of the served elements at
the one-in-a-million level.

## Limits

One snapshot (2026-10-20); SBDB changes daily, and the 50 rows may already differ. Internal consistency only:
nothing here says whether any MOID or H is right. H was read as exact at the served two decimals, as
pre-registered; if SBDB holds more digits internally, up to 10 of the 50 rows may be consistent on its side. The
class definitions come from SBDB's filter documentation and may simplify the rules JPL uses. No one will be
contacted about individual objects without Sheehan's approval; a short held note to JPL's SSD group listing the 50
designations is drafted for his review.

## Files

- this note
- `results/2026-10-20-sbdb-flags-0.1.0/`: `summary.json` (page byte counts and SHA-256 hashes, checks,
  decisions), `decisions.json`, `counts.json`, `mismatches.csv` (the 50 rows with their served values, expected
  flag and reason).

MV2, Munim, Inc., mv2@munimtech.com
