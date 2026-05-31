#!/usr/bin/env bash
# Spawn the per-team whale instance for challenge 25, discover host:port, then
# run the prototype-pollution exploit against the live service to read grey{...}.
# Tries several CTFd-whale endpoint shapes (plugin route names vary by version).
# All output -> $LOG (persistent artifact). Flag -> solve/flag.txt.
set -u
ENVF=/media/vad/Work2/hackathon/greyctf-2026/.env
LOG=/media/vad/Work2/hackathon/greyctf-2026/challenges/ezpz/06_pollution/solve/remote_run.log
EXPLOIT=/media/vad/Work2/hackathon/greyctf-2026/challenges/ezpz/06_pollution/solve/exploit.py
CID=25
: > "$LOG"

set -a; . "$ENVF" 2>/dev/null; set +a
AUTH=(-H "Authorization: Token ${CTFD_API_TOKEN}")
CK=/tmp/poll_ctfd_cookies.txt

log(){ echo "$@" >> "$LOG"; }

log "=== env ==="
log "CTFD_URL=${CTFD_URL:-UNSET}  api_token=$([ -n "${CTFD_API_TOKEN:-}" ] && echo yes || echo no)"

# Also establish a session login (whale often keyed to session, not API token).
log "=== session login ==="
CSRF=$(curl -s -c "$CK" "${CTFD_URL}/login" | grep -oP "csrfNonce['\"]?\s*[:=]\s*['\"]\K[0-9a-f]+" | head -1)
[ -z "$CSRF" ] && CSRF=$(curl -s -b "$CK" -c "$CK" "${CTFD_URL}/login" | grep -oP 'name="nonce"\s+value="\K[^"]+' | head -1)
log "csrf=${CSRF:0:12}..."
curl -s -b "$CK" -c "$CK" -X POST "${CTFD_URL}/login" \
  --data-urlencode "name=${CTFD_USER}" \
  --data-urlencode "password=${CTFD_PASS}" \
  --data-urlencode "nonce=${CSRF}" \
  --data-urlencode "_submit=Submit" -o /dev/null -w "login_http=%{http_code}\n" >> "$LOG" 2>&1
# refresh csrf from an authed page for whale POSTs
CSRF2=$(curl -s -b "$CK" "${CTFD_URL}/challenges" | grep -oP "csrfNonce['\"]?\s*[:=]\s*['\"]\K[0-9a-f]+" | head -1)
log "csrf2=${CSRF2:0:12}..."

try_get(){ # url
  log "--- GET $1 ---"
  curl -s -b "$CK" "${AUTH[@]}" "$1" 2>>"$LOG"
}

# Candidate whale endpoints (different plugin versions / forks).
GET_EPS=(
  "${CTFD_URL}/api/v1/plugins/ctfd-whale/container?challenge_id=${CID}"
  "${CTFD_URL}/api/v1/plugins/ctfd-whale/instance?challenge_id=${CID}"
  "${CTFD_URL}/plugins/ctfd-whale/container?challenge_id=${CID}"
)
POST_EPS=(
  "${CTFD_URL}/api/v1/plugins/ctfd-whale/container?challenge_id=${CID}"
  "${CTFD_URL}/api/v1/plugins/ctfd-whale/instance?challenge_id=${CID}"
)

# 1) Check existing
RESP=""
for ep in "${GET_EPS[@]}"; do
  R=$(try_get "$ep"); log "$R"
  if echo "$R" | grep -q '"success"'; then RESP="$R"; GOTEP="$ep"; break; fi
done

# 2) If none/empty, POST to create
if ! echo "$RESP" | grep -q '"ip"\|"port"\|domain\|lan_domain\|"host"'; then
  for ep in "${POST_EPS[@]}"; do
    log "--- POST $ep ---"
    R=$(curl -s -b "$CK" "${AUTH[@]}" -H "Content-Type: application/json" \
        -H "CSRF-Token: ${CSRF2}" -H "X-CSRF-Token: ${CSRF2}" \
        -X POST "$ep" --data "{\"challenge_id\": ${CID}}" 2>>"$LOG")
    log "$R"
    if echo "$R" | grep -q '"success"'; then break; fi
  done
  sleep 4
  # re-GET
  for ep in "${GET_EPS[@]}"; do
    R=$(try_get "$ep"); log "$R"
    if echo "$R" | grep -q '"ip"\|"port"\|domain\|"host"'; then RESP="$R"; break; fi
  done
fi

log "=== resolving target ==="
log "RESP=$RESP"

# Extract a usable URL. Whale typically returns either:
#   { "data": { "ip": "...", "port": 12345 } }  (tcp)  -> http://ip:port
#   { "data": { "domain": "host", "port": ... } }      -> http://host:port
#   { "data": "host:port" }
TARGET=$(python3 - "$RESP" <<'PY'
import sys, json, re
raw = sys.argv[1] if len(sys.argv)>1 else ""
url=""
try:
    j=json.loads(raw)
    d=j.get("data", j)
    if isinstance(d,str):
        s=d.strip()
        if s.startswith("http"): url=s
        elif ":" in s: url="http://"+s
        elif s: url="http://"+s
    elif isinstance(d,dict):
        host=d.get("domain") or d.get("lan_domain") or d.get("ip") or d.get("host")
        port=d.get("port") or d.get("ports")
        if isinstance(port,(list,tuple)) and port: port=port[0]
        if host and port: url=f"http://{host}:{port}"
        elif host and str(host).count(":")==1: url="http://"+host
except Exception as e:
    m=re.search(r'(https?://[^\s"]+)', raw)
    if m: url=m.group(1)
print(url)
PY
)
log "TARGET=$TARGET"

if [ -z "$TARGET" ]; then
  log "!! could not resolve whale target URL. Inspect RESP above."
  echo "NO_TARGET"
  exit 3
fi

# Wait for the service to come up.
for i in $(seq 1 40); do
  if curl -s -o /dev/null --max-time 5 "$TARGET/"; then log "service up after $i tries"; break; fi
  sleep 1
done

log "=== running exploit against $TARGET ==="
cd /media/vad/Work2/hackathon/greyctf-2026
uv run --with requests python "$EXPLOIT" "$TARGET" >> "$LOG" 2>&1
log "exploit rc=$?"

FLAG=$(grep -ao 'grey{[^}]*}' "$LOG" | head -1)
log "EXTRACTED_FLAG=${FLAG:-NONE}"
echo "RESULT_FLAG=${FLAG:-NONE}"
