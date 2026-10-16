# kepler-coverage 0.1.0

Run 2026-10-16T19:21Z. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0. A flag means Kepler's own data coverage cannot exclude that alias of the period; it is not a claim that the catalogued period is wrong. P/k: none of the extra epochs of P/k has data; kP: every epoch with data has the same epoch number mod k.

- reference_kepid: 8105398
- reference_quarters: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
- reference_segments: 187
- stars_with_quarters: 6923
- koi_rows: 8054
- kois_without_quarters: 0
- census_rows: 4094
- koi_ephemeris_rows: 4089
- archive_ephemeris_rows: 5
- flagged_rows: 10
- flagged_confirmed: 3
- flagged_candidate: 7
- by_flag: {'one_epoch': {'CONFIRMED': 0, 'CANDIDATE': 2}, 'P/3': {'CONFIRMED': 2, 'CANDIDATE': 0}, '3P': {'CONFIRMED': 1, 'CANDIDATE': 3}, 'P/2': {'CONFIRMED': 1, 'CANDIDATE': 1}, '2P': {'CONFIRMED': 0, 'CANDIDATE': 1}}
- lightcurve_checked: 14
- lightcurve_agree: 11
- lightcurve_disagree: 3
- lightcurve_error: 0
- controls: {'K05568.01 archive': {'flags': 'P/2;P/3', 'lc_flags': 'P/2;P/3'}, 'K05568.01 koi': {'flags': '3P', 'lc_flags': '3P'}, 'K02174.03 koi': {'flags': '', 'lc_flags': ''}, 'K02174.03 archive': {'flags': '', 'lc_flags': ''}, 'K05475.01 koi': {'flags': '', 'lc_flags': ''}, 'K05475.01 archive': {'flags': '', 'lc_flags': ''}}

## Light-curve checks (flagged confirmed planets and candidates first, then controls)

| KOI | planet | disposition | ephemeris | P (ref) | quarters | epochs with data | flags (quarters) | flags (light curve) | agree |
|---|---|---|---|---|---|---|---|---|---|
| K03975.01 | Kepler-1536 b | CONFIRMED | koi | 364.751562 (Q1-Q17 DR25 KOI Table) | 10101010101010101 | 0 1 2 3 | P/3 | P/3 | yes |
| K05568.01 | Kepler-1633 b | CONFIRMED | archive | 186.404271 (Morton et al. 2016) | 01010101010101010 | 1 2 3 4 5 6 7 | P/2;P/3 | P/2;P/3 | yes |
| K05568.01 | Kepler-1633 b | CONFIRMED | koi | 62.134919 (Q1-Q17 DR25 KOI Table) | 01010101010101010 | 4 7 10 13 16 19 22 | 3P | 3P | yes |
| K07880.01 |  | CANDIDATE | koi | 623.70774 (Q1-Q17 DR25 KOI Table) | 11111111111111111 | 0 2 | 2P | 2P | yes |
| K08046.01 |  | CANDIDATE | koi | 384.37706 (Q1-Q17 DR25 KOI Table) | 11100110011001000 | 0 1 2 | P/2 | P/2 | yes |
| K07930.01 |  | CANDIDATE | koi | 377.67241 (Q1-Q17 DR25 KOI Table) | 11111111111111111 | 0 3 | one_epoch | 3P | no |
| K00238.03 |  | CANDIDATE | koi | 362.97828 (Q1-Q17 DR25 KOI Table) | 11111111111111111 | 0 1 2 3 | one_epoch |  | no |
| K08033.01 |  | CANDIDATE | koi | 362.13187 (Q1-Q17 DR25 KOI Table) | 11111111111111111 | 0 3 | 3P | 3P | yes |
| K08109.01 |  | CANDIDATE | koi | 218.771117 (Q1-Q17 DR25 KOI Table) | 11110111011101110 | 2 3 5 | 3P |  | no |
| K08280.01 |  | CANDIDATE | koi | 66.67305 (Q1-Q17 DR25 KOI Table) | 00000000001010000 | 13 16 | 3P | 3P | yes |
| K02174.03 | Kepler-1802 b | CONFIRMED | koi | 7.72513619 (Q1-Q17 DR25 KOI Table) | 01111111111111111 | 0..183 (172) |  |  | yes |
| K02174.03 | Kepler-1802 b | CONFIRMED | archive | 15.45020008 (Valizadegan et al. 2022) | 01111111111111111 | 0..90 (87) |  |  | yes |
| K05475.01 | Kepler-1632 b | CONFIRMED | koi | 224.150923 (Q1-Q17 DR25 KOI Table) | 11111111111111111 | 0 1 2 3 4 5 |  |  | yes |
| K05475.01 | Kepler-1632 b | CONFIRMED | archive | 448.303558 (Morton et al. 2016) | 11111111111111111 | 0 1 2 |  |  | yes |

## All flagged rows (first 300)

| KOI | planet | disposition | ephemeris | P (ref) | quarters | epochs with data | P/k extra epochs with data | flags |
|---|---|---|---|---|---|---|---|---|
| K03975.01 | Kepler-1536 b | CONFIRMED | koi | 364.751562 (Q1-Q17 DR25 KOI Table) | 10101010101010101 | 0 1 2 3 | 2:4;3:0;4:4;5:7 | P/3 |
| K05568.01 | Kepler-1633 b | CONFIRMED | archive | 186.404271 (Morton et al. 2016) | 01010101010101010 | 0 1 2 3 4 5 6 7 | 2:0;3:0;4:6;5:8 | P/2;P/3 |
| K05568.01 | Kepler-1633 b | CONFIRMED | koi | 62.134919 (Q1-Q17 DR25 KOI Table) | 01010101010101010 | 1 4 7 10 13 16 19 22 | 2:13;3:17;4:32;5:37 | 3P |
| K07880.01 |  | CANDIDATE | koi | 623.70774 (Q1-Q17 DR25 KOI Table) | 11111111111111111 | 0 2 | 2:2;3:3;4:7;5:7 | 2P |
| K08046.01 |  | CANDIDATE | koi | 384.37706 (Q1-Q17 DR25 KOI Table) | 11100110011001000 | 0 1 2 | 2:0;3:4;4:3;5:4 | P/2 |
| K07930.01 |  | CANDIDATE | koi | 377.67241 (Q1-Q17 DR25 KOI Table) | 11111111111111111 | 3 | 2:4;3:5;4:9;5:15 | one_epoch |
| K00238.03 |  | CANDIDATE | koi | 362.97828 (Q1-Q17 DR25 KOI Table) | 11111111111111111 | 1 | 2:3;3:9;4:9;5:15 | one_epoch |
| K08033.01 |  | CANDIDATE | koi | 362.13187 (Q1-Q17 DR25 KOI Table) | 11111111111111111 | 0 3 | 2:3;3:8;4:11;5:12 | 3P |
| K08109.01 |  | CANDIDATE | koi | 218.771117 (Q1-Q17 DR25 KOI Table) | 11110111011101110 | 2 5 | 2:6;3:8;4:14;5:18 | 3P |
| K08280.01 |  | CANDIDATE | koi | 66.67305 (Q1-Q17 DR25 KOI Table) | 00000000001010000 | 13 16 | 2:3;3:7;4:7;5:11 | 3P |
