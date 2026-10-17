# Pre-registration: is any Kepler Object of Interest listed twice at a period alias? (koi_dupes 0.1.0)

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Code and data licence: Apache-2.0 (code), CC BY 4.0 (text). Committed **before** the census runs.

## Why

The alias-dupes census (findings/2026-10-17-dupes-results.md) found one duplicate among confirmed
planets: Kepler-289 e (330.07 d) is Kepler-289 d (66.03 d) seen at five times its period. In the
cumulative KOI table Kepler-289 e is K01353.03, and Kepler-289 d has no KOI at all. So the KOI table can
hold a signal at a period alias of a planet that is listed elsewhere.

Prior art: DR25 federation (Thompson et al. 2018, sec. VI.2, arXiv:1710.06758) matches a new TCE to a
known KOI only at the same period or at 2x / 1/2x (244 KOIs), within that one delivery, and bans 19
TCEs by hand as duplicates. The Robovetter's ephemeris-match flag (koi_fpflag_ec) targets contamination
from other stars. We found no published census of same-star KOI pairs at integer ratios k >= 3 across
the whole cumulative table (which merges every delivery), or of KOIs against confirmed non-KOI planets
on the same host. If one exists, this is a replication.

## Method (koi_dupes.py, standard library only)

Data: live TAP queries of `cumulative` (9,564 rows on 2026-10-17) and `pscomppars` where hostname is
`Kepler-%` (2,755 rows). Per Kepler star (kepid):

- **koi mode**: every pair of KOIs on the star.
- **cross mode**: every KOI against each confirmed planet on the same host that has no KOI of its own
  (host = a KOI's kepler_name minus its letter).

A pair (short Ps, long Pl) is an alias if k = round(Pl/Ps) is 1..30 and the drift
|Pl - k Ps| x 1460 d / Pl <= 0.5 d. It is **same_events** if the long signal's mid-time lands within
window = (Ds + Dl) of a short-signal transit (twice the half-sum, so TTVs like Kepler-289 d's 0.28 d
offset still match), else **offset**. A **null** repeats the test with the long epoch moved by 0.25
and 0.75 of Ps; the mean of those two counts is the chance rate (0.5 is reported but not used, as it
picks up eclipse secondaries).

The only real rows looked at before this was written are the 3 KOIs and 4 planets of Kepler-289 (the
positive control) and the table counts above.

## Predictions (scored after the run, misses included)

1. All 11 unit tests pass (every expected value worked out by hand).
2. The queries return 9,500-9,700 KOI rows and 2,700-2,800 pscomppars rows.
3. Positive control: cross mode flags Kepler-289 d / K01353.03 as same_events with k = 5.
4. koi mode: at most 25 same_events pairs.
5. koi mode: at least half of the same_events pairs include a FALSE POSITIVE member (already handled
   by the vetting).
6. koi mode: at most 3 same_events pairs where both members are CANDIDATE or CONFIRMED.
7. Chance rate (mean of the 0.25 and 0.75 nulls): at most 3 in koi mode and at most 1 in cross mode.
8. cross mode: at most 3 same_events pairs besides Kepler-289.

Every same_events flag will be hand-checked against the papers and the Archive's default rows before
anything is called a duplicate. A flag is a lead, not a finding.
