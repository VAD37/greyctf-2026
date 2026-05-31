from harness import restart_frozen, bulbs, step, Z0
r=restart_frozen(800000)
def lamps():
    return [1 if "passed" in r.cmd(f"execute if block 71 267 {Z0+i} minecraft:redstone_lamp[lit=true]") else 0 for i in range(256)]
b0=bulbs(r); l0=lamps(); print("b0 bulbs lit",sum(b0),"lamps lit",sum(l0))
# toggle lever0 multiple edges
for edge in range(1,5):
    p="true" if edge%2==1 else "false"
    r.cmd(f"setblock 69 267 67 minecraft:lever[face=wall,facing=west,powered={p}]")
    step(r,300000)
    nb=bulbs(r); nl=lamps()
    print(f"edge{edge}(powered={p}): bulbs lit={sum(nb)} dB={sum(a^b for a,b in zip(b0,nb))} lamps lit={sum(nl)} dL={sum(a^b for a,b in zip(l0,nl))}")
r.close()
