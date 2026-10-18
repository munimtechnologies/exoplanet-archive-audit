# KOI-1209.01: five equal transits that no linear ephemeris fits; the Archive's 272.087 d misses two of them, and DR25's 408.415 d folds two with a flat epoch (koi1209-events-v1 scored: 3 held, 3 partial, 1 missed)

By MV2 of Munim, Inc., 2026-10-18. Made with AI agents working in his name; no person has checked it yet.
Text CC BY 4.0, code Apache-2.0. Scores the pre-registration `findings/2026-10-18-koi1209-events-prereg.md`
(committed 2026-10-18 before the job ran) and its addendum `findings/2026-10-18-koi1209-prior-art-addendum.md`.
Job: `koi1209-events-v1`, run 2026-10-18 08:23-08:26Z in a sealed container (python:3.12, astropy 6.1.4,
numpy 2.1.3). Outputs: `results/2026-10-18-koi1209-events-0.1.0/`. Tool: `event_check.py` 0.1.0 (sha256
84c017aa...7cd4b007) on the published `kepler_alias.py` 0.3.0 (sha256 3cb894ca...5a0434), both recorded in
`fetched.json`. Light curves: Kepler long cadence, quality 0, PDCSAP, all 17 quarters of KIC 3534076
(53,097 points, BKJD 131.51-1591.00). Box duration 3.1 h.

## Score

| # | Prediction | Result | Held |
|---|---|---|---|
| 1 | `kepler_alias` 0.3.0 fetched; its 20 tests and the 12 `event_check` tests pass | version 0.3.0; `Ran 20 tests ... OK`, `Ran 12 tests ... OK` (stderr.txt) | yes |
| 2 | 378.137 deep, S/N >= 10, best centre within 0.05 d | 5,171.0 +- 229.3 ppm, S/N 22.6, best centre 378.167 (0.030 d) | yes |
| 3 | DR25-TCE (408.415 d) excluded because 786.556 is absent; 1,194.971 also absent | 786.556: 94.3 +- 296.3 ppm, **absent, 13.6 sigma below the reference**; DR25 excluded. But 1,194.971 is **deep**: 5,348.4 +- 248.5 ppm, S/N 21.5 | partial |
| 4 | Q1-Q16 and Lissauer2024 (272.087 d) not excluded; >= 3 of the four later epochs deep | **Both excluded.** 922.311: -1,395.6 +- 853.3 ppm, absent (7.4 sigma); 1,194.398: no_data; 650.224 and 1,466.485 deep | **no** |
| 5 | Alias n = 1 (272.087 d) not excluded; n = 2-12 excluded; two-transit period from best centres within 0.1 d of 272.087 | n = 1 excluded (statuses `ddand`); n = 2-12 all excluded; two-transit period 272.067 (0.02 d) | partial |
| 6 | The five highest-S/N blind dips are the five 272.087 d epochs, each within 0.3 d; rank 6 robust S/N < half of rank 5 | Ranks 1-5 are at 1,466.463, 650.213, 378.163, 1,194.963, 922.513 (S/N 20-28). Four are within 0.3 d of an epoch; 1,194.963 is 0.565 d from 1,194.398. Rank 6 (450.9 +- 77.4 ppm at 463.513) has robust S/N 5.5 vs 19.4 | partial |
| 7 | At most one of the seven named epochs is no_data | Only 1,194.398 (the Archive epoch; a 0.12 d hole of flagged cadences sits on it) | yes |

Sigma values: (D_ref - D) / hypot(err, err_ref) with D_ref = 5,171.0 +- 229.3 ppm. 786.556: 5,076.7 / 374.7 = 13.6.
922.311: 6,566.6 / 883.6 = 7.4. The 922.311 box reads a negative deficit with a large error because the real
transit, 0.19 d later, falls inside its out-of-transit baseline window.

## What the light curve shows

Five dips of about the same depth, and nothing else above 10 % of that depth in 17 quarters:

| event | box best centre (BKJD) | blind-search depth (ppm) | S/N | O-C vs Archive 272.0868 d (d) | O-C vs best linear fit (d) |
|---|---|---|---|---|---|
| 1 | 378.167 | 4,908.9 +- 196.6 | 25.0 | +0.030 | -0.032 |
| 2 | 650.234 | 4,753.6 +- 181.1 | 26.3 | +0.010 | -0.102 |
| 3 | 922.501 | 4,622.3 +- 225.6 | 20.5 | **+0.190** | +0.028 |
| 4 | 1,194.991 (see note) | 5,348.4 +- 248.5 | 21.5 | **+0.593** | +0.381 |
| 5 | 1,466.475 | 4,816.8 +- 172.5 | 27.9 | -0.010 | -0.272 |

Best centres come from `event_check`'s scan (+-0.5 d, 0.01 d step) around each catalogue epoch; their precision
is roughly a cadence (0.02 d), not a formal fit. Best linear fit by unweighted least squares to the five
centres: P = 272.137 d, T0 = 378.199 BKJD. Weighted mean depth 4,858 ppm; the largest departure is event 4
at +2.0 sigma, so the five depths are consistent with one body.

Note on event 4: the cutout (`cutouts.csv`, event 1194.971) has no cadences between 1,194.732 and 1,194.977;
the two in-transit cadences seen (1,194.977 and 1,194.997 at 0.9948 and 0.9944) are the end of the transit,
and the point at 1,195.038 is back at 0.9995. The ingress is inside a 0.245 d hole, so the centre is probably
earlier than the box value, about 1,194.93-1,194.99. Either way it is more than 0.5 d after the Archive's
epoch, which itself sits on a 0.12 d hole (1,194.405-1,194.527) and so reads no_data. Event 3 is fully
covered: six cadences from 922.458 to 922.581, bottom at 922.499-922.540.

**Reading.** All five dips are real transits of one period near 272.1 d (every n >= 2 alias is excluded by
flat epochs, and no sixth dip exists), but they do not lie on a straight line: against the best linear
ephemeris the residuals run from -0.27 to +0.38 d, and against the Archive's they run to +0.59 d. The
Archive's linear ephemeris (272.0868 d, from the Q1-Q16 fit) is right for transits 1, 2 and 5 and misses 3
and 4 by more than a transit duration, so a box test at its epochs calls it "excluded". DR25's only detection
of this star, TCE 003534076-01 at 408.415 d, is the fold of transits 1 and 4 (816.83 d apart, exactly twice
408.415) with a flat epoch between them at 786.56 BKJD, 13.6 sigma below the transit depth. That is what its
Robovetter flags said (INDIV_TRANS_CHASES_MARSHALL, INCONSISTENT_TRANS), and it was rightly rejected; but
the consequence is that the DR25 pipeline reported no 272 d signal on this star at all, even though three of
the five transits stay in phase at that period. Why the DR25 search preferred the two-transit fold to the
three-transit one cannot be told from the public outputs.

## Prior art: the timing variation is already published

Holczer et al. 2016 (ApJS 225, 9; arXiv:1606.01744), the Kepler long-cadence transit-timing catalogue, read
2026-10-18 from the journal's HTML and machine-readable tables:

- Table 2 (ephemerides), line for 1209.01: T0 = 311.176783 +- 0.467484 (BJD - 2,454,900, i.e. 378.1768 BKJD),
  P = 272.14512529 +- 0.00049835 d, duration 3.6948 h, depth 5,931 ppm, per-transit S/N 38.6, scatter
  ratio 1.30. Their period and T0 agree with our best linear fit (272.137 d, 378.199) to 0.01 d in P and
  0.02 d in T0; their 0.47 d T0 error is the timing scatter itself.
- Table 5 (KOIs with significant long-term TTV) lists 1209.01: 5 timings, cosine model, TTV period
  2,480 +- 370 d, amplitude 3,100 +- 1,400 min, residual scatter 100 min, multiplicity 1, no reference.
  With five timings over 1,088 d and a model period longer than the baseline, the amplitude is loosely
  constrained, as their errors say.

So the fact that KOI-1209.01's transits are not on a linear ephemeris is **not new**: Holczer et al. found it
in 2016. The per-transit O-C values are in their Table 3 (295,187 rows; too large for us to read this run), and
a follow-up job (`findings/2026-10-18-koi1209-times-prereg.md`) will extract them and compare with trapezoid
fits to our cutouts.

What is new here, as far as we can find (web search for KOI-1209, K01209 and KIC 3534076 on 2026-10-18 finds
only the Archive's pages and the Holczer table rows): (1) the per-epoch demonstration, with open code and
data, that the Archive's default ephemeris misses two of the five transits by 0.19 and 0.59 d, and that the DR25
TCE is a two-transit fold with a 13.6 sigma flat epoch; (2) the chain that follows from the timing variation:
DR25 found this star only at the wrong period, the Robovetter rejected that TCE, the star never got a DR24 or
DR25 KOI row, and so a five-transit, 5,000 ppm candidate at 0.9-1.5 times Earth's insolation (addendum, section
2) is absent from the Kepler habitable-zone catalogue of Kane et al. 2016 while the Archive's cumulative
table still carries it as a CANDIDATE with Q1-Q16 numbers and no TTV flag. We claim the mechanism and the
measurements, not planethood: the addendum's caution stands that a 2.7-3.7 h transit is about a quarter of
what a central transit of the catalogued star would last, so the geometry is grazing, eccentric or blended.

## Limits

- Box depths against a straight local baseline; no transit-shape fit, no limb darkening, no centroid or pixel
  test. "deep" and "absent" use the thresholds fixed in the pre-registration. Mid-times are box scan values.
- Quality-0 PDCSAP only. Event 4's ingress and the Archive's fourth epoch both sit in short holes of flagged
  cadences, which is why the fourth centre is uncertain by a few hundredths of a day.
- Made by AI agents for MV2 of Munim, Inc.; not yet checked by a person. Nothing has been sent to the
  Exoplanet Archive or to any author. No helpdesk note is drafted: a linear fit to a TTV system is not an
  Archive error, and the DR25 TCE is a pipeline product.

## Files

`results/2026-10-18-koi1209-events-0.1.0/`: `report.md`, `summary.json`, `hypotheses.csv`, `aliases.csv`,
`dips.csv`, `coverage.csv`, `gaps.csv`, `cutouts.csv` (+-2 d of flux around every named epoch), `fetched.json`
and `fetch_tool.py`. Tool: `event_check.py` with `test_event_check.py` at the repository root.
Re-run: `python event_check.py --data-dir <cache> --out-dir out --kepid 3534076 --dur-h 3.1 --hypotheses
"Q1-Q16=272.0868353@378.13721,DR25-TCE=408.415@378.141,Lissauer2024=272.08627407@378.13721" --anchors
378.137,650.224 --max-n 12 --step 0.05`.
