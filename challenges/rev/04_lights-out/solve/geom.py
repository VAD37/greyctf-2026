from pathlib import Path
from collections import Counter
from mca import iter_blocks
base=Path(__file__).resolve().parents[1]/"files/extracted/dist-lights-out"
want={"minecraft:observer","minecraft:dropper","minecraft:white_concrete"}
xh=Counter(); yh=Counter(); zh=Counter()
ofacing=Counter(); dfacing=Counter()
minx=miny=minz=10**9; maxx=maxy=maxz=-10**9
n=0
for name,props,x,y,z in iter_blocks(base/"region/r.0.0.mca", want=want):
    n+=1
    xh[x]+=1; yh[y]+=1; zh[z]+=1
    minx=min(minx,x);maxx=max(maxx,x);miny=min(miny,y);maxy=max(maxy,y);minz=min(minz,z);maxz=max(maxz,z)
    if name.endswith("observer"): ofacing[props.get('facing')]+=1
    if name.endswith("dropper"): dfacing[props.get('facing')]+=1
print("total logic blocks",n)
print("bbox x",minx,maxx," y",miny,maxy," z",minz,maxz)
print("observer facing",dict(ofacing))
print("dropper facing",dict(dfacing))
print("y-levels (sorted, count):")
for y in sorted(yh): print(" y",y,yh[y])
