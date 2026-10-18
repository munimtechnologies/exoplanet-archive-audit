# ttv_times 0.1.0: KOI-1209.01 mid-times

Run 2026-10-18T10:49Z. By MV2 of Munim, Inc.; made with AI agents. Code Apache-2.0, results CC BY 4.0.

| guess | tc | 1-sigma | depth (ppm) | T14 (h) | frac | n (in) | O-C weighted (d) | O-C unweighted (d) |
|---|---|---|---|---|---|---|---|---|
| 378.17 | 378.14 | 378.138-378.14 | 4961.7 +- 206.7 | 3.2 | 0.2 | 74 (5) | -0.0112 | -0.034 |
| 650.23 | 650.208 | 650.208-650.208 | 6017.4 +- 169.2 | 4.6 | 0.5 | 92 (9) | -0.0527 | -0.1136 |
| 922.51 | 922.522 | 922.52-922.524 | 4542.2 +- 202.7 | 3.8 | 0.2 | 86 (6) | 0.1518 | 0.0528 |
| 1194.96 | 1194.988 | 1194.986-1194.99 | 6583.6 +- 333.5 | 2.6 | 0.5 | 45 (3) | 0.5084 | 0.3712 |
| 1466.47 | 1466.488 | 1466.486-1466.488 | 6698.3 +- 234.1 | 4.4 | 0.5 | 86 (8) | -0.1011 | -0.2764 |

Weighted linear fit: P = 272.10947 +- 0.00033 d, T0 = 378.1512 +- 0.0008 BKJD, chi2 = 83497.2 for 3 dof, max |O-C| = 0.508 d (254.2 sigma).
Unweighted linear fit: P = 272.14760 d, T0 = 378.1740 BKJD, max |O-C| = 0.371 d.

## Holczer et al. 2016 rows for KOI 1209.01

- t2: 209451 bytes, sha256 8cd04f512f91..., 1 rows for the KOI; columns ['KOI', 'T0', 'e_T0', 'Period', 'e_Period', 'Dur', 'Depth', 'SNR', 'SRatio']
  - KOI=1209.01, T0=311.176783, e_T0=0.467484, Period=272.14512529, e_Period=0.00049835, Dur=3.6948, Depth=5931, SNR=38.6, SRatio=1.30
- t3: 28635521 bytes, sha256 74c90c022b7e..., 5 rows for the KOI; columns ['KOI', 'n', 'tn', 'O-C', 'e_O-C', 'f_O-C', 'TDV', 'e_TDV', 'f_TDV', 'TPV', 'e_TPV', 'f_TPV', 'Out', 'Over']
  - KOI=1209.01, n=0, tn=311.176783, O-C=-49.7, e_O-C=2.5e+00, f_O-C=, TDV=-6.100e-02, e_TDV=3.500e-02, f_TDV=, TPV=-1.000e-03, e_TPV=4.000e-02, f_TPV=, Out=0, Over=0
  - KOI=1209.01, n=1, tn=583.321908, O-C=-160., e_O-C=3.4e+00, f_O-C=, TDV=3.000e-02, e_TDV=4.800e-02, f_TDV=, TPV=-3.600e-02, e_TPV=4.100e-02, f_TPV=, Out=0, Over=0
  - KOI=1209.01, n=2, tn=855.467033, O-C=81.1, e_O-C=2.7e+00, f_O-C=, TDV=6.700e-02, e_TDV=3.300e-02, f_TDV=, TPV=-2.200e-02, e_TPV=3.800e-02, f_TPV=, Out=0, Over=0
  - KOI=1209.01, n=3, tn=1127.612159, O-C=516.5, e_O-C=2.5e+00, f_O-C=, TDV=-6.300e-02, e_TDV=3.900e-02, f_TDV=, TPV=5.000e-02, e_TPV=3.900e-02, f_TPV=, Out=0, Over=0
  - KOI=1209.01, n=4, tn=1399.757284, O-C=-387.9, e_O-C=2.6e+00, f_O-C=, TDV=7.000e-03, e_TDV=3.600e-02, f_TDV=, TPV=3.100e-02, e_TPV=3.800e-02, f_TPV=, Out=0, Over=0

Direct time matches (column value + 67.0 within 0.5 d of one of our centres): 5
- tn: Holczer 378.1768 vs ours 378.14 (ours - theirs = -0.0368 d)
- tn: Holczer 650.3219 vs ours 650.208 (ours - theirs = -0.1139 d)
- tn: Holczer 922.467 vs ours 922.522 (ours - theirs = 0.055 d)
- tn: Holczer 1194.6122 vs ours 1194.988 (ours - theirs = 0.3758 d)
- tn: Holczer 1466.7573 vs ours 1466.488 (ours - theirs = -0.2693 d)
