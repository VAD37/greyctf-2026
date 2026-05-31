# Playbook — forensics

> Attack ladder for forensics/stego. Tools: `docs/vendor/shop.md` (Forensics/Stego). Always identify the file first.

## Open with
```
file ./artifact; exiftool ./artifact; binwalk ./artifact
xxd ./artifact | head; strings -n6 ./artifact | grep -iE 'grey\{|flag|password'
```
`binwalk -e` to auto-extract embedded files; check magic bytes vs extension.

## Type → approach → tool

| artifact | first moves | tool |
|---|---|---|
| **pcap / pcapng** | follow TCP/HTTP streams, export objects, check DNS/ICMP exfil, creds | **tshark**/wireshark (want), `tcpflow` |
| **disk / fs image** | mount or carve, recover deleted, check slack | `foremost`, `testdisk`, autopsy |
| **memory dump** | profile, pslist, cmdline, filescan, dump procs | `volatility3` |
| **PNG/BMP** | LSB stego, chunk anomalies, dimension crop | `zsteg`, `stegsolve`, pngcheck |
| **JPEG** | appended data, EXIF, embedded w/ passphrase | `steghide`, exiftool, binwalk |
| **WAV/audio** | spectrogram (text in spectrum), LSB, DTMF | sonic-visualiser/Audacity, `steghide` |
| **zip/office** | known-plaintext / bkcrack, weak pw crack | `zip2john`+john, `bkcrack` |
| **PDF** | `pdf-parser`, objects, JS, hidden layers | pdfdetach, exiftool |
| **QR / barcode** | decode | `zbarimg` |
| **git repo** | `git log --all`, dangling commits, reflog | git |

## Gotchas
- Many tools are gem/dl install-later: `zsteg` (`gem install zsteg`), `stegsolve` (jar), `volatility3` (`uv add`) — grab before forensics.
- steghide needs a passphrase — try empty, challenge name, strings from the file.
- Check for **multiple** embedded layers (binwalk one level at a time).
- Spectrogram flags: look at full frequency + time range, not just default zoom.
- Don't ignore EXIF/metadata GPS/comment fields — easy flags hide there.
