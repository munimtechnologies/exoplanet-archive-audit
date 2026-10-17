# Draft research note: the catalogued periods of Kepler-1301 b, KOI-4711.01 and KOI-4893.01 are off by a factor of two

MV2 of Munim, Inc., 2026-10-17. **Draft.** Made with AI agents working in his name; no human has checked
it yet. Text CC BY 4.0; code Apache-2.0. This note brings together results already in this repository
(findings/2026-10-16-kepler-1301.md, 2026-10-16-dv-secondary.md, 2026-10-17-pixels-results.md,
2026-10-17-pixels-scatter-results.md). It adds no new measurements. It is written in the format of a
Research Note of the AAS (at most 1,500 words, one table). It has not been submitted anywhere.

## Abstract

The NASA Exoplanet Archive lists Kepler-1301 b (KOI-2643.01) at 9.082 d and the candidates KOI-4711.01
and KOI-4893.01 at 4.364 d and 6.588 d. For each, the later Kepler pipeline detections (threshold-crossing
events, TCEs) matched to the KOI are at a period that differs by a factor of two (4.541, 8.728 and
13.175 d), but the KOI kept its earlier period. We measure the alternate events separately in difference
images from the Q1-Q17 long-cadence target pixel files. Kepler-1301 b's events halfway between the
catalogued transits are as deep as the catalogued ones (ratio 0.90 +- 0.09), and both come from the
target. The signal therefore repeats every 4.541 d. For KOI-4893.01 and KOI-4711.01, every other
catalogued event is missing or much shallower (7.1 sigma and 4.8 sigma), so their periods are 13.175 d and
8.728 d. None of these corrections appears in the recent KOI re-analysis by Lissauer et al. (2024).

## 1. Introduction

When the Kepler pipeline detects a signal on a star that already has a KOI, the TCE is matched
("federated") to that KOI. Thompson et al. (2018, Sec. VI.2) count TCEs at double or half the KOI period
as matches, and the KOI keeps its original period. Lissauer et al. (2024) describe one case where this
left a wrong period in the table: for KOI-521.02 the TCEs had the correct period and the KOI kept the
earlier one. We searched the DR25 tables for KOIs whose federated TCE period is a whole multiple or
fraction of the KOI period and tested the leads in the light curves and then in the pixels. Three
survive. They are listed in Table 1.

## 2. Data and method

- **Catalogue values.** Read from the NASA Exoplanet Archive (Akeson et al. 2013): the cumulative KOI
  table, the Q1-Q16, DR24 and DR25 TCE tables, and the planetary-systems table. Kepler-1301 b's nine
  `ps` rows all give 9.0823-9.0824 d. Its default row is Morton et al. (2016), 9.08237046 d.
- **Pipeline detections.** On KIC 6933567 (Kepler-1301), the Q1-Q12, Q1-Q16, DR24 and DR25 searches
  each found one TCE, always at 4.5411-4.5412 d. The DR25 KOI row is federated to that TCE. The DR25
  Robovetter scored it 0.918 with no false-positive flags. The row's `koi_num_transits` is 298. A
  9.0823 d period allows at most 161 transits in Kepler's ~1,460 d span; a 4.541 d period allows 322.
  For KOI-4893.01 the Q1-Q16, DR24 and DR25 TCEs are at 13.1751 d. For KOI-4711.01 the DR24 and DR25
  TCEs are at 8.7276 d.
- **Pixels.** We used the Kepler long-cadence target pixel files, one per quarter (QUALITY = 0). For
  each event we made a difference image: the mean out-of-transit frame minus the mean in-transit frame.
  Events were averaged within each quarter. Each quarter's difference image was fitted by least squares
  as a scaled and shifted copy of its out-of-transit image. The scale gives the fractional depth and the
  shift gives the position of the dimming source (Bryson et al. 2013 discuss this kind of test).
  Quarters were combined with inverse-variance weights. Other KOIs on the same star were masked. Events
  were grouped by phase of the ephemeris folded at twice the shorter period: groups 0 and 0.5 hold the
  alternate events, and groups 0.25 and 0.75 are null controls. The quarter depths scatter more than
  their formal errors allow (Birge ratios 1.3-2.7), so we scaled each depth error by its group's Birge
  ratio (Birge 1932). Depths are measured against all the light in the pixel stamp and are not corrected
  for crowding, so they come out below the catalogue depths.
- **Pre-registration.** The predictions for the pixel tests were written down and published before each
  job ran. All 12 predictions of the first run held, and all 7 of the error-scaling re-run held.

## 3. Results

**Table 1.** Depths in the Kepler pixels (ppm against total stamp flux, 1 sigma, Birge-scaled) at the
four phase groups of the folded ephemeris. "On target" means the difference-image centroid is consistent
with the target position and not with a neighbour or a 1-pixel offset.

| Object (KIC) | Catalogued P (d) | TCE P (d) | Folded at (d) | Phase 0 | Phase 0.5 | Nulls 0.25 / 0.75 | Reading |
|---|---|---|---|---|---|---|---|
| Kepler-1301 b, KOI-2643.01 (6933567) | 9.08233 | 4.54116 | 9.08233 | 227.9 +- 13.6, on target | 204.9 +- 15.7, on target | -28.8 +- 22.0 / 20.5 +- 28.1 | equal depths (ratio 0.90 +- 0.09): P = 4.541 d |
| KOI-4893.01 (11970050) | 6.58754 | 13.17508 | 13.17507 | 275.4 +- 31.5, on target | -2.5 +- 23.2 | 25.0 +- 34.4 / 11.7 +- 32.7 | difference 278 +- 39 (7.1 sigma): P = 13.175 d |
| KOI-4711.01 (8355131) | 4.36383 | 8.72764 | 8.72766 | 45.3 +- 21.9 | 224.9 +- 30.3, on target | 3.4 +- 24.4 / -13.3 +- 30.1 | difference 180 +- 37 (4.8 sigma): P = 8.728 d |

The light curves give the same split. At the catalogued and the halfway phases, the box depths are
265 +- 20 and 199 +- 23 ppm for Kepler-1301 b, 314 +- 47 and 22 +- 43 ppm for KOI-4893.01, and 69 +- 29
and 267 +- 30 ppm for KOI-4711.01. Pixel data and light curves come from the same exposures, so the two
tests are not fully independent: the light curves use the pipeline's optimal aperture and systematics
corrections, and the pixel test uses the whole stamp. For
Kepler-1301 b, a Gaia DR3 source (G = 19.95, 3.3 arcsec from the G = 15.36 target) is excluded as the
source of either set of dips (chi2 37-67 against its position, 2 degrees of freedom).

## 4. Discussion

**Kepler-1301 b.** At 4.541 d the semi-major axis is about 0.0515 au instead of 0.0815 au. The
insolation is about 2.5 times the value at 9.08 d, and the equilibrium temperature is about 925 K (the
DR25 TCE's own estimate). The radius has to be refitted: the DR25 TCE fit gives 1.44 R_Earth with a poorly
constrained impact parameter, against 1.35-1.41 R_Earth in the catalogues. The statistical validation by
Morton et al. (2016) assumed 9.08 d. Our test does not exclude an eclipsing binary blended within about 1
arcsec that has two equal eclipses at 9.08 d. The validation would need redoing at 4.541 d.

**KOI-4893.01.** The DR25 data-validation fit at 13.175 d gives 2.28 R_Earth and an equilibrium
temperature of 787 K, against 1.51 R_Earth and 992 K in the KOI table. The catalogued depth averages real
transits with empty orbits. The pipeline's search for secondary events finds nothing at phase 0.5 of the
13.175 d orbit (its strongest secondary is at phase 0.650, MES 2.7). We did not test 26.35 d, so the
period could also be a multiple of 13.175 d.

**KOI-4711.01.** The deep events repeat every 8.728 d. Equal transits every 4.364 d are disfavoured at
4.8 sigma. The alternate epochs are not clearly empty: the pixels give 45 +- 22 ppm (2.1 sigma), the
light curve 69 +- 29 ppm, and the pipeline's strongest secondary sits at phase 0.500 (MES 3.4). If that
weak signal is real, an eclipsing binary at 8.728 d with unequal eclipses would fit, so whether
KOI-4711.01 is a planet is open.

**Prior work.** Lissauer et al. (2024, Table 1) list all three objects as planet candidates or planets
at their catalogued periods. Searching on 2026-10-16 and 2026-10-17 by planet name, KOI number and KIC
number, we found no paper, catalogue note or forum post that gives these periods. We have not read the
per-object material of Morton et al. (2016).

**Limits.** Each Birge ratio rests on 11-17 quarters, so it is itself uncertain by about 20%. Depths are
not corrected for crowding. No blended eclipsing binary within about 1 arcsec is excluded. The work was
done with AI agents and has not yet been checked by an independent person.

## Code and data

All code, inputs and outputs are at github.com/munimtechnologies/exoplanet-archive-audit (Apache-2.0 for
code, CC BY 4.0 for text): `kepler_pixels.py` 0.4.0 and its tests, the pre-registrations in `findings/`,
and the per-quarter outputs in `results/2026-10-17-kepler-pixels-0.4.0/`.

## AI disclosure

The catalogue queries, analysis code, measurements and text of this note were produced by AI agents
(Anthropic Claude models) working for MV2 of Munim, Inc. Every prediction was published before its test
ran.

## References

- Akeson, R. L., et al. 2013, PASP, 125, 989
- Birge, R. T. 1932, Phys. Rev., 40, 207
- Bryson, S. T., et al. 2013, PASP, 125, 889
- Lissauer, J. J., et al. 2024, PSJ, 5, 152
- Morton, T. D., et al. 2016, ApJ, 822, 86
- Thompson, S. E., et al. 2018, ApJS, 235, 38
