# Fort Knockies

- challenge_id: 30
- Category: Ezpz
- Points: 1000
- Challenge URL: https://ctfd.nusgreyhats.org/challenges#Fort Knockies-30
- Submit: `POST /api/v1/challenges/attempt` body `{"challenge_id": 30, "submission": "grey{...}"}`
- Connection: none
- Solved (initial scan): False

## Files
| name | sha256 | size |
|------|--------|------|
<!-- no attachments -->

## Description (verbatim from CTFd)

hey i make a local password manager check it out



https://drive.google.com/file/d/174UqF92-AGfT6niJN-HcPQZsO7Xnfeer

## Flag attempts
| timestamp | flag | verdict | submitted_by |
|-----------|------|---------|--------------|

## Solution
<!-- filled by submit on a `correct` verdict -->
- flag: (not recovered — BLOCKED)
- method (one line): BLOCKED — no network + no local artifact; real challenge is a "local password manager" hosted on Google Drive (drive.google.com/file/d/174UqF92-AGfT6niJN-HcPQZsO7Xnfeer), never extracted locally; sandbox has no DNS/outbound so it cannot be downloaded.
- solve dir: `solve/` (see ATTEMPTS.md)
- solved at: (pending network — download Drive app, reverse the password-manager to recover stored secret/flag, then submit)

## Notes
- Despite the "port-knocking" triage hint, the verbatim CTFd description is a downloadable **local password manager** app (Google Drive). The flag is obtained by reverse-engineering that downloaded app/binary, NOT by knocking a live host.
- Blocker: `files/extracted/` does not exist and `files/` is empty; no offline artifact. Sandbox has no network to fetch the Drive file. Recovery impossible offline.
