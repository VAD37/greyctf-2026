"""Minimal Minecraft RCON client (Source RCON protocol)."""
import socket, struct, itertools

class Rcon:
    def __init__(self, host="127.0.0.1", port=25575, password="ctf", timeout=120):
        self.s=socket.create_connection((host,port),timeout=timeout)
        self.s.settimeout(timeout)
        self._id=itertools.count(1)
        self._auth(password)
    def _send(self, typ, body):
        rid=next(self._id)
        pkt=struct.pack("<ii",rid,typ)+body.encode()+b"\x00\x00"
        self.s.sendall(struct.pack("<i",len(pkt))+pkt)
        return rid
    def _recv_one(self):
        ln=struct.unpack("<i",self._readn(4))[0]
        data=self._readn(ln)
        rid,typ=struct.unpack("<ii",data[:8])
        body=data[8:-2]
        return rid,typ,body.decode("utf-8","replace")
    def _readn(self,n):
        buf=b""
        while len(buf)<n:
            c=self.s.recv(n-len(buf))
            if not c: raise ConnectionError("closed")
            buf+=c
        return buf
    def _auth(self,pw):
        rid=self._send(3,pw)
        r,t,b=self._recv_one()
        if r==-1: raise RuntimeError("auth failed")
    def cmd(self, command):
        rid=self._send(2,command)
        # use a sentinel to flush multipacket responses
        sentinel=self._send(0,"")
        out=[]
        while True:
            r,t,b=self._recv_one()
            if r==sentinel:
                break
            out.append(b)
        return "".join(out)
    def close(self): 
        try: self.s.close()
        except: pass

if __name__=="__main__":
    import sys,time
    r=Rcon()
    print(repr(r.cmd("list")))
    print(repr(r.cmd("seed")))
