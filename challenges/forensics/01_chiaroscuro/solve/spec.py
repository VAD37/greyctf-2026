"""Chiaroscuro — spectrogram-stego solver attempt.

Renders per-channel spectrograms (L, R, mid, diff) in linear & log frequency,
plus an L/R magnitude spectral-subtraction view. Intended to surface a flag
painted into the audio spectrum. As of this attempt NO view shows readable text
(see ATTEMPTS.md). Run:  uv run python solve/spec.py
"""
import os
import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as sg
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
WAV = os.path.join(HERE, "../files/dist-Chiaroscuro/painted_audio.wav")

sr, x = wav.read(WAV)
L = x[:, 0].astype(float)
R = x[:, 1].astype(float)
chans = {"L": L, "R": R, "mid": (L + R) / 2, "diff": L - R}

# 1) linear-frequency spectrograms
for name, ch in chans.items():
    f, t, S = sg.spectrogram(ch, sr, nperseg=2048, noverlap=1536, window="hann")
    plt.figure(figsize=(20, 8))
    plt.pcolormesh(t, f, 10 * np.log10(np.abs(S) + 1e-9), shading="auto", cmap="magma")
    plt.ylim(0, 16000)
    plt.title(f"{name} spectrogram")
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, f"full_{name}.png"), dpi=120)
    plt.close()

# 2) L/R magnitude spectral subtraction (chiaroscuro = light/dark channels)
f, t, ML = sg.spectrogram(L, sr, nperseg=4096, noverlap=int(4096 * 0.85))
_, _, MR = sg.spectrogram(R, sr, nperseg=4096, noverlap=int(4096 * 0.85))
d = np.maximum(np.sqrt(MR) - 2.0 * np.sqrt(ML), 0)
plt.figure(figsize=(24, 10))
plt.imshow(20 * np.log10(d[f <= 16000] + 1e-6), origin="lower", aspect="auto",
           cmap="inferno", extent=[t[0], t[-1], 0, 16000], interpolation="nearest")
plt.title("R - L magnitude spectral subtraction")
plt.tight_layout()
plt.savefig(os.path.join(HERE, "specsub_R_minus_L_2.0.png"), dpi=120)
plt.close()
print("rendered full_*.png and specsub_R_minus_L_2.0.png")
