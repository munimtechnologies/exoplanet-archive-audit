# exoplanet-archive-audit

A physical self-consistency audit of the [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/). It reads every parameter set in the Planetary Systems table (`ps`, about 40,000 rows) and the composite table (`pscomppars`), then tests relations that must hold *within one solution*:

| check | relation |
|---|---|
| `kepler3_a` | a³ = (M★ + Mp)·P² (skipped for circumbinary, microlensing and imaging planets) |
| `bulk_density` | ρp = 5.514 g/cm³ · Mp/Rp³ (Earth units) |
| `a_over_rstar` | a/R★ = a[au] · 215.03 / R★ (near-circular orbits) |
| `rp_over_rstar` | Rp/R★ = Rp / (109.08 · R★) |
| `depth_vs_k2` | depth[%] ≈ 100·(Rp/R★)², within 0.6–1.6× (limb darkening, grazing) |
| `rhostar_transit_vs_MR` | 3π(a/R★)³/(GP²) = 1.4098 g/cm³ · M★/R★³ |
| `st_dens_vs_MR` | `st_dens` = 1.4098 g/cm³ · M★/R★³ |
| `logg_vs_MR` | log g = 4.438 + log M★ − 2 log R★ |
| `insolation` | S = R★²(Teff/5772)⁴/a² |

A row is flagged when the mismatch exceeds a physical tolerance **and** the quoted uncertainties (3σ) when the row gives them. Mismatches equal to a common unit factor (100, 10⁴, 317.8, 11.21, 109.1, 9.73, 215, 24, 1.41) are labelled as likely unit slips.

**Per-reference systematics (v0.2).** When most rows from one reference share the same offset, that points to the catalog rather than to scatter. `systematics.csv` lists every reference with at least 5 tested rows whose median ratio is more than 10% from 1, with at least half of its rows within 10% of that median. It also gives the unit factor that would explain the offset and the median once that factor is removed. In `pscomppars`, each value is charged to its own source through the `*_reflink` columns.

## Findings

See [FINDINGS.md](FINDINGS.md). In short, the stellar densities stored for Fulton & Petigura (2018) appear to be in solar units (ρ/ρ☉) although the Archive documents `st_dens` in g/cm³. The paper's own table carries the same "g/cc" label over solar-unit values. Four single-row inconsistencies are also self-evident from other columns of the same row. Every flag is a **candidate** until it is checked against the source paper.

## Run it

Python 3.9+, standard library only.

```
python -m unittest -v test_exo_audit
python exo_audit.py --out-dir out --data-dir cache
```

It downloads two TAP queries (a few tens of MB) and writes `out/report.md`, `out/flags.csv`, `out/systematics.csv`, `out/by_reference.csv` and `out/summary.json`. `--offline FILE` audits a local `ps`-format CSV instead.

## Results

- `results/2026-10-14-v0.1/`: the first full run (v0.1: 40,336 `ps` rows and 6,445 `pscomppars` rows, 17,675 flags). About 11,400 of those flags come from the Kepler KOI pipeline tables, where a/R★ and stellar density are free transit-fit parameters. v0.2 marks those catalogs as `pipeline`.

## Limits

- Eccentric orbits (e > 0.1) are skipped for a/R★ and the transit density. Grazing transits, limb darkening, white-dwarf hosts and planets larger than their star are not modelled.
- Some Archive values are computed by the Archive rather than taken from the paper, so a flag can point to either.
- A flag is a lead, not an error report. Nothing is reported to the Archive until it has been checked against the paper.

## Prior art

arXiv:2605.10427 (2026) tested Kepler's third law on the Archive's default parameters and found five outliers. This audit differs in four ways. It covers every solution row rather than only the defaults. It tests nine relations, not one. It separates rows whose planet and star values come from one reference, which cannot be blamed on mixing sources. And it looks for offsets shared across a whole reference, which is how the Fulton & Petigura density units showed up.

## About

By MV2 of Munim, Inc. (munimversion2@gmail.com). This code and write-up were made with AI agents working in his name, and every number comes from the code in this repository. Code: Apache-2.0 (see LICENSE). Findings and results text: CC BY 4.0. The data are from the NASA Exoplanet Archive, which is operated by Caltech under contract with NASA. This research has made use of the NASA Exoplanet Archive.
