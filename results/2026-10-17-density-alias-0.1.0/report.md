# density-alias 0.1.0

Run 2026-10-17T04:09Z. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0.

246 of 246 dv_alias census rows assessed; 224 with Berger et al. 2020 stellar densities. A verdict is evidence about the period, not a period correction.

## Calibration (confirmed planets outside the census, tested against 2P and P/2)

- confirmed_outside_census: 2725
- berger_matched: 2610
- constrained: 1710
- median_ln_r: 0.2172
- mad_sigma_ln_r: 0.4781
- frac_t_koi_ge_2: 0.1456
- frac_t_koi_ge_kepler1301b: 0.1433
- false_favors_alt_half: 92
- false_favors_alt_double: 9
- false_favors_alt_either: 101
- correct_favors_koi_half: 384
- correct_favors_koi_double: 342

## Counts (kind | dv_alias verdict | disposition | density verdict)

- koi_long|koi_long|CANDIDATE|both_tense: 1
- koi_long|koi_long|CANDIDATE|unconstrained: 3
- koi_long|koi_long|CONFIRMED|ambiguous: 1
- koi_long|koi_long|CONFIRMED|favors_alt: 1
- koi_long|koi_long|CONFIRMED|favors_koi: 1
- koi_long|koi_long|FALSE POSITIVE|ambiguous: 24
- koi_long|koi_long|FALSE POSITIVE|both_tense: 26
- koi_long|koi_long|FALSE POSITIVE|favors_alt: 15
- koi_long|koi_long|FALSE POSITIVE|favors_koi: 5
- koi_long|koi_long|FALSE POSITIVE|unconstrained: 32
- tce_long|no_alias_secondary|CANDIDATE|ambiguous: 1
- tce_long|no_alias_secondary|CONFIRMED|unconstrained: 1
- tce_long|no_alias_secondary|FALSE POSITIVE|ambiguous: 4
- tce_long|no_alias_secondary|FALSE POSITIVE|both_tense: 7
- tce_long|no_alias_secondary|FALSE POSITIVE|unconstrained: 7
- tce_long|secondary_at_alias|CANDIDATE|ambiguous: 7
- tce_long|secondary_at_alias|CANDIDATE|both_tense: 2
- tce_long|secondary_at_alias|CANDIDATE|favors_alt: 1
- tce_long|secondary_at_alias|CANDIDATE|favors_koi: 1
- tce_long|secondary_at_alias|CANDIDATE|unconstrained: 4
- tce_long|secondary_at_alias|CONFIRMED|unconstrained: 2
- tce_long|secondary_at_alias|FALSE POSITIVE|ambiguous: 31
- tce_long|secondary_at_alias|FALSE POSITIVE|both_tense: 29
- tce_long|secondary_at_alias|FALSE POSITIVE|favors_alt: 4
- tce_long|secondary_at_alias|FALSE POSITIVE|favors_koi: 3
- tce_long|secondary_at_alias|FALSE POSITIVE|unconstrained: 33

## Every confirmed or candidate row

| kepoi_name | kepler_name | koi_disposition | kind | k | koi_period | p_alt | verdict | stellar_src | rho_star | r_koi | r_alt | t_koi | t_alt | density_verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| K00179.02 | Kepler-458 b | CONFIRMED | koi_long | 2 | 572.377 | 286.187 | koi_long | berger2020 | 0.202 | 0.719 | 0.360 | 0.039 | 0.944 | ambiguous |
| K00422.01 |  | CANDIDATE | koi_long | 2 | 809.014 | 404.506 | koi_long | berger2020 | 0.399 | 19.561 | 9.781 | 17.663 | 13.084 | both_tense |
| K02643.01 | Kepler-1301 b | CONFIRMED | koi_long | 2 | 9.082 | 4.541 | koi_long | berger2020 | 2.008 | 4.454 | 2.230 | 2.048 | 0.861 | favors_alt |
| K00490.02 | Kepler-167 e | CONFIRMED | koi_long | 2 | 1071.233 | 535.616 | koi_long | berger2020 | 2.648 | 1.077 | 0.539 | 0.000 | 3.551 | favors_koi |
| K00272.01 |  | CANDIDATE | koi_long | 2 | 1.281 | 0.641 | koi_long | berger2020 | 0.456 | 2.803 | 1.661 | 4.324 | 1.225 | unconstrained |
| K00521.02 |  | CANDIDATE | koi_long | 2 | 10.821 | 5.410 | koi_long | dr25 | 1.183 | 1.835 | 0.922 | 0.076 | 0.000 | unconstrained |
| K06798.01 |  | CANDIDATE | koi_long | 2 | 2.642 | 1.321 | koi_long | berger2020 | 0.004 | 1098.861 | 556.503 | 5.797 | 5.208 | unconstrained |
| K02093.03 |  | CANDIDATE | tce_long | 2 | 0.496 | 0.992 | secondary_at_alias | berger2020 | 1.220 | 0.930 | 1.723 | 0.000 | 0.597 | ambiguous |
| K02732.04 |  | CANDIDATE | tce_long | 2 | 24.561 | 49.121 | secondary_at_alias | berger2020 | 0.336 | 0.772 | 1.543 | 0.000 | 0.373 | ambiguous |
| K02874.01 |  | CANDIDATE | tce_long | 2 | 0.353 | 0.705 | secondary_at_alias | berger2020 | 2.293 | 1.141 | 2.130 | 0.000 | 1.788 | ambiguous |
| K04144.01 |  | CANDIDATE | tce_long | 2 | 0.488 | 0.975 | secondary_at_alias | berger2020 | 1.581 | 2.669 | 5.190 | 1.174 | 2.321 | ambiguous |
| K04685.01 |  | CANDIDATE | tce_long | 2 | 0.494 | 0.988 | secondary_at_alias | berger2020 | 1.759 | 1.124 | 2.121 | 0.000 | 0.930 | ambiguous |
| K04893.01 |  | CANDIDATE | tce_long | 2 | 6.588 | 13.175 | no_alias_secondary | berger2020 | 2.069 | 3.201 | 6.397 | 0.840 | 1.515 | ambiguous |
| K05875.02 |  | CANDIDATE | tce_long | 2 | 4.274 | 8.548 | secondary_at_alias | berger2020 | 1.303 | 1.479 | 2.950 | 0.146 | 1.253 | ambiguous |
| K07859.01 |  | CANDIDATE | tce_long | 2 | 0.307 | 0.613 | secondary_at_alias | berger2020 | 2.122 | 1.749 | 3.289 | 0.433 | 1.489 | ambiguous |
| K01251.01 |  | CANDIDATE | tce_long | 2 | 0.576 | 1.152 | secondary_at_alias | berger2020 | 0.164 | 2.681 | 3.405 | 2.882 | 3.886 | both_tense |
| K04711.01 |  | CANDIDATE | tce_long | 2 | 4.364 | 8.728 | secondary_at_alias | berger2020 | 0.331 | 29.407 | 58.750 | 3.457 | 4.233 | both_tense |
| K07157.01 |  | CANDIDATE | tce_long | 2 | 23.983 | 47.967 | secondary_at_alias | berger2020 | 0.853 | 0.356 | 0.711 | 6.236 | 0.349 | favors_alt |
| K02796.01 |  | CANDIDATE | tce_long | 2 | 0.537 | 1.075 | secondary_at_alias | berger2020 | 1.306 | 2.050 | 3.959 | 0.795 | 2.048 | favors_koi |
| K00961.02 | Kepler-42 c | CONFIRMED | tce_long | 2 | 0.453 | 0.907 | secondary_at_alias | berger2020 | 39.209 | 0.338 | 0.654 | 0.759 | 0.120 | unconstrained |
| K02174.03 | Kepler-1802 b | CONFIRMED | tce_long | 2 | 7.725 | 15.450 | no_alias_secondary | dr25 | 3.540 | 0.115 | 0.229 | 0.529 | 0.334 | unconstrained |
| K02879.01 |  | CANDIDATE | tce_long | 2 | 0.339 | 0.678 | secondary_at_alias | dr25 | 0.165 | 1.764 | 1.289 | 0.232 | 0.000 | unconstrained |
| K03318.02 |  | CANDIDATE | tce_long | 2 | 25.697 | 51.395 | secondary_at_alias | berger2020 | 1.181 | 0.266 | 0.531 | 0.282 | 0.092 | unconstrained |
| K04419.01 |  | CANDIDATE | tce_long | 2 | 0.260 | 0.520 | secondary_at_alias | berger2020 | 4.191 | 0.174 | 0.167 | 0.412 | 0.424 | unconstrained |
| K04441.01 | Kepler-1604 b | CONFIRMED | tce_long | 2 | 0.342 | 0.684 | secondary_at_alias | berger2020 | 2.601 | 0.127 | 0.104 | 0.801 | 0.891 | unconstrained |
| K04844.01 |  | CANDIDATE | tce_long | 3 | 0.428 | 1.284 | secondary_at_alias | berger2020 | 2.711 | 3.013 | 8.814 | 0.223 | 0.521 | unconstrained |

## Every row whose density favours the other period

| kepoi_name | kepler_name | koi_disposition | kind | k | koi_period | p_alt | verdict | stellar_src | rho_star | r_koi | r_alt | t_koi | t_alt | density_verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| K01284.01 |  | FALSE POSITIVE | koi_long | 2 | 3.117 | 1.559 | koi_long | berger2020 | 0.118 | 1.972 | 1.313 | 3.618 | 0.000 | favors_alt |
| K02643.01 | Kepler-1301 b | CONFIRMED | koi_long | 2 | 9.082 | 4.541 | koi_long | berger2020 | 2.008 | 4.454 | 2.230 | 2.048 | 0.861 | favors_alt |
| K03550.01 |  | FALSE POSITIVE | koi_long | 2 | 2.148 | 1.074 | koi_long | berger2020 | 1.593 | 1.943 | 1.029 | 5.736 | 0.000 | favors_alt |
| K03566.01 |  | FALSE POSITIVE | koi_long | 2 | 8.646 | 4.324 | koi_long | berger2020 | 0.121 | 2.543 | 1.310 | 4.263 | 0.000 | favors_alt |
| K03600.01 |  | FALSE POSITIVE | koi_long | 2 | 4.809 | 2.405 | koi_long | berger2020 | 0.079 | 2.135 | 1.176 | 2.164 | 0.000 | favors_alt |
| K03764.01 |  | FALSE POSITIVE | koi_long | 2 | 1.304 | 0.652 | koi_long | berger2020 | 1.519 | 2.156 | 1.201 | 4.439 | 0.000 | favors_alt |
| K06117.01 |  | FALSE POSITIVE | koi_long | 2 | 9.524 | 4.762 | koi_long | berger2020 | 0.064 | 2.844 | 1.474 | 2.694 | 0.318 | favors_alt |
| K06385.01 |  | FALSE POSITIVE | koi_long | 2 | 9.761 | 4.881 | koi_long | berger2020 | 0.059 | 2.541 | 1.324 | 3.244 | 0.000 | favors_alt |
| K06435.01 |  | FALSE POSITIVE | koi_long | 2 | 15.289 | 7.644 | koi_long | berger2020 | 2.092 | 2.227 | 1.117 | 5.321 | 0.000 | favors_alt |
| K06567.01 |  | FALSE POSITIVE | koi_long | 2 | 9.584 | 4.792 | koi_long | berger2020 | 0.187 | 2.102 | 1.084 | 4.082 | 0.000 | favors_alt |
| K06764.01 |  | FALSE POSITIVE | koi_long | 2 | 7.003 | 3.501 | koi_long | berger2020 | 0.405 | 2.528 | 1.291 | 6.522 | 0.000 | favors_alt |
| K06792.01 |  | FALSE POSITIVE | koi_long | 2 | 4.239 | 2.119 | koi_long | berger2020 | 0.098 | 2.654 | 1.545 | 3.234 | 0.645 | favors_alt |
| K06800.01 |  | FALSE POSITIVE | koi_long | 2 | 5.078 | 2.539 | koi_long | berger2020 | 0.204 | 2.274 | 1.252 | 4.343 | 0.000 | favors_alt |
| K06833.01 |  | FALSE POSITIVE | koi_long | 2 | 7.119 | 3.559 | koi_long | berger2020 | 0.408 | 3.110 | 1.598 | 2.449 | 0.495 | favors_alt |
| K06974.01 |  | FALSE POSITIVE | koi_long | 2 | 7.140 | 3.570 | koi_long | berger2020 | 0.215 | 2.140 | 1.101 | 4.371 | 0.000 | favors_alt |
| K07482.01 |  | FALSE POSITIVE | koi_long | 2 | 9.763 | 4.881 | koi_long | berger2020 | 0.192 | 2.373 | 1.225 | 6.227 | 0.000 | favors_alt |
| K01380.01 |  | FALSE POSITIVE | tce_long | 2 | 1.074 | 2.148 | secondary_at_alias | berger2020 | 2.710 | 0.444 | 0.867 | 6.115 | 0.000 | favors_alt |
| K03167.01 |  | FALSE POSITIVE | tce_long | 2 | 0.500 | 0.999 | secondary_at_alias | berger2020 | 2.107 | 0.480 | 0.884 | 2.640 | 0.000 | favors_alt |
| K03896.01 |  | FALSE POSITIVE | tce_long | 2 | 3.890 | 7.781 | secondary_at_alias | berger2020 | 0.415 | 0.293 | 0.575 | 2.740 | 0.748 | favors_alt |
| K04408.01 |  | FALSE POSITIVE | tce_long | 2 | 1.105 | 2.210 | secondary_at_alias | berger2020 | 1.528 | 0.324 | 0.620 | 2.701 | 0.585 | favors_alt |
| K07157.01 |  | CANDIDATE | tce_long | 2 | 23.983 | 47.967 | secondary_at_alias | berger2020 | 0.853 | 0.356 | 0.711 | 6.236 | 0.349 | favors_alt |
