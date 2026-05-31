import json
from harness import restart_frozen, bulbs, step
r=restart_frozen(400000)
b0=bulbs(r); print("b0 lit",sum(b0)); json.dump(b0,open("b0.json","w"))
# lane0 input: lamp->air, watch settle in 50k chunks
r.cmd("setblock 71 267 67 air")
prev=b0
for k in range(8):
    step(r,50000); nb=bulbs(r); d=sum(a^b for a,b in zip(prev,nb))
    print(f"+{(k+1)*50000}: lit={sum(nb)} dprev={d} dvsb0={sum(a^b for a,b in zip(b0,nb))}")
    prev=nb
col0=[a^b for a,b in zip(b0,prev)]
print("col0 weight",sum(col0),"idx",[i for i,v in enumerate(col0) if v])
json.dump(col0,open("col0_run1.json","w"))
r.close()
