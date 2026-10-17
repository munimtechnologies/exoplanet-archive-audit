# Pre-registration: do "unrelated" orphans share a transit with a DR25 TCE? (shared_events 0.1.0)

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Code Apache-2.0, text and data CC BY 4.0. Committed **before** the job runs; scored in public, misses included.

## Why

findings/2026-10-17-orphan-census-results.md (koi_orphans 0.1.0) sorted the Archive's 600 "orphan"
CANDIDATEs (cumulative-table rows whose parameters still come from Q1-Q16 or DR24, not DR25). 146 were
called **unrelated**: their star has DR25 TCEs, but none at a period within a/b (a, b <= 12) of the
orphan's with under 0.5 d drift over Q1-Q17.

That test cannot see a TCE that kept one real transit and paired it with other events at a wrong period.
KOI-1356.01 is the known case (findings/2026-10-17-koi1356-events-prereg.md): Q1-Q16 384.026 d and the DR25
TCE 393.719 d share the first transit at 335.82 BKJD, the Robovetter scored that TCE 0.000 (not
transit-like: INDIV_TRANS_MARSHALL_SKYE, INCONSISTENT_TRANS), so it never became a DR25 KOI and the Archive
row kept the Q1-Q16 values. The census filed it as unrelated.

While writing the tests, the TCE rows of 8 of the 146 were read by hand (K00099.01, K00423.02, K00492.02,
K00682.01, K01032.01, K01192.01, K01356.01, K01421.01). Five look like KOI-1356.01:

| KOI | Archive (Q1-Q16) P, T0 | DR25 TCE P, T0 | shared event (BKJD) |
|---|---|---|---|
| K00099.01 | 2190.70 d, 140.048 | 627.765 d, 140.063 | 140.05 (orphan has 1 event in Q1-Q17) |
| K01032.01 | 1500.14 d, 176.082 | 293.805 d, 176.09 | 176.08 (1 event) |
| K01421.01 | 1693.66 d, 524.280 | 327.155 d, 197.119 | 524.27 (1 event) |
| K01356.01 | 384.026 d, 335.816 | 393.719 d, 335.817 | 335.82 (first of 4) |
| K00682.01 | 562.173 d, 185.969 | 563.276 d, 184.864 (rogue TCE) | 748.14 (middle of 3; the outer two miss by 1.1 d) |

K01192.01 (1295.36 d) shares nothing with either TCE on its star. This job runs the same test on all 146.

## Method (shared_events 0.1.0, standard library only)

- Inputs: results/2026-10-17-koi-orphans-0.1.0/orphans.csv and results/2026-10-17-lissauer-xmatch-0.1.0/xmatch.csv
  (this repository); cumulative and q1_q17_dr25_tce (live TAP); the DR25 Robovetter output
  (github.com/nasa/kepler-robovetter, kplr_dr25_obs_robovetter_output.txt). All inputs are saved in out/.
- Events: every T0 + nP in BKJD [131.5, 1591.0] (Q1 start to Q17 end; data gaps not removed).
  Window w = (D_orphan + D_tce)/24 d, as in koi_orphans. k = number of (orphan, TCE) event pairs within w.
- Chance: lam = n_o n_t 2w / 1459.5; p_chance = P(Poisson(lam) >= k).
- Per orphan, the TCE with k >= 1 and smallest p_chance decides: **shared_event** if p_chance <= 0.05,
  chance_overlap if k >= 1 but p > 0.05, disjoint otherwise.
- Null: each orphan's TCE set is swapped for another unrelated-orphan star's (100 random derangements,
  seed 20261017). Swapped pairs are not filtered for commensurability, so the null is, if anything, generous.
- Joins: Robovetter score, disposition, NT/SS/CO/EC and minor flags of the deciding TCE; the KOI it is
  federated to, if any; Lissauer et al. 2024 status and period.
- 22 unit tests on the real rows above, with hand-worked values (e.g. KOI-1356.01: 4 x 4 events,
  w = 1.1279 d, k = 1, lam = 0.02473, p = 0.02443).

## Predictions

1. All 22 unit tests pass.
2. Plumbing: 600 orphan rows read, 146 unrelated, none missing from cumulative; no_tce = 0; no_params <= 5.
3. Controls: K00099.01, K00682.01, K01032.01, K01356.01 and K01421.01 come out shared_event with k = 1 and
   p_chance 0.0069, 0.0101, 0.0144, 0.0244, 0.0125 (+/- 0.0005); K01192.01 comes out disjoint.
4. **The test**: at least 10 of the 146 are shared_event (so at least 5 beyond the controls), and the real
   shared_event count is at least twice the null mean.
5. Of the shared_event orphans beyond the five controls, at least 60% have an Archive period > 100 d.
6. Of all shared_event pairs whose TCE is neither rogue nor federated to a KOI, at least 70% are Robovetter
   FP with the not-transit-like flag (NT = 1), i.e. DR25 saw the event and rejected the period.
7. Exploratory, no prediction: Lissauer et al. 2024 status and period of each shared_event orphan;
   chance_overlap list.

## How it will be read

Only 4 is the test; 2 and 3 check the plumbing; 5 and 6 describe what kind of cases these are. A
shared_event flag says that DR25 detected an event that a catalogued CANDIDATE also has, at a period the
catalogue does not list. It does not say which period is right (KOI-1356.01 is being tested separately in
koi1356-events-v1). If 4 fails, the reading is that KOI-1356.01-type cases are rare among the orphans.

## Prior art

- Thompson et al. 2018 (ApJS 235, 38) built the Robovetter's individual-transit metrics (Marshall, Skye,
  Chases, Rubble) for TCEs whose events are not all real. The mechanism is documented; the link from those
  TCEs back to cumulative-table orphan CANDIDATEs that still carry Q1-Q16 parameters is what is new here.
- Twicken et al. 2016 (AJ 152, 158) sec. 3.3 matched 3,402 "golden" KOIs to DR25 TCEs and lists period
  mismatches (e.g. 2174.03, 4829.01, 4893.01). None of the six KOIs above is in its Table 3 (checked through
  a summarising reader, not line by line).
- Still to check at scoring: whether long-period and single-transit studies (e.g. Wang et al. 2015,
  Foreman-Mackey et al. 2016, Herman et al. 2019) already give periods for the flagged KOIs.
