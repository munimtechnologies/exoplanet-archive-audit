# Pre-registration: do Kepler's 600 "orphan" candidates match anything the final pipeline run found? (koi_orphans 0.1.0)

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Code Apache-2.0, text and data CC BY 4.0. Committed **before** the job runs; scored in public, misses included.

## Why

The cumulative KOI table lists 1,977 CANDIDATE KOIs. For 600 of them the parameters still come from an
older table (koi_parm_prov: 461 from Q1-Q16, 139 from DR24), because the final run of the pipeline (DR25)
did not deliver them. Thompson et al. 2018 (sec. VI.1) say such KOIs, with no DR25 observed TCE matched
to them, were left out of the DR25 table. Their CANDIDATE label is inherited through the DR25
supplemental table. They were not checked for period aliases. Three of them are already known to repeat a
confirmed sibling's transits (findings/2026-10-17-koi-dupes-results.md): K01101.02 (= Kepler-768 b),
K02167.02 (1/11 of Kepler-1129 c) and K01922.02 (1/7 of Kepler-1016 c; pixel test in
findings/2026-10-17-orphan-pixels-results.md).

Archive counts on 2026-10-17 (TAP): 437 of the 600 sit on a star with no DR25 TCE at all. The other
163 (on 148 stars) share their star with 343 DR25 TCEs. This census asks, for each of those 343 pairs,
whether the orphan's transits fall on the TCE's at a whole or simple-fraction period ratio.

## Method (koi_orphans 0.1.0)

- Inputs: cumulative table (period, mid-time, duration, provenance, TCE federation) and
  q1_q17_dr25_tce (period, mid-time, duration, depth, SNR, rogue flag), both live TAP queries.
- Ratio: the fraction a/b (a, b <= 12) nearest Po/Pt. The pair is commensurate if the coincident events
  drift by <= 0.5 d over the 1,460-day mission (|b Po - a Pt| x 1460 / (b Po)).
- Phase: offsets can only be multiples of g = Po / a, so the mid-time difference is folded into
  [-g/2, g/2). same_events if |offset| <= (Do + Dt) / 24, as in koi_dupes. p_phase = 2 window / g is
  the chance a random epoch passes. kind is same (1:1), integer (k or 1/k), or rational.
- Null: each orphan star's TCE set is swapped with another orphan star's (100 random derangements, seed
  20261017). The period mix stays the same and only the link to the star is broken.
- Control: every DR25-parameter CANDIDATE (1,377) tested against its own federated TCE.
- Also run, unscored: the same census for CONFIRMED orphans. And the job tries to save Lissauer et al.
  2024's Table 1 (its dispositions for about 9,700 KOIs, from CDS or the arXiv source), so each flagged
  orphan can be looked up by hand.

18 unit tests. The expected values in the tests were worked out by hand from Archive rows (for example,
K02167.02 against DR25 TCE 2 of KIC 6041734: ratio 1/11, drift 0.0150 d, offset +0.0125 d, window
0.455 d).

## Predictions

1. All 18 unit tests pass.
2. The inputs match today's counts: 600 +- 5 CANDIDATE orphans (461 Q1-Q16, 139 DR24, each +- 5),
   163 +- 3 of them with a DR25 TCE on the star, 343 +- 5 orphan-TCE pairs, 34,032 TCE rows.
3. Control: at least 95 % of the 1,377 DR25-parameter CANDIDATEs come out same_events at 1:1 with their
   own TCE, and at least 98 % same_events of any kind.
4. Known cases: K02167.02 is same_events at 1/11 against the TCE federated to K02167.03. K01922.02 is
   same_events at 1/7 against the TCE federated to K01922.03. K01101.02 is same_events at 1:1 against
   the TCE federated to K01101.01.
5. Chance: the null averages <= 1.5 same_events orphans per shuffle.
6. The real count of same_events orphans is between 3 and 15, and at least 2 above the null mean.
7. At most 6 orphans are same_events at 1:1. For each of them the TCE is federated to another KOI on the
   same star, so the orphan duplicates a DR25 KOI. A 1:1 TCE with no KOI of its own would mean that
   federation missed it.
8. At least half of the same_events orphans match a TCE federated to a CONFIRMED KOI.

## How it will be read

A same_events orphan is a lead, not a finding. Before anything is claimed about one, it gets a hand
check: its history across the Q1-Q6 to Q1-Q16 KOI tables, the disposition in Lissauer et al. 2024 Table 1
if saved, and the Archive's alias service. Claims are made only for same or integer kinds with p_phase
<= 0.2. A rational-ratio match needs a pixel test first. An orphan that is unrelated or no_tce is not
shown to be real. It only means DR25 did not see anything related on that star.

## Prior art and limits

- Thompson et al. 2018 sec. VI.1-2: orphans were left out, and federation compares DR25 TCEs with
  known KOIs only at 1x and 2x. Coughlin et al. 2014 never compares objects on the same star.
- Lissauer et al. 2024 (PSJ 5, 152) start from the same 9,564-KOI cumulative table and correct
  aliases case by case (KOI-521.02, 730.03, 2248.02, 1353.03), with an S/N >= 7.1 cut for PCs. Our
  reads of the arXiv HTML found no mention of KOI-1101, 1922 or 2167. Their full Table 1 (a separate
  file) may already mark some of these orphans false positives, which would make our flags a
  replication. That check comes before any claim.
- Orphan ephemerides come from short, old data sets, and their periods can be off. The 0.5 d drift
  limit may miss real aliases whose old period is too imprecise.
- Durations are catalogue values, and the window (the sum of both durations) is generous. The null
  measures what that costs.
