# SBDB flag-consistency pre-registration (F1-F3): are SBDB's NEO flag, PHA flag and orbit class the functions of its own served elements that their definitions say?

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-10-19 by AI agents working in his name, before any of the
data below are downloaded; not checked by a person. Apache-2.0 code, CC BY 4.0 text. A third check of JPL's
Small-Body Database (SBDB) as served, after `findings/2026-10-19-sbdb-triplet-results.md` (diameter, albedo and H
disagree for 96.4 % of 138,083 rows) and the diameter-source follow-up `findings/2026-10-20-sbdb-source-prereg.md`.

## Question

SBDB serves, for every asteroid, a NEO flag, a PHA ("potentially hazardous asteroid") flag and an orbit-class code
next to the elements they are defined from. Published definitions:

- **NEO** (CNEOS, cneos.jpl.nasa.gov/about/neo_groups.html): perihelion q < 1.3 au.
- **PHA** (same page): Earth MOID <= 0.05 au and H <= 22.0.
- **Orbit classes** (SBDB filter documentation, ssd-api.jpl.nasa.gov/doc/sbdb_filter.html): IEO Q < 0.983;
  ATE a < 1.0, Q > 0.983; APO a > 1.0, q < 1.017; AMO 1.017 < q < 1.3; MCA 1.3 < q < 1.666, a < 3.2; IMB a < 2.0,
  q > 1.666; MBA 2.0 < a < 3.2, q > 1.666; OMB 3.2 < a < 4.6; TJN 4.6 < a < 5.5, e < 0.3; CEN 5.5 < a < 30.1;
  TNO a > 30.1; PAA e = 1; HYA e > 1; AST none of the others (all in au).

If SBDB recomputes each flag and code whenever an orbit or H changes, the served values should agree with these
rules except where rounding of the served numbers hides which side of a boundary an object is on. If a flag is
set once and not refreshed (for example after an H revision; the triplet result shows H values are revised), some
served flags will contradict the served elements. This matters beyond bookkeeping: the PHA flag is the training
label of a series of machine-learning papers built on SBDB exports (for example arXiv:2504.18605, on a 958,524-row
NASA dataset, the size of the widely used Kaggle "Asteroid Dataset" export of SBDB), and critics of that work
assume the label is a deterministic function of MOID and H.

## Prior art

Searches on 2026-10-19 (web, arXiv, GitHub, Kaggle) found the definitions above, the ML papers and their
label-leakage critiques, but no published audit that counts how often SBDB's served NEO/PHA flags or class codes
disagree with its own served elements. We do not know of one; if one exists, this is a 2026 repeat of it.

## What has been seen before this note

None of the fields `pha`, `moid`, `q`, `a`, `e` or `ad` has been read for any row. The earlier triplet run read
`class` and `neo` (not `q`) for the 3 probe rows and the 340 rows of its published `sample.csv` and `outliers.csv`.
Those 343 spkids are excluded here (the job loads the two CSVs from their published raw URLs and refuses to run
unless they hold 340 distinct spkids; the 3 probe rows are coded in `sbdb_flags.py`). No SBDB request of any kind
was made while writing this note.

## Data

The SBDB Query API, all asteroids (`sb-kind=a`), fields `spkid, pdes, class, neo, pha, H, moid, q, a, e, ad`,
sorted by spkid, pages of 20,000 with a 1 s pause, every row processed (a census, no sampling).

## Reading the served numbers (`sbdb_flags.py` 0.1.0, unit-tested)

`q`, `moid`, `a`, `e` and `ad` are read as the interval of their last served digit (`decimal.Decimal`, never float):
a rule is decided only when the whole interval is on one side of its boundary, otherwise the row is "boundary"
for that check and not scored. `H` is read as exact, since the PHA definition is stated on the catalogued H.
Rows with a missing value or a flag other than Y/N are counted separately and not scored. For the class check,
a row is consistent if its served code is among the classes whose definitions its elements meet (definitions
can overlap, e.g. APO and OMB; we do not guess SBDB's precedence), or if it is AST and no definition is met.

## Decisions (integer arithmetic; `decide_f1`, `decide_f2`, `decide_f3`)

- **F1 (NEO flag).** n = rows with a decidable NEO rule and a Y/N flag; k = rows where they differ. Powered if
  n >= 100,000. **Holds** if 10,000 k <= n (at most 1 in 10,000).
- **F2 (PHA flag, among NEOs).** Over rows whose q is decidably < 1.3 au: n = rows with a decidable PHA rule and
  a Y/N flag; k = rows where they differ. Powered if n >= 10,000. **Holds** if 1,000 k <= n (at most 1 in 1,000).
- **F3 (orbit class).** n = rows whose class check is decidable; k = inconsistent rows. Powered if n >= 100,000.
  **Holds** if 10,000 k <= n.

Each decision is reported once as it comes out; no re-scoring. Everything else is descriptive: counts by
status, the flag-versus-rule confusion counts, the reason for each PHA mismatch (H > 22, MOID > 0.05, both, or
both conditions met while the flag says N), the served-class versus matched-class table, the number of decimals
served for H, MOID and q, and up to 5,000 mismatch rows per check (`mismatches.csv`; the counts are complete).

## Expected outcome, stated before the run

F1 holds and F3 holds: both depend only on the orbit, which SBDB refits and reclassifies as a unit. F2 is the
open one: MOID changes with every orbit fit, while H is revised on its own schedule. We lean "holds", with low
confidence. A "fails" would mean that some served PHA labels are stale, which ML users of SBDB exports should
know; a "holds" would confirm, with numbers, that the label is a deterministic function of the served MOID and H.

## Integrity checks written to `summary.json`

Gate note fetched and carries the gate text; 340 seen rows loaded; fields as requested; API count stable on
every page; rows read = count; spkids strictly increasing (no duplicates); all 343 excluded spkids found. If the
gate or the seen files fail, nothing is downloaded.

## Limits

This checks internal consistency of the served values only: it says nothing about whether an orbit, MOID or H is
right. Rounded served values hide boundary cases, which are counted, not scored. The class definitions come from
SBDB's own documentation and may simplify the rules used internally; disagreements are listed for reading, not
claimed as errors. No one will be contacted about individual objects without Sheehan's approval.

## Job and files

`sbdb-flags-v1`: fetches `fetch_published.py` 0.2.0 from this repo, waits for `sbdb_flags.py` and its tests to
be published and runs the tests, then fetches this note (text "SBDB flag-consistency pre-registration") and the
two seen-row files, then runs `sbdb_flags.py --gate-note ... --seen ...`. Outputs `summary.json`,
`decisions.json`, `counts.json` and `mismatches.csv`, published under `results/<date>-sbdb-flags-0.1.0/` with a
results note, whatever they say. Files in this commit: `sbdb_flags.py`, `test_sbdb_flags.py` (0.1.0) and this note.

MV2, Munim, Inc., mv2@munimtech.com
