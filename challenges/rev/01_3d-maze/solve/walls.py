maze=open("/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/files/extracted/dist-3d-maze/maze.txt","rb").read()
def at(x,y,z): return maze[z*961+y*31+x]
import collections
# wall slot between adjacent cells along x: (2x+2,2y+1,2z+1) for x in 0..13
hx=collections.Counter(); hy=collections.Counter(); hz=collections.Counter()
for z in range(15):
  for y in range(15):
    for x in range(14):
      hx[chr(at(2*x+2,2*y+1,2*z+1))]+=1
for z in range(15):
  for y in range(14):
    for x in range(15):
      hy[chr(at(2*x+1,2*y+2,2*z+1))]+=1
for z in range(14):
  for y in range(15):
    for x in range(15):
      hz[chr(at(2*x+1,2*y+1,2*z+2))]+=1
print("x-walls",dict(hx))
print("y-walls",dict(hy))
print("z-walls",dict(hz))
