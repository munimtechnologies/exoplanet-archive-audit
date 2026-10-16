# Update, 2026-10-16 (seventh): the pipeline's own secondary search backs KOI-4893.01 at 13.18 d and weakens KOI-4711.01

By MV2 of Munim, Inc. The queries, checks and this write-up were made with AI agents working in his name. No person has independently re-derived these numbers yet. Text CC BY 4.0; code Apache-2.0.

This follows `findings/2026-10-16-coverage-candidates.md` §3, which found two DR25 candidates whose light curves favour twice their catalogued period. This note uses only numbers the Kepler pipeline already published (NASA Exoplanet Archive tables `q1_q12_koi`, `q1_q16_koi`, `q1_q16_tce`, `q1_q17_dr24_tce`, `q1_q17_dr25_koi`, `q1_q17_dr25_sup_koi`, `q1_q17_dr25_tce`, `cumulative`). **The check in §2 was not pre-registered:** we looked at these columns and then drew the conclusion. The census in §5 *is* pre-registered.

## 1. Where the half period comes from

| | KOI-4893.01 (KIC 11970050) | KOI-4711.01 (KIC 8355131) |
|---|---|---|
| Q1–Q12 KOI table (where both KOIs first appear) | 6.58753753 d, 233.7 ppm | 4.3638363 d, 200 ppm |
| Q1–Q16 TCE | 13.1751 d, 446.5 ppm | none |
| DR24 TCE | 13.1751 d, 394.2 ppm | 8.7276 d, 242.1 ppm |
| DR25 TCE | 13.1750793 d, 415.5 ppm | 8.72763776 d, 275.7 ppm |
| DR25 KOI / supplemental / cumulative | 6.58753699 d, 232.1 ppm | 4.3638313 d, 194.1 ppm |

Each later TCE was matched back to the existing KOI. Thompson et al. 2018 (arXiv:1710.06758, §VI.2) explain that TCEs "found at double or half the period are also considered matches (244 KOIs in total)", with at least 95 % of the every-other transit cadences overlapping. The KOI keeps its original period. The DR25 KOI fit was rerun at the short period (6.58753699 d, not the Q1–Q12 value). Its depth is about half the TCE's, which is what folding one transit with one empty orbit gives. Lissauer et al. 2024 (arXiv:2311.00238) describe the same mechanism in the other direction for KOI-521.02: the TCEs had the correct 5.41 d, but the KOI was "assigned the previous period".

## 2. The weak-secondary check

DV searches every TCE for its strongest event outside the primary transit and reports its phase in days (`tce_maxmesd`) and its strength (`tce_maxmes`). If a TCE was found at k times a correct KOI period, the "missing" transits sit at phases j/k of the TCE orbit, so that is where the strongest secondary should land. We read these columns for all 15 DR25 candidates whose TCE period is a whole multiple of the KOI period (the `tce_long` rows of `results/2026-10-16-kepler-alias-0.3.0-candidates/lightcurve_tests.csv`):

| KOI | k | KOI P (d) | secondary phase | off by (d) | secondary MES | box-test reading (run 51) |
|---|---|---|---|---|---|---|
| KOI-2093.03 | 2 | 0.496 | 0.4992 | 0.0008 | 11.1 | short_period_real |
| KOI-2732.04 | 2 | 24.561 | 0.5018 | 0.089 | 3.7 | inconclusive |
| KOI-2796.01 | 2 | 0.537 | 0.5057 | 0.006 | 9.0 | short_period_real |
| KOI-2874.01 | 2 | 0.353 | 0.5009 | 0.0006 | 18.2 | short_period_real |
| KOI-3318.02 | 2 | 25.697 | 0.5000 | 0.0009 | 4.1 | inconclusive |
| KOI-3980.01 | 2 | 0.469 | 0.4994 | 0.0006 | 19.6 | short_period_real |
| KOI-4144.01 | 2 | 0.488 | 0.4916 | 0.008 | 12.5 | short_period_real |
| KOI-4216.01 | 2 | 0.492 | 0.4985 | 0.0015 | 16.6 | short_period_real |
| KOI-4419.01 | 2 | 0.260 | 0.5052 | 0.003 | 11.0 | (no epochs measured) |
| KOI-4685.01 | 2 | 0.494 | 0.5090 | 0.009 | 9.6 | short_period_real |
| KOI-4711.01 | 2 | 4.364 | **0.5002** | 0.0014 | 3.4 | long_period_real |
| KOI-4844.01 | 3 | 0.428 | 0.3308 (1/3) | 0.003 | 5.6 | inconclusive |
| **KOI-4893.01** | 2 | 6.588 | **0.6499** | **1.975** | **2.7** | long_period_real |
| KOI-7157.01 | 2 | 23.983 | 0.4966 | 0.161 | 4.6 | inconclusive |
| KOI-7859.01 | 2 | 0.307 | 0.4942 | 0.004 | 10.8 | short_period_real |

In 14 of the 15, the strongest secondary sits within 0.17 d of phase j/k. **KOI-4893.01 is the only exception.** Its strongest secondary is at phase 0.650, 1.98 d from phase 0.5 (its transit lasts 2.0 h), and it is the weakest of the 15 (MES 2.7). DR24 gives the same answer from a separate processing: phase 0.6505, MES 3.7. Note that DR24 and DR25 reprocess the same raw data, so they are not independent.

**What this adds.** For KOI-4893.01 there are now three readings of the data, and they agree:
- the pipeline detected 13.175 d in all three TCE runs;
- the box test gives 314 ± 47 vs 22 ± 43 ppm, in both halves of the mission;
- the pipeline's own search finds nothing at phase 0.5 of the 13.175 d orbit.

The catalogued 6.588 d needs a transit at phase 0.5, and none is seen there.

**A caution about `wst_depth`.** The depth DV reports for the secondary is not a reliable test of equal depths. For KOI-3980.01, whose alternate events have equal box depths (232.5 ± 15.6 and 231.6 ± 15.0 ppm), `wst_depth` / `tce_depth` = 0.37. We therefore use only the secondary's phase, not its depth.

## 3. What the pipeline's own fit says KOI-4893.01 is

The DR25 DV fit at 13.1750793 d (the same stellar radius, 0.99 R☉, as the KOI table) gives:

| | KOI table (6.588 d) | DR25 TCE fit (13.175 d) |
|---|---|---|
| radius | 1.51 R⊕ | **2.28 R⊕** |
| insolation | 228 S⊕ | **91 S⊕** |
| equilibrium temperature | 992 K | **787 K** |
| a/R* | 24.8 | 30.0 |

The DV difference-image centroid offset for the 13.175 d events is 0.23 ± 0.80″ from the KIC position (0.20 ± 0.88″ from the out-of-transit centroid). That is consistent with the target star, within the errors. Our planned pixel test of KOI-4893.01 would mostly repeat this, so it drops in priority. The radius estimate in the previous note (1.8–2.1 R⊕, scaled from box depths) is superseded by the pipeline's fit, but it is still a single fit and not a full MCMC.

## 4. KOI-4711.01 is weaker than the previous note said

DV's strongest secondary for KOI-4711.01 is at phase 0.5002 in DR25 (MES 3.4) and 0.5013 in DR24 (MES 4.3). So **something is there at the alternate epochs.** The box test still finds those events shallower: 69 ± 29 vs 267 ± 30 ppm overall (4.8σ apart), but only 115 ± 40 vs 230 ± 44 in the first half of the mission (1.9σ apart) against 23 ± 41 vs 302 ± 41 in the second.

- If both sets of events are real transits of one planet, the period is 4.364 d and the unequal depths would have to be noise or systematics.
- If the depths really differ, neither period describes a clean planet. A 1.3 R⊕ planet at a/R* = 42 cannot have an 82 ppm occultation at phase 0.5 (reflected light would be under 1 ppm). An eclipsing binary with primary and secondary eclipses at 8.73 d, diluted by the target, would fit.

We now call KOI-4711.01 **unresolved**, not "favours 8.728 d". The alternate events are too shallow for a centroid test, so the pixel test planned for it is dropped.

## 5. Pre-registered: `dv_alias` 0.1.0 census over every DR25 KOI

`dv_alias.py` (Apache-2.0, standard library) runs the §2 check on every DR25 KOI–TCE pair whose periods differ by a whole factor k ≥ 2 (within 0.1 %), for all dispositions, including confirmed planets. It also adds the DR24 phase as a consistency column. For the reverse case (TCE shorter than KOI) it reports DV's odd/even statistic. Predictions, written before the run:

1. All unit tests pass.
2. Between 150 and 350 KOI rows have a whole-number ratio (Thompson et al. count 244 at double or half).
3. KOI-4893.01 is `no_alias_secondary` in DR25 and DR24, and the other 14 rows in §2 are `secondary_at_alias`. This is a check of the code, not a test of the sky, since we read those values by hand.
4. At least 60 % of TCE-longer rows (all dispositions) are `secondary_at_alias`.
5. At most 3 CONFIRMED planets are TCE-longer and `no_alias_secondary`.
6. Kepler-1301 b (KOI-2643.01), Kepler-458 b (KOI-179.02) and Kepler-167 e (KOI-490.02) appear as KOI-longer, k = 2.

A `no_alias_secondary` row is a pointer for a light-curve check, not a period correction.

## Prior art checked

- **Thompson et al. 2018**, full text (all 346k characters via ar5iv): describes the double/half federation rule and the PLANET_PERIOD_IS_HALF override, but names neither KOI.
- **Valizadegan et al. 2022** (ExoMiner, arXiv:2111.10009; first 100k characters read): for confirmed planets whose DR25 TCE and Cumulative KOI periods differ, they "corrected the period", taking the Cumulative value. There were 5 such TCEs: 3239945.1, **6933567.1 (Kepler-1301 b)**, 8561063.3, 8416523.1 and 9663113.2. Neither of our two KOIs is listed (both are candidates, not confirmed). For Kepler-1301 b this means ExoMiner assumed the 9.08 d Cumulative period; our open lead questions that assumption (`findings/2026-10-16-lightcurves.md`; pixel test queued).
- **Lissauer et al. 2024** (multi-planet systems only), **Coughlin et al. 2016** §V.5, and **Ofir & Dreizler 2012** (Q1–Q6, before these KOIs existed): neither KOI appears.
- **Web searches** for the KOI and KIC numbers: no paper found.

## Limits

- §2 uses one pipeline number per TCE. A strongest-secondary search can miss a real alternate transit if a systematic elsewhere is stronger. For KOI-4893.01 the box test independently finds no alternate transit, but both rest on the same light curve.
- The §3 values are DV's fit, not a published planet characterization.
- None of this has been checked by a person, and these are not corrections we have submitted to anyone.

## Reproduce

TAP (`https://exoplanetarchive.ipac.caltech.edu/TAP/sync?format=csv&query=...`):

```
select k.kepoi_name, k.koi_period, t.tce_period, t.tce_depth, t.tce_maxmesd, t.wst_depth, t.tce_maxmes,
       t.tce_dikco_msky, t.tce_dikco_msky_err, t.tce_prad, k.koi_prad
from q1_q17_dr25_koi k join q1_q17_dr25_tce t on k.kepid = t.kepid and k.koi_tce_plnt_num = t.tce_plnt_num
where k.kepoi_name in ('K02093.03', ..., 'K07859.01')
```

plus `q1_q17_dr24_tce`, `q1_q16_tce` (`kepid = 11970050 or kepid = 8355131`) and `q1_q12_koi`. The census: `python -m unittest -v test_dv_alias && python dv_alias.py --out-dir out`.
