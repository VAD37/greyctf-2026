#!/usr/bin/env python3
r"""
An old soviet terminal  (GreyCTF 2026, misc, 1000pts)  ── single-file driver + probe lab
=========================================================================================

REMOTE
    nc challs.nusgreyhats.org 36167     (ONE connection at a time — server refuses a 2nd)

THE MENU ("click a terminal button")
    On connect the server prints a banner + a numbered menu, prompt is ">> ".
    You "click a button" by sending its number + newline:
        [1] Archive          [2] Censorship Desk   [3] Index Clerk
        [4] Transmission  <── the scripting terminal we use
        [5] Maintenance Log  [6] Self-Destruct     [7] Exit
    This driver always auto-presses 4, then submits a Troupe script.

OPTION 4 = SCRIPT TERMINAL
    After pressing 4 it asks for a program, ended by a line containing exactly: EOF
    The text you submit becomes the body of  fun retriever() = <YOUR CODE>  (an
    EXPRESSION that must return a STRING).  The wrapper then runs, on a remote actor
    node, roughly:
        printString("Message: " ^ retriever())
    So:
      * success  -> teletype box shows:  Message: <your returned string>
      * crash    -> teletype box shows:  [ERROR] Program terminated abnormally.
      * retriever MUST return a string (returning an int/bool -> crash).
      * printString INSIDE your code runs on the SERVER node -> invisible to us.
        The ONLY thing we observe is the returned string. Debug by encoding into it.
    After the program runs, the menu reprints (one program per option-4 entry).

SERVICES IN SCOPE inside retriever()  (send a tuple, then `receive` the reply)
    send(analysisService, ("analyze",  self()))           -> ("analysis",   len)   public length
    send(analysisService, ("compare",  self(), idx, ch))  -> ("comparison", bool)  SECRET equality
    send(logService,      ("log",      self(), content))  -> ("logged",     decl)  declassify->public
    send(logService,      ("status",   self()))           -> ("status", "OPERATIONAL")

TIMING / RELIABILITY
    The node self-kills ~2s after start (terminal.trp: exitAfterTimeout 2000), and the
    server is genuinely flaky ("not very reliable"). A single literal can pass on one
    attempt and crash on the next. Round-trip-heavy scripts reliably hit the ~2s wall
    -> abnormal termination. Treat one shot as noisy; use -nN to tally a distribution.

USAGE
    uv run python soviet.py                       # list probe names
    uv run python soviet.py logecho               # run one probe (retry until definitive)
    uv run python soviet.py lit ge logecho        # run several
    uv run python soviet.py launder_br -n8         # run 8x, tally msg/error/none
    uv run python soviet.py -e 'EXPR'             # run an ad-hoc inline Troupe expression
    uv run python soviet.py -f path.trp           # run a script from a file
    echo 'EXPR' | uv run python soviet.py -        # run from stdin
    (add --raw to any of the above to dump the full server output)

FINDINGS SO FAR
    works : "literal", `if a>=b ...`, log echo of a PUBLIC string, launder secret bool
            through log then return a LITERAL (round-trip completes).
    crash : using analyze `n` in a branch; branching on a secret OR laundered value;
            returning a non-string. (Unresolved: how much is IFC vs the ~2s timeout —
            flakiness pollutes every single shot. Use -nN.)
"""
import sys, time, fcntl, collections
from pwn import *

context.log_level = 'error'
HOST, PORT = 'challs.nusgreyhats.org', 36167

# ── global rate limiter: serialize + space out connection attempts (single-slot server) ──
LOCKFILE = '/tmp/soviet_nc.gate'
MIN_GAP = 30.0   # seconds between connection attempts, across ALL soviet.py processes (server rate-limits ~1/30s)


def _pace():
    lf = open(LOCKFILE, 'a+')
    fcntl.flock(lf, fcntl.LOCK_EX)
    try:
        lf.seek(0); data = lf.read().strip()
        last = float(data) if data else 0.0
        wait = MIN_GAP - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
    finally:
        lf.seek(0); lf.truncate(); lf.write(str(time.time())); lf.flush()
        fcntl.flock(lf, fcntl.LOCK_UN); lf.close()


def conn(tries=40):
    for _ in range(tries):
        _pace()
        try:
            return remote(HOST, PORT, timeout=8)
        except Exception:
            pass
    return None


def run_once(code, settle=8):
    """Connect -> press 4 -> submit code + EOF -> capture teletype output."""
    io = conn()
    if io is None:
        return ''
    out = b''
    try:
        io.recvuntil(b'>>', timeout=6)        # main menu prompt
        io.sendline(b'4')                     # "click" Transmission terminal
        io.recvuntil(b'>>', timeout=6)        # script prompt
        io.send(code.encode() + b'\nEOF\n')   # submit program, terminate with EOF line
        deadline = time.time() + settle
        while time.time() < deadline:
            try:
                chunk = io.recv(timeout=1)
                if chunk:
                    out += chunk
                    deadline = time.time() + settle
            except EOFError:
                break
            except Exception:
                pass
    except Exception:
        pass
    finally:
        try: io.close()
        except Exception: pass
    return out.decode(errors='replace')


def extract_message(out):
    msgs = []
    for ln in out.splitlines():
        if 'Message:' in ln:
            msgs.append(ln.split('Message:', 1)[1].strip().rstrip('║').strip())
    return msgs


def verdict(out):
    """('error',) | ('msg', text) | ('none',)."""
    if 'terminated abnormally' in out:
        return ('error',)
    m = extract_message(out)
    return ('msg', ' '.join(m)) if m else ('none',)


def run(code, settle=8, tries=20, raw=False):
    """Retry through flaky connections until a definitive teletype result (msg OR error)."""
    last = ''
    for _ in range(tries):
        out = run_once(code, settle=settle)
        last = out
        if raw and len(out) > 1300:
            return out
        if verdict(out)[0] in ('msg', 'error'):
            return out
    return last


# ── inline Troupe probes (each = retriever() body; MUST return a string) ──────────────────
PROBES = {
    "lit":         '"RETVAL_OK"',
    "ge":          'if 2 >= 1 then "GE_OK" else "no"',
    "logecho":     'send(logService,("log",self(),"LOGECHO123")); '
                   'receive [ hn ("logged", x) => x ]',
    "analyze_lit": 'send(analysisService,("analyze",self())); '
                   'receive [ hn ("analysis", n) => "ANALYZE_LIT" ]',
    "compare_lit": 'send(analysisService,("compare",self(),0,"g")); '
                   'receive [ hn ("comparison", b) => "COMPARE_LIT" ]',
    # launder secret bool through log, return LITERAL (no branch) — WORKS
    "launder_nb":  'send(analysisService,("compare",self(),0,"g")); '
                   'receive [ hn ("comparison", b) => '
                   '  send(logService,("log",self(),b)); '
                   '  receive [ hn ("logged", pb) => "NB" ] ]',
    # launder, THEN branch on laundered value — crashes
    "launder_br":  'send(analysisService,("compare",self(),0,"g")); '
                   'receive [ hn ("comparison", b) => '
                   '  send(logService,("log",self(),b)); '
                   '  receive [ hn ("logged", pb) => if pb then "T" else "F" ] ]',
    # branch on secret bool first, then launder the string — crashes
    "secret_br":   'send(analysisService,("compare",self(),0,"g")); '
                   'receive [ hn ("comparison", b) => '
                   '  send(logService,("log",self(), if b then "T" else "F")); '
                   '  receive [ hn ("logged", s) => s ] ]',
    # length rendered as stars (uses analyze n in a branch) — crashes
    "stars":       'send(analysisService,("analyze",self())); '
                   'receive [ hn ("analysis", n) => '
                   '  let fun st i = if i >= n then "" else ("#" ^ st (i+1)) in st 0 end ]',
}


def main():
    args = sys.argv[1:]
    raw = '--raw' in args
    args = [a for a in args if a != '--raw']

    # ad-hoc / file / stdin modes
    if args and args[0] == '-e':
        print(verdict(run(args[1], raw=raw)) if not raw else run(args[1], raw=True)); return
    if args and args[0] == '-f':
        print(verdict(run(open(args[1]).read(), raw=raw))); return
    if args and args[0] == '-':
        print(verdict(run(sys.stdin.read(), raw=raw))); return

    n = 1
    names = []
    for a in args:
        if a.startswith('-n'):
            n = int(a[2:])
        else:
            names.append(a)
    if not names:
        print("probes:", " ".join(PROBES))
        print("run:    uv run python soviet.py <name> [<name>...] [-nN] [--raw]")
        print("ad-hoc: uv run python soviet.py -e '\"HI\"'")
        return
    for name in names:
        code = PROBES.get(name)
        if code is None:
            print(f">>> {name}: UNKNOWN"); continue
        if n == 1:
            print(f">>> {name}: {verdict(run(code))}", flush=True)
        else:
            c = collections.Counter(); vals = set()
            for _ in range(n):
                v = verdict(run_once(code))   # raw single shot, no retry
                c[v[0]] += 1
                if v[0] == 'msg':
                    vals.add(v[1])
            print(f">>> {name} x{n}: {dict(c)} vals={vals}", flush=True)


if __name__ == '__main__':
    main()
