#!/usr/bin/env python3
import re, json
s = open('challenges/ezpz/07_codex-computer-use/solve/rsc_stream.txt','r',errors='replace').read()
res=[]
# exact flag-looking strings (not the literal placeholder)
for m in re.finditer(r'grey\\?\{([^}\\]{1,120})\\?\}', s):
    res.append(('GREYBRACE', m.group(0)[:140]))
# 'flag' word contexts trimmed to single line
for m in re.finditer(r'.{0,60}flag.{0,80}', s, re.I):
    seg=m.group(0).replace('\\n',' ')
    res.append(('FLAGCTX', seg[:160]))
# trace metadata
i=s.find('"trace":{'); j=i+8
depth=0;end=None
for k in range(j,len(s)):
    if s[k]=='{':depth+=1
    elif s[k]=='}':
        depth-=1
        if depth==0: end=k+1;break
obj=json.loads(s[j:end])
res.append(('META', json.dumps(obj['metadata'])))
res.append(('PREVIEW', str(obj.get('previewImageUrl'))))
res.append(('TITLE', obj.get('title')))
res.append(('USER', json.dumps(obj.get('user'))))
res.append(('COMMIT', json.dumps(obj.get('commitInfo'))))
with open('challenges/ezpz/07_codex-computer-use/solve/find.out','w') as f:
    for t,v in res:
        f.write(f'[{t}] {v}\n')
print('n',len(res))
for t,v in res[:40]:
    print(f'[{t}] {v}')
