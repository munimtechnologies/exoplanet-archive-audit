# KOI-1209.01 prior-art addendum: why no habitable-zone list carries it, and a transit too short for its star

By MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no person has checked it yet.
Text CC BY 4.0. Written **before** `koi1209-events-v1` has read any light curve; it adds context to
`findings/2026-10-18-koi1209-events-prereg.md` and changes none of its seven predictions or status rules.

## 1. Catalogue history of KIC 3534076 (Exoplanet Archive TAP, read 2026-10-18 ~07:00 UTC)

| table | rows for kepid 3534076 | what it says |
|---|---|---|
| `q1_q12_koi` | 1 | K01209.01, NOT DISPOSITIONED, P 272.0868353 d, T0 378.13721, 5,572 ppm, 2.7145 h |
| `q1_q16_koi` | 1 | K01209.01, NOT DISPOSITIONED, same ephemeris; S/N 21.50, insolation 0.93, Rp 5.95 Re; no TCE link |
| `q1_q17_dr24_tce` | **0** | DR24 produced no TCE on this star |
| `q1_q17_dr24_koi` | **0** | so no DR24 KOI row either |
| `q1_q17_dr25_tce` | 1 | 003534076-01, 408.415 d, Robovetter FP (from the shared-events job) |
| `q1_q17_dr25_sup_koi` | 1 | K01209.01, CANDIDATE, no score, all four FP flags 0, P 272.0868353 d, delivery name `q1_q17_dr25_tce` |
| `cumulative` | 1 | CANDIDATE; `koi_disp_prov` = q1_q17_dr25_sup_koi (vetted 2018-08-16), `koi_parm_prov` = q1_q16_koi, `koi_sparprov` = stellar_q1_q16 |

So the CANDIDATE label comes from the DR25 supplemental table, but every number in the cumulative row
(period, depth, radius, insolation) is still the Q1-Q16 fit, and the star's own DR25 detection is a
different period that the Robovetter rejected. Lissauer et al. 2024 keep 272.086 d (status PPNN).

## 2. Absent from the Kepler habitable-zone catalogue

Kane et al. 2016 (ApJ 830, 1; arXiv 1608.00620) built their four HZ tables from the Q1-Q17 DR24
candidates. We read all four tables (20, 29, 63 and 104 rows, read through ar5iv): **K01209.01 is in none
of them.** With the Q1-Q16 values it would qualify for their category 3 (any radius, conservative HZ),
so the likeliest reason is simply that DR24 never detected the star (section 1). Hill et al. 2023
(AJ 165, 34) catalogue planets from the Archive's planet tables, which as far as we can tell hold
confirmed planets only, so it would not be there either. Our inference about why it is missing has not
been confirmed with the authors.

**K01209.01 is not a one-off.** In `cumulative` today, 1,977 CANDIDATEs take their disposition from the DR25
supplemental table: 1,377 have DR25 parameters, 139 DR24 and **461 Q1-Q16** (TAP group-by, 2026-10-18).
A left join of those 461 against `q1_q17_dr24_koi` finds no DR24 row for any of the 138 with catalogued
insolation between 0.2 and 2.0. That is expected by construction, because the parameters come from the
newest table holding the KOI. It also means none of the 138 could enter a DR24-based HZ list, and every one
still carries pre-Gaia Q1-Q16 stellar values. The 138 include known single transits (K00435.02, K01032.01,
K01208.01), the timing-variation system K00682.01, and four members of our earlier lists (K05365.01,
K05893.01, K05165.01, K01209.01). This is a sample-definition fact, not an error: DR24 and DR25 studies are
meant to use their own detections. But anyone reading the Archive's CANDIDATE list for habitable-zone
objects is reading Q1-Q16 numbers for these 138.

**Insolation depends on which stellar row is used.** The Archive's `keplerstellar` table has five rows for
this star. The Q1-Q16 row behind the cumulative values is Teff 5,587 K, R 0.791 Rsun, M 0.806 Msun,
which gives 0.93 times Earth's insolation. Two later rows are Teff 5,821-5,822 K, R 0.995-1.006 Rsun,
M 0.989-1.028 Msun. Worked by hand with L = R^2 (Teff/5772)^4 and a^3 = M P^2, those give **about 1.5
times Earth's insolation**, inside the optimistic HZ but outside the conservative one. "About Earth's
insolation" in the pre-registration is the Q1-Q16 value only.

## 3. The catalogued transit is about four times too short for a central transit of this star

Using a/R* = 3.753 rho^(1/3) P^(2/3) (rho in g/cm^3, P in days) and P = 272.087 d:

| stellar row | rho (g/cm^3) | a/R* | longest (central) duration |
|---|---|---|---|
| Q1-Q16 (R 0.791) | 2.296 | 208 | 10.0 h |
| later (R 0.995, M 0.989) | 1.412 | 177 | 11.7 h |

The Q1-Q16 fit's duration is 2.71 h (DR25's TCE: 3.55 h). The same fit lists a/R* = 770 at impact
parameter 0.36, which needs a stellar density near 117 g/cm^3, about 50 times the catalogued 2.3. The
fitted geometry can't be right for this star. The transit must instead be grazing (with radius ratio
0.069, T14 / T_central = 0.23-0.27 puts b near 1.03-1.04), or the orbit eccentric with the transit near periastron, or the signal comes from a smaller,
denser star blended with KIC 3534076. None of these is excluded here, and none says the period is wrong:
a central 2.7 h transit of this star would need a period of a few days. This caution is published
alongside the period test so that a "272 d confirmed" result is not read as "a habitable-zone planet".

## Reproduce (Exoplanet Archive TAP, `https://exoplanetarchive.ipac.caltech.edu/TAP/sync?format=csv&query=...`)

    select koi_parm_prov, koi_disp_prov, count(*) as n from cumulative
      where koi_disposition='CANDIDATE' group by koi_parm_prov, koi_disp_prov
    select c.kepoi_name, c.koi_insol, d.koi_disposition as dr24_disp, d.koi_period as dr24_period
      from cumulative c left outer join q1_q17_dr24_koi d on c.kepoi_name=d.kepoi_name
      where c.koi_disposition='CANDIDATE' and c.koi_parm_prov='q1_q16_koi'
        and c.koi_insol between 0.2 and 2.0 order by c.koi_insol      -- 138 rows, dr24_disp empty in all
    select * from q1_q17_dr24_tce where kepid=3534076                  -- 0 rows
    select kepid, teff, logg, radius, mass, dens, feh, kepmag from keplerstellar where kepid=3534076

The join was checked on rows with `koi_parm_prov = 'q1_q17_dr24_koi'`, where it returns DR24 dispositions
as it should. (A `not in (select ...)` form of the query was refused by the server with HTTP 403.)

## What changes

Nothing in the scoring. If predictions 3 and 4 hold, the results note will say: one transit train, five
events, 272.09 d, on a star DR24 never detected and DR25 folded at the wrong period, and therefore missing
from the Kepler habitable-zone catalogue. Its transit shape is not yet consistent with a central transit
of the catalogued star. Nothing has been sent to the Archive or to any author.
