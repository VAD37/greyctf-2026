#!/usr/bin/env python3
"""
Self-contained AE-no-S solver. Writes everything it learns to RESULT.txt so the
agent can read results even if the live stdout channel is flaky.

Strategy ladder (auto):
  A) output.txt provides zero_ct (=c) and 128 basis pairs (col i = ct(e_i)^c)
     and flag_ct.  -> build M from those, invert, decrypt.  (no challenge.py needed)
  B) else import challenge.py, find a 16->16 encrypt for the fixed key, probe
     e_i to build M and c, then invert.
  C) else reconstruct AES-without-SubBytes from scratch (ShiftRows + MixColumns
     + AddRoundKey + key schedule with identity SubWord) as an affine map; but
     that needs the key -> only if key is in output.txt.

All of A/B/C reduce to: y = M x + c over GF(2)^128; x = M^{-1}(y ^ c).
We do GF(2) Gaussian elimination in pure python (no galois dep needed).
"""
import sys, os, re, importlib.util
from pathlib import Path

CH = Path("/media/vad/Work2/hackathon/greyctf-2026/challenges/ezpz/01_ae-no-s")
SOLVE = CH / "solve"
RESULT = SOLVE / "RESULT.txt"
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(s)

def find(name):
    for base in [CH/"files"/"extracted", CH/"files", CH]:
        if base.exists():
            for f in base.rglob(name):
                return f
    return None

# ---------- bit helpers (bit 0 = LSB of byte 0) ----------
def b2bits(b):
    out = []
    for byte in b:
        for i in range(8):
            out.append((byte >> i) & 1)
    return out
def bits2b(bits):
    out = bytearray(len(bits)//8)
    for j,bit in enumerate(bits):
        if bit: out[j//8] |= (1<<(j%8))
    return bytes(out)

# also try MSB-first ordering as fallback
def b2bits_msb(b):
    out = []
    for byte in b:
        for i in range(7,-1,-1):
            out.append((byte>>i)&1)
    return out
def bits2b_msb(bits):
    out = bytearray(len(bits)//8)
    for j,bit in enumerate(bits):
        if bit: out[j//8] |= (1<<(7-(j%8)))
    return bytes(out)

# ---------- GF(2) linear algebra via bitmask rows ----------
def invert_and_apply(M_cols, c, y, b2bits_f, bits2b_f, n=128):
    """M_cols: list of n column bit-lists. Solve M x = (y^c). Return x bytes.
    We build augmented [M | I], reduce, get Minv, then x = Minv @ (y^c)."""
    # Represent each ROW as integer bitmask over columns 0..n-1, plus rhs bits.
    # Build matrix rows from columns.
    # M[r][col] = M_cols[col][r]
    rows = []
    for r in range(n):
        val = 0
        for col in range(n):
            if M_cols[col][r]:
                val |= (1<<col)
        rows.append(val)
    yb = b2bits_f(y); cb = b2bits_f(c)
    rhs = [(yb[r]^cb[r]) for r in range(n)]
    # Gaussian elim to solve rows . x = rhs
    rowi = list(rows)
    where = [-1]*n
    pr = 0
    for col in range(n):
        sel = -1
        for r in range(pr, n):
            if (rowi[r]>>col)&1:
                sel = r; break
        if sel == -1:
            continue
        rowi[pr],rowi[sel] = rowi[sel],rowi[pr]
        rhs[pr],rhs[sel] = rhs[sel],rhs[pr]
        for r in range(n):
            if r!=pr and ((rowi[r]>>col)&1):
                rowi[r]^=rowi[pr]
                rhs[r]^=rhs[pr]
        where[col]=pr
        pr+=1
    if pr != n:
        return None  # singular for this bit ordering
    x = [0]*n
    for col in range(n):
        x[col] = rhs[where[col]]
    return bits2b_f(x)

# ---------- Strategy A: parse output.txt ----------
def parse_output():
    of = find("output.txt")
    if not of:
        log("[A] output.txt not found"); return None
    txt = of.read_text()
    log("[A] output.txt bytes:", len(txt))
    log("[A] output.txt head:\n" + txt[:600])
    # gather hex tokens of len 32 (16-byte blocks)
    hexes = re.findall(r"\b[0-9a-fA-F]{32}\b", txt)
    log("[A] found", len(hexes), "32-hex tokens")
    return txt, hexes

# ---------- Strategy B: import challenge.py ----------
def import_encrypt():
    cf = find("challenge.py")
    if not cf:
        log("[B] challenge.py not found"); return None
    src = cf.read_text()
    log("[B] challenge.py bytes:", len(src))
    log("[B] challenge.py FULL SOURCE:\n" + src)
    safe = re.sub(r"^if\s+__name__\s*==\s*['\"]__main__['\"]\s*:.*$",
                  "if False:", src, flags=re.M|re.S)
    g = {"__name__":"_imp_"}
    try:
        exec(compile(safe, str(cf), "exec"), g)
    except Exception as e:
        log("[B] exec failed:", repr(e)); return None
    log("[B] module globals:", [k for k in g if not k.startswith("__")])
    return g

def main():
    txt_hexes = parse_output()
    g = import_encrypt()

    # Persist the raw sources to RESULT first thing.
    RESULT.write_text("\n".join(LOG)+"\n")

    # Try strategy A: zero_ct + 128 basis + flag from output.txt
    flag_found = None
    if txt_hexes:
        txt, hexes = txt_hexes
        # Heuristic: many CTFs store as labelled lines. Try to find structure.
        # Common: first hex = zero ct, next 128 = basis cts, last few = flag cts.
        if len(hexes) >= 1+128+1:
            zero_ct = bytes.fromhex(hexes[0])
            basis = [bytes.fromhex(h) for h in hexes[1:1+128]]
            flag_cts = [bytes.fromhex(h) for h in hexes[1+128:]]
            log("[A] structured: zero_ct + 128 basis +", len(flag_cts), "flag blocks")
            for b2,bb2 in ((b2bits,bits2b),(b2bits_msb,bits2b_msb)):
                cbits = b2(zero_ct)
                M_cols = [[a^c for a,c in zip(b2(basis[i]), cbits)] for i in range(128)]
                pts=[]
                ok=True
                for fc in flag_cts:
                    x = invert_and_apply(M_cols, zero_ct, fc, b2, bb2)
                    if x is None: ok=False; break
                    pts.append(x)
                if ok:
                    pt=b"".join(pts)
                    log("[A] ordering", ("LSB" if b2 is b2bits else "MSB"), "pt:", pt)
                    m=re.search(rb"grey\{[^}]*\}", pt)
                    if m: flag_found=m.group(0).decode(); break

    # Strategy B: probe imported encrypt
    if not flag_found and g:
        enc=None; encname=None
        for name in ("encrypt","encrypt_block","aes_no_s","enc","cipher","E"):
            fn=g.get(name)
            if callable(fn):
                try:
                    r=fn(b"\x00"*16)
                    if isinstance(r,(bytes,bytearray)) and len(r)==16:
                        enc=lambda b: bytes(fn(b)); encname=name; break
                except Exception as e:
                    log("[B] try",name,"failed:",repr(e))
        # also handle an object with .encrypt
        if enc is None:
            for k,v in g.items():
                if hasattr(v,"encrypt"):
                    try:
                        r=v.encrypt(b"\x00"*16)
                        if isinstance(r,(bytes,bytearray)) and len(r)==16:
                            enc=lambda b: bytes(v.encrypt(b)); encname=k+".encrypt"; break
                    except Exception as e:
                        log("[B] obj",k,"failed:",repr(e))
        if enc:
            log("[B] using", encname)
            c=enc(b"\x00"*16)
            for b2,bb2 in ((b2bits,bits2b),(b2bits_msb,bits2b_msb)):
                cbits=b2(c)
                M_cols=[]
                for i in range(128):
                    x=bytearray(16); x[i//8]|=(1<<(i%8))
                    M_cols.append([a^d for a,d in zip(b2(enc(bytes(x))),cbits)])
                # need flag ciphertext from output.txt
                if txt_hexes:
                    txt,hexes=txt_hexes
                    # the flag ct is whatever blocks aren't the probe set; take all and test
                    for fc_hex in hexes:
                        pass
                    # better: try every contiguous candidate set later; first just decrypt all hexes
                    allpt=[]
                    for h in hexes:
                        x=invert_and_apply(M_cols,c,bytes.fromhex(h),b2,bb2)
                        if x: allpt.append((h,x))
                    blob=b"".join(p for _,p in allpt)
                    m=re.search(rb"grey\{[^}]*\}", blob)
                    if m: flag_found=m.group(0).decode(); log("[B] flag in decrypted blob"); break
                    # log a few decryptions for inspection
                    for h,p in allpt[:6]:
                        log("[B] dec", h, "->", p)
        else:
            log("[B] no 16->16 encrypt entry found")

    RESULT.write_text("\n".join(LOG)+"\n")
    if flag_found:
        (SOLVE/"flag.txt").write_text(flag_found+"\n")
        log("FLAG_FOUND:", flag_found)
        RESULT.write_text("\n".join(LOG)+"\n")
        print("FLAG:", flag_found)
    else:
        log("NO FLAG YET - inspect RESULT.txt for sources/structure")
        RESULT.write_text("\n".join(LOG)+"\n")

if __name__=="__main__":
    main()
