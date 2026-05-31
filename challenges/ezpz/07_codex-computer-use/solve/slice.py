#!/usr/bin/env python3
import re, json
s = open('challenges/ezpz/07_codex-computer-use/solve/rsc_stream.txt','r',errors='replace').read()

# 1) flag contexts
with open('challenges/ezpz/07_codex-computer-use/solve/s_flag.txt','w') as f:
    for m in re.finditer(r'flag', s, re.I):
        i=m.start()
        f.write(f'--- @ {i} ---\n{s[max(0,i-200):i+300]}\n\n')

# 2) the grey{...} literal context
with open('challenges/ezpz/07_codex-computer-use/solve/s_grey.txt','w') as f:
    for m in re.finditer(r'grey\\?{', s, re.I):
        i=m.start()
        f.write(f'--- @ {i} ---\n{s[max(0,i-400):i+400]}\n\n')

# 3) trace object full
with open('challenges/ezpz/07_codex-computer-use/solve/s_trace.txt','w') as f:
    i=s.find('"trace":{')
    f.write(s[i:i+6000])

# 4) try to json-parse the trace object cleanly
i=s.find('"trace":{')
j=i+len('"trace":')
depth=0; end=None
for k in range(j,len(s)):
    c=s[k]
    if c=='{':depth+=1
    elif c=='}':
        depth-=1
        if depth==0:
            end=k+1; break
raw=s[j:end] if end else ''
with open('challenges/ezpz/07_codex-computer-use/solve/s_trace_obj.json','w') as f:
    f.write(raw)
print('trace obj len', len(raw))
try:
    obj=json.loads(raw)
    print('KEYS', list(obj.keys()))
    for k,v in obj.items():
        sv=json.dumps(v)[:120]
        print(f'  {k} = {sv}')
except Exception as e:
    print('json fail', e)
