#!/usr/bin/env python3
import json, re
import numpy as np
EZ = "/media/vad/Work2/hackathon/greyctf-2026/challenges/ezpz"

def bits_of(v): return np.array([(v >> (127 - i)) & 1 for i in range(128)], dtype=np.uint8)
def int_of(bv):
    v = 0
    for i in range(128):
        if bv[i] & 1: v |= (1 << (127 - i))
    return v
def gf2_inv(A):
    n = A.shape[0]
    M = np.concatenate([A.copy() % 2, np.eye(n, dtype=np.uint8)], axis=1)
    row = 0
    for col in range(n):
        piv = next((r for r in range(row, n) if M[r, col]), None)
        if piv is None: raise ValueError("singular")
        M[[row, piv]] = M[[piv, row]]
        for r in range(n):
            if r != row and M[r, col]: M[r] ^= M[row]
        row += 1
    return M[:, n:] % 2

d = json.load(open(f"{EZ}/01_ae-no-s/files/extracted/dist-AE-no-S/output.txt"))
I = lambda h: int(h, 16)
b = I(d["zero"]["ct"])
cols = [None]*128
for pr in d["basis_pairs"]:
    x = I(pr["pt"]); cols[127 - (x.bit_length()-1)] = I(pr["ct"]) ^ b
A = np.zeros((128,128), dtype=np.uint8)
for k in range(128): A[:,k] = bits_of(cols[k])
ct = bytes.fromhex(d["flag_ct"])

ans = "AE_FAIL"
for M in (A, A.T):
    inv = gf2_inv(M)
    raw = b"".join(int_of((inv @ bits_of(int.from_bytes(ct[o:o+16],"big") ^ b)) % 2).to_bytes(16,"big")
                   for o in range(0, len(ct), 16))
    m = re.search(rb"grey\{[ -~]*\}", raw)
    if m:
        ans = m.group().decode(); break
open(f"{EZ}/_ans_ae.txt","w").write(ans + "\n")

# self-test gf2_inv
Ai = gf2_inv(A)
ident = ((A @ Ai) % 2 == np.eye(128, dtype=np.uint8)).all()
open(f"{EZ}/_ans_selftest.txt","w").write(("INV_OK" if ident else "INV_BAD") + "\n")

# rsa
from pathlib import Path
src = Path(f"{EZ}/04_babyrsa/files/extracted/dist-babyRSA/challenge.py").read_text()
g = lambda n: int(re.search(rf"# {n} = (\d+)", src).group(1))
N,e,c = g("N"),g("e"),g("c")
cand = "grey{th1s_15_pr0b4bly_t00_34sy_n0w4d4y5_1n34v80n23}"
ok = pow(int.from_bytes(cand.encode(),"big"), e, N) == c
open(f"{EZ}/_ans_rsa.txt","w").write(("MATCH " if ok else "NOMATCH ") + cand + "\n")
