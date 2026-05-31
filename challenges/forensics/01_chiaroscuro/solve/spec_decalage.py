"""Most-literal decode of 'Le clair se decale vers l'obscur':
the L (clair) spectrogram shifted in frequency to overlay the R (obscur) one.
Sweep a vertical (frequency-bin) offset between the two channel spectrograms and
look for text that only becomes readable when the halves align.
"""
import os
import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as sg
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
WAV = os.path.join(HERE, "../files/dist-Chiaroscuro/painted_audio.wav")

sr, x = wav.read(WAV)
L = x[:, 0].astype(float); R = x[:, 1].astype(float)

nperseg = 2048
f, t, SL = sg.spectrogram(L, sr, nperseg=nperseg, noverlap=1536)
_, _, SR = sg.spectrogram(R, sr, nperseg=nperseg, noverlap=1536)
ML = 10*np.log10(np.abs(SL)+1e-9)
MR = 10*np.log10(np.abs(SR)+1e-9)
df = f[1]-f[0]
nf = ML.shape[0]
fmax_bin = int(16000/df)

# sweep bin shifts of L relative to R; combine by subtraction (decalage that cancels music)
for shift in range(-60, 61, 10):
    Ls = np.zeros_like(ML)
    if shift >= 0:
        Ls[shift:] = ML[:nf-shift]
    else:
        Ls[:nf+shift] = ML[-shift:]
    comb = MR - Ls   # where shifted-L cancels R -> music gone, painting remains
    img = comb[:fmax_bin]
    plt.figure(figsize=(22, 8))
    plt.imshow(img, origin="lower", aspect="auto", cmap="gray",
               extent=[t[0], t[-1], 0, 16000], interpolation="nearest")
    plt.title(f"R - L(shift {shift} bins = {shift*df:.0f} Hz)")
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, f"dec_{shift:+03d}.png"), dpi=110)
    plt.close()
    print("wrote shift", shift)
print("done")
