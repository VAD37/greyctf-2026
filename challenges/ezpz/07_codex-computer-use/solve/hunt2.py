#!/usr/bin/env python3
import re, os, base64, binascii

D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, "HUNT2.txt")
log=[]
def L(*a): s=" ".join(str(x) for x in a); log.append(s); print(s)

streams = {}
for fn in ["stream_full.txt","stream_dotjson.txt","stream_page.txt"]:
    p=os.path.join(D,fn)
    if os.path.exists(p):
        streams[fn]=open(p,"r",errors="replace").read()

# 1) every 'flag' occurrence with wide context (DOTALL via [\s\S])
for fn,s in streams.items():
    for m in re.finditer(r'flag', s, re.I):
        i=m.start()
        ctx=s[max(0,i-60):i+200]
        L(f"--- FLAGCTX [{fn} @ {i}] ---")
        L(repr(ctx))

# 2) hunt base64 blobs that decode to something containing 'grey' or 'flag' or printable
L("\n==== BASE64 DECODE SCAN ====")
seen=set()
for fn,s in streams.items():
    for b in set(re.findall(r'[A-Za-z0-9+/]{16,}={0,2}', s)):
        if b in seen: continue
        seen.add(b)
        for variant in (b, b+"=", b+"=="):
            try:
                dec=base64.b64decode(variant, validate=False)
            except Exception:
                continue
            low=dec.lower()
            if b'grey' in low or b'flag' in low or b'ctf{' in low:
                L(f"[b64 hit {fn}] {b[:40]}... -> {dec[:120]!r}")
                break

# 3) decode the specific 'eMxx' fragment region (the flageMxx lead)
for fn,s in streams.items():
    idx = s.lower().find('flage')
    if idx>=0:
        frag = s[idx:idx+400]
        L(f"\n[flage region {fn}] {frag!r}")
        # try base64 decode of trailing token after 'flag'
        tok = re.match(r'flag([A-Za-z0-9+/=]+)', s[idx:], re.I)
        if tok:
            t=tok.group(1)
            L(f"  token after flag: {t[:200]}")
            for pad in ("","=","=="):
                try:
                    dd=base64.b64decode(t+pad, validate=False)
                    L(f"  b64 decode(+{len(pad)}): {dd[:160]!r}")
                except Exception as e:
                    pass

# 4) general: any printable run containing grey or g.r.e.y obfuscation
L("\n==== OBFUSCATED grey scan ====")
for fn,s in streams.items():
    for pat in [r'g[\W_]{0,3}r[\W_]{0,3}e[\W_]{0,3}y[\W_]{0,5}\{', r'grey\s*\{', r'g.?r.?e.?y.?\{']:
        for m in re.finditer(pat, s, re.I):
            i=m.start(); L(f"[obf {fn} {pat[:10]}] {s[i:i+120]!r}")

open(OUT,"w").write("\n".join(log)+"\n")
print("WROTE",OUT,"lines",len(log))
