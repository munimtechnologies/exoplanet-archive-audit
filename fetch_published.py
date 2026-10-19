#!/usr/bin/env python3
# Apache-2.0. fetch_published 0.2.0, MV2 of Munim, Inc. (mv2@munimtech.com). Made with AI agents.
"""Wait for a file to appear at a public URL (the publish commit may land after this job starts), save it, and
print its size and sha256, so a gated step runs on the published file rather than a hand copy.
0.2.0: --expect-text accepts a text file that contains the given string (0.1.0 accepted only valid JSON)."""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request


def fetch(url, timeout=60):
    """Bytes at url, or None on any HTTP or network error."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def acceptable(body, expect_text=""):
    """True if body is valid JSON (no expect_text) or contains expect_text (UTF-8)."""
    if expect_text:
        return expect_text.encode("utf-8") in body
    try:
        json.loads(body.decode("utf-8"))
        return True
    except Exception:
        return False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--wait-minutes", type=int, default=45)
    ap.add_argument("--every-seconds", type=int, default=60)
    ap.add_argument("--expect-text", default="")
    args = ap.parse_args(argv)
    deadline = time.time() + 60 * args.wait_minutes
    while True:
        body = fetch(args.url)
        if body is not None and acceptable(body, args.expect_text):
            os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
            with open(args.out, "wb") as f:
                f.write(body)
            print(json.dumps({"url": args.url, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}))
            return 0
        if time.time() >= deadline:
            print(json.dumps({"url": args.url, "error": "not available before deadline"}))
            return 1
        time.sleep(args.every_seconds)


if __name__ == "__main__":
    sys.exit(main())
