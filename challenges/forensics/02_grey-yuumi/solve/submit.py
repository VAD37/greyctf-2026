#!/usr/bin/env python3
"""Spam CTFd flag attempts for challenge 31 from a ranked dict.txt.
Logs in with session+CSRF (API token is expired). Persists tried.txt to
avoid resubmitting. Stops on `correct`, honors `ratelimited`."""
import re, json, time, sys, pathlib
import requests

HERE = pathlib.Path(__file__).parent
CHALL_ID = 31

# read .env directly (special chars break shell sourcing)
env = {}
for ln in (HERE.parent.parent.parent.parent / ".env").read_text().splitlines():
    if "=" in ln and not ln.startswith("#"):
        k, v = ln.split("=", 1)
        env[k.strip()] = v.strip().strip('"')
URL = env["CTFD_URL"].rstrip("/")
USER, PASS = env["CTFD_USER"], env["CTFD_PASS"]

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0"

def get_nonce(path):
    r = s.get(URL + path, timeout=20)
    m = re.search(r'name="nonce"[^>]*value="([0-9a-fA-F]+)"', r.text) \
        or re.search(r"'csrfNonce':\s*\"([0-9a-fA-F]+)\"", r.text) \
        or re.search(r'"csrfNonce":\s*"([0-9a-fA-F]+)"', r.text)
    return m.group(1) if m else None

# login
login_nonce = get_nonce("/login")
r = s.post(URL + "/login", data={"name": USER, "password": PASS,
           "nonce": login_nonce, "_submit": "Submit"}, allow_redirects=True, timeout=20)
me = s.get(URL + "/api/v1/users/me", headers={"Accept": "application/json"}, timeout=20)
print("login -> /users/me status", me.status_code)
if me.status_code != 200:
    print("LOGIN FAILED"); sys.exit(1)
csrf = get_nonce("/challenges")
print("csrf nonce:", (csrf or "")[:12], "...")

tried_path = HERE / "tried.txt"
tried = set(x.strip() for x in tried_path.read_text().splitlines() if x.strip()) if tried_path.exists() else set()
cands = [x.strip() for x in (HERE / "dict.txt").read_text().splitlines() if x.strip()]
pending = [c for c in cands if c not in tried]
print(f"dict={len(cands)} tried={len(tried)} pending={len(pending)}")

tf = open(tried_path, "a")
def headers():
    return {"Content-Type": "application/json", "CSRF-Token": csrf,
            "Referer": URL + "/challenges", "Accept": "application/json"}

n = 0
for flag in pending:
    while True:
        r = s.post(URL + "/api/v1/challenges/attempt", headers=headers(),
                   data=json.dumps({"challenge_id": CHALL_ID, "submission": flag}), timeout=20)
        try:
            d = r.json().get("data", {})
        except Exception:
            print("non-json", r.status_code, r.text[:200]); time.sleep(3); continue
        st = d.get("status")
        if st == "ratelimited":
            print("ratelimited, backoff 65s"); time.sleep(65); continue
        if r.status_code == 403:  # csrf expired
            csrf2 = get_nonce("/challenges")
            if csrf2 and csrf2 != csrf:
                print("refreshed csrf");
                globals()['csrf']=csrf2; continue
        break
    tried.add(flag); tf.write(flag + "\n"); tf.flush()
    n += 1
    if st == "correct" or st == "already_solved":
        print("\n*** CORRECT ***:", flag)
        (HERE / "FLAG.txt").write_text(flag + "\n")
        break
    if n % 20 == 0:
        print(f"  {n} tried, last={flag} -> {st}")
    time.sleep(8)
else:
    print("exhausted pending, no correct")
tf.close()
print("done, total submitted this run:", n)
