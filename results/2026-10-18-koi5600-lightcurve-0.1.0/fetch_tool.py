"""Fetch the published kepler_alias tool and its tests, and record what was run.

Munim, Inc. (MV2 of Munim, Inc.). Made with AI. Apache-2.0. Standard library only.

thirds_lc builds on the copy published in munimtechnologies/exoplanet-archive-audit, not a local
edit, so the result can be reproduced from the repo. Prints each file's sha256 and stops if the
version is not the one the pre-registration names.

    python fetch_tool.py --dest /out/tool --version 0.3.0
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request

RAW = "https://raw.githubusercontent.com/munimtechnologies/exoplanet-archive-audit/main/"
FILES = ("kepler_alias.py", "test_kepler_alias.py")
UA = "koi5600lc-fetch/0.1.0 (Munim, Inc.; mv2@munimtech.com)"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    ap.add_argument("--version", required=True)
    args = ap.parse_args(argv)
    os.makedirs(args.dest, exist_ok=True)
    record = {"source": RAW, "files": {}}
    for name in FILES:
        req = urllib.request.Request(RAW + name, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        with open(os.path.join(args.dest, name), "wb") as f:
            f.write(data)
        record["files"][name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("thirds_lc.py", "test_thirds_lc.py"):
        with open(os.path.join(here, name), "rb") as f:
            data = f.read()
        record["files"][name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "local": True}
    with open(os.path.join(args.dest, "kepler_alias.py"), encoding="utf-8") as f:
        m = re.search(r'^VERSION = "([^"]+)"', f.read(), re.M)
    record["version"] = m.group(1) if m else None
    with open(os.path.join(args.dest, "fetched.json"), "w", encoding="utf-8") as f:
        json.dump(record, f, indent=1)
    print(json.dumps(record, indent=1))
    if record["version"] != args.version:
        print(f"version {record['version']} is not the pre-registered {args.version}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
