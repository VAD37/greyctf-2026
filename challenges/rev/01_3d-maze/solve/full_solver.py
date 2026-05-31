#!/usr/bin/env python3
"""3d-maze full solver: maze emulator + win()-VM port + path search + verify.
Run: uv run python solve/full_solver.py
"""
import os, pty, time, select, re, sys
from pathlib import Path
from collections import deque

D = Path(__file__).resolve().parent.parent / "files/extracted/dist-3d-maze"
maze = D.joinpath("maze.txt").read_bytes()
pool = list(D.joinpath("pool.bin").read_bytes())
vm   = list(D.joinpath("vm.bin").read_bytes())

def at(x,y,z): return maze[z*961+y*31+x]
def idx(x,y,z): return (2*z+1)*961+(2*y+1)*31+(2*x+1)
MOVES={'w':(0,-1,0),'s':(0,1,0),'a':(-1,0,0),'d':(1,0,0),'o':(0,0,-1),'l':(0,0,1)}
CODE={'w':0,'s':1,'a':2,'d':3}
def passable(x,y,z,dx,dy,dz):
    nx,ny,nz=x+dx,y+dy,z+dz
    if not(0<=nx<15 and 0<=ny<15 and 0<=nz<15): return False
    return maze[(idx(x,y,z)+idx(nx,ny,nz))//2]==0x20
F=None
for z in range(15):
 for y in range(15):
  for x in range(15):
   if at(2*x+1,2*y+1,2*z+1)==ord('F'): F=(x,y,z)
START=(7,7,7)

# ---- win() VM port. Memory: code=vm[0x98:], data stack array, out=emit bytes. ----
# DATA grows UP from base; DATA points at next free? trace: 'C' does DATA+=1 then *DATA=imm.
#   So DATA points at TOP element; push = (++DATA; *DATA=v). pop('g') = DATA-=1. putchar pops.
# op35/36/37 = stack shuffles (verified by arity in disasm). 'L' indexed load vm[idx].
# 0x05/06/07 read OUT bytes.
def run_vm(emit, maxsteps=200000):
    code = bytes(vm)
    cp = 0x98
    data = [0]*4096
    dp = 0          # top index; data[dp] is top
    out_bytes = list(emit)
    op_i = 0        # OUT read pointer
    printed = []
    steps = 0
    def push(v):
        nonlocal dp
        dp += 1; data[dp] = v & 0xff
    def pop():
        nonlocal dp
        v = data[dp]; dp -= 1; return v
    while steps < maxsteps:
        steps += 1
        if cp >= len(code): break
        b = code[cp]; cp += 1
        op = (b-5)&0xff
        if b == 0x43:        # C: push immediate (next code byte)
            push(code[cp]); cp += 1
        elif b == 0x36:      # op36: push imm twice? disasm: reads 1 imm to [-3], pushes it twice
            v = code[cp]; cp += 1
            push(v); push(v)
        elif b == 0x37:      # op37: reads 3? push pattern. Treat as push imm 1 byte then dup?
            v = code[cp]; cp += 1
            push(v)
        elif b == 0x35:      # op35: pop2 push back swapped (dup/swap) -> approximate as dup
            a = pop(); push(a); push(a)
        elif b == 0x67:      # g: pop
            pop()
        elif b == 0x20:      # putchar: pop & print
            printed.append(pop())
        elif b == 0x4c:      # L: idx load vm[idx] from 2 popped bytes (lo|hi<<8)
            lo = pop(); hi = pop(); a = (hi<<8)|lo
            push(code[a] if a < len(code) else 0)
        elif b == 0x53:      # S: store
            lo = pop(); hi = pop(); val = pop()
            a = (hi<<8)|lo
        elif b == 0x2b: x=pop(); y=pop(); push(y+x)
        elif b == 0x2d: x=pop(); y=pop(); push(y-x)
        elif b == 0x2a: x=pop(); y=pop(); push(y*x)
        elif b == 0x26: x=pop(); y=pop(); push(y&x)
        elif b == 0x5e: x=pop(); y=pop(); push(y^x)
        elif b == 0x05:      # read OUT byte -> push
            v = out_bytes[op_i] if op_i < len(out_bytes) else 0; op_i += 1
            push(v)
        elif b == 0x06:      # read OUT, cond
            v = out_bytes[op_i] if op_i < len(out_bytes) else 0; op_i += 1
            push(v)
        elif b == 0x07:
            v = out_bytes[op_i] if op_i < len(out_bytes) else 0; op_i += 1
            push(v)
        else:
            break   # exit
    return bytes(printed), steps

# ---- emulate a key path -> emit bytes (and whether reaches F) ----
def emit_for_path(keys):
    x,y,z=START; lever=0x43; step=0; out=[]
    for k in keys:
        dx,dy,dz=MOVES[k]
        if not passable(x,y,z,dx,dy,dz): continue
        if k in CODE:
            b=(pool[4*step+CODE[k]]+lever)&0xff
            out.append(b); step+=1; lever=0
        x,y,z=x+dx,y+dy,z+dz
        c=at(2*x+1,2*y+1,2*z+1)
        if c==ord('.'): lever=0x43
    return out,(x,y,z)

# ---- BFS path then run VM on its emit ----
def bfs():
    q=deque([START]); prev={START:None}
    while q:
        c=q.popleft()
        if c==F: break
        for k,(dx,dy,dz) in MOVES.items():
            if passable(*c,dx,dy,dz):
                n=(c[0]+dx,c[1]+dy,c[2]+dz)
                if n not in prev: prev[n]=(c,k); q.append(n)
    path=[]; n=F
    while prev[n]: par,k=prev[n]; path.append(k); n=par
    return "".join(reversed(path))

if __name__=="__main__":
    p=bfs()
    em,pos=emit_for_path(p)
    print("BFS path",p,"emit",em)
    out,steps=run_vm(em)
    print("VM out (%d steps):"%steps, out, "->", out.decode("latin1","replace"))
    print("flag-match:", re.findall(rb"grey\{[a-z_]+\}", out))
