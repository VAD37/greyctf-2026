#!/usr/bin/env python3
"""Decode the RSC __next_f stream from the /full trace page and hunt the flag."""
import re, json, os, base64, urllib.parse

D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, "FULL_RESULT.txt")
log = []
def L(*a):
    s = " ".join(str(x) for x in a); log.append(s); print(s)

def decode_page(path, tag):
    html = open(path, "r", errors="replace").read()
    L(f"[{tag}] html len", len(html))
    # gather every __next_f push payload (any index, any quoted string)
    pushes = re.findall(r'self\.__next_f\.push\(\[\d+,\s*("(?:[^"\\]|\\.)*")\s*\]\)', html, re.S)
    L(f"[{tag}] pushes", len(pushes))
    stream = ""
    for p in pushes:
        try:
            stream += json.loads(p)
        except Exception:
            try:
                stream += p[1:-1].encode().decode("unicode_escape")
            except Exception:
                stream += p[1:-1]
    open(os.path.join(D, f"stream_{tag}.txt"), "w").write(stream)
    L(f"[{tag}] decoded stream len", len(stream))
    return html, stream

def hunt(name, text):
    hits = set()
    # direct
    for m in re.findall(r'grey\{[^}]{0,300}\}', text, re.I):
        hits.add(m)
    # unicode-escaped braces grey{ ... }
    for m in re.findall(r'grey\\u007b.{0,300}?\\u007d', text, re.I):
        try: hits.add(m.encode().decode('unicode_escape'))
        except Exception: hits.add(m)
    # html-entity braces grey&#123; ... &#125;
    for m in re.findall(r'grey&#x?123;.{0,300}?&#x?125;', text, re.I):
        hits.add(m)
    # base64 blobs
    for b in re.findall(r'[A-Za-z0-9+/]{20,}={0,2}', text):
        try:
            dec = base64.b64decode(b, validate=False).decode('utf-8','ignore')
            for m in re.findall(r'grey\{[^}]{0,300}\}', dec, re.I):
                hits.add(m + "  (b64)")
        except Exception: pass
    # url-decoded
    try:
        ud = urllib.parse.unquote(text)
        for m in re.findall(r'grey\{[^}]{0,300}\}', ud, re.I):
            hits.add(m + "  (urldec)")
    except Exception: pass
    if hits:
        L(f"[HUNT {name}] HITS:")
        for h in sorted(hits): L("   FLAG>>", repr(h))
    else:
        L(f"[HUNT {name}] none")
    return hits

allhits = set()
for fname, tag in [("trace_full.html","full"), ("trace_dotjson.html","dotjson"), ("trace_page.html","page")]:
    p = os.path.join(D, fname)
    if not os.path.exists(p):
        L(f"[skip] {fname} missing"); continue
    html, stream = decode_page(p, tag)
    allhits |= hunt(tag+"-html", html)
    allhits |= hunt(tag+"-stream", stream)
    # show flag-ish context regardless
    for word in ['flag','grey','007b','&#123','secret','ctf{','reward']:
        for m in re.finditer(re.escape(word), stream, re.I):
            i=m.start()
            ctx = stream[max(0,i-60):i+120].replace('\n',' ')
            L(f"   ctx[{tag}/{word}] ...{ctx}...")
            break  # one example per word per page to keep short

L("")
L("==== ALL FLAG HITS ====")
for h in sorted(allhits): L("FINAL_FLAG:", h)
if not allhits: L("NONE")
open(OUT,"w").write("\n".join(log)+"\n")
print("WROTE", OUT)
