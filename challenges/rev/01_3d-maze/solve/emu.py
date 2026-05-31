#!/usr/bin/env python3
"""Faithful emulator of chal's maze/move logic. Finds a path start->F.
Player state x,y,z,lever,score. Moves: w:y-1 s:y+1 a:x-1 d:x+1 o:z-1 l:z+1.
idx(x,y,z) = (2z+1)*961 + (2y+1)*31 + (2x+1).
move passable iff maze[midpoint]==' '. On horizontal move, emit pool-derived byte.
Stepping on '.' sets lever=0x43; on 'F' = win.
"""
from pathlib import Path
from collections import deque

D = Path("/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/files/extracted/dist-3d-maze")
maze = D.joinpath("maze.txt").read_bytes()
pool = D.joinpath("pool.bin").read_bytes()

N = 31
def at(x, y, z):
    return maze[z*961 + y*31 + x]

def idx(x, y, z):
    return (2*z+1)*961 + (2*y+1)*31 + (2*x+1)

# move deltas: (dx,dy,dz) ; key
MOVES = {
    'w': (0, -1, 0),
    's': (0, 1, 0),
    'a': (-1, 0, 0),
    'd': (1, 0, 0),
    'o': (0, 0, -1),
    'l': (0, 0, 1),
}
# direction code for emit: w->0 s->1 a->2 d->3 ; o/l -> none
DIRCODE = {'w': 0, 's': 1, 'a': 2, 'd': 3}

def passable(x, y, z, dx, dy, dz):
    nx, ny, nz = x+dx, y+dy, z+dz
    if not (0 <= nx < 15 and 0 <= ny < 15 and 0 <= nz < 15):
        return False
    mid = (idx(x, y, z) + idx(nx, ny, nz)) // 2
    return maze[mid] == 0x20  # ' '

START = (7, 7, 7)
# find F
F = None
for z in range(15):
    for y in range(15):
        for x in range(15):
            if at(2*x+1, 2*y+1, 2*z+1) == ord('F'):
                F = (x, y, z)
print("F =", F, "START =", START)

# BFS shortest path (ignoring dots/lever, just reachability)
q = deque([START]); prev = {START: None}
while q:
    cur = q.popleft()
    if cur == F:
        break
    for k, (dx, dy, dz) in MOVES.items():
        if passable(*cur, dx, dy, dz):
            nb = (cur[0]+dx, cur[1]+dy, cur[2]+dz)
            if nb not in prev:
                prev[nb] = (cur, k); q.append(nb)
path = []
node = F
while prev[node] is not None:
    par, k = prev[node]; path.append(k); node = par
path.reverse()
print("BFS path len", len(path), "moves:", "".join(path))

def simulate(moves, verbose=False):
    x, y, z = START
    lever = 0x43  # initial? check: init sets player 7,7,7 lever='C'=0x43 score 0 (0x1cd8)
    lever = 0x43
    score = 0
    out = []
    for k in moves:
        dx, dy, dz = MOVES[k]
        if not passable(x, y, z, dx, dy, dz):
            continue  # blocked move ignored (no state change)
        # before idx for pool? emit uses current poolptr; poolptr advances per emit
        if k in DIRCODE:
            code = DIRCODE[k]
            poff = len(out) * 4  # poolptr advances 4 each emit
            b = (pool[poff + code] + lever) & 0xff
            score = (score + b) & 0xffffffff
            out.append(b)
            lever = 0
        x, y, z = x+dx, y+dy, z+dz
        c = at(2*x+1, 2*y+1, 2*z+1)
        if c == ord('F'):
            if verbose: print("REACHED F at move", k)
        elif c == ord('.'):
            lever = 0x43
    return out, score, (x, y, z)

out, score, pos = simulate(path, verbose=True)
print("emit bytes:", out)
print("as chars:", "".join(chr(b) if 32 <= b < 127 else '.' for b in out))
print("score", score, "final pos", pos)
