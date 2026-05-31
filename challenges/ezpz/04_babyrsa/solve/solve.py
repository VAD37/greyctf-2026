#!/usr/bin/env python3
"""babyRSA solver (GreyCTF Qualifiers 2026, ezpz/crypto, id 21).

challenge.py:
    p, q = getPrime(1024), getPrime(1024)
    N = p**2 * q          # ~3072-bit modulus
    e = 65537
    c = pow(m, e, N)
    p_msb = (p >> 320) << 320     # leaks the top 704 bits of p, low 320 unknown

Weakness: high bits of a prime factor are known, AND p^2 | N.
    Let x0 = p mod 2^320 (the unknown low 320 bits), so p = p_msb + x0.
    g(x) = (p_msb + x)^2  has the small root x0 modulo p^2.
    p^2 ~= N^(2/3)  => Coppersmith univariate with beta = 2/3, degree 2,
    root bound N^(beta^2/deg) = N^(2/9) ~= 2^683 >> 2^320.  Tons of margin,
    so a tiny lattice (m=t=2) recovers x0 -> p instantly.

Then: q = N // p^2,  phi(N) = p*(p-1)*(q-1),  d = e^-1 mod phi,  m = c^d mod N.

LLL via fpylll (no Sage on the box). Params in solve/params.json (verbatim from
challenge.py).
"""
import json
import os

from fpylll import IntegerMatrix, LLL
from Crypto.Util.number import long_to_bytes

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "params.json")))
N, e, c, p_msb = P["N"], P["e"], P["c"], P["p_msb"]
UNKNOWN_BITS = 320
X = 1 << UNKNOWN_BITS                      # bound on the unknown low bits of p


def polymul(a, b):
    r = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                r[i + j] += ai * bj
    return r


def integer_root_in_range(coeffs, X):
    """Integer root in [0, X] of poly `coeffs` (low->high) via sign-change bisection."""
    def f(x):
        v = 0
        for a in reversed(coeffs):
            v = v * x + a
        return v

    lo, hi = 0, X
    flo, fhi = f(lo), f(hi)
    if flo == 0:
        return lo
    if fhi == 0:
        return hi
    if (flo < 0) == (fhi < 0):
        return None                       # no sign change -> try another lattice row
    while lo < hi:
        mid = (lo + hi) // 2
        fm = f(mid)
        if fm == 0:
            return mid
        if (flo < 0) != (fm < 0):
            hi = mid
        else:
            lo, flo = mid + 1, fm
    return lo if f(lo) == 0 else None


def coppersmith_p2(m, t):
    """Recover p via Coppersmith on g(x)=(p_msb+x)^2 mod p^2 (p^2 | N, beta=2/3).

    Howgrave-Graham shifts:
        N^(m-i) * g(x)^i      for i = 0..m
        x^j     * g(x)^m      for j = 1..t
    Scale x -> x*X, LLL-reduce, read each short row back as an integer polynomial,
    and look for an integer root that factors N.
    """
    g = [p_msb * p_msb, 2 * p_msb, 1]     # (x + p_msb)^2, low->high

    gpow = [[1]]
    for _ in range(m + 1):
        gpow.append(polymul(gpow[-1], g))

    polys = []
    for i in range(0, m + 1):
        polys.append([co * (N ** (m - i)) for co in gpow[i]])
    for j in range(1, t + 1):
        polys.append([0] * j + gpow[m][:])

    dim = len(polys)
    maxdeg = max(len(p) for p in polys)
    M = IntegerMatrix(dim, maxdeg)
    for r, p in enumerate(polys):
        for k, coef in enumerate(p):
            M[r, k] = coef * (X ** k)

    LLL.reduction(M)

    for row in range(dim):
        coeffs = []
        ok = True
        for k in range(maxdeg):
            val = int(M[row, k])
            xk = X ** k
            if val % xk != 0:
                ok = False
                break
            coeffs.append(val // xk)
        if not ok or all(a == 0 for a in coeffs):
            continue
        x0 = integer_root_in_range(coeffs, X)
        if x0 is not None:
            p = p_msb + x0
            if p > 1 and N % p == 0:
                return p
    return None


def finish(p):
    assert N % (p * p) == 0, "p^2 does not divide N"
    q = N // (p * p)
    assert p * p * q == N
    phi = p * (p - 1) * (q - 1)            # Euler phi of p^2 * q
    d = pow(e, -1, phi)
    m = pow(c, d, N)
    flag = long_to_bytes(m)
    print("[+] recovered p =", p)
    print("[+] q           =", q)
    print("[+] plaintext   =", flag)
    if b"grey{" in flag:
        s = flag[flag.index(b"grey{"):]
        s = s[: s.index(b"}") + 1].decode()
        print("[FLAG]", s)
        with open(os.path.join(HERE, "flag.txt"), "w") as fh:
            fh.write(s + "\n")
    else:
        print("[!] 'grey{' not found in decrypted plaintext")


def main():
    for (m, t) in [(2, 2), (3, 3), (4, 4), (5, 5)]:
        print(f"[*] Coppersmith try m={m} t={t} (dim={m + 1 + t})", flush=True)
        p = coppersmith_p2(m, t)
        if p:
            finish(p)
            return
    print("[-] no solution found")


if __name__ == "__main__":
    main()
