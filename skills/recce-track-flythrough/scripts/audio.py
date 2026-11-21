"""Soundtrack: synthesized cinematic pad + wind bed + timed SFX (video-shotcraft library). -> out/soundtrack.wav"""
import numpy as np, subprocess, wave, sys
sys.path.insert(0, '/home/user/recce/work')
from timeline import *
from scipy.signal import butter, sosfilt
SR = 48000; N = int(DUR * SR); t = np.arange(N) / SR
B = '/root/.claude/plugins/synced/5680f315-2fdc-44e7-a126-21641b1ed974_87e12e4a-faec-48c3-a56b-30a37ba29697/74655670-1540-4e3d-8509-c2f446898c2c/assets/audio/sfx'
rng = np.random.default_rng(7)

def env(x, pts):
    xs, ys = zip(*pts); return np.interp(x, xs, ys)
# --- pad: D minor, chord changes per section
chords = [(0, [73.42, 110.0, 146.83, 174.61]), (32, [65.41, 98.0, 130.81, 155.56]), (45, [73.42, 110.0, 146.83, 220.0]),
          (63, [58.27, 87.31, 116.54, 174.61]), (74, [73.42, 110.0, 146.83, 174.61]), (81, [55.0, 82.41, 110.0, 164.81]),
          (93, [73.42, 110.0, 146.83, 220.0]), (115, [65.41, 98.0, 130.81, 196.0]), (128, [58.27, 87.31, 116.54, 174.61]), (140, [73.42, 110.0, 146.83, 220.0])]
pad = np.zeros(N)
for i, (c0, fr) in enumerate(chords):
    c1 = chords[i + 1][0] if i + 1 < len(chords) else DUR
    w = np.clip((t - c0 + 1.5) / 1.5, 0, 1) * np.clip((c1 + 1.5 - t) / 1.5, 0, 1)
    m = w > 0
    for k, f in enumerate(fr):
        for det in (-0.12, 0.0, 0.11):
            ph = rng.uniform(0, 6.28)
            s = np.sin(2 * np.pi * (f + det) * t[m] + ph) + 0.35 * np.sin(2 * np.pi * 2 * (f + det) * t[m] + ph * 1.3)
            pad[m] += w[m] * s * (0.9 if k == 0 else 0.55) * (1 + 0.25 * np.sin(2 * np.pi * 0.07 * t[m] + k))
pad = sosfilt(butter(2, 900, 'low', fs=SR, output='sos'), pad)
pad /= np.abs(pad).max()
# --- wind
nz = rng.standard_normal(N); wind = sosfilt(butter(2, [180, 1400], 'band', fs=SR, output='sos'), nz)
wind *= (0.55 + 0.45 * np.sin(2 * np.pi * 0.05 * t + 1.2) ** 2); wind /= np.abs(wind).max()
# --- low pulse during fly-through (tension), muted in pauses
pulse = np.zeros(N)
for b in np.arange(SHOTS[4][0], SHOTS[4][1], 1.0):
    if pause_at(b): continue
    i0 = int(b * SR); L = int(0.45 * SR); tt = np.arange(L) / SR
    pulse[i0:i0 + L] += np.sin(2 * np.pi * (52 - 20 * tt) * tt) * np.exp(-tt * 9)
lvl_pad = env(t, [(0, 0), (1.5, 0.5), (9, 0.42)] + [p for a_, b_, _ in PAUSES for p in ((a_, 0.3), (b_, 0.42))] + [(SHOTS[5][0], 0.46), (SHOTS[6][0], 0.36), (DUR - 3, 0.36), (DUR, 0)])
lvl_wind = env(t, [(0, 0), (2, 0.16), (SHOTS[4][0], 0.14), (SHOTS[4][0] + 5, 0.2), (SHOTS[5][0], 0.2), (SHOTS[6][0], 0.1), (DUR - 3, 0.1), (DUR, 0)])
mix = pad * lvl_pad + wind * lvl_wind + pulse * 0.22
mix = np.stack([mix, mix], 1)
# stereo width on wind
mix[:, 1] += 0.04 * np.roll(wind, 900) * lvl_wind

def load(name):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{B}/{name}', '-f', 's16le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).reshape(-1, 2) / 32768.0
def sfx(name, at, g=0.7):
    a = load(name); i0 = int(at * SR); n = min(len(a), N - i0)
    if n > 0: mix[i0:i0 + n] += a[:n] * g

sfx('riser/riser-cine.mp3', 0.0, 0.55); sfx('impact/impact-cine-big.mp3', 1.35, 0.75)
sfx('transition/swoosh-slow.mp3', 8.6, 0.55)
for k in range(10): sfx('ui/pop.mp3', 11 + k * 0.45, 0.22)
sfx('ui/ui-popup-dry.mp3', 13.0, 0.35)
sfx('transition/air-woosh-deep.mp3', 25.0, 0.55)
B0, B1 = PAUSES[0][0], PAUSES[0][1]
sfx('transition/transition-soft.mp3', B0 - 0.2, 0.5)
for k, at in enumerate((B0 + 0.5, B0 + 1.6, B0 + 2.6)): sfx('ui/ui-popup-dry.mp3', at, 0.4)
sfx('ui/ui-notify-tech.mp3', B0 + 8.6, 0.35)
sfx('riser/riser-cine.mp3', B1 - 3.6, 0.35)
sfx('transition/air-whoosh-powerful.mp3', B1 - 0.4, 0.7)
# N xing ticks during fly-through
for l in SC['labels']:
    if l['kind'] in ('nx', 'km'):
        idx = np.where(CHS >= l['ch'] - (0.05 if l['kind'] == 'nx' else 0))[0]
        idx = idx[idx > SHOTS[4][0] * FPS]
        if len(idx): sfx('ui/ui-select-click.mp3' if l['kind'] == 'nx' else 'ui/switch-tap.mp3', idx[0] / FPS, 0.25)
for a, b, k in PAUSES[1:]:
    sfx('transition/transition-soft.mp3', a - 0.2, 0.5)
    sfx('ui/ui-popup-dry.mp3', a + 0.4, 0.4)
    n = {'ascent': 2, 'crest': 3}.get(k, 0)
    for j in range(n): sfx('camera/camera-lens-shutter.mp3', a + 1.0 + 0.7 * j, 0.45)
    sfx('transition/whoosh-fast.mp3', b - 0.3, 0.55)
sfx('impact/impact-deep-whoosh.mp3', PAUSES[2][0] - 0.4, 0.55)
G0, FN = SHOTS[5][0], SHOTS[6][0]
sfx('transition/swoosh-slow.mp3', G0 - 1.0, 0.5); sfx('data/data-scan.mp3', G0 + 2.0, 0.3)
sfx('transition/transition-tech.mp3', FN + 0.6, 0.45); sfx('transition/transition-tech.mp3', FN + (8.6 if VID == 1 else 6.6), 0.45)
sfx('impact/impact-transition.mp3', DUR - (7.3 if VID == 1 else 10.9), 0.45)
fo = np.clip((DUR - t) / 2.5, 0, 1)[:, None]; mix *= fo
pk = np.abs(mix).max(); mix = np.tanh(mix / pk * 1.4) / np.tanh(1.4) * 0.89
out = (mix * 32767).astype(np.int16)
with wave.open(f'{R}/out/soundtrack{VID}.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('ok', DUR)
