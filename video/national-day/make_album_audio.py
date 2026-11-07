"""Soft cinematic bed for the album reel (21 s): string pad, page-turn swishes,
chimes as photos come to life, timpani roll into the finale. Writes album-audio.wav."""
import numpy as np, wave
SR, DUR = 44100, 21.0
N = int(SR * DUR); out = np.zeros((N, 2)); rng = np.random.default_rng(3)
def add(sig, t, g=1.0, pan=0.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if i >= N: return
    s = sig[:j - i] * g; out[i:j, 0] += s * (1 - max(0, pan)); out[i:j, 1] += s * (1 + min(0, pan))
def lp(x, fc):                      # FFT low-pass
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / (1 + (f / fc) ** 4); return np.fft.irfft(X, len(x))
def strings(freqs, d, att=1.2, rel=1.5, bright=1800):
    n = int(d * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for f in freqs:
        for det in (-.15, 0, .17):
            vib = 1 + .003 * np.sin(2 * np.pi * 5.2 * t + det * 9)
            ph = 2 * np.pi * np.cumsum(f * (1 + det / 100) * vib) / SR
            s += sum(np.sin(k * ph) / k for k in range(1, 9))
    s = lp(s, bright)
    e = np.minimum(1, t / att) * np.minimum(1, (d - t) / rel).clip(0)
    return s * e / (len(freqs) * 6)
def swish(d=.55):
    n = int(d * SR); x = rng.standard_normal(n); t = np.arange(n) / SR
    e = np.sin(np.pi * t / d) ** 2; y = lp(x, 2500) - lp(x, 400); return y * e * .6
def chime(f):
    n = int(2.5 * SR); t = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * f * m * t) * a * np.exp(-t * (1.4 + m)) for m, a in ((1, 1), (2.76, .4), (5.4, .2))) * .5
def timp(f=55, d=1.6):
    n = int(d * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(f + 20 * np.exp(-t * 20)) / SR) * np.exp(-t * 2.5) + rng.standard_normal(n) * np.exp(-t * 40) * .2
def cymbal(d=4):
    n = int(d * SR); x = rng.standard_normal(n); t = np.arange(n) / SR
    return (x - lp(x, 5000)) * np.exp(-t * 1.1) * .5
nt = lambda m: 440 * 2 ** ((m - 69) / 12)
# chord bed (D minor -> Bb -> C -> D major lift for the finale)
prog = [(0.0, [50, 57, 62, 65], 5.1), (4.6, [46, 53, 58, 62], 5.4), (9.5, [48, 55, 60, 64], 5.5), (14.5, [50, 57, 62, 65, 69], 3.0)]
for t0, notes, d in prog: add(strings([nt(m) for m in notes], d + 1.2, att=1.4, rel=1.6), t0, .9)
add(strings([nt(m) for m in (38, 50, 57, 62, 66, 69, 74)], 4.4, att=.25, rel=2.2, bright=3200), 17.1, 1.4)   # D major arrival
add(strings([nt(m) for m in (26, 38)], 4.2, att=.3, rel=2.0, bright=600), 17.1, 1.2)
# page turns: cover open + five pages
for t in (1.6, 4.5, 7.0, 9.5, 12.0, 14.5): add(swish(), t, .55, .3)
# chimes as each photo comes to life (D hijaz colours)
for i, t in enumerate((3.05, 5.55, 8.05, 10.55, 13.05, 15.35)):
    add(chime(nt([74, 75, 78, 79, 81, 86][i])), t, .35, (-1) ** i * .4)
# timpani roll into the finale + hit
for k in range(36):
    t = 16.1 + k * (1.0 / 36); add(timp(55, .4), t, .05 + .5 * (k / 36) ** 2, (-1) ** k * .2)
add(timp(48, 3.0), 17.1, 1.4); add(cymbal(), 17.1, .8)
for t in (18.6, 19.35, 20.1): add(timp(55, 1.2), t, .55)     # slow ceremonial beats
mix = out / (np.percentile(np.abs(out), 99.95) + 1e-9) * .8
mix = np.tanh(mix * 1.1)
fi, fo = int(.4 * SR), int(.9 * SR); mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
with wave.open('album-audio.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok')
