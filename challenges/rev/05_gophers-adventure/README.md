# Gopher's Adventure! — rev (816 pts) — SOLVED

`grey{G0pHeR_g0e5_oN_4N_4dv3ntur3!XDDDD}`

Remote: http://challs.nusgreyhats.org:33167 (web-rev). No handout — pulled `index.html`, `wasm_exec.js`, `main.wasm` from the server. Go 1.26.3 + ebitengine compiled to a 15 MB WASM gopher dino-jump game (`Score: 00000000`). `wasm_exec.js` is stock; only 3 resources served, all logic in `main.wasm`.

## Recon
- Obfuscated `main.*` syms in pclntab: `rewngfvskjd`, `vfdbvdsfdsg` (`main.(*Game).Update/Draw/Layout`, `main.main`).
- No wasm name section (Go strips it). Mapped Go names -> wasm func indices by:
  1. Reconstructing linear memory from the 100k data segments (`mem.bin`) — file layout != memory layout.
  2. Walking the Go `pclntab` (pcHeader magic `F1FFFFFF0001 08`) at mem addr 1376224. `funcoff` is **relative to the pcln region**, not the header. `entryOff = 4096 + rank` -> wasm idx `24 + rank` (24 imports).
- Targets: `rewngfvskjd`=idx 8995, `(*Game).Update`=8996.

## Logic
`Update` (8996) builds a 16-byte key every frame and `rewngfvskjd` (8995) XOR-decrypts a 39-byte ciphertext and `Fprintln`s the flag — but only when a game value `== 0x67676767` ("gggg").

Key build (4 blocks x 4 bytes), all operands in static `.data`:
```
key[4*b+i] = D[ A[4*b+i] ^ F[ (seed[b] >> 8*i) & 0xff ] ]      b,i in 0..3
flag[n]    = cipher[n] ^ key[n % 16]
```
- `A`   @7395472 (16 B)             ptr 6680672
- `F`   @7395568 (256 B sbox)       ptr 6707296
- `D`   @7395600 (256 B sbox)       ptr 6707552
- `cipher` @7395504 (39 B)          ptr 6686848
- `seed[]` @7395440 = 4 int64s: `0x100, 0x5555, 0x1234567, 0x67676767`

Key value is fully static -> no need to win. Confirmed against live wasm memory: the partially-written key at idle was `a213823b...` = first 4 computed bytes.

## Solve
`solve/solve.py` (reads `mem.bin`) -> `grey{G0pHeR_g0e5_oN_4N_4dv3ntur3!XDDDD}`.
Submitted via CTFd id 39 -> Correct.
