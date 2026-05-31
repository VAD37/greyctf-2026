#!/usr/bin/env python3
import sys
from pathlib import Path
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from capstone import Cs, CS_ARCH_X86, CS_MODE_64, CS_OP_IMM

lo = int(sys.argv[1], 0); hi = int(sys.argv[2], 0)
outf = sys.argv[3] if len(sys.argv) > 3 else "/tmp/range.txt"

BASE = Path(__file__).resolve().parent.parent
CHAL = BASE / "files/extracted/dist-3d-maze/chal"
elf = ELFFile(open(CHAL, "rb"))
text = elf.get_section_by_name(".text")
ta = text["sh_addr"]; td = text.data()

got_name = {}
for sec in elf.iter_sections():
    if isinstance(sec, RelocationSection) and "plt" in sec.name:
        symtab = elf.get_section(sec["sh_link"])
        for r in sec.iter_relocations():
            got_name[r["r_offset"]] = symtab.get_symbol(r["r_info_sym"]).name

md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True
plt_name = {}
plt = elf.get_section_by_name(".plt.sec") or elf.get_section_by_name(".plt")
if plt:
    for i in md.disasm(plt.data(), plt["sh_addr"]):
        if i.mnemonic.endswith("jmp") and i.operands:
            op = i.operands[-1]
            if op.type == 3 and op.mem.base == 19:
                tgt = i.address + i.size + op.mem.disp
                if tgt in got_name:
                    plt_name[i.address & ~0xf] = got_name[tgt]
                    plt_name[i.address] = got_name[tgt]

# slice
start_off = lo - ta
data = td[start_off: hi - ta]
lines = []
for i in md.disasm(data, lo):
    ann = ""
    for op in i.operands:
        if op.type == CS_OP_IMM and op.imm in plt_name:
            ann = f"   ; -> {plt_name[op.imm]}"
    if i.mnemonic == "call" and i.operands and i.operands[0].type == CS_OP_IMM:
        t = i.operands[0].imm
        if t in plt_name: ann = f"   ; -> {plt_name[t]}"
        else: ann = f"   ; -> sub_{t:x}"
    if "jmp" in i.mnemonic and i.operands and i.operands[0].type != CS_OP_IMM:
        ann = "   ; *** INDIRECT JMP ***"
    lines.append(f"{i.address:#06x}: {i.mnemonic:<8} {i.op_str}{ann}")
Path(outf).write_text("\n".join(lines) + "\n")
print(f"wrote {outf} {len(lines)} insns {lo:#x}-{hi:#x}")
