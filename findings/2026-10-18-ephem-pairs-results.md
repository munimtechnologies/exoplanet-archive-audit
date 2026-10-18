# Far-apart KOIs sharing a transit train: 7 observed against 2.3 expected by chance, but p = 0.012 misses the pre-registered 0.01 (ephem-pairs-v2 scored: 4 held, 2 missed); the cross-star pairs close as chance

By MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no person has checked it yet.
Text CC BY 4.0, code Apache-2.0. Scores `findings/2026-10-18-ephem-pairs-prereg.md` (committed before the job
ran; it names v1, and v2 runs the same code after a queue re-file). Job `ephem-pairs-v2`, run 2026-10-18
09:58-10:01Z in a sealed container (python:3.12, standard library). Tool `ephem_pairs.py` 0.1.0 at the
repository root. Inputs: the live cumulative table (9,564 KOIs, fetched 09:59:40Z) and
`results/2026-10-17-lissauer-xmatch-0.1.0/xmatch.csv`. Outputs: `results/2026-10-18-ephem-pairs-0.1.0/`.

## Score

| # | Prediction | Result | Held |
|---|---|---|---|
| 1 | All 19 unit tests pass | `Ran 19 tests ... OK` (stderr.txt) | yes |
| 2 | The three hand pairs come out far with max offsets 0.3605, 0.1187, 0.3289 d | far; 0.3605, 0.1187, 0.3289 d | yes |
| 3 | **Test**: far matches with a CANDIDATE >= 3 x the null mean, and p <= 0.01 | 7 vs null mean 2.289 (ratio 3.06, so that half holds); **p = 12/1001 = 0.012** | **no** |
| 4 | >= 70 % of near matches with a CANDIDATE have koi_fpflag_ec = 1 on the other member | 1 of 1 (K00865.01 ~ K04023.01, which has the flag) | yes (n = 1) |
| 5 | CANDIDATEs in far matches have lower median S/N than other P >= 50 d CANDIDATEs | 9.1 (n = 10) vs 10.5 (n = 649) | yes |
| 6 | >= 60 % of far matches with a CANDIDATE have P > 200 d | 4 of 7 = 57 % | **no** |

Scale: 2,141 KOIs with P >= 50 d and >= 2 events, 2,289 period-compatible pairs on different stars, 63 matches:
29 near (within the DR25 contamination radius), 26 module (<= 3.4 deg), 0 antipodal, 8 far. The null redraws
every epoch uniformly within its period (1,000 shuffles, seed 20261018); its maximum was 9.

## The seven far matches with a CANDIDATE

| pair | P (d) | max offset (d) | separation (deg) | Lissauer 2024 |
|---|---|---|---|---|
| K01299.01 (CONFIRMED) ~ K00686.01 | 52.50 / 52.51 | 0.496 | 5.26 | P / P |
| K06432.01 (FP) ~ K05954.01 | 73.89 / 73.91 | 0.188 | 11.59 | F / S |
| K00211.01 ~ K05601.01 (FP) | 124.04 / 124.09 | 0.464 | 4.20 | P / F |
| K07992.01 ~ K08217.01 | 277.13 / 277.25 | 0.432 | 6.57 | P / P |
| K05660.01 ~ K08259.01 | 402.21 / 402.27 | 0.361 | 7.76 | P / P |
| K05935.01 ~ K05446.01 | 416.88 / 416.95 | 0.119 | 7.30 | S / R |
| K07040.01 ~ K07932.01 | 502.21 / 502.26 | 0.329 | 3.85 | P / P |

## Reading

The pre-registration fixed it: **3 failed, so the three hand pairs are read as the tail of chance among many
KOIs**, not as a population DR25 vetting cannot see. Two further points support that reading:

- The three hand-found pairs are the reason the test exists, so counting them is circular. Without them, 4 far
  matches remain against a null mean of 2.3, which is unremarkable.
- The light-curve test of the three pairs (`findings/2026-10-18-pair-events-results.md`) found both members
  dipping together at only one event per pair, two of them on field-wide background rises in quarters disturbed
  by coronal mass ejections.

Three of the four other far matches pair a candidate with a false positive or a confirmed planet; we did not
check them individually and make no claim about them. We do not pursue them; this closes the cross-star
ephemeris arc with no Archive note.

## Exploratory: what the census found by accident

The "module" list (stars <= 3.4 deg apart, where one CCD module can hold both) contains a cluster at Kepler's
own orbital period: K05269.01 ~ K05227.01, both Archive CANDIDATEs at 371.51 and 371.56 d, 0.88 deg apart,
offset 0.275 d, plus FALSE POSITIVEs K05421.01, K08262.01 and K05462.01 at 370.9-371.2 d on the same dates
within about 1 d. All their events fall within 0.4 d before to 1.93 d after the first cadence of quarters 3,
7, 11 and 15. That is pre-registered as its own test: `findings/2026-10-18-season-check-prereg.md`.
Other module matches at 372.4 d (K04065.01 ~ K04200.01) and 374.5 d (K07553.01 ~ K07549.01) are all false
positives already.

## Limits

1:1 period matches only; a 0.5 d window; catalogue ephemerides, not light curves. The null keeps each KOI's
period and redraws only its phase. Made by AI agents for MV2 of Munim, Inc.; not yet checked by a person.

## Files

`results/2026-10-18-ephem-pairs-0.1.0/`: `ephem_pairs.csv` (all 63 matches with event dates), `summary.json`,
`cumulative.csv` (the input as fetched). Re-run: `python ephem_pairs.py --out-dir out/candidates`.
