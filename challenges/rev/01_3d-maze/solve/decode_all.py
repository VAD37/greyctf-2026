import struct
chal=open("/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/files/extracted/dist-3d-maze/chal","rb").read()
# key dispatch table at vaddr 0x31d8, 0x17 entries (key-0x61, 'a'..'w' => 0..0x16)
base=0x31d8
keymap={}
HANDLERS={0x1f86:'w_dy-1',0x1f9c:'s_dy+1',0x1fb2:'a_dx-1',0x1fc8:'d_dx+1',0x1fde:'o_dz-1',0x1ff4:'l_dz+1'}
for i in range(0x17):
    off=struct.unpack_from("<i",chal,base+i*4)[0]
    tgt=base+off
    ch=chr(0x61+i)
    keymap[ch]=(tgt,HANDLERS.get(tgt,'default/ignore' if tgt==0x1f47 else hex(tgt)))
print("KEY TABLE (key -> handler):")
for ch,(t,n) in keymap.items():
    if 'default' not in n:
        print("  %s -> %#06x %s"%(ch,t,n))
# pool.bin
pool=open("/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/files/extracted/dist-3d-maze/pool.bin","rb").read()
print("\nPOOL first 64 bytes:", list(pool[:64]))
