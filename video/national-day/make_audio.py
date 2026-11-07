"""Synthesises the reel soundtrack (120 BPM, 15 s): Gulf-style drums, claps,
oud-like plucks (Karplus-Strong), riser and impacts. Writes audio.wav."""
import numpy as np, wave
SR, DUR, BEAT = 44100, 15.0, 0.5
N = int(SR * DUR); L = np.zeros(N); Rr = np.zeros(N)
rng = np.random.default_rng(7)
def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if i >= N: return
    s = sig[:j - i] * gain
    L[i:j] += s * (1 - max(0, pan)); Rr[i:j] += s * (1 + min(0, pan))
def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / d)
def doom(f0=58, d=0.45):          # deep frame drum (rahmani-ish)
    n = int(SR * 1.0); t = np.arange(n) / SR
    f = f0 + 90 * np.exp(-t * 30); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.tanh(2.2 * np.sin(ph) * env(n, .001, d))
def tak(f=900, d=0.05):           # high skin slap
    n = int(SR * .25); x = rng.standard_normal(n)
    X = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
    X *= np.exp(-((fr - f) / (f * .6)) ** 2); y = np.fft.irfft(X, n)
    y /= np.abs(y).max(); t = np.arange(n) / SR
    return (y + .5 * np.sin(2 * np.pi * f * .5 * t)) * env(n, .0005, d)
def clap():
    n = int(SR * .3); x = rng.standard_normal(n); out = np.zeros(n)
    for k, o in enumerate([0, .008, .016, .026]):
        i = int(o * SR); out[i:] += x[:n - i] * env(n - i, .0005, .012 if k < 3 else .09)
    X = np.fft.rfft(out); fr = np.fft.rfftfreq(n, 1 / SR); X *= np.exp(-((fr - 1500) / 1300) ** 2)
    y = np.fft.irfft(X, n); return y / np.abs(y).max()
def boom():
    n = int(SR * 2.2); t = np.arange(n) / SR
    f = 38 + 140 * np.exp(-t * 14)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .001, .7)
    noise = rng.standard_normal(n) * env(n, .001, .08) * .5
    return np.tanh(1.8 * (s + noise))
def pluck(freq, d=0.6, bright=0.5):   # Karplus-Strong oud-ish
    n = int(SR * d); p = int(SR / freq)
    buf = rng.uniform(-1, 1, p); out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = .996 * (bright * buf[i % p] + (1 - bright) * buf[(i + 1) % p]) if i % p != p - 1 else .996 * .5 * (buf[i % p] + buf[0])
    return out * env(n, .001, d * .6)
def riser(t0, t1):
    n = int((t1 - t0) * SR); t = np.arange(n) / SR; k = t / t[-1]
    x = rng.standard_normal(n); X = np.fft.rfft(x); y = np.fft.irfft(X * 1, n)
    f = 200 + 3000 * k ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * .3
    return (y * .25 + tone) * k ** 2

D, T, C, B = doom(), tak(), clap(), boom()
# --- intro: four huge hits synced to the word punches
for i, t in enumerate([0, .5, 1, 1.5]):
    add(B, t, .5); add(doom(50, .6), t, .6)
    add(T, t + .25, .35, .3 * (-1) ** i)
# --- groove 2s..15s (Gulf 6/8-feel over 4/4: doom . tak doom . tak tak .)
pattern = [(0, 'D'), (.375, 'T'), (.75, 'D'), (1.0, 'T'), (1.25, 'D'), (1.5, 'T'), (1.75, 'T')]
for bar in range(2, 15, 2):
    for off, k in pattern:
        t = bar + off
        if t >= 14.75: continue
        if k == 'D': add(D, t, .8 if bar < 8 else 1.25)
        else: add(T, t, .45 if bar < 8 else .75, rng.uniform(-.5, .5))
    for cb in (.5, 1.5):                       # claps on 2 & 4
        if bar + cb < 14.75: add(C, bar + cb, .45 if bar < 5 else .7, rng.uniform(-.2, .2))
# double-time claps building into the drop
for i in range(8): add(C, 7.0 + i * .125, .3 + i * .06)
add(riser(5.5, 8.0), 5.5, .55)
for t, g in ((2, .7), (5, .7), (8, 1.2), (11.5, 1.0)): add(B, t, g)
# --- oud line in D Hijaz (D Eb F# G A Bb C D)
hz = {'D3': 146.8, 'Eb3': 155.6, 'F#3': 185.0, 'G3': 196.0, 'A3': 220.0, 'Bb3': 233.1, 'C4': 261.6, 'D4': 293.7, 'D2': 73.4}
riff = ['D3', 'Eb3', 'F#3', 'G3', 'A3', 'G3', 'F#3', 'Eb3', 'D3', 'F#3', 'A3', 'Bb3', 'A3', 'G3', 'F#3', 'D3']
cache = {}
def P(n, d=.5):
    if (n, d) not in cache: cache[(n, d)] = pluck(hz[n], d)
    return cache[(n, d)]
for i in range(int((15 - 5) / .25)):
    t = 5 + i * .25
    if t >= 14.6 or (7.75 <= t < 8): continue
    add(P(riff[i % 16]), t, .35 if t < 8 else .5, .25)
    if t >= 8 and i % 4 == 0: add(P(riff[i % 16]), t, .25, -.25)
# bass drone after the drop
for t in np.arange(8, 14.5, 1.0): add(P('D2', 1.0), t, .55)
# final hit
add(B, 14.5, 1.0); add(doom(45, .9), 14.5, 1.0)
# --- master: soft clip + fade
mix = np.stack([L, Rr], 1)
mix /= np.percentile(np.abs(mix), 99.9) + 1e-9
mix = np.tanh(mix * 1.1) * .92
fade = np.ones(N); fl = int(.25 * SR); fade[-fl:] = np.linspace(1, 0, fl); mix *= fade[:, None]
with wave.open('audio.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok')
