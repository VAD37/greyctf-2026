# Codex Computer Use

- challenge_id: 29
- Category: Ezpz
- Points: 1000
- Challenge URL: https://ctfd.nusgreyhats.org/challenges#Codex Computer Use-29
- Submit: `POST /api/v1/challenges/attempt` body `{"challenge_id": 29, "submission": "grey{...}"}`
- Connection: none
- Solved (initial scan): False

## Files
| name | sha256 | size |
|------|--------|------|
<!-- no attachments -->

## Description (verbatim from CTFd)

Look at what my agent can [do](https://traces.com/s/jn7c59d3c3e847cwmdctga3z5d87h8mn) with computer use. The future is now!!

## Flag attempts
| timestamp | flag | verdict | submitted_by |
|-----------|------|---------|--------------|

## Notes
- BLOCKED offline. No attachments, no local files/extracted, no flag.txt. Flag lives only
  inside the remote traces.com computer-use agent trace (link in description) — sandbox has
  no network, so it cannot be fetched. Submission pending network.
- Method when online: open https://traces.com/s/jn7c59d3c3e847cwmdctga3z5d87h8mn, expand all
  agent steps, grep the loaded trace JSON / DOM for `grey{` (flag appears in the agent's
  computer-use tool output / screenshots). See solve/ATTEMPTS.md.

## Solution
<!-- filled by submit on a `correct` verdict -->
- flag:
- method (one line): inspect remote traces.com agent trace for grey{...} (needs network)
- solve dir: `solve/`
- solved at:
