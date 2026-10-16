# kepler-alias 0.1.0

Run 2026-10-16T12:41Z. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0. A verdict is a candidate to check by eye, not a published correction.

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
- tested: 6
- verdicts: {'long_period_real': 3, 'short_period_real': 2, 'inconclusive': 1, 'error': 0}
- check_kepler_1802_b: {'verdict': 'long_period_real', 'groups': 'g0: n=77 depth=649.2+-54.7 ppm snr=11.9; g1: n=74 depth=-66.6+-48.7 ppm snr=-1.4', 'error': ''}

## Light-curve tests

| KOI | planet | k | longer | P short | P long | depth ratio | Archive P is | a / Kepler a | verdict | groups |
|---|---|---|---|---|---|---|---|---|---|---|
| K02174.03 | Kepler-1802 b | 2 | tce_long | 7.72513619 | 15.4502 | 1.9328 | long | 0.6298 | long_period_real | g0: n=77 depth=649.2+-54.7 ppm snr=11.9; g1: n=74 depth=-66.6+-48.7 ppm snr=-1.4 |
| K00179.02 | Kepler-458 b | 2 | koi_long | 286.187 | 572.376632 | 1.3804 |  |  | long_period_real | g0: n=2 depth=1601.8+-32.2 ppm snr=49.8; g1: n=1 depth=-64.4+-33.6 ppm snr=-1.9 |
| K00490.02 | Kepler-167 e | 2 | koi_long | 535.616 | 1071.232624 | 1.0013 | long | 0.9996 | long_period_real | g0: n=2 depth=17354.7+-243.4 ppm snr=71.3; g1: n=1 depth=-92.9+-65.6 ppm snr=-1.4 |
| K00961.02 | Kepler-42 c | 2 | tce_long | 0.453287416 | 0.906561 | 0.2014 | short | 1.0256 | inconclusive | g0: n=0 depth=+- ppm snr=; g1: n=0 depth=+- ppm snr= |
| K02643.01 | Kepler-1301 b | 2 | koi_long | 4.54116 | 9.08233411 | 1.2629 | long | 1.0099 | short_period_real | g0: n=142 depth=198.6+-23.2 ppm snr=8.6; g1: n=146 depth=265.1+-20.0 ppm snr=13.2 |
| K04441.01 | Kepler-1604 b | 2 | tce_long | 0.341842017 | 0.683677 | 0.4716 | long | 0.9931 | short_period_real | g0: n=1113 depth=242.0+-6.6 ppm snr=36.9; g1: n=1081 depth=228.3+-6.7 ppm snr=34.1 |

## Confirmed planets in the census (first 100)

| KOI | planet | k | longer | TCE P | KOI P | depth ratio | hint | Archive P (ref) | a / Kepler a |
|---|---|---|---|---|---|---|---|---|---|
| K02174.03 | Kepler-1802 b | 2 | tce_long | 15.4502 | 7.72513619 | 1.9328 | long | 15.45020008 (Valizadegan et al. 2022) | 0.6298 |
| K00179.02 | Kepler-458 b | 2 | koi_long | 286.187 | 572.376632 | 1.3804 | short |  () |  |
| K00490.02 | Kepler-167 e | 2 | koi_long | 535.616 | 1071.232624 | 1.0013 | short | 1071.23205 (Chachan et al. 2022) | 0.9996 |
| K00961.02 | Kepler-42 c | 2 | tce_long | 0.906561 | 0.453287416 | 0.2014 | short | 0.45328509 (Muirhead et al. 2012) | 1.0256 |
| K02643.01 | Kepler-1301 b | 2 | koi_long | 4.54116 | 9.08233411 | 1.2629 | short | 9.08237046 (Morton et al. 2016) | 1.0099 |
| K04441.01 | Kepler-1604 b | 2 | tce_long | 0.683677 | 0.341842017 | 0.4716 | short | 0.683684256 (Morton et al. 2016) | 0.9931 |
