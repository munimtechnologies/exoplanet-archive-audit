# Correction: Lissauer et al. 2024 already reject our three "stale CANDIDATE" KOIs

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Text CC BY 4.0. This note corrects the novelty claims in findings/2026-10-17-koi-dupes-results.md,
findings/2026-10-17-orphan-pixels-results.md and findings/2026-10-17-orphan-census-prereg.md. Those notes
stay as published.

## What we found

Lissauer et al. 2024 ("Updated Catalog of Kepler Planet Candidates: Focus on Accuracy and Orbital Periods",
PSJ 5, 152, CC BY 4.0) publish a machine-readable Table 1 with a disposition for every KOI. It is at
https://content.cld.iop.org/journals/2632-3338/5/6/152/revision3/psjad0e6et1_mrt.txt (about 7 MB; it is
not on the arXiv HTML page we read before). Its Status column gives four letters: this work, DR25
supplemental, DR25, DR24 (P candidate, F false positive or false alarm, S rejected because S/N < 7.1,
N not in that catalogue).

The rows for our three leads, read on 2026-10-17:

| KOI | KIC | Lissauer period (d) | Lissauer S/N | Status | meaning |
|---|---|---|---|---|---|
| 1101.02 | 3245969 | 11.39114826 | 0.0 | FPNN | false positive in Lissauer 2024 |
| 1922.02 | 9411166 | 15.09681793 | 4.1 | SPNN | rejected, S/N < 7.1 |
| 2167.02 | 6041734 | 6.95745228 | 1.9 | SPNN | rejected, S/N < 7.1 |

Their siblings are PPPP: 1101.01 (Kepler-768 b, 11.39116273 d), 1922.03 (Kepler-1016 c, 105.65509204 d),
2167.03 (Kepler-1129 c, 76.53773375 d).

## What this changes

- **Disposition: a replication, not a discovery.** A peer-reviewed catalogue already rejected all three
  KOIs. Our koi-dupes note said web searches found no note calling them duplicates or aliases. That
  stays true of the reason, but the rejection itself was published in 2024. We should have read Table 1
  before calling them stale finds.
- **Reason: possibly new, but stated with care.** Lissauer et al. give S/N < 7.1 for two of them and no
  per-KOI reason in the text. Our notes add a mechanism: K02167.02 at 1/11 of Kepler-1129 c's period,
  K01922.02 at 1/7 of Kepler-1016 c's, and K01101.02 a second listing of Kepler-768 b. With Lissauer's
  own periods the ratios are 11.0008 and 6.99850. A low S/N after a joint fit is what such an alias
  would give, because the sibling's transits are modelled by the sibling. We have not found this
  mechanism written down for these KOIs, so it is a small addition to their result, not a new
  disposition.
- **The Archive point stands.** On 2026-10-17 the NASA Exoplanet Archive's cumulative table still lists
  all three as CANDIDATE (parameters from Q1-Q16). The gap between the Archive and Lissauer et al. 2024
  is real and is what a helpdesk note should be about.
- **Kepler-289:** our 2026-10-16 note already credited Schmitt et al. 2014 and Lissauer et al. 2024 for
  KOI-1353.03 being a 5x alias of Kepler-289 d. The Archive still lists K01353.03 as Kepler-289 e at
  330.071558 d.

## Our period leads are not in Lissauer et al. 2024

The same table keeps our three period leads (findings/2026-10-17-pixels-results.md) at their catalogued
periods, as candidates:

| KOI | KIC | Lissauer period (d) | Lissauer S/N | Status | our reading |
|---|---|---|---|---|---|
| 2643.01 (Kepler-1301 b) | 6933567 | 9.08243105 | 15.8 | PPPP | 4.541 d (half) |
| 4711.01 | 8355131 | 4.36384369 | 10.3 | PPPP | 8.728 d (double) |
| 4893.01 | 11970050 | 6.58745561 | 8.2 | PPPP | 13.175 d (double) |

So those readings are not a replication of Lissauer et al. They are still unreviewed, and their error
bars are being re-checked (findings/2026-10-17-pixels-scatter-prereg.md). S/N values were read by
column position from the fixed-width file.

## Next

A full census joining the Archive's cumulative table to Lissauer Table 1 is pre-registered in
findings/2026-10-17-lissauer-xmatch-prereg.md (tool lissauer_xmatch 0.1.0). Before any further claim
about a single KOI, we look it up in Lissauer Table 1 first.
