#!/usr/bin/env python3
import re, os

D = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(D,"stream_full.txt"),"r",errors="replace").read()
OUT=os.path.join(D,"STRUCT.txt")
log=[]
def L(*a): s2=" ".join(str(x) for x in a); log.append(s2)

# all URLs (esp images / cdn / blob)
urls=sorted(set(re.findall(r'https?:\\?/\\?/[A-Za-z0-9._~:/?#\[\]@!$&\'()*+,;=%\\-]+', s)))
L("==== URLS ("+str(len(urls))+") ====")
for u in urls:
    L(u.replace('\\/','/'))

# image-ish references
L("\n==== IMAGE-ish keys ====")
for m in re.finditer(r'(screenshot|image_url|imageUrl|previewImage|\.png|\.jpg|\.jpeg|\.webp|blob:|data:image|/files/|/blob/|/image)', s, re.I):
    i=m.start()
    L(repr(s[max(0,i-50):i+90]))

# find type/role markers for messages
L("\n==== message-ish tokens ====")
for m in re.finditer(r'"(input_text|output_text|computer_call|function_call|reasoning|tool_use|image|screenshot|assistant|user|developer|system|command|action|type|kind|role)"', s):
    i=m.start()
    L(repr(s[i:i+80]))

# typed text actions (computer use 'type' actions) - what the agent typed
L("\n==== typed/type_text ====")
for m in re.finditer(r'(type[_ ]?text|"text"\s*:\s*"|Type Text|keystroke|press)', s, re.I):
    i=m.start()
    L(repr(s[i:i+160]))

open(OUT,"w").write("\n".join(log)+"\n")
print("WROTE",OUT,"lines",len(log))
print("URLS:",len(urls))
