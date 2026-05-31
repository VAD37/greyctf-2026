"""Raw Minecraft 1.18+ Anvil (.mca) parser → block positions by name."""
import zlib, gzip, io, struct
from pathlib import Path
import nbtlib

def read_region(path):
    data = Path(path).read_bytes()
    chunks = {}
    for i in range(1024):
        off, = struct.unpack(">I", b"\x00" + data[i*4:i*4+3])
        cnt = data[i*4+3]
        if off == 0: continue
        cx, cz = i % 32, i // 32
        start = off * 4096
        length = struct.unpack(">I", data[start:start+4])[0]
        ctype = data[start+4]
        raw = data[start+5:start+4+length]
        if ctype == 1: nbtraw = gzip.decompress(raw)
        elif ctype == 2: nbtraw = zlib.decompress(raw)
        elif ctype == 3: nbtraw = raw
        else: raise ValueError(f"comp {ctype}")
        nbt = nbtlib.File.from_fileobj(io.BytesIO(nbtraw), byteorder='big')
        chunks[(cx,cz)] = nbt
    return chunks

def unpack_indices(longs, bits, count):
    out=[]; per = 64//bits; mask=(1<<bits)-1
    for L in longs:
        v = L & 0xFFFFFFFFFFFFFFFF
        for _ in range(per):
            out.append(v & mask); v >>= bits
            if len(out)>=count: return out
    return out

def iter_blocks(path, want=None):
    """yield (name, props, x,y,z). want=set of names to filter."""
    chunks = read_region(path)
    for (cx,cz), nbt in chunks.items():
        root = nbt
        # top-level compound (1.18 has data at root, no '')
        d = root[''] if '' in root else root
        xPos = int(d['xPos']); zPos = int(d['zPos'])
        secs = d.get('sections', [])
        for sec in secs:
            Y = int(sec['Y'])
            bs = sec.get('block_states')
            if bs is None: continue
            pal = bs['palette']
            names = [str(p['Name']) for p in pal]
            if want and not (set(names) & want): 
                continue
            data = bs.get('data')
            if data is None:
                # single-block section
                idx = [0]*4096
            else:
                import math
                bits = max(4, (len(pal)-1).bit_length())
                idx = unpack_indices(list(data), bits, 4096)
            for j,ix in enumerate(idx):
                name = names[ix]
                if want and name not in want: continue
                ly = j//256; lz=(j%256)//16; lx=j%16
                X = xPos*16+lx; Yb = Y*16+ly; Z=zPos*16+lz
                props = pal[ix].get('Properties')
                props = {str(k):str(v) for k,v in props.items()} if props else {}
                yield (name, props, X, Yb, Z)

if __name__=="__main__":
    import sys, collections
    base=Path("challenges/rev/04_lights-out/files/extracted/dist-lights-out")
    cnt=collections.Counter()
    for name,props,x,y,z in iter_blocks(base/"region/r.0.0.mca"):
        cnt[name]+=1
    for n,c in cnt.most_common():
        print(c, n)
