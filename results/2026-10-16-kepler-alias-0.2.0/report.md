# kepler-alias 0.2.0

Run 2026-10-16T16:01Z. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0. A verdict is a candidate to check by eye, not a published correction. short_period_real also fits an eclipsing binary at the long period with two equal eclipses.

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
- tested: 8
- verdicts: {'long_period_real': 3, 'short_period_real': 3, 'inconclusive': 2, 'error': 0}
- check_kepler_1802_b: {'verdict': 'long_period_real', 'groups': 'g0: n=77 depth=649.2+-54.7 ppm snr=11.9; g1: n=74 depth=-66.6+-48.7 ppm snr=-1.4', 'error': ''}

## Light-curve tests

| census | KOI | planet | k | longer | P short | P long | Archive P (ref) | Archive P is | a / Kepler a | verdict | groups | first half | second half |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tce | K02174.03 | Kepler-1802 b | 2 | tce_long | 7.72513619 | 15.4502 | 15.45020008 (Valizadegan et al. 2022) | long | 0.6298 | long_period_real | g0: n=77 depth=649.2+-54.7 ppm snr=11.9; g1: n=74 depth=-66.6+-48.7 ppm snr=-1.4 | g0: n=40 depth=677.3+-80.6 ppm snr=8.4; g1: n=35 depth=0.6+-70.0 ppm snr=0.0 | g0: n=37 depth=624.4+-75.1 ppm snr=8.3; g1: n=39 depth=-129.7+-71.5 ppm snr=-1.8 |
| tce | K00179.02 | Kepler-458 b | 2 | koi_long | 286.187 | 572.376632 |  () |  |  | long_period_real | g0: n=2 depth=1601.8+-32.2 ppm snr=49.8; g1: n=1 depth=-64.4+-33.6 ppm snr=-1.9 | g0: n=1 depth=1569.5+-31.5 ppm snr=49.8; g1: n=0 depth=+- ppm snr= | g0: n=1 depth=1633.9+-31.4 ppm snr=52.0; g1: n=1 depth=-64.4+-33.6 ppm snr=-1.9 |
| tce | K00490.02 | Kepler-167 e | 2 | koi_long | 535.616 | 1071.232624 | 1071.23205 (Chachan et al. 2022) | long | 0.9996 | long_period_real | g0: n=2 depth=17354.7+-243.4 ppm snr=71.3; g1: n=1 depth=-92.9+-65.6 ppm snr=-1.4 | g0: n=1 depth=17126.8+-48.4 ppm snr=353.9; g1: n=0 depth=+- ppm snr= | g0: n=1 depth=17614.7+-51.7 ppm snr=340.7; g1: n=1 depth=-92.9+-65.6 ppm snr=-1.4 |
| tce | K00961.02 | Kepler-42 c | 2 | tce_long | 0.453287416 | 0.906561 | 0.45328509 (Muirhead et al. 2012) | short | 1.0256 | inconclusive | g0: n=0 depth=+- ppm snr=; g1: n=0 depth=+- ppm snr= | g0: n=0 depth=+- ppm snr=; g1: n=0 depth=+- ppm snr= | g0: n=0 depth=+- ppm snr=; g1: n=0 depth=+- ppm snr= |
| tce | K02643.01 | Kepler-1301 b | 2 | koi_long | 4.54116 | 9.08233411 | 9.08237046 (Morton et al. 2016) | long | 1.0099 | short_period_real | g0: n=142 depth=198.6+-23.2 ppm snr=8.6; g1: n=146 depth=265.1+-20.0 ppm snr=13.2 | g0: n=72 depth=199.1+-32.2 ppm snr=6.2; g1: n=72 depth=277.9+-28.9 ppm snr=9.6 | g0: n=70 depth=198.3+-33.6 ppm snr=5.9; g1: n=74 depth=253.4+-27.7 ppm snr=9.1 |
| tce | K04441.01 | Kepler-1604 b | 2 | tce_long | 0.341842017 | 0.683677 | 0.683684256 (Morton et al. 2016) | long | 0.9931 | short_period_real | g0: n=1113 depth=242.0+-6.6 ppm snr=36.9; g1: n=1081 depth=228.3+-6.7 ppm snr=34.1 | g0: n=555 depth=248.1+-9.0 ppm snr=27.5; g1: n=542 depth=227.4+-9.6 ppm snr=23.7 | g0: n=558 depth=235.9+-9.5 ppm snr=24.7; g1: n=539 depth=229.3+-9.4 ppm snr=24.4 |
| archive | K05475.01 | Kepler-1632 b | 2 | archive_long | 224.150923 | 448.303558 | 448.303558 (Morton et al. 2016) | long | 0.568 | short_period_real | g0: n=3 depth=325.6+-17.8 ppm snr=18.3; g1: n=3 depth=394.4+-44.3 ppm snr=8.9 | g0: n=2 depth=314.2+-22.6 ppm snr=13.9; g1: n=1 depth=400.3+-40.1 ppm snr=10.0 | g0: n=1 depth=344.2+-28.8 ppm snr=11.9; g1: n=2 depth=392.9+-70.4 ppm snr=5.6 |
| archive | K05568.01 | Kepler-1633 b | 3 | archive_long | 62.134919 | 186.404271 | 186.404271 (Morton et al. 2016) | long | 0.571 | inconclusive | g0: n=0 depth=+- ppm snr=; g1: n=7 depth=149.0+-27.5 ppm snr=5.4; g2: n=0 depth=+- ppm snr= | g0: n=0 depth=+- ppm snr=; g1: n=3 depth=112.6+-48.5 ppm snr=2.3; g2: n=0 depth=+- ppm snr= | g0: n=0 depth=+- ppm snr=; g1: n=4 depth=175.8+-30.2 ppm snr=5.8; g2: n=0 depth=+- ppm snr= |

## Archive census: composite period k times the DR25 KOI period, or 1/k

| KOI | planet | disposition | k | longer | KOI P | Archive P (ref) | a / Kepler a |
|---|---|---|---|---|---|---|---|
| K02174.03 | Kepler-1802 b | CONFIRMED | 2 | archive_long | 7.72513619 | 15.45020008 (Valizadegan et al. 2022) | 0.6298 |
| K04441.01 | Kepler-1604 b | CONFIRMED | 2 | archive_long | 0.341842017 | 0.683684256 (Morton et al. 2016) | 0.9931 |
| K05475.01 | Kepler-1632 b | CONFIRMED | 2 | archive_long | 224.150923 | 448.303558 (Morton et al. 2016) | 0.568 |
| K05568.01 | Kepler-1633 b | CONFIRMED | 3 | archive_long | 62.134919 | 186.404271 (Morton et al. 2016) | 0.571 |

## Confirmed planets in the TCE census (first 100)

| KOI | planet | k | longer | TCE P | KOI P | depth ratio | hint | Archive P (ref) | a / Kepler a |
|---|---|---|---|---|---|---|---|---|---|
| K02174.03 | Kepler-1802 b | 2 | tce_long | 15.4502 | 7.72513619 | 1.9328 | long | 15.45020008 (Valizadegan et al. 2022) | 0.6298 |
| K00179.02 | Kepler-458 b | 2 | koi_long | 286.187 | 572.376632 | 1.3804 | short |  () |  |
| K00490.02 | Kepler-167 e | 2 | koi_long | 535.616 | 1071.232624 | 1.0013 | short | 1071.23205 (Chachan et al. 2022) | 0.9996 |
| K00961.02 | Kepler-42 c | 2 | tce_long | 0.906561 | 0.453287416 | 0.2014 | short | 0.45328509 (Muirhead et al. 2012) | 1.0256 |
| K02643.01 | Kepler-1301 b | 2 | koi_long | 4.54116 | 9.08233411 | 1.2629 | short | 9.08237046 (Morton et al. 2016) | 1.0099 |
| K04441.01 | Kepler-1604 b | 2 | tce_long | 0.683677 | 0.341842017 | 0.4716 | short | 0.683684256 (Morton et al. 2016) | 0.9931 |
