pool=open("/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/files/extracted/dist-3d-maze/pool.bin","rb").read()
print("len",len(pool))
print("first 80:", list(pool[:80]))
# pool used as: pool[poolptr+code]; poolptr starts at 5038=pool base, +=4 each emit.
# So entries are groups of 4 bytes: [w_val, s_val, a_val, d_val] per step.
for i in range(0,40,4):
    print(i//4, list(pool[i:i+4]))
