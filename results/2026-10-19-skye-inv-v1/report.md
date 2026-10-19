# skye_inv 0.1.0

Run 2026-10-19T02:04Z. By MV2 of Munim, Inc.; made with AI agents. Held-out test pre-registered in findings/2026-10-18-skye-inv-prereg.md. Code Apache-2.0, results CC BY 4.0. Skye flags are signs of clustered artefacts, not dispositions.

Status: done.

Gate: {"prereg_live": true, "code_matches": true}

OBS re-run of the chosen variant reproduces skye_diag 0.1.0: True (tp 3829, fp 1364, fn 446, tn 8313). Valid cadences: 128918. Light-curve error: none.

## INV against DR25's iflag3 (SKYE), P > 45 d

| variant | tp | fp | fn | tn | recall | precision | f1 | tces_compared | bad_bins | bin_events |
|---|---|---|---|---|---|---|---|---|---|---|
| chosen | 3270 | 987 | 367 | 3849 | 0.8991 | 0.7681 | 0.8285 | 8473 | 2251 | 60660 |
| scored_only | 3298 | 1047 | 339 | 3789 | 0.9068 | 0.759 | 0.8264 | 8473 | 2321 | 62894 |
| all_tces | 3298 | 1047 | 339 | 3789 | 0.9068 | 0.759 | 0.8264 | 8473 | 2321 | 62894 |

Data checks: inv_rows = 19531, inv_long_rows = 8473, inv_long_stars = 5169, stars_looked_up = 3256, mast_errors = 0, stars_with_skygroup = 5169, rv_rows = 19536, rv_names = ['Data_Set', 'TCE_ID', 'KIC', 'pn', 'n_plan', 'ntrans', 'nrealt', 'ngoodt', 'iflag0', 'iflag1', 'iflag2', 'iflag3', 'iflag4', 'iflag5'], rv_names_ok = True, rv_found = 8473, rv_skye_flag_1_all_periods = 12935, comment_skye_tces = 4816, comment_skye_with_flag_1 = 4816, valid_cadences = 128918

Robovetter: loaded.

Tests: p2_data = True, p3_tce_recall = True, p4_tce_precision = True, p5_f1_gain = True

## Chosen variant split by event count against DR25's nrealtrans

| events vs nrealtrans | n | tp | fp | fn | tn | recall | precision |
|---|---|---|---|---|---|---|---|
| more | 2937 | 866 | 779 | 84 | 1208 | 0.9116 | 0.5264 |
| equal | 5105 | 2198 | 187 | 239 | 2481 | 0.9019 | 0.9216 |
| fewer | 431 | 206 | 21 | 44 | 160 | 0.824 | 0.9075 |
