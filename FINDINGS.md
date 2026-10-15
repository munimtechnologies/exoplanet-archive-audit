# Findings so far (2026-10-14)

By MV2 of Munim, Inc. The code, checks and this write-up were made with AI agents working in his name. Each claim below is labelled with how far it has been verified. Every count comes from the 0.2.0 run on the 2026-10-14T14:00Z download (`results/2026-10-14-v0.2/`). Text: CC BY 4.0. Code: Apache-2.0.

**Summary.** Six kinds of problem, each checked against the source paper (and, where one exists, its erratum):

| # | kind | where the error is | cases checked |
|---|---|---|---|
| 1 | a whole reference's stellar densities in solar units under a g/cm³ label | 2 in the journal tables, 2 at ingestion | 4 references, about 1,470 rows |
| 2 | one value stored in the wrong unit | ingestion | 5 rows (plus 1 whose paper is not public) |
| 3 | a printed value that disagrees with the same paper's other numbers | the paper | 10 papers, 17 planets (section 3) |
| 4 | a different quantity stored in the column | ingestion | Kepler-419 b and c |
| 5 | a published erratum not applied | Archive not updated | HD 48948 b, c and d |
| 6 | a placeholder stored as a measurement | the paper's input table | Stassun et al. 2017: log g = 4.50 for KELT-2 A, KELT-7, WASP-33 |

## 1. Stellar densities from four references are stored in solar units, while the Archive documents g/cm³

**Status: verified, both across every row and against each source paper's own text or tables. Bibcodes checked against ADS/arXiv on 2026-10-14. 0.3.0 adds a row-by-row file (`unit_groups.csv`) and the exact count of composite (default) values affected. That run is queued.**

The Archive documents `st_dens` as "Stellar Density [g/cm**3]" ([column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)). For every parameter set it holds, the audit compares `st_dens` with 1.4098 g/cm³ · M★/R★³, using the star mass and radius of the same row. If a reference's densities were really in g/cm³, the median ratio would be close to 1. For four references the median is close to 1/1.4098 = 0.709, which is what you get when the densities are in solar units (ρ/ρ☉). Once they are multiplied by 1.4098, the median comes back to 1:

| reference | table | rows | median ratio | rows within 10% of median | median after ×1.4098 | what the source paper says |
|---|---|---|---|---|---|---|
| Fulton & Petigura 2018 (CKS VII, 2018AJ....156..264F) | `ps` | 1,414 | 0.7163 | 92.5% | 1.01 | Table 2 (arXiv:1805.01453) labels ρ_iso "g/cc", but its values equal M/R³ in solar units (K00001: 0.99/1.04³ = 0.88, listed as 0.87) |
| Torres et al. 2017 (2017AJ....154..264T) | `ps` | 22 | 0.7025 | 90.9% | 0.990 | Table 6 (arXiv:1711.01267) gives ρ★ in **(ρ☉)**. Its Table 8 gives a transit density in g cm⁻³ |
| Mann et al. 2017 (ZEIT IV, 2017AJ....153...64M) | `ps` | 19 | 0.7099 | 68.4% | 1.001 | Praesepe, arXiv:1609.00726, Table 2: "ρ∗ (ρ⊙)" for seven stars. Whether all 19 rows cite this paper is checked by bibcode in 0.3.0 |
| Mann et al. 2017 | `pscomppars` | 7 | 0.7184 | 71.4% | 1.013 | (same) |
| MacDonald et al. 2016 (Kepler-80, 2016AJ....152..105M) | `ps` | 11 | 0.7056 | 100% | 0.995 | Text (arXiv:1607.07540, §III): "ρ = 2.33 ± 0.15 ρ⊙", which equals 0.730/0.678³ in solar units. Table 2 prints the same 2.33 with the unit "g cm-3" |
| MacDonald et al. 2016 | `pscomppars` | 5 | 0.7056 | 100% | 0.995 | (same) |

**What this means.**
- **Fulton & Petigura 2018 and MacDonald et al. 2016:** the journal tables themselves print solar-unit values under a g/cm³ label, so the Archive copied the label faithfully.
- **Torres et al. 2017 and Mann et al. 2017:** the papers label ρ☉ correctly, so these look like slips at ingestion.
- **Impact.** For Kepler-80, the composite table, which most users take as "the" parameters, gives a stellar density of 2.33 "g/cm³". The value implied by the paper's own mass and radius is 1.4098 × 2.34 = 3.30 g/cm³. At least 12 composite values (7 from Mann et al. 2017, 5 from MacDonald et al. 2016) are affected. Of the Fulton & Petigura densities, 901 rows fail the audit's per-row test (10% and 3σ). At least three default parameter sets (Kepler-105 b and c, Kepler-139 f) carry those densities because later papers reused the CKS stellar parameters.

**Why it matters.** Comparing the stellar density from a transit fit with an independent stellar density is a standard way to measure orbital eccentricity (the "photo-eccentric" effect). A density that is 1.41 times too low mimics ((1 + e sin ω)/√(1 − e²))³ = 1.41, which means e ≈ 0.11 at ω = 90°, for an orbit that may be circular. Demographic work that pulls `st_dens` from the Archive would also inherit a 41% bias for these stars.

**Prior art.** Searches found no erratum for these papers, no Archive notice and no published report of the mismatch (searched 2026-10-14). An Archive-wide check of Kepler's third law on default parameters (arXiv:2605.10427) did not test stellar densities.

**Limits.**
- Only the arXiv versions of the papers were read. 0.3.0 also tries to save the published catalogs' CDS ReadMe files, which carry the journal's column units.
- Some Fulton & Petigura rows differ from M/R³ in solar units by up to about 15%, possibly because the Archive pairs ρ_iso with a different radius.
- The Torres et al. 2017 densities used in the composite table have a median ratio of 0.82, a less coherent mix that 0.3.0 will list row by row.

## 2. Single rows where one column is in the wrong unit

**Status: each is evident from other columns of the same row. Five were checked against the source paper on 2026-10-14; the sixth (TOI-2049 b) has no public paper yet.**

| planet (reference) | tables | stored | what the paper or row says | likely correct value |
|---|---|---|---|---|
| HAT-P-25 b (Wang et al. 2018, PASP 130, 064401) | `ps` | `pl_trandep` = 0.0161 % | **Paper checked:** Table 3 (arXiv:1805.01580) gives δ = 0.01610 ± 0.00027 with no unit, i.e. a fraction; Rp/R★ = 0.1269, and 0.1269² = 0.01610 | 1.610 % |
| HD 189733 b (Morello et al. 2014, ApJ 786, 22) | `ps` | `pl_trandep` = 0.02413 % | **Paper checked:** Table 3 (arXiv:1403.2874) gives p² = 0.02413 ± 0.00003, dimensionless, with p = 0.15534 | 2.413 % |
| K2-114 b (Ikwut-Ukwa et al. 2020, AJ 160, 209) | `ps` | `pl_trandep` = 0.01352 % | **Paper checked:** Table 3 (arXiv:2007.00678) labels δ "Transit depth (fraction)" = 0.01352; Rp/R★ = 0.1163 | 1.352 % |
| TOI-5624 c (Bonfanti et al. 2026, A&A 709, A265) | `ps` and `pscomppars` | `pl_trandep` = 0.762 % | **Paper checked:** Table 2 (arXiv:2604.15035) gives dF = 762 ppm, defined as (Rp/R★)², with Rp/R★ = 0.02760 (0.02760² = 7.62 × 10⁻⁴). 762 ppm is 0.0762 %. Planets b, d and e of the same paper (667, 1599 and 1312 ppm) are stored correctly, so this is a one-row decimal slip | 0.0762 % |
| TOI-1478 b (Rice et al. 2022, AJ 164, 104) | `ps` and `pscomppars` | `pl_trandep` = 0.10936 % | **Paper checked:** Table 3 (arXiv:2207.06511) gives δ_TESS = 10.936 (+0.10/−0.087) with no unit, next to Rp/R★ = 0.1020. Since 0.1020² = 0.0104, the 10.936 is in parts per thousand, i.e. 1.0936 %. The stored value is 10 times too small | 1.0936 % |
| TOI-2049 b (Guenther et al. 2026) | `ps` and `pscomppars` | `pl_ratror` = 1.49 | The row's own Rp and R★ give 0.0477, and its stored depth (0.2275 %) equals 0.0477² × 100. The stored 1.49 matches the planet's radius in Jupiter radii (1.485), so the radius looks to have been entered in the ratio column. The paper is not on arXiv (arXiv API search for "TOI-2049", 2026-10-14) | 0.0477 (paper not yet public) |

In the three fraction cases the papers give the depth as a fraction, and the Archive stored that number unchanged in a column documented in percent. TOI-5624 c is a single decimal slip. TOI-1478 b's paper prints its depth without a unit, and it was read as hundredths instead of thousandths. These are ingestion slips, not errors in the papers.

## 3. Numbers that are wrong in the source paper itself

**Status: each checked against the paper's own other numbers on 2026-10-14 (arXiv HTML versions; Soto et al. 2018 also in the published MNRAS version). No erratum was found for any of the first six (web searches, 2026-10-14); the errata of the second group are being checked by the errata watcher (section 8). The Archive copied these values faithfully, so the fix belongs with the authors and the Archive together.**

In each case two or more independent routes through the same paper's own numbers agree with each other and disagree with the printed value.

### 3a. A single printed value

| planet (reference) | Archive column, stored value | printed in the paper | the same paper's other numbers give | factor |
|---|---|---|---|---|
| K2-237 b (Soto et al. 2018, MNRAS 478, 5356) | `st_dens` 0.144 g/cm³ | Table 1: ρ★ = 0.102 ρ☉ | M/R³ = 1.28/1.43³ = 0.438 ρ☉; a/R★ = 5.50 at P = 2.18 d → 0.47 ρ☉ | 4.3–4.6 |
| K2-238 b (same) | `st_dens` 0.0775 g/cm³ | Table 1: ρ★ = 0.0550 ρ☉ | M/R³ = 1.19/1.59³ = 0.296 ρ☉; a/R★ = 6.27 at P = 3.20 d → 0.32 ρ☉ | 5.4–5.9 |
| G 9-40 b (Luque et al. 2022, A&A; arXiv:2208.07287) | `st_dens` 1.62 g/cm³ | Table 3: ρ★ = 1.62 ± 0.11 g cm⁻³ (prior 𝒩(1.5, 0.15)) | Table 1 M/R³ = 0.2952/0.3026³ = 10.65 ρ☉ = 15.0 g/cm³; Table 4 a/R★ = 30.46 at P = 5.746 d → 3π(a/R★)³/(GP²) = 16.2 g/cm³ | 10 (decimal) |
| GJ 3929 b (Beard et al. 2022, ApJ 936, 55; arXiv:2207.10672) | `pl_ratror` 0.0156 | Table 5: Rp/R★ = 0.0156 ± 0.0003 | Table 5 Rp = 1.09 R⊕ and Table 2 R★ = 0.32 R☉ → 1.09/(0.32 × 109.08) = 0.0312 | 2.0 |
| TOI-908 b (Hawthorn et al. 2023, MNRAS 524, 3877; arXiv:2306.09758) | `pl_insol` 80.884 S⊕ | Table 5: S = 80.884 ± 0.006 S⊕ | Table 4 R★ = 1.028 R☉, Teff = 5626 K → L = 0.954 L☉; Table 5 a = 0.041657 au → S = 550 S⊕. Table 5's own Teq = 1317 ± 38 K (zero albedo) needs S ≈ 500; S = 80.9 would give 835 K | 6.8 |
| TOI-1694 c (Polanski et al. 2024, ApJS; arXiv:2405.14786) | `pl_orbsmax` 0.1 au | Table 4: a = 0.1 ± 0.02 au | Table 5 P = 393.1 d; Kepler's third law with the row's stellar mass gives 0.996 au (planet b of the same star is listed at 0.045 au for P = 3.77 d) | 10 |

**Notes on each.**
- **Soto et al. 2018:** for K2-237, M/(4/3 π R³) = 0.104 is close to the printed 0.102, but the same formula gives 0.071 for K2-238, not 0.055, so the cause is not a single unit factor. The quoted ±0.0003 on K2-238's density is also implausibly small next to a ±10% radius. Affected Archive rows: five `ps` rows (K2-237 b: the Soto set and two Kokori et al. 2022/2023 sets that reuse its density; K2-238 b: the Soto set and one Kokori 2023 set) and the K2-238 b composite value.
- **G 9-40 b:** the fit was run in ρ★ instead of a/R★. The posterior a/R★ = 30.46 can only come from ρ★ ≈ 16 g/cm³, so the fit itself almost certainly used the right density and the table prints it (and its prior) a factor of 10 too small. Affected: the `ps` row and the composite `st_dens`.
- **GJ 3929 b:** the printed value is half the consistent one; the cause is not known. Affected: the `ps` row and the composite `pl_ratror`. The earlier Kemmer et al. 2022 set (Rp = 1.150 R⊕, R★ = 0.315 R☉) implies 0.0335.
- **TOI-908 b:** the ±0.006 uncertainty (0.007%) is also implausibly small. Affected: the `ps` row and the composite `pl_insol`.
- **TOI-1694 c:** one significant figure where a ≈ 1.0 au is needed, most likely a dropped digit. Affected: one `ps` row (not the default set).

### 3b. Orbits and stars whose printed parameters do not fit together (new, 2026-10-14)

The audit flagged these as Kepler's-law, transit-density, insolation or log g mismatches in **default** parameter sets whose planet and star values come from one paper. Each was read in the paper.

| planet(s) (reference) | Archive column, stored value | what the paper prints | what the same paper's other numbers give | factor |
|---|---|---|---|---|
| TOI-262 b (Oddo et al. 2023; arXiv:2301.08162) | `pl_orbsmax` 0.163 au | Table 14: a = 0.163 ± 0.002 au, a/R★ = 41.211 ± 8.024, Teq = 584 ± 45 K | Table 14 M★ = 0.913 M☉ and P = 11.14529 d → Kepler's law a = 0.0947 au, i.e. a/R★ = 23.9 with R★ = 0.853 R☉. The printed a is a/R★ × R★ (41.211 × 0.853 R☉ = 0.1635 au), and the printed Teq is Teff·√(R★/2a) with the same a/R★. With the Kepler a, Teq ≈ 768 K | 1.72 in a; 5.1 in implied ρ★ |
| K2-285 b, c, d, e (Palle et al. 2019, A&A; arXiv:1808.00575) | `pl_orbsmax` 0.0824, 0.1178, 0.18041 au (c, d, e) | Table 3: a/R★ = 10.43, 22.51, 32.20, 49.43 and a = 0.03817, 0.0824, 0.1178, 0.18041 au, with e fixed at 0 | Table 1 M★ = 0.830 M☉ → Kepler a = 0.0422, 0.0682, 0.0879, 0.1107 au. The printed a equal a/R★ × R★ (R★ = 0.787 R☉). One star cannot have four densities: the four a/R★ imply ρ★ = 1.78, 4.2, 5.8 and 10.5 g/cm³, while Table 1's M/R³ gives 2.40 g/cm³ and Table 3's light-curve density is 1.782 | 0.90, 1.21, 1.34, 1.63 in a |
| TOI-3862 b (Carleo et al. 2026; arXiv:2601.10450) | `pl_ratdor` 8.848 | Table 5: a/R★ = 8.848 (+0.074/−0.070), a = 0.02539 au, e = 0.0232 | Table 5 a = 0.02539 au (which is Kepler's law with Table 4 M★ = 0.90 M☉) over Table 4 R★ = 0.92 R☉ gives a/R★ = 5.93. The printed a/R★ implies ρ★ ≈ 5.4 g/cm³ against 1.6 g/cm³ from M/R³; e = 0.023 cannot bridge a factor of 3.3 | 1.49 in a/R★; 3.3 in ρ★ |
| GJ 3323 b, c (Astudillo-Defru et al. 2017, A&A; arXiv:1703.05386) | `st_rad` 0.119 R☉ (and `pl_insol` 2.58, 0.17 S⊕) | Table 1: M★ = 0.164 M☉, R★ = 0.119 ± 0.027 R☉, Teff = 3159 K, L = 0.0027 L☉; Table 4: S = 2.58 and 0.17 S⊕ (text: 2.51 and 0.17) | R★ and Teff give L = R★²(Teff/5772)⁴ = 0.00127 L☉, half the printed L; the insolations follow the printed L (0.0027/0.03282² = 2.51). R★ = 0.119 with M★ = 0.164 also means ρ★ ≈ 97 ρ☉ (137 g/cm³), far denser than a 0.16 M☉ M dwarf (whose radius is usually near 0.18–0.20 R☉). So R★ is the value that does not fit | 2.1 in L |
| GJ 887 b, c, d, e (Hartogh et al. 2026, A&A; arXiv:2602.08929) | `st_logg` 4.156 | Table 1: log g = 4.156 (+0.040/−0.038), taken from Gaia DR3; M★ = 0.495 M☉ and R★ = 0.468 R☉ from Mann et al. 2015 | M★/R★² gives log g = 4.79 for this early-M dwarf. The tabulated log g is 0.64 dex (a factor of 4.3 in g) lower than the same table's mass and radius allow, with a quoted error of ±0.04 | 0.64 dex |

**Notes.**
- **TOI-262 b:** the paper itself warns that a/R★ and the inclination are poorly constrained (impact parameter b ≥ 0.7, a/R★ ± 8). But the derived a is quoted as ±0.002 au, as if it came from Kepler's law, and it is the default `pl_orbsmax` in the Archive. Anyone computing insolation from it gets about 3 times too little.
- **K2-285:** each planet's a/R★ was fitted on its own, and a in au was then computed from it. For planet e the stored a puts the planet 63% farther out than Kepler's law allows for this star. Affected: the default `pl_orbsmax` (and `pl_ratdor`) of all four planets.
- **TOI-3862 b:** the transit duration and inclination in the paper agree with the printed a/R★, so the light curve itself prefers a denser star (or a higher impact parameter) than the adopted stellar parameters. The paper does not discuss the mismatch. Affected: the default `pl_ratdor`.
- **GJ 3323:** the radius is cited from Boyajian et al. 2012. The printed luminosity uncertainty (±0.0066 on 0.0027) is also larger than the value. Affected: the default `st_rad` and anything derived from it.
- **GJ 887:** the paper takes log g from Gaia DR3 while its mass and radius come from Mann et al. 2015, and the two disagree. Affected: the default `st_logg` of all four planets.

**Why it is worth knowing.** Each printed value would mislead a user who takes it at face value: G 9-40 b's density implies a/R★ ≈ 14 rather than 30; TOI-908 b would look like a warm planet (835 K) rather than a hot Neptune-desert planet (~1,350 K); GJ 3929 b's radius ratio implies a 0.54 R⊕ planet; Soto's densities imply large eccentricities for near-circular orbits; TOI-262 b and K2-285 e would be placed far outside their real orbits.

## 4. A different quantity stored in the stellar-density column: Kepler-419 (Dawson et al. 2014)

**Status: checked against the paper (arXiv:1405.5229, ApJ 791, 89) on 2026-10-14.**

The Archive's `st_dens` for Kepler-419 from Dawson et al. 2014 is **13.34 g/cm³**, 36 times the 0.37 g/cm³ that the row's own mass and radius give. The paper's Table 2 lists "Light curves stellar density, ρ_circ [ρ⊙]" = **9.47** (+0.13/−0.14), and 9.47 × 1.4098 = 13.35 g/cm³. ρ_circ is the density a transit fit returns if the orbit is *assumed circular*. Dawson et al. use it precisely because it differs from the true density for an eccentric orbit: Kepler-419 b has e = 0.83, and their density-ratio parameter g = (ρ_circ/ρ★)^(1/3) = 3.0. The star's own density in the same paper is ρ★ = 0.36 (+0.14/−0.10) ρ☉ (Table 1), i.e. **0.51 g/cm³**.

So the Archive stored the light-curve quantity, converted to g/cm³, in the column for the star's density. Affected: the `ps` rows for Kepler-419 b and c from Dawson et al. 2014, and the composite `st_dens` of both planets. (The Kepler DR25 KOI row, 13.69 g/cm³, is the pipeline's circular-orbit fit density and is labelled `pipeline` as expected.) A user comparing this `st_dens` with a transit density would see no sign of eccentricity at all for a transiting giant planet with e = 0.83.

## 5. A published erratum not applied: HD 48948 b, c and d (Dalal et al. 2024)

**Status: checked against the paper (MNRAS 531, 4464) and its erratum (MNRAS 534, 2410; doi:10.1093/mnras/stae2228) on 2026-10-14.**

The audit flagged the insolation of all three planets at the same factor, 3.19. The Archive holds `pl_insol` = 138.85, 15.50 and 2.46 S⊕, the values of the original paper's Table 3. The authors' erratum states that the incident flux and equilibrium temperatures "were incorrectly calculated due to a mathematical error" and gives **43.33 ± 2.41, 4.84 ± 0.27 and 0.77 ± 0.04** S⊕ (and Teq = 715, 413 and 261 K instead of 957, 553 and 349 K). The audit's prediction from the row's own stellar parameters and semi-major axes is 43.48, 4.86 and 0.772 S⊕, matching the erratum. Affected: three `ps` rows and three composite values of `pl_insol`, and very likely `pl_eqt` as well (not tested by the audit). HD 48948 d is described as a habitable-zone candidate, so its insolation (0.77, not 2.46 S⊕) matters.

## 6. Placeholders stored as measurements: log g = 4.50 in Stassun et al. 2017 (new, 2026-10-14)

**Status: checked against the paper (Stassun, Collins & Gaudi 2017, AJ 153, 136; arXiv:1609.04389, Tables 5 and 6) on 2026-10-14. An Archive-wide census of the same pattern is queued (`placeholder_census.py`).**

The paper's input tables take Teff, log g and [Fe/H] from the PASTEL catalog. For 14 hosts they print **log g = 4.50 with no uncertainty and [Fe/H] = 0.00**, also with none: 4 of the roughly 130 transiting hosts (GJ 436, KELT-7, KELT-2 A, WASP-33) and 10 of the roughly 240 radial-velocity hosts (GJ 328, GJ 176, HD 79498, GJ 649, HD 67087, HD 16760, HD 106270, GJ 581, GJ 876, HD 1666). The same round pair for stars as different as the M dwarf GJ 876 and the F-type subgiant KELT-2 A points to defaults that stood in for missing values, not to measurements. The Archive holds them as measured log g:

| planet | Archive tables | stored `st_logg` | log g from the same row's M★ and R★ | difference |
|---|---|---|---|---|
| KELT-2 A b | `ps` (default) and `pscomppars` | 4.50 | 4.05 | +0.45 dex |
| KELT-7 b | `ps` (two sets) and `pscomppars` | 4.50 | 4.17 | +0.33 dex |
| WASP-33 b | `ps` | 4.50 | 4.32 | +0.18 dex |
| WASP-56 b | `ps` (default) and `pscomppars` | 4.50 (no error; [Fe/H] 0.12) | 4.32 | +0.18 dex |

For the transiting hosts the paper derives the stellar mass from the transit density, not from log g, so its masses are unaffected. For radial-velocity hosts the paper computes the mass "from our R★ and the spectroscopic log g", so wherever one of these placeholders was used, the derived mass would be off as well. Whether the Archive holds such masses is what the census checks.

## 7. What looked like errors but is physics, or a coincidence

- **Circumbinary planets** (Kepler-34, -35, -47, -413, -1647, TIC 172900988) fail Kepler's third law against the primary's mass alone. The correct mass is the binary's, so they are skipped (`cb_flag` = 1).
- **The Kepler KOI pipeline tables** account for most flags on a/R★ and depth. There a/R★ is a free transit-fit parameter, and limb darkening makes depths about 1.18 × (Rp/R★)². They are labelled `pipeline` and kept out of the "strongest flags" lists.
- **White-dwarf hosts** (WD 1856+534 b, ZTF J1828+2308 b and others): the planet is larger than the star, so neither depth = (Rp/R*)² nor the transit-density formula applies.
- **Eccentric orbits the paper itself reports (checked 2026-10-14):** K2-174 b (Livingston et al. 2019, arXiv:1901.05855): a/R★ = 26.6 against 40 from the star; the paper reports its light-curve density as "∼10σ discrepant" with ρ★ = 3.21 g/cm³ and reads it as a sign of eccentricity. Kepler-210 b (Ioannidis et al. 2014, arXiv:1403.3238): the paper finds that the stellar parameters implied by each planet disagree and proposes significant eccentricities.
- **Grazing transits (checked 2026-10-14):** TOI-1855 b (Schulte et al. 2024, arXiv:2401.05923: b = 1.024, so depth < (Rp/R★)² as expected); TOI-2193 A b and TOI-3540 A b (Yee et al. 2022, arXiv:2205.09728: radii are 95% lower limits, and the printed density is the mode of its own skewed posterior, which need not equal mass/radius³ of the other modes).
- **0.2.0 also gave its 1.41 label** to four log g and insolation offsets (Leleu et al. 2024, Moutou et al. 2015, Tuomi et al. 2013, and Torres et al. 2017 insolation). A density unit cannot explain a log g or insolation offset, so those labels were coincidences. In 0.3.0 each unit factor applies only to the checks it can explain. The log g offsets (Leleu et al. 2024: −0.16 dex over 6 rows; Leleu et al. 2021: −0.17 dex over 8 rows) are the size of the usual gap between spectroscopic and mass-radius log g, so they are not treated as errors. The offsets stay listed in `systematics.csv`.

## 8. In progress: an errata watcher

HD 48948 (section 5) shows that a published erratum can leave the Archive unchanged. `errata_watch.py` (queued) harvests every erratum, correction and corrigendum from Crossref for AJ, ApJ, ApJL, ApJS, MNRAS, A&A and PASP. It finds the paper each one corrects (from the citation in AAS erratum titles, otherwise by title lookup) and matches it to the bibcodes behind the Archive's parameter sets. It then lists every Archive reference with a published erratum whose rows were last updated before the erratum appeared. Each candidate will be read by hand before anything is claimed. No earlier list of this kind was found (searches on 2026-10-14).

## Next

1. Read 0.3.0's `unit_groups.csv`: the rows behind each reference, the exact count of composite values affected, and the journal column units from the CDS ReadMe files.
2. Items 1 and 2 are going to the Archive helpdesk as one batched note. Record its reply here. Items 2 (TOI-5624 c, TOI-1478 b), 3, 4, 5 and 6 go in one short follow-up once the Archive replies.
3. Check TOI-2049 b against its paper once it is public.
4. Read the errata-watch and placeholder-census results and hand-check their top candidates.
5. Keep working down the "strongest flags" list (`report.md`): K2-43 b and c (Hedges et al. 2019), Kepler-53 c, OGLE2-TR-L9 b, TOI-128.01, TOI-4602.01, HATS-62 b, Kepler-1704 b, HD 10442 b.
