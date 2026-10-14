"""Save the CDS/VizieR ReadMe (byte-by-byte column units) of the published
catalogs behind the st_dens findings, so the unit label each journal table
carries can be quoted exactly. Never fails the job: errors are recorded.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

Usage: python fetch_readmes.py --out-dir /out
"""
import argparse
import json
import os
import urllib.request

CATALOGS = {
    "J/AJ/156/264": "Fulton & Petigura 2018 (CKS VII)",
    "J/AJ/154/264": "Torres et al. 2017",
    "J/AJ/153/64": "Mann et al. 2017 (ZEIT IV, Praesepe)",
    "J/AJ/152/105": "MacDonald et al. 2016 (Kepler-80)",
}
MIRRORS = ["https://cdsarc.cds.unistra.fr/ftp/{cat}/ReadMe",
           "https://cdsarc.u-strasbg.fr/ftp/{cat}/ReadMe"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "exo-audit (Munim, Inc.; munimversion2@gmail.com)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def density_lines(text):
    return [ln for ln in text.splitlines() if any(k in ln.lower() for k in ("dens", "rho", "msun", "rsun", "solmass", "solrad"))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out")
    args = ap.parse_args()
    d = os.path.join(args.out_dir, "readmes")
    os.makedirs(d, exist_ok=True)
    log = {}
    for cat, name in CATALOGS.items():
        log[cat] = {"name": name}
        for m in MIRRORS:
            url = m.format(cat=cat)
            try:
                text = get(url)
            except Exception as exc:
                log[cat].setdefault("errors", []).append(f"{url}: {exc}")
                continue
            if "Byte-by-byte" not in text:
                log[cat].setdefault("errors", []).append(f"{url}: no byte-by-byte section ({text[:80]!r})")
                continue
            with open(os.path.join(d, cat.replace("/", "_") + ".txt"), "w", encoding="utf-8") as f:
                f.write(text)
            log[cat].update({"url": url, "density_lines": density_lines(text)})
            break
    with open(os.path.join(d, "fetch_log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
