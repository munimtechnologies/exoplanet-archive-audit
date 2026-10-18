# Pre-registration: KOI-1209.01, is the Archive's 272.09 d or DR25's 408.42 d period right? (koi1209-events-v1)

By MV2 of Munim, Inc., 2026-10-18. Written by AI agents working in his name before the job runs; no person has
checked it yet. Text CC BY 4.0, code Apache-2.0. Committed before the job reads any light curve; scored in
public, misses included.

## Why

`findings/2026-10-18-shared-events-results.md` found six "KOI-1356-class" orphans: multi-event CANDIDATEs
whose DR25 TCE shares exactly one transit time at a period that is not a simple ratio. KOI-1356.01 was just
settled by its light curve (both catalogued periods wrong). KOI-1209.01 (KIC 3534076) is the only other
member deep enough for the same per-epoch test. Rows re-read 2026-10-18 (TAP `cumulative`; DR25 TCE and
Robovetter rows from the shared-events job):

| source | P (d) | T0 (BKJD) | dur (h) | depth (ppm) | S/N | events in Q1-Q17 | notes |
|---|---|---|---|---|---|---|---|
| Archive `cumulative` (Q1-Q16 values carried; no DR25 TCE link, `koi_num_transits` empty) | 272.0868353 +- 0.00085 | 378.13721 | 2.7145 | 5,572 | 21.5 | 5 | CANDIDATE, all FP flags 0; R* 0.791 Rsun, Teff 5,587 K, Rp 5.95 Re, insolation 0.93, Kp 15.17 |
| DR25 TCE 003534076-01 | 408.415 | 378.141 | 3.545 | 5,329 | 34.5 | 3 | Robovetter 0.000 FP, NT = 1: INDIV_TRANS_CHASES_MARSHALL, INCONSISTENT_TRANS, CENT_FEW_DIFFS |
| Lissauer et al. 2024 Table 1 | 272.08627407 | (not listed; Archive T0 used) | | | | | status PPNN |

Predicted epochs (BKJD). Archive / Lissauer, 272.087 d: **378.137, 650.224, 922.311, 1,194.398, 1,466.485**.
DR25, 408.415 d: **378.141, 786.556, 1,194.971** (the next, 1,603.4, is after Q17). The TCE's period is
within 0.07 % of 3/2 of the Archive's, but its second and third epochs miss the Archive's nearest epochs by
0.29 d and 0.57 d, three to five times the transit duration, so the two ephemerides predict different flux at
every epoch but the first.

MAST holds all 17 long-cadence quarters for KIC 3534076 (Q1-Q17; no short cadence). From spacecraft-wide gaps
seen on KIC 7363829, none of the seven epochs above falls in a known gap, but this star's own gaps are not
known until the job runs.

## Prior art (checked 2026-10-18)

Web search for "KOI-1209", "KOI 1209" and "KIC 3534076" finds no paper discussing this object. Lissauer et
al. 2024 keep it as PPNN at 272.086 d. We have not checked the habitable-zone candidate lists of Kane et al.
2016 or Hill et al. 2018 for it. The DR25 TCE and its Robovetter flags are public (NASA kepler-robovetter
repository) but, as far as we can find, no one has written down that DR25's only detection of this star is a
different period from the Archive's, or tested the epochs in the light curve.

## Job

`koi1209-events-v1` (1 GB, one CPU). Same recipe as `koi1356-events-v1`: fetch the published `kepler_alias.py`
0.3.0 and its tests, record sha256s, run its 20 tests and `event_check`'s 12 tests, then
`event_check.py 0.1.0 --kepid 3534076 --dur-h 3.1 --hypotheses "Q1-Q16=272.0868353@378.13721,
DR25-TCE=408.415@378.141,Lissauer2024=272.08627407@378.13721" --anchors 378.137,650.224 --max-n 12 --step 0.05`.
Box duration 3.1 h (between 2.71 and 3.55 h). Status rules are unchanged from the KOI-1356 pre-registration:
deep = D >= 0.5 D_ref and D/err >= 7; absent = D < 0.3 D_ref and (D_ref - D)/hypot(err, err_ref) >= 5.
D_ref is the event at 378.137.

A caution written before the run: with a 3.1 h box the core holds only four or five long cadences, so a
5,500 ppm event could have S/N below 7 and come out "unclear" rather than "deep". The Archive's S/N of 21.5
over five events suggests per-event S/N near 10; DR25's 34.5 over three suggests nearer 20. "absent" needs
only 5 sigma against the reference, so exclusions should still be decisive.

## Predictions

1. `kepler_alias` 0.3.0 is fetched; its 20 tests and the 12 `event_check` tests pass.
2. 378.137 is deep with S/N >= 10; its best centre is within 0.05 d of 378.137.
3. **The test: DR25-TCE is excluded, because 786.556 is absent.** 1,194.971 is also absent.
4. **Q1-Q16 and Lissauer2024 are not excluded:** none of 650.224, 922.311, 1,194.398, 1,466.485 is absent, and
   at least three of the four are deep. (The verdict "supported" needs all four deep; "unclear" because one
   epoch has S/N < 7 would count as a partial hit of this prediction, stated as such.)
5. Two-transit aliases through 378.137 and 650.224: n = 1 (272.087 d) is not excluded; n = 2 to 12 are all
   excluded. The two-transit period from the best centres is within 0.1 d of 272.087.
6. Blind search: the five 272.087 d epochs are the five highest-S/N dips (each within 0.3 d, any order), and
   rank 6's robust S/N is less than half of rank 5's.
7. At most one of the seven named epochs is no_data.

Exploratory, no prediction: the depths at each epoch (a 2.7 h, 5,500 ppm transit on a 0.79 Rsun star at
272 d needs a high impact parameter; equal depths would be a check); the coverage and gap tables.

## What each outcome would mean

- 3 and 4 hold: DR25's only detection of this star folded one real transit with two flat epochs, exactly as
  its flags say, and was rightly rejected; but as a result the DR25 KOI catalogue never listed a five-transit,
  5,500 ppm candidate at about Earth's insolation (Archive values, context only). The Archive keeps it only
  because Q1-Q16 CANDIDATE rows are carried forward; Lissauer et al. 2024 kept it too. We would claim the
  mechanism and the per-epoch evidence, not planethood.
- 3 fails (786.556 deep): the TCE is right and the Archive and Lissauer periods are wrong, a second KOI-1356.
- Both excluded, or mostly unclear: written up as found.

Nothing will be sent to the Exoplanet Archive or the authors without Sheehan's approval.
