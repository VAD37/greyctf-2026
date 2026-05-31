import json
from harness import restart, bulbs, settle, Z0
r=restart()
b0=bulbs(r); print("b0 lit",sum(b0)); json.dump(b0,open("b0.json","w"))
def pa(i): r.cmd(f"setblock 71 267 {Z0+i} air")
def pl(i): r.cmd(f"setblock 71 267 {Z0+i} minecraft:redstone_lamp[lit=false]")
pa(0); settle(r); R1=bulbs(r); c1=[a^b for a,b in zip(b0,R1)]
print("lamp->air changed",sum(c1),[i for i,v in enumerate(c1) if v])
pl(0); settle(r); R2=bulbs(r); print("air->lamp diff_b0",sum(a^b for a,b in zip(b0,R2)))
pa(0); settle(r); R3=bulbs(r); c3=[a^b for a,b in zip(b0,R3)]
print("again changed",sum(c3),"det?",c1==c3)
r.close()
