# CNEOS Sentry vs SBDB pre-registration (D1-D3): does JPL's impact-risk list agree with JPL's own Small-Body Database and with its stated diameter rule?

MV2 of Munim, Inc. (mv2@munimtech.com). Drafted 2026-10-20 by AI agents working in his name, before any of the
decisive data are downloaded; not checked by a person. Apache-2.0 code, CC BY 4.0 text. A new lane after the SBDB
series (`findings/2026-10-19-sbdb-triplet-results.md`, `findings/2026-10-19-sbdb-source-results.md`).

## Question

JPL's Sentry system lists every near-Earth object for which an Earth impact in the next century cannot yet be
ruled out (about 2,200 objects). Its API (https://ssd-api.jpl.nasa.gov/doc/sentry.html, version 2.0) serves for
each object an absolute magnitude `h`, a `diameter` and the date of the last observation used (`last_obs`). The
documentation says the diameter is computed from H "usually assuming a uniform spherical body with visual albedo
of 0.154", and that measured values are sometimes used instead. JPL's Small-Body Database (SBDB) serves the same
object's current H and the last observation used in its current orbit.

1. **D1.** How many served Sentry diameters do not follow D = 1329 km / sqrt(0.154) x 10^(-H/5) beyond rounding?
2. **D2.** For how many objects does SBDB's current orbit use observations made after the last observation Sentry's
   analysis used (that is, how many risk analyses are behind the orbit catalogue)?
3. **D3.** For how many objects does Sentry's H differ from SBDB's current H beyond rounding?

The series so far found that 96 % of SBDB's diameter/albedo/H triplets no longer agree because H was revised after
the albedo was fitted. Sentry's size and impact energy also come from H, so the same question applies to the list
people read for impact risk.

## Prior art (searched 2026-10-20)

The impact-monitoring systems are compared with each other: Del Vigna et al. ("Completeness of Impact
Monitoring", arXiv:1809.05790, Icarus doi:10.1016/j.icarus.2018.12.028) compared CLOMON-2 and Sentry virtual
impactors statistically; Fenucci et al. (arXiv:2411.03763, the ESA NEOCC Aegis system, accepted in CMDA) compare
risk lists and, per a secondary summary, say the three centres cross-check objects above Palermo -2 daily; Vavilov
& Hestroffer (NEOForCE, A&A 707, A317, 2026) check five objects against Sentry-II. (arXiv pages checked
2026-10-20.) A Hugging Face mirror of the Sentry
list (juliensimon/sentry-impact-risk, CC BY 4.0) republishes the fields without checks. We found no published
check of Sentry's served H, diameter and last observation against SBDB, or of how many diameters follow the stated
0.154 rule. The question here is bookkeeping consistency between two JPL services, not impact probabilities.

## What has been seen before this note

No Sentry list has been downloaded. Seen: the example record of the API documentation (1979 XB: h "18.56",
diameter "0.66", last_obs "1979-12-15"); the impact probability of 2010 RF12 in the dataset card above; and 99942
Apophis, a probe row of the close-approach preparation. All three are excluded by designation and never scored.

## Data

One request to `sentry.api` with no parameters (mode S, the whole list), saved byte for byte with its SHA-256.
Then the SBDB Query API with `sb-group=neo` (NEO asteroids and comets) and fields `spkid, pdes, full_name, kind, H,
last_obs, orbit_id, soln_date, producer`, in pages of 20,000 with a 1 s pause. Sentry `des` is joined to SBDB
`pdes` exactly (after trimming spaces).

## Rules (`sentry_sbdb.py` 0.1.0, unit-tested)

Every served number is read as an interval of half its last digit (`parse_dec`: "18.56" means 18.555-18.565).

- **Diameter rule** (`diameter_status`): consistent if the served diameter's interval meets
  [D(H + u_H) x 0.99, D(H - u_H) x 1.01], with D(H) = 3386.6 km x 10^(-H/5); otherwise inconsistent.
- **Observation order** (`obs_order`): compares the two `YYYY-MM-DD` strings; "later" if SBDB's date is after
  Sentry's. Dates with "??" are not comparable.
- **H agreement** (`h_differs`): the two H differ if |H_SBDB - h_Sentry| > u_SBDB + u_Sentry + 0.01 mag, in exact
  decimal arithmetic.

## Decisions (integer arithmetic; `decide_d1`, `decide_d2`, `decide_d3`)

Each is "underpowered" if its n is below 1,000. D2 and D3 are "not scored" if fewer than 95 % of the scored Sentry
rows match an SBDB row.

- **D1.** n = Sentry rows with parseable h and diameter, k = inconsistent. **Holds** if 100 k <= 3 n (at most 3 %).
- **D2.** n = matched rows with two comparable dates, k = "later". **Holds** if 50 k <= n (at most 2 %).
- **D3.** n = matched rows with two parseable H, k = differ. **Holds** if 10 k <= n (at most 10 %).

Each decision is reported once as it comes out; no re-scoring. Descriptive only: counts of each observation order;
the 2 x 2 table of H differs against observation order; the orbit producer of "later" rows; quantiles of the gap
in days for "later" rows and of H_SBDB - h_Sentry where H differs; the diameter ratio of every inconsistent row;
unmatched designations.

## Expected outcome, stated before the run

D1 holds (the documentation says the 0.154 rule is the usual case; few listed objects have measured albedos).
D2 holds (Sentry is documented as continually scanning the current catalogue; "later" rows should be objects
re-observed within the last day or two). D3 holds with low confidence: SBDB's H may come from a different source
(MPC or JPL) than the H Sentry used, which could push the share above 10 %.

## Power

A recent mirror of the list held 2,221 objects (dataset card read 2026-10-20; no rows were read), so n should be about 2,200 for each decision,
well above 1,000; 3 %, 2 % and 10 % of 2,200 are about 66, 44 and 220 objects.

## Integrity checks written to `summary.json`

Gate passed; Sentry signature version "2.0"; Sentry rows = count; no duplicate Sentry designation; SBDB fields as
requested; SBDB count stable on every page; rows = count; no duplicate spkid or pdes; which excluded designations
were present. If the gate fails, nothing is downloaded.

## Limits

One snapshot of each service, taken minutes apart, so an object re-observed in between can show as "later". Sentry's
`h` and `diameter` in mode S are means weighted by impact probability; for one object they should equal its single
H. A "later" row means the risk analysis predates the newest observations, not that its risk is wrong. No one will
be contacted about individual objects without Sheehan's approval.

## Job and files

`sentry-sbdb-v1`: `fetch_published.py` 0.2.0 waits for `sentry_sbdb.py` 0.1.0 and its tests, the tests run, then
it fetches this note (text "CNEOS Sentry vs SBDB pre-registration") and runs `sentry_sbdb.py --gate-note ...`.
Outputs `summary.json`, `decisions.json`, `descriptive.json`, `rows.csv`, `sentry.json`, published under
`results/<date>-sentry-sbdb-0.1.0/` with a results note, whatever they say. Files in this commit: `sentry_sbdb.py`,
`test_sentry_sbdb.py` (0.1.0) and this note.

MV2, Munim, Inc., mv2@munimtech.com
