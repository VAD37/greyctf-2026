# Playbook — osint

> Find real-world info from a given seed (image, username, name, coords). Browser-first via Playwright MCP. Stay legal; passive only.

## Open with
- Pin the seed: exact handle, image, phrase, timestamp, or place. Extract everything from it before searching.
- `exiftool` any image — GPS, camera, software, timestamps are free wins.

## Seed → moves → resource

| seed | moves | resource |
|---|---|---|
| **photo / landmark** | reverse image search; identify landmark/signage/language; shadow direction → rough time | Google/Yandex/Bing images, Google Lens |
| **GPS / coords in EXIF** | map it, Street View around for the exact spot | Google Maps/Earth, Street View |
| **username / handle** | enumerate across platforms; pivot to real name/email | sherlock, whatsmyname, manual |
| **real name** | socials, LinkedIn, public records, gravatar | search engines, dorks |
| **email** | breach data, gravatar, account links | hunter, haveibeenpwned (info only) |
| **domain / site** | whois, DNS, subdomains, wayback history, cert logs | crt.sh, wayback machine, `dig` |
| **company / org** | employees, tech stack, press, repos | github org, job posts |
| **tweet/post** | exact time (zone), replies, quoted media, geotag | platform advanced search |

## Search dorks
```
site: filetype: intitle: inurl: "exact phrase" -exclude
```
Wayback Machine for deleted pages; crt.sh for subdomains via cert transparency.

## Gotchas
- Answer format: OSINT flags are often the literal answer wrapped (`grey{The_Place_Name}`) — match their stated format exactly (underscores, case).
- Verify with a second source before submitting — wrong guesses burn the rate budget.
- Passive recon only; don't contact people or touch out-of-scope systems.
- Timebox: OSINT can rabbit-hole — re-read the prompt for the precise asked-for fact.
