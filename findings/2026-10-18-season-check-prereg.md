# Pre-registration: are the 371-day candidates KOI-5269.01 and KOI-5227.01 a start-of-quarter systematic? (season-check-v1)

By MV2 of Munim, Inc., 2026-10-18. Written by AI agents working in his name before the job runs; no person has
checked it yet. Text CC BY 4.0, code Apache-2.0. Committed before the job runs; scored in public, misses included.

## What prompted it

The pre-registered cross-star census (`findings/2026-10-18-ephem-pairs-results.md`) lists, among its "module"
matches, two Archive CANDIDATEs on stars 0.88 deg apart that share a transit train to 0.28 d:
K05269.01 (KIC 6359929, P 371.50631 d, T0 260.1243 BKJD, 8.85 h, 992 ppm, S/N 14.1, 2.88 Earth radii, 0.80 Earth
insolation) and K05227.01 (KIC 6034834, P 371.56492 d, T0 259.8491, 14.74 h, 376 ppm, S/N 16.2, 1.89 Earth radii,
1.06 Earth insolation). Their period is within 1 d of Kepler's 372.5 d orbit. Three FALSE POSITIVEs in the
same table have periods of 370.9-371.2 d and dates within about 1 d of theirs: K05421.01 (KIC 7751133),
K05462.01 (KIC 8025718) and K08262.01 (KIC 6195669).

Facts read on 2026-10-18 (Exoplanet Archive TAP: cumulative, q1_q16_koi, q1_q17_dr24_tce, q1_q17_dr25_tce,
q1_q17_dr25_sup_koi):

- All 20 catalogue events of the five KOIs fall between **0.40 d before and 1.93 d after the first cadence of
  quarters 3, 7, 11 and 15** (first good cadences 260.2451, 630.1955, 1001.2288 and 1,373.5085 BKJD in the
  KIC 9018021 light curves, `results/2026-10-18-koi5600-lightcurve-0.1.0/coverage.csv`; quarter boundaries are
  spacecraft-wide, though a star's first good cadence can differ by a few cadences). The job itself uses each
  file's first finite TIME. Quarters 3, 7, 11 and 15 are one season: each star is back on the same CCD.
  Offsets (d) for K05269.01: -0.121, 1.435, 1.908, 1.135; K05227.01: -0.396, 1.219, 1.750, 1.035. K05227.01's
  first event (259.849, 14.7 h long, so 259.54-260.16) lies wholly in the gap between Q2 (ends 258.47) and Q3.
- Neither star has a DR24 or DR25 TCE. Both KOIs come from the Q1-Q16 delivery.
- K05227.01 was dispositioned **FALSE POSITIVE (not-transit-like flag)** in the Q1-Q16 KOI table (vetted
  2014-12-18). The cumulative table now shows it as **CANDIDATE**, with disposition provenance
  q1_q17_dr25_sup_koi (2018-08-16); that supplemental row carries no score, depth, duration or S/N.
  K05269.01 is CANDIDATE in both.
- Lissauer et al. 2024 (arXiv 2311.00238), Table 1, as joined in `results/2026-10-17-lissauer-xmatch-0.1.0/`:
  both are "P" (status PPNN, periods 371.678 and 371.521 d); the three neighbours are "F".
- K08262.01 (DR25): FALSE POSITIVE, flags MOD_SEC_ALT and CENT_FEW_DIFFS. K05421.01: not-transit-like and
  ephemeris-match flags; K05462.01: ephemeris-match flag.

## Prior art

A pile-up of false alarms near Kepler's 372-d orbital period is well known: Mullally et al. 2015 (ApJS 217, 31),
Jenkins et al. 2016 (DR25 search, arXiv 1604.06140: image artefacts on the annual thermal cycle), Mullally et
al. 2016 (PASP 128, 074502: the "Marshall" per-event test on DR24 KOIs with P > 150 d), Thompson et al. 2018
(the excess near 370 d vanishes at score > 0.7), Kawahara & Masuda 2019 (arXiv 1904.04980: an "FP bump" at
350-390 d with durations over 0.3 d, clustered on particular CCDs) and a 2025 review of eta-Earth (arXiv
2511.05658: heater cycling and sun-angle focus changes repeating every 372.5 d). We found no publication that
names K05269.01 or K05227.01 (web search, 2026-10-18), and none of these works ties such signals to the first
days of a quarter. What would be new: a test, on named candidates that a 2024 catalogue still keeps, of whether
their events are a start-of-quarter artefact, using stars not selected for having one.

## Method (season_check 0.1.0 on the published pair_events 0.1.0)

`fetch_pe.py` downloads `pair_events.py` and its tests from this repository's main branch and records their
sha256. `season_check.py` (15 unit tests, all values worked by hand) reads every long-cadence file (PDCSAP,
quality 0) and each file's header (QUARTER, SEASON, MODULE, OUTPUT, CHANNEL) for:

- the five KOI stars, each with its catalogue duration, other KOIs on the star masked;
- **control stars, chosen by a fixed rule before any data is seen**: the 3 nearest KOI host stars to each
  candidate whose KOIs are all CANDIDATE or CONFIRMED with P < 300 d and Kp 12-16 (the five KOI stars
  excluded), giving 6 stars; their own KOIs are masked; box duration 12 h.

Cells: each KOI star at its own catalogue events ("own"), and every star at **first cadence + 1.2 d** of every
quarter file ("qstart"; 1.2 d is the median of the 20 catalogue offsets). Each cell is the pair_events box (line
through points 1-3 durations out, mean deficit of the central 70 %). A **dip** is a PDCSAP deficit > 0 at or above
the star's null 95th percentile, the null being 300 evenly spaced boxes that skip -0.5..+2.5 d around every
quarter start and +-2 d around the star's own events. "In season" = quarters 3, 7, 11, 15.

## Predictions (written before the job runs)

1. pair_events 0.1.0 is fetched; its 15 tests and the 15 season_check tests pass.
2. Six distinct control stars are chosen and read; every star (KOI or control) has at least 3 measured
   in-season quarter-start cells.
3. **The test.** Pooled over the six control stars, in-season quarter-start cells are dips at a fraction of at
   least 0.25, at least 3 times the out-of-season fraction (floor 0.05), with binomial p <= 0.01 against the
   null rate 0.05 (`p3_control_test` = true in summary.json).
4. The catalogue signals are in the PDCSAP light curves: K05269.01 has at least 3 of its 4 own events as dips;
   K05227.01's first event (259.849) gets no fit, and at least 2 of its other 3 are dips.
5. Pooled over the five KOI stars, out-of-season quarter-start cells are dips at a fraction of at most 0.15
   (the signal belongs to one season, not to every quarter start).
6. In at least 3 of quarters 3, 7, 11 and 15, K05269.01 and K05227.01 are on the same CCD module (MODULE).

Exploratory, no prediction: modules and channels of all eleven stars in season (Kawahara & Masuda name chip 58
and the edge of chip 62); SAP, background and centroid shifts at the own events; the FP stars' rates.

Our priors: 1, 2 and 4 likely; 3 about 40 % (an artefact tied to one CCD would not reach controls on other
CCDs); 5 about 60 %; 6 about 60 %.

## How it will be read (fixed now)

- **3 holds**: stars chosen without regard to any transit dip at the same quarter starts, so a start-of-season
  artefact exists in this part of the field, and K05269.01 and K05227.01 should be read as probable instrumental
  false alarms. We would write that up with all cells; a correction note to the Archive would be drafted and held
  for Sheehan's approval, not sent.
- **3 fails, 4 and 5 hold**: the dips are tied to one season but appear only on the KOI stars. That fits a
  channel-specific artefact (look at 6 and the channel table) and also fits real transits on a near-year period;
  we would claim neither.
- **4 fails**: the catalogue signals are not reproduced by this box; nothing is claimed about either candidate.
- Nothing here says whether either signal is a planet. No email or ticket goes to anyone without Sheehan's approval.
