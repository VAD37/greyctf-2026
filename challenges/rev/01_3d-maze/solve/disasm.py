#!/usr/bin/env python3
"""Disassemble chal, resolve PLT, find functions and the VM dispatch loop."""
import sys
from pathlib import Path
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from capstone import Cs, CS_ARCH_X86, CS_MODE_64, CS_OP_IMM

BASE = Path(__file__).resolve().parent.parent
CHAL = BASE / "files/extracted/dist-3d-maze/chal"

f = open(CHAL, "rb")
elf = ELFFile(f)

# section map
sects = {}
for s in elf.iter_sections():
    sects[s.name] = s

text = sects.get(".text")
text_addr = text["sh_addr"]
text_data = text.data()

plt = sects.get(".plt.sec") or sects.get(".plt")

# Resolve PLT/GOT names: parse .rela.plt -> got slot -> symbol name
got_name = {}  # got addr -> symbol name
for sec in elf.iter_sections():
    if isinstance(sec, RelocationSection) and "plt" in sec.name:
        symtab = elf.get_section(sec["sh_link"])
        for r in sec.iter_relocations():
            sym = symtab.get_symbol(r["r_info_sym"])
            got_name[r["r_offset"]] = sym.name

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

out = []
def p(*a):
    out.append(" ".join(str(x) for x in a))


# Build a map: plt stub address -> name, by scanning plt.sec for jmp [rip+x]
plt_name = {}
if plt:
    pd = plt.data(); pa = plt["sh_addr"]
    for i in md.disasm(pd, pa):
        if i.mnemonic in ("jmp", "bnd jmp") and i.operands:
            op = i.operands[-1]
            if op.type == 3 and op.mem.base == 19:  # rip-relative (X86_REG_RIP)
                tgt = i.address + i.size + op.mem.disp
                if tgt in got_name:
                    # plt stub starts 0x10-aligned typically; record stub head
                    stub = i.address & ~0xf
                    plt_name[stub] = got_name[tgt]
                    plt_name[i.address] = got_name[tgt]


# Disassemble .text, annotate calls to plt
p("\n=== .text disasm (annotated) ===")
insns = list(md.disasm(text_data, text_addr))
for i in insns:
    ann = ""
    if i.mnemonic == "call" and i.operands and i.operands[0].type == CS_OP_IMM:
        tgt = i.operands[0].imm
        if tgt in plt_name:
            ann = f"   ; -> {plt_name[tgt]}"
    # flag indirect jmp (dispatch)
    if i.mnemonic == "jmp" and i.operands and i.operands[0].type != CS_OP_IMM:
        ann = "   ; *** INDIRECT JMP (vm dispatch?) ***"
    p(f"  {i.address:#06x}: {i.mnemonic:<7} {i.op_str}{ann}")

Path("/tmp/chal_full.txt").write_text("\n".join(out))
print("wrote /tmp/chal_full.txt lines:", len(out))
print("plt_name count:", len(plt_name))
