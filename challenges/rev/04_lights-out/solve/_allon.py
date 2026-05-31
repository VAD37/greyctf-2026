from harness import restart_frozen, bulbs, step, Z0
r=restart_frozen(500000)
b0=bulbs(r); print("b0 lit",sum(b0))
# all inputs high
for i in range(256): r.cmd(f"setblock 70 267 {Z0+i} minecraft:redstone_block")
prev=b0
for k in range(10):
    step(r,80000); nb=bulbs(r); print(f"+{(k+1)*80000}: lit={sum(nb)} dvsb0={sum(a^b for a,b in zip(b0,nb))} dprev={sum(a^b for a,b in zip(prev,nb))}")
    prev=nb
r.close()
