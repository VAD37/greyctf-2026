# Pollution

- challenge_id: 25
- Category: Ezpz
- Points: 1000
- Challenge URL: https://ctfd.nusgreyhats.org/challenges#Pollution-25
- Submit: `POST /api/v1/challenges/attempt` body `{"challenge_id": 25, "submission": "grey{...}"}`
- Connection: whale docker (spawn per-team)
- Solved (initial scan): False

## Files
| name | sha256 | size |
|------|--------|------|
| dist-pollution.zip | 3cdc3d151bbae10ac9303ad9c23343cf5b20029fd515f606e18946362bb39cec | 15080 |

## Description (verbatim from CTFd)

The world is polluted with random prototypes and AI slop.

## Flag attempts
| timestamp | flag | verdict | submitted_by |
|-----------|------|---------|--------------|

## Solution
<!-- filled by submit on a `correct` verdict -->
- flag: (pending live capture — see solve/ATTEMPTS.md; exploit verified locally)
- method (one line): Unauth prototype pollution via POST /upload/users recursive merge() (item with __proto__ on the alice UPDATE branch) sets Object.prototype.userAutoCreateTemplate; logging in as a non-existent user makes passport.js authenticate() eval() that template literal (${require('./secrets').flag}) → creates a user whose bio = flag → read it from GET /profile.
- solve dir: `solve/` (exploit.py = the 3-step attack; run_remote.sh = whale spawn + run)
- solved at:
