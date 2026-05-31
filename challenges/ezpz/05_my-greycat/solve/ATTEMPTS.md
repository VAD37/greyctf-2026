# ATTEMPTS — ezpz/05_my-greycat (rev → trailer video)

## SOLVED the reversing half; flag-extraction from the trailer is the open part.

## Binary analysis (DONE, verified)
- `files/extracted/dist-my_greycat/main` is a 51 MB x86-64 PIE ELF (g++, not stripped).
- objdump @ main (0x1209): reads three .data arrays and writes `data.bin` in CWD:
  - `cs` int32[] @ vaddr 0x4020   (values 0..255)
  - `ds` int32[] @ vaddr 0x186f3e0  (used as **UNSIGNED** exponent — the loop compare is `jb`)
  - `n`  u32      @ vaddr 0x30da784  = **6401257**
  - .data: vaddr 0x4000 -> file off 0x3000, so file_off = vaddr - 0x1000.
  - per i: `x=1; for j in [0,(u32)ds[i]): x = REDUCE(x*cs[i]); data.bin[i]=x&0xff`
- IMPORTANT: REDUCE is the compiler magic-number `imul 0xff00ff01; shr; ...` which is **NOT a true `% 255`**.
  Exact: `REDUCE(x) = x - 257*((0xff00ff01*x) >> 40)`. e.g. REDUCE(255)=255, REDUCE(256)=256, REDUCE(257)=0.
  Must emulate exactly (not `pow(c,d,255)`). x stays in 0..256 → per-c trajectory is short-cyclic →
  resolve any ~4e9 exponent via tail+cycle indexing.
- The shipped binary itself **times out** (each element loops up to ~4 billion times); reimplement in Python.

## Reconstruction (DONE, byte-exact)
- `solve/solve.py` reproduces the loop with exact REDUCE + cycle-jump.
  Validated against the literal loop: 0 mismatches over 20000 random (c,d) incl. the asm reduce.
- Output `solve/data.bin` (6401257 bytes) = a **valid MP4** (also copied to `solve/trailer.mp4`).
  `file` → "ISO Media, MP4 v2"; h264 decodes cleanly to 568 frames (379 real @ 19.98 fps), 1280x720, +AAC.
  This is the GreyCTF 2026 promo **trailer** (draft, made in CapCut 2026-05-22).

## Trailer content (full visual review — NO grey{...} found anywhere)
Scenes: glitch "GreyCTF 2026" (multilingual 灰/グレー/희색/Grey) → "New Mode: King of the Hill" →
"5 Categories" greycat w/ RSA-DH math overlay (Pwn/Misc/Web/Cryptography/Reverse Engineering) →
glasses close-up "something will happen here uhhh" (placeholder) → "Team Logo" placeholders →
"Team Legit" vs "Team Clankers" → "Teams of 4 / Local / International" → green star transition →
"LOCK AND LOAD" → CapCut outro. No flag text in any frame (every decoded frame, dense contact sheets,
gamma-boosted dark frames, single-frame "flash" detector → only the green-star bright frame).

## Negative results (so the flag is NOT here)
- exiftool -a -u -g1 -ee: standard MP4 tags only, no comment/flag, no embedded thumbnail.
- MP4 atom walk: ftyp+mdat+moov, **0 trailing bytes**, **0 unreferenced mdat bytes** (no carved file).
- No udta/meta/ilst flag; raw `strings` on mdat = H264 noise only.
- Audio: showspectrumpic (both channels, lin+log) = music only, no spectrogram text.
- Web origin hunt: no public writeup yet (contest live). No "bibble"/known-cat hit.

## Contest note seen mid-solve
- Admin: "the flag for my-greycat has been **updated**. Resubmit your old flags if they didn't work."
  → implies the flag IS obtainable from the trailer (location/method unchanged); only the value was fixed.

## Where the flag likely is (next session)
1. A frame's on-screen text mis-read — re-OCR every frame (install `tesseract`/`easyocr`) for `grey{`.
2. Possibly a brief/animated overlay only readable mid-motion — play `solve/trailer.mp4` in a real player.
3. Re-examine the "5 Categories" greycat math overlay + placeholder frames at full res for a stylized flag,
   or the green decorative text strip in King-of-the-Hill frames (motion-blurred).
4. Reconsider if the flag references another CTF (user hint: cat name "bibble").

## Key artifacts
- solve/solve.py              — byte-exact reconstructor (`uv run python solve.py`)
- solve/trailer.mp4 / data.bin — the recovered trailer
- solve/frames_full/          — all 568 decoded PNG frames
- solve/sheets/               — contact sheets per section
- solve/spectro*.png          — audio spectrograms
