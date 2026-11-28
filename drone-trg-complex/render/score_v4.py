"""Proposal v4 score: confident cinematic-corporate cue, D major, 112 BPM, synthesised in numpy.

Piano ostinato, pizzicato and legato strings, pulse bass, tight drum kit (kick, snare/clap, hats, toms),
synth arpeggio, glockenspiel and bell pad for the night section, risers and impacts on the cuts.
Arrangement follows the clip starts in proposal_timeline.js: intro (title) -> build (site) -> full groove
(time-lapse) -> night breakdown -> groove (exterior) -> light groove (interiors) -> finale (dusk) -> ring-out.
Writes build/proposal4/soundtrack.wav (48 kHz stereo, peak -1 dBFS).
"""
import json, os, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
S = json.loads(subprocess.check_output(['node', '-e', "const {CLIPS,XF}=require('./proposal_timeline');let t=0;const o={};for(const c of CLIPS){o[c.name]=t;t+=c.dur-XF;}o.end=t+XF;console.log(JSON.stringify(o))"], cwd=HERE))
DUR = S['end']
N = int((DUR + 4) * SR)
rng = np.random.default_rng(2026)
OUT = os.path.join(HERE, '..', 'build', 'proposal4', 'soundtrack.wav')
os.makedirs(os.path.dirname(OUT), exist_ok=True)

BPM = 112.0
BEAT = 60 / BPM
BAR = 4 * BEAT
def midi(n): return 440.0 * 2 ** ((n - 69) / 12)
# chords as (bass root, triad notes)
CH = {'D': (38, [62, 66, 69]), 'A': (45, [61, 64, 69]), 'Bm': (47, [62, 66, 71]), 'G': (43, [62, 67, 71]),
      'Em': (40, [64, 67, 71]), 'F#m': (42, [61, 66, 69]), 'Dsus': (38, [62, 67, 69])}
SEC = [  # (start, name, progression)
    (0.0, 'intro', ['D', 'G', 'Bm', 'A']), (S['site_location'], 'build', ['D', 'A', 'Bm', 'G']),
    (S['construction'], 'groove', ['D', 'A', 'Bm', 'G']), (S['night_reveal'], 'night', ['Bm', 'G', 'D', 'A']),
    (S['scope_of_work'], 'groove2', ['G', 'D', 'A', 'Bm']), (S['foyer'], 'light', ['D', 'Bm', 'G', 'A']),
    (S['dusk_closing'], 'finale', ['G', 'A', 'Bm', 'D']), (S['dusk_closing'] + 6.0, 'end', ['D'])]
def section(t):
    s = SEC[0]
    for x in SEC:
        if t >= x[0]: s = x
    return s
def chord(t):
    s = section(t); return s[2][int((t - s[0]) / BAR) % len(s[2])]

def env(n, a, d, sus=1.0, r=0.05):
    e = np.ones(n) * sus; na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nd and na < n: e[na:na + nd] = np.linspace(1, sus, min(nd, n - na))
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e
def fft_filter(x, fn):
    f = np.fft.rfftfreq(len(x), 1 / SR); return np.fft.irfft(np.fft.rfft(x) * fn(f), len(x))
def lp(x, fc): return fft_filter(x, lambda f: 1 / np.sqrt(1 + (f / fc) ** 4))
def hp(x, fc): return fft_filter(x, lambda f: 1 / np.sqrt(1 + (fc / np.maximum(f, 1)) ** 4))
def bp(x, fc, q): return fft_filter(x, lambda f: np.exp(-((f - fc) / (fc / q)) ** 2))
def saw(f, n, det=0.0):
    p = np.cumsum(np.full(n, f * (1 + det))) / SR + rng.random(); return 2 * (p % 1) - 1
L = np.zeros(N); R = np.zeros(N)
def add(at, sig, g=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N: return
    if i < 0: sig = sig[-i:]; i = 0
    j = min(N, i + len(sig)); s = sig[:j - i] * g
    L[i:j] += s * np.sqrt(0.5 * (1 - pan)) * 1.414; R[i:j] += s * np.sqrt(0.5 * (1 + pan)) * 1.414

# ---------------- instruments ----------------
def piano(f, dur, vel=1.0):
    n = int((dur + 1.2) * SR); tt = np.arange(n) / SR; out = np.zeros(n)
    for k in range(1, 9):
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)
        if fk > 12000: break
        out += np.sin(2 * np.pi * fk * tt) * (0.9 / k ** 1.25) * np.exp(-tt * (1.2 + 0.9 * k) * (f / 400) ** 0.3)
    out += bp(rng.standard_normal(n) * np.exp(-tt * 60), 2500, 1.2) * 0.08
    rel = np.ones(n); i = int(dur * SR); rel[i:] = np.exp(-(tt[i:] - dur) * 9)
    return out * rel * vel * env(n, 0.002, 0, 1, 0.01)
def pluck(f, dur=0.6):
    n = int(dur * SR); per = max(2, int(SR / f)); buf = rng.uniform(-1, 1, per); out = np.zeros(n)
    for a in range(0, n, per): b = min(n, a + per); out[a:b] = buf[:b - a]; buf = 0.5 * (buf + np.roll(buf, -1)) * 0.996
    return lp(out, 3500) * env(n, 0.001, 0, 1, 0.05)
def pad(f, dur, bright=2200, a=0.6):
    n = int(dur * SR); x = sum(saw(f, n, d) for d in (-0.006, -0.002, 0.003, 0.007)) / 4
    return lp(x, bright) * env(n, a, 0, 1, min(0.6, dur / 3))
def bass(f, dur):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * tt) * 0.8 + lp(saw(f, n), 600) * 0.35
    return x * env(n, 0.004, 0.12, 0.75, 0.03)
def kick():
    n = int(0.45 * SR); tt = np.arange(n) / SR; fr = 48 + 110 * np.exp(-tt * 28)
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt * 7.5) + rng.standard_normal(n) * np.exp(-tt * 300) * 0.12
def snare():
    n = int(0.35 * SR); tt = np.arange(n) / SR
    return bp(rng.standard_normal(n), 3200, 0.6) * np.exp(-tt * 16) * 0.9 + np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 28) * 0.5
def clap():
    n = int(0.3 * SR); tt = np.arange(n) / SR; e = sum(np.exp(-np.maximum(tt - d, 0) * 90) * (tt >= d) for d in (0, 0.011, 0.023))
    return bp(rng.standard_normal(n), 1600, 1.0) * (e + np.exp(-tt * 14) * 0.5) * 0.7
def hat(open_=False):
    n = int((0.25 if open_ else 0.06) * SR); tt = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7500) * np.exp(-tt * (14 if open_ else 70)) * 0.5
def tom(f):
    n = int(0.6 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(f * (1 + 0.6 * np.exp(-tt * 18))) / SR) * np.exp(-tt * 6)
def shaker():
    n = int(0.09 * SR); tt = np.arange(n) / SR; return hp(rng.standard_normal(n), 5000) * np.sin(np.pi * tt / tt[-1]) * 0.35
def glock(f, dur=1.6):
    n = int(dur * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt + 1.8 * np.sin(2 * np.pi * f * 3.5 * tt) * np.exp(-tt * 6)) * np.exp(-tt * 2.6)) * env(n, 0.002, 0, 1, 0.05)
def riser(dur):
    n = int(dur * SR); tt = np.arange(n) / SR; x = rng.standard_normal(n); k = tt / dur
    out = np.zeros(n)
    for a in range(0, n, 2048):
        b = min(n, a + 2048); fc = 300 + 7000 * k[a] ** 2; out[a:b] = bp(x[a:b], fc, 1.5)
    return out * k ** 2 * 0.8
def impact():
    n = int(3.0 * SR); tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(32 + 60 * np.exp(-tt * 6)) / SR) * np.exp(-tt * 1.6)
    return boom + lp(rng.standard_normal(n), 900) * np.exp(-tt * 3.5) * 0.4
def swell(dur):
    n = int(dur * SR); tt = np.arange(n) / SR; return hp(rng.standard_normal(n), 3000) * (tt / dur) ** 3 * 0.35

# ---------------- arrangement ----------------
def energy(name):
    return {'intro': 0.35, 'build': 0.6, 'groove': 1.0, 'night': 0.3, 'groove2': 0.9, 'light': 0.55, 'finale': 1.0, 'end': 0.0}[name]
nb = int(DUR / BEAT) + 1
for bi in range(nb):
    t0 = bi * BEAT
    if t0 > DUR + 0.5: break
    sec = section(t0); name = sec[1]; root, tri = CH[chord(t0)]; beat_in_bar = bi % 4
    e = energy(name)
    if name == 'end':
        if bi == int(SEC[-1][0] / BEAT):
            for nn in tri + [tri[0] - 12, tri[0] + 12]: add(t0, pad(midi(nn), 5.5, 1800, 0.05), 0.12, rng.uniform(-0.4, 0.4))
            add(t0, piano(midi(root + 12), 4.0), 0.35); add(t0, piano(midi(tri[0] + 12), 4.0), 0.25); add(t0, impact(), 0.45)
        continue
    # bar-level: pad chords, bass line
    if beat_in_bar == 0:
        bright = 1400 + 2600 * e
        for nn in tri: add(t0, pad(midi(nn), BAR + 0.3, bright, 0.25 if e > 0.5 else 0.8), 0.07 + 0.04 * e, rng.uniform(-0.5, 0.5))
        add(t0, pad(midi(tri[0] - 12), BAR + 0.3, 900, 0.4), 0.06)
    # piano ostinato (8ths): root-fifth-octave pattern on the triad
    pat = [tri[0], tri[1], tri[2], tri[1] + 12 if name in ('groove', 'finale') else tri[1]]
    for h in range(2):
        nn = pat[(beat_in_bar * 2 + h) % 4] + (12 if name in ('night', 'end') else 0)
        add(t0 + h * BEAT / 2 + rng.normal(0, 0.003), piano(midi(nn), BEAT / 2 * 0.9, 0.9 if h == 0 else 0.7), 0.13 if name != 'night' else 0.10, 0.25)
    if name == 'night':
        if beat_in_bar in (0, 2): add(t0, glock(midi(tri[2] + 12)), 0.10, -0.3)
        if beat_in_bar == 1: add(t0 + BEAT / 2, glock(midi(tri[1] + 24), 2.4), 0.06, 0.4)
        continue
    # bass: 8th-note pulse (ducked under the kick)
    if e >= 0.55:
        for h in range(2): add(t0 + h * BEAT / 2, bass(midi(root - 12 if root > 40 else root), BEAT / 2 * 0.85), 0.42 * e * (0.75 if h else 1.0))
    elif name == 'intro' and beat_in_bar == 0:
        add(t0, bass(midi(root - 12 if root > 40 else root), BAR * 0.9), 0.3)
    # pizzicato / arpeggio
    if e >= 0.55:
        arp = [tri[0] + 12, tri[2], tri[1] + 12, tri[2] + 12]
        for h in range(2): add(t0 + h * BEAT / 2, pluck(midi(arp[(beat_in_bar * 2 + h) % 4])), 0.16 * e, -0.45 + 0.9 * ((bi + h) % 2))
    # drums
    if name in ('groove', 'groove2', 'finale', 'build'):
        full = name != 'build' or (t0 - sec[0]) > BAR * 2
        if beat_in_bar in (0, 2) or (name != 'build' and beat_in_bar == 3 and bi % 8 == 7): add(t0, kick(), 0.75)
        if full and beat_in_bar in (1, 3): add(t0, snare(), 0.32); add(t0, clap(), 0.22)
        for h in range(2): add(t0 + h * BEAT / 2, hat(open_=(h == 1 and beat_in_bar == 3)), 0.16 if h else 0.11, 0.35)
        if name == 'finale' and bi % 16 == 15:
            for k, f in enumerate([180, 140, 110, 85]): add(t0 + k * BEAT / 4, tom(f), 0.35, -0.3 + 0.2 * k)
    elif name == 'light':
        if beat_in_bar == 0: add(t0, kick(), 0.45)
        for h in range(4): add(t0 + h * BEAT / 4, shaker(), 0.18 if h % 2 else 0.1, 0.3)
        if beat_in_bar == 2: add(t0, clap(), 0.12)

# hits and transitions on the cuts
for name in ('site_location', 'construction', 'scope_of_work', 'foyer', 'dusk_closing'):
    add(S[name] - 2.0, riser(2.0), 0.25); add(S[name], impact(), 0.32)
add(S['night_reveal'] - 1.5, swell(1.5), 0.4); add(S['night_reveal'], impact(), 0.25)
add(0.0, swell(1.2), 0.2); add(1.0, impact(), 0.4)
# a construction-site texture under the time-lapse (distant machinery rumble)
n = int(28 * SR); tt = np.arange(n) / SR
rum = lp(rng.standard_normal(n), 140) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.31 * tt) ** 2) * env(n, 1.5, 0, 1, 2.0)
add(S['construction'], rum, 0.25)

# ---------------- mix: sidechain, reverb, master ----------------
def reverb(x, secs=2.2, wet=0.22):
    n = int(secs * SR); tt = np.arange(n) / SR; ir = rng.standard_normal(n) * np.exp(-tt * 6.9 / secs); ir = lp(ir, 5000); ir /= np.sqrt((ir ** 2).sum())
    m = len(x) + n; F = 1 << (m - 1).bit_length(); y = np.fft.irfft(np.fft.rfft(x, F) * np.fft.rfft(ir, F), F)[:len(x)]
    return x + y * wet
L = reverb(L); R = reverb(R[::-1])[::-1] * 0.5 + reverb(R) * 0.5
# soft sidechain pump on everything except the kick region is approximated by the kick envelope
duck = np.ones(N)
for bi in range(nb):
    t0 = bi * BEAT; nm = section(t0)[1]
    if nm in ('groove', 'groove2', 'finale') and bi % 4 in (0, 2):
        i = int(t0 * SR); k = np.arange(int(0.22 * SR)); j = min(N, i + len(k)); duck[i:j] = np.minimum(duck[i:j], 0.7 + 0.3 * (k[:j - i] / len(k)))
L *= duck; R *= duck
end = int((DUR + 3.5) * SR); L, R = L[:end], R[:end]
fo = int(2.5 * SR); L[-fo:] *= np.linspace(1, 0, fo) ** 2; R[-fo:] *= np.linspace(1, 0, fo) ** 2
st = np.stack([L, R], 1); st = np.tanh(st / np.abs(st).max() * 1.6) ; st *= 0.89 / np.abs(st).max()
with wave.open(OUT, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
print(OUT, round(len(st) / SR, 2), 's')
