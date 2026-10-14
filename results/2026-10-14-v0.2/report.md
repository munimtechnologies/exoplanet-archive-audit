# NASA Exoplanet Archive self-consistency audit (exo_audit 0.2.0)

Downloaded 2026-10-14T14:00Z from https://exoplanetarchive.ipac.caltech.edu/TAP/sync. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Each flag is a candidate for checking against the source paper, not a confirmed error.

## Systematic offsets by reference

A reference is listed when at least 5 of its rows were tested, their median ratio (observed / predicted) is more than 10% from 1, and at least half of them lie within 10% of that median. Pipeline catalogs (Kepler KOI tables) are marked: their a/R* and stellar densities are free transit-fit parameters, so offsets there are expected physics, not slips.

| table | check | reference | pipeline | rows | median ratio | within 10% | unit pattern | median after fix |
|---|---|---|---|---|---|---|---|---|
| ps | st_dens_vs_MR | Fulton & Petigura 2018 |  | 1414 | 0.7163 | 0.925 | solar vs g/cm3 density (1.41) | 1.01 |
| ps | st_dens_vs_MR | Torres et al. 2017 |  | 22 | 0.7025 | 0.909 | solar vs g/cm3 density (1.41) | 0.9904 |
| ps | st_dens_vs_MR | Mann et al. 2017 |  | 19 | 0.7099 | 0.684 | solar vs g/cm3 density (1.41) | 1.001 |
| ps | st_dens_vs_MR | MacDonald et al. 2016 |  | 11 | 0.7056 | 1.000 | solar vs g/cm3 density (1.41) | 0.9948 |
| pscomppars | insolation | Torres et al. 2017 |  | 11 | 0.7193 | 0.636 | solar vs g/cm3 density (1.41) | 1.014 |
| pscomppars | st_dens_vs_MR | Mann et al. 2017 |  | 7 | 0.7184 | 0.714 | solar vs g/cm3 density (1.41) | 1.013 |
| ps | logg_vs_MR | Leleu et al. 2024 |  | 6 | 0.6963 | 1.000 | solar vs g/cm3 density (1.41) | 0.9817 |
| pscomppars | logg_vs_MR | Leleu et al. 2024 |  | 6 | 0.6963 | 1.000 | solar vs g/cm3 density (1.41) | 0.9817 |
| pscomppars | logg_vs_MR | Moutou et al. 2015 |  | 6 | 0.7082 | 0.500 | solar vs g/cm3 density (1.41) | 0.9984 |
| pscomppars | st_dens_vs_MR | MacDonald et al. 2016 |  | 5 | 0.7056 | 1.000 | solar vs g/cm3 density (1.41) | 0.9948 |
| pscomppars | logg_vs_MR | Tuomi et al. 2013 |  | 5 | 0.7181 | 1.000 | solar vs g/cm3 density (1.41) | 1.012 |
| ps | depth_vs_k2 | Q1-Q16 KOI Table | yes | 2720 | 1.182 | 0.796 |  |  |
| ps | depth_vs_k2 | Q1-Q17 DR24 KOI Table | yes | 2700 | 1.182 | 0.796 |  |  |
| ps | depth_vs_k2 | Q1-Q12 KOI Table | yes | 2678 | 1.182 | 0.795 |  |  |
| ps | depth_vs_k2 | Q1-Q17 DR25 KOI Table | yes | 2718 | 1.168 | 0.669 |  |  |
| pscomppars | depth_vs_k2 | Q1-Q17 DR25 KOI Table | yes | 1894 | 1.126 | 0.698 |  |  |
| pscomppars | depth_vs_k2 | Q1-Q17 DR24 KOI Table | yes | 741 | 1.187 | 0.765 |  |  |
| ps | depth_vs_k2 | Vanderburg et al. 2016 |  | 107 | 1.179 | 0.804 |  |  |
| ps | st_dens_vs_MR | Soto et al. 2018 |  | 5 | 0.2333 | 0.600 |  |  |
| ps | logg_vs_MR | Leleu et al. 2021 |  | 8 | 0.6703 | 0.750 |  |  |
| ps | depth_vs_k2 | Torres et al. 2017 |  | 22 | 1.145 | 0.727 |  |  |
| pscomppars | logg_vs_MR | Unger et al. 2021 |  | 12 | 1.258 | 0.667 |  |  |
| ps | logg_vs_MR | Moutou et al. 2026 |  | 7 | 0.6886 | 0.714 |  |  |
| ps | logg_vs_MR | Lubin et al. 2022 |  | 11 | 0.7939 | 1.000 |  |  |
| ps | logg_vs_MR | Gonz&aacute;lez Hern&aacute;ndez et al. 2024 |  | 5 | 0.6121 | 1.000 |  |  |
| pscomppars | st_dens_vs_MR | Wright et al. 2009 |  | 11 | 0.8053 | 0.545 |  |  |
| pscomppars | logg_vs_MR | Moutou et al. 2026 |  | 6 | 0.6886 | 0.667 |  |  |
| pscomppars | depth_vs_k2 | Vanderburg et al. 2016 |  | 8 | 1.317 | 0.625 |  |  |
| pscomppars | logg_vs_MR | Jenkins et al. 2025 |  | 7 | 0.7334 | 0.714 |  |  |
| pscomppars | logg_vs_MR | Fabrycky et al. 2012 |  | 8 | 0.7711 | 0.625 |  |  |
| ps | logg_vs_MR | Donati et al. 2023 |  | 6 | 1.354 | 1.000 |  |  |
| pscomppars | logg_vs_MR | Gajdo&scaron; et al. 2019 |  | 9 | 0.8181 | 0.667 |  |  |
| pscomppars | depth_vs_k2 | Q1-Q16 KOI Table | yes | 13 | 1.149 | 0.692 |  |  |
| ps | logg_vs_MR | Triaud et al. 2010 |  | 6 | 1.331 | 0.500 |  |  |
| pscomppars | depth_vs_k2 | Torres et al. 2017 |  | 12 | 1.148 | 0.583 |  |  |
| ps | logg_vs_MR | David et al. 2018 |  | 6 | 1.298 | 0.667 |  |  |
| pscomppars | st_dens_vs_MR | Torres et al. 2017 |  | 8 | 0.8242 | 0.625 |  |  |
| ps | logg_vs_MR | Lubin et al. 2024 |  | 6 | 0.7939 | 1.000 |  |  |
| pscomppars | logg_vs_MR | Frensch et al. 2023 |  | 8 | 0.8422 | 0.500 |  |  |
| pscomppars | logg_vs_MR | Trifonov et al. 2018 |  | 5 | 0.7636 | 0.800 |  |  |
| ps | logg_vs_MR | Demangeon et al. 2021 |  | 10 | 0.8854 | 0.500 |  |  |
| pscomppars | logg_vs_MR | Lubin et al. 2022 |  | 5 | 0.7939 | 1.000 |  |  |
| pscomppars | logg_vs_MR | Butler et al. 2006 |  | 6 | 1.212 | 0.667 |  |  |
| ps | rhostar_transit_vs_MR | D&iacute;ez Alonso et al. 2018 |  | 8 | 0.8707 | 0.500 |  |  |
| pscomppars | rhostar_transit_vs_MR | D&iacute;ez Alonso et al. 2018 |  | 8 | 0.8707 | 0.500 |  |  |
| ps | depth_vs_k2 | Lissauer et al. 2013 |  | 6 | 1.199 | 0.833 |  |  |
| pscomppars | depth_vs_k2 | Lissauer et al. 2013 |  | 6 | 1.199 | 0.833 |  |  |
| pscomppars | logg_vs_MR | Lo Curto et al. 2013 |  | 5 | 1.243 | 0.600 |  |  |
| ps | logg_vs_MR | Fischer et al. 2007 |  | 5 | 1.22 | 0.600 |  |  |
| pscomppars | rhostar_transit_vs_MR | Dressing et al. 2017 |  | 8 | 0.884 | 0.500 |  |  |
| ps | logg_vs_MR | Motalebi et al. 2015 |  | 5 | 1.207 | 1.000 |  |  |
| ps | st_dens_vs_MR | Hedges et al. 2021 |  | 5 | 0.8292 | 0.800 |  |  |
| ps | logg_vs_MR | Moutou et al. 2011 |  | 6 | 1.167 | 0.500 |  |  |
| ps | logg_vs_MR | Barros et al. 2016 |  | 7 | 1.134 | 1.000 |  |  |
| ps | depth_vs_k2 | Borucki et al. 2013 |  | 5 | 1.19 | 0.800 |  |  |
| pscomppars | depth_vs_k2 | Borucki et al. 2013 |  | 5 | 1.19 | 0.800 |  |  |
| ps | logg_vs_MR | Niraula et al. 2017 |  | 5 | 1.176 | 1.000 |  |  |
| pscomppars | depth_vs_k2 | Fabrycky et al. 2012 |  | 8 | 1.101 | 0.750 |  |  |
| pscomppars | depth_vs_k2 | Chaplin et al. 2013 |  | 5 | 0.8583 | 0.600 |  |  |
| ps | logg_vs_MR | Vogt et al. 2015 |  | 6 | 0.8814 | 1.000 |  |  |

## Table `ps` (40336 rows)

| check | rows tested | flagged | gross (x2) | unit-slip pattern | flagged, same ref for planet and star | flagged default rows |
|---|---|---|---|---|---|---|
| kepler3_a | 20500 | 80 | 3 | 1 | 77 | 40 |
| bulk_density | 2494 | 15 | 5 | 0 | 14 | 6 |
| a_over_rstar | 14769 | 9863 | 1565 | 0 | 9863 | 62 |
| rp_over_rstar | 20798 | 114 | 6 | 0 | 106 | 11 |
| depth_vs_k2 | 14340 | 163 | 136 | 11 | 160 | 15 |
| rhostar_transit_vs_MR | 16329 | 807 | 692 | 40 | 777 | 40 |
| st_dens_vs_MR | 22589 | 1729 | 759 | 63 | 1664 | 75 |
| logg_vs_MR | 28314 | 101 | 40 | 0 | 99 | 46 |
| insolation | 13503 | 28 | 13 | 0 | 28 | 23 |

## Table `pscomppars` (6445 rows)

| check | rows tested | flagged | gross (x2) | unit-slip pattern | same ref (n/a) | flagged default rows |
|---|---|---|---|---|---|---|
| kepler3_a | 5534 | 93 | 0 | 0 | n/a | n/a |
| bulk_density | 2232 | 19 | 10 | 0 | n/a | n/a |
| a_over_rstar | 3762 | 1518 | 303 | 0 | n/a | n/a |
| rp_over_rstar | 4649 | 326 | 8 | 0 | n/a | n/a |
| depth_vs_k2 | 4453 | 115 | 54 | 5 | n/a | n/a |
| rhostar_transit_vs_MR | 4159 | 543 | 431 | 23 | n/a | n/a |
| st_dens_vs_MR | 5835 | 727 | 339 | 14 | n/a | n/a |
| logg_vs_MR | 6091 | 136 | 41 | 0 | n/a | n/a |
| insolation | 5581 | 1269 | 325 | 1 | n/a | n/a |

## Likely unit slips in single rows, excluding pipeline catalogs (first 60)

| table | planet | check | observed | predicted | ratio | pattern | source |
|---|---|---|---|---|---|---|---|
| ps | HAT-P-25 b | depth_vs_k2 | 0.0161 | 1.61036 | 0.009998 | x100 (percent vs fraction) | Wang et al. 2018 |
| ps | HD 189733 b | depth_vs_k2 | 0.02413 | 2.41305 | 0.01 | x100 (percent vs fraction) | Morello et al. 2014 |
| ps | TOI-1478 b | depth_vs_k2 | 0.10936 | 1.0404 | 0.1051 | Sun vs Jupiter radius (9.73) | Rice et al. 2022 |
| ps | TOI-2049 b | depth_vs_k2 | 0.2275 | 222.01 | 0.001025 | x1000 | Guenther et al. 2026 |
| ps | TOI-1694 c | kepler3_a | 0.1 | 0.996333 | 0.1004 | Sun vs Jupiter radius (9.73) | Polanski et al. 2024 |
| ps | TOI-5624 c | depth_vs_k2 | 0.762 | 0.076176 | 10 | Sun vs Jupiter radius (9.73) | Bonfanti et al. 2026 |
| ps | K2-114 b | depth_vs_k2 | 0.01352 | 1.35257 | 0.009996 | x100 (percent vs fraction) | Ikwut-Ukwa et al. 2020 |
| ps | Kepler-210 b | rhostar_transit_vs_MR | 0.273079 | 2.70365 | 0.101 | Sun vs Jupiter radius (9.73) | Ioannidis et al. 2014 |
| pscomppars | Lupus-TR-3 b | insolation | 15.9599 | 175.86 | 0.09075 | Jupiter vs Earth radius (11.21) | Calculated Value |
| pscomppars | Kepler-53 c | rhostar_transit_vs_MR | 0.198803 | 1.95981 | 0.1014 | Sun vs Jupiter radius (9.73) | Ofir et al. 2025 |
| pscomppars | HAT-P-25 b | depth_vs_k2 | 0.0161 | 1.61036 | 0.009998 | x100 (percent vs fraction) | Wang et al. 2018 |
| pscomppars | TOI-1478 b | depth_vs_k2 | 0.10936 | 1.0404 | 0.1051 | Sun vs Jupiter radius (9.73) | Rice et al. 2022 |
| pscomppars | TOI-5624 c | depth_vs_k2 | 0.762 | 0.076176 | 10 | Sun vs Jupiter radius (9.73) | Bonfanti et al. 2026 |
| pscomppars | TOI-2049 b | depth_vs_k2 | 0.2275 | 222.01 | 0.001025 | x1000 | Guenther et al. 2026 |

## Strongest flags in default rows whose planet and star parameters share one reference, excluding pipeline catalogs (first 60)

| planet | check | observed | predicted | ratio | z | reference |
|---|---|---|---|---|---|---|
| ZTF J1828+2308 b | rhostar_transit_vs_MR | 0.887323 | 382537 | 2.32e-06 | -277.11 | Parsons et al. 2025 |
| ZTF J1230-2655 b | rhostar_transit_vs_MR | 0.932138 | 489412 | 1.905e-06 | -215.57 | Parsons et al. 2025 |
| TOI-2049 b | depth_vs_k2 | 0.2275 | 222.01 | 0.001025 |  | Guenther et al. 2026 |
| TOI-2049 b | rp_over_rstar | 1.49 | 0.0476885 | 31.24 | 52.41 | Guenther et al. 2026 |
| HAT-P-25 b | depth_vs_k2 | 0.0161 | 1.61036 | 0.009998 |  | Wang et al. 2018 |
| WD 1856+534 b | depth_vs_k2 | 56.65 | 5299.84 | 0.01069 |  | Vanderburg et al. 2020 |
| PH1 b | rhostar_transit_vs_MR | 0.0107356 | 0.413175 | 0.02598 |  | Schwamb et al. 2013 |
| TOI-262 b | kepler3_a | 0.163 | 0.0947297 | 1.721 | 33.49 | Oddo et al. 2023 |
| Kepler-419 c | st_dens_vs_MR | 13.34 | 0.371984 | 35.86 | 26.93 | Dawson et al. 2014 |
| Kepler-419 b | st_dens_vs_MR | 13.34 | 0.371984 | 35.86 | 26.93 | Dawson et al. 2014 |
| TOI-908 b | insolation | 80.884 | 549.672 | 0.1471 | -26.35 | Hawthorn et al. 2023 |
| K2-174 b | a_over_rstar | 26.6 | 40.0799 | 0.6637 | -25.45 | Livingston et al. 2019 |
| TOI-5624 c | depth_vs_k2 | 0.762 | 0.076176 | 10 |  | Bonfanti et al. 2026 |
| K2-174 b | rhostar_transit_vs_MR | 0.930342 | 3.19459 | 0.2912 | -22.73 | Livingston et al. 2019 |
| TOI-1478 b | depth_vs_k2 | 0.10936 | 1.0404 | 0.1051 |  | Rice et al. 2022 |
| TOI-4602.01 | depth_vs_k2 | 0.006 | 0.0433889 | 0.1383 |  | Di Maio et al. 2026 |
| K2-285 e | rhostar_transit_vs_MR | 10.4826 | 2.40055 | 4.367 | 19.55 | Palle et al. 2019 |
| K2-285 e | kepler3_a | 0.18041 | 0.110682 | 1.63 | 19.31 | Palle et al. 2019 |
| G 9-40 b | st_dens_vs_MR | 1.62 | 15.0199 | 0.1079 | -17.83 | Luque et al. 2022 |
| HD 48948 d | insolation | 2.46 | 0.771777 | 3.187 | 15.57 | Dalal et al. 2024 |
| HD 48948 b | insolation | 138.85 | 43.4835 | 3.193 | 15.47 | Dalal et al. 2024 |
| HD 48948 c | insolation | 15.5 | 4.8563 | 3.192 | 15.41 | Dalal et al. 2024 |
| HD 10442 b | logg_vs_MR | 1548.82 | 7134.92 | 0.2171 |  | Luhn et al. 2019 |
| GJ 3929 b | rp_over_rstar | 0.0156 | 0.0312282 | 0.4995 | -13.37 | Beard et al. 2022 |
| TOI-1855 b | depth_vs_k2 | 0.707 | 2.6244 | 0.2694 |  | Schulte et al. 2024 |
| PH1 b | a_over_rstar | 22.1435 | 80.854 | 0.2739 |  | Schwamb et al. 2013 |
| TOI-2193 A b | bulk_density | 0.06 | 0.210945 | 0.2844 |  | Yee et al. 2022 |
| K2-349 b | rhostar_transit_vs_MR | 1.85221 | 6.47088 | 0.2862 |  | de Leon et al. 2021 |
| OGLE2-TR-L9 b | kepler3_a | 0.0308 | 0.0413274 | 0.7453 | -12.30 | Snellen et al. 2009 |
| K2-285 d | kepler3_a | 0.1178 | 0.0879427 | 1.34 | 11.12 | Palle et al. 2019 |
| K2-285 d | rhostar_transit_vs_MR | 5.77683 | 2.40055 | 2.406 | 11.11 | Palle et al. 2019 |
| TOI-128.01 | insolation | 182.406 | 545.068 | 0.3346 |  | Hord et al. 2024 |
| KELT-2 A b | logg_vs_MR | 31622.8 | 11334.6 | 2.79 |  | Stassun et al. 2017 |
| TOI-2578 b | logg_vs_MR | 29716.7 | 12945.4 | 2.296 | 9.70 | Guenther et al. 2026 |
| HD 6860 b | logg_vs_MR | 3.47536 | 9.14475 | 0.38 |  | Lee et al. 2023 |
| TOI-3862 b | rhostar_transit_vs_MR | 5.40183 | 1.62943 | 3.315 | 9.41 | Carleo et al. 2026 |
| TOI-3862 b | a_over_rstar | 8.848 | 5.93442 | 1.491 | 9.40 | Carleo et al. 2026 |
| HATS-62 b | bulk_density | 0.076 | 0.189695 | 0.4006 |  | Hartman et al. 2019 |
| GJ 887 b | logg_vs_MR | 14321.9 | 61960.3 | 0.2311 | -8.96 | Hartogh et al. 2026 |
| GJ 887 c | logg_vs_MR | 14321.9 | 61960.3 | 0.2311 | -8.96 | Hartogh et al. 2026 |
| GJ 887 d | logg_vs_MR | 14321.9 | 61960.3 | 0.2311 | -8.96 | Hartogh et al. 2026 |
| GJ 887 e | logg_vs_MR | 14321.9 | 61960.3 | 0.2311 | -8.96 | Hartogh et al. 2026 |
| TOI-3540 A b | bulk_density | 0.065 | 0.158557 | 0.4099 |  | Yee et al. 2022 |
| HD 154857 c | logg_vs_MR | 6606.93 | 15205.4 | 0.4345 |  | Wittenmyer et al. 2014 |
| HD 64121 b | kepler3_a | 1.51 | 1.68432 | 0.8965 | -8.19 | Ottoni et al. 2022 |
| K2-285 c | kepler3_a | 0.0824 | 0.068185 | 1.208 | 7.98 | Palle et al. 2019 |
| TOI-4616 b | logg_vs_MR | 50118.7 | 144519 | 0.3468 | -7.98 | Lang et al. 2026 |
| K2-285 c | rhostar_transit_vs_MR | 4.23453 | 2.40055 | 1.764 | 7.87 | Palle et al. 2019 |
| GJ 3323 b | insolation | 2.58 | 1.17953 | 2.187 |  | Astudillo-Defru et al. 2017 |
| NGTS-14 A b | logg_vs_MR | 15848.9 | 34725.8 | 0.4564 | -7.76 | Smith et al. 2021 |
| KELT-7 b | logg_vs_MR | 31622.8 | 14728.4 | 2.147 |  | Stassun et al. 2017 |
| GJ 3323 c | insolation | 0.17 | 0.079523 | 2.138 |  | Astudillo-Defru et al. 2017 |
| TOI-216.02 | depth_vs_k2 | 0.475 | 1 | 0.475 |  | Dawson et al. 2021 |
| Ross 176 b | logg_vs_MR | 117490 | 48859.8 | 2.405 | 7.13 | Gerald&iacute;a-Gonz&aacute;lez et al. 2025 |
| NGTS-6 b | st_dens_vs_MR | 3.9304 | 2.52254 | 1.558 | 6.87 | Vines et al. 2019 |
| Kepler-413 b | st_dens_vs_MR | 1.755 | 2.47297 | 0.7097 | -6.66 | Kostov et al. 2014 |
| K2-43 c | rhostar_transit_vs_MR | 0.803506 | 5.05587 | 0.1589 | -6.56 | Hedges et al. 2019 |
| K2-43 b | rhostar_transit_vs_MR | 0.803825 | 5.05587 | 0.159 | -6.54 | Hedges et al. 2019 |
| TOI-411 b | rhostar_transit_vs_MR | 1.55503 | 1.11071 | 1.4 | 6.20 | Garai et al. 2023 |
| Kepler-1704 b | insolation | 0.342 | 0.688356 | 0.4968 | -6.19 | Dalba et al. 2021 |
