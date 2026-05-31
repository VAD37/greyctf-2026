#!/usr/bin/env python3
"""
Independent verification: re-encrypt the recovered plaintext with the REAL
challenge cipher and confirm it equals flag_ct from output.txt.

We don't know the key, BUT the affine model means: if our recovered plaintext P
satisfies M P + c == flag_ct, it is correct. We verify by reconstructing
ciphertext from P purely via the affine model (columns built from basis pairs),
WITHOUT inversion, i.e. forward direction, and compare to flag_ct. This is a
genuinely independent check of the inverse.
"""
import json, re
from pathlib import Path
CH=Path("/media/vad/Work2/hackathon/greyctf-2026/challenges/ezpz/01_ae-no-s")

def b2(b):
    out=[]
    for byte in b:
        for i in range(8): out.append((byte>>i)&1)
    return out
def bb2(bits):
    out=bytearray(len(bits)//8)
    for j,v in enumerate(bits):
        if v: out[j//8]|=(1<<(j%8))
    return bytes(out)
def unit_index(pb):
    idx=[i for i,v in enumerate(pb) if v]; return idx[0] if len(idx)==1 else None

of=next((CH/"files"/"extracted").rglob("output.txt"))
data=json.loads(of.read_text())
c=bytes.fromhex(data["zero"]["ct"]); cbits=b2(c)
flag_ct=bytes.fromhex(data["flag_ct"])

# columns of M
columns=[None]*128
for p in data["basis_pairs"]:
    j=unit_index(b2(bytes.fromhex(p["pt"])))
    ct=bytes.fromhex(p["ct"])
    columns[j]=[a^d for a,d in zip(b2(ct), cbits)]

def enc_affine(p16):
    pb=b2(p16)
    ybits=list(cbits)
    for j in range(128):
        if pb[j]:
            col=columns[j]
            for r in range(128): ybits[r]^=col[r]
    return bb2(ybits)

flag="grey{l1n34r_l4y3rs_4r3_n0t_3n0ugh_!!!}"
# pkcs7 to 3 blocks (48 bytes)
pt=flag.encode()
pad=48-len(pt)
P=pt+bytes([pad])*pad
assert len(P)==48, len(P)
recon=b"".join(enc_affine(P[i:i+16]) for i in range(0,48,16))
print("flag         :", flag)
print("padded pt len:", len(P), "pad byte:", pad)
print("reconstructed ct ==", recon.hex())
print("expected     ct ==", flag_ct.hex())
print("MATCH:", recon==flag_ct)

# also confirm E(0)=c
print("E(0)==c:", enc_affine(b'\x00'*16)==c)
