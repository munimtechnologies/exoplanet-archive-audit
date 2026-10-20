# SBDB close-approach results (G1, G2, G3 all hold): JPL's served close-approach table and orbit table cite the same orbit solution for all 12,684 joined approaches, and the impact-parameter bound holds for all 2,866 eligible objects

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-10-20 ~05:45 UTC by AI agents working in his name; scored
strictly against `findings/2026-10-19-sbdb-cad-prereg.md` and re-counted by hand, but not checked by a person.
CC BY 4.0 text and data; code (`sbdb_cad.py` 0.1.0) Apache-2.0. Outputs: `results/2026-10-20-sbdb-cad-0.1.0/`.
Lane G of the SBDB served-catalog series.

## Run

Job `sbdb-cad-v1` (python:3.12, 1 CPU, host dell): 19 unit tests passed; `fetch_published.py` fetched the
pre-registration (text "SBDB close-approach pre-registration") and the two seen-row files before anything was
downloaded; `sbdb_cad.py` then read the NEO asteroid orbit table (SBDB Query API, `sb-group=neo&sb-kind=a`,
`full-prec=true`, 3 pages, count 42,787) and one close-approach request (CAD API, 2024-01-01 to 2028-01-01,
`dist-max=0.2`, `nea=true`, 12,685 rows, 2.2 MB), 2026-10-20 04:55 UTC. Integrity checks, all true: gate passed;
SBDB fields as requested, count stable, rows = count, spkids strictly increasing, no duplicate designation, the 4
probe rows found; CAD fields as requested, rows = count, every approach inside the window; join matched at least
99 % (12,684 of 12,685 CAD rows; the one unmatched row is an excluded seen object).

## Decisions (as pre-registered; no re-scoring)

| | Rule | Counts | Decision |
|---|---|---|---|
| G1 same orbit solution | 100 k <= n, n >= 5,000 | n = 12,684 matched approaches, k = 0 differ | **holds** |
| G2 impact parameter b >= MOID - 0.001 au | 1,000 k <= n, n >= 1,000 | n = 2,866 eligible objects, k = 0 | **holds** |
| G3 dist_min <= dist <= dist_max | k = 0, n >= 5,000 | n = 12,685, k = 0 | **holds** |

All three came out as expected. The close-approach table and the orbit table cite the same JPL orbit solution
for every one of the 12,684 approaches that could be joined, so the two products are regenerated together, not
one behind the other. No object's unperturbed miss distance (the two-body impact parameter b = dist v_rel / v_inf)
falls below its served Earth MOID by more than the tolerance, and every nominal distance lies inside its own
3-sigma range.

## Hand checks

- `g2_rows.csv` by text search: 2,866 data rows (2,867 lines with the header), equal to `G2.n_eligible`.
- `flagged.csv` holds only the header: no G1, G2 or G3 row was listed, matching k = 0 for all three.
- G2 eligibility statuses in `counts.json` close: ok 2,866 + no approach after the epoch 7,107 + first approach
  more than a year after the epoch 586 + epoch outside the window 185 + missing value 1 = 10,745 joined objects.
- b - MOID bins over the 2,866 eligible objects: [-0.001, 0) 25; [0, 0.001) 390; [0.001, 0.01) 764; [0.01, 0.1)
  1,178; >= 0.1 509; sum 2,866. Time from epoch to the tested approach: 0-30 d 1,380; 30-90 d 359; 90-180 d 539;
  180-365.25 d 588; sum 2,866.

## Descriptive, not scored

- **Gravitational focusing is visible but small.** The naive comparison (nominal distance below the served MOID)
  is true for 40 of the 2,866 objects (1.4 %), all by less than 0.001 au; the impact parameter b is below the MOID
  for 25 of them, again all by less than 0.001 au. So 15 objects show the expected focusing signature (dist < MOID
  <= b), fewer than the "visible share" the pre-registration anticipated, because within one year of a current
  epoch the osculating MOID and the actual encounter geometry rarely differ by more than the rounding.
- Most eligible objects are tested close to their epoch: 1,380 within 30 days.
- 7,849 joined objects carry the standard served epoch JD 2461200.5 (2026-06-09); the others carry individual
  epochs spread from 2002 to October 2026, typically near the object's last observed approach (`epochs.json`).
- The 328 objects whose listed approach precedes their epoch (orbit served is the post-encounter one): nominal
  distance below MOID in 7, b below MOID in 4, all within 0.001 au.
- Served precision: CAD distances carry 13 to 18 decimals and speeds 10 to 15 (full double precision); the
  full-precision SBDB MOID carries 4 to 12 decimals, most often 7.

## What it means

Anyone joining JPL's close-approach table to its orbit table by designation can rely on the orbit solution being
the same in both, at least within a 2024-2028 window queried on one day. The impact-parameter bound, which is a
physical consistency check between a served MOID and a served encounter, found nothing to flag. The result is a
clean negative: unlike the diameter-albedo-H triplet (96.4 % shifted) and the PHA flag (1 in 850 stale), the two
orbit-derived products agree with each other.

## Limits

One window (2024-2028), one distance cut (0.2 au), one snapshot. The two-body impact parameter is an
approximation that loosens for slow, distant encounters, in both directions; the 0.001 au tolerance absorbs it.
The join is by designation string only. Objects with no approach after their epoch inside the window (7,107) are
untested by G2.

## Files

- this note
- `results/2026-10-20-sbdb-cad-0.1.0/`: `summary.json` (request byte counts and SHA-256 hashes, checks,
  decisions), `decisions.json`, `counts.json`, `epochs.json`, `flagged.csv` (header only), `g2_rows.csv`
  (the 2,866 eligible objects with jd, epoch, dt, dist, v_rel, v_inf, b, MOID, b - MOID, dist - MOID, status,
  condition code and data arc).

MV2, Munim, Inc., mv2@munimtech.com
