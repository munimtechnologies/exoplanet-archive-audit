# Findings so far (2026-10-14)

By MV2 of Munim, Inc. The code, checks and this write-up were made with AI agents working in his name. Each claim below is labelled with how far it has been verified. Text: CC BY 4.0. Code: Apache-2.0.

## 1. Fulton & Petigura (2018) stellar densities in the Archive appear to be in solar units, not g/cm³

**Status: verified by hand on the rows quoted here. The full row count and median offset come from the v0.2 run (`systematics.csv`), which is still pending.**

The NASA Exoplanet Archive documents `st_dens` as "Stellar Density [g/cm**3]" ([column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)). For the parameter sets whose reference is Fulton & Petigura 2018 (CKS VII, AJ 156, 264; [arXiv:1805.01453](https://arxiv.org/abs/1805.01453)), the stored values match M/R³ in **solar units** (ρ☉ = 1.41 g/cm³). They are about 1.41 times too small for g/cm³.

**The source table.** Table 2 of the arXiv version labels ρ_iso "g/cc", but each value equals M_iso / R_iso³ in solar units:

| KOI | M_iso (M☉) | R_iso (R☉) | M/R³ (ρ☉) | same in g/cm³ | listed ρ_iso |
|---|---|---|---|---|---|
| K00001 | 0.99 | 1.04 | 0.880 | 1.24 | 0.87 |
| K00002 | 1.51 | 1.96 | 0.200 | 0.28 | 0.20 |
| K00006 | 1.20 | 1.28 | 0.572 | 0.81 | 0.57 |
| K00008 | 1.00 | 0.93 | 1.243 | 1.75 | 1.23 |

**The Archive rows.** Below are the first eleven host stars, in file order, with `st_dens_vs_MR` flags that the v0.1 run (2026-10-14, full `ps` table over TAP) raised on rows whose reference is Fulton & Petigura 2018, with the audit's own computed numbers. In g/cm³ the observed/predicted ratio runs from 0.60 to 0.73. With M/R³ in solar units, nine of the eleven agree within 3%:

| planet | `st_dens` in the Archive | 1.41·M/R³ (g/cm³) | ratio | M/R³ (ρ☉) | Archive / (M/R³ in ρ☉) |
|---|---|---|---|---|---|
| Kepler-6 b | 0.56 | 0.766 | 0.73 | 0.544 | 1.03 |
| Kepler-491 b | 1.11 | 1.545 | 0.72 | 1.096 | 1.01 |
| Kepler-257 b | 1.63 | 2.513 | 0.65 | 1.782 | 0.91 |
| Kepler-222 d | 1.57 | 2.559 | 0.61 | 1.815 | 0.86 |
| Kepler-179 b | 1.64 | 2.275 | 0.72 | 1.614 | 1.02 |
| Kepler-165 c | 1.89 | 2.617 | 0.72 | 1.856 | 1.02 |
| Kepler-20 c | 1.36 | 1.949 | 0.70 | 1.382 | 0.98 |
| Kepler-166 d | 1.75 | 2.495 | 0.70 | 1.770 | 0.99 |
| Kepler-197 d | 0.55 | 0.768 | 0.72 | 0.545 | 1.01 |
| Kepler-184 d | 1.59 | 2.221 | 0.72 | 1.576 | 1.01 |
| Kepler-229 b | 1.94 | 3.237 | 0.60 | 2.296 | 0.84 |

**The audit.** v0.1 listed only rows past its tolerance (10% and 3σ), so the table above is a selected sample. v0.2 measures the median ratio over every tested row of each reference, so a factor shared by a whole catalog shows up as one line, along with the median once the unit is fixed.

**Why it matters.** Comparing the stellar density from a transit fit with an independent stellar density is a standard way to constrain orbital eccentricity (the "photo-eccentric" effect). A density that is 1.41 times too low mimics ((1 + e sin ω)/√(1 − e²))³ = 1.41, which means e ≈ 0.11–0.12 at ω = 90°, for an orbit that may be circular.

**Prior art.** Searches found no erratum for the paper, no Archive notice and no published report of this mismatch. An Archive-wide check of Kepler's third law on default parameters (arXiv:2605.10427) did not test stellar densities.

**Limits.** Only the arXiv version of the paper was read, so the published AJ table may already carry a corrected label. Some rows also differ from M/R³ in solar units by up to about 15%, possibly because the Archive pairs ρ_iso with a radius other than R_iso. The v0.2 numbers will show how large that scatter is.

## 2. Single-row unit slips that the Archive's own columns expose

**Status: each is self-evident from other columns of the same row. None has yet been checked against the paper.**

- **HAT-P-25 b (Wang et al. 2018):** `pl_trandep` = 0.0161 (%), while the same row's (Rp/R*)² = 1.61%. This is a fraction stored in a percent column.
- **HD 189733 b (Morello et al. 2014):** `pl_trandep` = 0.02413 (%), against (Rp/R*)² = 2.41%. The same slip.
- **TOI-2049 b (Guenther et al. 2026):** `pl_ratror` = 1.49, while the same row's Rp and R* give 0.048. A ratio above 1 is impossible for this star, so a value from another column is the likely cause (unconfirmed).
- **TOI-5624 c (Bonfanti et al. 2026):** the depth is 10× (Rp/R*)²; which of the two values is wrong is not yet known.

## 3. What looked like errors but is physics (so v0.2 handles it)

- **Circumbinary planets** (Kepler-34, -35, -47, -413, -1647, TIC 172900988) fail Kepler's third law against the primary's mass alone. The correct mass is the binary's, so v0.2 skips rows with `cb_flag` = 1.
- **The Kepler KOI pipeline tables** account for about 11,400 of the 17,675 v0.1 flags, many of them on a/R*. In those tables a/R* is a free transit-fit parameter, often stored without uncertainties, and it is poorly constrained for small planets. v0.2 labels these catalogs `pipeline` and keeps them out of the "strongest flags" lists.
- **White-dwarf hosts** (WD 1856+534 b, ZTF J1828+2308 b and others): the planet is larger than the star, so neither depth = (Rp/R*)² nor the transit-density formula applies.

## Next

1. Read the v0.2 `systematics.csv`: the row count and median ratio for Fulton & Petigura 2018, and any other catalogs with a shared offset.
2. Check the strongest non-pipeline single-row flags against their papers.
3. Send one batched, polite note to the Archive helpdesk with the confirmed items.
