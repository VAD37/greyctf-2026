import os,pty,time,select,re,sys
PATH=sys.argv[1] if len(sys.argv)>1 else "wdsdsdsodsdsddssls"
CHAL="/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/files/extracted/dist-3d-maze"
# loop head 0x14ec; log byte fetched (the op) and op=byte-5 and the computed target idx.
gdb=r'''set pagination off
set $b=0x555555554000
break *($b+0x14cc)
commands
 silent
 printf "WINSTART\n"
 cont
end
break *($b+0x14ec)
commands
 silent
 set $vm=*(unsigned long*)($b+0x5048)
 set $cp=*(unsigned long*)($b+0x5050)
 printf "LOOP cp=0x%lx byte=%d\n", $cp-$vm, *(unsigned char*)$cp
 cont
end
break *($b+0x1aaf)
commands
 silent
 printf "VMEXIT\n"
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
open("/tmp/vs2.gdb","w").write(gdb)
pid,fd=pty.fork()
if pid==0:
    os.chdir(CHAL); os.environ["TERM"]="xterm"
    os.execv("/usr/bin/gdb",["gdb","-q","-nx","-batch","-x","/tmp/vs2.gdb","./chal"]); os._exit(1)
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
drain(2.5)
try:os.close(fd)
except:pass
try:os.waitpid(pid,0)
except:pass
t=buf.decode("latin1")
out=[ln for ln in t.splitlines() if ln.startswith(("WINSTART","LOOP","VMEXIT","PUTC"))]
open("/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/solve/vmstep2_out.txt","w").write("\n".join(out))
print("lines",len(out))
