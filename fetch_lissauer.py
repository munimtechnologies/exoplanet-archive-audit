"""fetch_lissauer: save the machine-readable tables of Lissauer et al. 2024 (PSJ 5, 152; arXiv:2311.00238),
whose Table 1 gives a disposition for almost 9,700 KOIs, so flagged orphans can be looked up by hand.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.
Tries the CDS archive (J/PSJ/5/152) and then the arXiv source. Never raises: every outcome goes to
fetch.json. Only text tables are kept (no code is run from the downloads).

Usage: python fetch_lissauer.py --out-dir /out/lissauer
"""
import argparse
import io
import json
import os
import re
import tarfile
import urllib.request

UA = "koi-orphans/0.1.0 (Munim, Inc.; mv2@munimtech.com)"
CDS = "https://cdsarc.cds.unistra.fr/ftp/J/PSJ/5/152/"
ARXIV = "https://arxiv.org/e-print/2311.00238"
KEEP = (".dat", ".txt", ".csv", ".mrt", ".tex")
MAX_BYTES = 40_000_000


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read(MAX_BYTES)


def save(out_dir, name, data):
    path = os.path.join(out_dir, os.path.basename(name))
    with open(path, "wb") as f:
        f.write(data)
    return path


def from_cds(out_dir, log):
    readme = get(CDS + "ReadMe")
    save(out_dir, "cds_ReadMe.txt", readme)
    names = sorted(set(re.findall(r"^(\S+\.dat)\s", readme.decode("utf-8", "replace"), re.M)))
    log["cds_files"] = names
    for n in names:
        try:
            save(out_dir, "cds_" + n, get(CDS + n))
        except Exception as exc:
            log.setdefault("errors", []).append(f"cds {n}: {type(exc).__name__}: {exc}"[:300])
    return bool(names)


def from_arxiv(out_dir, log):
    blob = get(ARXIV)
    kept = []
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tf:
        for m in tf.getmembers():
            if m.isfile() and m.name.lower().endswith(KEEP) and m.size <= MAX_BYTES:
                save(out_dir, "arxiv_" + os.path.basename(m.name), tf.extractfile(m).read())
                kept.append(m.name)
    log["arxiv_files"] = kept
    return bool(kept)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    log = {}
    for name, fn in (("cds", from_cds), ("arxiv", from_arxiv)):
        try:
            log[name + "_ok"] = fn(args.out_dir, log)
        except Exception as exc:
            log[name + "_ok"] = False
            log.setdefault("errors", []).append(f"{name}: {type(exc).__name__}: {exc}"[:300])
    with open(os.path.join(args.out_dir, "fetch.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, indent=1)
    print(json.dumps(log, indent=1))
    return 0


if __name__ == "__main__":
    main()
