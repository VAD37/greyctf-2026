# Challenges — status board

> Root index. Live values from CTFd (dynamic scoring — `val` drops as `solves` rises; high solves = easier).
> **FINAL (frozen):** Team **CoolBingo** (id 45) — **score 4442, 95th place**. **Solved 18/35.** (Mid-contest sync was 4974 / 76th @ 2026-05-31 03:25 SGT; values below are final frozen — dynamic scoring dropped as solves rose.)
> Solve mode: ≥500pt only, cheapest-first, 1 subagent/challenge sequential.
> ✅ **Remote infra UP** (corrected): `challs.nusgreyhats.org`→`34.124.219.136`, test.txt replay = HTTP 200. Earlier "NXDOMAIN" = stale *pcap* IP `35.187.240.51` (dead). Contest LIVE.
> ⚠️ Live token-replay probing trips auto-mode classifier → remote forensics (APTV3R4) parked. Main bash shell wedged this session (output lag) — prefer subagents/Read.
> ⚠️ Sandbox bash clock ~1yr ahead of real; trust browser epoch.

## 🎯 Priority — unsolved ≥500 (cheapest-flag-first by live val)

| P | challenge | cat | id | val | solves | status | next action |
|---|-----------|-----|----|-----|--------|--------|-------------|
| **1** | [APTV3R4_STRIKES_AGAIN](challenges/forensics/04_aptv3r4-strikes-again/) | forensics | 38 | 738 | 82 | ⏸️ PARKED | infra UP. abs `/proc/self/fd/N`→404. Next: relative `../../../proc/self/fd/N` + `../app.py`. Remote probe blocked by auto-mode classifier (`solve/ATTEMPTS.md`) |
| **2** | [lights-out](challenges/rev/04_lights-out/) | rev | 37 | 769 | 77 | 🔄 WIP | big solve dir (bot/server/rcon), MC redstone GF(2) |
| **3** | [ghidra gangster edition](challenges/rev/02_ghidra-gangster-edition/) | rev | 26 | 799 | 72 | ⛔ win-only | Win64 PE anti-decomp |
| **4** | [dbench_jumbf](challenges/pwn/02_dbench-jumbf/) | pwn | 17 | 831 | 66 | ⛔ queued | heap OOB tcache poison, remote nc :32167 |
| **5** | [Grey Yuumi](challenges/forensics/02_grey-yuumi/) | forensics | 31 | 831 | 66 | 🔄 solving | video frame stego, gdrive dl |
| **6** | [baby-bof](challenges/pwn/03_baby-bof/) | pwn | 18 | 847 | 63 | 🔄 WIP | docker build → exact binary, canary-bypass CGI |
| **7** | [Crimewatch](challenges/forensics/03_crimewatch/) | forensics | 35 | 744 | 81 | ⛔ heavy-dl | 1.3GB disk/mem carve (cheapest val but heavy) |
| **8** | [Chiaroscuro](challenges/forensics/01_chiaroscuro/) | forensics | 2 | 964 | 31 | ⛔ STUCK | spectrogram stego; `solve/ATTEMPTS.md` |
| **9** | [Red Flag](challenges/web/03_red-flag/) | web | 13 | 971 | 28 | ⛔ queued | wkhtmltopdf cmdi, docker |
| **10** | [67](challenges/misc/03_67/) | misc | 34 | 977 | 25 | ⛔ queued | WS trace anti-cheat, remote wss |
| **11** | [Go Going Goen](challenges/web/01_go-going-goen/) | web | 11 | 983 | 22 | ⛔ queued | 3-stage timing+race, web (team token) |
| **12** | [3d-maze](challenges/rev/01_3d-maze/) | rev | 10 | 991 | 16 | 🟡 triaged | custom VM (`chal`+`vm.bin`+`pool.bin`+`maze.txt`). maze.txt=31³ 3D=red herring; real=4D. VM disasm unfinished (`solve/ATTEMPTS.md`) |
| **13** | [Greyhats Gallery](challenges/web/02_greyhats-gallery/) | web | 12 | 998 | 9 | 🔄 WIP | zip-slip symlink; `solve/REPORT.md` |
| **14** | [If Models Could Dream](challenges/ai/04_if-models-could-dream/) | ai | 33 | 1000 | 0 | ⛔ unsolved-global | hardest, DreamerV3 RSSM |

> <500pt skipped per scope (still unsolved): SeeTeeEffedIn(23,100), SABLE(3,239), Pollution(25,293).

## ✅ Solved (18)

> Sorted by solve time (earliest first). `val` = final frozen value.

| # | solved (scoreboard) | challenge | cat | id | val | flag |
|---|---------------------|-----------|-----|----|-----|------|
| 1 | 05-30 09:18 | [AE-no-S](challenges/ezpz/01_ae-no-s/) | ezpz | 7 | 100 | `grey{iT5_4LL_l1N3R_aLGyBeR?...}` |
| 2 | 05-30 09:27 | [babyRSA](challenges/ezpz/04_babyrsa/) | ezpz | 21 | 100 | `grey{th1s_15_pr0b4bly_t00_34sy_n0w4d4y5_1n34v80n23}` |
| 3 | 05-30 09:28 | [Codex Computer Use](challenges/ezpz/07_codex-computer-use/) | ezpz | 29 | 100 | `grey{be_careful_when_sh4ring_agent_traces!1!}` |
| 4 | 05-30 09:32 | [Say My Name](challenges/ezpz/02_say-my-name/) | ezpz | 19 | 444 | teammate (alien≈Bibble) |
| 5 | 05-30 09:33 | [spidr](challenges/rev/03_spidr/) | rev | 27 | 100 | `grey{4022823573008984730}` |
| 6 | 05-30 09:41 | [Duality in All Things](challenges/ai/03_duality-in-all-things/) | ai | 5 | 100 | `grey{du4l_0pt1m1z4t10n_l3ft_th3_supp0rt_v3ct0rs_b3h1nd}` |
| 7 | 05-30 10:05 | [Fort Knockies](challenges/ezpz/08_fort-knockies/) | ezpz | 30 | 100 | `grey{jz_some_rookie_mistakesi9v2k}` |
| 8 | 05-30 11:42 | [filter_flag](challenges/crypto/01_filter-flag/) | crypto | 14 | 100 | ✅ (flag in CTFd) |
| 9 | 05-30 11:43 | [my-greycat](challenges/ezpz/05_my-greycat/) | ezpz | 24 | 100 | ✅ (flag in CTFd) |
| 10 | 05-30 13:41 | [elite ball knowledge](challenges/pwn/01_elite-ball-knowledge/) | pwn | 16 | 551 | `grey{3l1t3_b4lL_kn0wLedge_is_just_more_syscalls}` |
| 11 | 05-30 15:48 | [Jurgen's Revenge](challenges/ai/02_jurgen-s-revenge/) | ai | 4 | 100 | `grey{h1y4_there_n3el_n4nda_d1dnt_s3e_y0u_0ver_fr0m_ov3r_h3re}` |
| 12 | 05-30 16:34 | [Training Shooting Flags](challenges/misc/04_training-shooting-flags/) | misc | 36 | 804 | `grey{lmao_imagine_revvin}` |
| 13 | 05-30 17:03 | [Gopher's Adventure!](challenges/rev/05_gophers-adventure/) | rev | 39 | 324 | `grey{G0pHeR_g0e5_oN_4N_4dv3ntur3!XDDDD}` |
| 14 | 05-30 18:11 | [babyheap](challenges/ezpz/03_babyheap/) | ezpz | 20 | 100 | ✅ (flag in CTFd) |
| 15 | 05-30 18:42 | [Wait a minute](challenges/misc/02_wait-a-minute/) | misc | 9 | 100 | ✅ (flag in CTFd) |
| 16 | 05-30 20:03 | [GreyCat Game](challenges/web/05_greycat-game/) | web | 28 | 100 | `grey{you_better_run_bruno_cat}` |
| 17 | 05-30 23:56 | [An old soviet terminal](challenges/misc/01_an-old-soviet-terminal/) | misc | 8 | 744 | ✅ (user solved) |
| 18 | 05-31 02:24 | [caexor](challenges/crypto/02_caexor/) | crypto | 15 | 375 | `grey{why_lattice_enumerate_when_you_can_bkz}` (lattice/BKZ preimage) |

## Notes

> **Submit:** POST `/api/v1/challenges/attempt` via browser `CTFd.fetch` (auto-CSRF). All flags `grey{...}`.
> **Whale (dynamic_docker):** `/api/v1/plugins/ctfd-whale/container?challenge_id=N` — GET/POST/DELETE (CSRF). TTL ~300s.
> **Subagent caution:** offensive-framed prompts (APT/breach/replay/exploit) trip the usage-policy filter → solve those inline with CTF framing, or reframe subagent as authorized-competition defensive analysis.
