"""v4 soundtrack: voice-over (work/vo/*.wav at the timeline cues) over an original synthesized score + wind bed + licensed SFX
(video-shotcraft library, free commercial use). Music ducks ~9 dB under the voice. Reads work/timeline_v4.json.
-> /home/user/khabri/render/v4/soundtrack_v4.wav (48 kHz stereo, -16 LUFS integrated, true peak <= -1.5 dBTP via loudnorm)"""
import json, numpy as np, subprocess, wave, glob, soundfile as sf
from scipy.signal import butter, sosfilt
from scipy.ndimage import uniform_filter1d
from geo import R
TL = json.load(open(f'{R}/work/timeline_v4.json')); SH = {s['key']: s for s in TL['shots']}
SR = 48000; DUR = TL['total'] + 0.5; N = int(DUR * SR); t = np.arange(N) / SR; rng = np.random.default_rng(11)
B = glob.glob('/root/.claude/plugins/synced/*/*/assets/audio/sfx')[0]
def load(rel):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{B}/{rel}', '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)
def env(pts): xs, ys = zip(*pts); return np.interp(t, xs, ys)
S0 = lambda k: SH[k]['t0']; S1 = lambda k: SH[k]['t1']
OPT = ['T1', 'T2', 'T3', 'T4', 'T5']
# ---- score: slow D-minor pad, chord per shot, tension under the options, resolve to D major at the close
CH_ = [[73.42, 110.0, 146.83, 174.61], [58.27, 87.31, 116.54, 174.61], [65.41, 98.0, 130.81, 164.81], [73.42, 110.0, 146.83, 220.0], [55.0, 82.41, 110.0, 164.81]]
plan = {'open': 0, 'orient': 1, 'air': 2, 'slope': 3, 'section': 1, 'climb': 2, 'align': 3, 'postair': 4, 'T1': 0, 'T2': 1, 'T3': 2, 'T4': 3, 'T5': 1, 'top1': 2, 'top2': 0, 'compare': 1}
ch = [(S0(k), CH_[v]) for k, v in plan.items()] + [(S0('close'), [73.42, 110.0, 146.83, 185.0])]
pad = np.zeros(N)
for i, (c0, fr) in enumerate(ch):
    c1 = ch[i + 1][0] if i + 1 < len(ch) else DUR + 2
    w = np.clip((t - c0 + 1.5) / 1.5, 0, 1) * np.clip((c1 + 1.5 - t) / 1.5, 0, 1); m = w > 0
    for k, f in enumerate(fr):
        for det in (-0.13, 0.0, 0.12):
            ph = rng.uniform(0, 6.28)
            pad[m] += w[m] * (np.sin(2 * np.pi * (f + det) * t[m] + ph) + 0.3 * np.sin(4 * np.pi * (f + det) * t[m] + ph)) * (0.9 if k == 0 else 0.5) * (1 + 0.2 * np.sin(2 * np.pi * 0.06 * t[m] + k))
pad = sosfilt(butter(2, 1000, 'low', fs=SR, output='sos'), pad); pad /= np.abs(pad).max()
pulse = np.zeros(N); beats = list(np.arange(S0('align') + 0.3, S1('align'), 1.25))
for k in OPT: beats += list(np.arange(S0(k) + 0.5, S0(k) + 6.0, 1.0)) + list(np.arange(S1(k) - 5.0, S1(k) - 0.2, 1.0))
for b in beats:
    i0 = int(b * SR); L = int(0.5 * SR); tt = np.arange(L) / SR; pulse[i0:i0 + L] += np.sin(2 * np.pi * (55 - 22 * tt) * tt) * np.exp(-tt * 8)
nz = rng.standard_normal(N); wind = sosfilt(butter(2, [160, 1300], 'band', fs=SR, output='sos'), nz); wind *= 0.55 + 0.45 * np.sin(2 * np.pi * 0.045 * t + 1) ** 2; wind /= np.abs(wind).max()
music = pad * env([(0, 0), (2, 0.42), (S0('postair'), 0.5), (S0('T1'), 0.6), (S1('T5'), 0.55), (S0('close'), 0.5), (DUR - 2.5, 0.45), (DUR, 0)]) \
      + wind * env([(0, 0), (1.5, 0.22), (S0('orient'), 0.12), (S0('air'), 0.22), (S0('slope'), 0.1), (S0('climb'), 0.22), (S0('align'), 0.1), (S0('top1'), 0.24), (S0('top2'), 0.08), (DUR, 0)]) + pulse * 0.25
sfx = np.zeros(N)
cues = [(S0(k) - 0.3, 'transition/transition-soft.mp3', 0.35) for k in SH if k not in ('open', 'T1')] + [(S0('open') + 1.2, 'transition/air-woosh-deep.mp3', 0.45), (S0('orient') + 0.2, 'ui/chime-crystal.mp3', 0.2)] + \
       [(S0('align') + 0.3 + 2.6 * i, 'light/shimmer-sparkle-sweep.mp3', 0.14) for i in range(5)] + [(S0('T1') - 3.5, 'riser/riser-cine.mp3', 0.5), (S0('T1'), 'impact/impact-cine-big.mp3', 0.5)] + \
       [(S0(k) + 6.0, 'ui/chime-crystal.mp3', 0.2) for k in OPT] + [(S0('top2') + 8.0, 'data/data-scan.mp3', 0.18)] + [(S0('compare') + 5.6 + 0.45 * i, 'counter/clock-tick-single.mp3', 0.2) for i in range(5)] + \
       [(S0('close') + 0.3, 'light/light-aura.mp3', 0.28)]
for tc, f, g in cues:
    x = load(f)
    if f.startswith('riser'): L = int(3.5 * SR); x = x[-L:] if len(x) > L else x; i0 = int(S0('T1') * SR) - len(x)
    else: i0 = int(max(0, tc) * SR)
    x = x[:N - i0]; sfx[i0:i0 + len(x)] += x * g / max(np.abs(x).max(), 1e-6)
# ---- voice
vo = np.zeros(N)
for s in TL['shots']:
    if s['vo'] is None: continue
    a, sr = sf.read(f"{R}/work/vo/{s['key']}.wav"); assert sr == SR
    i0 = int(s['vo'] * SR); a = a[:N - i0]; vo[i0:i0 + len(a)] += a
vo /= np.abs(vo).max(); vo *= 0.89
act = uniform_filter1d((np.abs(vo) > 0.02).astype(float), int(0.25 * SR)); act = uniform_filter1d(np.clip(act * 4, 0, 1), int(0.6 * SR))
duck = 1 - 0.65 * act                                                                   # ~ -9 dB under the voice
bed = np.tanh((music * duck + sfx * (1 - 0.4 * act)) * 1.1) / np.tanh(1.1)
bed *= 10 ** (-24 / 20) / np.sqrt(np.mean(bed ** 2))                                   # bed ~ -24 dBFS RMS
vrms = np.sqrt(np.mean(vo[np.abs(vo) > 0.02] ** 2)); vo *= 10 ** (-15 / 20) / vrms     # speech ~ -15 dBFS RMS while talking
mix = bed + vo
st = np.stack([mix + 0.004 * np.roll(bed, 480), mix - 0.004 * np.roll(bed, 480)], 1); st /= max(1.0, np.abs(st).max() / 0.95)
raw = '/home/user/khabri/render/v4/mix_raw.wav'
with wave.open(raw, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=9', '-ar', '48000', '/home/user/khabri/render/v4/soundtrack_v4.wav'], check=True)
print('soundtrack', round(DUR, 1), 's')
