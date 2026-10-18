# Pre-registration: do the candidates Skye would fail match those an independent 2026 pipeline could not recover?

By MV2 of Munim, Inc., 2026-10-18 (~17:50 UTC). Written by AI agents working in his name before skye-census-v3 has
produced any output; no person has checked it yet. Text CC BY 4.0, code Apache-2.0 (`robnik_crosscheck.py` 0.1.0,
8 hand-worked tests). Published unchanged at ~18:45 UTC the same day; skye-census-v3 had still not started then.

## Why

skye-census-v3 (pre-registration `findings/2026-10-18-skye-census-v2-prereg.md`, amended by
`findings/2026-10-18-skye-census-v3-amendment.md`) re-implements DR25's Skye test, which looks for transit events
falling on dates when unusually many other TCEs on the same skygroup also have events (rolling-band artifacts;
Thompson et al. 2018, ApJS 235, 38, A.3.7.4).

Robnik, Seljak, Jenkins & Bryson 2026 (MNRAS, doi:10.1093/mnras/stag419, arXiv:2601.07465) re-searched the light
curves of 2,974 Kepler stars with a new single-star pipeline: per-transit defect and gap tests, plus a Bayes-factor
significance. They publish the 406 known candidates it did not recover
(github.com/JakobRobnik/exo-probability, `results/unrecovered_candidates.csv`, MIT, read 2026-10-18 ~17:45 UTC:
406 data rows, tab-separated, columns kepid, KOI, period, SNR, SNR_with_defects, FAP, vetting_tests,
vetting_tests_defects, flag_low_significance_kepler, flag_defect, flag_ttv, flag_low_significance). Their method
uses only each star's own light curve: the paper describes no cross-star, skygroup or same-time test, and mentions
rolling bands only to explain the 372-day excess and in an appendix filter that was not adopted.

So the two tests use different information. If they agree beyond chance on which long-period candidates are
suspect, each supports the other. Prior-art search on 2026-10-18 (web search, arXiv, the paper's full HTML text and
its repository) found no comparison of a Skye-type cross-star test with Robnik et al.'s list.

## Looked up beforehand, so excluded

While checking the table we read its rows for K05269.01 (listed, P = 371.51 d), K04426.01 (listed), K05423.01
(listed), K05398.01 (listed), K07894.01 (listed) and K05227.01, K01209.01, K01356.01, K05600.01 (not listed). The
paper names K08063.01, K08107.01, K08242.01 and K07915.01 as false alarms. All 13 are left out of every scored
group. K05269.01 and K05227.01 are v3's P7 targets; this exclusion does not change P7.

## Population and groups (fixed now)

From v3's `koi_skye.csv`: cumulative-table KOIs with koi_disposition = CANDIDATE, P > 45 d, status ok, Skye-eligible
(at least 3 events), whose star has exactly one CANDIDATE or CONFIRMED KOI in the published cumulative snapshot
(`results/2026-10-18-skye-census-0.1.0/tap/cumulative.csv`). The single-planet condition is there because
Robnik et al. kept only the lowest-SNR candidate on each star. F = would_fail 1; S = would_fail 0. "Listed" = the
KOI number appears in Robnik et al.'s table.

## Predictions

- Q1: F has at least 10 KOIs. If not, the comparison is reported as underpowered and nothing is claimed.
- Q2 (primary): the listed fraction in F is at least twice that in S, and the one-sided Fisher exact p < 0.01.
- Q3 (period control): within 340-400 d, where rolling-band false alarms pile up and both groups are concentrated,
  the listed fraction in F is strictly greater than in S. Direction only; counts reported.

Reported but not scored: the same comparison restricted to KOIs in the DR25 KOI table, and how Robnik et al.'s 406
listed KOIs split by cumulative disposition (this shows which catalogue they started from).

## How it will be read

- Q2 and Q3 hold: two independent methods agree on which long-period candidates are suspect, beyond what period
  alone explains. Published as a note with the agreeing KOIs as leads, not as false-positive verdicts.
- Q2 holds, Q3 fails: the agreement may only reflect that both tests pick out periods near 372 d. Stated that way.
- Q2 fails: negative result, published as such.
- The cross-check runs only if v3's P2 (data check) holds. If any of v3's P3-P6 fail, the cross-check is still run
  but reported only as a diagnosis of the re-implementation.

## Known limits

Robnik et al.'s input list is taken from the Exoplanet Archive (Christiansen et al. 2025), and its exact selection
isn't stated in the text we could read. A KOI that is not listed may have been recovered or may never have been
searched. Both groups share this ambiguity, but if Skye failures are more often outside the input list, Q2 is biased
toward failing. The table was fetched by WebFetch for reading only; the job downloads it again and records its
sha256.
