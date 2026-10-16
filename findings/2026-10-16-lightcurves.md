# Update, 2026-10-16 (second): Kepler light-curve tests of period aliases, and the R☉ census

By MV2 of Munim, Inc. The scripts, checks and this write-up were made with AI agents working in his name. No person has re-derived these numbers yet. Text: CC BY 4.0; code Apache-2.0.

This file adds to `FINDINGS.md` and `findings/2026-10-16.md`, using their numbering of kinds. It reports two scripts that ran on 2026-10-16 in a sealed container on public data. Their code is in this repository (`kepler_alias.py`, `rsun_census.py`, with tests) and their full outputs are in `results/2026-10-16-kepler-alias-0.1.0/` and `results/2026-10-16-rsun-census-0.1.0/`. Before either ran, the expected results were written down (in MV2's working notes). Every expectation held.

| planet | Archive default period | what the Kepler light curve shows | status |
|---|---|---|---|
| Kepler-1802 b | 15.4502 d (Valizadegan et al. 2022) | transits every 15.45 d; none at the half-period phase | **15.45 d confirmed**; the composite row's a, a/R★, insolation and Teq are still from the 7.725 d fit |
| Kepler-1604 b | 0.683684 d (Morton et al. 2016) | equal dips every 0.342 d | **the default period is twice what the light curve shows** (0.342 d was published in 2014); the composite row mixes both periods |
| Kepler-1301 b | 9.08237 d (Morton et al. 2016) | dips every 4.541 d, at both half-phases | **new candidate**: the period may be 4.541 d (or the system is an eclipsing binary) |

## The light-curve test (kepler_alias 0.1.0)

- **Census.** The DR25 TCE table was joined to the DR25 KOI table on (kepid, TCE number). For 246 of the 8,054 KOIs, the detection period (TCE) and the catalogue period (KOI) differ by a whole factor k = 2 to 5, within 0.2%. Six of them are confirmed planets.
- **Test.** The script read Kepler long-cadence PDCSAP light curves from MAST (quality flag 0, the star's other KOIs masked). It measured each transit epoch on the shorter period against a straight-line baseline, then split the epochs by epoch number mod k. If the long period is real, only one group is deep and the others are empty. If the short period is real, every group is deep, with the same depth. Thresholds: deep ≥ 5σ, empty < 3σ, equal within 3σ. Group errors are scaled up by the epoch-to-epoch scatter.
- **Validation.** The test is not biased toward either answer. Kepler-458 b and Kepler-167 e (whose catalogue periods are known to be right and whose TCEs found half the period) came out `long_period_real` with clean nulls (−64 ± 34 and −93 ± 66 ppm). Kepler-42 c was `inconclusive` (no usable epochs).

| planet | k | P short (d) | P long (d) | group depths (ppm) | verdict |
|---|---|---|---|---|---|
| Kepler-1802 b (K02174.03) | 2 | 7.72513619 | 15.4502 | 649.2 ± 54.7 (77 epochs) / −66.6 ± 48.7 (74) | long period real |
| Kepler-458 b (K00179.02) | 2 | 286.187 | 572.376632 | 1601.8 ± 32.2 (2) / −64.4 ± 33.6 (1) | long period real |
| Kepler-167 e (K00490.02) | 2 | 535.616 | 1071.232624 | 17354.7 ± 243.4 (2) / −92.9 ± 65.6 (1) | long period real |
| Kepler-1301 b (K02643.01) | 2 | 4.54116 | 9.08233411 | 198.6 ± 23.2 (142) / 265.1 ± 20.0 (146) | short period real |
| Kepler-1604 b (K04441.01) | 2 | 0.341842017 | 0.683677 | 242.0 ± 6.6 (1113) / 228.3 ± 6.7 (1081) | short period real |
| Kepler-42 c (K00961.02) | 2 | 0.453287416 | 0.906561 | no usable epochs | inconclusive |

### Kepler-1802 b: 15.45 d is right (kind 18, resolved)

`findings/2026-10-16.md` left open which period is real. The light curve settles it. On the 15.45 d phase the transits are 649 ± 55 ppm deep (11.9σ). At the other half of the 7.725 d epochs there is nothing (−67 ± 49 ppm). So the default period (Valizadegan et al. 2022, 15.4502 d) is right, and every KOI table's 7.725 d is half the true period.

Two things still need fixing in the Archive:
- The composite row's `pl_orbsmax` 0.0662 au, `pl_ratdor` 10.88, `pl_insol` 26.9 and `pl_eqt` 581 K come from the DR25 KOI fit at 7.725 d. At 15.45 d Kepler's law with M★ = 0.649 M☉ gives a = 0.1051 au, about 10.7 S⊕ and about 461 K.
- The KOI fit's depth, 382 ppm, averages real transits with empty orbits. The per-transit depth measured here, 649 ± 55 ppm, would make the planet about √(649/382) = 1.30 times larger than the KOI tables' 1.71 R⊕, so about 2.2 R⊕, if the stellar radius holds. This is an estimate from a box-depth measurement, not a transit fit.

### Kepler-1604 b: the default period is twice what the light curve shows (new kind 22)

- **Archive rows, live 2026-10-16.** The default (Morton et al. 2016) gives P = 0.683684256 d, and so do the Q1–Q12, Q1–Q16 and DR24 KOI tables and Fulton & Petigura 2018. The DR25 KOI table gives **0.341842017 d**. Its robovetter comment reads `MOD_SEC_DV---MOD_SEC_ALT---PLANET_PERIOD_IS_HALF_ALT---HAS_SEC_TCE`.
- **DR25 detections.** The DR25 pipeline found **two** TCEs on KIC 8416523, both at 0.68368 d: epochs 131.667 and 132.007 BKJD, depths 135 and 150 ppm. They are 0.340 d apart, which is half the period. In other words, the 0.684 d signal has a second, equal dip halfway between its transits.
- **Light curve.** Folded on 0.342 d, the two alternating groups are 242.0 ± 6.6 and 228.3 ± 6.7 ppm (37σ and 34σ). Their difference is 1.5σ. A planet on a 0.684 d orbit cannot make a second dip of equal depth halfway round, so the 0.684 d planet in the default row is not what the data show.
- **Prior art.** The 0.342 d period is not new. Sanchis-Ojeda et al. 2014 (ApJ 787, 47; arXiv:1403.2379), Table 1, list KIC 8416523 / KOI 4441.01 as an ultra-short-period candidate at P = 0.34184200 d, 279 ppm, that passed their false-positive tests (which include an odd–even comparison). Morton et al. 2016 validated the planet two years later at 0.684 d, and the Archive made that the default. That 2014 result is not among the Archive's eight rows for this planet. What is new here is that the Archive's default contradicts that 2014 result and DR25, and an independent light-curve test agrees with them.
- **The composite row mixes the two periods (kind 18).** `pl_orbper` 0.683684 d (Morton), `pl_orbsmax` 0.01406 au and `pl_insol` 1391 S⊕ (the values in the Fulton & Petigura 2018 row, at 0.684 d), but `pl_ratdor` 1.268 and `pl_eqt` 2023 K (the values in the DR25 row, at 0.342 d). With the row's own a and R★ = 0.76 R☉, a/R★ = 0.01406 / (0.76 × 0.0046505) = 3.98, not 1.268.
- **What follows if 0.342 d is right.** Kepler's law with M★ = 0.81 M☉ gives a = 0.0089 au (a/R★ ≈ 2.5). Insolation would be 2^(4/3) = 2.52 times the default's, about 3,500 S⊕, and Teq would be about 2,030 K. The planet would orbit in 8.2 hours.
- **Caveat.** Equal dips every 0.342 d also fit an eclipsing binary at 0.684 d with two equal eclipses, diluted by a brighter star. And the observed duration (1.00–1.16 h) is close to the longest possible for a central transit at 0.342 d around this star (about 1.07 h). So which of the two it is needs a proper transit fit. Either way, the default row's 0.684 d planet is the one interpretation the light curve rules out.

### Kepler-1301 b: a possible 4.54-day planet listed at 9.08 days (candidate)

- **Archive rows.** The Archive has nine rows for this planet: the default (Morton et al. 2016), every KOI table from Q1–Q8 to DR25, Berger et al. 2018 and Gajdoš et al. 2019. Every one of them that gives a period gives 9.0823 d. But the only DR25 TCE on this star (KIC 6933567, TCE 1) is at **4.54116 d**, with depth 235 ppm against the KOI fit's 297 ppm. If the true period were 9.08 d, folding on 4.54 d would roughly halve the depth. The TCE depth is 0.79 of the KOI depth, not 0.5.
- **Light curve.** Folded on 4.541 d, the group at the 9.08 d phase is 265 ± 20 ppm (13σ). The other group, halfway between the catalogued transits, is **199 ± 23 ppm (8.6σ)**. The difference is 66 ± 31 ppm (2.2σ). The off-phase dips are not confined to one stretch of the mission. Over roughly the first 360 days alone (epochs 0–80), the unweighted mean of the off-phase epochs is about 165 ± 47 ppm.
- **Prior art.** No paper or catalogue that gives Kepler-1301 b (KOI-2643.01) a 4.54 d period was found (web searches on 2026-10-16). Sanchis-Ojeda et al. 2014 do not cover it (their search was for periods under a day).
- **What follows if 4.541 d is right.** a = 0.0815 × 2^(−2/3) ≈ 0.051 au, insolation ≈ 76 × 2.52 ≈ 192 S⊕, and Teq ≈ 734 × 1.26 ≈ 925 K. The radius is unchanged, because every catalogued transit is still a transit.
- **Status: candidate, not a claim.** The off-phase group is 2.2σ shallower, so an eclipsing binary at 9.08 d with slightly unequal eclipses is not excluded. kepler_alias 0.2.0 (queued) splits each group's depth into the two halves of the mission. A transit fit with free period, and a check of the DR25 robovetter's model-shift results for this TCE, should come before anyone corrects the catalogue.

## The R☉ census (rsun_census 0.1.0): kind 21 is confined to Hedges et al. 2019

The census checked every transiting `ps` row whose stored R★ is far enough from 1 R☉ to tell a ratio to the star from a ratio to the Sun:
- a/R★ against a / R☉: 12,239 rows tested;
- Rp/R★ against Rp / R☉: 12,412 rows tested;
- 15,592 rows tested on at least one of the two.

| result | count |
|---|---|
| rows matching R☉ in **both** ratios | **7**, all Hedges et al. 2019 (7 of its 7 rows), as `findings/2026-10-16.md` reported |
| rows matching in Rp/R★ only | 3: TOI-2048 b (Newton et al. 2022, already reported), TOI-199 b (Bello-Arufe et al. 2026, not the default row; open lead), Kepler-289 c (Santerne et al. 2016, see below) |
| rows matching in a/R★ only | 237, mostly KOI-table rows (36–51 per KOI delivery, about 2–3% of the rows tested) |

- **Both ratios.** Only Hedges et al. 2019 normalised by the Sun's radius in both columns. No other source in the Archive does.
- **a/R★ only.** These matches are not unit errors. A transit fit measures a/R★ from the light curve, independently of the catalogue's R★. When the catalogue's R★ is wrong and the star is really about 1 R☉, the fitted a/R★ naturally equals a / R☉. Example: for Kepler-128, Ofir et al. 2025 (26.8) and every KOI table (26.8–27.6) fit an a/R★ near a / R☉ (26.5–27.2). The stored R★ is 1.61–1.66 R☉, which would give about 16.4. This points at Kepler-128's stellar radius (or an eccentric orbit), not at a units slip. Such rows belong to a later stellar-consistency census.
- **Kepler-289 c (Santerne et al. 2016).** `pl_ratror` 0.1062 agrees with the KOI tables' 0.1039. But the row's Rp and R★ (1.46 R☉) give 0.0725. The R☉ match comes from the stored R★ being too large for the measured ratio, as for Kepler-128. Open lead: check Santerne et al. 2016's stellar radius.
- **Method note.** The census's control windows (0.85 and 1/0.85 of a / R☉) are hit by correctly normalised rows of stars near 1.18 and 0.85 R☉. So they do not give a clean chance rate, and the "control per window" counts in `summary.json` (381 for a/R★, 1,676 for Rp/R★) should not be read as one. 0.2.0 will use a control that excludes 1/R★.

## Limits

- The light-curve verdicts use a box-depth measurement on PDCSAP flux with a linear local baseline. They are not transit fits. A `short_period_real` verdict cannot tell a planet at the short period from an eclipsing binary at the long period with equal eclipses.
- Archive values were read live through the TAP service on 2026-10-16. Prior art was searched with web search and the arXiv/ar5iv text of Sanchis-Ojeda et al. 2014. No paper other than that one was read in full for this update.
- No erratum or Archive note for any of the three planets was found.
