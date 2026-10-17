# Update, 2026-10-17: the dv_alias census is in; 6 of 6 pre-registered predictions held, and it finds no new period error among confirmed planets

By MV2 of Munim, Inc. The census, the checks and this write-up were made with AI agents working in his name. No person has independently re-derived these numbers yet. Text CC BY 4.0; code Apache-2.0.

This scores the census pre-registered in `findings/2026-10-16-dv-secondary.md` §5. `dv_alias.py` 0.1.0 (already on main) ran once in a sealed container on 2026-10-17 at 01:56Z against live NASA Exoplanet Archive TAP tables. Its unmodified output is in `results/2026-10-17-dv-alias-0.1.0/` (`census.csv`, `report.md`, `summary.json`).

**What it does.** For every DR25 KOI whose matched DR25 TCE has a period k times the KOI's (or 1/k; k ≥ 2, within 0.1 %), it asks where the Kepler pipeline's own weak-secondary search put the strongest non-primary event (`tce_maxmesd`). If the TCE is k times a correct KOI period, the "missing" transits sit at phase j/k, so the secondary should land there. `secondary_at_alias` means it does, to within one transit duration (at least one 29.4-min cadence). `no_alias_secondary` means it doesn't. Either verdict points at rows worth a light-curve check; neither is a period correction.

## 1. Scorecard

| # | Prediction (written before the run) | Result | Held? |
|---|---|---|---|
| 1 | All unit tests pass | `python -m unittest -v test_dv_alias` exit 0 | yes |
| 2 | 150–350 KOI rows with a whole-number ratio | 246 (137 TCE-longer, 109 KOI-longer) of 8,054 joined DR25 rows | yes |
| 3 | KOI-4893.01 `no_alias_secondary` in DR25 and DR24; the other 14 rows of the earlier hand table `secondary_at_alias` (a code check) | 4893.01: phase 0.6499 (DR25), 0.6505 (DR24), both `no_alias_secondary`; all 14 others `secondary_at_alias` in DR25 | yes |
| 4 | ≥ 60 % of TCE-longer rows `secondary_at_alias` | 117 of 137 (85.4 %) | yes |
| 5 | ≤ 3 CONFIRMED planets TCE-longer and `no_alias_secondary` | 1 (Kepler-1802 b) | yes |
| 6 | Kepler-1301 b, Kepler-458 b, Kepler-167 e appear as KOI-longer, k = 2 | all three, k = 2 | yes |

Six of six. Prediction 3 only checks the code against values we had already read by hand. Predictions 2 and 6 were loose. The ones that tested something were 4 and 5.

DR24 is a consistency column, not an independent test (DR24 and DR25 reprocess the same pixels). Where DR24 has a row, the two releases give the same verdict for 59 of 63 rows: 10 of 10 `no_alias_secondary` and 49 of 53 `secondary_at_alias`. The four that disagree (KOI-1269.01, 1286.01, 1735.01 and 3980.01) are `secondary_at_alias` in DR25 only. Three are false positives; the fourth is KOI-3980.01, whose alternate events the light-curve box test had already shown to be equal (232.5 ± 15.6 vs 231.6 ± 15.0 ppm).

## 2. Confirmed planets: the census recovers both known cases and finds no new one

Six confirmed planets have a whole-number KOI/TCE ratio:

| Planet | KOI | KOI P (d) | TCE P (d) | Census verdict | Archive default (ps, `default_flag = 1`) | Reading |
|---|---|---|---|---|---|---|
| Kepler-1802 b | 2174.03 | 7.725 | 15.450 | `no_alias_secondary`: secondary at phase 0.903, MES 2.7 (DR24 0.903, MES 3.9) | 15.45020008 d, Valizadegan et al. 2022 | Agrees with the default and with our light-curve box test (649 ± 55 vs −67 ± 49 ppm, `findings/2026-10-16-lightcurves.md`). The KOI depth (382 ppm) is half the TCE depth (739 ppm), which is what folding one transit with one empty orbit gives. |
| Kepler-1604 b | 4441.01 | 0.342 | 0.684 | `secondary_at_alias`: phase 0.503, MES 13.6 (DR24 0.485, MES 11.1) | 0.683684256 d, Morton et al. 2016 | A third, independent reading for 0.342 d, after Sanchis-Ojeda et al. 2014 (Table 1) and our box test (242.0 ± 6.6 vs 228.3 ± 6.7 ppm). Already written up as kind 22. Caveat unchanged: an eclipsing binary at 0.684 d with two equal eclipses would look the same. |
| Kepler-42 c | 961.02 | 0.453 | 0.907 | `secondary_at_alias`: phase 0.504, MES 9.7 | 0.45328509 d, Muirhead et al. 2012 | Consistent with the published short period. |
| Kepler-1301 b | 2643.01 | 9.082 | 4.541 | KOI-longer (odd/even stat 0.75) | 9.08237046 d, Morton et al. 2016 | Open lead; the pixel-level test is still waiting in the compute queue. |
| Kepler-458 b | 179.02 | 572.4 | 286.2 | KOI-longer | (checked earlier: 572 d) | Long period real; checked on 2026-10-16. |
| Kepler-167 e | 490.02 | 1071.2 | 535.6 | KOI-longer | 1071.23205 d, Chachan et al. 2022 | Long period real. |

So, with no tuning on these planets, the census flags the one confirmed planet whose published period is twice its KOI period (Kepler-1802 b). It also puts the one whose Archive default is twice the light-curve period (Kepler-1604 b) on the short-period side. Both are already known: they serve as controls, not discoveries. **Among confirmed planets, the pipeline's own secondary search turns up no period error we had not already found.**

## 3. Candidates: KOI-4893.01 is still the only lead

Among TCE-longer rows, 16 are candidates by Archive disposition. Fifteen are `secondary_at_alias`, which supports the KOI period. **KOI-4893.01 is the only candidate that is `no_alias_secondary`.** For it, the 13.175 d reading in `findings/2026-10-16-dv-secondary.md` stands and gains nothing new here.

Four candidates are KOI-longer (KOI period = 2 × TCE period):
- **KOI-521.02** (10.82 d KOI, 5.41 d TCE): Lissauer et al. 2024 (arXiv:2311.00238, §II.3) already give 5.41 d. Known.
- **KOI-6798.01** (2.64 / 1.32 d): our box test confirmed the KOI's 2.642 d (153.8 ± 27.6 vs 17.9 ± 27.7 ppm, `findings/2026-10-16-coverage-candidates.md`). Not an error.
- **KOI-272.01** (1.281 / 0.641 d) and **KOI-422.01** (809 / 404.5 d): see §4.

## 4. Two dispositions depend on which DR25 table you read

The DR25 KOI table (`q1_q17_dr25_koi`) gives a pipeline disposition of FALSE POSITIVE for four KOI-longer rows whose cumulative-table disposition is CANDIDATE or CONFIRMED:

| KOI | DR25 KOI table | flags / comment there | DR25 supplemental and cumulative |
|---|---|---|---|
| Kepler-458 b (179.02) | FALSE POSITIVE | nt; `INCONSISTENT_TRANS---CENT_FEW_DIFFS` | CONFIRMED (pipeline disposition CANDIDATE), no flags |
| Kepler-167 e (490.02) | FALSE POSITIVE | nt; `INDIV_TRANS_MARSHALL_ZUMA---INCONSISTENT_TRANS---CENT_FEW_DIFFS` | CONFIRMED (pipeline disposition CANDIDATE), no flags |
| KOI-272.01 | FALSE POSITIVE | ss; `MOD_ODDEVEN_ALT` | CANDIDATE, no flags |
| KOI-422.01 | FALSE POSITIVE | nt; `INDIV_TRANS_CHASES_MARSHALL_ZUMA---LPP_DV---LPP_ALT---INCONSISTENT_TRANS---CENT_FEW_DIFFS` | CANDIDATE, no flags |

One row goes the other way. KOI-4668.01 (15.07 d KOI, 7.54 d TCE, DV odd/even statistic 40.4) is CANDIDATE in the DR25 KOI table but FALSE POSITIVE (ss) in the supplemental and cumulative tables. A TCE at half the period with very unequal alternate events is what a secondary eclipse would give.

In each case the DR25 KOI table vetted a TCE at half the KOI period. Its "inconsistent transits" and odd/even flags are what you would expect from folding real events with empty orbits. The cumulative table takes its dispositions from the supplemental table (`koi_disp_prov = q1_q17_dr25_sup_koi` for all five), so **the Archive's main KOI table is right**. The practical point is for anyone who uses `q1_q17_dr25_koi` on its own: it lists two confirmed long-period planets as pipeline false positives. That matches Thompson et al. 2018's description of double/half-period federation (§VI.2). We did not find a list naming these five, but we are not calling it a new result.

We also read the cumulative flags and comments for the 10 long-period (100–1,064 d) KOI-longer rows that are false positives. Eight of the ten have reasons that don't depend on the period: resolved centroid offsets, ephemeris matches, secondary eclipses, V shapes or giant radii. The other two (KOI-5395.01 at 601 d, flagged by individual-transit tests; KOI-6880.01 at 553 d, `INCONSISTENT_TRANS` at 266,000 ppm) we did not re-check.

## 5. What this run does not settle

- The census reads one pipeline number per TCE. A strong systematic elsewhere in the orbit can hide a real alternate transit; the light-curve box tests are the stronger check.
- Kepler-1301 b (pixel test) and the Kepler-289 d/e duplicate census are still waiting in the compute queue. Their predictions are in the playbook, and both will be scored here when they land, including any misses.
- None of this has been checked by a person, and nothing here has been sent to the Archive.

## Reproduce

```
python -m unittest -v test_dv_alias
python dv_alias.py --out-dir out
```

Hand checks (TAP, `https://exoplanetarchive.ipac.caltech.edu/TAP/sync?format=csv&query=...`):

```
select pl_name, default_flag, pl_orbper, pl_refname from ps where hostname = 'Kepler-1802'
select pl_name, pl_orbper, pl_refname from ps where default_flag = 1 and pl_name in ('Kepler-1604 b', 'Kepler-42 c', 'Kepler-167 e', 'Kepler-1301 b', 'Kepler-1802 b')
select kepoi_name, koi_pdisposition, koi_fpflag_nt, koi_fpflag_ss, koi_fpflag_co, koi_fpflag_ec, koi_comment from q1_q17_dr25_koi where kepoi_name in ('K00179.02', 'K00490.02', 'K00272.01', 'K00422.01', 'K04668.01')
select kepoi_name, koi_disposition, koi_pdisposition, koi_fpflag_ss from q1_q17_dr25_sup_koi where kepoi_name in (...)
select kepoi_name, koi_disposition, koi_disp_prov, koi_comment from cumulative where kepoi_name in (...)
```
