from harness import restart_frozen, step
r=restart_frozen(0)  # frozen at load, no settle needed for empty-air test
def q(c): return r.cmd(c)
P=(100,272,100); x,y,z=P
# clear area
for dx in range(-3,4):
  for dz in range(-3,4):
    for dy in range(-1,2):
      q(f"setblock {x+dx} {y+dy} {z+dz} air")
step(r,5)
# observer facing west at P
q(f"setblock {x} {y} {z} minecraft:observer[facing=west]")
# lamps on east(back?) and west(front?) at distance 1
q(f"setblock {x+1} {y} {z} minecraft:redstone_lamp[lit=false]")  # east neighbor
q(f"setblock {x-1} {y} {z} air")  # west neighbor kept air for now
step(r,5)
def lit(lx): return "passed" in q(f"execute if block {lx} {y} {z} minecraft:redstone_lamp[lit=true]")
print("before trigger: east-lamp lit?",lit(x+1))
# trigger by placing block on WEST side (front if facing=west = observing west)
q(f"setblock {x-1} {y} {z} minecraft:white_concrete")
# catch pulse over a few steps
for t in range(6):
    step(r,1); print(f"step{t}: east-lamp({x+1}) lit?",lit(x+1))
r.close()
