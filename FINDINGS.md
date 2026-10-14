# Findings so far (2026-10-14)

By MV2 of Munim, Inc. The code, checks and this write-up were made with AI agents working in his name. Each claim below is labelled with how far it has been verified. Every count comes from the 0.2.0 run on the 2026-10-14T14:00Z download (`results/2026-10-14-v0.2/`). Text: CC BY 4.0. Code: Apache-2.0.

## 1. Stellar densities from four references are stored in solar units, while the Archive documents g/cm³

**Status: verified, both across every row and against each source paper's own text or tables. 0.3.0 adds a row-by-row file with ADS bibcodes (`unit_groups.csv`) and the exact count of composite (default) values affected. That run is queued.**

The Archive documents `st_dens` as "Stellar Density [g/cm**3]" ([column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)). For every parameter set it holds, the audit compares `st_dens` with 1.4098 g/cm³ · M★/R★³, using the star mass and radius of the same row. If a reference's densities were really in g/cm³, the median ratio would be close to 1. For four references the median is close to 1/1.4098 = 0.709, which is what you get when the densities are in solar units (ρ/ρ☉). Once they are multiplied by 1.4098, the median comes back to 1:

| reference | table | rows | median ratio | rows within 10% of median | median after ×1.4098 | what the source paper says |
|---|---|---|---|---|---|---|
| Fulton & Petigura 2018 (CKS VII, AJ 156, 264) | `ps` | 1,414 | 0.7163 | 92.5% | 1.01 | Table 2 (arXiv:1805.01453) labels ρ_iso "g/cc", but its values equal M/R³ in solar units (K00001: 0.99/1.04³ = 0.88, listed as 0.87) |
| Torres et al. 2017 (AJ 154, 264) | `ps` | 22 | 0.7025 | 90.9% | 0.990 | Table 6 (arXiv:1711.01267) gives ρ★ in **(ρ☉)**. Its Table 8 gives a transit density in g cm⁻³ |
| Mann et al. 2017 | `ps` | 19 | 0.7099 | 68.4% | 1.001 | ZEIT IV (Praesepe, arXiv:1609.00726), Table 2: "ρ∗ (ρ⊙)" for seven stars. Which Mann et al. 2017 paper(s) the 19 rows cite is checked by bibcode in 0.3.0 |
| Mann et al. 2017 | `pscomppars` | 7 | 0.7184 | 71.4% | 1.013 | (same) |
| MacDonald et al. 2016 (Kepler-80, AJ 152, 105) | `ps` | 11 | 0.7056 | 100% | 0.995 | Text (arXiv:1607.07540, §III): "ρ = 2.33 ± 0.15 ρ⊙", which equals 0.730/0.678³ in solar units. Table 2 prints the same 2.33 with the unit "g cm-3" |
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

## 2. Single rows whose own columns disagree

**Status: each is self-evident from other columns of the same row. None has yet been checked against the paper.**

- **HAT-P-25 b (Wang et al. 2018):** `pl_trandep` = 0.0161 (%), while the same row's (Rp/R*)² = 1.61%. This is a fraction stored in a percent column.
- **HD 189733 b (Morello et al. 2014):** `pl_trandep` = 0.02413 (%), against (Rp/R*)² = 2.41%. The same slip.
- **K2-114 b (Ikwut-Ukwa et al. 2020):** `pl_trandep` = 0.01352 (%), against (Rp/R*)² = 1.35%. The same slip.
- **TOI-2049 b (Guenther et al. 2026):** `pl_ratror` = 1.49, while the same row's Rp and R* give 0.048. A ratio above 1 is impossible for this star.
- **TOI-5624 c (Bonfanti et al. 2026):** the depth is 10× (Rp/R*)². That fits a depth in parts per thousand stored as percent; 0.3.0 labels this pattern.

## 3. What looked like errors but is physics, or a coincidence

- **Circumbinary planets** (Kepler-34, -35, -47, -413, -1647, TIC 172900988) fail Kepler's third law against the primary's mass alone. The correct mass is the binary's, so they are skipped (`cb_flag` = 1).
- **The Kepler KOI pipeline tables** account for most flags on a/R★ and depth. There a/R★ is a free transit-fit parameter, and limb darkening makes depths about 1.18 × (Rp/R★)². They are labelled `pipeline` and kept out of the "strongest flags" lists.
- **White-dwarf hosts** (WD 1856+534 b, ZTF J1828+2308 b and others): the planet is larger than the star, so neither depth = (Rp/R*)² nor the transit-density formula applies.
- **0.2.0 also gave its 1.41 label** to four log g and insolation offsets (Leleu et al. 2024, Moutou et al. 2015, Tuomi et al. 2013, and Torres et al. 2017 insolation). A density unit cannot explain a log g or insolation offset, so those labels were coincidences. In 0.3.0 each unit factor applies only to the checks it can explain. The offsets themselves stay listed in `systematics.csv` as leads.

## Next

1. Read 0.3.0's `unit_groups.csv`: the bibcodes behind each reference, the exact count of composite values affected, and the journal column units from the CDS ReadMe files.
2. Send one batched, polite note to the Archive helpdesk with item 1 and the item 2 rows.
3. Check the remaining single-row flags against their papers.
