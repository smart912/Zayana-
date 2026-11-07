"""Soundtrack for Zayana's intro video: knocks, door, a light Omani-style rhythm, sparkles and a car."""
import numpy as np, wave, sys
SR = 44100; DUR = 26.6
out = np.zeros(int(SR * DUR))
rng = np.random.default_rng(7)
def add(sig, t, gain=1.0):
    i = int(t * SR)
    if i >= len(out): return
    j = min(len(out), i + len(sig)); out[i:j] += sig[: j - i] * gain
def env(n, a=0.005, d=0.2):
    t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / d)
def lowpass(x, k=8):
    return np.convolve(x, np.ones(k) / k, mode='same')
def tone(f, dur, d=0.25, kind='sine'):
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(np.broadcast_to(f, n) if np.ndim(f) else np.full(n, f)) / SR
    w = np.sin(ph) if kind == 'sine' else (2 * ((ph / (2 * np.pi)) % 1) - 1)
    return w * env(n, 0.004, d)
# knocks on the wooden door
for k in (1.3, 1.75, 2.2, 3.4):
    n = int(.25 * SR); f = np.linspace(140, 70, n)
    add(tone(f, .25, .06) + lowpass(rng.normal(0, 1, n), 20) * env(n, .001, .02) * .8, k, .9)
# night drone
n = int(4.6 * SR); t = np.arange(n) / SR
add((np.sin(2*np.pi*73.4*t) + .5*np.sin(2*np.pi*110*t)) * np.minimum(1, t/1.5) * np.minimum(1, (4.6-t)/0.8) * .12, 0)
# door opening: a rising swell
n = int(1.6 * SR); t = np.arange(n) / SR
sw = lowpass(rng.normal(0, 1, n), 30) * np.sin(np.pi * t / 1.6) * .35
sw += np.sin(2*np.pi*(220 + 160*t)*t) * np.sin(np.pi*t/1.6) * .12
add(sw, 4.4)
# sparkles
def sparkle(at, g=.35):
    for i, f in enumerate((1568, 2093, 2637, 3136)): add(tone(f, .5, .18), at + i * .06, g * (1 - i * .15))
for s in (9.05, 20.54, 24.06): sparkle(s, .45 if s == 9.05 else .3)
# hops
for h in (9.1, 12.6, 18.97, 23.35):
    n = int(.3 * SR); add(tone(np.linspace(300, 700, n), .3, .12), h, .25)
# rhythm: 96 BPM, dum on 1 and the "and" of 2, tak on 2 and 4, from 5.8 s
bpm = 96; beat = 60 / bpm; start = 5.8
def dum():
    n = int(.35 * SR); return tone(np.linspace(120, 55, n), .35, .16)
def tak():
    n = int(.12 * SR); x = rng.normal(0, 1, n); x = x - lowpass(x, 6); return x * env(n, .001, .03)
t0 = start
while t0 < DUR - .6:
    add(dum(), t0, .55); add(tak(), t0 + beat, .35); add(dum(), t0 + 1.5 * beat, .4); add(tak(), t0 + 3 * beat, .35)
    add(tak(), t0 + 3.5 * beat, .2); t0 += 4 * beat
# a plucked melody in a Hijaz flavour (D Eb F# G A Bb C)
D = 293.66; scale = [D, D*16/15, D*5/4, D*4/3, D*3/2, D*8/5, D*16/9, D*2]
phrase = [0, 2, 3, 4, 3, 2, 1, 0,  4, 5, 4, 3, 2, 3, 1, 0]
def pluck(f, dur=.45):
    n = int(dur * SR); w = tone(f, dur, .22, 'saw') + .4 * tone(2*f, dur, .12); return lowpass(w, 5)
t0 = start + 4 * beat * 1; i = 0
while t0 < DUR - .8:
    if not (16.4 < t0 < 17.4):
        add(pluck(scale[phrase[i % len(phrase)]]), t0, .16)
    t0 += beat / 2; i += 1
# the car: an engine roar in, a whoosh out
n = int(1.0 * SR); t = np.arange(n) / SR
eng = tone(np.linspace(55, 170, n), 1.0, .6, 'saw') * np.minimum(1, t / .1) + lowpass(rng.normal(0, 1, n), 4) * .2 * np.exp(-t / .5)
add(lowpass(eng, 6), 16.47, .5)
n = int(.6 * SR); t = np.arange(n) / SR
add(lowpass(rng.normal(0, 1, n), 12) * np.sin(np.pi * t / .6) * .6, 18.81)
# Zayana's voice (ElevenLabs, Jumana), cut on its pauses and placed on the scenes; the music ducks under it
if len(sys.argv) > 2:
    with wave.open(sys.argv[2]) as w: v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    cuts = [(0.0, 1.05), (1.25, 4.05), (4.27, 7.42), (7.66, 10.41), (10.6, 11.95), (12.15, 14.33), (14.49, 17.04)]
    at = [6.9, 9.45, 12.75, 16.55, 19.5, 20.9, 23.5]
    out *= 0.5
    for (a, b), t0 in zip(cuts, at):
        seg = v[int(a * SR):int(b * SR)].copy(); f = int(.02 * SR); seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        add(seg / max(1e-6, np.max(np.abs(v))) * 1.1, t0)
# fade out and normalise
fade = int(.5 * SR); out[-fade:] *= np.linspace(1, 0, fade)
out = out / np.max(np.abs(out)) * .89
pcm = (out * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote', sys.argv[1])
