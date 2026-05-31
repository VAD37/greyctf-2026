# spidr

- challenge_id: 27
- Category: Rev
- Points: 1000
- Challenge URL: https://ctfd.nusgreyhats.org/challenges#spidr-27
- Submit: `POST /api/v1/challenges/attempt` body `{"challenge_id": 27, "submission": "grey{...}"}`
- Connection: none
- Solved (initial scan): False

## Files
| name | sha256 | size |
|------|--------|------|
| dist-spidr.zip | a61643d62f861ed1a4b2c6ba3240d37b899013919c5cc5fabf437b0e87cfb571 | 362278 |

## Description (verbatim from CTFd)

AHHH SPIDERS!!! AND SO MANY OF THEM ;-;

## Flag attempts
| timestamp | flag | verdict | submitted_by |
|-----------|------|---------|--------------|

## Solution
<!-- filled by submit on a `correct` verdict -->
- flag: `grey{4022823573008984730}`
- method (one line): Unicorn-trace the fixed 9900-op invertible u64 chain (add/xor/imul-odd) in `tjlfs`, then invert from target 0x67696d65666c6167 ("gimeflag") via sub/xor/modinv-mod-2^64; verified against real binary.
- solve dir: `solve/`
- solved at: 2026-05-30
