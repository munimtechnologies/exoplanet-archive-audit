# skye_diag 0.1.0

Run 2026-10-18T22:50Z. By MV2 of Munim, Inc.; made with AI agents. Exploratory diagnosis of skye-census-v3 on data already seen; not a validated result. Code Apache-2.0, results CC BY 4.0.

Reproduced v3's confusion counts: True. TCEs: 15349 (not in the Robovetter input: 1397). Valid cadences: 128918. Light-curve error: none.

| variant | tp | fp | fn | tn | recall | precision | bad_bins | bin_events | events_equal_nitrans | events_equal_nrealtrans |
|---|---|---|---|---|---|---|---|---|---|---|
| v3 | 3382 | 1621 | 893 | 8056 | 0.7911 | 0.676 | 1908 | 108011 | 0.8258 | 0.5814 |
| scored_only | 3792 | 1401 | 483 | 8276 | 0.887 | 0.7302 | 1913 | 99507 | 0.8258 | 0.5814 |
| real_events_w0.1 | 3700 | 1799 | 575 | 7878 | 0.8655 | 0.6728 | 2150 | 103265 | 0.6545 | 0.6365 |
| scored_only_real_events_w0.1 | 3832 | 1623 | 443 | 8054 | 0.8964 | 0.7025 | 2067 | 95118 | 0.6545 | 0.6365 |
| scored_only_real_events_w0.1_data_bins | 3822 | 1411 | 453 | 8266 | 0.894 | 0.7304 | 1932 | 95118 | 0.6545 | 0.6365 |
| real_events_w0.25 | 3639 | 1778 | 636 | 7899 | 0.8512 | 0.6718 | 2080 | 104192 | 0.6833 | 0.6441 |
| scored_only_real_events_w0.25 | 3839 | 1573 | 436 | 8104 | 0.898 | 0.7093 | 2049 | 95965 | 0.6833 | 0.6441 |
| scored_only_real_events_w0.25_data_bins | 3829 | 1364 | 446 | 8313 | 0.8957 | 0.7373 | 1926 | 95965 | 0.6833 | 0.6441 |
| real_events_w0.5 | 3632 | 1738 | 643 | 7939 | 0.8496 | 0.6764 | 2058 | 105331 | 0.7203 | 0.6379 |
| scored_only_real_events_w0.5 | 3854 | 1543 | 421 | 8134 | 0.9015 | 0.7141 | 2046 | 97014 | 0.7203 | 0.6379 |
| scored_only_real_events_w0.5_data_bins | 3791 | 1382 | 484 | 8295 | 0.8868 | 0.7328 | 1932 | 97014 | 0.7203 | 0.6379 |

## v3 split by event count against DR25's nrealtrans

| events vs nrealtrans | n | tp | fp | fn | tn | recall | precision |
|---|---|---|---|---|---|---|---|
| more | 5564 | 1146 | 1202 | 310 | 2906 | 0.7871 | 0.4881 |
| equal | 8111 | 2130 | 397 | 566 | 5018 | 0.7901 | 0.8429 |
| fewer | 277 | 106 | 22 | 17 | 132 | 0.8618 | 0.8281 |
