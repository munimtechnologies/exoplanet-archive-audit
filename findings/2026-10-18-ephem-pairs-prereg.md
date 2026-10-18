# Pre-registration: KOIs on far-apart stars that share a transit train (ephem_pairs 0.1.0)

MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no human has checked this yet.
Code Apache-2.0, text and data CC BY 4.0. Committed **before** the job runs; scored in public, misses included.

## Why

findings/2026-10-18-cross-star-ephemeris-pairs.md found by hand three pairs of long-period CANDIDATEs on
stars 3.9-7.8 deg apart whose events agree to within 0.37 d (K05660.01 ~ K08259.01, K05935.01 ~ K05446.01,
K07040.01 ~ K07932.01). Neither DR25 ephemeris matching (geometry-gated) nor the Skye metric (one skygroup)
can see such pairs. The hand estimate (P ~ 4e-7 by chance) is post hoc. This job tests every KOI.

## Method (ephem_pairs 0.1.0, standard library only)

- Input: the live cumulative table (all dispositions) and results/2026-10-17-lissauer-xmatch-0.1.0/xmatch.csv;
  both saved in out/.
- KOIs used: P >= 50 d, a mid-time, and >= 2 predicted events in BKJD [131.5, 1591.0].
- Match (1:1 periods only): for every pair on different stars, the largest distance from any event of
  either train to the nearest predicted event of the other is <= 0.5 d.
- Geometry of each match: **near** (separation <= DR25 radius 55 sqrt(1e6 10^(-0.4 Kp) + 1)" of the
  brighter star), **antipodal** (one star within 100" of the other mirrored through the field centre
  290.6667, +44.5, gnomonic), **module** (<= 3.4 deg, the same module is possible), else **far**.
- Null: every KOI's epoch redrawn uniformly within one period, 1,000 shuffles, seed 20261018; the number
  of far matches with at least one Archive CANDIDATE is recounted. p = (1 + #shuffles >= observed) / 1001.
- 19 unit tests on the six real rows, with hand-worked offsets (0.36052, 0.1186644, 0.3289 d), separations,
  and the DR25 radius checked against the paper's own examples (552.7" at Kp 10, 5500" at Kp 5).

## Predictions

1. All 19 unit tests pass.
2. Plumbing: the three hand pairs come out **far** with max_offset 0.3605, 0.1187 and 0.3289 d.
3. **The test**: the number of far matches with at least one CANDIDATE is at least 3 times the null mean,
   and p <= 0.01.
4. Of near matches that include a CANDIDATE, at least 70% have koi_fpflag_ec = 1 on the other member
   (DR25 matching caught the local cases; a check that "near" means what it should).
5. CANDIDATEs in far matches have a lower median koi_model_snr than all other CANDIDATEs with P >= 50 d.
6. At least 60% of far matches with a CANDIDATE have P > 200 d.
7. Exploratory, no prediction: the full far list with Lissauer et al. 2024 status; whether event dates
   recur across different far pairs (a recurring date would point to a spacecraft-wide cause); module and
   antipodal matches.

## How it will be read

Only 3 is the test. If it holds, far-apart shared transit trains are a real population that the DR25
vetting cannot see, and each such CANDIDATE should be read as "not independent" until someone checks the
light curves. It will not say which member, if either, is a planet. If 3 fails, the three hand pairs are
more likely the tail of chance among many KOIs (the hand estimate used only the 139 P > 400 d CANDIDATEs)
and will be reported that way.
