import socket, time, sys
s = socket.create_connection(("challs.nusgreyhats.org", 35567), timeout=120)
s.settimeout(120)
buf = b""
start = time.time()
try:
    while time.time() - start < 110:
        try:
            d = s.recv(4096)
        except socket.timeout:
            break
        if not d:
            break
        buf += d
        sys.stdout.write(d.decode(errors="replace")); sys.stdout.flush()
        if b"http" in buf.lower() and (b"\n" in buf[-3:] or b"min" in buf.lower()):
            time.sleep(1)
            try:
                d2 = s.recv(4096)
                if d2: buf += d2; sys.stdout.write(d2.decode(errors='replace'))
            except: pass
            break
except Exception as e:
    print("ERR", e)
open("solve/instance_spawn.txt","wb").write(buf)
print("\n=== LEN", len(buf))
