import json, sys
from harness import restart, bulbs
def run():
    r=restart(settle=0)
    r.cmd("tick freeze")
    vals=[]
    for k in range(8):
        r.cmd("tick step 50000")
        # step is async? wait by querying until done
        import time
        for _ in range(120):
            q=r.cmd("tick query")
            if "frozen" in q.lower() or "stepping" not in q.lower(): break
            time.sleep(0.2)
        nb=bulbs(r); vals.append(sum(nb))
    r.close(); return vals, nb
v1,b1=run()
print("run1 lit progression:",v1)
v2,b2=run()
print("run2 lit progression:",v2)
print("final identical?",b1==b2,"diff",sum(a^b for a,b in zip(b1,b2)))
json.dump(b1,open("b0.json","w"))
