import socket
class Bot:
    def __init__(self,host='127.0.0.1',port=4000,timeout=60):
        self.s=socket.create_connection((host,port),timeout=timeout); self.s.settimeout(timeout); self.buf=b''
    def cmd(self,line):
        self.s.sendall((line+'\n').encode())
        while b'\n' not in self.buf:
            self.buf+=self.s.recv(4096)
        i=self.buf.index(b'\n'); out=self.buf[:i].decode(); self.buf=self.buf[i+1:]; return out
    def close(self): self.s.close()
