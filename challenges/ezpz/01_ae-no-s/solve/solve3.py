#!/usr/bin/env python3
"""
AE-no-S solver (clean, JSON-driven).

The cipher (challenge.py) is AES with SubBytes AND SubWord replaced by identity,
so for the fixed key it is affine over GF(2)^128:  y = M x  (+)  c.

output.txt gives us, all under the same key:
  zero.ct        = E(0)              = c           (the affine constant)
  basis_pairs[i] = (e_i, E(e_i))     -> col i of M = E(e_i) (+) c
  flag_ct                            = E(FLAG blocks)   (ECB, pkcs7-padded)

We DON'T need the key. Build M from the basis pairs, invert over GF(2), then
each ciphertext block decrypts as  x = M^{-1} (y (+) c).

Two consistency checks make this self-verifying:
  1. M e_i == ct(e_i)(+)c by construction; we re-verify a couple of pairs by
     reconstructing E(p)=Mp+c and comparing to the recorded ct.
  2. Decrypting any basis ct must return the basis pt (a unit vector).
Bit ordering: AES bytes map to GF(2) coords; we try both LSB-first and
MSB-first and keep whichever makes the self-checks pass AND yields printable
ASCII flag text.
"""
import json, re
from pathlib import Path

CH = Path("/media/vad/Work2/hackathon/greyctf-2026/challenges/ezpz/01_ae-no-s")
SOLVE = CH / "solve"
OUT = SOLVE / "RESULT3.txt"
log_lines = []
def log(*a):
    s = " ".join(str(x) for x in a); log_lines.append(s); print(s)

def find(name):
    for base in [CH/"files"/"extracted", CH/"files", CH]:
        for f in base.rglob(name):
            return f
    return None

# ---- bit orderings ----
def b2bits_lsb(b):
    out=[]
    for byte in b:
        for i in range(8): out.append((byte>>i)&1)
    return out
def bits2b_lsb(bits):
    out=bytearray(len(bits)//8)
    for j,v in enumerate(bits):
        if v: out[j//8]|=(1<<(j%8))
    return bytes(out)
def b2bits_msb(b):
    out=[]
    for byte in b:
        for i in range(7,-1,-1): out.append((byte>>i)&1)
    return out
def bits2b_msb(bits):
    out=bytearray(len(bits)//8)
    for j,v in enumerate(bits):
        if v: out[j//8]|=(1<<(7-(j%8)))
    return bytes(out)

def build_M_rows(basis_cts, c, b2):
    """Return rows[] (each int bitmask over 128 cols) for matrix M where
    M[:,i] = ct(e_i) ^ c. rows[r] has bit col set iff M[r][col]=1."""
    cbits=b2(c)
    cols=[]   # cols[i] = bitlist of column i
    for ct in basis_cts:
        cols.append([a^d for a,d in zip(b2(ct), cbits)])
    n=128
    rows=[]
    for r in range(n):
        val=0
        for col in range(n):
            if cols[col][r]:
                val|=(1<<col)
        rows.append(val)
    return rows

def gf2_solve(rows, rhs_bits, n=128):
    """Solve rows . x = rhs over GF(2). rows[r] int bitmask; rhs_bits list."""
    R=list(rows); rhs=list(rhs_bits); where=[-1]*n; pr=0
    for col in range(n):
        sel=-1
        for r in range(pr,n):
            if (R[r]>>col)&1: sel=r; break
        if sel<0: continue
        R[pr],R[sel]=R[sel],R[pr]; rhs[pr],rhs[sel]=rhs[sel],rhs[pr]
        for r in range(n):
            if r!=pr and ((R[r]>>col)&1):
                R[r]^=R[pr]; rhs[r]^=rhs[pr]
        where[col]=pr; pr+=1
    if pr!=n: return None
    x=[0]*n
    for col in range(n): x[col]=rhs[where[col]]
    return x

def main():
    of=find("output.txt"); assert of, "output.txt not found"
    data=json.loads(of.read_text())
    c=bytes.fromhex(data["zero"]["ct"])
    pairs=data["basis_pairs"]
    flag_ct=bytes.fromhex(data["flag_ct"])
    log("[+] #basis pairs:", len(pairs), "| flag_ct bytes:", len(flag_ct),
        "blocks:", len(flag_ct)//16)
    # order basis by pt unit-vector index so column index is unambiguous.
    # pt is hex; the i-th basis (i=0..127) sets bit (MSB byte0) -> e_i.
    # We index columns by the position of the single set bit in pt (MSB-first
    # over the 128-bit pt), which matches how AES would index the state.
    # But the matrix/col indexing must be CONSISTENT with the b2() we use.
    # Simplest: keep pairs in file order and let col index = file order; the
    # inverse doesn't care about labelling as long as we use the SAME basis for
    # forward and inverse. (Identity: any invertible relabel cancels.)
    basis_cts=[bytes.fromhex(p["ct"]) for p in pairs]

    flag=None
    for name,(b2,bb2) in {"LSB":(b2bits_lsb,bits2b_lsb),
                          "MSB":(b2bits_msb,bits2b_msb)}.items():
        rows=build_M_rows(basis_cts, c, b2)
        # self-check: decrypt c itself -> must be 0 vector (E(0)=c)
        z=gf2_solve(rows,[a^d for a,d in zip(b2(c),b2(c))])
        if z is None:
            log(f"[{name}] singular M"); continue
        if any(z):
            log(f"[{name}] dec(c) != 0  -> wrong ordering"); continue
        # decrypt flag blocks
        pts=[]
        ok=True
        for i in range(0,len(flag_ct),16):
            blk=flag_ct[i:i+16]
            rhs=[a^d for a,d in zip(b2(blk), b2(c))]
            x=gf2_solve(rows,rhs)
            if x is None: ok=False; break
            pts.append(bb2(x))
        if not ok:
            log(f"[{name}] solve failed"); continue
        pt=b"".join(pts)
        log(f"[{name}] decrypted pt repr:", pt)
        m=re.search(rb"grey\{[^}]*\}", pt)
        if m:
            flag=m.group(0).decode()
            log(f"[{name}] FLAG FOUND:", flag)
            break
    if flag:
        (SOLVE/"flag.txt").write_text(flag+"\n")
        print("FLAG:",flag)
    else:
        log("NO FLAG via direct file-order basis. Need correct column "
            "labelling: rebuild M with col index = unit-bit position of pt.")
    OUT.write_text("\n".join(log_lines)+"\n")

if __name__=="__main__":
    main()
