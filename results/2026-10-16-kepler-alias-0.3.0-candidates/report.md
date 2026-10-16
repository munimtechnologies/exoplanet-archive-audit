# kepler-alias 0.3.0

Run 2026-10-16T19:19Z. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0. A verdict is a candidate to check by eye, not a published correction. short_period_real also fits an eclipsing binary at the long period with two equal eclipses.

- dispositions: ['CANDIDATE']
- joined_rows: 8054
- koi_rows: 8054
- composite_rows: 6451
- alias_pairs: 246
- tce_long: 137
- koi_long: 109
- confirmed_alias_pairs: 6
- confirmed_depth_hint_long: 1
- confirmed_archive_long: 4
- confirmed_archive_short: 1
- archive_alias_pairs: 4
- archive_alias_archive_long: 4
- impossible_count_pairs: 85
- tested: 18
- verdicts: {'long_period_real': 3, 'short_period_real': 9, 'inconclusive': 6, 'error': 0}
- check_kepler_1802_b: None

## Light-curve tests

| census | KOI | planet | disposition | k | longer | P short | P long | depth ratio (hint) | odd-even | transits / max | Archive P (ref) | verdict | groups | first half | second half |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tce | K00521.02 |  | CANDIDATE | 2 | koi_long | 5.41038 | 10.8206034 | 0.9741 (short) | 0.3783 | 239 / 135 IMPOSSIBLE |  () | short_period_real | g0: n=101 depth=115.5+-20.4 ppm snr=5.7; g1: n=104 depth=123.6+-18.8 ppm snr=6.6 | g0: n=50 depth=127.1+-33.2 ppm snr=3.8; g1: n=52 depth=118.4+-26.4 ppm snr=4.5 | g0: n=51 depth=105.3+-24.9 ppm snr=4.2; g1: n=52 depth=128.7+-26.9 ppm snr=4.8 |
| tce | K02093.03 |  | CANDIDATE | 2 | tce_long | 0.496069986 | 0.992144 | 0.9146 (short) | 0.03239 | 940 / 2943 |  () | short_period_real | g0: n=874 depth=125.2+-9.8 ppm snr=12.7; g1: n=888 depth=118.9+-10.0 ppm snr=11.9 | g0: n=441 depth=119.1+-13.5 ppm snr=8.8; g1: n=440 depth=130.9+-13.5 ppm snr=9.7 | g0: n=433 depth=131.7+-14.3 ppm snr=9.2; g1: n=448 depth=106.8+-14.6 ppm snr=7.3 |
| tce | K02732.04 |  | CANDIDATE | 2 | tce_long | 24.5607107 | 49.1213 | 1.096 (short) | 0.3975 | 26 / 60 |  () | inconclusive | g0: n=29 depth=62.1+-6.3 ppm snr=9.9; g1: n=22 depth=43.3+-8.8 ppm snr=4.9 | g0: n=13 depth=72.5+-9.3 ppm snr=7.8; g1: n=12 depth=42.9+-9.5 ppm snr=4.5 | g0: n=16 depth=53.5+-8.5 ppm snr=6.3; g1: n=10 depth=43.8+-18.2 ppm snr=2.4 |
| tce | K02796.01 |  | CANDIDATE | 2 | tce_long | 0.5374094 | 1.07479 | 0.7368 (short) | 0.05928 | 1246 / 2716 |  () | short_period_real | g0: n=760 depth=84.5+-7.4 ppm snr=11.4; g1: n=763 depth=84.7+-7.3 ppm snr=11.6 | g0: n=380 depth=101.1+-10.7 ppm snr=9.5; g1: n=381 depth=83.1+-10.4 ppm snr=8.0 | g0: n=380 depth=68.2+-10.2 ppm snr=6.7; g1: n=382 depth=86.2+-10.3 ppm snr=8.4 |
| tce | K02874.01 |  | CANDIDATE | 2 | tce_long | 0.352515897 | 0.705028 | 0.9096 (short) | 0.006922 | 1899 / 4141 |  () | short_period_real | g0: n=787 depth=131.9+-8.1 ppm snr=16.2; g1: n=780 depth=146.3+-8.4 ppm snr=17.3 | g0: n=396 depth=131.2+-11.4 ppm snr=11.5; g1: n=387 depth=140.2+-12.0 ppm snr=11.6 | g0: n=391 depth=132.6+-11.6 ppm snr=11.5; g1: n=393 depth=152.4+-11.9 ppm snr=12.9 |
| tce | K03318.02 |  | CANDIDATE | 2 | tce_long | 25.6970688 | 51.3955 | 1.2563 (short) | 0.6772 | 14 / 57 |  () | inconclusive | g0: n=14 depth=1033.4+-152.2 ppm snr=6.8; g1: n=15 depth=570.7+-182.8 ppm snr=3.1 | g0: n=6 depth=1191.7+-179.1 ppm snr=6.7; g1: n=8 depth=581.4+-269.8 ppm snr=2.2 | g0: n=8 depth=897.9+-234.8 ppm snr=3.8; g1: n=7 depth=555.9+-261.4 ppm snr=2.1 |
| tce | K03980.01 |  | CANDIDATE | 2 | tce_long | 0.469334634 | 0.938662 | 0.7479 (short) | 2.491e-05 | 1425 / 3110 |  () | short_period_real | g0: n=301 depth=232.5+-15.6 ppm snr=14.9; g1: n=301 depth=231.6+-15.0 ppm snr=15.5 | g0: n=154 depth=225.3+-21.7 ppm snr=10.4; g1: n=147 depth=230.3+-21.5 ppm snr=10.7 | g0: n=147 depth=240.0+-22.4 ppm snr=10.7; g1: n=154 depth=233.0+-21.0 ppm snr=11.1 |
| tce | K04144.01 |  | CANDIDATE | 2 | tce_long | 0.487656278 | 0.97531 | 1.0082 (short) | 1.161e-22 | 1371 / 2993 |  () | short_period_real | g0: n=516 depth=94.6+-9.0 ppm snr=10.5; g1: n=517 depth=100.6+-8.6 ppm snr=11.7 | g0: n=260 depth=95.4+-13.1 ppm snr=7.3; g1: n=256 depth=104.1+-12.0 ppm snr=8.7 | g0: n=256 depth=93.7+-12.4 ppm snr=7.6; g1: n=261 depth=97.3+-12.3 ppm snr=7.9 |
| tce | K04216.01 |  | CANDIDATE | 2 | tce_long | 0.492291661 | 0.984591 | 0.6134 (short) | 0.009707 | 843 / 2965 |  () | short_period_real | g0: n=201 depth=749.9+-34.8 ppm snr=21.6; g1: n=205 depth=670.1+-37.9 ppm snr=17.7 | g0: n=102 depth=767.8+-48.5 ppm snr=15.8; g1: n=101 depth=700.0+-52.7 ppm snr=13.3 | g0: n=99 depth=731.3+-50.0 ppm snr=14.6; g1: n=104 depth=640.4+-54.5 ppm snr=11.8 |
| tce | K04419.01 |  | CANDIDATE | 2 | tce_long | 0.259819659 | 0.519638 | 0.9827 (short) | 1.79e-25 | 2180 / 5618 |  () | inconclusive | g0: n=0 depth=+- ppm snr=; g1: n=0 depth=+- ppm snr= | g0: n=0 depth=+- ppm snr=; g1: n=0 depth=+- ppm snr= | g0: n=0 depth=+- ppm snr=; g1: n=0 depth=+- ppm snr= |
| tce | K04668.01 |  | CANDIDATE | 2 | koi_long | 7.53639 | 15.07277287 | 1.3264 (short) | 40.35 | 176 / 97 IMPOSSIBLE |  () | inconclusive | g0: n=4 depth=104.5+-78.4 ppm snr=1.3; g1: n=3 depth=413.0+-109.3 ppm snr=3.8 | g0: n=1 depth=33.4+-151.8 ppm snr=0.2; g1: n=2 depth=458.4+-80.1 ppm snr=5.7 | g0: n=3 depth=130.3+-98.5 ppm snr=1.3; g1: n=1 depth=13.4+-233.8 ppm snr=0.1 |
| tce | K04685.01 |  | CANDIDATE | 2 | tce_long | 0.494247662 | 0.988485 | 0.8244 (short) | 1.008e-18 | 872 / 2953 |  () | short_period_real | g0: n=542 depth=254.2+-21.8 ppm snr=11.6; g1: n=562 depth=189.1+-21.4 ppm snr=8.8 | g0: n=273 depth=252.4+-31.3 ppm snr=8.1; g1: n=279 depth=161.2+-31.0 ppm snr=5.2 | g0: n=269 depth=255.9+-30.5 ppm snr=8.4; g1: n=283 depth=217.0+-29.6 ppm snr=7.3 |
| tce | K04711.01 |  | CANDIDATE | 2 | tce_long | 4.3638313 | 8.72764 | 1.4204 (short) | 0.01057 | 152 / 335 |  () | long_period_real | g0: n=125 depth=68.6+-28.5 ppm snr=2.4; g1: n=134 depth=267.4+-30.0 ppm snr=8.9 | g0: n=63 depth=114.6+-40.3 ppm snr=2.8; g1: n=66 depth=229.7+-44.4 ppm snr=5.2 | g0: n=62 depth=23.2+-40.6 ppm snr=0.6; g1: n=68 depth=301.7+-40.5 ppm snr=7.5 |
| tce | K04844.01 |  | CANDIDATE | 3 | tce_long | 0.428046051 | 1.28413 | 0.9143 (short) | 0.01197 | 1045 / 3410 |  () | inconclusive | g0: n=88 depth=80.7+-36.1 ppm snr=2.2; g1: n=84 depth=95.3+-37.6 ppm snr=2.5; g2: n=89 depth=133.8+-42.5 ppm snr=3.1 | g0: n=45 depth=166.5+-51.8 ppm snr=3.2; g1: n=40 depth=43.8+-52.9 ppm snr=0.8; g2: n=45 depth=171.8+-60.2 ppm snr=2.9 | g0: n=43 depth=-6.4+-50.7 ppm snr=-0.1; g1: n=44 depth=148.0+-53.4 ppm snr=2.8; g2: n=44 depth=89.0+-60.1 ppm snr=1.5 |
| tce | K04893.01 |  | CANDIDATE | 2 | tce_long | 6.58753699 | 13.1751 | 1.7902 (long) | 1.941 | 104 / 222 |  () | long_period_real | g0: n=91 depth=314.2+-47.0 ppm snr=6.7; g1: n=92 depth=22.1+-43.1 ppm snr=0.5 | g0: n=47 depth=349.7+-64.1 ppm snr=5.5; g1: n=44 depth=65.7+-62.2 ppm snr=1.1 | g0: n=44 depth=272.2+-69.4 ppm snr=3.9; g1: n=48 depth=-16.3+-59.7 ppm snr=-0.3 |
| tce | K06798.01 |  | CANDIDATE | 2 | koi_long | 1.32093 | 2.64185268 | 3.0044 (long) | 0.1451 | 1006 / 553 IMPOSSIBLE |  () | long_period_real | g0: n=451 depth=153.8+-27.6 ppm snr=5.6; g1: n=457 depth=17.9+-27.7 ppm snr=0.6 | g0: n=228 depth=107.1+-39.3 ppm snr=2.7; g1: n=226 depth=18.9+-39.6 ppm snr=0.5 | g0: n=223 depth=205.2+-38.3 ppm snr=5.4; g1: n=231 depth=17.0+-38.8 ppm snr=0.4 |
| tce | K07157.01 |  | CANDIDATE | 2 | tce_long | 23.9830523 | 47.9669 | 0.8629 (short) | 0.1625 | 29 / 61 |  () | inconclusive | g0: n=24 depth=85.5+-22.9 ppm snr=3.7; g1: n=26 depth=91.1+-15.6 ppm snr=5.8 | g0: n=13 depth=38.2+-22.8 ppm snr=1.7; g1: n=12 depth=83.9+-19.7 ppm snr=4.3 | g0: n=11 depth=157.7+-35.3 ppm snr=4.5; g1: n=14 depth=98.6+-24.6 ppm snr=4.0 |
| tce | K07859.01 |  | CANDIDATE | 2 | tce_long | 0.306702491 | 0.613402 | 0.8062 (short) | 0.01524 | 1851 / 4759 |  () | short_period_real | g0: n=418 depth=102.5+-14.8 ppm snr=6.9; g1: n=433 depth=96.5+-15.0 ppm snr=6.4 | g0: n=205 depth=96.2+-21.5 ppm snr=4.5; g1: n=220 depth=70.8+-21.4 ppm snr=3.3 | g0: n=213 depth=108.0+-20.5 ppm snr=5.3; g1: n=213 depth=121.4+-21.1 ppm snr=5.8 |

## Archive census: composite period k times the DR25 KOI period, or 1/k

| KOI | planet | disposition | k | longer | KOI P | Archive P (ref) | a / Kepler a |
|---|---|---|---|---|---|---|---|
| K02174.03 | Kepler-1802 b | CONFIRMED | 2 | archive_long | 7.72513619 | 15.45020008 (Valizadegan et al. 2022) | 0.6298 |
| K04441.01 | Kepler-1604 b | CONFIRMED | 2 | archive_long | 0.341842017 | 0.683684256 (Morton et al. 2016) | 0.9931 |
| K05475.01 | Kepler-1632 b | CONFIRMED | 2 | archive_long | 224.150923 | 448.303558 (Morton et al. 2016) | 0.568 |
| K05568.01 | Kepler-1633 b | CONFIRMED | 3 | archive_long | 62.134919 | 186.404271 (Morton et al. 2016) | 0.571 |

## TCE census rows whose transit count the KOI period cannot allow

| KOI | planet | disposition | k | TCE P | KOI P | transits | max at KOI P | odd-even |
|---|---|---|---|---|---|---|---|---|
| K00179.02 | Kepler-458 b | CONFIRMED | 2 | 286.187 | 572.376632 | 4 | 3 | 0.0 |
| K00490.02 | Kepler-167 e | CONFIRMED | 2 | 535.616 | 1071.232624 | 3 | 2 | 6.001e-19 |
| K02643.01 | Kepler-1301 b | CONFIRMED | 2 | 4.54116 | 9.08233411 | 298 | 161 | 0.7513 |
| K00028.01 |  | FALSE POSITIVE | 2 | 2.05043 | 4.100870416 | 654 | 356 | 0.0 |
| K00088.01 |  | FALSE POSITIVE | 2 | 2.58984 | 5.17968868 | 520 | 282 | 1.092 |
| K00272.01 |  | FALSE POSITIVE | 2 | 0.64066 | 1.28132831 | 1670 | 1140 | 0.009489 |
| K00422.01 |  | FALSE POSITIVE | 2 | 404.506 | 809.0141881 | 4 | 2 | 0.0 |
| K00521.02 |  | CANDIDATE | 2 | 5.41038 | 10.8206034 | 239 | 135 | 0.3783 |
| K00798.01 |  | FALSE POSITIVE | 2 | 1.67092 | 3.341913228 | 780 | 437 | 117.2 |
| K01077.01 |  | FALSE POSITIVE | 2 | 0.551983 | 1.103971357 | 2053 | 1323 | 11.49 |
| K01126.02 |  | FALSE POSITIVE | 2 | 237.962 | 475.91706 | 5 | 4 | 3.17e-07 |
| K01132.01 |  | FALSE POSITIVE | 2 | 0.957073 | 1.914158508 | 1401 | 763 | 0.2773 |
| K01134.02 |  | FALSE POSITIVE | 2 | 100.305 | 200.61103346 | 14 | 8 | 158.2 |
| K01136.01 |  | FALSE POSITIVE | 2 | 0.817459 | 1.63484631 | 1647 | 893 | 1.196 |
| K01284.01 |  | FALSE POSITIVE | 2 | 1.55854 | 3.117087797 | 861 | 469 | 88320.0 |
| K01351.01 |  | FALSE POSITIVE | 2 | 5.36293 | 10.72396374 | 206 | 137 | 150.5 |
| K01463.01 |  | FALSE POSITIVE | 2 | 532.134 | 1064.2680956 | 3 | 2 | 0.0 |
| K01652.01 |  | FALSE POSITIVE | 2 | 0.54187 | 1.083736642 | 1969 | 1347 | 0.0 |
| K01778.01 |  | FALSE POSITIVE | 2 | 0.75975 | 1.519529227 | 1499 | 961 | 0.0 |
| K02301.01 |  | FALSE POSITIVE | 2 | 1.75645 | 3.51289168 | 765 | 416 | 74.13 |
| K02360.01 |  | FALSE POSITIVE | 2 | 1.15181 | 2.30367952 | 1168 | 634 | 0.02062 |
| K02425.01 |  | FALSE POSITIVE | 2 | 1.75643 | 3.51295674 | 765 | 416 | 39.69 |
| K02645.01 |  | FALSE POSITIVE | 2 | 0.85288 | 1.705782214 | 1560 | 856 | 1.435 |
| K02870.01 |  | FALSE POSITIVE | 2 | 2.81487 | 5.62950902 | 405 | 260 | 17.96 |
| K03518.01 |  | FALSE POSITIVE | 2 | 4.46974 | 8.939461148 | 175 | 164 | 462900.0 |
| K03525.01 |  | FALSE POSITIVE | 2 | 3.14102 | 6.282033445 | 278 | 233 | 0.3961 |
| K03550.01 |  | FALSE POSITIVE | 2 | 1.07411 | 2.148219541 | 1055 | 680 | 276400.0 |
| K03603.01 |  | FALSE POSITIVE | 2 | 2.7596 | 5.519188936 | 289 | 265 | 0.0 |
| K03645.01 |  | FALSE POSITIVE | 2 | 2.22772 | 4.45543346 | 353 | 328 | 0.0 |
| K03656.01 |  | FALSE POSITIVE | 2 | 1.50776 | 3.01551943 | 521 | 484 | 12470.0 |
| K03658.01 |  | FALSE POSITIVE | 2 | 1.1262 | 2.252417903 | 1007 | 648 | 11180.0 |
| K03785.01 |  | FALSE POSITIVE | 2 | 3.14098 | 6.2820426 | 350 | 233 | 0.0 |
| K03874.01 |  | FALSE POSITIVE | 2 | 0.733274 | 1.466535757 | 1825 | 996 | 0.8368 |
| K03912.01 |  | FALSE POSITIVE | 2 | 3.88624 | 7.77241144 | 350 | 188 | 48.15 |
| K03920.01 |  | FALSE POSITIVE | 2 | 7.23493 | 14.46993942 | 186 | 101 | 44.68 |
| K03929.01 |  | FALSE POSITIVE | 2 | 60.5301 | 121.0598037 | 24 | 13 | 2.842 |
| K03932.01 |  | FALSE POSITIVE | 2 | 178.267 | 356.535835 | 7 | 5 | 0.3119 |
| K03970.01 |  | FALSE POSITIVE | 2 | 5.09327 | 10.18670759 | 265 | 144 | 5.76 |
| K04006.01 |  | FALSE POSITIVE | 2 | 6.21246 | 12.4247333 | 225 | 118 | 0.0 |
| K04229.01 |  | FALSE POSITIVE | 2 | 7.29419 | 14.5893928 | 194 | 101 | 15.31 |
| K04239.01 |  | FALSE POSITIVE | 2 | 1.08906 | 2.17815935 | 1227 | 671 | 5.294 |
| K04596.01 |  | FALSE POSITIVE | 2 | 0.530965 | 1.061937837 | 2521 | 1375 | 1.879 |
| K04668.01 |  | CANDIDATE | 2 | 7.53639 | 15.07277287 | 176 | 97 | 40.35 |
| K04681.01 |  | FALSE POSITIVE | 2 | 4.11712 | 8.2344072 | 256 | 178 | 15.65 |
| K04741.01 |  | FALSE POSITIVE | 2 | 3.57018 | 7.1403113 | 378 | 205 | 13.4 |
| K04884.01 |  | FALSE POSITIVE | 2 | 0.987543 | 1.97515457 | 1087 | 739 | 2.96 |
| K04953.01 |  | FALSE POSITIVE | 2 | 1.42945 | 2.858879267 | 939 | 511 | 35.89 |
| K04965.01 |  | FALSE POSITIVE | 2 | 10.2655 | 20.5311708 | 124 | 72 | 1.05 |
| K05059.01 |  | FALSE POSITIVE | 2 | 323.144 | 646.28789332 | 5 | 3 | 0.0 |
| K05395.01 |  | FALSE POSITIVE | 2 | 300.596 | 601.13797 | 5 | 3 | 0.3494 |
| K05962.01 |  | FALSE POSITIVE | 2 | 1.30798 | 2.61594288 | 1034 | 558 | 2.136 |
| K06082.01 |  | FALSE POSITIVE | 2 | 0.907079 | 1.814128042 | 1483 | 805 | 0.0 |
| K06257.01 |  | FALSE POSITIVE | 2 | 1.16288 | 2.32539968 | 1005 | 628 | 0.05575 |
| K06260.01 |  | FALSE POSITIVE | 2 | 2.05078 | 4.101595158 | 658 | 356 | 0.0 |
| K06306.01 |  | FALSE POSITIVE | 2 | 1.84686 | 3.693702974 | 732 | 396 | 9905.0 |
| K06317.01 |  | FALSE POSITIVE | 2 | 3.68181 | 7.363572395 | 289 | 199 | 0.0 |
| K06365.01 |  | FALSE POSITIVE | 2 | 1.17206 | 2.344138713 | 1145 | 623 | 0.01042 |
| K06385.01 |  | FALSE POSITIVE | 2 | 4.8807 | 9.761172507 | 223 | 150 | 0.0 |
| K06390.01 |  | FALSE POSITIVE | 2 | 2.59871 | 5.197420145 | 519 | 281 | 0.0 |
| K06398.01 |  | FALSE POSITIVE | 2 | 4.70121 | 9.4022333 | 224 | 156 | 0.03565 |
| K06437.01 |  | FALSE POSITIVE | 2 | 0.576927 | 1.15495063 | 1794 | 1264 | 5.578e-08 |
| K06460.01 |  | FALSE POSITIVE | 2 | 1.23513 | 2.470283788 | 875 | 591 | 0.0 |
| K06555.01 |  | FALSE POSITIVE | 2 | 1.72854 | 3.457078812 | 629 | 423 | 0.0 |
| K06567.01 |  | FALSE POSITIVE | 2 | 4.79203 | 9.58405667 | 283 | 153 | 1301.0 |
| K06588.01 |  | FALSE POSITIVE | 2 | 1.49594 | 2.991884392 | 902 | 488 | 0.0 |
| K06730.01 |  | FALSE POSITIVE | 2 | 5.38419 | 10.768391927 | 255 | 136 | 1490000.0 |
| K06743.01 |  | FALSE POSITIVE | 2 | 5.6505 | 11.300987626 | 238 | 130 | 0.0 |
| K06792.01 |  | FALSE POSITIVE | 2 | 2.11944 | 4.238855579 | 632 | 345 | 0.0 |
| K06795.01 |  | FALSE POSITIVE | 3 | 2.61369 | 7.841066931 | 515 | 187 | 0.0 |
| K06798.01 |  | CANDIDATE | 2 | 1.32093 | 2.64185268 | 1006 | 553 | 0.1451 |
| K06800.01 |  | FALSE POSITIVE | 2 | 2.53892 | 5.077746556 | 530 | 288 | 12330.0 |
| K06833.01 |  | FALSE POSITIVE | 2 | 3.5594 | 7.11879848 | 375 | 206 | 2142.0 |
| K06894.01 |  | FALSE POSITIVE | 2 | 3.18673 | 6.373454978 | 420 | 229 | 118.6 |
| K06900.01 |  | FALSE POSITIVE | 2 | 4.23386 | 8.467706136 | 318 | 173 | 14990.0 |
| K06928.01 |  | FALSE POSITIVE | 2 | 0.864602 | 1.72933255 | 1550 | 844 | 9.67 |
| K06964.01 |  | FALSE POSITIVE | 2 | 2.15295 | 4.305917719 | 622 | 339 | 0.0 |
| K06974.01 |  | FALSE POSITIVE | 2 | 3.57018 | 7.140373046 | 378 | 205 | 0.0 |
| K06997.01 |  | FALSE POSITIVE | 2 | 2.01433 | 4.028671454 | 668 | 363 | 0.0 |
| K07086.01 |  | FALSE POSITIVE | 2 | 0.563352 | 1.12679793 | 2034 | 1296 | 0.0003911 |
| K07098.01 |  | FALSE POSITIVE | 2 | 2.70173 | 5.40346248 | 500 | 271 | 0.0 |
| K07132.01 |  | FALSE POSITIVE | 2 | 4.12909 | 8.258181993 | 330 | 177 | 0.0 |
| K07186.01 |  | FALSE POSITIVE | 2 | 1.85594 | 3.71186243 | 718 | 394 | 0.3708 |
| K07193.01 |  | FALSE POSITIVE | 2 | 1.08905 | 2.17814186 | 1228 | 671 | 3.523 |
| K07482.01 |  | FALSE POSITIVE | 2 | 4.88128 | 9.762550001 | 274 | 150 | 7270.0 |
| K07601.01 |  | FALSE POSITIVE | 2 | 171.276 | 342.55315723 | 9 | 5 | 12.94 |

## Confirmed planets in the TCE census (first 100)

| KOI | planet | k | longer | TCE P | KOI P | depth ratio | hint | Archive P (ref) | a / Kepler a |
|---|---|---|---|---|---|---|---|---|---|
| K02174.03 | Kepler-1802 b | 2 | tce_long | 15.4502 | 7.72513619 | 1.9328 | long | 15.45020008 (Valizadegan et al. 2022) | 0.6298 |
| K00179.02 | Kepler-458 b | 2 | koi_long | 286.187 | 572.376632 | 1.3804 | short |  () |  |
| K00490.02 | Kepler-167 e | 2 | koi_long | 535.616 | 1071.232624 | 1.0013 | short | 1071.23205 (Chachan et al. 2022) | 0.9996 |
| K00961.02 | Kepler-42 c | 2 | tce_long | 0.906561 | 0.453287416 | 0.2014 | short | 0.45328509 (Muirhead et al. 2012) | 1.0256 |
| K02643.01 | Kepler-1301 b | 2 | koi_long | 4.54116 | 9.08233411 | 1.2629 | short | 9.08237046 (Morton et al. 2016) | 1.0099 |
| K04441.01 | Kepler-1604 b | 2 | tce_long | 0.683677 | 0.341842017 | 0.4716 | short | 0.683684256 (Morton et al. 2016) | 0.9931 |
