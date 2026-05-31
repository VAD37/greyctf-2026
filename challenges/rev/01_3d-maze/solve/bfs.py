#!/usr/bin/env python3
"""Parse 31^3 maze, BFS from start cell to F. Moves map to keys.
Index: idx(x,y,z) = (2z+1)*961 + (2y+1)*31 + (2x+1).  961=31^2, 31.
Move through midpoint cell which must be ' ' (space) to be passable.
Key deltas (cell-space): w:Y-1 s:Y+1 o:X-1 l:X+1 a:Z-1 d:Z+1
"""
from pathlib import Path
from collections import deque

D = Path(__file__).resolve().parent.parent / "files/extracted/dist-3d-maze"
maze = (D / "maze.txt").read_bytes()
N = 31
def at(x, y, z):
    return maze[z * 961 + y * 31 + x]

def cell(cx, cy, cz):
    return at(2 * cx + 1, 2 * cy + 1, 2 * cz + 1)

# find F
Fpos = None
dots = []
for cz in range(15):
    for cy in range(15):
        for cx in range(15):
            c = cell(cx, cy, cz)
            if c == ord('F'):
                Fpos = (cx, cy, cz)
            elif c == ord('.'):
                dots.append((cx, cy, cz))
print("F at cell", Fpos, "  start (7,7,7) cell val", chr(cell(7,7,7)))
print("num dots", len(dots))

# moves: key -> (dx,dy,dz)
MOVES = {
    'w': (0, -1, 0),
    's': (0, 1, 0),
    'o': (-1, 0, 0),
    'l': (1, 0, 0),
    'a': (0, 0, -1),
    'd': (0, 0, 1),
}

def passable(cx, cy, cz, dx, dy, dz):
    # midpoint between cells = wall slot at odd*? mid index = avg of two odd indices = even -> wall slot
    ix1 = 2 * cx + 1, 2 * cy + 1, 2 * cz + 1
    ix2 = 2 * (cx + dx) + 1, 2 * (cy + dy) + 1, 2 * (cz + dz) + 1
    mx = (ix1[0] + ix2[0]) // 2
    my = (ix1[1] + ix2[1]) // 2
    mz = (ix1[2] + ix2[2]) // 2
    if not (0 <= mx < N and 0 <= my < N and 0 <= mz < N):
        return False
    # also destination must be in bounds
    if not (0 <= cx + dx < 15 and 0 <= cy + dy < 15 and 0 <= cz + dz < 15):
        return False
    return at(mx, my, mz) == ord(' ')

start = (7, 7, 7)
q = deque([start])
prev = {start: None}
while q:
    cur = q.popleft()
    if cur == Fpos:
        break
    cx, cy, cz = cur
    for k, (dx, dy, dz) in MOVES.items():
        if passable(cx, cy, cz, dx, dy, dz):
            nxt = (cx + dx, cy + dy, cz + dz)
            if nxt not in prev:
                prev[nxt] = (cur, k)
                q.append(nxt)

if Fpos not in prev:
    print("NO PATH TO F"); raise SystemExit(1)

# reconstruct
path = []
node = Fpos
while prev[node] is not None:
    par, k = prev[node]
    path.append(k)
    node = par
path.reverse()
print("path len", len(path))
keys = "".join(path)
print("keys:", keys)
Path("/tmp/path_keys.txt").write_text(keys)
