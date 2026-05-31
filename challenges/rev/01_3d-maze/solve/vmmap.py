import os,pty,time,select,re,sys
PATH=sys.argv[1] if len(sys.argv)>1 else "wdsdsdsodsdsddssls"
CHAL="/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/files/extracted/dist-3d-maze"
# Dump OUT buffer (emit bytes) at win entry, and each PUTC. Map emit->out.
gdb=r'''set pagination off
set $b=0x555555554000
break *($b+0x14cc)
commands
 silent
 set $vm=*(unsigned long*)($b+0x5048)
 printf "OUTBUF "
 set $i=0
 while $i<30
  printf "%d ", *(unsigned char*)($vm+0x100+$i)
  set $i=$i+1
 end
 printf "\n"
 cont
end
break *($b+0x154d)
commands
 silent
 printf "PUTC %d\n", $edi
 cont
end
run
'''
open("/tmp/vm.gdb","w").write(gdb)
pid,fd=pty.fork()
if pid==0:
    os.chdir(CHAL); os.environ["TERM"]="xterm"
    os.execv("/usr/bin/gdb",["gdb","-q","-nx","-batch","-x","/tmp/vm.gdb","./chal"]); os._exit(1)
import fcntl,termios,struct
fcntl.ioctl(fd,termios.TIOCSWINSZ,struct.pack("HHHH",50,200,0,0))
buf=b""
def drain(t):
    global buf
    e=time.time()+t
    while time.time()<e:
        r,_,_=select.select([fd],[],[],0.05)
        if r:
            try:d=os.read(fd,65536)
            except OSError:return
            if not d:return
            buf+=d
drain(1.6); os.write(fd,b"\n"); drain(0.5)
for c in PATH: os.write(fd,c.encode()); drain(0.09)
drain(1.3)
for _ in range(3): os.write(fd,b"\n"); drain(0.2)
try:os.close(fd)
except:pass
try:os.waitpid(pid,0)
except:pass
t=buf.decode("latin1")
ob=re.search(r'OUTBUF ([\d ]+)',t)
emit=[int(x) for x in ob.group(1).split()] if ob else []
putc=[int(x) for x in re.findall(r'PUTC (\d+)',t)]
print("EMIT:",emit)
print("PUTC:",putc)
print("EMIT chars:","".join(chr(c) if 32<=c<127 else '.' for c in emit))
print("PUTC chars:","".join(chr(c) if 32<=c<127 else '.' for c in putc))
