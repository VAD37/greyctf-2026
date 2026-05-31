#!/usr/bin/env python3
"""Codex Computer Use (GreyCTF id 29) solver.

Flag lives in a shared computer-use agent trace on traces.com (Next.js app).
Strategy:
  1. Fetch the share page HTML.
  2. Pull the trace id / any embedded JSON (__NEXT_DATA__, self.__next_f RSC chunks).
  3. Probe likely JSON/API data endpoints for the trace.
  4. Grep EVERYTHING (raw + base64/url-decoded) for grey{...}.
Writes results to solve/RESULT.txt so progress survives even if stdout is dropped.
"""
import re, json, sys, base64, urllib.parse, urllib.request, os

SHARE_ID = "jn7c59d3c3e847cwmdctga3z5d87h8mn"
BASE = "https://traces.com"
SHARE_URL = f"{BASE}/s/{SHARE_ID}"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "RESULT.txt")
FLAG_RE = re.compile(rb"grey\{[^}]*\}", re.I)

log_lines = []
def log(*a):
    s = " ".join(str(x) for x in a)
    log_lines.append(s)
    print(s)

def flush():
    with open(OUT, "w") as f:
        f.write("\n".join(log_lines) + "\n")

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
      "Accept": "text/html,application/json,*/*"}

def fetch(url, headers=None, timeout=40):
    h = dict(UA)
    if headers: h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
            return r.status, dict(r.headers), data
    except Exception as e:
        return None, {}, f"ERR {e}".encode()

found = set()
def scan(name, data):
    if isinstance(data, str): data = data.encode("utf-8", "replace")
    for m in FLAG_RE.findall(data):
        found.add(m.decode("utf-8", "replace"))
    # also try decoding base64-ish blobs
    for b in re.findall(rb"[A-Za-z0-9+/]{24,}={0,2}", data):
        try:
            dec = base64.b64decode(b, validate=False)
            for m in FLAG_RE.findall(dec):
                found.add(m.decode("utf-8", "replace") + "  (base64)")
        except Exception:
            pass
    # url-decoded
    try:
        ud = urllib.parse.unquote_to_bytes(data)
        for m in FLAG_RE.findall(ud):
            found.add(m.decode("utf-8", "replace") + "  (urldecoded)")
    except Exception:
        pass

# 1. main page
st, hdr, html = fetch(SHARE_URL)
log(f"[page] {SHARE_URL} status={st} bytes={len(html)}")
with open(os.path.join(os.path.dirname(OUT), "trace_page.html"), "wb") as f:
    f.write(html)
scan("page", html)

txt = html.decode("utf-8", "replace")

# 2. RSC / next data chunks: self.__next_f.push([1,"...."])
chunks = re.findall(r'self\.__next_f\.push\(\[\d+,\s*"((?:[^"\\]|\\.)*)"\]\)', txt)
log(f"[rsc] {len(chunks)} __next_f chunks")
rsc_all = ""
for c in chunks:
    try:
        dec = c.encode().decode("unicode_escape")
    except Exception:
        dec = c
    rsc_all += dec + "\n"
with open(os.path.join(os.path.dirname(OUT), "rsc_stream.txt"), "w") as f:
    f.write(rsc_all)
scan("rsc", rsc_all)

# pull any uuid-like / share-related ids and urls from rsc+html
ids = set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', txt + rsc_all))
log(f"[ids] uuids found: {sorted(ids)[:10]}")
urls = set(re.findall(r'https?://[^\s"\'\\<>]+', txt + rsc_all))
api_urls = sorted(u for u in urls if 'api' in u or 'trace' in u or SHARE_ID in u)
log(f"[urls] candidate api urls: {api_urls[:20]}")

# also relative api paths
rel = set(re.findall(r'["\'](/(?:api|trpc|trace|s)/[^"\'\\<>]+)["\']', txt + rsc_all))
log(f"[rel] candidate relative paths: {sorted(rel)[:20]}")

# 3. probe likely endpoints
candidates = [
    f"{BASE}/api/s/{SHARE_ID}",
    f"{BASE}/api/share/{SHARE_ID}",
    f"{BASE}/api/traces/{SHARE_ID}",
    f"{BASE}/api/trace/{SHARE_ID}",
    f"{BASE}/api/v1/shares/{SHARE_ID}",
    f"{BASE}/s/{SHARE_ID}.json",
    f"{BASE}/s/{SHARE_ID}/data",
    f"{BASE}/api/public/share/{SHARE_ID}",
]
for u in api_urls:
    candidates.append(u)
for p in rel:
    candidates.append(BASE + p)
for i in ids:
    candidates.append(f"{BASE}/api/traces/{i}")
    candidates.append(f"{BASE}/api/trace/{i}")

seen=set()
for u in candidates:
    if u in seen: continue
    seen.add(u)
    st, hdr, data = fetch(u, headers={"Accept":"application/json"})
    ct = hdr.get("Content-Type","")
    log(f"[probe] {st} {len(data) if isinstance(data,bytes) else data} ct={ct} :: {u}")
    if isinstance(data, bytes) and st and st < 400 and len(data) > 0:
        scan(u, data)
        # save interesting json
        if 'json' in ct.lower() or data[:1] in (b'{', b'['):
            safe = re.sub(r'[^a-zA-Z0-9]+','_',u)[-60:]
            with open(os.path.join(os.path.dirname(OUT), f"probe_{safe}.json"), "wb") as f:
                f.write(data)

log("")
log("==== FLAG CANDIDATES ====")
for f_ in sorted(found):
    log("FLAG:", f_)
if not found:
    log("NO grey{...} found yet.")
flush()
print("\nDONE. results in", OUT)
