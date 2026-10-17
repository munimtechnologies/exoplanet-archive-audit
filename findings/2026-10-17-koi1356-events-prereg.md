# Pre-registration: which transits of KOI-1356.01 are real?

By MV2 of Munim, Inc., 2026-10-17 ~19:40Z. Written by AI agents working in his name before the job below
has run; no person has checked it yet. Text CC BY 4.0, code Apache-2.0.

## Why

`findings/2026-10-17-period-flags-check.md` found that three catalogues give KOI-1356.01 (KIC 7363829)
three periods and agree only on its first transit at 335.82 BKJD. Each table below was re-queried on its
own through the Exoplanet Archive TAP service at about 19:20Z today:

| source | P (d) | T0 (BKJD) | depth (ppm) | dur (h) | S/N | notes |
|---|---|---|---|---|---|---|
| Q1-Q8 KOI | 384.026 | 335.8162 | 6,367 | 14.556 | 119.40 | NOT DISPOSITIONED |
| Q1-Q12 KOI, Q1-Q16 KOI | 384.02570682 | 335.816169 | | 14.56 | | NOT DISPOSITIONED |
| Archive `cumulative` | 384.02570682 | 335.816169 | | 14.56 | | CANDIDATE, all FP flags 0 |
| Q1-Q16 TCE, DR24 TCE, DR24 KOI | no rows | | | | | |
| DR25 TCE 1 | 393.719 +- 0.0012 | 335.817 | 6,367 | 12.51 | 82.31 | 3 transits, b 0.005, Rp/R* 0.0721, rogue 0 |
| DR25 KOI | no rows | | | | | |
| DR25 supplemental KOI | 384.02570682 | 335.816169 | | | | CANDIDATE; Q1-Q16 values carried over, no new fit |
| Lissauer et al. 2024 Table 1 | 787.43235 | | | | 83.9 | status PPNN |

**Why the DR25 TCE never became a KOI (new, read today).** The DR25 Robovetter output for observed TCEs
(github.com/nasa/kepler-robovetter, `kplr_dr25_obs_robovetter_output.txt`) has:

    007363829-01 0.000 FP 1 0 0 0 INDIV_TRANS_MARSHALL_SKYE---INCONSISTENT_TRANS---CENT_FEW_DIFFS

Score 0.000, Not-Transit-Like flag 1, and minor flags saying individual events failed the Marshall and
Skye per-transit tests and that the transits are inconsistent with each other. Under DR25's rules
(Thompson et al. 2018) a non-federated TCE that is not-transit-like with score < 0.1 gets no KOI, which
confirms the inference in the earlier note. One reading, not a measurement: at least one of the three
events DR25 counted is not like the others.

Predicted later transits (BKJD):
- Q1-Q16 / Archive (384.026 d): 719.84, 1,103.87, 1,487.89
- DR25 TCE (393.719 d): 729.54, 1,123.26, 1,516.97
- Lissauer et al. (787.432 d): 1,123.25

## Prior art (checked today)

No paper we could find discusses this object. Web search for "KOI-1356", "K01356" and "KIC 7363829"
finds only the Archive's overview page. It is absent from Herman, Zhu & Wu 2019 (AJ 157, 248; first 100k
characters read), Hansen & Dittmann 2026 (arXiv:2608.23425, four new long-period candidates) and the
abstract of Kawahara & Masuda 2019 (arXiv:1904.04980; its tables were not read). Hill et al. 2018 (ApJ 860,
67), whose habitable-zone giant list is built on Kane et al. 2016's DR24-based catalogue, goes from
K01268.01 to K01375.01. That fits DR24 having no KOI row for this star. Lissauer et al. 2024's full text
does not mention it (read 2026-10-17).

## Data coverage (from MAST file names, not yet from the data)

MAST has long-cadence light curves for all 17 quarters (Q1-Q17) and short cadence in Q11-Q12. The Q7 file
is stamped 2010-355 (about BKJD 719.2), so **both candidate second transits, 719.84 and 729.54, probably
fall in the Q7/Q8 downlink gap**. The events that decide between the periods are 1,103.87 and 1,487.89
(384 d), 1,123.26 (all but 384 d) and 1,516.97 (393.7 d only).

## Job

`koi1356-events-v1`. It fetches `kepler_alias.py` 0.3.0 and its tests from this repository's main branch,
records their sha256, runs their tests and the new tests, then runs `event_check.py` 0.1.0 (published
with the results). Light curves: Kepler long cadence, quality 0, PDCSAP. Box duration 13.5 h (between
DR25's 12.51 h and the KOI tables' 14.56 h). One event's depth is the mean deficit of the central 70 % of
the duration below a straight line through the points 1 to 3 durations from the centre.

Status of each predicted epoch, against the depth D_ref measured at 335.817:
- **deep**: D >= 0.5 D_ref and D/err >= 7
- **absent**: D < 0.3 D_ref and (D_ref - D) / hypot(err, err_ref) >= 5
- **no_data**: too few points in the core or on either side
- **unclear**: otherwise

A period is **excluded** if any of its epochs is absent. It is **supported** if at least two epochs have
data and all of those are deep, **untested** if fewer than two have data, and **unclear** otherwise. The
same rules are applied to every period (T2 - T1)/n, n = 1..12, through 335.817 and 1,123.255. A blind
search steps the box every 0.05 d over the whole light curve and lists the 25 highest-S/N dips at least
1 d apart.

## Predictions

1. The fetched `kepler_alias` is version 0.3.0; its 20 tests and the 12 new tests pass.
2. 335.817 is deep, with S/N >= 20.
3. 1,123.255 is deep.
4. **Q1-Q16 / Archive 384.026 d is excluded** (1,103.87 or 1,487.89 absent).
5. **Lissauer's 787.432 d is supported and DR25's 393.719 d is excluded (1,516.97 absent).** This is the
   prediction most likely to miss. It rests only on Lissauer et al. having worked later and with more
   checks. DR25 counted three transits, and its third could be 1,516.97.
6. 719.84 and 729.54 are both no_data.
7. In the blind search, ranks 1 and 2 lie within 0.5 d of 335.8 and 1,123.3, and rank 3's robust S/N is
   less than half of rank 2's.

Exploratory, no prediction: which n of the two-transit aliases stay allowed; the period from the two best
centres; the depths of every epoch; the coverage table and gap list.

## What each outcome would mean

- 4 and 5 hold: two transits 787.4 d apart. The Archive's default period, 384.03 d, would be wrong, and
  so would the TCE's. As context only, Kepler's law with the Archive's star (R* 1.71 Rsun, Teff 5,719 K)
  or DR25's (1.94-2.02 Rsun, 5,676 K, 1.16-1.18 Msun) puts a 787 d orbit at about 0.9-1.2 times Earth's
  insolation, and a 384 d orbit at about 2.4-3.2. Rp/R* = 0.072-0.083 makes it Jupiter-sized (13-16 Earth
  radii) on either star. We would claim only the period mismatch, not habitability or planethood.
- 393.7 d supported: the never-catalogued DR25 TCE is right and Lissauer et al.'s period is twice it.
- 384 d supported: the older catalogues are right and both later periods are wrong.
- Anything else: written up as found, misses included.

Nothing will be sent to the Exoplanet Archive helpdesk or the authors without Sheehan's approval.
