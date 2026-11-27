"""Soundtrack for the video: desert wind, rotor hum (follows the shot's rpm), soft ambient pad. -> build/video/soundtrack.wav"""
import json, os, subprocess, wave
import numpy as np
SR = 48000
shots = json.loads(subprocess.check_output(['node', '-e', "const {SHOTS}=require('./timeline');console.log(JSON.stringify(SHOTS.map(s=>({n:s.name,d:s.dur,i:s.interior||0,rpm:s.rpm||[160,160]}))))"], cwd=os.path.dirname(__file__)))
XF = float(subprocess.check_output(['node', '-e', "console.log(require('./timeline').XF)"], cwd=os.path.dirname(__file__)))
starts, t = [], 0.0
for s in shots:
    starts.append(t); t += s['d'] - XF
total = t + XF
n = int(total * SR); tt = np.arange(n) / SR
rng = np.random.default_rng(7)

def lowpass(x, fc):                    # one-pole low-pass response applied in the frequency domain
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(np.fft.rfft(x) / (1 + 1j * f / fc), len(x))
def smooth_env(points):               # piecewise-linear envelope from (time, value)
    ts, vs = zip(*points); return np.interp(tt, ts, vs)

# per-shot curves
inside, rpm = np.zeros(n), np.full(n, 160.0)
for s, st in zip(shots, starts):
    a, b = int(st * SR), int(min(st + s['d'], total) * SR)
    seg = np.linspace(0, 1, b - a)
    inside[a:b] = np.maximum(inside[a:b], s['i'])
    rpm[a:b] = s['rpm'][0] + (s['rpm'][1] - s['rpm'][0]) * np.minimum(1, seg * 1.15)
c = np.concatenate([[0.0], np.cumsum(inside)])          # 1 s moving average via cumulative sum
lo = np.clip(np.arange(n) - SR // 2, 0, n); hi = np.clip(np.arange(n) + SR // 2, 0, n)
inside = (c[hi] - c[lo]) / np.maximum(hi - lo, 1)

noise = rng.standard_normal(n).astype(np.float64)
wind = lowpass(noise, 350) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * tt) ** 2)
wind *= (1 - 0.8 * inside)

phase = np.cumsum(rpm / 60.0 * 2 / SR) * 2 * np.pi          # blade-pass phase (2 blades)
f0 = 70 + (rpm - 160) * 0.12
hum_phase = np.cumsum(f0 / SR) * 2 * np.pi
hum = (np.sin(hum_phase) + 0.5 * np.sin(2 * hum_phase) + 0.25 * np.sin(3 * hum_phase)) * (0.65 + 0.35 * np.sin(phase))
hum *= (0.35 + 0.65 * (rpm - 160) / 360) * (1 - 0.7 * inside)

pad = np.zeros(n)
for f, w in [(110.0, 1.0), (164.8, 0.7), (220.0, 0.6), (261.6, 0.35), (329.6, 0.3)]:
    for det in (-0.6, 0.6):
        pad += w * np.sin(2 * np.pi * (f + det) * tt + rng.uniform(0, 6))
pad *= 0.5 + 0.5 * np.sin(2 * np.pi * tt / 16 - 1.2) ** 2

mix = 0.16 * wind / np.abs(wind).max() + 0.22 * hum / np.abs(hum).max() + 0.14 * pad / np.abs(pad).max()
fade = smooth_env([(0, 0), (0.6, 1), (total - 1.0, 1), (total, 0)])
mix *= fade
stereo = np.stack([mix, np.roll(mix, 240)], 1)
stereo = (stereo / np.abs(stereo).max() * 0.85 * 32767).astype(np.int16)
out = os.path.join(os.path.dirname(__file__), '..', 'build', 'video', 'soundtrack.wav')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(stereo.tobytes())
print('soundtrack', round(total, 2), 's')
