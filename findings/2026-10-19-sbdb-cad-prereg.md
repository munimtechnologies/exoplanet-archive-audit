# SBDB close-approach pre-registration (G1-G3): is JPL's served Earth close-approach table consistent with its served orbit table?

MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0 for code, CC BY 4.0 for text and data.
Lane G of the served-catalog audit series (after C1 triplet, C2 source, C3/F flags). Written and unit-tested before any
census data was read. The gate for the job is this note's title text; the gate log is the timestamp.

## Question

JPL serves two products for the same near-Earth asteroids: the orbit table (SBDB Query API: orbit-solution ID, epoch,
Earth MOID, ...) and the close-approach table (CAD API: for each Earth approach, the orbit-solution ID used, time,
nominal distance, its 3-sigma range, and the speeds v_rel and v_inf). Are they consistent with each other?

- **G1 (same solution).** For a listed close approach, is the orbit-solution ID behind it the ID the orbit table
  serves for that object right now? A difference means one of the two tables is behind the other.
- **G2 (impact-parameter bound).** The nominal approach distance may be *smaller* than the served Earth MOID without
  any contradiction: Earth's gravity bends the incoming path inward, and the osculating MOID drifts. What must not be
  smaller than the MOID of the orbit the object was on just before the encounter is the *unperturbed* miss distance,
  which in the two-body picture of the encounter is the impact parameter `b = dist * v_rel / v_inf` (conservation of
  angular momentum about Earth; CAD serves all three numbers). So: for an object's **first** listed Earth approach
  **after** its served orbit epoch, within one year of it, is `b >= moid - TOL`?
- **G3 (range sanity).** Does every listed approach's 3-sigma range contain its nominal distance?

## Why new

Searched before writing this note: arXiv:2403.00541 recomputes Apophis-asteroid MOIDs independently and reports
differences from JPL of order 100-300 km; arXiv:2609.22045 compares an independent periapsis search with CAD (73 % of
its sub-lunar-distance encounters appear in CAD); arXiv:2505.01686 classifies the time evolution of NEA MOIDs. Tool
authors note that CAD does not serve the MOID and that `orbit_id` is JPL's solution number. No published check of
JPL's two *served* tables against each other was found: nothing reports how often the close-approach table and the
orbit table cite different orbit solutions, and nothing tests the impact-parameter bound against the served MOID.

## Data

- Orbit table: `sbdb_query.api` with `sb-group=neo`, `sb-kind=a`, `full-prec=true`, sorted by spkid, pages of
  20,000, fields `spkid,pdes,orbit_id,epoch,moid,condition_code,data_arc,n_obs_used,last_obs,soln_date`. The count
  seen in the format probe was 42,783 NEO asteroids. (`sb-group=neo` alone also returns comets; `sb-kind=a` removes
  them.)
- Close-approach table: one `cad.api` request, `date-min=2024-01-01`, `date-max=2028-01-01`, `dist-max=0.2`,
  `nea=true`, sorted by date. The `total-only` probe gave 12,681 rows. Fields
  `des,orbit_id,jd,cd,dist,dist_min,dist_max,v_rel,v_inf,t_sigma_f,h`.
- Join: CAD `des` equals SBDB `pdes` (both are the IAU number for numbered objects and the provisional designation
  otherwise). Orbit IDs are normalised by dropping a leading `JPL` (the orbit table serves both `659` and `JPL 732`;
  CAD served `220` in the probe).
- The served standard epoch seen in the probe is JD 2461200.5 (2026-Jun-09), inside the window, so for most objects
  the year after the epoch is fully covered.
- Rows looked at before this note, excluded from every count: the 340 rows of sbdb_triplet's published
  `sample.csv` and `outliers.csv`; Ceres, Pallas, Juno (sbdb_triplet's format probe); 433 Eros, 719 Albert,
  887 Alinda (this lane's 3-row Query API probe, the three lowest spkids); 99942 Apophis (this lane's CAD format probe).
  The job refuses to download anything unless this note and the two seen-row files are present.

## Reading the served numbers (`sbdb_cad.py` 0.1.0, unit-tested)

All numbers are `decimal.Decimal`, never floats. `dist` and `moid` are read as the interval of their last served
digit; `v_rel`, `v_inf`, `jd` and `epoch` are read exactly. `b` is computed as an interval from `dist`'s interval.
TOL = 0.001 au (about 150,000 km, 0.39 lunar distances): well above the rounding of any served value, above the
Earth-versus-Earth-Moon-barycentre difference (under 5,000 km), and above the secular MOID change of a typical NEA
over one year (Hu et al. 2025 find most NEA MOIDs drift nearly linearly over two centuries). An object that had a
planetary encounter between its epoch and the tested approach can legitimately exceed TOL; that is why G2 allows
1 in 1,000 rather than zero.

G2 eligibility, decided per object: the close-approach orbit ID equals the served one (G1 same); the served epoch E
satisfies 2460310.5 <= E and E + 365.25 <= 2461771.5 (the whole year after E is inside the window); the first listed
approach after E (smallest jd >= E) is at most 365.25 days after E; `dist`, `v_rel`, `v_inf` and `moid` are present
and both speeds are positive. Later approaches after the epoch, and approaches before it, are reported descriptively
only (the orbit served at the epoch is the post-encounter orbit for those).

## Decisions (integer arithmetic; `decide_g1`, `decide_g2`, `decide_g3`)

- **G1.** n = matched CAD rows in the window with both orbit IDs present; k = rows whose normalised IDs differ.
  Powered if n >= 5,000. **Holds** if 100 k <= n (at most 1 in 100). Also reported: how many differing rows cite an
  older or a newer integer solution than the orbit table.
- **G2.** n = eligible objects; k = objects whose upper bound of b is below the lower bound of moid minus TOL.
  Powered if n >= 1,000. **Holds** if 1,000 k <= n (at most 1 in 1,000).
- **G3.** n = CAD rows with all three distances present; k = rows with dist < dist_min or dist > dist_max.
  Powered if n >= 5,000. **Holds** if k = 0.

Scored strictly from the job's counts. Anything else in the outputs (the distribution of b - moid and of
dist - moid, how many nominal distances fall below the MOID while b does not, the dt bins, the before-epoch subset,
the epoch histogram) is descriptive, not scored.

## Expectations, written before the data

G1: holds (both tables come from the same database; a few per cent of stale rows would already be notable). G2: holds
(this is a physical bound on a nominal-versus-nominal comparison; a failure would mean a stale or inconsistent MOID
or a bug in the reasoning above, to be reported either way). G3: holds (zero violations expected). The descriptive
"naive" count is expected to show that a visible share of close approaches have dist < moid while b >= moid, which is
exactly the gravitational-focusing effect and the reason the naive inequality is not a valid test.

## Outputs

Job `sbdb-cad-v1` (sealed container, pure stdlib) writes `summary.json` (both requests' byte counts and SHA-256,
API counts, checks, decisions), `decisions.json`, `counts.json`, `epochs.json`, `flagged.csv` (G1 differing rows, G2
flagged objects, G3 violations, each capped at 5,000 rows; counts are always complete) and `g2_rows.csv` (every
eligible object with jd, epoch, dt, dist, v_rel, v_inf, b, moid, b - moid, dist - moid, status, condition code and
data arc). Results will be published under `results/<date>-sbdb-cad-0.1.0/` with a results note in `findings/`.

## Limits

One window (2024-2028) and one distance cut (0.2 au); a single snapshot of each API on the job's day; the two-body
impact parameter is an approximation that is excellent for short encounters and loosens for very slow, distant ones,
in the direction of making b slightly uncertain either way, which TOL absorbs. The join is by designation string only.
