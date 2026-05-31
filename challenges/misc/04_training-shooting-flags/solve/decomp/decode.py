#!/usr/bin/env python3
# Read sim dump (cyc + 10-bit output per line), try to reconstruct ASCII from each
# output column (serial) and from byte-grouping. Look for grey{ / printable runs.
import sys, re

lines=[l.split() for l in open(sys.argv[1]) if l and l[0].isdigit()]
cols=list(zip(*[l[1] for l in lines]))  # transpose: 10 strings, each = bitstream of one output over time
names="cib25 cib39 pa11 pb13 pa15 tx20 tx22 tx9 tx2c pc20".split()

def bits_to_ascii(bs, msb_first=True):
    out=[]
    for i in range(0,len(bs)-7,8):
        chunk=bs[i:i+8]
        if not msb_first: chunk=chunk[::-1]
        out.append(chr(int(chunk,2)))
    return ''.join(out)

for n,c in zip(names, cols):
    bs=''.join(c)
    for mf in (True,False):
        s=bits_to_ascii(bs,mf)
        # printable ratio
        pr=sum(32<=ord(ch)<127 for ch in s)/max(1,len(s))
        if 'grey' in s.lower() or 'TEA' in s or pr>0.85:
            print(f"[{n} msb={mf} pr={pr:.2f}] {s[:120]!r}")

# also concat all 10 per cycle as a byte? print first 64 cycles raw
print("\n# first 40 cycles raw (cib25 cib39 pa11 pb13 pa15 tx20 tx22 tx9 tx2c pc20):")
for l in lines[:40]:
    print(l[0], l[1])
