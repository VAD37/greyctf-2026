import json
from harness import restart, bulbs
r=restart(settle=0)
prev=bulbs(r); print("fresh load lit",sum(prev))
import time
total=0
stable=0
for k in range(40):
    r.cmd("tick sprint 50000"); total+=50000
    nb=bulbs(r); d=sum(a^b for a,b in zip(prev,nb))
    print(f"t={total}: lit={sum(nb)} dprev={d}",flush=True)
    if d==0: stable+=1
    else: stable=0
    prev=nb
    if stable>=4: print("STABLE confirmed at",total); break
json.dump(prev,open("b0.json","w"))
print("final lit",sum(prev))
r.close()
