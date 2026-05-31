import json
from pathlib import Path
from mca import iter_blocks
base=Path(__file__).resolve().parents[1]/"files/extracted/dist-lights-out"
want={"minecraft:lever","minecraft:redstone_lamp","minecraft:waxed_copper_bulb"}
out={"lever":[],"redstone_lamp":[],"waxed_copper_bulb":[]}
for name,props,x,y,z in iter_blocks(base/"region/r.0.0.mca", want=want):
    key=name.split(":")[1]
    out[key].append((x,y,z,props))
for k,v in out.items():
    print(k, len(v))
    xs=sorted(set(p[0] for p in v)); ys=sorted(set(p[1] for p in v)); zs=sorted(set(p[2] for p in v))
    print("  x range",min(xs),max(xs),"distinct",len(xs))
    print("  y range",min(ys),max(ys),"distinct",len(ys))
    print("  z range",min(zs),max(zs),"distinct",len(zs))
    # sample props
    from collections import Counter
    pc=Counter(tuple(sorted(p[3].items())) for p in v)
    for pp,c in pc.most_common(6):
        print("  props",dict(pp),"x",c)
json.dump(out, open(Path(__file__).parent/"blocks.json","w"))
print("saved blocks.json")
