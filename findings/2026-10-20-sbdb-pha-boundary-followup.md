# SBDB PHA flags at exactly H = 22.0: 23 of 33 flagged, 10 not, so a strict "H < 22.0" rule does not explain F2 (follow-up, descriptive, not scored)

MV2 of Munim, Inc. (mv2@munimtech.com). Written 2026-10-20 ~07:00 UTC by AI agents working in his name; not
checked by a person. CC BY 4.0 text. Follow-up to `findings/2026-10-20-sbdb-flags-results.md` (F2 fails, 50 of
42,619). That note is unchanged and its decision stands; this note scores nothing. Everything below was looked at
after F was scored and is descriptive only.

## Question

The F results note offered two readings for the 50 PHA flags that contradict the served MOID and H: (a) stale
flags, or (b) a boundary convention, either the cut applied as H < 22.0 instead of H <= 22.0 or applied to an
internal H with more digits than the served ones. Reading (b) could only explain the 10 rows served unflagged at
exactly H = 22.00, and without those 10 rows F2 would have held. So we checked how SBDB flags the other rows at
exactly H = 22.0.

## What we read (2026-10-20, about 06:50-07:05 UTC)

1. One SBDB Query API request (read twice, both reads agree):
   `https://ssd-api.jpl.nasa.gov/sbdb_query.api?fields=pdes,H,moid,pha&sb-kind=a&full-prec=true&sb-cdata={"AND":["H|EQ|22","moid|LE|0.05"]}`
   (URL-encode the sb-cdata value). It serves **33 asteroids** with H = 22.0 and Earth MOID <= 0.05 au: **23 with
   pha = Y and 10 with pha = N**. The 10 unflagged rows are 886097, 2006 QJ65, 2008 XM1, 2009 QS, 2013 LF7, 2013 UX,
   2014 CM13, 2015 AM45, 2015 BW310 and 2019 RW. These are exactly the ten H = 22.00 rows that the F job
   (`sbdb-flags-v1`, about 2.5 hours earlier, from a full download) listed in `mismatches.csv`, which
   cross-checks both reads. The 23 flagged rows are 457662, 674590, 2001 TA2, 2001 VJ5, 2001 YP3, 2002 DO3,
   2003 GP51, 2003 WH166, 2007 PR25, 2007 SR11, 2011 TX8, 2012 DK31, 2012 FG58, 2013 WR67, 2014 HE124, 2015 YY9,
   2016 SJ1, 2017 GM4, 2017 SL17, 2019 NO4, 2020 BX, 2020 ST1 and 2021 NM8. We read this list through a
   page-reading tool, not a saved file, so re-run the query above to check it.
2. Six SBDB single-object API requests (`sbdb.api?sstr=<designation>&phys-par=1`), one at a time. The pha flag
   there agrees with the Query API flag for all six.

| Object | Served H (as served) | H sigma | H ref | MOID (au) | Orbit solution date | pha |
|---|---|---|---|---|---|---|
| 2000 WC1 | 22.57 | none | E2025-CG0 | 0.00551 | 2025-02-11 | Y |
| 154019 (2002 CZ9) | 22.07 | none | MPO694396 | 0.0256 | 2026-06-06 | Y |
| 2001 TA2 | 22.0 | none | MPO260735 | 0.0361 | 2021-04-14 | Y |
| 2013 LF7 | 22.0 | none | E2013S59 | 0.00848 | 2021-04-15 | N |
| 2015 AM45 | 22.0 | none | E2018N80 | 0.000487 | 2021-04-15 | N |
| 2019 KD7 | 21.7 | 0.59736 | E2020-QF4 | 0.0341 | 2021-04-15 | N |

For 154019, the Minor Planet Center's
object page gives H = 22.03 and Earth MOID 0.02534 au, and it does not label the object a PHA.

## What it shows

- **A strict "H < 22.0" rule is ruled out as the explanation.** Under that rule all 33 rows would be unflagged; 23
  are flagged. Under the published "H of 22.0 or less" all 33 would be flagged; 10 are not. At one and the same
  served H, SBDB serves both flags.
- **Hidden digits are unlikely for at least two of the ten.** 2001 TA2 (flagged) and 2015 AM45 (unflagged) both
  serve H as "22.0", one decimal, with no uncertainty and an MPC publication as the reference. 2015 AM45 has the
  smallest MOID of the 33 (0.000487 au, about 73,000 km) and is unflagged. We cannot see SBDB's internal values,
  so this is a likelihood, not a proof.
- **The flags are not simply recomputed whenever an orbit is solved.** 154019's orbit was re-solved on 2026-06-06,
  and both JPL (22.07) and the MPC (22.03) serve an H above 22.0, yet it is still flagged. 2000 WC1 was re-solved
  on 2025-02-11, and its H reference (E2025-CG0) dates from the same month, yet it is flagged at H 22.57. Four of
  the six objects share the solution dates 2021-04-14/15, which may be a bulk re-solution.

Taken together, the 50 F2 rows look like flags that do not follow the current H, which is reading (a), and not
like a consistent boundary convention. We did not see when each flag was set; SBDB does not serve a flag date.
The F2 decision stands as scored. This follow-up removes the idea that the result hinges on an equality
convention, because the ten equality rows break no single convention.

## Limits

Descriptive, post hoc, one day, and only 33 + 6 objects read (three of the six are among the 33); none of it is scored. The 23 flagged designations
were read through a page-reading tool (cross-checked as described above), not from a saved download. We do not
know how JPL sets the PHA flag internally. A served flag may follow a rule we have not been told about (for
example, MPC's PHA list or an H with more digits), and a sentence in the API documentation would settle it. No one
has been contacted; a short note to JPL's Solar System Dynamics group is drafted and held for Sheehan's approval.

MV2, Munim, Inc., mv2@munimtech.com
