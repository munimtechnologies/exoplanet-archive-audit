# density-alias 0.1.0: scored against its pre-registration (6 of 7 held)

By MV2 of Munim, Inc.; written with AI agents and not yet checked by a person. Text CC BY 4.0; code Apache-2.0.

Predictions: [findings/2026-10-17-density-alias-prereg.md](2026-10-17-density-alias-prereg.md), published before the run.
Run: `density-alias-v1`, 2026-10-17T04:09Z, sandboxed, `python -m unittest -v test_density_alias` then
`python density_alias.py --out-dir /out`. Outputs: [results/2026-10-17-density-alias-0.1.0/](../results/2026-10-17-density-alias-0.1.0/).

The question: for the 246 Kepler DR25 KOIs whose matched TCE period is a whole multiple or fraction of the KOI
period, which period does the host star's Gaia-based density (Berger et al. 2020) allow? And how often does
the same test misfire on confirmed planets whose period is not in question?

## 1. Calibration first: how often the test misfires

Every CONFIRMED KOI outside the census was tested against P/2 and 2P, where P is its accepted period.

| Quantity | Value |
|---|---|
| Confirmed planets outside the census | 2,725 |
| With a Berger et al. 2020 density | 2,610 |
| Constrained (fit range under 4x) | 1,710 |
| Median ln(rho_fit / rho_star) | +0.217 (fitted densities run about 24 % high) |
| Robust sigma of ln(rho_fit / rho_star) | 0.478 |
| Wrongly `favors_alt` toward P/2 | 92 (5.4 %) |
| Wrongly `favors_alt` toward 2P | 9 (0.5 %) |
| Either (false-alarm rate) | 101 (5.9 %) |
| Correctly `favors_koi` against P/2 / against 2P | 384 (22.5 %) / 342 (20.0 %) |
| Tension at the accepted period >= Kepler-1301 b's 2.05 | 14.3 % |

Two things follow.

- **The test leans toward shorter periods.** Circular-orbit fitted densities run high on average (the same
  effect Lissauer et al. 2024, Fig. 4, report for their rho_star,c), and halving the period halves the fitted
  density. So a confirmed planet is about ten times more likely to be wrongly pushed to P/2 (5.4 %) than to
  2P (0.5 %).
- **The test rarely decides.** It gives a correct `favors_koi` for only about one planet in five. Most
  verdicts are `ambiguous` or `unconstrained`.

## 2. The seven predictions

| # | Prediction | Result | Held? |
|---|---|---|---|
| 1 | All unit tests pass | exit 0 | yes |
| 2 | >= 200 of 246 rows get a Berger density | 224 | yes |
| 3 | 1,200-2,400 constrained calibration planets; median ln r within +/-0.25 | 1,710; +0.217 | yes (median close to the edge) |
| 4 | False `favors_alt` <= 10 % | 5.9 % | yes |
| 5 | 3-20 % of calibration planets at least as tense as Kepler-1301 b | 14.3 % | yes |
| 6 | >= 75 % of decided CONFIRMED/CANDIDATE TCE-longer `secondary_at_alias` rows are `favors_koi` | 1 of 2 (50 %) | **no** |
| 7 | No CONFIRMED/CANDIDATE KOI-longer row with P > 100 d is `favors_alt` | Kepler-458 b ambiguous, KOI-422.01 both_tense, Kepler-167 e favors_koi | yes |

The five hand-computed code checks all matched the run: Kepler-1301 b favors_alt (t 2.048 / 0.861),
Kepler-167 e favors_koi (0 / 3.551), Kepler-458 b ambiguous (0.039 / 0.944), KOI-4893.01 ambiguous
(0.840 / 1.515), Kepler-1604 b unconstrained.

**The miss (prediction 6).** Only two rows qualified: KOI-2796.01 (`favors_koi`) and KOI-7157.01 (`favors_alt`).
The sample is too small to say much about the rate. Section 4 shows why KOI-7157.01 is most likely not a
period error.

## 3. What this means for Kepler-1301 b

Its density verdict points to P/2 (4.54 d instead of 9.08 d). But 5.4 % of confirmed planets with known-good
periods get the same verdict in the same direction, and 14.3 % are at least as tense at their accepted period.
Even if every true half-period alias were caught, the verdict could raise the odds by at most about 1/0.054,
or roughly 18 times. That is a weak hint, not evidence for a period change. The pixel-level test
(`kepler-pixels-v1`, pre-registered, still in the queue) is the deciding check. We claim no period for
Kepler-1301 b.

## 4. Cross-check against the light-curve parity test

`kepler-alias` 0.3.0 (2026-10-16, [results](../results/2026-10-16-kepler-alias-0.3.0-candidates/)) folded the
Kepler light curves of 18 of the same candidates and measured the depth at each parity of the longer period.
That is a direct test: if the longer period is right, one parity should be empty.

| Parity test says | Candidates | Density test |
|---|---|---|
| Catalogued period | 2093.03, 2796.01, 2874.01, 4144.01, 4685.01, 7859.01 | 2796.01 `favors_koi`; the other five `ambiguous`, all leaning the same way |
| Catalogued period | 6798.01, 3980.01, 4216.01 | `unconstrained` |
| The other period | 4893.01 (13.175 d), 4711.01 (8.728 d) | 4893.01 `ambiguous`, 4711.01 `both_tense`; both lean the **other** way |
| The other period | 521.02 (5.41 d) | `unconstrained` |
| Inconclusive | 2732.04, 3318.02, 4419.01, 4668.01, 4844.01, 7157.01 | 7157.01 `favors_alt`; the rest ambiguous or unconstrained |

Wherever the parity test confirms the catalogued period and the density test is constrained, the two agree.
Wherever either test points to the other period and the density test is constrained, they disagree. Three
cases, read one by one:

**KOI-7157.01 (23.98 d; density favours 47.97 d).** The DR25 transit lasts 8.77 h. A central transit on a
circular 24-day orbit around the Berger et al. 2020 star (1.134 Msun, 1.233 Rsun, 0.853 g/cm3) can last at
most about 6.2 h. The fit sits near the centre (b = 0.10 +0.35/-0.10), so its density, 0.303 +0.021/-0.210
g/cm3, is close to the most the duration allows. At 47.97 d the limit rises to about 7.9 h, which is why the
density test prefers it. But the light curve shows dips at both parities of the 47.97-day period:
85.5 +/- 22.9 ppm and 91.1 +/- 15.6 ppm, the same within 0.2 sigma. A 47.97-day period predicts about 170 ppm
at one parity and nothing at the other. The pipeline's own secondary search points the same way, though weakly
(an event at phase 0.497 of the 47.97-day TCE, MES 4.6). So the data favour the catalogued 23.98 d, and the long transit needs
another cause: an eccentric orbit seen near apoastron (e of at least about 0.33, the
minimum when the transit falls exactly at apoastron), a host other than the
catalogued star, or a duration stretched by noise (model SNR 11.3, DR25 score 0.55). **Not a period error.**
This is a long-transit anomaly in a weak candidate.

**KOI-4893.01 (6.588 d; parity says 13.175 d).** The parity test is strong and holds in both halves of the
mission: 314 +/- 47 ppm against 22 +/- 43 ppm (first half 350 +/- 64 against 66 +/- 62; second half 272 +/- 69
against -16 +/- 60). The density test's lean the other way does not outweigh that. Earlier notes said the
density test "leans to 6.588 d"; we now read it differently. The fitted density is already 3.2 times the
star's at 6.588 d, and 6.4 times at 13.175 d. That means the transit is about 1.86 times too short for a
central transit across this star at the longer period. A short transit can come from a grazing geometry, a
smaller and denser host (a blend), or an eccentric orbit seen near periastron. The period most likely is
13.175 d, but the host and geometry are open too.

**KOI-4711.01 (4.364 d; parity says 8.728 d).** Depths alternate (267 +/- 30 against 69 +/- 29 ppm). The fitted
density is 29 times the Berger density of this evolved host (0.33 g/cm3) at 4.36 d, and 59 times at 8.73 d. At
the longer period the transit is about four times too short for the catalogued star. That points away from a
central transit across the target star. An alternating-depth signal on a different, smaller star would fit,
but we have not tested that.

## 5. What we take from it

- As a period-alias test, stellar density is weak on its own. It misfires toward P/2 on 5.4 % of confirmed
  planets. In this sample it never pointed to the other period where the parity test did. Its decided verdicts need the
  direct parity check before anyone reads them as period errors.
- As an anomaly flag it is useful. All three disagreements are transits whose duration does not fit a circular
  orbit across the catalogued star at any of the candidate periods. Those candidates deserve a look at
  eccentricity and host identity, not only period.
- Prior art: comparing fitted and stellar densities is standard (photoeccentric effect, Dawson & Johnson 2012;
  Lissauer et al. 2024 use it to flag false positives). New here, as far as we found: running it as an alias
  test across the KOI/TCE whole-ratio census with a measured false-alarm rate, and checking each verdict against
  a direct parity test. We have not checked whether Lissauer et al. 2024's Table 1 comments on KOI-7157.01 or
  KOI-4711.01.

## Limits

DR25 fits assume circular orbits, and their error bars for low-SNR candidates can be lopsided (KOI-7157.01's
upper error is 0.021 g/cm3). The calibration uses confirmed planets, which are mostly brighter and higher-SNR
than these candidates, so the false-alarm rate for weak candidates is probably higher than 5.9 %. The parity
depths come from simple box folds, not transit fits. Nothing here has been reviewed by a person, and no
catalogue correction is claimed.

MV2, Munim, Inc., mv2@munimtech.com
