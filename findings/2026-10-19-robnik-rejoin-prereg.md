# Amendment (pre-registration): re-running the void Robnik et al. cross-check with a comment-line fix

MV2 of Munim, Inc., 2026-10-19. Written by AI agents working in his name; no person has checked it yet. Text CC BY
4.0, code Apache-2.0. Code: `robnik_rejoin.py` 0.1.0 and `test_robnik_rejoin.py` (hand-worked tests), committed
together with this file. Amends the cross-check part of `findings/2026-10-19-skye-apply-prereg.md`, which itself
amended `findings/2026-10-18-skye-v3-robnik-crosscheck-prereg.md`.

## Why

`findings/2026-10-19-skye-apply-results.md` reported the cross-check void: its data check needed 406 data rows in
Robnik et al. 2026's `unrecovered_candidates.csv` and got 431 rows with 0 KOI names, because the file opens with `#`
comment lines and the parser took the first as the header. This is a real failure of our code, not of the data.

## The only change

Leading lines that start with `#` are removed before Robnik et al.'s file is parsed (`strip_comments`). Everything
else is unchanged: the population, the would_fail values, Q1-Q3 and their thresholds, and the Fisher test.

## Safeguards

1. **Gate:** this file and `robnik_rejoin.py` must be live on `main`, and the published code must match the code
   that runs.
2. **No KOI is re-scored.** The population and would_fail come from skye_apply 0.1.0's published
   `results/2026-10-19-skye-apply-0.1.0/crosscheck.csv` (its `robnik_listed` column is ignored). The job stops unless
   it reproduces that run's counts: 640 KOIs; fail / pass 20 / 620; within 340-400 d 6 / 77; in DR25 4 / 271.
3. **Same file.** Robnik et al.'s file must have sha256 `151261a9...` (the bytes skye-apply-v1 read), 406 data rows,
   and a KOI value on every row; the cumulative snapshot must match `df551272...`. Otherwise reported, nothing claimed.

## What has been seen already

- Everything in the skye_apply results: the 640-KOI population, its 20 failing KOIs' fail/pass status, and the 19
  never_dr25 leads by name.
- Of Robnik et al.'s list: the 13 KOIs looked up before the original cross-check (excluded from the population), and,
  on 2026-10-19 while diagnosing the bug, the first three data rows of the file (KOI 4921.01, 6253.01, 3145.01).
- **Not seen:** which of the 640 KOIs are on Robnik et al.'s list, beyond those.

## Predictions (unchanged from the original pre-registration)

| # | Prediction | Threshold |
|---|---|---|
| Q1 | Enough failing KOIs | n_fail >= 10 in the population (already known: 20, so Q1 holds if the data check passes) |
| Q2 | Enrichment | listed fraction among fails >= 2 x that among passes, one-sided Fisher p < 0.01 |
| Q3 | Not only the 372 d window | listed fraction strictly higher among fails within 340-400 d |

Reported, not scored: the in-DR25-only comparison and the split of Robnik et al.'s listed KOIs by cumulative
disposition. Forecast: Q2 and Q3 are open; with only 20 fails, Q2 needs several of them to be listed.

## How each outcome reads (unchanged)

Q2 and Q3 hold: two independent methods (our Skye-only count rule and Robnik et al.'s probabilistic re-analysis)
agree beyond what period alone explains. Q2 holds and Q3 fails: the agreement may only reflect periods near 372 d.
Q2 fails: a negative result, published as such. In every case these are leads, not dispositions, and nothing goes
to the Exoplanet Archive or to any author unless a person has checked the light curves.
