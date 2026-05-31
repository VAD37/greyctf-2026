#!/usr/bin/env bash
# 24h waiting-game runner for "An old soviet terminal".
# Each iteration: ONE single-shot whole-flag attempt (ONESHOT=1 ./probe flag).
# Sleep a RANDOM 1-60s between attempts. Stop the instant a flag is captured.
#
# probe exit codes:  0 = flag captured (-> flag.txt)   10 = ran, no flag   20 = refused
#
#   ./run24h.sh            # 24h cap
#   ./run24h.sh 3600       # custom cap (seconds)
set -u
cd "$(dirname "$0")"

CAP="${1:-86400}"                     # default 24h
LOG="flag_hunt.log"
START=$(date +%s)
END=$(( START + CAP ))

tries=0; hits=0; refused=0
echo "===== HUNT START $(date '+%F %T')  cap=${CAP}s (ends $(date -d "@$END" '+%F %T')) =====" | tee -a "$LOG"

while :; do
    now=$(date +%s)
    [ "$now" -ge "$END" ] && { echo "[$(date '+%T')] 24h cap reached, stopping. tries=$tries hits=$hits refused=$refused" | tee -a "$LOG"; exit 2; }

    tries=$((tries+1))
    out=$(ONESHOT=1 ./probe flag 2>&1)
    rc=$?
    # one compact line per attempt into the log (full raw kept too)
    #line=$(printf '%s\n' "$out" | grep -E 'connected|connfail|verdict=|FLAG/RESULT' | tr '\n' ' ')
    line=$(printf '%s\n' "$out" | tr '\n' ' ')
    printf '[%s] try=%d rc=%d  %s\n' "$(date '+%T')" "$tries" "$rc" "$line" | tee -a "$LOG"

    if [ "$rc" -eq 0 ]; then
        flag=$(cat flag.txt 2>/dev/null)
        echo "===== SUCCESS $(date '+%F %T')  flag=${flag}  after tries=$tries hits=$hits refused=$refused =====" | tee -a "$LOG"
        printf '%s\n' "$out" >> "$LOG"
        echo "$flag"
        exit 0
    elif [ "$rc" -eq 10 ]; then
        hits=$((hits+1))
    else
        refused=$((refused+1))
    fi

    s=$(( (RANDOM % 60) + 1 ))         # random 1..60s
    sleep "$s"
done
