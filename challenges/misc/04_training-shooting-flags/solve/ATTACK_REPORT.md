# Attack Report — Training Shooting Flags (misc, 1000pts)

> Possible-attacks plan written BEFORE solving. CTF, not audit. Cheapest flag-grab first.

## Target

- Single artifact: `files/extracted/dist-training_shooting_flags/main.bit` (582369 B).
- **Lattice ECP5 FPGA bitstream.** Header: `Part: LFE5U-25F-6CABGA256` (ECP5-25F, CABGA256 pkg).
- No nc, no board. Flag derived from design logic / embedded data → 100% static RE.
- Story: GreyMecha/Army "Shooting Formation" — design checks input formation vs secret, "reveals part" only when right.

## Confirmed smells (static)

- Only non-header ASCII run = `TEA{` at file offset `0x43168` (274792 dec).
  - bytes: `54 45 41 7b 80 00 34 81 ff 00` — sits inside config frames (`ff` byte = ECP5 frame separator).
  - `TEA{` = either flag wrapper used inside design, OR pointer to **TEA (Tiny Encryption Algorithm)** cipher.
- No raw `grey{` in file (flag is computed/encrypted, not plaintext).

## Possible attacks (ranked, cheapest first)

### A1 — Unpack config, dump BRAM/LUT init (PRIMARY)
`ecpunpack main.bit main.config` → text config of tiles/LUTs/BRAM.
- `ecpbram` / pytrellis to extract BRAM initialisation words → secret constants + ciphertext.
- Read LUT init bits to recover the compare/cipher datapath.
- conf **M**, ~60-120 min. Tool: prjtrellis (`fpga-trellis` apt pkg).

### A2 — Full decompile to Verilog
VoidMercy `Lattice-ECP5-Bitstream-Decompiler` → netlist/Verilog → read cipher + constants directly, simulate.
- conf **M**, ~120 min. Heavier; use only if A1 config is unreadable.

### A3 — Treat TEA region as ciphertext, brute/invert
Extract bytes near `0x43168`, assume TEA with standard delta `0x9E3779B9`, recover key from BRAM (A1), invert TEA → flag.
- conf **L**, ~60 min. Quick sanity check; depends on A1 giving the key.

### A4 — yosys read + analysis
After A1/A2 produce netlist, `yosys` to flatten/simulate the FSM ("formation" state machine), feed candidate inputs, observe flag-reveal path.

## Toolchain (apt, Mint 22.3 / Ubuntu 24.04)

```
fpga-trellis            # ecpunpack, ecppack, ecpbram
fpga-trellis-database   # ECP5 chip DB
python3-pytrellis       # pytrellis lib (BRAM/LUT extraction in python)
nextpnr-ecp5            # place&route (for round-trip / netlist work)
yosys                   # synthesis / netlist analysis
```

## What to try first

1. `ecpunpack main.bit main.config` — text dump.
2. grep config for BRAM data words + LUT init near the TEA region.
3. pytrellis script → list all BRAM inits, all non-trivial LUT inits.
4. If TEA confirmed: pull key+ct, invert with delta `0x9E3779B9`, 32 rounds.

## Findings log

**2026-05-30 — tools installed + unpacked.**
- Installed apt: `fpga-trellis fpga-trellis-database python3-pytrellis nextpnr-ecp5 yosys`. DB `/usr/share/trellis/database`.
- `ecpunpack main.bit main.config` → OK (3811 lines, `solve/main.config`).
- Device `LFE5U-25F`. 68 PLC2 tiles, **273 LUT4 INITs** (`solve/luts.txt`), **NO BRAM**, FFs present → sequential.
- IO: ~34 inputs (LVCMOS25), ~8 outputs (SSTL18_II). Input = formation, outputs = reveal.
- LUT clusters cols C10–C20 + C35–C41, rows R2–R5. Regular INIT patterns = comparator/parity tree.

**KILLED A3 (TEA):** `grep TEA main.config` → 0. `TEA{` lives only in raw frame bytes, NOT logical config. No EBR → no ciphertext. A3 dead. (also kills `ecpbram`, A1's BRAM step.)

**Revised primary = netlist reconstruction:**
- VoidMercy decompiler cloned `solve/decomp/`, DB symlinked. Running BLOCKED by auto-classifier (untrusted external code) → awaiting user OK.
- Fallback: parse `main.config` (arcs + LUT INIT) → boolean net in python → SAT for satisfying formation input → ASCII → flag.
