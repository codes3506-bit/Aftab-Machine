"""v3 (2:52 timeline). Original soundtrack for the Khabri-1 film: synthesized pad (builds to the 0:55 option flights) + wind bed + licensed SFX
(video-shotcraft library, free commercial use). -> /home/user/khabri/render/soundtrack_v3.wav (48 kHz stereo, -16 LUFS approx, peak < -1 dBFS)"""
import numpy as np, subprocess, wave, glob
from scipy.signal import butter, sosfilt
SR = 48000; DUR = 172.0; N = int(DUR * SR); t = np.arange(N) / SR; rng = np.random.default_rng(11)
B = glob.glob('/root/.claude/plugins/synced/*/*/assets/audio/sfx')[0]
def load(rel):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{B}/{rel}', '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)
def env(pts): xs, ys = zip(*pts); return np.interp(t, xs, ys)
# ---- pad: D minor -> Bb -> F -> C (tension) -> D (reveal) -> resolve D major at the card
CH_ = [[73.42, 110.0, 146.83, 174.61], [58.27, 87.31, 116.54, 174.61], [65.41, 98.0, 130.81, 164.81], [73.42, 110.0, 146.83, 220.0], [55.0, 82.41, 110.0, 164.81]]
ch = [(0, CH_[0]), (21, CH_[1]), (29, CH_[2]), (39, CH_[3]), (49, CH_[1]), (63, CH_[2]), (69, CH_[3])] + \
     [(69 + 17 * i + o, CH_[(i + j) % 4 + (1 if j == 1 else 0)]) for i in range(5) for j, o in enumerate((6, 12)) if 69 + 17 * i + o < 154] + \
     [(80 + 17 * i, CH_[3]) for i in range(5)] + [(154, CH_[1]), (164, [73.42, 110.0, 146.83, 220.0])]
ch = sorted(ch)
pad = np.zeros(N)
for i, (c0, fr) in enumerate(ch):
    c1 = ch[i + 1][0] if i + 1 < len(ch) else DUR + 2
    w = np.clip((t - c0 + 1.2) / 1.2, 0, 1) * np.clip((c1 + 1.2 - t) / 1.2, 0, 1); m = w > 0
    for k, f in enumerate(fr):
        for det in (-0.13, 0.0, 0.12):
            ph = rng.uniform(0, 6.28)
            pad[m] += w[m] * (np.sin(2 * np.pi * (f + det) * t[m] + ph) + 0.3 * np.sin(4 * np.pi * (f + det) * t[m] + ph)) * (0.9 if k == 0 else 0.5) * (1 + 0.2 * np.sin(2 * np.pi * 0.06 * t[m] + k))
pad = sosfilt(butter(2, 1100, 'low', fs=SR, output='sos'), pad); pad /= np.abs(pad).max()
# low pulse under the track draw-on and the chase (tension), heartbeat-slow
pulse = np.zeros(N)
for b in list(np.arange(49, 63, 1.25)) + [x for x in np.arange(69.5, 153, 1.0) if not (6 <= (x - 69) % 17 < 12)]:
    i0 = int(b * SR); L = int(0.5 * SR); tt = np.arange(L) / SR; pulse[i0:i0 + L] += np.sin(2 * np.pi * (55 - 22 * tt) * tt) * np.exp(-tt * 8)
nz = rng.standard_normal(N); wind = sosfilt(butter(2, [160, 1300], 'band', fs=SR, output='sos'), nz); wind *= 0.55 + 0.45 * np.sin(2 * np.pi * 0.045 * t + 1) ** 2; wind /= np.abs(wind).max()
mix = pad * env([(0, 0), (2, 0.38), (21, 0.38), (49, 0.42), (63, 0.5), (69, 0.6), (152, 0.55), (154, 0.4), (164, 0.45), (170, 0.4), (172, 0)]) \
    + wind * env([(0, 0), (1.5, 0.2), (9, 0.12), (21, 0.2), (29, 0.12), (63, 0.2), (69, 0.14), (154, 0.08), (170, 0.08), (172, 0)]) + pulse * 0.25
# ---- SFX cues (time s, file, gain)
cues = [(8.6, 'transition/air-woosh-deep.mp3', 0.5), (11.0, 'ui/chime-crystal.mp3', 0.25), (14.5, 'text/marker-pen-line.mp3', 0.18), (20.7, 'transition/transition-soft.mp3', 0.35),
        (28.7, 'transition/transition-soft.mp3', 0.35), (29.5, 'data/data-scan.mp3', 0.22), (32.0, 'data/sweep-digital.mp3', 0.2), (38.7, 'transition/swoosh-slow.mp3', 0.35),
        (39.5, 'impact/hit-weak.mp3', 0.3), (48.7, 'transition/transition-soft.mp3', 0.35)] + [(49.3 + 2.6 * i, 'light/shimmer-sparkle-sweep.mp3', 0.16) for i in range(5)] + \
       [(62.7, 'transition/transition-soft.mp3', 0.35), (65.0, 'riser/riser-cine.mp3', 0.55), (69.0, 'impact/impact-cine-big.mp3', 0.6)] + \
       [(68.7 + 17 * i, 'transition/swoosh-slow.mp3', 0.3) for i in range(1, 5)] + [(75.2 + 17 * i, 'ui/chime-crystal.mp3', 0.22) for i in range(5)] + \
       [(80.7 + 17 * i, 'transition/transition-soft.mp3', 0.22) for i in range(5)] + \
       [(153.7, 'transition/transition-soft.mp3', 0.35)] + [(154.8 + 0.45 * i, 'counter/clock-tick-single.mp3', 0.25) for i in range(5)] + [(163.7, 'light/light-aura.mp3', 0.3)]
for tc, f, g in cues:
    x = load(f)
    if f.startswith('riser'):          # align the riser's END to the impact at 75.0
        L = int((69.0 - tc) * SR); x = x[-L:] if len(x) > L else x; i0 = int(69.0 * SR) - len(x)
    else: i0 = int(tc * SR)
    x = x[:N - i0]; mix[i0:i0 + len(x)] += x * g / max(np.abs(x).max(), 1e-6)
mix = np.tanh(mix * 1.1) / np.tanh(1.1)                                   # gentle soft-clip, no hard clipping
rms = np.sqrt(np.mean(mix ** 2)); mix *= 10 ** (-17 / 20) / rms        # ~ -17 dBFS RMS (≈ -16 LUFS for this material)
pk = np.abs(mix).max(); mix *= min(1, 10 ** (-1 / 20) / pk)            # peak <= -1 dBFS
st = np.stack([mix, mix * 0.98 + 0.02 * np.roll(mix, 480)], 1)
with wave.open('/home/user/khabri/render/soundtrack_v3.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print('peak dBFS', round(20 * np.log10(np.abs(st).max()), 2), 'rms dBFS', round(20 * np.log10(np.sqrt(np.mean(st ** 2))), 2))
