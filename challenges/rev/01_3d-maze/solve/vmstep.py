import os,pty,time,select,re,sys
PATH=sys.argv[1] if len(sys.argv)>1 else "wdsdsdsodsdsddssls"
CHAL="/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/files/extracted/dist-3d-maze"
# Single-step the win() VM dispatch: break at 0x14fe (fetch byte) log code byte + data/out ptrs.
gdb=r'''set pagination off
set $b=0x555555554000
break *($b+0x14cc)
commands
 silent
 printf "WINSTART\n"
 cont
end
break *($b+0x14fe)
commands
 silent
 set $vm=*(unsigned long*)($b+0x5048)
 printf "FETCH code=0x%lx byte=%d data=0x%lx out=0x%lx\n", *(unsigned long*)($b+0x5050)-$vm, *(unsigned char*)(*(unsigned long*)($b+0x5050)), *(unsigned long*)($b+0x5040)-$vm, *(unsigned long*)($b+0x5058)-$vm
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
open("/tmp/vs.gdb","w").write(gdb)
pid,fd=pty.fork()
if pid==0:
    os.chdir(CHAL); os.environ["TERM"]="xterm"
    os.execv("/usr/bin/gdb",["gdb","-q","-nx","-batch","-x","/tmp/vs.gdb","./chal"]); os._exit(1)
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
drain(2.0)
try:os.close(fd)
except:pass
try:os.waitpid(pid,0)
except:pass
t=buf.decode("latin1")
out=[ln for ln in t.splitlines() if ln.startswith(("WINSTART","FETCH","PUTC"))]
open("/media/vad/Work2/hackathon/greyctf-2026/challenges/rev/01_3d-maze/solve/vmstep_out.txt","w").write("\n".join(out))
print("lines",len(out))
