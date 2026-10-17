# kepler-pixels 0.2.0 and alias-dupes 0.1.0: predictions written before the run (2026-10-17 ~05:45Z)

By MV2 of Munim, Inc.; written with AI agents. Scored in public when the job lands, misses included.
The code is committed alongside this note, before any result exists. The first queued attempt at both
jobs did not run, so they were re-queued as kepler-pixels-v2 and alias-dupes-v2. The Kepler-1301 b
predictions (1-6) are unchanged from the ones written for the first attempt.

## kepler-pixels 0.2.0

The question: do a Kepler candidate's dips come from the target star's pixels, and do the alternate
events of a KOI suspected to orbit at twice its catalogued period differ in the pixels too? Method in
the `kepler_pixels.py` docstring. 0.2.0 only adds `--period-mult` (a whole factor applied to the
catalogued period); with the default of 1 the results are those of 0.1.0.

### Kepler-1301 b (KOI-2643.01, KIC 6933567), catalogued 9.0823 d; Gaia DR3 neighbour at +2.69" E, -1.85" N

1. All unit tests pass.
2. At least 14 quarterly target pixel files are read without error.
3. Phase 0 (the catalogued transits): depth 200-350 ppm, depth SNR >= 5, verdict `on_target`.
4. Phase 0.5 (the dips halfway, which would make the period 4.541 d): depth 120-300 ppm, verdict `on_target`.
5. Null phases 0.25 and 0.75: `no_signal`.
6. The neighbour calibration offset has a size between 2.0" and 3.5".

If 4 holds, the 4.541 d dips come from the target's pixels at the predicted depth, and the period
correction stands as a candidate correction (an eclipsing binary blended on the target is still not
excluded). If phase 0.5 comes out `neighbour`, the half-phase dips belong to the faint neighbour and
9.08 d stands.

### KOI-4893.01 (KIC 11970050), catalogued 6.5875 d, tested at 2 x = 13.1751 d

Light-curve parity test (kepler_alias 0.3.0): alternate events 314 +- 47 vs 22 +- 43 ppm. No neighbour is
modelled; the job uses a nominal reference one pixel (3.98") north, so here `on_target` only means
"consistent with no shift and not with a one-pixel shift".

7. Exactly one of phases 0 and 0.5 has depth SNR >= 3, at 150-450 ppm; the other has SNR < 3 and a depth
   below one third of the deep group's.
8. The deep group is `on_target`.
9. Null phases 0.25 and 0.75 (of the 13.18 d ephemeris): `no_signal`.

### KOI-4711.01 (KIC 8355131), catalogued 4.3638 d, tested at 2 x = 8.7277 d

Light-curve parity test: alternate events 267 +- 30 vs 69 +- 29 ppm. Same nominal reference as above.

10. One of phases 0 and 0.5 has depth SNR >= 3, at 130-400 ppm; the other's depth is below half of it.
11. The deep group is `on_target`.
12. Null phases 0.25 and 0.75: `no_signal`.

## alias-dupes 0.1.0

The question: is any other confirmed planet in the Archive's composite table listed twice, once at a
whole multiple of a sibling's period with transits on the same dates, as Kepler-289 e (330.07 d) is
Kepler-289 d (66.03 d) seen at five times its period (`findings/2026-10-16-kepler-289.md`)?

13. All 9 unit tests pass.
14. Kepler-289 d / Kepler-289 e is flagged `same_events` with k = 5.
15. Between 1 and 5 pairs in total are flagged `same_events`.
16. Fewer than half of all flagged pairs are `same_events` (most are `offset` resonant pairs or
    `no_epoch` radial-velocity pairs).

## Limits known in advance

- A difference-image offset says where the light comes from, not whether the object is a planet.
  An eclipsing binary blended within about 1" of the target is not excluded by an `on_target` verdict.
- The pixel fit is first order in the shift; the calibration step measures its bias for Kepler-1301 b's
  neighbour, but not for the nominal reference used for KOI-4893.01 and KOI-4711.01.
- The pixel depth is measured against all light in the stamp, so it can be diluted relative to the
  crowding-corrected light-curve depth.
- An alias-dupes flag is a lead for a hand check against the papers, not a finding.
