#!/usr/bin/env python3
"""Extract every embedded data:image base64 from the decoded trace stream and save as files.
The trace inlines computer-use screenshots as data:image/jpeg;base64,... — the flag is
rendered ON-SCREEN in one of these. We just need the bytes; no network required."""
import re, os, base64

D = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(D, "imgs")
os.makedirs(out_dir, exist_ok=True)

texts = {}
for fn in ["stream_full.txt","stream_dotjson.txt","stream_page.txt","trace_full.html"]:
    p = os.path.join(D, fn)
    if os.path.exists(p):
        texts[fn] = open(p, "r", errors="replace").read()

# data:image/<type>;base64,<DATA>  — DATA runs until a non-base64 char (quote/backslash/whitespace)
pat = re.compile(r'data:image/(?P<typ>[a-zA-Z0-9.+-]+);base64,(?P<data>[A-Za-z0-9+/=]+)')
count = 0
seen = set()
manifest = []
for fn, txt in texts.items():
    # the stream may have \/ or escaped sequences; normalize backslash-escapes minimally
    norm = txt.replace('\\/', '/')
    for m in pat.finditer(norm):
        b64 = m.group('data')
        typ = m.group('typ')
        if len(b64) < 200:   # skip tiny icons
            continue
        key = b64[:64]
        if key in seen:
            continue
        seen.add(key)
        # fix padding
        pad = (-len(b64)) % 4
        b64p = b64 + ("=" * pad)
        try:
            raw = base64.b64decode(b64p)
        except Exception as e:
            print("decode fail", fn, e); continue
        ext = "jpg" if "jpeg" in typ or "jpg" in typ else typ
        fname = f"img_{count:02d}.{ext}"
        with open(os.path.join(out_dir, fname), "wb") as f:
            f.write(raw)
        manifest.append((fname, typ, len(raw)))
        count += 1

for fn, typ, sz in manifest:
    print(f"{fn}\t{typ}\t{sz} bytes")
print("TOTAL images:", count, "-> dir:", out_dir)
