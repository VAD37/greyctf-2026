import json
from harness import restart, bulbs, settle
r=restart(settle=100000)
prev=bulbs(r); base=prev; print("settled lit",sum(prev))
changes=[]
for t in range(1,61):
    r.cmd("tick sprint 1"); nb=bulbs(r); d=sum(a^b for a,b in zip(prev,nb))
    if d: changes.append((t,d,sum(nb)))
    prev=nb
print("ticks with change (vs prev):",changes[:40])
print("total distinct from base after 60t:",sum(a^b for a,b in zip(base,prev)))
# bigger: sprint 1000 x5 read
for k in range(5):
    r.cmd("tick sprint 1000"); nb=bulbs(r); print(f"+{(k+1)*1000}t lit={sum(nb)} dvsbase={sum(a^b for a,b in zip(base,nb))}")
r.close()
