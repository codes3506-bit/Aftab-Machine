"""Cinematic orchestral score for the proposal video (v3, D minor, 84 BPM), synthesised in numpy.

Instruments: string ensemble (detuned saws, vibrato, low-pass), legato violins melody, brass (bright saws with
swell), choir pad (formant-filtered saws), piano, timpani, taiko, cymbal swells; plus library SFX (riser,
impacts, whooshes) and a soft rotor hum under the exterior shots. Section times come from proposal_timeline.js.
Writes build/proposal3/soundtrack.wav (48 kHz stereo).
"""
import json, os, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
clips = json.loads(subprocess.check_output(['node', '-e', "const {CLIPS,XF}=require('./proposal_timeline');let t=0;const o={};for(const c of CLIPS){o[c.name]=t;t+=c.dur-XF;}o.end=t+XF;console.log(JSON.stringify(o))"], cwd=HERE))
DUR = clips['end']
N = int(DUR * SR) + SR
t = np.arange(N) / SR
rng = np.random.default_rng(1947)
OUT = os.path.join(HERE, '..', 'build', 'proposal3', 'soundtrack.wav')
SFX = '/root/.claude/plugins/synced/5680f315-2fdc-44e7-a126-21641b1ed974_87e12e4a-faec-48c3-a56b-30a37ba29697/74655670-1540-4e3d-8509-c2f446898c2c/assets/audio/sfx'

BPM = 84.0
BEAT = 60 / BPM
BAR = 4 * BEAT
S = clips
T_DONE = S['construction'] + 0.25 + 14.2        # building complete (finishes start)
INTERIOR = (S['foyer'], S['hall_360'])

def midi(n): return 440.0 * 2 ** ((n - 69) / 12)
CH = {'Dm': [38, 50, 53, 57, 62], 'Bb': [34, 50, 53, 58, 62], 'F': [41, 53, 57, 60, 65], 'C': [36, 52, 55, 60, 64],
      'Gm': [43, 55, 58, 62, 67], 'A': [45, 52, 57, 61, 64], 'Am': [45, 52, 57, 60, 64]}
def chord_at(time):
    if time < S['construction']: prog = ['Dm', 'Bb', 'F', 'C']
    elif time < T_DONE: prog = ['Dm', 'Dm', 'Bb', 'A']
    elif time < INTERIOR[0]: prog = ['Dm', 'Bb', 'F', 'C']
    elif time < INTERIOR[1]: prog = ['Dm', 'Gm', 'Bb', 'A']
    else: prog = ['Bb', 'F', 'Gm', 'A'] if time < S['closing'] else ['Dm', 'Dm', 'Dm', 'Dm']
    return prog[int(time / BAR) % 4]

def lowpass(x, fc):
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(np.fft.rfft(x) / np.sqrt(1 + (f / fc) ** 4), len(x))
def bandpass(x, fc, q):
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(np.fft.rfft(x) * np.exp(-((f - fc) / (fc / q)) ** 2), len(x))
def saw(f, n, ph=0.0, vib=0.0, vr=5.0):
    tt = np.arange(n) / SR
    inst = f * (1 + vib * np.sin(2 * np.pi * vr * tt + ph))
    p = np.cumsum(inst) / SR + ph
    return 2 * (p % 1.0) - 1
def env(n, a, r):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na) ** 1.5
    if nr: e[-nr:] *= np.linspace(1, 0, nr) ** 1.2
    return e
def add(buf, at, sig, g=1.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(sig) <= 0: return
    a = max(0, -i); j = min(len(buf), i + len(sig))
    buf[max(i, 0):j] += sig[a:a + j - max(i, 0)] * g
def level(time, pts):
    xs, ys = zip(*pts); return np.interp(time, xs, ys)

strings = np.zeros(N); brass = np.zeros(N); choir = np.zeros(N); piano = np.zeros(N); perc = np.zeros(N); melody = np.zeros(N)

# 1) string ensemble pad: chord per bar, 6 detuned voices per note
nb = int(DUR / BAR) + 2
for b in range(nb):
    st = b * BAR
    if st > DUR: break
    name = chord_at(st + 0.01)
    n = int((BAR + 1.6) * SR)
    sig = np.zeros(n)
    for note in CH[name][1:]:
        for d in (-0.18, -0.07, 0.0, 0.06, 0.13, 0.2):
            sig += saw(midi(note) * (1 + d / 100), n, rng.uniform(0, 1), 0.0025, 4.5 + rng.uniform(-0.6, 0.6))
    sig *= env(n, 1.1, 1.4) * 0.018
    add(strings, st, sig)
    lo = (saw(midi(CH[name][0]), n, 0, 0.002, 4.0) + saw(midi(CH[name][0] - 12), n, 0.3, 0.002, 4.2)) * env(n, 0.6, 1.2) * 0.05
    add(strings, st, lo)
strings = lowpass(strings, 1800)

# 2) construction ostinato: staccato 8ths on violas, growing
time = S['construction']
k = 0
while time < T_DONE:
    name = chord_at(time + 0.01); notes = CH[name][1:4]
    n = int(0.26 * SR); note = notes[[0, 1, 2, 1][k % 4]] + 12
    s = sum(saw(midi(note) * (1 + d / 100), n, rng.uniform(0, 1)) for d in (-0.1, 0.0, 0.1)) * env(n, 0.01, 0.18)
    grow = (time - S['construction']) / (T_DONE - S['construction'])
    add(strings, time, lowpass(s, 2600) * (0.02 + 0.05 * grow))
    time += BEAT / 2; k += 1

# 3) violins melody (main theme) for scope/exterior and hall
theme = [(62, 1), (65, 1), (69, 2), (67, 1), (65, 1), (64, 2), (65, 1), (67, 1), (69, 1.5), (70, 0.5), (69, 2), (62, 2)]
def play_theme(at, octave, gain, stretch=1.0):
    tt0 = at
    for note, beats in theme:
        n = int((beats * BEAT * stretch + 0.5) * SR)
        s = sum(saw(midi(note + octave) * (1 + d / 100), n, rng.uniform(0, 1), 0.004, 5.2) for d in (-0.12, 0.0, 0.12))
        add(melody, tt0, lowpass(s, 3200) * env(n, 0.12, 0.45) * gain)
        tt0 += beats * BEAT * stretch
play_theme(S['scope_of_work'] + 0.2, 12, 0.03)
play_theme(S['fly_exterior'] + 4.0, 12, 0.035)
play_theme(S['hall_360'] + 0.5, 12, 0.03, 1.25)

# 4) brass fanfare on the title reveal, completion and closing
def brass_chord(at, name, dur, gain):
    n = int(dur * SR)
    s = sum(saw(midi(note) * (1 + d / 100), n, rng.uniform(0, 1), 0.0015, 4.0) for note in CH[name][:4] for d in (-0.08, 0.08))
    add(brass, at, lowpass(s, 1400) * env(n, 0.35, 1.2) * gain)
for at, name, dur, g in [(S['title'] + 1.4, 'Dm', 3.5, 0.03), (S['title'] + 4.2, 'Bb', 2.6, 0.026), (T_DONE, 'Dm', 3.0, 0.04), (T_DONE + 2.8, 'F', 2.8, 0.032),
                         (S['hall_360'] + 13.0, 'Bb', 3.0, 0.024), (S['closing'] + 0.8, 'Dm', 4.5, 0.04)]:
    brass_chord(at, name, dur, g)

# 5) choir pad ("ah") under title, completion and hall
ch_src = np.zeros(N)
for at, dur, name in [(S['title'] + 0.5, 6.5, 'Dm'), (T_DONE - 1.0, 6.0, 'Dm'), (S['hall_360'], 16.0, 'Bb'), (S['closing'], 5.5, 'Dm')]:
    n = int(dur * SR)
    s = sum(saw(midi(note + 12) * (1 + d / 100), n, rng.uniform(0, 1), 0.004, 5.5) for note in CH[name][1:4] for d in (-0.15, 0.0, 0.15))
    add(ch_src, at, s * env(n, 1.4, 1.8))
choir = (bandpass(ch_src, 800, 3) + 0.6 * bandpass(ch_src, 1150, 4) + 0.25 * bandpass(ch_src, 2900, 5)) * 0.03

# 6) piano: motif in site and interiors
def pn(f, dur, vel):
    n = int((dur + 1.6) * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * h * tt) * a * np.exp(-tt * (1.8 + h * 0.7)) for h, a in [(1, 1.0), (2, 0.5), (3, 0.25), (4, 0.12), (5, 0.06)])
    return s * np.minimum(1, tt * 500) * vel
motif = [74, 69, 72, 69, 74, 76, 77, 76]
for rep in range(2):
    for i, note in enumerate(motif):
        add(piano, S['site_location'] + 0.6 + rep * 8 * BEAT + i * BEAT, pn(midi(note), BEAT, 0.07))
time = INTERIOR[0]
while time < INTERIOR[1] - 0.5:
    name = chord_at(time + 0.01); arp = CH[name][1:] + [CH[name][2] + 12]
    for i in range(8):
        add(piano, time + i * BEAT / 2, pn(midi(arp[[0, 1, 2, 3, 4, 3, 2, 1][i]] + 12), BEAT / 2, 0.035))
    time += BAR

# 7) percussion: timpani pulse in construction, taiko groove in the fly-through, cymbal swells into hits
def timp(f0, vel):
    n = int(1.6 * SR); tt = np.arange(n) / SR
    f = f0 * (1 + 0.2 * np.exp(-tt * 20))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.8) + rng.standard_normal(n) * np.exp(-tt * 45) * 0.2) * vel
def taiko(vel):
    n = int(1.2 * SR); tt = np.arange(n) / SR
    f = 62 * (1 + 0.6 * np.exp(-tt * 30))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 5) + lowpass(rng.standard_normal(n), 900) * np.exp(-tt * 25) * 0.6) * vel
def swell(dur, vel):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = rng.standard_normal(n); x = x - lowpass(x, 3500)
    return x * (tt / dur) ** 2.5 * vel
time, i = S['construction'], 0
while time < T_DONE:
    if i % 2 == 0: add(perc, time, timp(midi(38), 0.08 + 0.18 * (time - S['construction']) / (T_DONE - S['construction'])))
    time += BEAT; i += 1
time, i = T_DONE, 0
while time < INTERIOR[0] - 0.4:
    if i % 4 in (0, 3) or (i % 8 == 6): add(perc, time, taiko(0.22 if i % 4 == 0 else 0.13))
    if i % 2 == 1: add(perc, time, timp(midi(45), 0.08))
    time += BEAT / 2; i += 1
for at, d, v in [(S['title'] + 1.4, 1.2, 0.05), (T_DONE, 2.6, 0.07), (S['closing'] + 0.8, 1.6, 0.06)]:
    add(perc, at - d, swell(d, v)); add(perc, at, taiko(0.32))

# mix bus: section dynamics + reverb
music = strings + 0.9 * melody + brass + choir + piano + perc
dyn = level(t, [(0, 0.5), (S['site_location'], 0.55), (S['construction'], 0.6), (T_DONE, 1.0), (S['scope_of_work'], 0.95), (S['fly_exterior'], 1.0),
                (INTERIOR[0] - 0.5, 0.95), (INTERIOR[0] + 1, 0.62), (INTERIOR[1], 0.7), (INTERIOR[1] + 2, 0.85), (S['closing'], 0.95), (DUR, 0.95)])
music *= dyn
ir_n = int(2.6 * SR)
ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR * 2.6); ir[:int(0.02 * SR)] = 0; ir /= np.abs(ir).sum() / 7
L = 1 << int(np.ceil(np.log2(N + ir_n)))
wet = np.fft.irfft(np.fft.rfft(music, L) * np.fft.rfft(ir, L), L)[:N]
music = music + 0.3 * wet

def load(rel):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', os.path.join(SFX, rel), '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'])
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768
fx = np.zeros(N)
riser = load('riser/riser-cine.mp3'); add(fx, T_DONE - len(riser) / SR, riser, 0.4)
for at, g in [(S['title'] + 1.4, 0.45), (T_DONE, 0.6), (S['closing'] + 0.8, 0.5)]:
    add(fx, at, load('impact/impact-cine-big.mp3'), g)
for name in ('site_location', 'construction', 'scope_of_work', 'fly_exterior', 'foyer', 'hall_360', 'closing'):
    add(fx, S[name] - 0.3, load('transition/whoosh-big.mp3'), 0.22)
hum = np.zeros(N)
a0, a1 = T_DONE, S['fly_cutaway'] + 6
seg = (t > a0) & (t < a1)
ph = 2 * np.pi * 50 * t
hum[seg] = (np.sin(ph) + 0.35 * np.sin(2 * ph))[seg] * (0.65 + 0.35 * np.sin(2 * np.pi * 2.67 * t[seg]))
hum *= np.interp(t, [a0, a0 + 2, a1 - 2, a1], [0, 1, 1, 0]) * 0.022

mix = music / np.abs(music).max() * 0.82 + fx * 0.8 + hum
mix *= np.interp(t, [0, 0.6, DUR - 1.4, DUR], [0, 1, 1, 0])
mix = mix[:int(DUR * SR)]
st = np.stack([mix, np.roll(mix, 220) * 0.98], 1)
st = np.tanh(st / np.abs(st).max() * 1.15) / np.tanh(1.15) * 0.9
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with wave.open(OUT, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print('soundtrack', round(DUR, 2), 's ->', OUT, '| complete at', round(T_DONE, 2))
