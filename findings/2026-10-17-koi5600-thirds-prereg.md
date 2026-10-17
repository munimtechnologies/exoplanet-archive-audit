# Pre-registration: is KOI-5600.01 at 17.17 d or 51.50 d? (kepler_pixels 0.4.0, period x 3)

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Text CC BY 4.0. Committed before the job runs; it will be scored in public, misses included.
Background: findings/2026-10-17-period-flags-check.md.

## Question

The Archive's default period for KOI-5600.01 (KIC 9018021) is DR25's 17.168095 d. DR24 and Lissauer et al.
2024 give 51.51 and 51.50 d, three times as long. If the true period is 51.5 d, only one in three of DR25's
events holds a transit. If it is 17.17 d, all three do.

## Method (no new code)

Job koi5600-thirds-v1 fetches kepler_pixels.py 0.4.0 and its 18 tests from this repository (main) and
records their sha256. It then runs the tests and the tool on the 17 Kepler long-cadence target pixel files
of KIC 9018021:

- Run A: `--koi K05600.01 --period-mult 3 --phases 0,0.3333333333,0.6666666667,0.1666666667,0.5,0.8333333333`.
  The ephemeris is DR25's (T0 = BKJD 134.637329, duration 13.04 h) at 3 x 17.168095 = 51.504285 d. The
  phase groups 0, 1/3 and 2/3 are DR25's events n = 0, 1 and 2 (mod 3). Group 2/3 holds the DR24 epoch
  (168.85, 0.126 d before 168.97). Groups 1/6, 1/2 and 5/6 sit halfway between DR25 events: they are nulls.
- Run B (descriptive only): `--koi K05600.01 --phases 0,0.5,0.25,0.75` at the DR25 period itself.
- `--neighbour 0,3.98` is a placeholder (no neighbour was checked), so the neighbour verdicts are not
  read. Offsets from zero are reported but not tested here.

Depths D0, D1, D2 (groups 0, 1/3, 2/3) with errors s0, s1, s2: the tool's Birge-scaled error
(`depth_err_scaled_ppm`), or its formal error where a group has fewer than 3 quarters.

Outcome rule (decided now):
- **"51.5 d"**: D2 / s2 >= 3; D0 / s0 < 2 and D1 / s1 < 2; and D2 - (D0 + D1) / 2 >= 3 sqrt(s2^2 + (s0^2 + s1^2) / 4).
  The same pattern in group 0 or 1/3 instead of 2/3 counts as "51.5 d, other epoch" and is reported as such.
- **"17.17 d"**: the inverse-variance mean of D0, D1, D2 is >= 3 sigma; every pair satisfies
  |Di - Dj| < 2 sqrt(si^2 + sj^2); and at least two of the three are >= 2 sigma.
- **"inconclusive"**: anything else.

## Predictions

1. fetch_tool reports version 0.4.0, and all 18 unit tests pass.
2. At least 15 of 17 quarter files are read without error, and each of groups 0, 1/3 and 2/3 has 18-30 events.
3. **Outcome "51.5 d", in group 2/3.** Our prior is about 60 %. The DR24 and Lissauer periods agree, and
   the DR25 fit is strained (impact parameter 0.999, fitted density 90 times below DR25's own stellar row, about 15 times with the largest published radius). The main
   alternative is "inconclusive": the whole signal is only S/N ~8.
4. Null groups 1/6, 1/2 and 5/6: each |D| / s < 3.
5. Exploratory, no prediction: Run B's depth at phase 0, and the offsets from zero in group 2/3.

## Interpretation, decided now

- "51.5 d": the pixels support Lissauer et al.'s 51.50 d, and the Archive's default 17.168 d looks like a
  1/3 alias. That would go into a correction note for the Archive, which Sheehan approves before it is sent.
  It is not a disposition: the signal stays an S/N ~8 candidate, and a pixel depth says nothing about
  whether it is a planet.
- "17.17 d": the pixels support DR25, and Lissauer et al.'s table period is the one to question.
- "inconclusive": we say so and claim nothing.

Limits: the DR25 duration (13.04 h) is about three times DR24's 4.66 h. If the transit is the short one,
each group's depth is diluted by the long window, equally for all groups. The ephemeris is DR25's.
DR24's period differs by 0.0064 d per 51.5 d cycle (about 4 h over the mission), and Lissauer's by
0.0044 d, so late events can sit off-centre in the window.
