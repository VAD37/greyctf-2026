import json, subprocess, time, os, signal
from pathlib import Path
from rcon import Rcon
SDIR=Path(__file__).parent/"server"
Z0=67
def restart(settle=200000):
    subprocess.run("pkill -9 -f 'server.jar nogui'",shell=True); time.sleep(2)
    subprocess.run("rm -rf world && cp -r world_pristine world",shell=True,cwd=SDIR)
    log=open(SDIR/"server.log","w")
    subprocess.Popen(["java","-Xmx6G","-Xms2G","-jar","server.jar","nogui"],cwd=SDIR,stdout=log,stderr=log)
    for _ in range(60):
        try:
            if "Done (" in (SDIR/"server.log").read_text(): break
        except: pass
        time.sleep(1)
    time.sleep(1)
    r=Rcon(timeout=600); r.cmd("tick unfreeze")
    if settle: r.cmd(f"tick sprint {settle}")
    return r
def bulbs(r):
    return [1 if "passed" in r.cmd(f"execute if block 71 268 {Z0+i} minecraft:waxed_copper_bulb[lit=true]") else 0 for i in range(256)]
def settle(r,n=30000): r.cmd(f"tick sprint {n}")

def restart_frozen(settle=400000):
    r=restart(settle=0); r.cmd("tick freeze")
    step(r, settle); return r
def step(r, n, chunk=50000):
    import time
    done=0
    while done<n:
        m=min(chunk,n-done); r.cmd(f"tick step {m}")
        for _ in range(200):
            q=r.cmd("tick query")
            if "stepping" not in q.lower(): break
            time.sleep(0.1)
        done+=m
