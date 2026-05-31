import json
from harness import restart_frozen, bulbs, step
r=restart_frozen(400000)
b0=bulbs(r); print("b0 lit",sum(b0))
def lampon(z): return "passed" in r.cmd(f"execute if block 71 267 {z} minecraft:redstone_lamp[lit=true]")
print("lamp0 lit at b0?",lampon(67))
# redstone_block at 70 (power concrete spot) -> should light lamp71
r.cmd("setblock 70 267 67 minecraft:redstone_block")
step(r,5000); print("after 5k: lamp0 lit?",lampon(67))
prev=b0
for k in range(8):
    step(r,50000); nb=bulbs(r); print(f"+{(k+1)*50000}: lit={sum(nb)} dvsb0={sum(a^b for a,b in zip(b0,nb))}")
    prev=nb
col=[a^b for a,b in zip(b0,prev)]
print("redstone_block@70 col weight",sum(col),"idx",[i for i,v in enumerate(col) if v])
# revert and re-settle, check returns to b0
r.cmd("setblock 70 267 67 minecraft:white_concrete")
step(r,400000); back=bulbs(r); print("revert diff vs b0",sum(a^b for a,b in zip(b0,back)))
r.close()
