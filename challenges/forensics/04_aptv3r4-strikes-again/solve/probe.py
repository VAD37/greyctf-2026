#!/usr/bin/env python3
"""Quick structural probe of the pcap. Emits SHORT tokens only."""
import collections
from scapy.all import PcapReader, TCP, UDP, IP, Raw, DNS

PCAP = '/media/vad/Work2/hackathon/greyctf-2026/challenges/forensics/04_aptv3r4-strikes-again/files/dist-APTV3R4_STRIKES_AGAIN/artifact.pcap'

proto = collections.Counter()
loport = collections.Counter()
convs = collections.Counter()
dnsq = collections.Counter()
n = 0
http_like = 0
raw_bytes = 0
sample = []
for pkt in PcapReader(PCAP):
    n += 1
    if pkt.haslayer(TCP):
        t = pkt[TCP]
        lp = min(t.sport, t.dport)
        loport[lp] += 1
        proto['TCP'] += 1
        if pkt.haslayer(IP):
            ip = pkt[IP]
            key = tuple(sorted([(ip.src, t.sport), (ip.dst, t.dport)]))
            convs[key] += 1
        if pkt.haslayer(Raw):
            d = bytes(pkt[Raw].load)
            raw_bytes += len(d)
            if len(sample) < 6 and d[:4] in (b'GET ', b'POST', b'HTTP', b'PUT ', b'HEAD'):
                sample.append(d[:60])
    elif pkt.haslayer(UDP):
        u = pkt[UDP]
        proto['UDP'] += 1
        loport[min(u.sport, u.dport)] += 1
        if pkt.haslayer(DNS) and pkt[DNS].qd is not None:
            try:
                dnsq[pkt[DNS].qd.qname.decode(errors='replace')] += 1
            except Exception:
                pass
    else:
        proto['OTHER'] += 1

print('TOTAL', n)
print('RAWBYTES', raw_bytes)
for k, v in proto.most_common():
    print('PROTO', k, v)
for k, v in loport.most_common(10):
    print('LOPORT', k, v)
for k, v in convs.most_common(8):
    print('CONV', v, k)
for k, v in dnsq.most_common(15):
    print('DNS', v, k)
for s in sample:
    print('HTTP', s)
