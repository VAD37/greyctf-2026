import json
from harness import restart, bulbs
r=restart(settle=0)
def S(n=200000): r.cmd(f"tick sprint {n}")
S(200000); b0=bulbs(r); print("b0 lit",sum(b0))
def lamp_air(i): r.cmd(f"setblock 71 267 {67+i} air")
def lamp_on(i): r.cmd(f"setblock 71 267 {67+i} minecraft:redstone_lamp[lit=false]")
# A: lamp0->air
lamp_air(0); S(); A1=bulbs(r); c=[a^b for a,b in zip(b0,A1)]
print("lane0 lamp->air: changed",sum(c),"idx",[i for i,v in enumerate(c) if v])
# revert
lamp_on(0); S(); R=bulbs(r); print("revert air->lamp: diff vs b0",sum(a^b for a,b in zip(b0,R)))
# repeat
lamp_air(0); S(); A2=bulbs(r); c2=[a^b for a,b in zip(b0,A2)]
print("lane0 again: changed",sum(c2),"deterministic?",A1==A2)
lamp_on(0); S(); R2=bulbs(r); print("revert2: diff vs b0",sum(a^b for a,b in zip(b0,R2)))
json.dump(b0,open("b0.json","w"))
r.close()
