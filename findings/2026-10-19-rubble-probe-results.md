# Probe: can DR25's Rubble metric be re-derived from public Kepler files? (exploratory, no hypothesis)

MV2 of Munim, Inc., 2026-10-19. Written by AI agents working in his name; no person has checked it yet. Text CC BY
4.0, code Apache-2.0. Code: `probe_rubble.py` 0.1.0 and `test_probe_rubble.py` (17 tests, all passed in the job).
Outputs: `results/2026-10-19-rubble-probe-0.1.0/`. Job rubble-probe-v1 ran 2026-10-19 08:22-08:29 UTC.

This was a probe, not a test. Nothing was predicted beforehand, so nothing here is "confirmed". It settles format
questions before a pre-registered test, and it found one thing worth recording: on public DV time series, the
literal Rubble rule from the DR25 paper is stricter than what DR25 actually did.

## Background

Rubble (Thompson et al. 2018, ApJS 235, 38, Appendix A.3.7.1) is one of DR25's individual-transit checks: "the
number of Kepler cadences that are available in the DV time series" over "the number of cadences expected" across
"two transit durations", and an event below "0.75" "is not counted as a valid transit". The public Robovetter input
(github.com/nasa/kepler-robovetter, OBS, 32,534 TCEs, sha256 3d6689de...) gives per TCE `ntrans`, `nrealt`
("real" events: non-zero SES, or SES = 0 with more than 75% real in-transit data), `ngoodt` and `iflag0` (1 if at
least one event failed Rubble). We found no public code that derives Rubble or `nrealt` from light curves and
checks them per TCE against these columns (GitHub and arXiv searches, 2026-10-18/19).

## 1. What the OBS input says (all 32,534 TCEs)

- `iflag0` = 1 for 13,939 TCEs (42.8%): 4,263 of 16,612 with pn = 1 (25.7%), 9,676 of 15,922 with pn > 1 (60.8%).
  By period: P < 10 d 7,396 / 13,874; 10-45 d 2,128 / 4,708; 45-200 d 2,591 / 4,263; P > 200 d 1,824 / 9,689.
- 24,766 TCEs have `ntrans` > `nrealt`; 13,177 of them carry `iflag0`. Only 762 `iflag0` TCEs have
  `ntrans` = `nrealt`.
- `ngoodt` < `nrealt` for 30,535 TCEs, never without at least one individual-transit flag, and `ngoodt` > `nrealt`
  never occurs. So `nrealt` - `ngoodt` counts events removed by the six per-event metrics.
- 3,092 TCEs have Rubble as their only per-event flag. For them, `nrealt` - `ngoodt` is the number of events Rubble
  removed: 1 (391 TCEs), 2 (338), 3 (901), 4 (800), 5 (319), 6 (154), 7 (80), 8-27 (109).
- TRANS_GAPPED rule (`nrealt`/`ntrans` <= 0.5): 5,551 TCEs. Fewer than 3 good events: 13,354. Recomputed MES < 7.1:
  12,652. Either: 14,567.

## 2. The public DV time-series files

- The DR25 DVT file name stamp is **20160128150956** (found in the MAST directory listing for all three stars that
  have one), not 20160209194854 as we had assumed.
- KIC 6359929 (KOI-5269) and KIC 6034834 (KOI-5227) have no DR25 OBS TCE and no DV directory (404).
- Each file has one `TCE_n` extension per TCE plus a `Statistics` extension, all on the full Q1-Q17 long-cadence
  grid (71,427 rows). In a TCE extension, the number of finite `LC_INIT` cadences falls with TCE number
  (KIC 11442793: 51,409 for TCE 1 down to 44,501 for TCE 7), which fits earlier TCEs' transits having been removed.
  The finite `MODEL_WHITE` count is the same in every extension of a star (54,376) and larger than any `LC_INIT`
  count. That *might* mean the whitened series includes gap-filled cadences, which would matter for Rubble. This is
  a guess, and it has not been tested.

## 3. Per-event results for three stars (9 TCEs)

Events are t0 + nP inside the DVT time span; coverage is finite `LC_INIT` cadences within the window over those
expected at 29.4244 min. "Real" means at least one cadence within half a duration of mid-transit. "Literal fails"
are real events whose two-duration coverage is below 0.75. Counts were taken by hand from `events.csv`.

| TCE | ntrans | nrealt | real (ours) | iflag0 | literal fails |
|---|---|---|---|---|---|
| 11446443-01 | 492 | 433 | 432 | 0 | 3 |
| 11442793-01 | 3 | 3 | 3 | 0 | 0 |
| 11442793-02 | 6 | 6 | 6 | 0 | 0 |
| 11442793-03 | 19 | 16 | 16 | 0 | 0 |
| 11442793-04 | 13 | 12 | 12 | 0 | 0 |
| 11442793-05 | 8 | 7 | 7 | 0 | 2 |
| 11442793-06 | 174 | 155 | 154 | 1 | 5 |
| 11442793-07 | 140 | 106 | 110 | 1 | 12 |
| 6922244-01 | 415 | 384 | 384 | 0 | 4 |

- **`nrealt` is reproduced** exactly for 6 of 9 TCEs and within one event for 2 more. The one miss of 4 events is the
  seventh TCE of a seven-TCE star.
- **The literal Rubble rule over-flags.** Against `iflag0` it gives 2 true flags, 3 false flags, 0 misses and 4
  correct passes. DR25 kept the 9 events behind the false flags: their two-duration coverage was 0.33-0.68 (in-transit
  coverage 0.17-0.82). For example, KIC 11442793 TCE 5 has two real events covered at 0.44 and 0.33, but DR25 lists
  `nrealt` = `ngoodt` = 7 and no Rubble flag.
- So on finite `LC_INIT` cadences, no threshold above about 0.33 can match DR25 on these TCEs. Either DR25 counted
  other cadences as "available" (for example gap-filled ones), or it used a different window. The paper does not
  say which.
- For pn > 1, the long-cadence light curves (no earlier transits removed) give different counts from the DV series
  (TCE 7: 117 vs 98 events at or above 0.75). TCEs with pn > 1 have to be scored on the DV series and reported
  separately.

## 4. Self-check note

The probe's self-check printed `ok = False` (129,595 vs 128,918). That was a bug in the check, not in the data. The
probe summed each star's valid cadences (64,798 + 64,797). The reference 128,918 from skye_apply 0.1.0 is the
number of *distinct* rounded times across both stars, and 677 timestamps coincide after rounding to 1e-5 d. The
per-file counts agree file by file with skye-apply-v1 (for example Q13: 4,244 and 4,243).

## Next

An exploratory development scan (scan_rubble 0.1.0, job rubble-scan-v1) uses 60 seeded OBS stars that were never
looked up and tabulates four cadence sources x two windows x three thresholds against `nrealt`, `iflag0` and the
Rubble-only `nrealt` - `ngoodt`. It lists a disjoint reserve of 200 stars that it never downloads. One variant will
then be fixed in writing and pre-registered before the reserve is scored. The five probe stars (and KICs 9018021,
7363829 and 3534076 from earlier work) are excluded from both sets.

Limits: three stars and nine TCEs, all looked up, so they serve as regression controls only. No claim about any
planet candidate follows from this. Made with AI agents.
