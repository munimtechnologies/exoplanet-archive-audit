# alias-dupes 0.1.0 results, and why the first pixel run measured nothing (2026-10-17)

By MV2 of Munim, Inc.; analysis and text made with AI agents. Text CC BY 4.0, code Apache-2.0.
Scores the predictions in `findings/2026-10-17-pixels-dupes-prereg.md`, misses included.

## alias-dupes: no second Kepler-289 e in the Archive

Job `alias-dupes-v2` ran on 2026-10-17 at about 05:45Z. It used a live query of the Exoplanet Archive's
composite table (`pscomppars`, `sy_pnum > 1`). It covered 2,683 planets around 1,079 hosts. The flagged pairs
are in `results/2026-10-17-alias-dupes-0.1.0/flags.csv`, with the job's `summary.json`.

171 pairs have a period ratio within 0.2 % of a whole number: 4 `same_events`, 88 `offset`, 79 `no_epoch`.

| # | Prediction | Result | Held? |
|---|---|---|---|
| 13 | All 9 unit tests pass | 9 of 9 OK | yes |
| 14 | Kepler-289 d / e flagged `same_events`, k = 5 | flagged, k = 5, phase 0.0042 | yes |
| 15 | 1 to 5 `same_events` pairs | 4 | yes |
| 16 | `same_events` fewer than half of all flags | 4 of 171 | yes |

All four held. The census was meant to find more of what it found in Kepler-289, and it didn't.
A hand check of the three new `same_events` pairs shows that none of them is one planet listed twice:

| Pair | k | Phase | Radii in the table (Earth radii) | Hand check |
|---|---|---|---|---|
| pi Men c / HD 39091 b | 333 | 0.0045 | 2.02 / 12.3 | Different objects. pi Men b is a massive radial-velocity planet (minimum mass about 10 Jupiter masses) on an eccentric 2,089-day orbit. pi Men c is a small transiting planet. At k = 333 the period ratio is always within 0.2 % of some whole number, so the period test means nothing here. The phase match has a 2 % chance of happening by luck. |
| TOI-500 b / TOI-500 e | 112 | 0.0021 | 1.17 / 3.99 | Different objects: b is a transiting planet on a 0.548-day orbit and e is a 61.3-day planet seen in radial velocities. Chance match. |
| HD 224018 b / HD 224018 d | 13 | 0.0045 | 0.91 / 2.4 | Different objects, flagged because the two planets have a shared epoch. Damasso et al. 2025 (A&A; arXiv:2508.13684, read for this check) report that K2 saw b, c and d transit together near BJD 2457741.7 (their Fig. 16 and Table 4). The adopted reference time of d is that event, and the reference time of b is two of b's orbits later. So the two reference times line up by construction. The radii differ (0.91 vs 2.4 Earth radii), and 13 x 10.6413 d = 138.34 d is 0.26 d off d's 138.0731 d. |

**How many chance matches to expect.** 92 flagged pairs have a mid-transit time for both planets. For
those, the phase is close to uniform on [0, 0.5], so the chance that it lands within 0.01 is 2 %. That
gives about 1.8 chance `same_events` pairs. Two pure-chance matches (pi Men, TOI-500) and one
shared-epoch artefact (HD 224018) fit that well.

**Conclusion (a negative result):** among the confirmed planets in the Archive's composite table, Kepler-289
e is the only pair whose transits fall on a sibling's at a whole multiple of its period. Two improvements
for any later version: the expected number of chance matches should be computed per pair (the period
test means nothing once k is above about 250), and planets of very different radii should not be
counted as one planet.

Limits: the scan uses only the default composite row per planet. A duplicate whose default period or
epoch is badly off would be missed. Candidates (KOIs, TOIs) are not included.

## kepler-pixels: the first run read no pixels, so predictions 1-12 are still open

Job `kepler-pixels-v2` (05:46-05:50Z) passed its unit tests (prediction 1). Then it failed on all 17 target
pixel files of each of the three stars with `AttributeError: module 'numpy' has no attribute 'in1d'`.
The job pinned `astropy==6.1.4` but not numpy, so pip installed numpy 2.5.4. That numpy removed
`numpy.in1d`, which this astropy's FITS reader still calls. The code under test never got any data, so
no depth, offset or verdict was measured, and the run neither confirms nor refutes predictions 2-12.

The fix touches only the environment. `requirements-pixels.txt` pins `astropy==6.1.4` and `numpy==2.1.3`, and
`kepler_pixels.py` and its tests are byte-identical to the committed 0.2.0. The re-run (`kepler-pixels-v3`)
is scored against the same 16 predictions, unchanged, in a later note. The downloaded pixel files are
cached, so the re-run does not fetch them again.

Lesson for the method: pin every numerical dependency in a pre-registered job, not just the top-level
package. A run that fails on its environment should be reported as "no measurement", never as a miss
or a pass.
