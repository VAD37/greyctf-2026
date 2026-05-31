# Attempt log — Chiaroscuro

> Solver fail-log. Resumable record so a rerun / manual takeover starts warm.

- challenge: `challenges/forensics/01_chiaroscuro/`
- category / stack: forensics / audio stego — Python (uv: numpy/scipy/matplotlib/librosa/opencv)
- verdict: **unsolved**
- time spent: ~1 deep session

## File facts
- `files/dist-Chiaroscuro/painted_audio.wav` — RIFF WAVE PCM 16-bit, **stereo 48000 Hz, 7.44 s** (356997 samples/ch).
- RIFF clean: chunks `fmt `, `LIST(INFO)`, `data` only. No trailing bytes, no extra chunks, no appended data.
- INFO metadata: `INAM="Le clair se décale vers l'obscur. Seul le prélude fut repeint."`, `IGNR=piano`, `ICRD=33`, `ISFT=Lavf58.76.100` (FFmpeg-encoded).
- Channels: L peak 19935 ("clair"), R peak 13637 ("obscur"). NCC(L,R)=0.62 at ~0 lag (panned stereo, same performance), coherence 0.11. NOT delayed copies (lag scan: residual stays huge at every lag).
- LSB planes (bits 0-3) of both channels ≈ random (mean 0.5) → no LSB image.
- Welch: 18-24 kHz band is anomalously louder than 14-18 kHz, but zoom shows it is **unstructured white/dither noise**, not painted text.
- Piano onset ~0.73 s; "prelude" = first ~0.7 s contains only diffuse reverb/noise, no visible painting.

## Origin checked
- CTFtime / writeup search: not performed online; name "Chiaroscuro" is generic, scout found no direct writeup match.
- GitHub source / known clone: none identified.
- Encoder Lavf58.76.100 (FFmpeg) — re-encode artifact, no CVE angle.

## Approaches tried (all NEGATIVE — no `grey{...}` / readable text)
- **Linear-freq spectrograms** L/R/mid/diff, nperseg 512–8192, full 0–24 kHz + zoomed bands (0-4k, 4-12k, 12-20k, 16-24k). Only piano harmonics.
- **Prelude zoom** (first 0.5/0.73/0.8/1.2/1.6 s), grayscale + whitened, small & large nperseg. Only transients/reverb.
- **Log-frequency STFT, mel (256 bins), CQT** (7 oct, 24 bpo) — painting tools (Coagula/ARSS) use log-freq; still only piano.
- **Phase** spectrograms (L/R/diff) + **inter-channel phase difference** — noise.
- **L/R magnitude-squared coherence** (time-varying) — tracks note energy, no text.
- **Mid/side**, side channel, **side/(mid+side) panning map**, strong-side mask — music only.
- **L/R dB ratio** (energy-masked) — natural stereo image, no text.
- **Magnitude spectral subtraction** |R|-α|L| and |L|-α|R| (α 1.0/1.5/2.0): shows complementary HF stereo transients (12-19 kHz blocks) but NOT structured text.
- **Complex Wiener decorrelation** (global + local) R−g·L and L−g·R — residual keeps harmonics.
- **Background/median subtraction** (over freq, over time, 2-D median model) — harmonics only.
- **Per-freq-row whitening / z-score**, full + high band — noise/harmonics.
- **CLAHE + global histogram equalization** on the dB image (opencv) — amplifies noise, no text.
- **Frequency shift** (SSB via Hilbert) of side channel ±2–8 kHz ("se décale") — shifted music, no text.
- **Time reversal** of L/R/diff and reversed-channel sums/diffs ("repeint") — piano only.
- **Anomaly detector** (resid vs gaussian-smoothed model, hot time/freq) — only note onsets & piano fundamentals.
- **SSTV** hypothesis — spectrogram has no SSTV sync/tone structure; pysstv is encoder-only. Ruled out.
- **Frequency-decalage overlay** (`spec_decalage.py`): swept L-spectrogram vs R-spectrogram bin-shift -60..+60 (≈±2.3 kHz) and subtracted to cancel music at the aligning offset ("le clair se decale vers l'obscur"). NO offset yields readable text — harmonic comb just shifts. Negative.
- **strings / exiftool / RIFF walk** — only the French INAM title; no plaintext flag.

## Blocking
- The signal is, by every statistical and spectral measure, a genuine clean stereo piano recording. No standard or advanced spectrogram/phase/channel-combination view reveals painted text. If a painting exists it is either (a) reconstructable only with the author's exact encoder/transform params, or (b) hidden by a mechanism not yet identified.

## Next ideas (where a human / rerun should pick up)
- Open in **Audacity / sonic-visualiser GUI** directly — confirm whether a basic spectrogram shows text that headless renders miss (low prior; matplotlib renders were exhaustive, but worth a human eyeball).
- Decode the French title as an explicit transform: "le clair se décale vers l'obscur" may encode a precise (channel, freq-offset, blend) recipe — try **adding L spectrogram to a frequency-shifted R spectrogram** at many offsets, or stacking L over R with a vertical décalage so the two halves of the text align.
- Consider the flag is split: half painted in L, half in R, offset in frequency ("se décale") so neither channel alone is readable but an **aligned overlay** is. Sweep R freq-offset vs L and look for letters lining up.
- Try **ffmpeg `showspectrumpic`** (the encoder was FFmpeg) with log scale / different window to match the author's exact spectrogram rendering.
- Re-examine `ICRD=33` — possible numeric clue (offset? key? 33 Hz / 33-sample shift?).
- Check whether the "prelude" is a literal short clip that, isolated and **time-stretched**, reveals slow-scan painted content.
