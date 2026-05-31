from rcon import Rcon
from botctl import Bot
def bulbs(r): return [1 if "passed" in r.cmd(f"execute if block 71 268 {67+i} minecraft:waxed_copper_bulb[lit=true]") else 0 for i in range(256)]
def settle_stable(r, chunk=200000, need=2, mx=2400000):
    total=0; prev=None; same=0
    while total<mx:
        r.cmd(f"tick sprint {chunk}"); total+=chunk
        cur=bulbs(r)
        if prev is not None and cur==prev: same+=1
        else: same=0
        prev=cur
        if same>=need: break
    return prev, total
def click(b,z): return b.cmd(f"click 69 267 {z}")
