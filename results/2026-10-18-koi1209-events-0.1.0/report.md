# event-check 0.1.0: KIC 3534076

Run 2026-10-18T08:25Z. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0. A verdict is a lead to check by eye, not a published correction.

- points: 53097; quarters: 17; span: [131.5128, 1591.0017]; duration used: 3.1 h
- reference (first anchor): {'depth_ppm': 5171.0, 'err_ppm': 229.3, 'snr': 22.55, 'n_in': 3, 'n_out': 20}
- anchors: [{'time': 378.137, 'event': {'depth_ppm': 5171.0, 'err_ppm': 229.3, 'snr': 22.55, 'n_in': 3, 'n_out': 20}, 'best_centre': 378.167}, {'time': 650.224, 'event': {'depth_ppm': 4372.7, 'err_ppm': 166.5, 'snr': 26.27, 'n_in': 5, 'n_out': 25}, 'best_centre': 650.234}]
- two-transit period from best centres: 272.067

## Hypotheses

| hypothesis | verdict |
|---|---|
| Q1-Q16 | excluded |
| DR25-TCE | excluded |
| Lissauer2024 | excluded |

| hypothesis | n | time | core pts | depth (ppm) | S/N | status | best centre | best S/N |
|---|---|---|---|---|---|---|---|---|
| Q1-Q16 | 0 | 378.1372 | 3 | 5171.0 +- 229.3 | 22.55 | deep | 378.167 | 25.45 |
| Q1-Q16 | 1 | 650.224 | 4 | 4393.6 +- 183.0 | 24.01 | deep | 650.234 | 26.39 |
| Q1-Q16 | 2 | 922.3109 | 4 | -1395.6 +- 853.3 | -1.64 | absent | 922.501 | 21.24 |
| Q1-Q16 | 3 | 1194.3977 | 3 |  +-  |  | no_data |  |  |
| Q1-Q16 | 4 | 1466.4846 | 4 | 5186.9 +- 211.0 | 24.58 | deep | 1466.475 | 31.96 |
| DR25-TCE | 0 | 378.141 | 4 | 4908.6 +- 202.9 | 24.2 | deep | 378.161 | 25.36 |
| DR25-TCE | 1 | 786.556 | 3 | 94.3 +- 296.3 | 0.32 | absent | 786.876 | 2.44 |
| DR25-TCE | 2 | 1194.971 | 2 | 5348.4 +- 248.5 | 21.52 | deep | 1194.991 | 22.87 |
| Lissauer2024 | 0 | 378.1372 | 3 | 5171.0 +- 229.3 | 22.55 | deep | 378.167 | 25.45 |
| Lissauer2024 | 1 | 650.2235 | 5 | 4372.7 +- 166.5 | 26.27 | deep | 650.223 | 26.27 |
| Lissauer2024 | 2 | 922.3098 | 4 | -1395.6 +- 853.3 | -1.64 | absent | 922.5 | 20.77 |
| Lissauer2024 | 3 | 1194.396 | 3 |  +-  |  | no_data |  |  |
| Lissauer2024 | 4 | 1466.4823 | 4 | 5164.1 +- 209.0 | 24.71 | deep | 1466.472 | 29.27 |

## Two-transit aliases (statuses per epoch: d deep, a absent, n no data, u unclear)

| n | P (d) | verdict | epochs |
|---|---|---|---|
| 1 | 272.087 | excluded | ddand |
| 2 | 136.0435 | excluded | adadaaanad |
| 3 | 90.6957 | excluded | aadnadanaaanaada |
| 4 | 68.0218 | excluded | aaadnaadaanaaannaaada |
| 5 | 54.4174 | excluded | aaandanaadaannaaaaanaaaadaa |
| 6 | 45.3478 | excluded | aaaaadanaaadaaannaaaaaanaaaaadaa |
| 7 | 38.8696 | excluded | anaaaadaaaaaadanannaaaaaananaaaaaadaan |
| 8 | 34.0109 | excluded | aaaaaaadannaaaadaanannaaaaaaannnnanaaaadaaa |
| 9 | 30.2319 | excluded | anaaaaaadaanaaaaadaaaaanaaaaaaaaaannnaaaaaandaaaa |
| 10 | 27.2087 | excluded | aaaaaaanndaannaaaaadaanaananaaaanaaaaaannaaaaaaaadaaaa |
| 11 | 24.7352 | excluded | anaanaaaadaaanaaaaaadaanaaaanaaaaaanannaaannannaaaanadaaaaa |
| 12 | 22.6739 | excluded | aaaaaaaaaadnannaaaaaaadaaaanannnnaaaaaaaaaanaanaaaaaaaaaaadaaaaa |

## Blind search (robust S/N scale 1.054)

| rank | time | depth (ppm) | S/N | robust S/N |
|---|---|---|---|---|
| 1 | 1466.463 | 4816.8 +- 172.5 | 27.93 | 26.51 |
| 2 | 650.213 | 4753.6 +- 181.1 | 26.26 | 24.92 |
| 3 | 378.163 | 4908.9 +- 196.6 | 24.96 | 23.7 |
| 4 | 1194.963 | 5348.4 +- 248.5 | 21.52 | 20.43 |
| 5 | 922.513 | 4622.3 +- 225.6 | 20.49 | 19.44 |
| 6 | 463.513 | 450.9 +- 77.4 | 5.82 | 5.53 |
| 7 | 1131.263 | 719.7 +- 147.1 | 4.89 | 4.64 |
| 8 | 411.313 | 630.2 +- 131.3 | 4.8 | 4.55 |
| 9 | 1548.513 | 751.4 +- 160.8 | 4.67 | 4.43 |
| 10 | 539.663 | 857.7 +- 191.2 | 4.49 | 4.26 |
| 11 | 278.513 | 710.1 +- 167.6 | 4.24 | 4.02 |
| 12 | 798.213 | 773.3 +- 184.1 | 4.2 | 3.99 |
| 13 | 866.713 | 1065.3 +- 272.8 | 3.9 | 3.71 |
| 14 | 587.013 | 797.6 +- 206.3 | 3.87 | 3.67 |
| 15 | 1174.213 | 605.9 +- 159.4 | 3.8 | 3.61 |
| 16 | 611.263 | 793.4 +- 209.8 | 3.78 | 3.59 |
| 17 | 975.363 | 889.2 +- 235.7 | 3.77 | 3.58 |
| 18 | 1086.913 | 546.5 +- 147.3 | 3.71 | 3.52 |
| 19 | 568.063 | 872.1 +- 235.1 | 3.71 | 3.52 |
| 20 | 1432.713 | 531.3 +- 144.6 | 3.67 | 3.49 |
| 21 | 1346.463 | 715.9 +- 195.7 | 3.66 | 3.47 |
| 22 | 630.513 | 528.6 +- 145.7 | 3.63 | 3.44 |
| 23 | 572.413 | 589.0 +- 162.4 | 3.63 | 3.44 |
| 24 | 1587.113 | 652.3 +- 180.1 | 3.62 | 3.44 |
| 25 | 341.613 | 472.6 +- 131.5 | 3.59 | 3.41 |

## Coverage

| file | quarter | points | first | last |
|---|---|---|---|---|
| kplr003534076-2009166043257_llc.fits | 1 | 1389 | 131.5128 | 164.9843 |
| kplr003534076-2009259160929_llc.fits | 2 | 3772 | 169.7659 | 258.4676 |
| kplr003534076-2009350155506_llc.fits | 3 | 3730 | 260.2453 | 349.4952 |
| kplr003534076-2010078095331_llc.fits | 4 | 3587 | 352.4579 | 442.2029 |
| kplr003534076-2010174085026_llc.fits | 5 | 2569 | 444.0216 | 537.6319 |
| kplr003534076-2010265121752_llc.fits | 6 | 4028 | 539.471 | 629.2966 |
| kplr003534076-2010355172524_llc.fits | 7 | 3745 | 630.1956 | 719.5477 |
| kplr003534076-2011073133259_llc.fits | 8 | 2699 | 735.4037 | 802.3447 |
| kplr003534076-2011177032512_llc.fits | 9 | 2468 | 808.5567 | 905.927 |
| kplr003534076-2011271113734_llc.fits | 10 | 3994 | 906.867 | 1000.2686 |
| kplr003534076-2012004120508_llc.fits | 11 | 3752 | 1001.2289 | 1098.3251 |
| kplr003534076-2012088054726_llc.fits | 12 | 2701 | 1099.4285 | 1182.0216 |
| kplr003534076-2012179063303_llc.fits | 13 | 2235 | 1183.8607 | 1273.0573 |
| kplr003534076-2012277125453_llc.fits | 14 | 4005 | 1274.1608 | 1371.3224 |
| kplr003534076-2013011073258_llc.fits | 15 | 4100 | 1373.5087 | 1471.1157 |
| kplr003534076-2013098041711_llc.fits | 16 | 3086 | 1472.1169 | 1557.9387 |
| kplr003534076-2013131215648_llc.fits | 17 | 1237 | 1559.2465 | 1591.0017 |
