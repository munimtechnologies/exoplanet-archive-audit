# density-alias 0.1.0: predictions written before the run (2026-10-17 ~03:40Z)

By MV2 of Munim, Inc.; written with AI agents. Scored in public when the job lands, misses included.

The question: for the 246 DR25 KOIs whose matched TCE period is a whole multiple (or fraction) of the KOI
period (dv_alias 0.1.0 census), which period does the host star's independent density allow? It also asks
how often the same test misfires on confirmed planets whose period is not in question.

## Predictions

1. All unit tests pass.
2. At least 200 of the 246 census rows get a Berger et al. 2020 stellar density.
3. Calibration: 1,200-2,400 constrained confirmed planets outside the census; median ln(rho_fit/rho_star)
   within +/-0.25.
4. Calibration false-alarm rate (density `favors_alt` for P/2 or for 2P, when P is the confirmed period):
   at most 10 % of constrained planets.
5. Between 3 % and 20 % of constrained calibration planets have t_koi at least as large as Kepler-1301 b's
   (about 2.05). Above 20 % would mean Kepler-1301 b's density tension is unremarkable.
6. Among CONFIRMED/CANDIDATE TCE-longer rows that dv_alias marked `secondary_at_alias` and that get a decided
   density verdict (`favors_koi` or `favors_alt`), at least 75 % are `favors_koi`.
7. No CONFIRMED/CANDIDATE KOI-longer row with a KOI period above 100 d gets `favors_alt`.

## Code checks (computed by hand from the same inputs; not predictions)

| KOI | P_koi / P_alt (d) | r_koi | r_alt | t_koi | t_alt | verdict |
|---|---|---|---|---|---|---|
| Kepler-1301 b (2643.01) | 9.082 / 4.541 | 4.45 | 2.23 | 2.05 | 0.86 | favors_alt (marginal) |
| Kepler-167 e (490.02) | 1071.2 / 535.6 | 1.08 | 0.54 | 0 | 3.55 | favors_koi |
| Kepler-458 b (179.02) | 572.4 / 286.2 | 0.72 | 0.36 | 0.04 | 0.94 | ambiguous |
| KOI-4893.01 | 6.588 / 13.175 | 3.20 | 6.40 | 0.84 | 1.52 | ambiguous |
| Kepler-1604 b (4441.01) | 0.342 / 0.684 | - | - | - | - | unconstrained (grazing fit) |

## Limits known in advance

- DR25 fits assume circular orbits; an eccentric planet's fitted density is off by
  ((1 + e sin w) / sqrt(1 - e^2))^3. Only e <= 0.1 is allowed for.
- The b-rho degeneracy makes many fitted densities lopsided or unconstrained, mostly for grazing and
  low-SNR fits.
- For eclipsing binaries and blends the stellar density test is not meaningful. Dilution from a
  neighbour also biases the fitted density.
- For Kepler-1301 b, a high fitted density at 9.08 d could come from the 4.54 d period, from e >~ 0.3,
  or from the transit being on a different (denser) star. The pixel-level job (kepler-pixels-v1)
  addresses the last of these.
