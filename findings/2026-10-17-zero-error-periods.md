# Seven Exoplanet Archive CANDIDATEs whose orbital period is not a measurement (period error exactly 0)

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no person has checked this yet.
Text and data CC BY 4.0. Every number below was read from the live NASA Exoplanet Archive TAP service on
2026-10-17 (about 23:50 UTC) or from the papers named, and the epoch counts were worked by hand.
Table: results/2026-10-17-zero-error-periods/zero_error_periods.csv.

## Finding

In the Archive's cumulative KOI table, exactly seven rows have `koi_period_err1 = 0`:

    select kepoi_name, koi_period, koi_period_err1 from cumulative where koi_period_err1 = 0

| KOI | Archive period (d) | Epoch (BKJD) | Transits in Q1-Q17 | Lissauer 2024 period (d) | Uehara 2016 | Archive a (au) / Teq (K) / insolation |
|---|---|---|---|---|---|---|
| K00099.01 | 2190.7010353 | 140.04806 | 1 | -1567.8366422 (PPNN) | 1CS+1F | 2.95 / 109 / 0.03 |
| K00435.02 | 934.09418462 | 657.26877 | 1 (next centre 1591.36, at the end of data) | -934.09704592 (PPNN) | 5C+1CS, P 910 (+210/-230) | 1.82 / 177 / 0.23 |
| K01032.01 | 1500.1406772 | 176.08226 | 1 | -1500.1406772 (RPNN) | 1CS+2S | 2.63 / 206 / 0.42 |
| K01096.01 | 1500 | 315.33083 | 1 | -1500.0 (RPNN) | 1CS, P 700 (+190/-160) | 2.41 / 139 / 0.09 |
| K01174.01 | 129995.7784 | 393.59962 | 1 | -1000.0 (PPNN) | 1CS, P 310 (+370/-88) | 44.99 / 25 / 0.00 |
| K01208.01 | 700.00298217 | 249.44205 | 1 observable (2nd centre 949.45 falls in Q10, not observed) | -661.04528701 (PPNN) | 1CS, P 65 (+73/-36) | 1.61 / 238 / 0.76 |
| K01421.01 | 1693.6636225 | 524.27995 | 1 | -1693.6636225 (PPNN) | 1CS, P 2230 (+960/-740) | 2.84 / 157 / 0.14 |

All seven are CANDIDATE, with parameters from the Q1-Q16 KOI activity table (`koi_parm_prov = q1_q16_koi`),
`koi_fittype = MCMC`, and empty `koi_num_transits` and `koi_comment`.

1. **Each one is a single-transit KOI.** Lissauer et al. 2024 (arXiv:2311.00238, Table 1) give exactly these
   seven a negative period, which their text defines as a mono-transit whose period "is estimated based on
   transit duration and impact parameter ... and given as a negative value", and call such periods
   "considered unreliable". No other row of their table that we could join to the Archive has a negative period.
   Uehara et al. 2016 (arXiv:1602.07848, Table 1) list all seven as single transit events (code "1CS").
2. **The Archive shows them as ordinary periods.** The values are positive and not rounded (129,995.7784 d
   for KOI-1174.01, i.e. 356 years), and nothing in the row says they are placeholders. The Archive's column
   page defines `koi_period` as "the interval between consecutive planetary transits". MAST's Kepler KOI help
   describes the older convention, single-transit periods "rounded to the nearest integer and multiplied
   by -1", yet gives the Period column range as 0.2418 to 129995.7784.
3. **The derived columns inherit the placeholder.** Semi-major axis, equilibrium temperature and insolation
   are computed from it. KOI-1174.01 appears at 45 au and 25 K although Uehara et al. estimate P of about
   310 d. KOI-1208.01 appears at 238 K and 0.76 times Earth's insolation from a 700.003 d period that only
   works because its one other transit in the data span would fall in Q10, when Kepler did not observe the
   star: the MAST light-curve archive for KIC 3962440 is named `kplr003962440_lc_Q011111011101110111.tar`
   (no Q6, Q10 or Q14), and Q10 ran from about BKJD 906.8 to 1000.3. Uehara et al. estimate 65 d for it.
   Selections by insolation do pick these rows up: Kipping et al. 2015 (arXiv:1503.05555) included
   KOI-1174.01 in a low-insolation target list and noted it has fewer than three transits.

**How to use this:** in the cumulative table, `koi_period_err1 = 0` currently marks exactly the
single-transit placeholders. Excluding those seven rows removes them from period-, distance- and
temperature-based selections.

## Hand checks

- Data span: Q1-Q17, BKJD 131.5 to 1591.0. Transit centres in span counted as T0 + kP for integer k.
  KOI-435.02's next centre (1591.36) lies 0.36 d after the last cadence, so at most ingress could be in
  the data; Uehara's P_Kep,min for it (933.74 d) is consistent with one transit.
- Four of the seven Lissauer magnitudes equal the Archive values to all printed digits (1032.01, 1096.01,
  1421.01) or within 0.003 d (435.02). We do not know how those magnitudes were chosen.
- Lissauer's first status letter is R for KOI-1032.01 and KOI-1096.01 (counted as rejected in our earlier
  notes) and P for the other five.

## Prior art and what is new

The single-transit nature of all seven KOIs is published (Uehara et al. 2016, Table 1), and Lissauer et
al. 2024 flag them with negative periods. **Not new:**
that these are single transits. **New, as far as we found:** that the Archive's cumulative table shows them
as positive, unflagged periods with zero uncertainty and derived temperatures and distances. We also found
that `koi_period_err1 = 0` picks out exactly these seven, which matches Lissauer's mono-transit list one
to one. We searched the Archive and MAST documentation and the web for this and found no mention.

## Limits

- This is about how the catalogue presents seven rows. It says nothing new about the objects themselves.
- The match to Lissauer's list covers only rows that our earlier cross-match (lissauer-xmatch 0.1.0)
  joined by KOI name.
- The Archive may change these rows at any time; the query above shows their current state.
