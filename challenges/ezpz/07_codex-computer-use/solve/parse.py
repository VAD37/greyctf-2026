#!/usr/bin/env python3
"""Reconstruct traces.com RSC stream from the trace page HTML and hunt for the flag."""
import re, json, sys

HTML = 'challenges/ezpz/07_codex-computer-use/solve/trace_page.html'
OUT_STREAM = 'challenges/ezpz/07_codex-computer-use/solve/rsc_stream.txt'
OUT_LOG = 'challenges/ezpz/07_codex-computer-use/solve/parse.log'

log_lines = []
def log(*a):
    s = ' '.join(str(x) for x in a)
    log_lines.append(s)

html = open(HTML, 'r', errors='replace').read()
log('html len', len(html))

pushes = re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)', html, re.S)
log('pushes', len(pushes))
stream = ''
for p in pushes:
    try:
        stream += json.loads(p)
    except Exception:
        stream += p[1:-1]
open(OUT_STREAM, 'w').write(stream)
log('stream len', len(stream))

# direct flag patterns in stream and html
for name, txt in [('stream', stream), ('html', html)]:
    for pat in [r'grey\{[^}]{0,200}\}', r'grey\\u007b.{0,200}?\\u007d']:
        for m in re.findall(pat, txt):
            log('FLAG-HIT', name, repr(m))

# locate trace object + interesting keys
for key in ['"trace":{', '"initialTrace"', '"events"', '"steps"', '"messages"', '"output"', 'flag', 'grey', '/api/', 'realtimeToken', 'externalId', 'opengraph']:
    i = stream.find(key)
    log(f'key {key!r} at', i)

# dump trace object context
i = stream.find('"trace":{')
if i >= 0:
    log('--- trace ctx (4000) ---')
    log(stream[i:i+4000])

open(OUT_LOG, 'w').write('\n'.join(log_lines))
print('WROTE', OUT_LOG, 'lines', len(log_lines))
