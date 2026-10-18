# Pre-registration: what the light curves show at the shared events of the three cross-star pairs (pair_events 0.1.0)

MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no human has checked this yet.
Text CC BY 4.0, code Apache-2.0. Committed before job pair-events-v1 reads any light curve; it will be
scored in public, misses included. Background: findings/2026-10-18-cross-star-ephemeris-pairs.md and
findings/2026-10-18-ephem-pairs-timing-geometry.md.

## 1. What NASA's DR25 vetting already says (checked 2026-10-18)

From the DR25 Robovetter output (github.com/nasa/kepler-robovetter, kplr_dr25_obs_robovetter_output.txt)
and the Archive `cumulative` table (`koi_comment`, `koi_num_transits`):

| Object | Pipeline run | Score | Disposition | Robovetter comment | Transits |
|---|---|---|---|---|---|
| K08259.01 (TCE 005956171-01), pair A | DR25 | 0.311 | PC | CENT_FEW_DIFFS | 4 |
| K07932.01 (TCE 009278575-01), pair C | DR25 | 0.230 | PC | CENT_FEW_DIFFS | 3 |
| K07040.01, pair C | DR24 | - | CANDIDATE | TOO_FEW_QUARTERS | 3 |
| K05660.01, K05935.01, K05446.01 | Q1-Q16 | - | CANDIDATE | (none stored) | - |
| KIC 7049486 TCE 3 (250.981 d) | DR25 | 0.000 | FP, not transit-like | INDIV_TRANS_CHASES_MARSHALL, ALL_TRANS_CHASES, INCONSISTENT_TRANS, CENT_FEW_DIFFS | - |

What this adds:
- **Both DR25 pair members passed every individual-transit test.** The Robovetter drops single events
  that look like systematics (Rubble, Marshall, Chases, Skye, Zuma, Tracker; Thompson et al. 2018, ApJS
  235, 38, App. A.3.7) and marks a TCE that lost events this way with an INDIV_TRANS_<metric> flag, as on
  KIC 7049486 TCE 3 below. Neither pair member carries one, so each of K08259.01's four and K07932.01's
  three events passed on its own.
- **Neither DR25 member's centroid was tested.** CENT_FEW_DIFFS means too few quarters had usable
  difference images for the centroid-offset test. So DR25 never checked *where* on the sky these signals
  come from, and that is the check that could tell a copied signal from a real one.
- **The eclipsing binary's 250.981 d TCE, whose every second event falls on pair C's dates (0.50, 0.25,
  0.01 d away), failed as not transit-like.** Its individual events are inconsistent with each other and
  fail Chases and Marshall. That fits the eclipse-residual reading in the first note; it is still measured
  below as a control.
- K07040.01's DR24 row was kept with TOO_FEW_QUARTERS (three transits in too few quarters), a minor flag.

## 2. The test

pair_events 0.1.0 (this repository; 15 unit tests on noise-free synthetic data and on the catalogue
ephemerides, which reproduce the published offsets 0.361, 0.119 and 0.329 d) downloads every long-cadence
light curve of the six stars and of KIC 7049486 from MAST. It measures each star at the events of **all
seven** ephemerides inside its data, so each star's own events sit next to controls (the other pairs'
dates). Quality-0 cadences only. The EB's primary and secondary eclipses (26.7184 d at 138.054 and 156.04
BKJD) are masked first. The box is the kepler_alias 0.3.0 box (central 70 % of the duration against a line
through points 1 to 3 durations out), using each star's catalogue duration (5.30, 15.67, 4.45, 4.03, 9.39,
14.84, 8.777 h). For each event it reports:

- PDCSAP and SAP deficits (ppm);
- **background excess**: SAP_BKG change in units of the quarter's median SAP_FLUX. SAP is raw minus
  background, so an over-estimated background makes a SAP dip of the same size. A diffuse spacecraft-wide
  event (for example the Argabrightening glows in the Kepler release notes) would act through this path;
- centroid shifts (MOM_CENTR1/2, millipixels);
- cadences with SAP_QUALITY != 0 within +-1 d, and the OR of their bits;
- an empirical null: the PDCSAP deficit at 300 evenly spaced times across the star's data (skipping +-2 d
  of any measured event), giving each event's percentile `pct` and z = deficit / (1.4826 MAD).

**Dip** (fixed now): PDCSAP deficit > 0 and pct >= 0.95 of the star's own null.

Scored events: the three events both members' searches covered (A1-A3 at ~369.5, 771.7, 1173.9; B1-B3 at
~227.5, 644.4, 1061.3; C1-C3 at ~162.9, 665.1, 1167.3 BKJD). A4 (Q17, ~1576.1-1576.5) is reported but not
scored. B4 (~1478.2) falls in the January 2013 wheel rest and should have no data.

## 3. Predictions (written before any light curve was read)

- **P1 (sanity).** At least 4 of the 6 members show a dip at >= 2 of their 3 scored events. (They were
  detected, but K05660.01's star gave no DR25 TCE at all, and the MAST files are the final DR25 processing.)
- **P2 (the signals are in the data together).** In at least 2 of the 3 pairs, both members dip at >= 2 of
  the 3 shared events.
- **P3 (controls behave).** Of all control events (a star at another ephemeris's dates), at most 10 % are
  dips (5 % expected by construction). If more, the dip rule is too loose and P1-P2 are read with that in mind.
- **P4 (not background).** An event is *background-led* if the SAP deficit is > 0, the background excess is
  >= 0.5 x the SAP deficit, and the excess is >= 3 x its error. Prediction: **no** pair has background-led
  events on both members at >= 2 shared events. Low confidence: we have no measurement behind it.
- **P5 (no shared flag).** No scored shared event has a SAP_QUALITY bit set on both members within +-1 d
  that is absent from both members' control events.
- **P6 (EB control).** KIC 7049486 shows no dip at >= 2 of pair C's three dates.

Centroid shifts are reported only. With S/N ~7-11 signals, single-event centroids will be noisy (run 76's
lesson); a shift >= 3 sigma on one member at >= 2 shared events would be a lead for a pixel-level test,
not a claim.

## 4. How each outcome will be read

| P2 | P4 | Reading |
|---|---|---|
| holds | holds | Both stars dim at the same times and the background does not explain it. Open: a copied signal or a shared systematic outside the background estimate; next, difference images at the shared events. |
| holds | fails | A shared background mis-estimate dims both stars: a spacecraft-wide systematic. Then all six rows are probably not planets, and a helpdesk note (held for approval) would say so. |
| fails | - | The catalogued signals do not appear together in the final light curves; the coincidence lives in the pipeline detections only. The six rows still should not count as independent. |

## 5. Limits

PDCSAP detrending can bend long, shallow events. Catalogue durations differ inside pairs (5.3 vs 15.7 h,
9.4 vs 14.8 h), so each star is measured with its own duration. Quality-0 only: an event hidden under
flagged cadences reads as no data, and the flag count shows it. The null is empirical, not Gaussian,
so red noise is in it. Nothing here says which member, if either, is a planet.
