# Emit byte for the k-th HORIZONTAL move = (pool[4*k + code] + lever) & 0xff
#   code: w->0 s->1 a->2 d->3 ; lever = 0x43 if the cell entered by the PREVIOUS move was '.', else 0
#   (lever set to 0x43 on stepping on a dot, consumed+reset to 0 on next emit; init lever=0x43).
# We want the emitted stream to read grey{...}. Let's just see, for each step k and each code,
# what chars are reachable with lever 0 or 0x43, to confirm 'grey{' is even encodable early.
from pathlib import Path
D=Path("/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/files/extracted/dist-3d-maze")
pool=D.joinpath("pool.bin").read_bytes()
target="grey{"
print("pool len",len(pool))
for k in range(8):
    row=pool[4*k:4*k+4]
    opts={}
    for code in range(4):
        for lev in (0,0x43):
            v=(row[code]+lev)&0xff
            if 32<=v<127:
                opts.setdefault(chr(v),[]).append((code,lev))
    print("step",k,"pool",list(row),"-> chars",sorted(opts.keys()))
