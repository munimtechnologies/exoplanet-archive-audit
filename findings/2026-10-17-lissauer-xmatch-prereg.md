# Pre-registration: where does the Exoplanet Archive still disagree with Lissauer et al. 2024? (lissauer_xmatch 0.1.0)

MV2 of Munim, Inc., 2026-10-17. Made with AI agents working in his name; no human has checked this yet.
Code Apache-2.0, text and data CC BY 4.0. Committed **before** the job runs; scored in public, misses included.

## Why

Lissauer et al. 2024 (PSJ 5, 152) re-fit and re-dispositioned the 9,564 KOIs of the Archive's cumulative
table as retrieved on 2022-10-27, plus KOI-8339 to 8394. They report 4,376 planet candidates, 361 S/N
rejections (S), 100 too-large radii (R), 13 mass rejections (M), 11 FP -> PC and 6 PC -> FP changes, and
period corrections (for example KOI-6262.01 and 4777.01 halved, KOI-1353.03 set to Kepler-289 d's period).
On 2026-10-17 the Archive's cumulative table still shows the old values for the ones we checked by hand:
K01101.02, K01922.02 and K02167.02 are CANDIDATE although Lissauer rejects them
(findings/2026-10-17-lissauer-check.md); K04777.01 is CONFIRMED (Kepler-1971 b) at 0.824000125 d,
K06262.01 CANDIDATE at 0.673141323 d, K01353.03 "Kepler-289 e" at 330.071558 d; K03032.01, K01416.01,
K01450.01 and K00245.04 are CONFIRMED although the paper's text calls them false positives or a false alarm.

This census joins the two tables by KOI number and counts every disagreement.

What is and isn't new: Lissauer's Status column already pairs their disposition with DR25 supplemental's,
so most per-KOI disagreements can be read off their table. We found no published join to the Archive's
**current** table, and none that splits the rejections by where the Archive's parameters come from
(koi_parm_prov). That split tests our "orphan" idea (600 CANDIDATEs whose parameters predate DR25;
findings/2026-10-17-orphan-census-prereg.md) against an independent, peer-reviewed vetting.

## Method (lissauer_xmatch 0.1.0)

- Lissauer Table 1 from IOP's machine-readable file
  (content.cld.iop.org/journals/2632-3338/5/6/152/revision3/psjad0e6et1_mrt.txt). Column byte ranges are
  read from the file's own header, with the published ranges as a fallback.
- Archive: live TAP query of cumulative (kepoi_name, kepid, kepler_name, koi_disposition, koi_parm_prov,
  koi_period, koi_model_snr).
- Join on KOI number; check KIC. "Rejected" = Lissauer's first letter is F, S, M or R. "Orphan" =
  koi_parm_prov is not q1_q17_dr25_koi.
- Period flag: |P_Lissauer / P_Archive - 1| > 0.001, with the nearest a/b (a, b <= 12).
- Outputs: xmatch.csv (every matched KOI), candidates_rejected.csv, disagreements_other.csv (CONFIRMED
  rejected; FALSE POSITIVE now P), period_flags.csv, summary.json.

16 unit tests on a fixture built from the real rows of KOI 1101, 1922 and 2167, with hand-worked
expected values.

## Predictions

1. All 16 unit tests pass.
2. The header gives KIC 1-8, KOI 10-16, Status 548-551. 9,600-9,800 Lissauer rows; 9,564 +- 5 Archive
   rows; at most 10 Archive KOIs unmatched; at most 5 KIC mismatches; 40-150 Lissauer-only rows.
3. K01101.02 FPNN, K01922.02 SPNN, K02167.02 SPNN (as read by hand); K00001.01 starts with P.
4. Among matched KOIs, Lissauer's first letter counts: P 4,330-4,380; S 300-345; R 90-105; M 10-14.
5. 300-500 Archive CANDIDATEs are rejected by Lissauer.
6. Orphan CANDIDATEs (600) are rejected at least twice as often as DR25-parameter CANDIDATEs (1,377).
7. Lissauer's DR25-supplemental letter agrees with the Archive's disposition (CANDIDATE or CONFIRMED = P,
   FALSE POSITIVE = F) for at least 98 % of KOIs where that letter is P or F.
8. 3-25 Archive CONFIRMED planets are rejected by Lissauer, including K03032.01, K01416.01, K01450.01,
   K00245.04 and K00129.01 (M).
9. K04777.01 and K06262.01 come out at period ratio 1/2 and K01353.03 at 1/5. Between 5 and 300 KOIs are
   period-flagged (a loose, exploratory bound).

## How it will be read

- The result is a list of where the Archive has not caught up with a 2024 catalogue, not new
  dispositions of our own. Each listed KOI carries Lissauer's reason letter.
- If 6 holds, Lissauer's rejections concentrate in the KOIs whose Archive parameters predate DR25. That
  supports, independently, the reason we gave for looking at orphans.
- Any claim about a single KOI repeats Lissauer's result and says so. Our own additions (aliases of a
  sibling) are reported only where we hand-checked them.
- If the IOP file can't be fetched or parsed, that is no measurement, and the job is re-queued.

## Limits

- Lissauer's S cut uses their own S/N, which can differ from the Kepler pipeline's (Kunimoto et al. 2020
  give an example). A rejected KOI is "rejected by Lissauer et al. 2024", not "shown false".
- CONFIRMED planets validated after 2022 may legitimately differ from Lissauer's table.
- The period flag mixes alias corrections with small mean-period changes (for example Kepler-9 b and c
  moved by about an hour). The nearest-fraction column separates them only roughly.
