#!/usr/bin/env python3
"""Gopher's Adventure! (GreyCTF 2026, rev) — offline flag recovery.

Go(ebiten)->WASM jump game. Flag printed by obfuscated func main.rewngfvskjd
(wasm idx 8995) on the win trigger, decoded as:

    key[4*b+i] = D[ A[4*b+i] ^ F[ (seed[b] >> 8*i) & 0xff ] ]   b=0..3, i=0..3
    flag[n]    = cipher[n] ^ key[n % 16]

A,F,D, cipher and the 4 int64 block-seeds are static .data, recovered by
reconstructing wasm linear memory from the 100k data segments and walking
the Go pclntab to name funcs. Seeds: 0x100,0x5555,0x1234567,0x67676767
(the last == the "gggg" score trigger checked in main.(*Game).Update).
"""
import struct

mem = open("mem.bin","rb").read()           # reconstructed linear-memory image
A      = mem[6680672:6680672+16]
F      = mem[6707296:6707296+256]            # 256-byte sbox
D      = mem[6707552:6707552+256]            # 256-byte sbox
cipher = mem[6686848:6686848+39]
sptr, slen = struct.unpack_from("<QQ", mem, 7395440)
seeds = [struct.unpack_from("<q", mem, sptr+8*i)[0] for i in range(slen)]

key = bytearray(16)
for b in range(4):
    s = seeds[b] & 0xffffffffffffffff
    for i in range(4):
        j = 4*b + i
        key[j] = D[(A[j] ^ F[(s >> (8*i)) & 0xff]) & 0xff]

flag = bytes(cipher[n] ^ key[n % 16] for n in range(len(cipher)))
print(flag.decode())
