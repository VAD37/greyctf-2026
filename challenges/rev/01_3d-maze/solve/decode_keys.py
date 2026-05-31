from pathlib import Path
import struct
from elftools.elf.elffile import ELFFile
BASE=Path(__file__).resolve().parent.parent
D=BASE/"files/extracted/dist-3d-maze"
elf=ELFFile(open(D/"chal","rb"))
def read_vaddr(va,n):
    for s in elf.iter_sections():
        a=s["sh_addr"]; sz=s["sh_size"]
        if a<=va<a+sz and s["sh_type"]!="SHT_NOBITS":
            return s.data()[va-a:va-a+n]
jt=read_vaddr(0x31d8,0x16*4)
ents=struct.unpack("<22i",jt)
for i,e in enumerate(ents):
    print(chr(0x61+i), hex(0x31d8+e))
