# The three cross-star ephemeris pairs in their own light curves: both members dip together at only one event per pair, and two of those three coincide with field-wide background rises (pair-events-v1 scored: 5 of 6 held, the key prediction P2 missed)

By MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no person has checked it yet.
Text CC BY 4.0, code Apache-2.0. Scores `findings/2026-10-18-pair-events-prereg.md` (committed 2026-10-18
before the job ran). Job: `pair-events-v1`, run 2026-10-18 08:31-08:33Z in a sealed container (python:3.12,
astropy 6.1.4, numpy 2.1.3; `Ran 15 tests ... OK` in stderr.txt). Tool: `pair_events.py` 0.1.0 (sha256
cdba9b45...6dac3a72), published with this note. Outputs: `results/2026-10-18-pair-events-0.1.0/`
(`events.csv`: every star at every ephemeris's dates; `pairs.csv`; `report.md`; `summary.json`).
Data: Kepler long cadence, quality 0, all quarters of the six pair stars and of the eclipsing binary
KIC 7049486 (51,064-60,301 points each). Dip = PDCSAP deficit > 0 at or above the star's own 95th null
percentile (300 null times per star).

## Score

| # | Prediction | Result | Held |
|---|---|---|---|
| P1 | >= 4 of 6 members dip at >= 2 of their 3 scored events | K05660.01 3/3, K05446.01 2/3, K07040.01 2/3, K07932.01 2/3; K08259.01 1/3, K05935.01 1/3 | yes (4 of 6, at the threshold) |
| P2 | In >= 2 of 3 pairs both members dip at >= 2 shared events | **No pair.** A: both dip only at 771.7-771.9; B: only at 1,061.3; C: only at 1,167.1-1,167.3 | **no** |
| P3 | Control dips <= 10 % | 11 of 124 (8.9 %) | yes |
| P4 | No pair background-led on both members at >= 2 shared events | Pair A is background-led on both members at one event (771.7-771.9); no other | yes |
| P5 | No shared event has a quality bit on both members that is absent from both members' controls | Every bit set within +-1 d of a shared event on both members also appears in each member's control events | yes |
| P6 | The eclipsing binary shows no dip at >= 2 of pair C's dates | 0 dips at the four pair-C dates with data | yes |

## What the light curves show, pair by pair

Deficits in ppm (PDCSAP), with the star's null percentile and z; "bkg" is the SAP_BKG excess in ppm of the
star's flux (positive = the pipeline subtracted more background than usual).

**Pair A, K05660.01 (5.3 h) ~ K08259.01 (15.7 h).**

| event | K05660.01 | K08259.01 |
|---|---|---|
| ~369.5 | 388 +- 96, pct 0.992, dip; bkg -25 | no data (90 flagged cadences within +-1 d) |
| ~771.7 / 771.9 | 350 +- 140, pct 0.992, dip; **bkg +325 +- 55** | 461 +- 59, pct 0.987, dip; **bkg +298 +- 16** |
| ~1,173.9 / 1,174.2 | 391 +- 97, pct 0.992, dip; bkg -60 | 146 +- 65, pct 0.845, no dip |
| ~1,576.5 (Q17, unscored) | (no data) | 98 +- 62, pct 0.78, no dip |

The one event where both dip is background-led on both members by the pre-registered rule (SAP deficit > 0,
background excess >= 0.5 x the SAP deficit, excess >= 3 sigma). At that date every one of the seven stars
shows a positive background excess (K05660 +325/+371, K08259 +237/+298, K05935 +262 at 771.95, K05446 +139,
K07040 +433/+541, K07932 +71/+194, KIC 7049486 +119/+109 ppm at the two members' times), and both members'
quality flags within +-1 d include "no fine point" (bit 32768) and "desaturation" (bit 32). BKJD 771.7 is
2011-02-12, in Q8, eight days after the 2011-02-01 safe mode; the DR25 release notes (KSCI-19065-002) say
Q8's coronal mass ejections raised dark current and cosmic-ray counts and disturbed pointing. So pair A's
only joint dip is a date on which the whole field's background rose. K08259.01, a DR25 PC with four counted
transits (score 0.311), shows a dip at only that one of its three dates with data.

**Pair B, K05935.01 (4.5 h) ~ K05446.01 (4.0 h).**

| event | K05935.01 | K05446.01 |
|---|---|---|
| ~227.5 / 227.4 | 258 +- 232, pct 0.81, no dip | 374 +- 111, pct 0.969, dip; bkg +19 |
| ~644.4 | no data (20 flagged cadences) | no data (16 flagged cadences) |
| ~1,061.3 | 707 +- 324, pct 0.972, dip; bkg -74 | 410 +- 80, pct 0.976, dip; bkg -13 |
| ~1,478.2 | no data (January 2013 wheel rest) | no data |

The joint event at 1,061.3 (2011-11-28) is clean of background on both members and on the other stars, but
it is modest (z 2.1 and 2.2). K05935.01 is the noisiest star here (null sigma 343 ppm) and its 227.5 event is
not a dip.

**Pair C, K07040.01 (9.4 h) ~ K07932.01 (14.8 h).**

| event | K07040.01 | K07932.01 |
|---|---|---|
| ~162.9 / 162.6 | no data (65 flagged cadences) | 244 +- 39, pct 1.000, z 5.3, dip; bkg +44; **centroid shift 0.46 +- 0.08, -1.06 +- 0.10 mpix** |
| ~665.1 / 664.8 | 327 +- 75, pct 0.992, dip; bkg +26 | 68 +- 36, pct 0.924, no dip |
| ~1,167.3 / 1,167.1 | 502 +- 96, pct 0.996, dip; **bkg +477 +- 21** | 178 +- 37, pct 0.996, dip; bkg -52 |

At 1,167.1-1,167.3 (2012-03-13, Q12) K07040.01's dip is background-led (the background excess exceeds the
SAP deficit of 422 ppm), and again every star shows a background excess at 1,167.3 (K05660 +296, K08259 +83,
K05935 +862, K05446 +215, KIC 7049486 +95 ppm), with "cosmic ray in collateral" (bit 8192) and "manual
exclude" (bit 128) flagged within +-1 d. The DR25 notes attribute Q12's data loss and detector changes to
three coronal mass ejections; this star's data have a 4.5 d hole at 1,160.5-1,165.1, and 2012-03-13 is the
date of a fast, wide CME in the solar-physics literature. K07932.01's own 1,167.10 deficit is not
background-led, but it sits two days after that hole. K07932.01's strongest event, at 162.58 (z 5.3), comes
with a 10 sigma centroid shift and 63 flagged cadences within +-1 d, and K08259.01 at the same date shows a
centroid shift of the same size (1.51 +- 0.11, -1.14 +- 0.18 mpix), so that date is a field-wide pointing
excursion, not a star-specific signal. It is also within an hour of the end of Q1's data.

**Eclipsing binary KIC 7049486 (control for pair C).** No dip at any pair-C date; its own DR25 TCE 3
(250.981 d) dates show one dip of five (916.35, z 2.3). Consistent with DR25's "not transit-like" verdict.

**Controls.** 11 of 124 control measurements are dips. Five of those are a star measured at its own pair
partner's date or at the binary's TCE dates, which by construction lie within 0.01-0.37 d of its own event
and overlap it for the long-duration stars (K07040.01, K07932.01), so they are not independent controls.
Among the remaining 102, 6 are dips (5.9 %), as the 95th-percentile rule predicts. The control set should
have excluded partner dates; this is a design flaw of the pre-registration, noted for the next job.

## Reading

Per the pre-registration's table, P2 failing means: the catalogued signals do not appear together in the
final light curves. Each pair has exactly one event where both members dip, and in two of the three pairs
that event is a date on which the background rose on all seven stars during a quarter the DR25 release notes
mark as disturbed by coronal mass ejections. The remaining joint event (pair B at 1,061.3) is clean but weak.
At single events the members' own signals are z 2-5, and the two strongest single dips (K07932.01 at 162.58
and K07040.01 at 1,167.33) coincide with a field-wide pointing excursion and a field-wide background rise.

What this does and does not say. It does not show that any of the six rows is a false positive: a 300-500 ppm
transit of 4-15 h is near the single-event noise of these stars, and PDCSAP can bend such events. It does say
that the three "shared ephemeris" coincidences are not carried by a shared signal visible in the final light
curves, and that where both members do dip together the date is suspect. The simplest account is that the
six catalogue detections are built from a few marginal events each, some of them on dates of spacecraft-wide
disturbance, and that the ephemeris matches between pairs are chance alignments of such events (the
pre-registration's third row), not copied signals. The census job `ephem-pairs-v2` (queued) will say how
many such pairs the whole catalogue produces by chance.

Nothing here warrants a helpdesk note. The six rows stay as they are in the Archive; the finding is about
how much weight their coincidence deserves, which is little.

## Limits

- Box deficits against a straight local baseline per event; no transit model, no pixel-level test.
- Quality-0 only: three of the nine scored shared events have no data on one member, so each pair had only
  two scorable joint events, less than the pre-registration assumed.
- The "background-led" rule and the 95th-percentile dip rule are as pre-registered; both are coarse.
- The CME attribution rests on the DR25 release notes' description of Q8 and Q12 and on the quality bits and
  background excesses measured here; we did not read the notes' per-cadence anomaly tables (PDF).
- Made by AI agents for MV2 of Munim, Inc.; not yet checked by a person.

## Files

`pair_events.py`, `test_pair_events.py` (root; `python -m unittest -v test_pair_events`), and
`results/2026-10-18-pair-events-0.1.0/{events.csv, pairs.csv, report.md, summary.json}`.
Re-run: `python pair_events.py --data-dir <cache> --out-dir out/pairs`.
