# dv-alias 0.1.0

Run 2026-10-17T01:56Z. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0.

8054 DR25 KOI-TCE rows; 246 with a whole-number period ratio (137 TCE longer, 109 KOI longer). A verdict points at rows worth a light-curve check; it is not a period correction.

## Counts (kind | verdict | disposition)

- koi_long|koi_long|CANDIDATE: 4
- koi_long|koi_long|CONFIRMED: 3
- koi_long|koi_long|FALSE POSITIVE: 102
- tce_long|no_alias_secondary|CANDIDATE: 1
- tce_long|no_alias_secondary|CONFIRMED: 1
- tce_long|no_alias_secondary|FALSE POSITIVE: 18
- tce_long|secondary_at_alias|CANDIDATE: 15
- tce_long|secondary_at_alias|CONFIRMED: 2
- tce_long|secondary_at_alias|FALSE POSITIVE: 100

## TCE at k x the KOI period, strongest secondary not at an alias phase

| kepoi_name | kepler_name | koi_disposition | k | koi_period | tce_period | tce_depth_ppm | sec_mes | sec_phase | offset_d | verdict | dr24_sec_phase | dr24_verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| K00263.01 |  | FALSE POSITIVE | 2 | 20.719 | 41.438 | 202.560 | 8.444 | 0.273 | 9.426 | no_alias_secondary |  |  |
| K00324.01 |  | FALSE POSITIVE | 2 | 1.089 | 2.178 | 94.659 | 7.070 | 0.570 | 0.153 | no_alias_secondary | 0.558 | no_alias_secondary |
| K01013.01 |  | FALSE POSITIVE | 2 | 0.519 | 1.037 | 305.676 | 1.180 | 0.591 | 0.094 | no_alias_secondary | 0.868 | no_alias_secondary |
| K01091.01 |  | FALSE POSITIVE | 2 | 15.238 | 30.477 | 47087.585 | 848.781 | 0.368 | 4.023 | no_alias_secondary |  |  |
| K01093.01 |  | FALSE POSITIVE | 2 | 0.529 | 1.057 | 75.194 | 5.137 | 0.382 | 0.124 | no_alias_secondary | 0.391 | no_alias_secondary |
| K01181.01 |  | FALSE POSITIVE | 2 | 0.652 | 1.304 | 378.070 | 10.406 | 0.748 | 0.323 | no_alias_secondary |  |  |
| K01324.01 |  | FALSE POSITIVE | 2 | 0.522 | 1.044 | 433.484 | 5.211 | 0.589 | 0.093 | no_alias_secondary | 0.431 | no_alias_secondary |
| K01811.01 |  | FALSE POSITIVE | 2 | 2.464 | 4.927 | 1884.202 | 52.576 | 0.548 | 0.239 | no_alias_secondary | 0.548 | no_alias_secondary |
| K02174.03 | Kepler-1802 b | CONFIRMED | 2 | 7.725 | 15.450 | 738.660 | 2.669 | 0.903 | 6.225 | no_alias_secondary | 0.903 | no_alias_secondary |
| K03714.01 |  | FALSE POSITIVE | 2 | 0.875 | 1.751 | 3527.427 | 18.107 | 0.564 | 0.113 | no_alias_secondary |  |  |
| K04077.01 |  | FALSE POSITIVE | 2 | 0.786 | 1.573 | 9192.747 | 4.446 | 0.307 | 0.303 | no_alias_secondary |  |  |
| K04417.01 |  | FALSE POSITIVE | 2 | 0.438 | 0.876 | 89.325 | 1.544 | 0.246 | 0.223 | no_alias_secondary | 0.246 | no_alias_secondary |
| K04893.01 |  | CANDIDATE | 2 | 6.588 | 13.175 | 415.519 | 2.747 | 0.650 | 1.975 | no_alias_secondary | 0.651 | no_alias_secondary |
| K04909.01 |  | FALSE POSITIVE | 2 | 1.653 | 3.306 | 225.060 | 2.586 | 0.681 | 0.600 | no_alias_secondary | 0.725 | no_alias_secondary |
| K04910.01 |  | FALSE POSITIVE | 2 | 3.375 | 6.750 | 85.158 | 3.218 | 0.656 | 1.050 | no_alias_secondary | 0.852 | no_alias_secondary |
| K06084.01 |  | FALSE POSITIVE | 2 | 3.269 | 6.538 | 58909.331 | 854.724 | 0.521 | 0.136 | no_alias_secondary |  |  |
| K06710.01 |  | FALSE POSITIVE | 2 | 0.777 | 1.554 | 20572.384 | 2172.606 | 0.751 | 0.389 | no_alias_secondary |  |  |
| K06909.01 |  | FALSE POSITIVE | 2 | 0.758 | 1.517 | 35037.063 | 15.795 | 0.750 | 0.379 | no_alias_secondary |  |  |
| K06999.01 |  | FALSE POSITIVE | 2 | 0.449 | 0.899 | 418205.499 | 73.584 | 0.656 | 0.140 | no_alias_secondary |  |  |
| K07190.01 |  | FALSE POSITIVE | 2 | 1.123 | 2.245 | 8.563 | 7.345 | 0.678 | 0.400 | no_alias_secondary |  |  |

## Every confirmed planet with a whole-number KOI/TCE period ratio

| kepoi_name | kepler_name | koi_disposition | k | koi_period | tce_period | tce_depth_ppm | sec_mes | sec_phase | offset_d | verdict | dr24_sec_phase | dr24_verdict | oedp_stat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| K00179.02 | Kepler-458 b | CONFIRMED | 2 | 572.377 | 286.187 | 1263.393 | 4.601 |  |  | koi_long |  |  | 0.000 |
| K00490.02 | Kepler-167 e | CONFIRMED | 2 | 1071.233 | 535.616 | 19018.995 | 4.307 |  |  | koi_long |  |  | 0.000 |
| K02643.01 | Kepler-1301 b | CONFIRMED | 2 | 9.082 | 4.541 | 235.074 | 2.733 |  |  | koi_long |  |  | 0.751 |
| K02174.03 | Kepler-1802 b | CONFIRMED | 2 | 7.725 | 15.450 | 738.660 | 2.669 | 0.903 | 6.225 | no_alias_secondary | 0.903 | no_alias_secondary | 0.609 |
| K00961.02 | Kepler-42 c | CONFIRMED | 2 | 0.453 | 0.907 | 294.396 | 9.714 | 0.504 | 0.003 | secondary_at_alias |  |  | 0.000 |
| K04441.01 | Kepler-1604 b | CONFIRMED | 2 | 0.342 | 0.684 | 134.709 | 13.591 | 0.503 | 0.002 | secondary_at_alias | 0.485 | secondary_at_alias | 0.001 |
