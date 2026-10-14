# NASA Exoplanet Archive self-consistency audit (exo_audit)

Downloaded 2026-10-14T10:00Z from https://exoplanetarchive.ipac.caltech.edu/TAP/sync. Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Each flag is a candidate for checking against the source paper, not a confirmed error.

## Table `ps` (40336 rows)

| check | rows tested | flagged | gross (x2) | unit-slip pattern | flagged, same ref for planet and star | flagged default rows |
|---|---|---|---|---|---|---|
| kepler3_a | 20540 | 98 | 3 | 1 | 95 | 50 |
| bulk_density | 2494 | 15 | 5 | 0 | 14 | 6 |
| a_over_rstar | 14769 | 9863 | 1565 | 0 | 9863 | 62 |
| rp_over_rstar | 20798 | 114 | 6 | 0 | 106 | 11 |
| depth_vs_k2 | 14340 | 163 | 136 | 11 | 160 | 15 |
| rhostar_transit_vs_MR | 16329 | 807 | 692 | 40 | 777 | 40 |
| st_dens_vs_MR | 22589 | 1729 | 759 | 63 | 1664 | 75 |
| logg_vs_MR | 28314 | 101 | 40 | 0 | 99 | 46 |
| insolation | 13503 | 28 | 13 | 0 | 28 | 23 |

## Table `pscomppars` (6445 rows)

| check | rows tested | flagged | gross (x2) | unit-slip pattern | flagged, same ref for planet and star | flagged default rows |
|---|---|---|---|---|---|---|
| kepler3_a | 5565 | 104 | 0 | 0 | 0 | 0 |
| bulk_density | 2232 | 19 | 10 | 0 | 0 | 0 |
| a_over_rstar | 3762 | 1518 | 303 | 0 | 0 | 0 |
| rp_over_rstar | 4649 | 326 | 8 | 0 | 0 | 0 |
| depth_vs_k2 | 4453 | 115 | 54 | 5 | 0 | 0 |
| rhostar_transit_vs_MR | 4159 | 543 | 431 | 23 | 0 | 0 |
| st_dens_vs_MR | 5835 | 727 | 339 | 14 | 0 | 0 |
| logg_vs_MR | 6091 | 136 | 41 | 0 | 0 | 0 |
| insolation | 5581 | 1269 | 325 | 1 | 0 | 0 |

## Likely unit slips (first 60)

| table | planet | check | observed | predicted | ratio | pattern | reference |
|---|---|---|---|---|---|---|---|
| ps | HAT-P-25 b | depth_vs_k2 | 0.0161 | 1.61036 | 0.009998 | x100 (percent vs fraction) | Wang et al. 2018 |
| ps | HD 189733 b | depth_vs_k2 | 0.02413 | 2.41305 | 0.01 | x100 (percent vs fraction) | Morello et al. 2014 |
| ps | Kepler-743 b | rhostar_transit_vs_MR | 24.8187 | 2.15024 | 11.54 | Jupiter vs Earth radius (11.21) | Q1-Q17 DR25 KOI Table |
| ps | TOI-1478 b | depth_vs_k2 | 0.10936 | 1.0404 | 0.1051 | Sun vs Jupiter radius (9.73) | Rice et al. 2022 |
| ps | Kepler-421 b | rhostar_transit_vs_MR | 0.235369 | 2.31668 | 0.1016 | Sun vs Jupiter radius (9.73) | Q1-Q8 KOI Table |
| ps | TOI-2049 b | depth_vs_k2 | 0.2275 | 222.01 | 0.001025 | x1000 | Guenther et al. 2026 |
| ps | Kepler-223 e | rhostar_transit_vs_MR | 0.00400232 | 1.26026 | 0.003176 | Jupiter vs Earth mass (317.8) | Q1-Q16 KOI Table |
| ps | Kepler-223 e | st_dens_vs_MR | 0.00401 | 1.26026 | 0.003182 | Jupiter vs Earth mass (317.8) | Q1-Q16 KOI Table |
| ps | Kepler-223 e | rhostar_transit_vs_MR | 0.00400232 | 1.26026 | 0.003176 | Jupiter vs Earth mass (317.8) | Q1-Q17 DR24 KOI Table |
| ps | Kepler-223 e | st_dens_vs_MR | 0.00401 | 1.26026 | 0.003182 | Jupiter vs Earth mass (317.8) | Q1-Q17 DR24 KOI Table |
| ps | Kepler-223 e | rhostar_transit_vs_MR | 0.00400232 | 1.26026 | 0.003176 | Jupiter vs Earth mass (317.8) | Q1-Q12 KOI Table |
| ps | Kepler-223 e | st_dens_vs_MR | 0.00401 | 1.26026 | 0.003182 | Jupiter vs Earth mass (317.8) | Q1-Q12 KOI Table |
| ps | Kepler-244 c | st_dens_vs_MR | 23.6756 | 2.40228 | 9.855 | Sun vs Jupiter radius (9.73) | Q1-Q16 KOI Table |
| ps | Kepler-244 c | st_dens_vs_MR | 23.6756 | 2.40228 | 9.855 | Sun vs Jupiter radius (9.73) | Q1-Q12 KOI Table |
| ps | Kepler-244 c | st_dens_vs_MR | 23.6756 | 2.40228 | 9.855 | Sun vs Jupiter radius (9.73) | Q1-Q17 DR24 KOI Table |
| ps | Kepler-408 b | st_dens_vs_MR | 8.01283 | 0.827505 | 9.683 | Sun vs Jupiter radius (9.73) | Q1-Q12 KOI Table |
| ps | Kepler-408 b | st_dens_vs_MR | 8.01283 | 0.827505 | 9.683 | Sun vs Jupiter radius (9.73) | Q1-Q16 KOI Table |
| ps | Kepler-408 b | st_dens_vs_MR | 8.01283 | 0.827505 | 9.683 | Sun vs Jupiter radius (9.73) | Q1-Q17 DR24 KOI Table |
| ps | TOI-1694 c | kepler3_a | 0.1 | 0.996333 | 0.1004 | Sun vs Jupiter radius (9.73) | Polanski et al. 2024 |
| ps | Kepler-943 b | st_dens_vs_MR | 0.2356 | 2.33617 | 0.1008 | Sun vs Jupiter radius (9.73) | Q1-Q17 DR25 KOI Table |
| ps | TOI-5624 c | depth_vs_k2 | 0.762 | 0.076176 | 10 | Sun vs Jupiter radius (9.73) | Bonfanti et al. 2026 |
| ps | Kepler-1780 b | rhostar_transit_vs_MR | 18.0364 | 1.87119 | 9.639 | Sun vs Jupiter radius (9.73) | Q1-Q17 DR25 KOI Table |
| ps | Kepler-1780 b | st_dens_vs_MR | 18.0332 | 1.87119 | 9.637 | Sun vs Jupiter radius (9.73) | Q1-Q17 DR25 KOI Table |
| ps | Kepler-1780 b | st_dens_vs_MR | 18.0332 | 1.87119 | 9.637 | Sun vs Jupiter radius (9.73) | Valizadegan et al. 2022 |
| ps | Kepler-1768 b | rhostar_transit_vs_MR | 0.0707942 | 1.68193 | 0.04209 | hours vs days (24) | Q1-Q8 KOI Table |
| ps | Kepler-1058 b | st_dens_vs_MR | 0.19135 | 4.65974 | 0.04106 | hours vs days (24) | Q1-Q17 DR24 KOI Table |
| ps | Kepler-1058 b | st_dens_vs_MR | 0.19135 | 4.65974 | 0.04106 | hours vs days (24) | Q1-Q16 KOI Table |
| ps | Kepler-1058 b | st_dens_vs_MR | 0.19135 | 4.65974 | 0.04106 | hours vs days (24) | Q1-Q12 KOI Table |
| ps | Kepler-409 b | rhostar_transit_vs_MR | 19.7931 | 1.81738 | 10.89 | Jupiter vs Earth radius (11.21) | Q1-Q12 KOI Table |
| ps | Kepler-409 b | st_dens_vs_MR | 19.7942 | 1.81738 | 10.89 | Jupiter vs Earth radius (11.21) | Q1-Q12 KOI Table |
| ps | Kepler-409 b | rhostar_transit_vs_MR | 19.7931 | 1.81738 | 10.89 | Jupiter vs Earth radius (11.21) | Q1-Q17 DR24 KOI Table |
| ps | Kepler-409 b | st_dens_vs_MR | 19.7942 | 1.81738 | 10.89 | Jupiter vs Earth radius (11.21) | Q1-Q17 DR24 KOI Table |
| ps | Kepler-409 b | rhostar_transit_vs_MR | 19.7931 | 1.81738 | 10.89 | Jupiter vs Earth radius (11.21) | Q1-Q16 KOI Table |
| ps | Kepler-409 b | st_dens_vs_MR | 19.7942 | 1.81738 | 10.89 | Jupiter vs Earth radius (11.21) | Q1-Q16 KOI Table |
| ps | Kepler-1979 b | rhostar_transit_vs_MR | 0.0177488 | 1.75607 | 0.01011 | x100 (percent vs fraction) | Q1-Q17 DR24 KOI Table |
| ps | Kepler-1979 b | st_dens_vs_MR | 0.01772 | 1.75607 | 0.01009 | x100 (percent vs fraction) | Q1-Q17 DR24 KOI Table |
| ps | Kepler-1979 b | rhostar_transit_vs_MR | 0.0177488 | 1.75607 | 0.01011 | x100 (percent vs fraction) | Q1-Q16 KOI Table |
| ps | Kepler-1979 b | st_dens_vs_MR | 0.01772 | 1.75607 | 0.01009 | x100 (percent vs fraction) | Q1-Q16 KOI Table |
| ps | Kepler-1979 b | depth_vs_k2 | 0.07589 | 8.20009 | 0.009255 | Sun vs Earth radius (109.1) | Q1-Q17 DR25 KOI Table |
| ps | Kepler-1979 b | rhostar_transit_vs_MR | 0.0177488 | 1.75607 | 0.01011 | x100 (percent vs fraction) | Q1-Q12 KOI Table |
| ps | Kepler-1979 b | st_dens_vs_MR | 0.01772 | 1.75607 | 0.01009 | x100 (percent vs fraction) | Q1-Q12 KOI Table |
| ps | Kepler-1124 b | rhostar_transit_vs_MR | 75.3334 | 6.80222 | 11.07 | Jupiter vs Earth radius (11.21) | Q1-Q17 DR24 KOI Table |
| ps | Kepler-1124 b | st_dens_vs_MR | 75.3516 | 6.80222 | 11.08 | Jupiter vs Earth radius (11.21) | Q1-Q17 DR24 KOI Table |
| ps | Kepler-1124 b | rhostar_transit_vs_MR | 75.3334 | 6.80222 | 11.07 | Jupiter vs Earth radius (11.21) | Q1-Q12 KOI Table |
| ps | Kepler-1124 b | st_dens_vs_MR | 75.3516 | 6.80222 | 11.08 | Jupiter vs Earth radius (11.21) | Q1-Q12 KOI Table |
| ps | Kepler-1124 b | rhostar_transit_vs_MR | 75.3334 | 6.80222 | 11.07 | Jupiter vs Earth radius (11.21) | Q1-Q16 KOI Table |
| ps | Kepler-1124 b | st_dens_vs_MR | 75.3516 | 6.80222 | 11.08 | Jupiter vs Earth radius (11.21) | Q1-Q16 KOI Table |
| ps | Kepler-1069 b | st_dens_vs_MR | 0.03487 | 0.820295 | 0.04251 | hours vs days (24) | Q1-Q12 KOI Table |
| ps | Kepler-1069 b | st_dens_vs_MR | 0.03487 | 0.820295 | 0.04251 | hours vs days (24) | Q1-Q17 DR24 KOI Table |
| ps | Kepler-1069 b | st_dens_vs_MR | 0.03487 | 0.820295 | 0.04251 | hours vs days (24) | Q1-Q16 KOI Table |
| ps | Kepler-1821 b | st_dens_vs_MR | 19.0611 | 1.9306 | 9.873 | Sun vs Jupiter radius (9.73) | Valizadegan et al. 2022 |
| ps | Kepler-1821 b | rhostar_transit_vs_MR | 19.0901 | 1.9306 | 9.888 | Sun vs Jupiter radius (9.73) | Q1-Q17 DR25 KOI Table |
| ps | Kepler-1821 b | st_dens_vs_MR | 19.0611 | 1.9306 | 9.873 | Sun vs Jupiter radius (9.73) | Q1-Q17 DR25 KOI Table |
| ps | Kepler-303 c | rhostar_transit_vs_MR | 60.4799 | 5.5265 | 10.94 | Jupiter vs Earth radius (11.21) | Q1-Q12 KOI Table |
| ps | Kepler-303 c | st_dens_vs_MR | 60.484 | 5.5265 | 10.94 | Jupiter vs Earth radius (11.21) | Q1-Q12 KOI Table |
| ps | Kepler-303 c | rhostar_transit_vs_MR | 60.4799 | 5.5265 | 10.94 | Jupiter vs Earth radius (11.21) | Q1-Q17 DR24 KOI Table |
| ps | Kepler-303 c | st_dens_vs_MR | 60.484 | 5.5265 | 10.94 | Jupiter vs Earth radius (11.21) | Q1-Q17 DR24 KOI Table |
| ps | Kepler-303 c | rhostar_transit_vs_MR | 60.4799 | 5.5265 | 10.94 | Jupiter vs Earth radius (11.21) | Q1-Q16 KOI Table |
| ps | Kepler-303 c | st_dens_vs_MR | 60.484 | 5.5265 | 10.94 | Jupiter vs Earth radius (11.21) | Q1-Q16 KOI Table |
| ps | Kepler-381 c | st_dens_vs_MR | 1.78056 | 0.16124 | 11.04 | Jupiter vs Earth radius (11.21) | Q1-Q17 DR25 KOI Table |

## Strongest flags in default rows whose planet and star parameters share one reference (first 60)

| planet | check | observed | predicted | ratio | z | reference |
|---|---|---|---|---|---|---|
| TIC 172900988 b | kepler3_a | 0.90281 | 0.720376 | 1.253 | 864.10 | Kostov et al. 2021 |
| ZTF J1828+2308 b | rhostar_transit_vs_MR | 0.887323 | 382537 | 2.32e-06 | -277.11 | Parsons et al. 2025 |
| ZTF J1230-2655 b | rhostar_transit_vs_MR | 0.932138 | 489412 | 1.905e-06 | -215.57 | Parsons et al. 2025 |
| Kepler-34 b | kepler3_a | 1.0896 | 0.868608 | 1.254 | 173.14 | Welsh et al. 2012 |
| Kepler-35 b | kepler3_a | 0.60347 | 0.486297 | 1.241 | 82.29 | Welsh et al. 2012 |
| TOI-2049 b | depth_vs_k2 | 0.2275 | 222.01 | 0.001025 |  | Guenther et al. 2026 |
| TOI-2049 b | rp_over_rstar | 1.49 | 0.0476885 | 31.24 | 52.41 | Guenther et al. 2026 |
| Kepler-1647 b | kepler3_a | 2.7205 | 2.23991 | 1.215 | 48.63 | Kostov et al. 2016 |
| Kepler-1979 b | depth_vs_k2 | 0.07589 | 8.20009 | 0.009255 |  | Q1-Q17 DR25 KOI Table |
| HAT-P-25 b | depth_vs_k2 | 0.0161 | 1.61036 | 0.009998 |  | Wang et al. 2018 |
| WD 1856+534 b | depth_vs_k2 | 56.65 | 5299.84 | 0.01069 |  | Vanderburg et al. 2020 |
| Kepler-1984 b | depth_vs_k2 | 0.03148 | 2.20739 | 0.01426 |  | Q1-Q17 DR25 KOI Table |
| PH1 b | rhostar_transit_vs_MR | 0.0107356 | 0.413175 | 0.02598 |  | Schwamb et al. 2013 |
| TOI-262 b | kepler3_a | 0.163 | 0.0947297 | 1.721 | 33.49 | Oddo et al. 2023 |
| Kepler-297 d | depth_vs_k2 | 0.43197 | 11.079 | 0.03899 |  | Q1-Q17 DR25 KOI Table |
| Kepler-419 c | st_dens_vs_MR | 13.34 | 0.371984 | 35.86 | 26.93 | Dawson et al. 2014 |
| Kepler-419 b | st_dens_vs_MR | 13.34 | 0.371984 | 35.86 | 26.93 | Dawson et al. 2014 |
| TOI-908 b | insolation | 80.884 | 549.672 | 0.1471 | -26.35 | Hawthorn et al. 2023 |
| K2-174 b | a_over_rstar | 26.6 | 40.0799 | 0.6637 | -25.45 | Livingston et al. 2019 |
| TOI-5624 c | depth_vs_k2 | 0.762 | 0.076176 | 10 |  | Bonfanti et al. 2026 |
| K2-174 b | rhostar_transit_vs_MR | 0.930342 | 3.19459 | 0.2912 | -22.73 | Livingston et al. 2019 |
| TOI-1478 b | depth_vs_k2 | 0.10936 | 1.0404 | 0.1051 |  | Rice et al. 2022 |
| Kepler-413 b | kepler3_a | 0.3553 | 0.299975 | 1.184 | 21.26 | Kostov et al. 2014 |
| Kepler-896 c | a_over_rstar | 6.444 | 47.9872 | 0.1343 |  | Q1-Q17 DR25 KOI Table |
| TOI-4602.01 | depth_vs_k2 | 0.006 | 0.0433889 | 0.1383 |  | Di Maio et al. 2026 |
| K2-285 e | rhostar_transit_vs_MR | 10.4826 | 2.40055 | 4.367 | 19.55 | Palle et al. 2019 |
| K2-285 e | kepler3_a | 0.18041 | 0.110682 | 1.63 | 19.31 | Palle et al. 2019 |
| Kepler-1984 b | a_over_rstar | 1.971 | 12.1851 | 0.1618 |  | Q1-Q17 DR25 KOI Table |
| G 9-40 b | st_dens_vs_MR | 1.62 | 15.0199 | 0.1079 | -17.83 | Luque et al. 2022 |
| Kepler-1979 b | a_over_rstar | 5.88 | 31.7046 | 0.1855 |  | Q1-Q17 DR25 KOI Table |
| Kepler-47 b | kepler3_a | 0.2877 | 0.259877 | 1.107 | 15.57 | Orosz et al. 2019 |
| HD 48948 d | insolation | 2.46 | 0.771777 | 3.187 | 15.57 | Dalal et al. 2024 |
| Kepler-47 c | kepler3_a | 0.9638 | 0.870467 | 1.107 | 15.49 | Orosz et al. 2019 |
| HD 48948 b | insolation | 138.85 | 43.4835 | 3.193 | 15.47 | Dalal et al. 2024 |
| HD 48948 c | insolation | 15.5 | 4.8563 | 3.192 | 15.41 | Dalal et al. 2024 |
| HD 10442 b | logg_vs_MR | 1548.82 | 7134.92 | 0.2171 |  | Luhn et al. 2019 |
| Kepler-975 c | depth_vs_k2 | 0.07483 | 0.344733 | 0.2171 |  | Q1-Q17 DR25 KOI Table |
| Kepler-47 d | kepler3_a | 0.6992 | 0.631502 | 1.107 | 15.22 | Orosz et al. 2019 |
| GJ 3929 b | rp_over_rstar | 0.0156 | 0.0312282 | 0.4995 | -13.37 | Beard et al. 2022 |
| TOI-1855 b | depth_vs_k2 | 0.707 | 2.6244 | 0.2694 |  | Schulte et al. 2024 |
| PH1 b | a_over_rstar | 22.1435 | 80.854 | 0.2739 |  | Schwamb et al. 2013 |
| TOI-2193 A b | bulk_density | 0.06 | 0.210945 | 0.2844 |  | Yee et al. 2022 |
| K2-349 b | rhostar_transit_vs_MR | 1.85221 | 6.47088 | 0.2862 |  | de Leon et al. 2021 |
| OGLE2-TR-L9 b | kepler3_a | 0.0308 | 0.0413274 | 0.7453 | -12.30 | Snellen et al. 2009 |
| Kepler-1999 b | a_over_rstar | 7.43 | 24.4137 | 0.3043 |  | Q1-Q17 DR25 KOI Table |
| Kepler-896 c | st_dens_vs_MR | 0.0058 | 2.38787 | 0.002429 | -11.37 | Q1-Q17 DR25 KOI Table |
| K2-285 d | kepler3_a | 0.1178 | 0.0879427 | 1.34 | 11.12 | Palle et al. 2019 |
| K2-285 d | rhostar_transit_vs_MR | 5.77683 | 2.40055 | 2.406 | 11.11 | Palle et al. 2019 |
| TOI-128.01 | insolation | 182.406 | 545.068 | 0.3346 |  | Hord et al. 2024 |
| KELT-2 A b | logg_vs_MR | 31622.8 | 11334.6 | 2.79 |  | Stassun et al. 2017 |
| Kepler-1518 c | a_over_rstar | 5.25 | 14.4687 | 0.3629 |  | Q1-Q17 DR25 KOI Table |
| Kepler-2001 c | rhostar_transit_vs_MR | 0.973906 | 2.66808 | 0.365 |  | Q1-Q17 DR25 KOI Table |
| Kepler-2001 c | st_dens_vs_MR | 0.97395 | 2.66808 | 0.365 |  | Q1-Q17 DR25 KOI Table |
| Kepler-896 c | rhostar_transit_vs_MR | 0.00579986 | 2.38787 | 0.002429 | -9.92 | Q1-Q17 DR25 KOI Table |
| TOI-2578 b | logg_vs_MR | 29716.7 | 12945.4 | 2.296 | 9.70 | Guenther et al. 2026 |
| HD 6860 b | logg_vs_MR | 3.47536 | 9.14475 | 0.38 |  | Lee et al. 2023 |
| TOI-3862 b | rhostar_transit_vs_MR | 5.40183 | 1.62943 | 3.315 | 9.41 | Carleo et al. 2026 |
| TOI-3862 b | a_over_rstar | 8.848 | 5.93442 | 1.491 | 9.40 | Carleo et al. 2026 |
| HATS-62 b | bulk_density | 0.076 | 0.189695 | 0.4006 |  | Hartman et al. 2019 |
| Kepler-1988 b | a_over_rstar | 5.08 | 12.4834 | 0.4069 |  | Q1-Q17 DR25 KOI Table |
