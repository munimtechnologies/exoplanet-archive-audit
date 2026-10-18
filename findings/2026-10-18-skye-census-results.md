# skye-census-v1 scored: the validation check missed (66 % against 70 %), so nothing is claimed; two causes found in DR25's own code, and v2 pre-registered

By MV2 of Munim, Inc., 2026-10-18. Written by AI agents working in his name; no person has checked it yet.
Text CC BY 4.0, code Apache-2.0. Pre-registration: `findings/2026-10-18-skye-census-prereg.md` (committed before
the job ran). Job outputs: `results/2026-10-18-skye-census-0.1.0/`. Tool: `skye_census.py` 0.1.0 (sha256
`e1a8419e24b28b07519ddfd53d90df98d084fbc471a7bd41cffbf35f98e3b92d`, in the job's summary.json).

## Scores (as fixed in advance)

The job (skye-census-v1, 2026-10-18 13:51-13:54 UTC) ran 23 unit tests (all OK) and the census, with 0 MAST errors.

| # | prediction | result | held? |
|---|---|---|---|
| 1 | 23 unit tests pass | 23 OK | **yes** |
| 2 | >= 99 % of TCE stars and KOI stars get a skygroup | 8,034 / 8,034 and 2,165 / 2,165 | **yes** |
| 3 | >= 70 % of dr25_skye KOIs have an event in a Skye bin | 39 / 59 = 66.1 % | **no** |
| 4 | <= 10 % of eligible DR25 candidates would fail | 13 / 668 = 1.95 % | **yes** |
| 5 | K05269.01 and K05227.01 both would fail | both: 2 of 3 events flagged (631.6 and 1003.1 d BKJD) | yes (not claimed) |
| 6 | never-DR25 candidates fail at >= 2 x max(PC rate, 0.02), p <= 0.01 | 24 / 415 = 5.8 % vs 4.0 %, p = 5e-6 | yes (not claimed) |

The reading rule fixed in advance says: **if 3 or 4 fails, the re-implementation is not faithful enough; 5 and 6
are reported but nothing is claimed.** Prediction 3 failed, so nothing is claimed about K05269.01, K05227.01 or
the 24 never-scored candidates in the job's report. They stay unconfirmed.

## Why it missed (found after scoring, by reading DR25's own code)

1. **The validation group was built wrong.** The pre-registration defined dr25_skye as DR25 KOIs with SKYE in
   their comment, "109 with DR25 P > 45 d" (that count came from a `like '%SKYE%'` query). The code tested for the
   exact substring `INDIV_TRANS_SKYE`. That misses every comment where SKYE follows another individual-transit
   flag, such as `INDIV_TRANS_MARSHALL_SKYE` or `INDIV_TRANS_RUBBLE_SKYE`. So prediction 3 was scored on 59 of the
   109 KOIs. The miss stands as scored; the corrected group is re-tested in v2.
2. **The bin origin was off by half a day.** Thompson et al. 2018 do not give the bin origin, so v1 used edges
   at 131.0 + k BKJD. The reference code, `Skye.py` in github.com/JeffLCoughlin/skye (linked from the paper),
   uses `np.arange(131.5, 1591 + 1, 1.0)`, which puts the edges at 131.5 + k and the centres on whole days. A
   half-day shift moves events near a bin edge into a different bin.
3. **The rate counted unobserved seasons.** `Skye.py` divides by the number of non-gap bins. A gap bin is one
   where the skygroup has no events with data. v1 counted every bin inside a quarter. That included the seasons
   when a skygroup sat on the failed module 3, so the rate came out low and the threshold low.
4. **What the DR25 comment means.** In `Kepler-RoboVetter-DR25.cpp` (github.com/nasa/kepler-robovetter),
   `INDIV_TRANS_..._SKYE` is written only when at least one transit failed Skye *and* the TCE then had fewer than
   3 good transits or a recomputed MES below 7.1. The per-TCE flag itself ("at least one individual transit
   failed Skye") is column 12 of the public Robovetter input table, for all 34,032 observed TCEs. That table is
   a much larger, independent ground truth. v1 did not use it.

## Exploratory, labelled as such (no claim)

- Under v1's bins, DR25's own Skye-commented KOIs would fail 37 % of the time (22 / 59) and DR25 candidates 2 %
  (13 / 668). The test separates the two groups even though it misses a third of DR25's flags.
- Among the never-scored candidates, K04426.01 (369.1 d, skygroup 58), K05423.01 (366.6 d, skygroup 58) and
  K05398.01 (551.2 d, skygroup 58) had every event flagged. Skygroup 58 is the one Thompson et al. show in their
  Fig. 20. These are leads only if v2 validates.

## What happens next

`skye_census.py` 0.2.0 follows `Skye.py`. It uses edges at 131.5 + k, per-skygroup non-gap bins, and five fixed
rejection passes. It matches SKYE anywhere among the INDIV_TRANS flags. It is validated TCE by TCE against
DR25's own Skye flags in the Robovetter input table, data no earlier run has looked at. Pre-registration:
`findings/2026-10-18-skye-census-v2-prereg.md`, committed before the job runs. Every change above comes from
the paper's reference code, the Robovetter source or the pre-registration text, not from tuning against v1's
per-KOI results.
