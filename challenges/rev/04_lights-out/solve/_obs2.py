from harness import restart_frozen, step
r=restart_frozen(0)
def q(c): return r.cmd(c)
x,y,z=100,272,100
def clear():
    for dx in range(-3,4):
        for dz in range(-3,4):
            for dy in range(-2,3): q(f"setblock {x+dx} {y+dy} {z+dz} air")
    step(r,5)
def opow(): return "passed" in q(f"execute if block {x} {y} {z} minecraft:observer[powered=true]")
for face in ["west","east","up","down","north","south"]:
    clear()
    q(f"setblock {x} {y} {z} minecraft:observer[facing={face}]")
    step(r,5)
    res={}
    for nm,(dx,dy,dz) in {"W":(-1,0,0),"E":(1,0,0),"U":(0,1,0),"D":(0,-1,0),"N":(0,0,-1),"S":(0,0,1)}.items():
        # place concrete at neighbor, step1, check observer powered, then remove
        q(f"setblock {x+dx} {y+dy} {z+dz} minecraft:white_concrete")
        step(r,1); p1=opow()
        step(r,1); 
        q(f"setblock {x+dx} {y+dy} {z+dz} air"); step(r,2)
        res[nm]=p1
    fired=[k for k,v in res.items() if v]
    print(f"facing={face}: neighbor-change that FIRED observer -> {fired}")
r.close()
