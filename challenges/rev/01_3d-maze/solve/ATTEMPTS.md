# 3d-maze (rev, id10) — ATTEMPTS / FULL RE (win()-VM port is the last mechanical step)

## Status: ARCHITECTURE FULLY REVERSED + emit formula live-verified. NOT captured: the printed
flag. Blocker = (a) recurring harness infra failure (Bash/Read return EMPTY for long stretches;
several of my Write/edits silently reverted), and (b) the win()-VM stack-op arities (op35/36/37
shuffles) need a couple more disasm passes to port exactly. A healthy session finishes in minutes.

## ARCHITECTURE (CONFIRMED via static disasm + live gdb-LAUNCH traces; image base 0x0, PIE base 0x555555554000)
`chal` = ncurses maze + a stack-VM run only inside win(). gdb ATTACH blocked (ptrace_scope=1);
use gdb-as-LAUNCHER (`gdb ./chal`) or PTY-drive `./chal` (both work; see solve/*.py).

### Globals: 0x5010 x 0x5011 y 0x5012 z 0x5013 lever 0x5014 score(dword). init x=y=z=7 lever=0x43.
 0x5030 maze.txt(31^3) | 0x5038 poolptr (into pool.bin, +=4/emit) | 0x5048 vm.bin
 0x5050 = vm.bin+0x98 = VM CODE ptr | 0x5058 = vm.bin+0x100 = VM OUT (emit) buffer | 0x5040 = VM DATA stack.

### Move (loop 0x1f3f; key=wgetch-0x61; jt 0x31d8): w:y-1 s:y+1 a:x-1 d:x+1 o:z-1 l:z+1 (q quit)
 move() 0x1b53: idx=(2z+1)*961+(2y+1)*31+(2x+1); passable iff maze[avg(idx_a,idx_b)]==' '.
 dir code w0 s1 a2 d3 (o/l = z = NO emit). EMIT (horizontal only):
   emit = (pool[4*step + code] + lever) & 0xff   [LIVE-VERIFIED: mv1 pool[0]=1->1; mv2 pool[7]=1->1]
   then score+=emit; *OUT++=emit; lever=0; poolptr+=4. After move: 'F'->win(); '.'-> lever=0x43.

### win() 0x14cc: puts("You win!") then VM (dispatch 0x14ec: op=*code++ -5; if op>0x62 exit; jt 0x3028).
 Handlers (BYTE -> sem; DATA=0x5040 grows UP, top=*DATA; CODE=0x5050; OUT=0x5058):
   0x20 putchar: print *DATA; DATA-=1        (pop+print)
   0x43 'C'   : DATA+=1; *DATA=*CODE++        (push code immediate)
   0x67 'g'   : DATA-=1                       (pop/discard)
   0x36 '6' / 0x37 '7' / 0x35 '5' : stack shuffles reading code immediates / dup-swap
                (EXACT arity: re-read solve/handlers_resolved.txt — op35 reads 2 data slots & 1 imm,
                 op36 reads 1 imm pushes twice, op37 reads 3 — finish porting these)
   0x4c 'L'   : a=pop|pop<<8; push vm.bin[a]  (16-bit indexed load)   0x53 'S' indexed store
   0x2b + 0x2d - 0x2a * 0x26 & 0x5e ^   (pop2 push1)
   0x05 / 0x06 / 0x07 : read one OUT(emit) byte -> push (06/07 are conditional variants,
                see 0x1a3d cmp0 / 0x1a8e cmp!=0)    else -> exit 0x1aaf.
 CODE (vm.bin+0x98, 104 bytes) = the flag program:
   43 00 36 36 36 43 01 4c 37 2b 37 37 36 43 01 4c 37 36 36 2b 36 43 ff 35 2d 37 36 37 36 2b 36
   06 06 35 36 2b 35 05 f5 67 2b 2b 2b 37 37 43 01 2b 36 07 d1 43 cc 2b 5e 07 05 43 76 5e 06 01
   00 43 00 43 06 43 01 4c 43 07 43 01 4c 36 37 5e 37 36 43 00 4c 37 5e 36 06 0a 36 20 35 43 01
   2b 37 37 05 e9 43 0a 20 67 67 67
 LIVE TRACE (solve/vmstep2_out.txt): on the BFS emit stream the VM enters inner loop cp 0xb4..0xbd
   (push54; readOUT 06; readOUT; op35 cmp0 at 0xbc; op05 0xbd) iterating once per OUT byte, never
   reaching putchar (0xf1) -> prints NOTHING. => win() prints grey{...} ONLY for the CORRECT emit
   stream. (The flag is NOT the raw emit bytes; you MUST run this VM. Earlier guess was wrong.)

## MAZE: maze.txt = 31^3 = literal RED HERRING (3D). z-axis ZERO walls (3150 open); x 1453 '#', y 1487.
 2D wall maze + free z "phase" (Miegakure). cells 15^3, START (7,7,7), F (14,14,7), 96 '.', 1 'F'.
 BFS path = wdsdsdsodsdsddssls (16 horiz emits) reaches F but VM prints nothing (herring path).
 pool step recs [w,s,a,d]: rec0 [1,3,0,2] rec1 [2,0,3,1] rec2.. random. Per-step reachable chars
 (lever 0/0x43) include lowercase (step2 y, step5 u, step7 m, step9 n, step10 g/x/y/z, step13 y/j)
 -> [a-z_] flag chars are producible through the VM transform.

## NEXT STEPS (resume on healthy tools)
1. Finish porting win()-VM (solve/full_solver.py has a near-complete port; fix op35/36/37 arities
   from solve/handlers_resolved.txt). Validate: BFS emit -> loops/no output (matches live).
2. DFS maze paths to F (emit=pool[4*step+code]+lever); run ported VM per candidate; keep path whose
   VM putchar output = /grey\{[a-z_]+\}/. Reconstruct key string. (small search: 2D walls + free z.)
3. VERIFY: solve/wintrace.py <keys> (gdb-launch, logs PUTC) and solve/drive_real.py <keys>
   (stdout flag after "You win!"). Run twice; identical. Both scripts WORK.
 ALT (if VM port stays fiddly): drive the REAL binary while searching — PTY-feed candidate key
   strings to ./chal and grep stdout for grey{...} (drive_real.py already does this).

## WORKING solve/ scripts: emu.py, drive_real.py, wintrace.py, vmstep2.py (full VM FETCH trace),
 etrace3.py (live emit formula), full_solver.py (VM port+BFS), handlers_resolved.txt (handler disasm),
 decode_all.py (key table+pool), invert.py (per-step char options).

## Constants: w:y-1 s:y+1 a:x-1 d:x+1 o:z-1 l:z+1 ; emit codes w0 s1 a2 d3 ; o/l no emit.
 emit=(pool[4*step+code]+lever)&0xff ; lever 0x43 init/on '.', else 0 after each emit.
 START (7,7,7) ; F (14,14,7) ; flag printed by win()-VM after "You win!" ; format /grey\{[a-z_]+\}/.
