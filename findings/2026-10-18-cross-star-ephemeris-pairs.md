# Three pairs of Kepler CANDIDATEs on stars 4-8 degrees apart share every transit

MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no human has checked this yet.
Text and data CC BY 4.0. Values from the NASA Exoplanet Archive TAP service (~01:00 UTC 2026-10-18) and
the papers cited; offsets and separations worked by hand and re-checked by the unit tests of
ephem_pairs 0.1.0 (this repository).

## Finding

While listing the 139 Archive CANDIDATEs with P > 400 d (`select ... from cumulative where
koi_disposition='CANDIDATE' and koi_period>400`), three pairs on **different stars** turned out to share
period and epoch:

| Pair | KOI (KIC) | Source of row | P (d) | T0 (BKJD) | Depth (ppm) | Dur (h) | SNR | Kp |
|---|---|---|---|---|---|---|---|---|
| A | K05660.01 (9363944) | Q1-Q16 | 402.20969 | 369.5086 | 472.5 | 5.30 | 9.5 | 13.66 |
| A | K08259.01 (5956171) | DR25, score 0.311 | 402.27493 | 369.6734 | 294.5 | 15.67 | 11.1 | 14.62 |
| B | K05935.01 (11818566) | Q1-Q16 | 416.87893 | 227.5107 | - | 4.45 | - | 15.69 |
| B | K05446.01 (7917068) | Q1-Q16 | 416.9504 | 227.392 | 479.8 | 4.03 | 6.9 | 12.69 |
| C | K07040.01 (8442795) | DR24 | 502.20642 | 162.9131 | 447.9 | 9.39 | 7.1 | 14.95 |
| C | K07932.01 (9278575) | DR25, score 0.230 | 502.25648 | 162.5842 | 153.2 | 14.84 | 8.1 | 13.34 |

Every event of each train inside Q1-Q17 lies within 0.37 d of an event of its partner:

| Pair | Events (BKJD, first member) | Largest offset | Separation | Brighter star's DR25 match radius |
|---|---|---|---|---|
| A | 369.51, 771.72, 1173.93, 1576.14 | 0.361 d | 7.75 deg | 116" |
| B | 227.51, 644.39, 1061.27, 1478.15 | 0.119 d | 7.30 deg | 168" |
| C | 162.91, 665.12, 1167.33 | 0.329 d | 3.86 deg | 128" |

All six are CANDIDATE in the Archive (all with `koi_disp_prov = q1_q17_dr25_sup_koi`, every FP flag 0,
including the ephemeris-match flag EC) and planet candidates ("P") in Lissauer et al. 2024 (arXiv 2311.00238)
Table 1.

## Why this is unlikely to be chance

Of the 139 long-period CANDIDATEs, 6 pairs on different stars have periods within 0.1 d of each other
(about what uniform periods give): the three above plus 425.59/425.65, 455.20/455.27 and 578.216/578.218 d,
whose epochs differ by 59, 56 and 74 d. For an unrelated pair, the chance that their epochs also agree
within 0.5 d is about 1 d / P ~ 1/450. Expected among 6: ~0.013; observed: 3. Poisson P(>= 3) ~ 4e-7.
This is a **post-hoc** estimate (the pattern was noticed first), so it is being re-tested on every KOI with
a pre-registered phase-shuffle null: findings/2026-10-18-ephem-pairs-prereg.md.

## Why the catalogues did not flag them

- **DR25 ephemeris matching** (Thompson et al. 2018, ApJS 235, 38, App. A.6) counts a match only if a
  contamination geometry allows it: separation <= 55 sqrt(1e6 10^(-0.4 Kp) + 1) arcsec (116-168" here),
  antipodal reflection about the field centre (none of the three pairs is antipodal: the mirrored positions
  miss by degrees), or column anomaly / video crosstalk on the same CCD module (a module is ~2.4 x 2.3 deg,
  so stars 3.9-7.8 deg apart cannot share one). A pair that fits no geometry is simply not a match.
- **The Skye metric** (same paper, A.3.7.4) flags individual transits that coincide with an excess of
  events "in the same skygroup". Stars on different modules are in different skygroups.
- **Coughlin et al. 2014** (AJ 147, 119) ephemeris matching used Q1-Q12 KOIs; these KOI numbers (5446-8259)
  came later.

So both vetting tools are blind to this case by design, and the six rows stand as independent candidates.

## Other stars at these ephemerides

The Q1-Q16, DR24 and DR25 TCE tables (live TAP queries for Q1-Q16 and DR24; the full DR25 TCE list saved by
orphan-census-v1 for DR25; P within ~0.5 d of 402.2, 416.9 and 502.2 d and of half those periods) hold no
other star at the 402 d or 417 d ephemerides. At the 502 d ephemeris there is one weak, half-period case,
**not counted above**: DR25 TCE 3 of KIC 7049486 (P = 250.981 d, T0 = 163.411, 8.8 h, 399 ppm, MES 8.8).
Every second event of it (163.41, 665.37, 1167.33) falls 0.50, 0.25 and 0.00 d from K07040.01's three
events. That star is the 26.7 d eclipsing binary K06815.01 (FALSE POSITIVE, 7.2% eclipses), 1.9 deg from
KIC 8442795, so its long-period TCE is probably an eclipse-removal residual. If it shares the dates, that
favours a common cause over one star copying another. Each pair member was detected by only one
pipeline run (A: Q1-Q16 and DR25; B: both Q1-Q16; C: DR24 and DR25), and DR25 produced no TCE at all on
KIC 9363944, 11818566, 7917068 or 8442795.

## What it means, and limits

- Two unrelated planets, on stars degrees apart, transiting at the same times to within hours three or four
  times is not plausible. Either the signals share a cause that is not a planet (a spacecraft-wide systematic
  that only these stars' light curves turned into dips, or a contamination path not in the four DR25
  geometries), or one member is a real planet and the other copies it by an unknown path. **This does not
  say which member, if either, is a planet.** It does say the six should not be counted as six independent
  candidates.
- All six are near the detection threshold (SNR 6.9-11.1; the DR25 pair members have MES 7.48 and 7.21 and
  Robovetter scores 0.31 and 0.23), where Thompson et al. 2018 already put DR25 reliability at about 37%
  for P > 200 d and MES < 10.
- The fitted durations differ inside pairs A (5.3 vs 15.7 h) and C (9.4 vs 14.8 h). A copied signal would be
  expected to keep its shape; low-SNR fits are loose, and this has not been checked against the light curves.
- No light curve or pixel data were inspected. Positions are from the Archive table.

## Prior art checked

A web search for the six KOI designations found no paper discussing them. Thompson et al. 2018 App. A.6 and
A.3.7.4 were read for the matching and Skye rules (arXiv 1710.06758v2, characters 260,000-360,000).
