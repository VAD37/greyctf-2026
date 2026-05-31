# Playbook — misc

> Catch-all: jails, scripting, encodings, "guessy". Read the prompt literally — misc rewards spotting the exact constraint.

## Open with
- Read the full description + any handout. Misc flags often hinge on one sentence.
- Identify sub-type: pyjail / shell-escape, encoding chain, custom protocol, logic puzzle, programming, AI/prompt.

## Sub-type → approach

| sub-type | approach | note |
|---|---|---|
| **pyjail** | escape sandbox → read flag/RCE | `().__class__.__bases__`, `__builtins__`, `breakpoint()`, audit-hook bypass; if `eval` filtered, use getattr chains / unicode |
| **shell jail** (rbash/restricted) | env tricks, `${IFS}`, `$0`, builtins, path abuse | `BASH_ENV`, wildcards |
| **encoding chain** | identify + peel layers | base64/32/85, hex, ROT, URL; `CyberChef`-style magic; look for `=` pad, charset |
| **esolang / cipher** | identify lang (brainfuck, whitespace, …), interpret | dcode.fr identifier |
| **programming / fast I/O** | script the interaction, beat the timer | pwntools `remote`, fast loop |
| **proof-of-work gate** | solve PoW to reach challenge | hashcash-style, read their format exactly |
| **AI / prompt-injection** | craft prompt to leak flag / bypass filter | jailbreak, system-prompt extraction |
| **QR/audio/visual misc** | decode (see forensics) | — |
| **"guess"-ish** | check title/author hints, OSINT the theme | timebox — don't sink hours |

## pyjail quick refs
```python
# no builtins:  ().__class__.__base__.__subclasses__()  → find os/subprocess
# read file:    open('flag.txt').read()   or  __import__('os').system('sh')
# filtered dots: getattr(x,'attr')         ; chr()/unicode escapes for blocked chars
```

## Gotchas
- Identify the encoding before brute-decoding — wrong layer order wastes time.
- Interaction/timer challenges: automate with pwntools, don't type by hand.
- Timebox pure-guess challenges; pivot to cheaper flags (solve-order is cheapest-first).
