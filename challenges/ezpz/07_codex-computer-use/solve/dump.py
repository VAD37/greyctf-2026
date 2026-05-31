#!/usr/bin/env python3
import re
s = open('challenges/ezpz/07_codex-computer-use/solve/rsc_stream.txt','r',errors='replace').read()
out = []
def show(label, idx, before=120, after=600):
    out.append(f'==== {label} @ {idx} ====')
    out.append(s[max(0,idx-before):idx+after])

# all grey occurrences with context
for m in re.finditer(r'grey', s, re.I):
    show('grey', m.start(), 80, 200)
# all flag occurrences
for m in re.finditer(r'flag', s, re.I):
    show('flag', m.start(), 80, 200)
# trace object
i = s.find('"trace":{')
show('trace', i, 0, 4000)
# realtime token area
i = s.find('realtimeToken')
show('realtimeToken', i, 200, 400)
# any urls
urls = sorted(set(re.findall(r'https?://[A-Za-z0-9._~:/?#\[\]@!$&\'()*+,;=%-]+', s)))
out.append('==== URLS ====')
out.extend(urls)
# any /api or /s/.../ paths
paths = sorted(set(re.findall(r'/(?:api|s|trace|traces|events|stream)[A-Za-z0-9._/?=&%-]*', s)))
out.append('==== PATHS ====')
out.extend(paths[:200])
open('challenges/ezpz/07_codex-computer-use/solve/dump.out','w').write('\n'.join(out))
print('done', len(out))
