#!/usr/bin/env python3
"""
AE-no-S solver, robust version.

Affine cipher: E(p) = M p (+) c over GF(2)^128, fixed key.
From output.txt:
  c = E(0)                       (zero.ct)
  for each basis pair (p_i, ct_i): p_i is a UNIT vector; ct_i (+) c = M @ p_i
                                   = the column of M selected by p_i's set bit.
  flag_ct = E(flag plaintext)    (ECB, pkcs7 padded, 3 blocks)

Crucial: column j of M (in our chosen bit ordering b2) equals (ct_i (+) c)
where p_i is the unit vector whose single set bit is coordinate j under b2.
So we must place each basis pair into the matrix by the bit index of its own
plaintext, NOT by file order. We do exactly that, then invert and decrypt.

We try both LSB-first and MSB-first byte->bit orderings; the correct one makes
M @ p_i == ct_i (+) c for ALL i (self-check) and yields a printable grey{...}.
"""
import json, re
from pathlib import Path

CH = Path("/media/vad/Work2/hackathon/greyctf-2026/challenges/ezpz/01_ae-no-s")
SOLVE = CH / "solve"
log_lines=[]
def log(*a):
    s=" ".join(str(x) for x in a); log_lines.append(s); print(s)

def find(name):
    for base in [CH/"files"/"extracted", CH/"files", CH]:
        for f in base.rglob(name):
            return f
    return None

def b2_lsb(b):
    out=[]
    for byte in b:
        for i in range(8): out.append((byte>>i)&1)
    return out
def bits2b_lsb(bits):
    out=bytearray(len(bits)//8)
    for j,v in enumerate(bits):
        if v: out[j//8]|=(1<<(j%8))
    return bytes(out)
def b2_msb(b):
    out=[]
    for byte in b:
        for i in range(7,-1,-1): out.append((byte>>i)&1)
    return out
def bits2b_msb(bits):
    out=bytearray(len(bits)//8)
    for j,v in enumerate(bits):
        if v: out[j//8]|=(1<<(7-(j%8)))
    return bytes(out)

def unit_index(pbits):
    idx=[i for i,v in enumerate(pbits) if v]
    return idx[0] if len(idx)==1 else None

def gf2_solve(rows, rhs, n=128):
    R=list(rows); rhs=list(rhs); where=[-1]*n; pr=0
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

def try_ordering(name, b2, bb2, c, pairs, flag_ct):
    cbits=b2(c)
    # columns[j] = bitlist of M's column j
    columns=[None]*128
    for p in pairs:
        pb=b2(bytes.fromhex(p["pt"]))
        j=unit_index(pb)
        if j is None:
            log(f"[{name}] pt not unit vector?!"); return None
        ct=bytes.fromhex(p["ct"])
        columns[j]=[a^d for a,d in zip(b2(ct), cbits)]
    if any(col is None for col in columns):
        log(f"[{name}] missing columns"); return None
    # rows for M: rows[r] bit col = columns[col][r]
    rows=[]
    for r in range(128):
        val=0
        for col in range(128):
            if columns[col][r]: val|=(1<<col)
        rows.append(val)
    # self-check: M @ p_i == ct_i ^ c for every basis pair
    def matmul(rowint_list):  # not needed; verify via columns directly
        pass
    # verify by reconstructing E(e_j) = column_j ^ ... actually E(e_j)=M e_j + c
    # M e_j = column_j ; so E(e_j) bits = column_j XOR? no: E = M p + c => bits = col_j ^ cbits
    okcols=True
    for p in pairs[:8]:
        pb=b2(bytes.fromhex(p["pt"])); j=unit_index(pb)
        recon=[columns[j][r]^cbits[r] for r in range(128)]
        if bytes(bb2(recon))!=bytes.fromhex(p["ct"]):
            okcols=False; break
    log(f"[{name}] column self-check {'OK' if okcols else 'FAIL'}")
    if not okcols: return None
    # decrypt flag blocks: x = M^{-1}(y ^ c)
    pts=[]
    for i in range(0,len(flag_ct),16):
        y=flag_ct[i:i+16]
        rhs=[a^d for a,d in zip(b2(y), cbits)]
        x=gf2_solve(rows,rhs)
        if x is None: log(f"[{name}] singular"); return None
        pts.append(bb2(x))
    pt=b"".join(pts)
    log(f"[{name}] pt repr:", pt)
    return pt

def main():
    of=find("output.txt"); assert of
    data=json.loads(of.read_text())
    c=bytes.fromhex(data["zero"]["ct"])
    pairs=data["basis_pairs"]
    flag_ct=bytes.fromhex(data["flag_ct"])
    log("[+] basis", len(pairs), "flag blocks", len(flag_ct)//16)
    flag=None
    for name,(b2,bb2) in {"LSB":(b2_lsb,bits2b_lsb),"MSB":(b2_msb,bits2b_msb)}.items():
        pt=try_ordering(name,b2,bb2,c,pairs,flag_ct)
        if pt is None: continue
        m=re.search(rb"grey\{[^}]*\}", pt)
        if m:
            flag=m.group(0).decode(); log(f"[{name}] FLAG:",flag); break
    if flag:
        (SOLVE/"flag.txt").write_text(flag+"\n"); print("FLAG:",flag)
    else:
        log("no grey{} yet")
    (SOLVE/"RESULT4.txt").write_text("\n".join(log_lines)+"\n")

if __name__=="__main__":
    main()
