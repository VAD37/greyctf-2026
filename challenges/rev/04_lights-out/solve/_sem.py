from harness import restart_frozen, step
r=restart_frozen(0)  # frozen at load (structure intact, no settle needed)
def q(c): return r.cmd(c)
def opw(): return 1 if "passed" in q("execute if block 72 267 67 minecraft:observer[powered=true]") else 0
# also a known reference: build a fresh observer facing a lamp and verify it fires
# First: real machine - change lamp(71,267,67) to concrete (block change on Ow's west face)
print("Ow powered before:",opw())
q("setblock 71 267 67 minecraft:white_concrete")
for t in range(6):
    step(r,1); print(f"after lamp->concrete step{t}: Ow_powered={opw()}")
# restore
q("setblock 71 267 67 minecraft:redstone_lamp[lit=false]")
step(r,4)
# CONTROL: fresh observer facing=north watching a block we toggle, confirm detection works
bx,by,bz=120,272,120
for dx in range(-2,3):
  for dz in range(-2,3): q(f"setblock {bx+dx} {by+dz-dz} {bz+dz} air")
q(f"setblock {bx} {by} {bz} minecraft:observer[facing=north]")  # observes north=-z (bz-1)
q(f"setblock {bx} {by} {bz-1} minecraft:white_concrete")  # block on north face
step(r,3)
def cpow(): return 1 if "passed" in q(f"execute if block {bx} {by} {bz} minecraft:observer[powered=true]") else 0
print("control obs powered (stable):",cpow())
q(f"setblock {bx} {by} {bz-1} minecraft:air")  # change north-face block
for t in range(5):
    step(r,1); print(f"control after change step{t}: powered={cpow()}")
r.close()
