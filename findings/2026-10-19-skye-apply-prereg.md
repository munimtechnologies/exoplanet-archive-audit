# Pre-registration: applying the validated open Skye variant to long-period KOIs, and an amended Robnik cross-check

MV2 of Munim, Inc., 2026-10-19 ~03:50Z. Written by AI agents working in his name; no person has checked it yet. Text
CC BY 4.0, code Apache-2.0. Code: `skye_apply.py` 0.1.0 and `test_skye_apply.py` (hand-worked tests), committed
together with this file. Follows the outcome rule of `findings/2026-10-18-skye-inv-prereg.md`: "P3 and P4 hold ...
Only then will a **separate** pre-registration apply it to KOI-5269.01, KOI-5227.01 and the candidates DR25 never
scored." They held (`findings/2026-10-19-skye-inv-results.md`). This is that separate pre-registration.

## What is applied (frozen; nothing is tuned here)

The variant `scored_only_real_events_w0.25_data_bins`, exactly as tested on DR25's inverted run by `skye_inv` 0.1.0.
Its functions are copied unchanged into `skye_apply.py`; one new function, `frozen_bins`, returns the bad bins that
`run_variant` builds internally so they can be applied to KOIs.

- **Bins:** per skygroup, the kept events of the DR25 OBS TCEs with P > 45 d that are in the DR25 Robovetter input
  (`results/2026-10-18-skye-census-0.2.1/tce_skye.csv`, rv_found = 1), skygroups and quarters from that folder's
  `skygroups.csv`.
- **Events:** t0 + nP inside the star's long-cadence quarters, kept only within 0.25 d of a valid cadence (finite TIME
  and PDCSAP_FLUX) in the Q1-Q17 files of KIC 9018021 or KIC 6359929.
- **Rate:** over the bins of the skygroup's quarters that hold a valid cadence; cutoff R + 3 sqrt(R), five passes.
- **KOIs:** every row of v3's `results/2026-10-18-skye-census-0.2.1/koi_skye.csv` (2,257 cumulative-table KOIs with
  P > 45 d). Their events are recomputed and must equal v3's `event_times`. Then: kept events; flagged = kept events
  in a bad bin of the KOI's skygroup; good = kept - flagged; eligible = kept >= 3; **would_fail = eligible and good
  < 3**.

**Design choice, fixed now:** eligibility and would_fail use kept events only (not every ephemeris time). DR25 counts
good transits among transits that have data, and the variant already uses kept events for the TCE flags it was
validated on. Groups as in v3: `dr25_pc` (DR25 KOI table, CANDIDATE), `dr25_skye` (DR25 KOI table, SKYE among the
INDIV_TRANS flags of its comment), `never_dr25` (cumulative CANDIDATE absent from the DR25 KOI table).

## Safeguards built into the job

1. **Gate:** the job fetches this file and `skye_apply.py` from the repository's main branch; if this file is not
   live or the code differs, it stops.
2. **Reproduction:** on OBS the frozen variant must give skye_diag 0.1.0's counts exactly (tp 3,829, fp 1,364, fn 446,
   tn 8,313) twice: through `run_variant`, and by applying the `frozen_bins` output to the TCEs. Otherwise it stops
   before any KOI is scored.

## What has been seen already (stated so the reader can discount it)

- v3's per-KOI results (published), including v3's P5-P8: dr25_skye flagged 87 / 109; dr25_pc fail 7 / 668;
  never_dr25 fail 22 / 415 (p = 4.5e-5); K05269.01 and K05227.01 would fail under v3 (skygroup 66; v3 flagged 631.6306
  and 1003.1369 for K05269.01, 1002.9789 for K05227.01; each has 3 events).
- The 13 KOIs looked up by hand in Robnik et al.'s table, listed in `findings/2026-10-18-skye-v3-robnik-crosscheck-prereg.md`.
- **Not seen:** the frozen variant's bad bins or flags for any KOI, and any join of the KOIs with Robnik et al.'s list
  beyond those 13.

## Predictions (thresholds fixed here)

| # | Prediction | Threshold |
|---|---|---|
| A0 | Unit tests pass | all of `test_skye_apply.py` |
| A1 | OBS reproduction | both routes give tp 3,829 / fp 1,364 / fn 446 / tn 8,313 (else the job stops) |
| A2 | KOI data check | 2,257 rows; every row has a skygroup; every row's recomputed events and skygroup equal v3's; valid cadences = 128,918 |
| A3 | Named candidates | K05269.01 and K05227.01 both would_fail = 1 |
| A4 | Census | never_dr25 fail fraction >= 2 x max(dr25_pc fail fraction, 0.02) and binomial tail p <= 0.01 (v3's P8 form) |
| A5 | Sanity: few DR25 candidates fail | dr25_pc fail fraction <= 0.10 |
| A6 | Sanity: DR25's own Skye KOIs are seen | dr25_skye KOIs with >= 1 flagged kept event >= 70 % |

**Our forecast, stated before anything is run:** A1 and A2 hold. A5 and A6 held under v3 and should hold. A3 is a coin
flip: both stars sit in skygroup 66 near P = 371.5 d, and removing rogue TCEs from the bins may clear bin 871 (BKJD
1002.5-1003.5); we lean slightly toward both still failing. A4 more likely than not holds, but with fewer flagged
bins the never_dr25 fail count may drop below what the test needs.

## Amendment of the Robnik et al. 2026 cross-check (`findings/2026-10-18-skye-v3-robnik-crosscheck-prereg.md`)

That cross-check never ran: it was conditional on v3's data check (P2), which failed. It is amended in two places only:

1. Its condition "runs only if v3's P2 holds" becomes "runs only if A1 and A2 hold, and Robnik et al.'s table has 406
   data rows and the cumulative snapshot matches sha256 `df551272...`" (otherwise reported, nothing claimed).
2. `would_fail` and `eligible` are the frozen variant's (kept events), not v3's.

Everything else is unchanged: population (cumulative CANDIDATE, P > 45 d, eligible, the star's only CANDIDATE or
CONFIRMED KOI, the same 13 exclusions); Q1 at least 10 failing KOIs; Q2 listed fraction among fails >= 2 x that among
passes with one-sided Fisher p < 0.01; Q3 strictly higher listed fraction among fails within 340-400 d. Reported, not
scored: the in-DR25-only comparison and the split of the 406 listed KOIs by cumulative disposition. The code is copied
unchanged from `robnik_crosscheck.py` 0.1.0. Forecast: Q1 holds; Q2 and Q3 are open questions.

## How each outcome reads

- Gate or A1 fails: void; nothing about KOIs was computed.
- A2 fails: the KOI inputs were not read as intended; nothing is claimed.
- A5 or A6 fails: the variant over- or under-flags KOIs in ways the TCE validation did not catch; A3, A4 and the leads
  are reported only as a diagnosis.
- A2, A5, A6 hold: per-KOI results are published as **leads**, not verdicts. A3 and A4 are scored as stated. On OBS
  about 26 % of this variant's TCE flags were not DR25 flags (precision 0.737; false-positive rate 0.141), so any one
  flagged KOI may be a false alarm of this re-implementation. No note goes to the Exoplanet Archive and no author is
  contacted unless a person has checked the light curves.
- Cross-check: read as in its original pre-registration (Q2 and Q3 hold: two independent methods agree beyond what
  period explains; Q2 holds and Q3 fails: may only reflect periods near 372 d; Q2 fails: a negative result).

## Limits known now

- Only Skye is modelled; DR25's other individual-transit tests (Rubble, Chases, Marshall, ...) and its MES re-check are
  not, so would_fail is a Skye-only count rule.
- A DR25 TCE's own events are in the bins; a never_dr25 KOI's are not (unless it matches a scored TCE). That makes
  DR25 candidates slightly more likely to be flagged than never_dr25 ones, which works against A4.
- "Valid cadence" is a two-star proxy; module outages are not seen.
- INV validated agreement with DR25's flags on false alarms by construction; transfer to real candidates is assumed.
