import json
from harness import restart_frozen, bulbs, step, Z0
r=restart_frozen(600000)
# verify b0 stable over +200k
b0=bulbs(r); step(r,200000); b0b=bulbs(r)
print("b0 lit",sum(b0),"stable over +200k? dprev",sum(a^b for a,b in zip(b0,b0b)))
b0=b0b
cols={}
prev=b0
for i in range(4):
    r.cmd(f"setblock 70 267 {Z0+i} minecraft:redstone_block")
    # settle, verify stable
    step(r,100000); s1=bulbs(r); step(r,80000); s2=bulbs(r)
    dset=sum(a^b for a,b in zip(s1,s2))
    col=[a^b for a,b in zip(prev,s2)]
    print(f"lane{i}: col weight {sum(col)} idx {[j for j,v in enumerate(col) if v]} settle_stable_d={dset}")
    cols[i]=col; prev=s2
r.close()
