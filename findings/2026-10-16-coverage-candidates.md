# Update, 2026-10-16 (sixth): coverage census, candidate alias tests, and a correction

By MV2 of Munim, Inc. The code, queries, checks and this write-up were made with AI agents working in his name. No person has independently re-derived these numbers yet. Text CC BY 4.0; code Apache-2.0.

This note reports two runs that were pre-registered (predictions written down before the results came back), scores those predictions, and corrects one argument in `findings/2026-10-16-kepler-1301.md`.

- `kepler_coverage.py` 0.1.0 (results in `results/2026-10-16-kepler-coverage-0.1.0/`)
- `kepler_alias.py` 0.3.0 run on DR25 **candidates** (results in `results/2026-10-16-kepler-alias-0.3.0-candidates/`)

## 1. Correction: the "impossible transit count" is not independent evidence

The Kepler-1301 b note argued that DR25's `koi_num_transits` = 298 "belongs to the 4.541 d signal", because at 9.0823 d at most 161 transits fit in the mission, and it said Kepler-1301 b was the only confirmed planet with such a count. Both points need correcting.

- **It is not the only one.** The 0.3.0 census lists two more confirmed planets whose DR25 KOI count is larger than their KOI period allows: **Kepler-458 b** (KOI-179.02; 4 transits listed, at most 3 at 572.38 d) and **Kepler-167 e** (KOI-490.02; 3 listed, at most 2 at 1071.23 d).
- **Why it happens.** In all three cases the DR25 TCE was detected at half the KOI period (286.19 d, 535.62 d, 4.541 d), and the KOI row kept the TCE's transit count (which counts epochs *with data* at the TCE period). Kepler-167 e's 1071 d period (Kipping et al. 2016) and Kepler-458 b's 572 d period (Planet Hunters, Wang et al. 2015; two transits seen) are well established. Their mismatch only shows that DR25 vetting doubled the TCE period, as it should have.
- **What this changes for Kepler-1301 b.** The count shows only that the pipeline found the signal at 4.541 d and vetting chose 9.08 d. It cannot tell which is right. The evidence that remains is the light curve: dips at phase 0.5 of the 9.08 d ephemeris (`findings/2026-10-16-lightcurves.md`). Kepler-1301 b's status is unchanged: a candidate correction, with a 9.08 d eclipsing binary or a contaminating neighbour still possible. The pixel-level test (`kepler-pixels`) is queued.

So the transit-count census is a list of KOIs whose period vetting changed relative to the TCE, not a list of wrong periods.

Side note on naming: the Archive's planet tables call KOI-179.02 "KIC 9663113 b" (host "KIC 9663113"), while its sibling is "Kepler-458 c" and the KOI tables call KOI-179.02 "Kepler-458 b". The Archive's overview page resolves "Kepler 458 b" to that system, so this is an alias quirk, not a data error.

## 2. Coverage census (kepler_coverage 0.1.0)

For each KOI ephemeris (4,089 KOI rows plus 5 Archive ephemerides, CONFIRMED and CANDIDATE), the census asks whether Kepler's actual data can exclude an alias of the period. A **P/k** flag means none of the extra epochs at P/k has data. A **kP** flag means every epoch with data has the same epoch number mod k, so k×P fits equally well. A flag is a limit of the data, not a claim that the period is wrong.

- 10 rows flagged: 3 confirmed and 7 candidates.
- Confirmed: **Kepler-1536 b** (KOI-3975.01, 364.75 d: P/3 not excluded; the star has data only in alternate quarters) and **Kepler-1633 b** (KOI-5568.01, two rows: on the KOI's 62.13 d ephemeris every epoch with data is ≡ 1 mod 3; on the Archive's 186.40 d, P/2 and P/3 cannot be excluded). Kepler-1633 b was reported in `findings/2026-10-16-kepler-1632-1633.md`. Kepler-1536 b is new here, but it is a coverage caveat only: a transit fit's duration and stellar density can still separate P from P/3, and we have not checked that.
- Cadence-level re-checks of the 14 flagged and control rows agreed with the quarter-level flags in 11 cases. The 3 disagreements (KOI-7930.01, 238.03, 8109.01, all candidates) come from quarters that are only partly covered. The cadence-level answer is the one to trust.

## 3. Candidate alias tests (kepler_alias 0.3.0, DR25 CANDIDATE only)

There were 18 candidates whose DR25 TCE and KOI periods differ by a whole factor. For each one, the light curve's transit depth was measured at every epoch of the shorter period, and the epochs were split into k groups. Results: 9 `short_period_real`, 3 `long_period_real`, 6 `inconclusive`.

Most results confirm the KOI period. Three do not:

| KOI | KOI P (d) | TCE P (d) | group depths at the KOI period (ppm) | reading |
|---|---|---|---|---|
| KOI-521.02 | 10.8206 | 5.4104 | 115 ± 20 and 124 ± 19 | 5.41 d. This is **already published**: Lissauer et al. 2024, arXiv:2311.00238 §III.2. Our test reproduces it independently. |
| **KOI-4893.01** | 6.58754 | 13.1751 | **314 ± 47** and **22 ± 43** | Favours **13.175 d**; same pattern in both halves of the mission (350/66 and 272/−16) |
| **KOI-4711.01** | 4.36383 | 8.72764 | 69 ± 29 and **267 ± 30** | Favours **8.728 d**; second half 23/302, first half 115/230 |

KOI-4893.01 (KIC 11970050) and KOI-4711.01 (KIC 8355131) are single-candidate systems with no KOI comment. The pipeline found **KOI-4893.01 at 13.1751 d in three separate runs** (Q1–Q16 TCE: 446.5 ppm, DR24: 394.2 ppm, DR25: 415.5 ppm), and **KOI-4711.01 at 8.7276 d in two** (DR24, DR25). Yet every KOI table from Q1–Q16 to DR25 and the cumulative table lists half those periods. The ratios are 2.00001 and 1.99999. The KOI depths (232 and 194 ppm) are close to what you get by folding one transit with one empty orbit. In KOI-4893.01's per-epoch depths (`epochs.csv`), the events at 13.18 d spacing sit mostly at +300 to +900 ppm throughout the mission, while the events in between scatter around zero (each event's error is about 350 ppm).

If the longer periods are right, the radii rise from 1.51 to about 1.8–2.1 R⊕ (KOI-4893.01) and from 1.08 to about 1.3–1.5 R⊕ (KOI-4711.01), scaling by the square root of the depth ratio (between our group depth over the KOI depth and a full factor of 2). Both remain candidates either way.

**Prior art checked:** Lissauer et al. 2024 (full text, 300k of 313k characters, through the tables; the rest is references) does not mention either KOI. That is expected, since it covers multi-planet systems. Coughlin et al. 2016 (DR24) §V.5 lists only KOI-5475.01 as a period fix. A web search found no paper naming either KOI with a period. We have not checked Thompson et al. 2018's machine-readable tables or ExoFOP-Kepler community notes (the ExoFOP page did not load).

**Limits:** this is a simple box-depth test on PDCSAP flux, using 2–3 long-cadence points per event. It is not a transit fit. Alternating depths at the shorter period can also come from systematics or a blended eclipsing binary. Either way, the catalogued shorter period does not fit. A free-period transit fit and pixel-level checks are the next step. These are leads to check, not corrections to submit.

## 4. Pre-registered predictions, scored: 6 of 8

| Prediction (written before the runs) | Result | Held? |
|---|---|---|
| Kepler-1633 b flagged 3P on its KOI ephemeris and P/2;P/3 (not P/4, P/5) on 186.40 d | exactly that | yes |
| Kepler-1632 b and Kepler-1802 b unflagged | unflagged | yes |
| fewer than 25 confirmed planets with any flag | 3 rows (2 planets) | yes |
| ≥ 80% of light-curve re-checks agree with the quarter flags | 11 / 14 = 78.6% | **no** |
| KOI-521.02 short_period_real or inconclusive | short_period_real | yes |
| KOI-4893.01 long_period_real | long_period_real | yes |
| KOI-6798.01 inconclusive | long_period_real (153.8 ± 27.6 vs 17.9 ± 27.7 ppm), i.e. the KOI's own 2.642 d is confirmed over the TCE's 1.321 d | **no** |
| impossible-count rows include Kepler-1301 b and KOI-521.02 | both present | yes (but see §1 for what that flag means) |

## Reproduce

```
python -m unittest -v test_kepler_coverage test_kepler_alias
python kepler_coverage.py --data-dir data --out-dir out-cov --max-targets 40
python kepler_alias.py --data-dir data --out-dir out-alias --max-targets 40 --dispositions CANDIDATE
```

Queries used by hand for §1 and §3 (NASA Exoplanet Archive TAP): `q1_q16_tce`, `q1_q17_dr24_tce`, `q1_q17_dr25_tce` with `kepid = 11970050 or kepid = 8355131`; `q1_q16_koi`, `q1_q17_dr24_koi`, `q1_q17_dr25_koi`, `cumulative` with `kepoi_name like 'K04893%' or kepoi_name like 'K04711%'`; `q1_q17_dr25_koi` and `pscomppars` for KOI-179 / KIC 9663113.
