# kepler-pixels 0.4.0: K05600.01 

Run 2026-10-18T02:05Z. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0. A difference-image offset is evidence about where the light comes from, not a disposition.

P = 51.504285 d (3 x catalogued 17.168095 d), T0 = BKJD 134.637329, duration 13.04 h. Other KOIs masked: 0; not masked: none. Neighbour at +0.00" E, +3.98" N. Offsets are arcsec east/north of the out-of-transit light, jackknife errors over quarters; 'if neighbour' is the same estimator run on a copy of the image moved to the neighbour.

| phase | quarters | events | depth (ppm) | offset E | offset N | if neighbour E, N | chi2 vs 0 | chi2 vs neighbour | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 17 | 23 | 108 +- 14 | 1.28 +- 2.24 | -0.58 +- 2.05 | -1.07, 5.87 | 0.4 | 9.5 | unclear |
| 0.3333333333 | 16 | 27 | -37 +- 14 | -6.78 +- 550.11 | -2.16 +- 321.88 | -0.76, 5.98 | 0.0 | 0.0 | no_signal |
| 0.6666666667 | 15 | 22 | 192 +- 10 | 0.21 +- 0.64 | 0.26 +- 0.69 | -0.52, 6.00 | 0.3 | 27.0 | on_target |
| 0.1666666667 | 14 | 22 | 103 +- 12 | -0.02 +- 2.32 | 1.18 +- 2.03 | -0.69, 6.00 | 0.3 | 4.8 | unclear |
| 0.5 | 16 | 26 | -55 +- 10 | 2.56 +- 4.36 | -0.83 +- 2.14 | -0.72, 5.92 | 0.5 | 9.1 | no_signal |
| 0.8333333333 | 16 | 25 | 35 +- 12 | -10.32 +- 1067.10 | 11.35 +- 1065.06 | -0.77, 6.06 | 0.0 | 0.0 | unclear |

Between quarters: Birge ratio of the quarter depths about the weighted mean, the depth with its error scaled by max(1, Birge), and the unweighted mean of the quarter depths.

| phase | Birge | depth, scaled error (ppm) | SNR scaled | unweighted mean (ppm) | verdict scaled |
|---|---|---|---|---|---|
| 0.0 | 5.43 | 108 +- 75 | 1.4 | -362 +- 310 | no_signal |
| 0.3333333333 | 4.41 | -37 +- 64 | -0.6 | -214 +- 151 | no_signal |
| 0.6666666667 | 4.38 | 192 +- 44 | 4.4 | 375 +- 194 | on_target |
| 0.1666666667 | 4.72 | 103 +- 58 | 1.8 | 109 +- 93 | no_signal |
| 0.5 | 4.07 | -55 +- 42 | -1.3 | -145 +- 61 | no_signal |
| 0.8333333333 | 4.89 | 35 +- 57 | 0.6 | 273 +- 115 | no_signal |
