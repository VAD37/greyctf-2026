maze=open("/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/files/extracted/dist-3d-maze/maze.txt","rb").read()
N=31
def at(x,y,z): return maze[z*961+y*31+x]
# index func from 1ac5: idx=(2z+1)*961+(2y+1)*31+(2x+1). cells at odd coords, 15 cells per axis (0..14)? 2*14+1=29<31, 2*15+1=31 oob. so 0..14 -> 15 cells, plus walls between.
# Actually 31 = 2*15+1 grid: cells 0..14 (15), walls at even. wait 2*14+1=29, index 30 is last wall. so 15 cells 0..14? but render uses 0x1f=31 size. Let me find F and dots in cell space.
cells={}
import collections
hist=collections.Counter()
F=[]; dots=[]
for z in range(15):
    for y in range(15):
        for x in range(15):
            c=at(2*x+1,2*y+1,2*z+1)
            hist[chr(c)]+=1
            if c==ord('F'): F.append((x,y,z))
            if c==ord('.'): dots.append((x,y,z))
print("cell hist",dict(hist))
print("F cells",F)
print("num dots",len(dots))
print("start cell (7,7,7)=",chr(at(15,15,15)))
