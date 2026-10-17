"""lissauer_xmatch: where do the NASA Exoplanet Archive's Kepler dispositions and periods differ from
Lissauer et al. 2024 (PSJ 5, 152), Table 1?

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

Lissauer et al. 2024 re-fit and re-dispositioned the 9,564 KOIs of the Archive's cumulative table (plus a
few later ones). Their machine-readable Table 1 (CC BY 4.0) gives a four-letter Status: this work, DR25
supplemental, DR25, DR24 (P planet candidate, F false positive, N not in that catalogue, S rejected for
S/N < 7.1, R radius too large, M mass above 13 Jupiter masses). The Archive's cumulative table has not
taken these up. This tool joins the two by KOI number and counts where they disagree.

    python lissauer_xmatch.py --out-dir out            # live: IOP table + Archive TAP
    python lissauer_xmatch.py --out-dir out --mrt-file t1.txt --cumulative-file cum.csv
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from fractions import Fraction

VERSION = "0.1.0"
MRT_URL = "https://content.cld.iop.org/journals/2632-3338/5/6/152/revision3/psjad0e6et1_mrt.txt"
TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
UA = f"lissauer_xmatch/{VERSION} (MV2 of Munim, Inc.; mv2@munimtech.com)"
CUM_COLS = "kepoi_name,kepid,kepler_name,koi_disposition,koi_parm_prov,koi_period,koi_model_snr"
DR25_PROV = "q1_q17_dr25_koi"
REJECT = set("FSMR")
# Byte ranges (1-based, inclusive) from the table's own header, used if the header can't be parsed.
FALLBACK = {"KIC": (1, 8), "KOI": (10, 16), "Kepler": (18, 31), "Period": (33, 46),
            "S/N": (255, 260), "MES": (262, 269), "Status": (548, 551)}
SPEC_RE = re.compile(r"^\s*(\d+)(?:\s*-\s*(\d+))?\s+([AIFE]\d+(?:\.\d+)?)\s+(\S+)\s+(\S+)")
# KOIs named in the paper's text or in our earlier findings, reported one by one.
WATCH = ["K00001.01", "K01101.02", "K01922.02", "K02167.02", "K01353.03", "K06262.01", "K04777.01",
         "K02061.03", "K00245.04", "K00129.01", "K00125.01"]


def koi_name(text):
    """'1101.02' -> 'K01101.02'."""
    whole, _, frac = text.strip().partition(".")
    return f"K{int(whole):05d}.{(frac + '00')[:2]}"


def to_float(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def is_rule(line):
    s = line.strip()
    return len(s) >= 20 and set(s) <= set("-=")


def parse_byte_spec(lines):
    """Label -> (first byte, last byte) from an AAS MRT 'Byte-by-byte Description'."""
    spec = {}
    for line in lines:
        m = SPEC_RE.match(line)
        if m:
            a = int(m.group(1))
            b = int(m.group(2)) if m.group(2) else a
            spec[m.group(5)] = (a, b)
    return spec


def parse_mrt(text):
    """Rows of Table 1 as dicts; also returns the column ranges used."""
    lines = text.splitlines()
    rules = [i for i, line in enumerate(lines) if is_rule(line)]
    start = rules[-1] + 1 if rules else 0
    spec = parse_byte_spec(lines[:start])
    cols = {k: spec.get(k, v) for k, v in FALLBACK.items()}

    def field(line, key):
        a, b = cols[key]
        return line[a - 1:b].strip()

    rows = []
    for line in lines[start:]:
        if not line.strip():
            continue
        koi = field(line, "KOI")
        if not re.fullmatch(r"\d+\.\d+", koi):
            continue
        rows.append({"kepoi_name": koi_name(koi), "kic": int(field(line, "KIC") or 0),
                     "kepler_name": field(line, "Kepler"), "period": to_float(field(line, "Period")),
                     "snr": to_float(field(line, "S/N")), "mes": to_float(field(line, "MES")),
                     "status": field(line, "Status")})
    return rows, cols


def letter(status, i):
    return status[i] if len(status) > i else ""


def archive_letter(disposition):
    return {"CONFIRMED": "P", "CANDIDATE": "P", "FALSE POSITIVE": "F"}.get(disposition, "")


def nearest_fraction(ratio, limit=12):
    """Closest a/b (a, b <= limit) to ratio, and |ratio - a/b| / (a/b)."""
    best = None
    for b in range(1, limit + 1):
        for a in range(1, limit + 1):
            f = a / b
            err = abs(ratio - f) / f
            if best is None or err < best[2]:
                best = (a, b, err)
    frac = Fraction(best[0], best[1])
    return f"{frac.numerator}/{frac.denominator}", best[2]


def xmatch(archive, lissauer, period_tol=1e-3):
    """Join on KOI name. Returns merged rows, archive-only names, Lissauer-only names."""
    lis = {r["kepoi_name"]: r for r in lissauer}
    merged, arch_only = [], []
    for a in archive:
        name = a["kepoi_name"]
        r = lis.get(name)
        if r is None:
            arch_only.append(name)
            continue
        pa, pl = to_float(a.get("koi_period")), r["period"]
        ratio = pl / pa if pa and pl else None
        frac, frac_err = nearest_fraction(ratio) if ratio else ("", None)
        kepid = int(a["kepid"]) if str(a.get("kepid", "")).strip() else 0
        prov = a.get("koi_parm_prov", "")
        merged.append({
            "kepoi_name": name, "kepid": kepid, "kic_match": kepid == r["kic"],
            "kepler_name": a.get("kepler_name", "") or r["kepler_name"],
            "archive_disposition": a.get("koi_disposition", ""), "parm_prov": prov,
            "orphan": bool(prov) and prov != DR25_PROV,
            "archive_period": pa, "archive_snr": to_float(a.get("koi_model_snr")),
            "lissauer_status": r["status"], "lissauer_now": letter(r["status"], 0),
            "lissauer_dr25supp": letter(r["status"], 1),
            "lissauer_period": pl, "lissauer_snr": r["snr"],
            "period_ratio": ratio, "ratio_fraction": frac, "ratio_fraction_err": frac_err,
            "period_flag": ratio is not None and abs(ratio - 1) > period_tol,
        })
    seen = {a["kepoi_name"] for a in archive}
    lis_only = [n for n in lis if n not in seen]
    return merged, arch_only, lis_only


def summarize(merged, arch_only, lis_only, n_lissauer):
    cross = {}
    for m in merged:
        row = cross.setdefault(m["archive_disposition"], {})
        row[m["lissauer_now"]] = row.get(m["lissauer_now"], 0) + 1
    cands = [m for m in merged if m["archive_disposition"] == "CANDIDATE"]
    by_prov = {}
    for m in cands:
        row = by_prov.setdefault(m["parm_prov"], {})
        row[m["lissauer_now"]] = row.get(m["lissauer_now"], 0) + 1

    def rate(rows):
        n = len(rows)
        k = sum(1 for m in rows if m["lissauer_now"] in REJECT)
        return {"n": n, "rejected": k, "fraction": round(k / n, 4) if n else None}

    orphan_rate = rate([m for m in cands if m["orphan"]])
    dr25_rate = rate([m for m in cands if not m["orphan"]])
    supp = [m for m in merged if m["lissauer_dr25supp"] in ("P", "F") and archive_letter(m["archive_disposition"])]
    agree = sum(1 for m in supp if m["lissauer_dr25supp"] == archive_letter(m["archive_disposition"]))
    flags = [m for m in merged if m["period_flag"]]
    by_name = {m["kepoi_name"]: m for m in merged}
    watch = {}
    for name in WATCH:
        m = by_name.get(name)
        watch[name] = None if m is None else {
            k: m[k] for k in ("archive_disposition", "parm_prov", "lissauer_status", "archive_period",
                              "lissauer_period", "ratio_fraction", "lissauer_snr", "archive_snr")}
    return {
        "version": VERSION, "n_lissauer_rows": n_lissauer, "n_archive_rows": len(merged) + len(arch_only),
        "n_matched": len(merged), "n_archive_only": len(arch_only), "n_lissauer_only": len(lis_only),
        "archive_only": arch_only[:50], "lissauer_only": lis_only[:200],
        "n_kic_mismatch": sum(1 for m in merged if not m["kic_match"]),
        "lissauer_now_counts": _count(m["lissauer_now"] for m in merged),
        "crosstab_archive_vs_lissauer_now": cross,
        "candidates_by_prov_vs_lissauer_now": by_prov,
        "candidates_rejected": sum(1 for m in cands if m["lissauer_now"] in REJECT),
        "candidate_reject_rate_orphan": orphan_rate, "candidate_reject_rate_dr25": dr25_rate,
        "confirmed_rejected": sum(1 for m in merged if m["archive_disposition"] == "CONFIRMED"
                                  and m["lissauer_now"] in REJECT),
        "fp_now_p": sum(1 for m in merged if m["archive_disposition"] == "FALSE POSITIVE"
                        and m["lissauer_now"] == "P"),
        "dr25supp_letter_vs_archive": {"n": len(supp), "agree": agree},
        "n_period_flags": len(flags),
        "period_flags_by_fraction": _count(m["ratio_fraction"] for m in flags),
        "watch": watch,
    }


def _count(values):
    out = {}
    for v in values:
        out[v] = out.get(v, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as resp:
                return resp.read()
        except Exception as exc:  # network trouble: retry, then report
            last = exc
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"fetch failed: {url}: {last}")


def read_cumulative(text):
    return list(csv.DictReader(io.StringIO(text, newline="")))


def write_csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


MERGED_COLS = ["kepoi_name", "kepid", "kepler_name", "archive_disposition", "parm_prov", "orphan",
               "lissauer_status", "lissauer_now", "lissauer_dr25supp", "archive_period", "lissauer_period",
               "period_ratio", "ratio_fraction", "ratio_fraction_err", "archive_snr", "lissauer_snr",
               "kic_match"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--mrt-file")
    ap.add_argument("--cumulative-file")
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    log = {"version": VERSION, "python": sys.version.split()[0]}

    if args.mrt_file:
        raw = open(args.mrt_file, "rb").read()
        log["mrt_source"] = args.mrt_file
    else:
        raw = fetch(MRT_URL)
        log["mrt_source"] = MRT_URL
        with open(os.path.join(args.out_dir, "lissauer2024_table1_mrt.txt"), "wb") as fh:
            fh.write(raw)
    log["mrt_bytes"], log["mrt_sha256"] = len(raw), hashlib.sha256(raw).hexdigest()
    lissauer, cols = parse_mrt(raw.decode("utf-8", errors="replace"))
    log["mrt_columns"] = cols

    if args.cumulative_file:
        cum_text = open(args.cumulative_file, encoding="utf-8").read()
        log["cumulative_source"] = args.cumulative_file
    else:
        q = f"select {CUM_COLS} from cumulative"
        url = TAP_URL + "?" + urllib.parse.urlencode({"query": q, "format": "csv"})
        cum_text = fetch(url).decode("utf-8")
        log["cumulative_source"] = url
        log["cumulative_fetched_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    archive = read_cumulative(cum_text)

    merged, arch_only, lis_only = xmatch(archive, lissauer)
    summary = summarize(merged, arch_only, lis_only, len(lissauer))
    summary["fetch"] = log
    write_csv(os.path.join(args.out_dir, "xmatch.csv"), merged, MERGED_COLS)
    write_csv(os.path.join(args.out_dir, "candidates_rejected.csv"),
              [m for m in merged if m["archive_disposition"] == "CANDIDATE" and m["lissauer_now"] in REJECT],
              MERGED_COLS)
    write_csv(os.path.join(args.out_dir, "disagreements_other.csv"),
              [m for m in merged if (m["archive_disposition"] == "CONFIRMED" and m["lissauer_now"] in REJECT)
               or (m["archive_disposition"] == "FALSE POSITIVE" and m["lissauer_now"] == "P")], MERGED_COLS)
    write_csv(os.path.join(args.out_dir, "period_flags.csv"), [m for m in merged if m["period_flag"]],
              MERGED_COLS)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("archive_only", "lissauer_only")},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
