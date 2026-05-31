#!/usr/bin/env python3
"""Search maze paths whose emitted byte-stream matches /grey\{[a-z_]+\}/.
emit on horizontal move k = (pool[poolptr+code] + lever)&0xff ; poolptr advances +4 per emit (=step k).
lever: init 0x43; consumed->0 on each emit; set 0x43 when entering a '.' cell.
Reach F to trigger win() which prints the emitted stream verbatim (PUTC===EMIT confirmed).
We DFS over (x,y,z, step, lever, entered_dot_pending) pruning so emitted prefix stays in [a-z_{] + 'grey{' prefix.
"""
from pathlib import Path
from collections import deque
import sys

D=Path("/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/files/extracted/dist-3d-maze")
maze=D.joinpath("maze.txt").read_bytes()
pool=list(D.joinpath("pool.bin").read_bytes())
def at(x,y,z): return maze[z*961+y*31+x]
def idx(x,y,z): return (2*z+1)*961+(2*y+1)*31+(2*x+1)
MOVES={'w':(0,-1,0),'s':(0,1,0),'a':(-1,0,0),'d':(1,0,0),'o':(0,0,-1),'l':(0,0,1)}
CODE={'w':0,'s':1,'a':2,'d':3}
def passable(x,y,z,dx,dy,dz):
    nx,ny,nz=x+dx,y+dy,z+dz
    if not(0<=nx<15 and 0<=ny<15 and 0<=nz<15): return False
    return maze[(idx(x,y,z)+idx(nx,ny,nz))//2]==0x20
# F
F=None
for z in range(15):
 for y in range(15):
  for x in range(15):
    if at(2*x+1,2*y+1,2*z+1)==ord('F'): F=(x,y,z)
START=(7,7,7)
FLAGCHARS=set(range(ord('a'),ord('z')+1))|{ord('_'),ord('{'),ord('}')}
# valid flag must be grey{...}. We require emitted stream startswith 'grey{' and is all [a-z_] then '}'.
# DFS with depth limit on # of emits (flag length). Allow z-moves freely (no emit) but bound total moves.
import sys
sys.setrecursionlimit(100000)
best=[]
# BFS over states to find ANY path to F; track emitted string; prune invalid prefixes.
# state: (x,y,z,step,lever,emitted_str). Too big -> restrict: emitted must be valid prefix of grey{[a-z_]+}
def valid_prefix(s):
    pre="grey{"
    for i,c in enumerate(s):
        if i<len(pre):
            if c!=pre[i]: return False
        else:
            if not (c=='_' or 'a'<=c<='z' or c=='}'): return False
            if '}' in s[:-1]: return False
    return True
from collections import deque
# We do BFS but state includes emitted string (variable). Use visited on (x,y,z,step,lever,len(emitted)) won't dedup content.
# Practical: emitted content is determined by the SEQUENCE of (code,lever) which is determined by path; but many paths.
# Limit: DFS up to N emits; z-moves limited to avoid infinite. Cap path length.
sols=[]
import collections
def dfs(x,y,z,step,lever,emitted,depth,visit):
    if emitted and not valid_prefix(emitted): return
    if (x,y,z)==F:
        if emitted.startswith("grey{") and emitted.endswith("}") and len(emitted)>6:
            sols.append(emitted)
        return
    if depth>60: return
    key=(x,y,z,step,lever)
    if key in visit and visit[key]<=depth: return
    visit[key]=depth
    for k,(dx,dy,dz) in MOVES.items():
        if not passable(x,y,z,dx,dy,dz): continue
        nx,ny,nz=x+dx,y+dy,z+dz
        ne=emitted; nstep=step; nlev=lever
        if k in CODE:
            b=(pool[4*step+CODE[k]]+lever)&0xff
            ne=emitted+(chr(b) if 32<=b<127 else '\x00')
            nstep=step+1; nlev=0
        c=at(2*nx+1,2*ny+1,2*nz+1)
        if c==ord('.'): nlev=0x43
        dfs(nx,ny,nz,nstep,nlev,ne,depth+1,visit)
dfs(*START,0,0x43,"",0,{})
print("solutions found:",len(sols))
for s in sols[:5]: print(repr(s))
Path("/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/solve/search_sols.txt").write_text("\n".join(sols))
