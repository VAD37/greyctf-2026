#!/usr/bin/env python3
"""
caexor (GreyCTF 2026, crypto, CTFd id 15) — full solver.

REAL challenge (files/extracted/dist-caexor/chal.py). The original task brief
(Caesar+XOR decrypt oracle) was WRONG. The live service is a custom algebraic
preimage challenge:

  `word` = 16 base-29 digits (a=0..z=25, {=26 |=27 }=28), big-endian.
  Per 2-char chunk of input s (remote chars a-z only):
      h = ((h + C) * F) mod (29**16)                 # affine, bijective
      then set base-29 digits 14,15 of h to (d14^c0)%29,(d15^c1)%29  # the chunk
  start  H0 = word("greyctfisawesome")
  consts C  = word("cryptoisverycool"),  F = word("{|}helloworld{|}")
  goal   caexor(s) == TARGET = word("gimmeflagthankuu")
  gate   len(s) >= 24, NOT s.startswith('a'), no chars in '{|}', and the flag
         prints only when len(s) <= LEN  => need the SHORTEST preimage (24 chars).

Solve idea (the intended crypto):
  Multiply == integer mul mod M=29**16 (verified); F is a unit, so A(h)=(h+C)*F
  is affine bijective. The only per-chunk freedom is overwriting the two LOWEST
  base-29 digits. Writing each chunk as adding a delta d_i supported on digits
  14,15, deltas propagate LINEARLY: caexor(s) = A^N(H0) + sum_i F^{N-1-i} * d_i.
  So solving for N chunks is one modular linear equation
      sum_i F^{N-1-i} * d_i == TARGET - A^N(H0)   (mod M)
  with each d_i small (a 2-digit perturbation). Solve it with LLL (Kannan
  embedding). Because the realizable delta at a step depends on the live digits
  (xor reaches 26/29 values; n14 must stay in 0..28), we re-solve the remaining
  suffix's linear system at every step and realize its leading delta (falling
  back to the nearest realizable delta, which the next re-solve absorbs).
  N=12 => exactly 24 chars => len==LEN => flag prints.

Run from repo root: uv run python challenges/crypto/02_caexor/solve/solve.py
"""
import re
import sys

from pwn import context, remote

import core as K
from lll import lll

context.log_level = "error"

HOST = "challs.nusgreyhats.org"
PORT = 37267
M, F = K.M, K.F


def A(x):
    return (F * x + F * K.C) % M


def reach(y):
    return {(y ^ x) % 29 for x in range(26)}


def chunk_for(y, n):
    for x in range(26):
        if (y ^ x) % 29 == n:
            return x
    return None


def delta_system(h_cur, k):
    """Smallest deltas (len k) with sum F^{k-1-i} d_i == TARGET - A^k(h_cur) mod M."""
    a = h_cur
    for _ in range(k):
        a = A(a)
    R = (K.TARGET - a) % M
    c = [pow(F, k - 1 - i, M) for i in range(k)]
    We = 1 << 110
    T = 1 << 20
    rows = []
    for i in range(k):
        r = [0] * (k + 2)
        r[i] = 1
        r[k] = c[i] * We
        rows.append(r)
    mrow = [0] * (k + 2)
    mrow[k] = M * We
    rows.append(mrow)
    trow = [0] * (k + 2)
    trow[k] = -R * We
    trow[k + 1] = T
    rows.append(trow)
    for row in lll(rows):
        if abs(row[k + 1]) == T and row[k] == 0:
            sgn = 1 if row[k + 1] == T else -1
            d = [sgn * row[i] for i in range(k)]
            if sum(c[i] * d[i] for i in range(k)) % M == R:
                return d
    return None


def realize_step(h, di):
    """Apply exact delta di by overwriting digits 14,15; return (chunk,h') or None."""
    y = A(h)
    yd = K.to_d(y)
    y14, y15 = yd[14], yd[15]
    r14, r15 = reach(y14), reach(y15)
    for da in range(-y14, 29 - y14):
        db = di - 29 * da
        n15 = y15 + db
        if not (0 <= n15 < 29):
            continue
        n14 = y14 + da
        if n14 in r14 and n15 in r15:
            d0, d1 = chunk_for(y14, n14), chunk_for(y15, n15)
            return (d0, d1), K.fwd(h, d0, d1)
    return None


def nearest_step(h):
    """Realizable chunk giving the smallest-magnitude delta (fallback)."""
    y = A(h)
    yd = K.to_d(y)
    y14, y15 = yd[14], yd[15]
    best = None
    for d0 in range(26):
        da = (y14 ^ d0) % 29 - y14
        for d1 in range(26):
            db = (y15 ^ d1) % 29 - y15
            di = 29 * da + db
            if best is None or abs(di) < abs(best[0]):
                best = (di, d0, d1)
    _, d0, d1 = best
    return (d0, d1), K.fwd(h, d0, d1)


def _try_once(N):
    """One incremental-resolve pass. Returns chunks list or None on any glitch."""
    h = K.H0
    chunks = []
    for step in range(N):
        d = delta_system(h, N - step)
        applied = None
        if d is not None:
            r = realize_step(h, d[0])
            if r is not None:
                applied, h = r
        if applied is None:
            applied, h = nearest_step(h)
        d0, d1 = applied
        if not (0 <= d0 <= 25 and 0 <= d1 <= 25):  # must be valid a-z digits
            return None
        chunks.append((d0, d1))
    return chunks


def _valid(s, N):
    return (len(s) == 2 * N
            and all("a" <= c <= "z" for c in s)
            and not s.startswith("a")
            and not any(c in s for c in "{|}")
            and K.caexor_int(s) == K.TARGET)


def find_preimage(N):
    """Return a fully-validated N-chunk (2N-char) preimage, or None."""
    chunks = _try_once(N)
    if chunks is None:
        return None
    s = "".join(chr(97 + a) + chr(97 + b) for a, b in chunks)
    return s if _valid(s, N) else None


def shortest_preimage(nmin=12, nmax=40):
    """Smallest N (>=12, i.e. >=24 chars) yielding a verified preimage."""
    for N in range(nmin, nmax + 1):
        s = find_preimage(N)
        if s is not None:
            return s
    raise RuntimeError("no verified preimage found")


def get_flag(host, port, s):
    io = remote(host, port)
    io.recvuntil(b">> ")
    io.sendline(s.encode())
    resp = io.recvall(timeout=6).decode(errors="replace")
    io.close()
    m = re.search(r"grey\{[^}\n]{1,256}\}", resp)
    return (m.group(0) if m else None), resp


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else PORT
    s = shortest_preimage()
    print("PREIMAGE:", s, "(len", len(s), ")")
    flag, resp = get_flag(host, port, s)
    if flag:
        print("FLAG:", flag)
        return 0
    print("NO FLAG. Server response:")
    print(resp)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
