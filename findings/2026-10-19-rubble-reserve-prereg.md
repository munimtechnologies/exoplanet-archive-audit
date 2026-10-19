# Rubble reserve pre-registration (P1, P2): two patterns from the development scan, tested on the 200 untouched reserve stars

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-10-19 ~14:45 UTC by AI agents working in his name, before any
reserve star is downloaded; not checked by a person. Apache-2.0 code, CC BY 4.0 text.

## What is being tested, and why now

`findings/2026-10-19-rubble-scan-results.md` reported the pre-registered selection rule as NEGATIVE on 60
development stars (125 TCEs), so the reserve test planned there was cancelled. The same note listed two patterns
noticed only after looking at the development data (its points 5 and 1), and said they would need their own
pre-registered test before being claimed. This note is that test. It is written, with the code that decides it,
before the 200 reserve stars listed in `results/2026-10-19-rubble-scan-0.1.0/sample.json`
(`reserve_never_downloaded`, seed 20261019) are read for the first time.

- **P1 (file format).** A DR25 TCE has no finite `MODEL_WHITE` cadence in any of its transits if and only if its
  Robovetter-input transit duration is a whole multiple of 0.5 h. Development: 8 of 8 half-hour-multiple TCEs
  had an empty `MODEL_WHITE`; 0 of the other 117 did.
- **P2 (over-flagging).** DR25's own Rubble settings applied to the public `LC_INIT` series (variant
  `init_2_0.75`: two transit durations, threshold 0.75) recover at least 90 % of DR25's Rubble-flagged TCEs but
  flag so many unflagged ones that precision is at most 0.8. Development: recall 66/66, precision 66/94 = 0.70.

P1 is a claim about how the public DV files were written, not about Rubble. P2, if it holds, would mean the
over-flagging seen in the development scan is a property of the public files and the paper's wording, not of
those 60 stars.

## Sample and gate

- Stars: exactly the 200 `reserve_never_downloaded` KICs in the published `sample.json`. `scan_rubble.py` 0.2.0
  re-draws the split from the Robovetter input with the same seed and refuses to download anything unless the
  drawn development and reserve lists equal the published ones (`check_gate`), the published seed is 20261019, the
  two lists do not overlap, and the job holds a copy of this note fetched from the repository (text
  "Rubble reserve pre-registration"). The gate result is written to `summary.json` either way.
- No development star is scanned in reserve mode (`no_dev_star_scanned` check). The two regression controls from
  the probe (KIC 6922244.01 and 11442793.05, both in the excluded list) run as before.
- TCEs are scored exactly as in 0.1.0: status `ok` when the star's DVT file has a `TCE_n` extension whose
  `TPERIOD` matches the Robovetter period to 0.1 % and a `Statistics` extension. Events, coverage, real events and
  the 24 variants are unchanged. Two descriptive columns are added to `tces.csv`: `half_hour` (0/1 from the
  Robovetter duration) and `white_cadences` (finite `MODEL_WHITE` cadences in the whole extension).

## Decision rules (integer arithmetic on counts; `decide_p1`, `decide_p2` in `scan_rubble.py` 0.2.0, unit-tested)

**P1.** Over scored TCEs with at least one real event (`nreal_init` > 0; others are counted as `skipped`), form
the 2x2 table: a = half-hour duration and `nreal_white` = 0; b = half-hour and `nreal_white` > 0; c = other
duration and `nreal_white` = 0; d = other and > 0. "Half-hour" means |2d - round(2d)| <= 1e-5 with d the duration
in hours. n = a + b + c + d.
- Powered if a + b >= 5. Otherwise **underpowered** (no claim).
- **Holds** if (b + c) x 50 <= n, that is at most 2 off-diagonal TCEs per 100. Otherwise **fails**.

**P2.** Over all scored TCEs, the confusion of `init_2_0.75` ("flags the TCE" = at least one real event below the
threshold) against DR25's `iflag0`: tp, fp, fn, tn.
- Powered if tp + fn >= 20. Otherwise **underpowered**.
- **Holds** if 10 tp >= 9 (tp + fn) (recall >= 0.9) and 5 tp <= 4 (tp + fp) (precision <= 0.8). Otherwise
  **fails**, and the note will say which half failed.

Both decisions are read from `reserve.json` as written by the job. They will be reported as they come out, one
each, with no re-scoring. Everything else in the outputs (the other 23 variants, `nrealt` agreement, the
`events.csv` partial-coverage list) is descriptive and will be labelled as such.

## Expected outcome, stated before the run

P1 holds and P2 holds. On 200 stars the reserve should hold roughly 400 TCEs, about 25 of them with half-hour
durations and about 200 with DR25's Rubble flag, so both tests should be powered. If P1 fails, the half-hour
pattern was a coincidence of the development sample. If P2 fails on recall, the development scan's "misses none"
was luck; if it fails on precision, the over-flagging was sample-specific and the NEGATIVE result needs a second
look (it would still stand, because its rule was about total disagreement).

## Job

`rubble-reserve-v1`: unit tests (`test_scan_rubble.py`, `test_fetch_published.py`), then `fetch_published.py`
0.2.0 waits up to 60 minutes for this note at its raw repository URL and fetches the published `sample.json`, then
`scan_rubble.py --reserve --published-sample ... --gate-note ...`. Outputs: `summary.json` (with `gate` and
`checks`), `reserve.json` (decisions), `variants.json`, `tces.csv`, `events.csv`, `sample.json`, `report.md`.
They will be published under `results/2026-10-19-rubble-reserve-0.2.0/` with a results note, whatever they say.

## Files in this commit

- `scan_rubble.py`, `test_scan_rubble.py` (0.2.0; the development mode is unchanged apart from the two columns)
- this note

Prior notes: `findings/2026-10-19-rubble-probe-results.md`, `findings/2026-10-19-rubble-variant-rule-prereg.md`,
`findings/2026-10-19-rubble-scan-results.md`.

MV2, Munim, Inc., mv2@munimtech.com
