# SBDB triplet pre-registration (P1-P3): do the diameter, albedo and H that JPL's Small-Body Database serves still agree?

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-10-19 ~16:30 UTC by AI agents working in his name, before the
decisive data are downloaded; not checked by a person. Apache-2.0 code, CC BY 4.0 text. This is a new question,
outside Kepler; it sits in this repository because the method (pre-registered integer rules in tested code, a job
gated on this note's public URL) is the one used here.

## Question

For an asteroid, diameter D (km), geometric albedo p and absolute magnitude H are tied by
D = 1329 / sqrt(p) x 10^(-H/5) (Harris & Harris 1997; Pravec & Harris 2007). Albedos are normally *computed* from a
measured diameter (thermal infrared, mostly NEOWISE; also radar, occultations, spacecraft) and the H known at that
time. H is then refined as new photometry reaches the Minor Planet Center, but the stored albedo is not. Solving the
identity for H gives H_fit = -5 log10(D sqrt(p) / 1329), the H the served albedo implies, so

    dH = H (served now) - H_fit

measures how far the served H has moved since the albedo was computed, object by object, from SBDB alone.

## Prior art (searched 2026-10-19)

- Pravec et al. 2012 (Icarus 221, 365): catalogue H too bright by up to 0.4-0.5 mag near H = 14, < 0.1 mag for
  large asteroids; WISE albedos revised with their own H.
- Vereš et al. 2015; Masiero et al. 2017 (AJ 154, 168; arXiv 1708.09504): Pan-STARRS H on average 0.26 mag
  fainter than the MPC H used in earlier NEOWISE fits; albedos from radar/occultation diameters are offset too.
- Berthier et al. 2023, SsODNet (arXiv 2209.10697): recomputes p from the latest H for its own catalogue, because
  stored albedos go stale.
- arXiv 2110.12098: SBDB and Horizons serve MPC H values.

As far as these searches found, nobody has measured the drift *inside SBDB's own served records* across the whole
database, as of 2026, against a rounding-aware tolerance. That is the new part; the mechanism is known. The
result is a data-quality measurement, not a new physical claim.

## Data

SBDB Query API (`https://ssd-api.jpl.nasa.gov/sbdb_query.api`), asteroids only (`sb-kind=a`), constraint
`{"AND":["diameter|DF","albedo|DF","H|DF"]}`, fields spkid, pdes, full_name, class, neo, H, diameter, albedo,
diameter_sigma, sorted by spkid, pages of 20,000. Values are kept as the strings served.

What was seen before this note: one 3-row format probe (spkid 20000001-20000003; it showed Ceres as H 3.34,
D 939.4 km, p 0.090) and the total count (138,086 on 2026-10-19). Those three rows are excluded from every
scored count (`EXCLUDED_SPKIDS`). No other row has been read.

## Per-row rule (`row_metrics` in `sbdb_triplet.py` 0.1.0, unit-tested)

- Status `unparsed` if any of the three strings is not a plain decimal; `nonpositive` if D or p <= 0. Only
  status `ok` rows are scored.
- dH in integer units of 1e-4 mag: dh_e4 = round(1e4 dH).
- Tolerance: tol_e4 = ceil(1e4 x (largest |H_fit change| over the four corners D +- u_D, p +- u_p, plus u_H)) + 100,
  where u is half the last served digit (0.090 -> 0.0005). The extra 0.01 mag covers the choice of the constant
  (1329 vs up to ~1335) and float error.
- A row is **shifted** if |dh_e4| > tol_e4. Hand-checked example (Ceres, excluded): dh_e4 = -278, tol_e4 = 212.

## Decisions (integer arithmetic; `decide_p1`, `decide_p2`, `decide_p3`, unit-tested)

- **P1 (prevalence).** n = scored rows, k = shifted rows. Powered if n >= 1000. **Holds** if 2k >= n (at least
  half of SBDB's served triplets no longer agree beyond rounding).
- **P2 (direction).** Among the k shifted rows, pos = rows with dh_e4 > 0 (served H fainter than the H implied by
  the albedo, so the served albedo is too high for today's H). Powered if k >= 100. **Holds** if 5 pos >= 3k.
- **P3 (size dependence).** Lower median of dh_e4 over scored rows with H >= 14 minus that over rows with H < 10.
  Powered if each group has >= 100 rows. **Holds** if the difference is >= 1000 (0.1 mag).

Each decision is reported once, as it comes out, with no re-scoring. Everything else is descriptive and will be
labelled so: dH quantiles by H bin, NEO flag, orbit class and whether diameter_sigma is given; a 0.05-mag
histogram; the 300 largest |dH| rows; the count with |dH| > 1 mag.

## Expected outcome, stated before the run

P1 holds (H has been refined for most numbered asteroids since the 2010-2017 NEOWISE fits). P2 holds, following the
Pravec and Masiero offsets, if the MPC's H has since moved toward the fainter Pan-STARRS values; this is the least
certain of the three. P3 holds if the drift follows Pravec's size dependence. A failure of P2 or P3 would itself
be informative: it would say the served H has not moved the way the published offsets suggest.

## Integrity checks written to `summary.json`

Fields returned as requested; the API count is the same on every page; rows equal the count; no duplicate spkid;
spkids strictly increasing; per-page byte counts and sha256. If the job is refused by the gate, it downloads
nothing and says so.

## Job

`sbdb-triplet-v1`: unit tests (`test_sbdb_triplet.py`, `test_fetch_published.py`), then `fetch_published.py` 0.2.0
waits for this note at its raw URL (text "SBDB triplet pre-registration"), then `sbdb_triplet.py --gate-note ...`.
Outputs: `summary.json`, `decisions.json`, `descriptive.json`, `histogram.csv`, `outliers.csv`, `sample.csv`
(40 rows, seed 2026101916, for hand checks) and `rows.csv` (kept locally; too large to publish). They will be
published under `results/2026-10-19-sbdb-triplet-0.1.0/` with a results note, whatever they say.

Limits known in advance: SBDB does not say which H each albedo was computed with, or where each diameter came from,
so dH mixes H revisions with any cases where the albedo was set by other means; a large |dH| is a flag for a
look, not proof of an error. No one will be contacted about individual objects without Sheehan's approval.

## Files in this commit

- `sbdb_triplet.py`, `test_sbdb_triplet.py` (0.1.0)
- this note

MV2, Munim, Inc., mv2@munimtech.com
