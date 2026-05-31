#!/usr/bin/env python3
"""Drive the real ./chal in a PTY, feed a move sequence, capture win() output (the flag)."""
import os, pty, time, select, sys, re, struct
from pathlib import Path

D = Path("/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/files/extracted/dist-3d-maze")
keys = sys.argv[1] if len(sys.argv) > 1 else "wdsdsdsodsdsddssls"

pid, fd = pty.fork()
if pid == 0:
    os.chdir(str(D))
    os.environ["TERM"] = "xterm"
    os.execv("./chal", ["./chal"])
    os._exit(1)

import fcntl, termios
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 50, 200, 0, 0))
buf = b""
def drain(t):
    global buf
    end = time.time() + t
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            try:
                d = os.read(fd, 65536)
            except OSError:
                return
            if not d:
                return
            buf += d

# initial screen waits for Enter (start screen: wgetch==0xa). Send Enter first.
drain(0.6)
os.write(fd, b"\n")
drain(0.5)
for c in keys:
    os.write(fd, c.encode())
    drain(0.08)
drain(0.6)
# after win, "Press enter to exit" loop reads more chars (it printed flag via VM putchar already)
for _ in range(4):
    os.write(fd, b"\n")
    drain(0.2)
try:
    os.close(fd)
except OSError:
    pass
try:
    os.waitpid(pid, 0)
except ChildProcessError:
    pass

txt = buf.decode("latin1")
# strip ANSI
clean = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", txt)
clean = re.sub(r"\x1b[()][AB0]", "", clean)
clean = clean.replace("\r", "")
Path("/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/solve/real_clean.txt").write_text(clean)
flags = re.findall(r"grey\{[a-z_]+\}", clean)
print("FLAGS:", flags)
# also print any "You win" context + the tail
i = clean.find("You win")
if i >= 0:
    print("WINCTX:", repr(clean[i:i+120]))
print("TAILRAW:", repr(clean[-200:]))
