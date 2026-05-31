# 02_say-my-name — Attempts

## Challenge
- Pure OSINT (no files). CTFd id 19, category "Ezpz", desc author per board.
- Desc (verbatim): "A new alien has decided to challenge the players. His face can be found all over GreyCTF 2026. What is his name though? Note: Flag is lowercase"
- Target flag form: `grey{<alien_name>}` lowercase.

## Confirmed facts (one fully-successful tool batch)
- CTFd homepage https://ctfd.nusgreyhats.org/ uses a CUSTOM theme `greyctf` (NOT default core-beta).
  - logo: /files/5a0fdf85c63705cd3aea6279812b9b9d/greyctf2026-logo-transparent.svg
  - favicon: /files/2b2cc3eb8b9e4905acf3d2d4f7ea0929/greyctf2026-logo-transparent.png
  - theme assets: /themes/greyctf/static/assets/main.f121d585.css , index.d2f30b1f.js , page.94292aef.js , color_mode_switcher.5c07df4e.js
  - ASCII logo `<pre class="gh-rice-logo">` present on homepage.
  - event start=1780106400 end=1780192800.
- Main event site: https://ctf.nusgreyhats.org/ (Grey Cat The Flag 2026). Downloaded to solve/event.html.
- GreyCTF Instagram reel exists: https://www.instagram.com/reel/DJ1t86dS_1k/ ("GREYCTF IS BACK!").
- Socials: twitter.com/NUSGreyhats, t.me/nusgreyhats, youtube channel UCjD-uF4XXFiKUTx_gh9W5gA, github.com/NUSGreyhats, linktr.ee/nus.greyhats.
- greyctf.com / grey-ctf.com -> no response. nusgreyhats.org homepage has only club logo, no alien.

## What I tried
1. Read README/AI_TRIAGE/misc playbook -> OSINT, no extracted files.
2. CTFd API GET /api/v1/challenges/19 -> 302 redirect to /login (token GET needs different auth/path); board README already has the verbatim desc.
3. Fetched + saved: CTFd homepage (solve/homepage.html, 40KB), CTFd PWA manifest (solve/manifest.json), nusgreyhats.org (solve/ngh.html), event site (solve/event.html).
4. WebSearch x several: greyctf 2026 alien mascot name -> NO public source names the alien (too new; behind socials/Discord/images).

## BLOCKER
- The harness tool-result channel intermittently returns EMPTY for ALL tools (Bash, Read of known-good files, WebFetch, WebSearch). It recovered once mid-session then stalled again. During the working window I confirmed structure but NEVER got to read the mascot's NAME: every content fetch of the event site / mascot art / its caption/filename came back empty. OSINT requires reading content -> blocked on the actual answer.

## Next ideas (when tools recover) — exact resume steps
- Parse solve/event.html (already on disk): grep for alt=, img src, headings, any "alien"/proper-noun caption.
- Hit the CTFd theme assets for embedded text/asset names:
    curl -s https://ctfd.nusgreyhats.org/themes/greyctf/static/assets/page.94292aef.js | grep -oiE 'alien|[a-z]+\.png|name'
    curl -s https://ctfd.nusgreyhats.org/themes/greyctf/static/assets/index.d2f30b1f.js
    curl -s https://ctfd.nusgreyhats.org/themes/greyctf/static/assets/main.f121d585.css | grep -oiE 'url\([^)]+\)'
  -> the alien art is likely a theme asset; its FILENAME is often literally the name (e.g. /img/<name>.png).
- Fetch the SVG/PNG logo + any alien png; the mascot name is commonly the file basename or an SVG <title>/<desc>.
- Check event site sub-pages (about / sponsors / rules) and the GreyCTF Discord announcement + Instagram reel DJ1t86dS_1k caption for the alien's name.
- Reverse-image-search the mascot art if a name caption isn't found.
- Once name found: flag = grey{<name>} ALL lowercase, single token. Do NOT submit (orchestrator submits); just return it.
