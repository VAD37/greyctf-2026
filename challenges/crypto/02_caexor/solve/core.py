#!/usr/bin/env python3
"""caexor core algebra (integer model, verified against the word class)."""
B = 29
M = B ** 16


def to_d(v):
    d = [0] * 16
    for i in range(15, -1, -1):
        d[i] = v % B
        v //= B
    return d


def fr_d(d):
    v = 0
    for x in d:
        v = v * B + x
    return v


def s2i(s):
    v = 0
    for ch in s:
        v = v * B + (ord(ch) - 97)
    return v


C = s2i("cryptoisverycool")
F = s2i("{|}helloworld{|}")
H0 = s2i("greyctfisawesome")
TARGET = s2i("gimmeflagthankuu")
FINV = pow(F, -1, M)
ALLOWED = list(range(26))  # 'a'..'z'


def fwd(h, d0, d1):
    h = ((h + C) * F) % M
    dg = to_d(h)
    dg[14] = (dg[14] ^ d0) % B
    dg[15] = (dg[15] ^ d1) % B
    return fr_d(dg)


def bwd(v, d0, d1):
    dg = to_d(v)
    dg[14] = (dg[14] ^ d0) % B
    dg[15] = (dg[15] ^ d1) % B
    return ((fr_d(dg) * FINV) % M - C) % M


def caexor_int(s):
    h = H0
    for i in range(0, len(s), 2):
        h = fwd(h, ord(s[i]) - 97, ord(s[i + 1]) - 97)
    return h


def fwd_path(h, s):
    for i in range(0, len(s), 2):
        h = fwd(h, ord(s[i]) - 97, ord(s[i + 1]) - 97)
    return h
