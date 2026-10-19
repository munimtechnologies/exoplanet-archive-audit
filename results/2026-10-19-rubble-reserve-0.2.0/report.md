# scan_rubble 0.2.0 report (reserve mode)

Status: done.

Gate: {"ok": true, "reasons": [], "published_sample": "/out/gate/sample_published.json", "gate_note": "/out/gate/prereg_note.md"}

Checks: {"rv_rows_ok": true, "rv_sha256_ok": true, "controls_ok": true, "sample_size_ok": true, "no_dev_star_scanned": true}

Stars scanned: 200; TCEs: 361; scored: 361; iflag0 among scored: 133; Rubble-only among scored: 29.

## Pre-registered decisions

P1 (empty MODEL_WHITE iff half-hour duration): **holds**. Table a/b/c/d = 18/0/0/343, skipped 0; n = 361, half-hour = 18, off-diagonal = 0.
P2 (init_2_0.75 recall >= 0.9 and precision <= 0.8): **holds**. tp/fp/fn/tn = 133/125/0/103; recall_ok = True, precision_ok = True.

Real events vs nrealt (TCEs): {"init": {"exact": 167, "within1": 210, "over": 41, "under": 110}, "white": {"exact": 102, "within1": 132, "over": 208, "under": 21}, "pdc": {"exact": 148, "within1": 200, "over": 94, "under": 67}, "resid": {"exact": 0, "within1": 0, "over": 0, "under": 361}}

| variant | tp | fp | fn | tn | Rubble-only exact / n |
|---|---|---|---|---|---|
| init_1_0.25 | 82 | 67 | 51 | 161 | 6 / 29 |
| init_1_0.5 | 111 | 103 | 22 | 125 | 9 / 29 |
| init_1_0.75 | 124 | 126 | 9 | 102 | 10 / 29 |
| init_2_0.25 | 21 | 6 | 112 | 222 | 1 / 29 |
| init_2_0.5 | 116 | 98 | 17 | 130 | 8 / 29 |
| init_2_0.75 | 133 | 125 | 0 | 103 | 7 / 29 |
| white_1_0.25 | 36 | 54 | 97 | 174 | 0 / 29 |
| white_1_0.5 | 52 | 68 | 81 | 160 | 1 / 29 |
| white_1_0.75 | 61 | 91 | 72 | 137 | 1 / 29 |
| white_2_0.25 | 6 | 12 | 127 | 216 | 0 / 29 |
| white_2_0.5 | 53 | 65 | 80 | 163 | 0 / 29 |
| white_2_0.75 | 68 | 90 | 65 | 138 | 1 / 29 |
| pdc_1_0.25 | 51 | 64 | 82 | 164 | 1 / 29 |
| pdc_1_0.5 | 69 | 98 | 64 | 130 | 1 / 29 |
| pdc_1_0.75 | 81 | 123 | 52 | 105 | 1 / 29 |
| pdc_2_0.25 | 5 | 5 | 128 | 223 | 0 / 29 |
| pdc_2_0.5 | 71 | 91 | 62 | 137 | 1 / 29 |
| pdc_2_0.75 | 82 | 118 | 51 | 110 | 1 / 29 |
| resid_1_0.25 | 133 | 228 | 0 | 0 | 5 / 29 |
| resid_1_0.5 | 133 | 228 | 0 | 0 | 5 / 29 |
| resid_1_0.75 | 133 | 228 | 0 | 0 | 5 / 29 |
| resid_2_0.25 | 133 | 228 | 0 | 0 | 5 / 29 |
| resid_2_0.5 | 133 | 228 | 0 | 0 | 5 / 29 |
| resid_2_0.75 | 133 | 228 | 0 | 0 | 5 / 29 |

Details: variants.json (also split by pn), tces.csv, events.csv, sample.json, reserve.json. Made with AI agents; MV2, Munim, Inc., mv2@munimtech.com.
