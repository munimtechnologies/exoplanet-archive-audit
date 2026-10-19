# Pre-registration: the rule that will pick one Rubble variant, fixed before the development scan ran

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-10-19 ~10:20 UTC by AI agents working in his name; not
checked by a person. Apache-2.0 code, CC BY 4.0 text.

## Why this note exists

`findings/2026-10-19-rubble-probe-results.md` (exploratory, nine TCEs) found that DR25's Rubble rule, applied
as the paper words it to the public DV time series, flags transits DR25 kept, while counting events with any
in-transit cadence nearly reproduces DR25's `nrealt`. Job `rubble-scan-v1` (`scan_rubble.py` 0.1.0, queued at
~09:40 UTC today) will tabulate 24 variants (cadence source x window x threshold) on 60 seeded development
stars, and list 200 reserve stars it never downloads.

The plan said "pick ONE variant in writing" after the scan. Picking by eye after seeing 24 columns of numbers
would let the choice drift toward whatever looks best, and the margins for the reserve bars could be chosen to
fit. So the selection rule and the bar formulas are fixed here, in code with hand-worked tests, before the scan
has started. At the time of writing `compete-results/rubble-scan-v1/` did not exist on the runner. The order is
verifiable in public: this commit's timestamp against the `started` stamp that the scan writes into its
`summary.json`, which will be published with the scan results.

## The rule (pick_variant.py 0.1.0, R1-R6)

Input is the scan's `variants.json`: per variant, a tp/fp/fn/tn table comparing "at least one real event fails
the variant" with DR25's per-TCE `iflag0` (RUBBLE), and for TCEs whose only per-event flag is RUBBLE, how many
have a variant fail count exactly equal to `nrealt - ngoodt` ("Rubble-only exact").

- **R1 power.** The development scan is underpowered if fewer than 20 scored TCEs have `iflag0 = 1` or fewer
  than 8 are Rubble-only. Then nothing is chosen; a second development batch would be drawn from stars outside
  both lists with a new seed, pre-registered first.
- **R2 floor.** error = fp + fn over all scored TCEs. If every variant has error above 20 % of n (tested as
  5 x error > n, no floats), the result is **negative**: no public variant reproduces `iflag0` well enough, and
  that is published as the result. No reserve test follows.
- **R3 candidates.** Variants with error <= min_error + max(1, ceil(min_error / 10)).
- **R4 DR25's value.** If any candidate uses threshold 0.75, only those remain.
- **R5 pick.** The candidate with the most Rubble-only exact TCEs; ties go to the higher threshold, then window 2
  over 1, then the source order init, white, pdc, resid.
- **R6 bars for the reserve.** From the chosen variant's development rates: recall >= dev - 0.10; precision >=
  dev - 0.10; Rubble-only exact fraction >= dev - 0.15; `nrealt` exact fraction for the chosen cadence source >=
  dev - 0.10. Bars are floored at 0 and rounded to 3 decimals; reserve rates are rounded to 3 decimals before
  comparing. The reserve is underpowered (reported, not scored) if its scored rows have fewer than 30 `iflag0`
  TCEs or fewer than 10 Rubble-only TCEs. **PASS** = every bar met; otherwise **FAIL**. Scored once from counts,
  misses explained afterwards, never re-scored.

Why these numbers: 20 % is the bar the design already named for "worth testing at all"; a 10 % tolerance on
error keeps near-ties in play so that DR25's own 0.75 can win when it is close; recall and precision margins
of 0.10 on ~50 flagged development TCEs roughly cover binomial scatter at that size; the Rubble-only margin is
wider (0.15) because that count will be small (about 10-20 TCEs on 60 stars).

## What happens next, in order

1. `rubble-scan-v1` finishes. `pick_variant.py --variants <scan>/variants.json` is run as a job and its
   `decision.json` / `decision.md` are published with the scan results and code in one commit. If the status is
   `negative` or `underpowered_dev`, that note is the result of this lane and no reserve job is written.
2. If a variant is chosen, `scan_rubble.py` gets a version bump adding a reserve mode (score only the stars in
   `sample.json`'s `reserve_never_downloaded` list, one fixed variant reported alongside all 24 for the record),
   committed with `test_first`. The reserve job is gated on that commit and on the decision note being live.
3. The reserve is scored with `pick_variant.py --reserve`, published as `findings/<date>-rubble-reserve-results.md`
   whether it passes or fails.

## Limits

- The rule scores agreement with DR25's `iflag0` per TCE, not whether DR25's choice was right.
- `iflag0` is set when at least one event failed Rubble; a variant that fails a different event of the same TCE
  still counts as agreement at the TCE level. The Rubble-only exact count is the finer check.
- Everything here is made with AI agents in MV2's name and has not been checked by a person.

MV2, Munim, Inc., mv2@munimtech.com
