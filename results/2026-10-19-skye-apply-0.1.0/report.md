# skye_apply 0.1.0

Run 2026-10-19T07:25Z. By MV2 of Munim, Inc.; made with AI agents. Pre-registered in findings/2026-10-19-skye-apply-prereg.md. Code Apache-2.0, results CC BY 4.0. A Skye failure marks transits that coincide with clustered artefacts; it is a lead, not a disposition.

Status: done.

Gate: {"prereg_live": true, "code_matches": true}

OBS reproduction of skye_diag 0.1.0: True (run_variant tp 3829, fp 1364, fn 446, tn 8313; via frozen bins tp 3829, fp 1364, fn 446, tn 8313). Valid cadences: 128918. Light-curve error: none.

## KOI groups (frozen variant)

| group | KOIs | with a flagged kept event | fraction | eligible (>= 3 kept) | would fail | fraction |
|---|---|---|---|---|---|---|
| dr25_pc | 668 | 311 | 0.4656 | 668 | 4 | 0.006 |
| dr25_skye | 109 | 101 | 0.9266 | 109 | 65 | 0.5963 |
| never_dr25 | 425 | 66 | 0.1553 | 414 | 19 | 0.0459 |

Checks: koi_rows = 2257, koi_with_skygroup = 2257, events_match = 2257, valid_cadences = 128918, robnik_rows = 431, robnik_listed_names = 0, cumulative_sha256_ok = True

Tests: a1_reproduced = True, a2_data = True, a3_named_fail = False, a4_census = True, a4_p = 0.000842, a5_pc_fail_fraction = True, a6_dr25_skye_flagged = True, robnik_data = False, q1_enough_fails = False, q2_enrichment = False, q3_window_direction = False

Named: {"K05269.01": {"skygroup": 66, "n_events": 3, "n_kept": 3, "n_flagged": 0, "good": 3, "would_fail": 0, "v3_would_fail": 1, "flagged_times": "", "kept_times": "631.6306 1003.1369 1374.6432"}, "K05227.01": {"skygroup": 66, "n_events": 3, "n_kept": 3, "n_flagged": 0, "good": 3, "would_fail": 0, "v3_would_fail": 1, "flagged_times": "", "kept_times": "631.4140 1002.9789 1374.5439"}}

Changed vs v3: {"dr25_pc": {"v3_fail_now_pass": 3, "v3_pass_now_fail": 0}, "dr25_skye": {"v3_fail_now_pass": 3, "v3_pass_now_fail": 18}, "never_dr25": {"v3_fail_now_pass": 4, "v3_pass_now_fail": 1}}

## Robnik et al. 2026 cross-check (amended)

| comparison | n_fail | fail_listed | n_pass | pass_listed | p_one_sided |
|---|---|---|---|---|---|
| main | 20 | 0 | 620 | 0 | 1.0 |
| window_340_400 | 6 | 0 | 77 | 0 | 1.0 |
| in_dr25_only | 4 | 0 | 271 | 0 | 1.0 |

## Leads: candidates DR25 never scored that the frozen variant would fail

| KOI | period | skygroup | kept | flagged | good | flagged times (BKJD) |
|---|---|---|---|---|---|---|
| K00682.01 | 562.1725914 | 58 | 3 | 1 | 2 | 185.9685 |
| K04426.01 | 369.13236 | 58 | 4 | 4 | 0 | 235.5195 604.6519 973.7842 1342.9166 |
| K05291.01 | 525.560452 | 66 | 3 | 1 | 2 | 1491.4546 |
| K05228.01 | 546.53309 | 66 | 3 | 1 | 2 | 880.5916 |
| K05237.01 | 380.39474 | 66 | 3 | 1 | 2 | 882.6279 |
| K05649.01 | 426.942225 | 22 | 3 | 1 | 2 | 912.3239 |
| K05408.01 | 415.748785 | 60 | 3 | 1 | 2 | 1341.5972 |
| K05423.01 | 366.55705 | 58 | 3 | 2 | 1 | 604.6972 971.2543 |
| K05434.01 | 581.87357 | 58 | 3 | 1 | 2 | 971.7397 |
| K05570.01 | 574.65297 | 42 | 3 | 2 | 1 | 939.9476 1514.6005 |
| K05578.01 | 388.048463 | 28 | 3 | 2 | 1 | 683.8838 1459.9807 |
| K05467.01 | 502.8356901 | 58 | 3 | 2 | 1 | 234.1811 737.0167 |
| K05618.01 | 318.49078 | 55 | 3 | 1 | 2 | 485.4950 |
| K05380.01 | 369.93355 | 62 | 3 | 1 | 2 | 915.1491 |
| K05385.01 | 331.70918 | 60 | 3 | 1 | 2 | 644.3245 |
| K05398.01 | 551.22396 | 58 | 3 | 3 | 0 | 185.7811 737.0051 1288.2290 |
| K05973.01 | 419.93373 | 4 | 3 | 1 | 2 | 1231.7988 |
| K07136.01 | 441.17369 | 43 | 3 | 1 | 2 | 1256.3566 |
| K07592.01 | 381.97977 | 42 | 3 | 2 | 1 | 545.1603 1309.1198 |
