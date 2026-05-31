# Say My Name

- challenge_id: 19
- Category: Ezpz
- Points: 1000
- Challenge URL: https://ctfd.nusgreyhats.org/challenges#Say My Name-19
- Submit: `POST /api/v1/challenges/attempt` body `{"challenge_id": 19, "submission": "grey{...}"}`
- Connection: none
- Solved (initial scan): False

## Files
| name | sha256 | size |
|------|--------|------|
<!-- no attachments -->

## Description (verbatim from CTFd)

A new alien has decided to challenge the players. His face can be found all over GreyCTF 2026. What is his name though? 



Note: Flag is lowercase

## Flag attempts
| timestamp | flag | verdict | submitted_by |
|-----------|------|---------|--------------|

## Solution
<!-- filled by submit on a `correct` verdict -->
- flag: UNKNOWN (BLOCKED — no network)
- method (one line): OSINT/guess — name = GreyCTF 2026 alien mascot (lowercase) read off live site branding; needs network, sandbox offline, no offline artifact ships the answer.
- solve dir: `solve/` (see `solve/ATTEMPTS.md` for resume steps)
- solved at:

## Notes
- No local files / no flag.txt. Requires reading the mascot's name off the live
  CTFd site imagery or external OSINT. Sandbox has no network (DNS + outbound
  down) -> BLOCKED. Submission pending network.
