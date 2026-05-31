#!/usr/bin/env python3
"""
spidr (rev) solver.

main: scanf u64 x -> tjlfs(&x) (chain of 100 obfuscated state-machine funcs
applying a fixed sequence of invertible u64 ops: add/xor/imul-by-odd) ->
cmp x == 0x67696d65666c6167 ("gimeflag" LE) -> printf("grey{%llu}", original_x).

So flag = grey{<original_int>} where transform(original_int) == target.

Strategy: emulate the real tjlfs chain in Unicorn on a probe input, decoding
each instruction with Capstone to record the ordered (op, k) list that mutates
the u64. The op sequence is input-independent (no data-dependent branches), so
one trace gives the whole forward transform. Then invert from the target.
"""
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from unicorn import (
    Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE, UC_PROT_ALL,
)
from unicorn.x86_const import (
    UC_X86_REG_RAX, UC_X86_REG_RDX, UC_X86_REG_RIP, UC_X86_REG_RSP,
    UC_X86_REG_RBP, UC_X86_REG_RDI,
)

HERE = Path(__file__).resolve().parent
BIN = HERE.parent / "files" / "extracted" / "dist-spidr" / "chal"
TARGET = 0x67696D65666C6167  # "gimeflag" little-endian
TJLFS = 0x75C10              # _Z5tjlfsPy (file/static offset; PIE base=0)
MASK = (1 << 64) - 1

# ---- load ELF segments (PIE base 0) ----
data = BIN.read_bytes()


def u16(o): return struct.unpack_from("<H", data, o)[0]
def u32(o): return struct.unpack_from("<I", data, o)[0]
def u64(o): return struct.unpack_from("<Q", data, o)[0]


def load_segments():
    e_phoff = u64(0x20)
    e_phentsize = u16(0x36)
    e_phnum = u16(0x38)
    segs = []
    for i in range(e_phnum):
        ph = e_phoff + i * e_phentsize
        p_type = u32(ph)
        if p_type != 1:  # PT_LOAD
            continue
        p_offset = u64(ph + 0x08)
        p_vaddr = u64(ph + 0x10)
        p_filesz = u64(ph + 0x20)
        p_memsz = u64(ph + 0x28)
        segs.append((p_vaddr, p_offset, p_filesz, p_memsz))
    return segs


PAGE = 0x1000
BASE = 0  # PIE loaded at 0

uc = Uc(UC_ARCH_X86, UC_MODE_64)

# map a generous code region
mapped = set()


def ensure_mapped(addr, size):
    start = addr & ~(PAGE - 1)
    end = (addr + size + PAGE - 1) & ~(PAGE - 1)
    for p in range(start, end, PAGE):
        if p not in mapped:
            uc.mem_map(p, PAGE, UC_PROT_ALL)
            mapped.add(p)


for vaddr, off, filesz, memsz in load_segments():
    ensure_mapped(BASE + vaddr, memsz)
    uc.mem_write(BASE + vaddr, data[off:off + filesz])

# stack
STACK = 0x7000_0000
STACK_SZ = 0x100000
uc.mem_map(STACK, STACK_SZ, UC_PROT_ALL)

# value cell that tjlfs mutates via its &x argument
VALCELL = 0x6000_0000
uc.mem_map(VALCELL, PAGE, UC_PROT_ALL)

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = False

ops = []  # ordered list of ('add'|'xor'|'mul', k)

# We detect the three mutation instructions inside the chain:
#   imul %rax,%rdx   (0x48 0x0f 0xaf 0xd0)   k previously loaded into rdx by movabs
#   add  %rax,%rdx   (0x48 0x01 0xc2)
#   xor  %rax,%rdx   (0x48 0x31 0xc2)
# In each block the constant k is a movabs imm into %rdx, then the op combines
# %rax(=current value) with %rdx; result stored back. So at the op instruction,
# rdx holds k and rax holds current value. We read rdx as k.

OP_BYTES = {
    bytes.fromhex("480faf"): "mul",   # imul r64, r/m64 -> 48 0f af /r ; d0 = rax->rdx
    bytes.fromhex("4801"): "add",     # add r/m64, r64  -> 48 01 /r ; c2 = rdx,rax
    bytes.fromhex("4831"): "xor",     # xor r/m64, r64  -> 48 31 /r ; c2
}


def hook_code(uc, address, size, user_data):
    code = uc.mem_read(address, size)
    # imul %rax,%rdx
    if size >= 4 and bytes(code[:3]) == b"\x48\x0f\xaf" and code[3] == 0xD0:
        k = uc.reg_read(UC_X86_REG_RDX)
        ops.append(("mul", k & MASK))
    elif size == 3 and bytes(code[:2]) == b"\x48\x01" and code[2] == 0xC2:
        k = uc.reg_read(UC_X86_REG_RDX)
        ops.append(("add", k & MASK))
    elif size == 3 and bytes(code[:2]) == b"\x48\x31" and code[2] == 0xC2:
        k = uc.reg_read(UC_X86_REG_RDX)
        ops.append(("xor", k & MASK))


uc.hook_add(UC_HOOK_CODE, hook_code)


def run_chain(x0):
    ops.clear()
    # set up value cell
    uc.mem_write(VALCELL, struct.pack("<Q", x0 & MASK))
    # registers / stack
    sp = STACK + STACK_SZ - 0x800
    uc.reg_write(UC_X86_REG_RSP, sp)
    uc.reg_write(UC_X86_REG_RBP, sp)
    uc.reg_write(UC_X86_REG_RDI, VALCELL)  # &x
    # push a fake return address we can stop on
    RET_STOP = 0x5000_0000
    if RET_STOP not in mapped:
        uc.mem_map(RET_STOP, PAGE, UC_PROT_ALL)
        mapped.add(RET_STOP)
    sp -= 8
    uc.mem_write(sp, struct.pack("<Q", RET_STOP))
    uc.reg_write(UC_X86_REG_RSP, sp)
    uc.emu_start(BASE + TJLFS, RET_STOP, count=0)
    final = struct.unpack("<Q", uc.mem_read(VALCELL, 8))[0]
    return final


def forward(x, op_list):
    v = x & MASK
    for op, k in op_list:
        if op == "add":
            v = (v + k) & MASK
        elif op == "xor":
            v ^= k
        elif op == "mul":
            v = (v * k) & MASK
    return v & MASK


def modinv64(a):
    # inverse of odd a mod 2^64 via Newton iteration
    assert a & 1, f"multiplier not odd: {a:#x}"
    x = 1
    for _ in range(7):  # converges for 2^64
        x = (x * (2 - a * x)) & MASK
    assert (a * x) & MASK == 1
    return x


def invert(target, op_list):
    v = target & MASK
    for op, k in reversed(op_list):
        if op == "add":
            v = (v - k) & MASK
        elif op == "xor":
            v ^= k
        elif op == "mul":
            v = (v * modinv64(k)) & MASK
    return v & MASK


def main():
    # 1) trace the op sequence on a probe input
    probe = 0x1122334455667788
    final = run_chain(probe)
    seq = list(ops)
    print(f"[*] traced {len(seq)} ops")
    from collections import Counter
    print("    op mix:", Counter(o for o, _ in seq))

    # sanity: emulated forward(probe) must equal our python replay
    assert forward(probe, seq) == final, (
        f"replay mismatch: {forward(probe,seq):#x} != {final:#x}")
    print(f"[*] forward replay matches emulator: {final:#x}")

    # 2) invert target -> candidate input
    x = invert(TARGET, seq)
    print(f"[*] candidate input = {x} ({x:#x})")

    # 3) verify: emulate chain on candidate, must hit TARGET
    chk = run_chain(x)
    assert chk == TARGET, f"verify fail: {chk:#x} != {TARGET:#x}"
    print(f"[+] verified: transform({x}) == {TARGET:#x} (gimeflag)")

    flag = f"grey{{{x}}}"
    print(flag)
    return flag


if __name__ == "__main__":
    main()
