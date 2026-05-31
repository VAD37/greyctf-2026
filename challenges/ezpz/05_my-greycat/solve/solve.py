#!/usr/bin/env python3
"""
my-greycat (ezpz/rev) solver.

main (objdump @0x1209), for i in [0,n):
    x = 1
    for j in [0, (unsigned)ds[i]):        # cmp+jb -> UNSIGNED loop count
        x = (x * cs[i]) ; x = REDUCE(x)   # REDUCE = the 0xff00ff01/shr pseudo-"mod 255"
    data.bin[i] = x & 0xff
where:
    cs = int32[] @ vaddr 0x4020
    ds = int32[] @ vaddr 0x186f3e0   (used as UNSIGNED exponent)
    n  = u32      @ vaddr 0x30da784
.data: vaddr 0x4000 -> file off 0x3000, so file_off = vaddr - 0x1000.

IMPORTANT: REDUCE is NOT a true `% 255`. The compiler's magic-number division
(imul 0xff00ff01; shr 32; ...) only matches `x%255` for small x; for x>=255 it
under-divides (e.g. REDUCE(255)=255, REDUCE(256)=256, REDUCE(257)=0). So we must
emulate REDUCE exactly. Because x stays in 0..256 (257 states), each per-c
trajectory is eventually periodic with a short cycle -> we resolve any exponent d
(up to ~4e9) in O(cycle) via tail+cycle indexing.
"""
import struct, os, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "..", "files", "extracted", "dist-my_greycat", "main")
OUT = os.path.join(HERE, "data.bin")

VA_CS = 0x4020
VA_DS = 0x186f3e0
VA_N  = 0x30da784
DELTA = 0x1000


def fo(v):
    return v - DELTA


def reduce_(x):
    """Exact emulation of the asm pseudo-mod-255 at 0x12aa..0x12cd."""
    x &= 0xffffffff
    rax = (0xff00ff01 * x) & 0xffffffffffffffff
    eax = rax >> 32
    ecx = (eax & 0xffffffff) >> 8
    eax2 = ((ecx << 8) + ecx) & 0xffffffff      # ecx*257
    return (x - eax2) & 0xffffffff


def build_table(c):
    """Return function k -> value after iterating x=reduce(x*c), x0=1, k times.
    Implemented as a precomputed trajectory with cycle, indexed by k."""
    traj = []          # traj[k] = x after k steps
    pos = {}           # value -> first step index it appeared
    x = 1
    while x not in pos:
        pos[x] = len(traj)
        traj.append(x)
        x = reduce_((x * c) & 0xffffffff)
    cycle_start = pos[x]
    cycle_len = len(traj) - cycle_start

    def at(k):
        if k < len(traj):
            return traj[k]
        return traj[cycle_start + (k - cycle_start) % cycle_len]

    return at


def main():
    with open(BIN, "rb") as f:
        blob = f.read()

    n = struct.unpack_from("<I", blob, fo(VA_N))[0]
    cs_off, ds_off = fo(VA_CS), fo(VA_DS)
    assert cs_off + 4 * n <= len(blob)
    assert ds_off + 4 * n <= len(blob)
    print(f"[*] n = {n}")

    cs = struct.unpack_from(f"<{n}i", blob, cs_off)
    ds = struct.unpack_from(f"<{n}I", blob, ds_off)   # unsigned exponents

    tables = {c: build_table(c) for c in range(256)}

    out = bytearray(n)
    for i in range(n):
        out[i] = tables[cs[i] & 0xff](ds[i]) & 0xff

    with open(OUT, "wb") as f:
        f.write(out)
    print(f"[*] wrote {OUT} ({len(out)} bytes)")

    try:
        ft = subprocess.run(["file", OUT], capture_output=True, text=True).stdout.strip()
        print("[*] file:", ft)
    except Exception as e:
        print("[!] file failed:", e)
    print("[*] head hex:", out[:32].hex())

    found = False
    for m in re.finditer(rb"grey\{[^}]{0,300}\}", out):
        print("[FLAG]", m.group().decode("latin1")); found = True
    if not found:
        try:
            st = subprocess.run(["strings", "-n", "5", OUT], capture_output=True, text=True).stdout
            for line in st.splitlines():
                if "grey{" in line.lower():
                    print("[FLAG-strings]", line)
        except Exception:
            pass


if __name__ == "__main__":
    main()
