# Findings so far (2026-10-14)

By MV2 of Munim, Inc. The code, checks and this write-up were made with AI agents working in his name. Each claim below is labelled with how far it has been verified. Every count comes from the 0.2.0 run on the 2026-10-14T14:00Z download (`results/2026-10-14-v0.2/`). Text: CC BY 4.0. Code: Apache-2.0.

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

**Status: each is evident from other columns of the same row. Four were checked against the source paper on 2026-10-14; the fifth (TOI-2049 b) has no public paper yet.**

| planet (reference) | tables | stored | what the paper or row says | likely correct value |
|---|---|---|---|---|
| HAT-P-25 b (Wang et al. 2018, PASP 130, 064401) | `ps` | `pl_trandep` = 0.0161 % | **Paper checked:** Table 3 (arXiv:1805.01580) gives δ = 0.01610 ± 0.00027 with no unit, i.e. a fraction; Rp/R★ = 0.1269, and 0.1269² = 0.01610 | 1.610 % |
| HD 189733 b (Morello et al. 2014, ApJ 786, 22) | `ps` | `pl_trandep` = 0.02413 % | **Paper checked:** Table 3 (arXiv:1403.2874) gives p² = 0.02413 ± 0.00003, dimensionless, with p = 0.15534 | 2.413 % |
| K2-114 b (Ikwut-Ukwa et al. 2020, AJ 160, 209) | `ps` | `pl_trandep` = 0.01352 % | **Paper checked:** Table 3 (arXiv:2007.00678) labels δ "Transit depth (fraction)" = 0.01352; Rp/R★ = 0.1163 | 1.352 % |
| TOI-5624 c (Bonfanti et al. 2026, A&A 709, A265) | `ps` and `pscomppars` | `pl_trandep` = 0.762 % | **Paper checked:** Table 2 (arXiv:2604.15035) gives dF = 762 ppm, defined as (Rp/R★)², with Rp/R★ = 0.02760 (0.02760² = 7.62 × 10⁻⁴). 762 ppm is 0.0762 %. Planets b, d and e of the same paper (667, 1599 and 1312 ppm) are stored correctly, so this is a one-row decimal slip | 0.0762 % |
| TOI-2049 b (Guenther et al. 2026) | `ps` and `pscomppars` | `pl_ratror` = 1.49 | The row's own Rp and R★ give 0.0477, and its stored depth (0.2275 %) equals 0.0477² × 100. The stored 1.49 matches the planet's radius in Jupiter radii (1.485), so the radius looks to have been entered in the ratio column. The paper is not on arXiv (arXiv API search for "TOI-2049", 2026-10-14) | 0.0477 (paper not yet public) |

In the three fraction cases the papers give the depth as a fraction, and the Archive stored that number unchanged in a column documented in percent. TOI-5624 c is a single decimal slip. These are ingestion slips, not errors in the papers.

## 3. Stellar densities that are wrong in the source paper itself: Soto et al. 2018 (K2-237, K2-238)

**Status: checked against both the arXiv version (arXiv:1801.07959) and the published MNRAS version (478, 5356; doi:10.1093/mnras/sty1334) on 2026-10-14. No erratum found.**

The audit flagged every `st_dens` value from Soto et al. 2018 (median ratio to M/R³: 0.23). Unlike finding 1, the Archive did nothing wrong. Table 1 of the paper gives "Density (ρ⊙)" = 0.102 for K2-237 and 0.0550 for K2-238. The Archive converted those correctly to g/cm³ (× 1.41 = 0.144 and 0.0775). The printed densities themselves disagree with the same paper's other numbers:

| star | Table 1 ρ★ (ρ☉) | M/R³ from Table 1 (ρ☉) | from the paper's fitted a/R★ and period (ρ☉) | factor |
|---|---|---|---|---|
| K2-237 (EPIC 229426032) | 0.102 | 1.28/1.43³ = 0.438 | a/R★ = 5.50, P = 2.18 d → 0.47 | 4.3–4.6 |
| K2-238 (EPIC 246067459) | 0.0550 (+0.0003/−0.0002) | 1.19/1.59³ = 0.296 | a/R★ = 6.27, P = 3.20 d → 0.32 | 5.4–5.9 |

The transit-based density is ρ★ = 3π (a/R★)³ / (G P²). Two independent routes from the paper's own numbers agree with each other and disagree with the printed density. The quoted ±0.0003 uncertainty on K2-238's density is also implausibly small next to a ±10% radius. The cause is not a single unit factor: for K2-237, M/(4/3 π R³) = 0.104 is close to the printed 0.102, but the same formula gives 0.071 for K2-238, not 0.055.

**Affected Archive rows:** five `ps` rows (K2-237 b: the Soto et al. 2018 set and two Kokori et al. 2022/2023 sets that reuse its stellar density; K2-238 b: the Soto set and one Kokori 2023 set) and the K2-238 b composite value (0.0775 g/cm³, about 0.42 expected).

**Why it is worth knowing.** A user comparing these densities with a transit fit would infer a large eccentricity for orbits the paper itself fits as near-circular.

## 4. What looked like errors but is physics, or a coincidence

- **Circumbinary planets** (Kepler-34, -35, -47, -413, -1647, TIC 172900988) fail Kepler's third law against the primary's mass alone. The correct mass is the binary's, so they are skipped (`cb_flag` = 1).
- **The Kepler KOI pipeline tables** account for most flags on a/R★ and depth. There a/R★ is a free transit-fit parameter, and limb darkening makes depths about 1.18 × (Rp/R★)². They are labelled `pipeline` and kept out of the "strongest flags" lists.
- **White-dwarf hosts** (WD 1856+534 b, ZTF J1828+2308 b and others): the planet is larger than the star, so neither depth = (Rp/R*)² nor the transit-density formula applies.
- **0.2.0 also gave its 1.41 label** to four log g and insolation offsets (Leleu et al. 2024, Moutou et al. 2015, Tuomi et al. 2013, and Torres et al. 2017 insolation). A density unit cannot explain a log g or insolation offset, so those labels were coincidences. In 0.3.0 each unit factor applies only to the checks it can explain. The log g offsets (Leleu et al. 2024: −0.16 dex over 6 rows; Leleu et al. 2021: −0.17 dex over 8 rows) are the size of the usual gap between spectroscopic and mass-radius log g, so they are not treated as errors. The offsets stay listed in `systematics.csv`.

## Next

1. Read 0.3.0's `unit_groups.csv`: the rows behind each reference, the exact count of composite values affected, and the journal column units from the CDS ReadMe files.
2. Items 1 and 2 were sent to the Archive helpdesk as one batched note (2026-10-14). Record its reply here. Items 2 (TOI-5624 c, now checked) and 3 will go in a short follow-up only if the Archive replies.
3. Check TOI-2049 b against its paper once it is public.
