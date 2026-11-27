"""Original cinematic score for the proposal video (D minor, 90 BPM) + library SFX at the cuts.

Layers: string pad, low strings, piano motif/arpeggios, timpani pulses, shaker, a riser into the
"complex complete" hit, impacts on the title / completion / closing, whooshes on section changes,
and a soft rotor hum under the exterior fly-through. Writes build/proposal/soundtrack.wav (48 kHz).
SFX: video-shotcraft audio library (Mixkit free licence).
"""
import os, subprocess, wave
import numpy as np

SR = 48000
DUR = 65.0
N = int(DUR * SR)
t = np.arange(N) / SR
rng = np.random.default_rng(44)
OUT = os.path.join(os.path.dirname(__file__), '..', 'build', 'proposal', 'soundtrack.wav')
SFX = '/root/.claude/plugins/synced/5680f315-2fdc-44e7-a126-21641b1ed974_87e12e4a-faec-48c3-a56b-30a37ba29697/74655670-1540-4e3d-8509-c2f446898c2c/assets/audio/sfx'

BPM = 90.0
BEAT = 60 / BPM
BAR = 4 * BEAT
# section starts (s): title, site, construction, fly-through, hall, closing
S_SITE, S_CONS, S_FLY, S_HALL, S_CLOSE, T_DONE = 5.0, 15.0, 30.0, 49.5, 61.5, 28.4

def midi(n): return 440.0 * 2 ** ((n - 69) / 12)
CHORDS = {'Dm': [50, 53, 57], 'Bb': [46, 50, 53], 'F': [53, 57, 60], 'C': [48, 52, 55], 'Gm': [55, 58, 62], 'A': [45, 49, 52]}
PROG = ['Dm', 'Bb', 'F', 'C']
HALL_PROG = ['Dm', 'Gm', 'Bb', 'A']

def env_adsr(n, a, r, sus=1.0):
    e = np.ones(n) * sus
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na) if na else e[:na]
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e

def saw_soft(f, n, phase=0.0, harmonics=12):
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for h in range(1, harmonics + 1):
        if f * h > 9000: break
        out += np.sin(2 * np.pi * f * h * tt + phase * h) / h * np.exp(-h / 5.0)
    return out

def add(buf, start, sig, gain=1.0):
    i = int(start * SR)
    if i >= len(buf): return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i] * gain

def chord_at(time):
    if S_HALL <= time < S_CLOSE:
        return HALL_PROG[int((time - S_HALL) / BAR) % 4]
    return PROG[int(time / BAR) % 4]

def section_level(time):
    """Overall intensity 0..1 following the picture."""
    pts = [(0, 0.35), (S_SITE, 0.45), (S_CONS, 0.55), (T_DONE, 0.95), (S_FLY, 1.0), (S_HALL - 0.5, 0.95), (S_HALL + 1, 0.55), (S_CLOSE, 0.8), (DUR - 1.5, 0.9), (DUR, 0.0)]
    xs, ys = zip(*pts)
    return np.interp(time, xs, ys)

pad = np.zeros(N); bass = np.zeros(N); piano = np.zeros(N); drums = np.zeros(N); shaker = np.zeros(N)

# string pad + low strings: one chord per bar, overlapping crossfades
nbars = int(DUR / BAR) + 2
for b in range(nbars):
    st = b * BAR
    if st >= DUR: break
    name = chord_at(st + 0.01)
    n = int((BAR + 1.2) * SR)
    sig = np.zeros(n)
    for k, note in enumerate(CHORDS[name] + [CHORDS[name][0] + 12]):
        for det in (-0.12, 0.12):
            sig += saw_soft(midi(note + 12) * (1 + det / 100), n, rng.uniform(0, 6))
    sig *= env_adsr(n, 0.9, 1.2) * 0.07
    add(pad, st, sig)
    lo = saw_soft(midi(CHORDS[name][0] - 12), n, 0.0, 8) * env_adsr(n, 0.4, 1.0) * 0.16
    add(bass, st, lo)

# piano: motif in title/hall, eighth-note arpeggios during the fly-through and the end of construction
def piano_note(f, dur, vel):
    n = int((dur + 1.5) * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * h * tt) * a for h, a in [(1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)])
    return s * np.exp(-tt * 2.4) * np.minimum(1, tt * 400) * vel
motif = [62, 65, 69, 67, 65, 64, 62, 57]
for i, note in enumerate(motif):
    add(piano, 0.5 + i * BEAT, piano_note(midi(note + 12), BEAT, 0.16))
for i, note in enumerate(motif):
    add(piano, S_HALL + 0.4 + i * BEAT * 1.5, piano_note(midi(note + 12), BEAT * 1.5, 0.14))
time = T_DONE - 2 * BAR
while time < S_HALL - 0.3:
    name = chord_at(time + 0.01)
    notes = CHORDS[name] + [CHORDS[name][0] + 12, CHORDS[name][1] + 12]
    seq = notes + notes[::-1][1:-1]
    for k in range(8):
        add(piano, time + k * BEAT / 2, piano_note(midi(seq[k % len(seq)] + 12), BEAT / 2, 0.075))
    time += BAR
for k, note in enumerate([62, 69, 74]):
    add(piano, S_CLOSE + 0.3 + k * BEAT / 2, piano_note(midi(note + 12), 2.0, 0.15))

# timpani and shaker: construction pulse growing, full groove in the fly-through
def timpani(f0, vel):
    n = int(1.4 * SR); tt = np.arange(n) / SR
    f = f0 * (1 + 0.25 * np.exp(-tt * 18))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.2)
    hit = rng.standard_normal(n) * np.exp(-tt * 40) * 0.25
    return (body + hit) * vel
beat_i = 0
time = S_CONS
while time < S_HALL - 0.2:
    k = (time - S_CONS) / (T_DONE - S_CONS)
    if time < T_DONE:
        if beat_i % 2 == 0: add(drums, time, timpani(midi(38), 0.12 + 0.25 * k))
    else:
        add(drums, time, timpani(midi(38 if beat_i % 4 in (0, 2) else 45), 0.32 if beat_i % 4 == 0 else 0.2))
        for s16 in range(4):
            n = int(0.09 * SR); tt = np.arange(n) / SR
            add(shaker, time + s16 * BEAT / 4, rng.standard_normal(n) * np.exp(-tt * 60) * (0.05 if s16 % 2 else 0.03))
    time += BEAT; beat_i += 1

# gentle high-pass on the shaker (difference) and a small room reverb on the music bus
shaker = np.concatenate([[0], np.diff(shaker)])
music = pad + bass + piano + drums + shaker
music *= section_level(t)
ir_n = int(1.8 * SR)
ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR * 3.5); ir[0] = 0; ir /= np.abs(ir).sum() / 6
L = 1 << int(np.ceil(np.log2(N + ir_n)))
wet = np.fft.irfft(np.fft.rfft(music, L) * np.fft.rfft(ir, L), L)[:N]
music = music + 0.22 * wet

# SFX
def load(rel):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', os.path.join(SFX, rel), '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'])
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768
fx = np.zeros(N)
riser = load('riser/riser-cine.mp3')
add(fx, T_DONE - len(riser) / SR, riser, 0.5)
for when, g in [(1.0, 0.55), (T_DONE, 0.7), (S_CLOSE + 0.3, 0.55)]:
    add(fx, when, load('impact/impact-cine-big.mp3'), g)
for when in (S_SITE - 0.25, S_CONS - 0.25, S_FLY - 0.25, S_HALL - 0.25):
    add(fx, when, load('transition/whoosh-big.mp3'), 0.35)
# rotor hum under the exterior shots (props at 50 % speed)
hum = np.zeros(N)
seg = (t > T_DONE) & (t < 43.0)
ph = 2 * np.pi * 52 * t
hum[seg] = (np.sin(ph) + 0.4 * np.sin(2 * ph))[seg] * (0.6 + 0.4 * np.sin(2 * np.pi * 2.67 * t[seg]))
hum *= np.interp(t, [T_DONE, T_DONE + 1.5, 41.0, 43.0], [0, 1, 1, 0]) * 0.04

mix = music / np.abs(music).max() * 0.8 + fx * 0.9 + hum
mix *= np.interp(t, [0, 0.4, DUR - 1.2, DUR], [0, 1, 1, 0])
st = np.stack([mix, np.roll(mix, 180)], 1)
st = st / np.abs(st).max() * 0.89
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with wave.open(OUT, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print('soundtrack', DUR, 's ->', OUT)
