#!/usr/bin/env python3
"""Drive the ncurses binary via a pty, feed BFS path keys, capture output (the flag)."""
import os, pty, select, time, sys
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "files/extracted/dist-3d-maze"
keys = (Path("/tmp/path_keys.txt").read_text()).strip()
print("feeding keys:", keys, "len", len(keys), file=sys.stderr)

pid, fd = pty.fork()
if pid == 0:
    os.chdir(D)
    os.execv("./chal", ["./chal"])
    os._exit(1)

# set window size big enough (rows, cols)
import fcntl, termios, struct
winsz = struct.pack("HHHH", 60, 200, 0, 0)
fcntl.ioctl(fd, termios.TIOCSWINSZ, winsz)

buf = b""
def drain(t=0.3):
    global buf
    end = time.time() + t
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            try:
                d = os.read(fd, 65536)
            except OSError:
                return False
            if not d:
                return False
            buf += d
    return True

drain(0.5)
seq = list(keys) + ["\n"]  # final enter quits at win? actually 'You win!' then getch==\n exits
for c in seq:
    os.write(fd, c.encode())
    drain(0.05)
# extra drain for final render
drain(0.8)
# send newline a few times to exit cleanly
for _ in range(3):
    os.write(fd, b"\n")
    drain(0.1)

try:
    os.close(fd)
except OSError:
    pass
try:
    os.waitpid(pid, 0)
except ChildProcessError:
    pass

txt = buf.decode("latin1")
Path("/tmp/run_out.txt").write_text(txt)
# strip ANSI
import re
clean = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", txt)
clean = re.sub(r"\x1b[()][AB0]", "", clean)
Path("/tmp/run_clean.txt").write_text(clean)
print("raw bytes:", len(txt), file=sys.stderr)
import re as _re
for m in _re.finditer(r"grey\{[^}]*\}", clean):
    print("FLAG:", m.group(0))
# also print last visible chars
print("---tail clean---", file=sys.stderr)
print(clean[-800:], file=sys.stderr)
