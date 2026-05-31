from harness import restart_frozen, step
r=restart_frozen(400000)
def q(c): return r.cmd(c)
def op(x,y,z): return 1 if "passed" in q(f"execute if block {x} {y} {z} minecraft:observer[powered=true]") else 0
def lamplit(z): return 1 if "passed" in q(f"execute if block 71 267 {z} minecraft:redstone_lamp[lit=true]") else 0
Z=67
col=[(72,267),(72,266),(72,265),(72,264),(72,263),(72,262)]
print("b0 settled. lamp0 lit?",lamplit(Z))
print("col powered before:",[op(x,y,Z) for x,y in col])
q(f"setblock 70 267 {Z} minecraft:redstone_block")
for t in range(10):
    step(r,1)
    print(f"step{t}: lamp0={lamplit(Z)} col={[op(x,y,Z) for x,y in col]}")
# also check the y268 east-row observers near x72-76
print("y268 row pow:",[op(x,268,Z) for x in range(72,80)])
r.close()
