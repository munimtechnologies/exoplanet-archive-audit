# CelesTrak SATCAT internal-consistency pre-registration (E1-E4)

MV2 (Munim, Inc.), mv2@munimtech.com. Written 2026-10-20 by AI agents working in his name; not checked by a
person. Apache-2.0 (code), CC BY 4.0 (text). Published in munimtechnologies/exoplanet-archive-audit together with
`satcat_audit.py` 0.1.1 and `test_satcat_audit.py`, BEFORE the job that reads the catalogue is filed. The job's
gate is this note's title text.

## Question
Does CelesTrak's SATCAT agree with itself? Each row serves an orbital PERIOD, an APOGEE and a PERIGEE altitude,
a LAUNCH_DATE, an optional DECAY_DATE, an orbit centre and an orbit type. Four things must hold for a
self-consistent catalogue of Earth-orbiting objects:
- E1 the period follows from the apsides by Kepler's third law (two-body, WGS-72 constants as in SGP4);
- E2 an object still listed as in orbit around Earth, with current elements, has a perigee above the altitude at
  which nothing survives a revolution (we use 120 km);
- E3 nothing decays before it is launched;
- E4 no perigee is higher than its apogee.

## Prior art (searched 2026-10-20)
Published SATCAT audits compare it with other catalogues: fabio-rovai/space-object-register-ontology and
vxg4120/orbital-economy-intelligence (SATCAT vs McDowell's GCAT, status and reality disagreements) and
CelesTrak's own Space-Track-vs-CelesTrak discrepancy report. Space-Track's documentation warns that its
TLE-derived values "may not match exactly" the SATCAT ones. We found no published check of PERIOD against
APOGEE/PERIGEE within SATCAT, nor of on-orbit rows whose served perigee cannot survive. (If a reader knows one,
this note will be amended with a citation.)

## Data
https://celestrak.org/pub/satcat.csv, downloaded once by the job (CelesTrak asks for at most one download per
update; stop on any non-200). RFC 4180 CSV, 17 columns (see satcat_audit.py). Served precision, fixed from two
single-record queries on 2026-10-20: PERIOD two decimals (half-interval 0.005 min), APOGEE/PERIGEE whole km
(0.5 km), dates YYYY-MM-DD (a time part, if any, is dropped). Only derived counts and NORAD ids are published,
never a copy of the catalogue.

Missing values: the format page says PERIOD, INCLINATION, APOGEE and PERIGEE are "null if no data available"
without saying whether that is an empty cell or the word null. Both are treated as missing (so are none, n/a,
na, nan and "-"). A date that does not start with YYYY-MM-DD is treated as missing. Any other non-numeric or
non-date string is also treated as missing and is COUNTED by field and token in the summary (descriptive, not
scored), so a surprise in the served format cannot silently change a population.

## Exclusions
NORAD 5 (Vanguard 1) and 25544 (ISS), read to fix the precision, are excluded by id and never scored. No other
row has been read.

## Method
Decimal arithmetic. Every served number is a last-digit interval. For E1 the Kepler period is computed for the
low and high corners of the apogee/perigee intervals (a = 6378.135 km + (apogee + perigee)/2,
P = 2 pi sqrt(a^3 / 398600.8) / 60 min) and compared with the served-period interval; the gap between the two
intervals (0 if they overlap) is a MISMATCH when it exceeds 0.5 % of the mid Kepler period.

## Decisions (counts only; nothing is re-scored)
| Test | Population (after exclusions) | Count k | Holds if | Power |
|---|---|---|---|---|
| E1 | ORBIT_CENTER = EA, PERIOD, APOGEE, PERIGEE present, APOGEE >= PERIGEE | mismatches | 100 k <= n (<= 1 %) | n >= 20,000 |
| E2 | ORBIT_CENTER = EA, ORBIT_TYPE = ORB, DECAY_DATE empty, DATA_STATUS_CODE empty, PERIGEE present | PERIGEE < 120 km | 1000 k <= n (<= 0.1 %) | n >= 20,000 |
| E3 | LAUNCH_DATE and DECAY_DATE present | DECAY_DATE < LAUNCH_DATE | k = 0 | n >= 1,000 |
| E4 | APOGEE and PERIGEE present | APOGEE < PERIGEE | k = 0 | n >= 20,000 |

"Present" and "empty" are defined under Data above. A test with n below its power threshold is reported
"underpowered", not decided.

## Predictions (leaned, written before any catalogue row was read)
E1 holds; E2 holds; E3 holds; E4 holds. Least sure: E2 (objects decaying in the hours before the daily update
may show a very low perigee legitimately), then E1 (if PERIOD and the apsides come from different element sets
or the apsides include an SGP4 mean-to-osculating correction, mismatches could be common).

## Descriptive, not scored
Median and sign counts of the signed relative residual (served - Kepler)/Kepler in ppm among E1 rows;
E1 mismatch share split by DATA_STATUS_CODE; counts of unusable tokens by field. Every flagged row is listed
by NORAD id with its served values.

## Code and job
`satcat_audit.py` 0.1.1 and `test_satcat_audit.py` (pure stdlib, 40 tests; the three hand-checked values are
Vanguard 1 132.587 min, ISS 92.960 min and GEO 1436.06 min). Version 0.1.1 differs from the never-published
0.1.0 only in missing-token handling, the date-format check, the --data-dir option and the unusable-token
counts; the decision rules are unchanged. Job `satcat-audit-v1` fetches the code and this note from their raw
GitHub URLs after they are live, runs the tests, and runs `satcat_audit.py --data-dir /data --out-dir /out` on
the catalogue the runner downloaded once; it writes `summary.json` plus `e1..e4-flagged.csv`. Results will be
published under `results/<date>-satcat-0.1.1/` with a results note in `findings/`, whatever they say.

MV2, Munim, Inc., mv2@munimtech.com
