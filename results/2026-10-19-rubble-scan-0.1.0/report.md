# scan_rubble 0.1.0 report (exploratory, no hypothesis)

Status: done.

Checks: {"rv_rows_ok": true, "rv_sha256_ok": true, "controls_ok": true, "dev_size_ok": true}

Development stars: 60; TCEs: 125; scored: 125; iflag0 among scored: 66; Rubble-only among scored: 17.

Real events vs nrealt (TCEs): {"init": {"exact": 45, "within1": 59, "over": 27, "under": 39}, "white": {"exact": 31, "within1": 41, "over": 73, "under": 11}, "pdc": {"exact": 45, "within1": 62, "over": 40, "under": 23}, "resid": {"exact": 0, "within1": 0, "over": 0, "under": 125}}

| variant | tp | fp | fn | tn | Rubble-only exact / n |
|---|---|---|---|---|---|
| init_1_0.25 | 32 | 16 | 34 | 43 | 0 / 17 |
| init_1_0.5 | 49 | 23 | 17 | 36 | 2 / 17 |
| init_1_0.75 | 61 | 30 | 5 | 29 | 1 / 17 |
| init_2_0.25 | 14 | 3 | 52 | 56 | 0 / 17 |
| init_2_0.5 | 54 | 23 | 12 | 36 | 4 / 17 |
| init_2_0.75 | 66 | 28 | 0 | 31 | 4 / 17 |
| white_1_0.25 | 16 | 13 | 50 | 46 | 0 / 17 |
| white_1_0.5 | 21 | 17 | 45 | 42 | 0 / 17 |
| white_1_0.75 | 33 | 23 | 33 | 36 | 0 / 17 |
| white_2_0.25 | 5 | 3 | 61 | 56 | 0 / 17 |
| white_2_0.5 | 23 | 17 | 43 | 42 | 0 / 17 |
| white_2_0.75 | 29 | 22 | 37 | 37 | 0 / 17 |
| pdc_1_0.25 | 19 | 16 | 47 | 43 | 0 / 17 |
| pdc_1_0.5 | 29 | 23 | 37 | 36 | 0 / 17 |
| pdc_1_0.75 | 38 | 30 | 28 | 29 | 0 / 17 |
| pdc_2_0.25 | 4 | 2 | 62 | 57 | 0 / 17 |
| pdc_2_0.5 | 30 | 22 | 36 | 37 | 0 / 17 |
| pdc_2_0.75 | 36 | 28 | 30 | 31 | 0 / 17 |
| resid_1_0.25 | 66 | 59 | 0 | 0 | 3 / 17 |
| resid_1_0.5 | 66 | 59 | 0 | 0 | 3 / 17 |
| resid_1_0.75 | 66 | 59 | 0 | 0 | 3 / 17 |
| resid_2_0.25 | 66 | 59 | 0 | 0 | 3 / 17 |
| resid_2_0.5 | 66 | 59 | 0 | 0 | 3 / 17 |
| resid_2_0.75 | 66 | 59 | 0 | 0 | 3 / 17 |

Details: variants.json (also split by pn), tces.csv, events.csv, sample.json. Made with AI agents; MV2, Munim, Inc., mv2@munimtech.com.
