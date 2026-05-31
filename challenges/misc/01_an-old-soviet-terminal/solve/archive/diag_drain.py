#!/usr/bin/env python3
# Diagnostic: stage the submission, then drain until the SERVER closes the socket
# (or a generous overall cap). Timestamp every meaningful token so we learn WHEN the
# result frame arrives relative to EOF -- to decide whether probe.rs's 2600ms DRAIN
# is cutting off real results.
import socket, sys, time

HOST, PORT = "challs.nusgreyhats.org", 36167
CAP = 12.0  # overall read budget after EOF

PRESETS = {
    "none": '"AAAA"',
    "ok":   'send(analysisService,("analyze",self()));receive[hn("analysis",L)=>"OK"]',
    "g":    'send(analysisService,("compare",self(),0,"g"));receive[hn("comparison",s)=>(send(logService,("log",self(),s));receive[hn("logged",b)=>if b then "g" else "?"])]',
}

def recv_until(s, needle, cap):
    s.settimeout(0.3)
    buf = b""
    t0 = time.time()
    while time.time() - t0 < cap:
        try:
            d = s.recv(8192)
            if not d:
                return buf, True  # closed
            buf += d
            if needle and needle in buf:
                return buf, False
        except socket.timeout:
            continue
        except OSError:
            return buf, True
    return buf, False

def run(preset):
    prog = PRESETS[preset]
    t_conn = time.time()
    s = socket.create_connection((HOST, PORT), timeout=6)
    recv_until(s, b">>", 5)
    s.sendall(b"4\n")
    recv_until(s, b">>", 5)
    s.sendall(prog.encode() + b"\nEOF\n")
    t_eof = time.time()
    # drain until close or CAP, recording arrival time of key tokens
    s.settimeout(0.3)
    buf = b""
    marks = {}
    closed = False
    while time.time() - t_eof < CAP:
        try:
            d = s.recv(8192)
            if not d:
                closed = True
                break
            buf += d
            for tok in (b"TELETYPE", b"Message:", b"abnormally", b"grey{"):
                if tok not in marks and tok in buf:
                    marks[tok] = time.time() - t_eof
        except socket.timeout:
            continue
        except OSError:
            closed = True
            break
    s.close()
    txt = buf.decode("utf-8", "replace")
    msg = ""
    for ln in txt.splitlines():
        if "Message:" in ln:
            msg = ln.split("Message:", 1)[1].replace("║", "").strip()
    print(f"[{preset}] conn->eof={t_eof-t_conn:.2f}s  drained={time.time()-t_eof:.2f}s  closed_by_server={closed}  bytes={len(buf)}")
    print(f"   token arrival (s after EOF): " +
          ", ".join(f"{k.decode()}={v:.2f}" for k, v in marks.items()) or "   (no tokens)")
    if msg:
        print(f"   >>> Message: {msg!r}")
    elif b"abnormally" in marks:
        print("   >>> result: terminated abnormally")
    else:
        print("   >>> result: NO result frame seen")
    return msg

if __name__ == "__main__":
    preset = sys.argv[1] if len(sys.argv) > 1 else "none"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    for i in range(n):
        try:
            run(preset)
        except Exception as e:
            print(f"[{preset}] connfail: {e}")
        time.sleep(2)
