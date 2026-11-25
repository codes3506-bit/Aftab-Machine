import json, sys, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy.ndimage import map_coordinates
from engine import *
from overlay import *

O = '/home/user/Aftab-Machine/output'; SP = sys.argv[1] if len(sys.argv) > 1 else O
W, H = 3840, 2160; s = 2.0
S = Scene(W, H)
G = np.load(f'{R}/work/grid.npz'); gx0, gy0, st = float(G['x0']), float(G['y0']), float(G['st']); LACC = np.log10(np.maximum(G['ACC'], 0.01))
def acc_fn(X, Y):
    fi = (Y - gy0) / st; fj = (X - gx0) / st; v = map_coordinates(LACC, [fi, fj], order=1, mode='constant', cval=-2)
    return np.where((fi < 0) | (fj < 0) | (fi > LACC.shape[0] - 1) | (fj > LACC.shape[1] - 1), -2, v)
S.set_acc(acc_fn)
PR = json.load(open(f'{R}/work/profiles.json')); MT = {t['name']: t for t in json.load(open(f'{R}/work/metrics.json'))['tracks']}
pe, pn = en(63.43978, 25.42739); S.focus = (float(pe), float(pn)); pz = float(S.height(np.array([pe]), np.array([pn]))[0])

def track3d(llz, step=2.0, lift=1.2):
    a = np.array(llz); e, n = en(a[:, 0], a[:, 1]); P = np.c_[e, n]
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; t = np.arange(0, d[-1], step)
    e2 = np.interp(t, d, e); n2 = np.interp(t, d, n); return np.c_[e2, n2, S.height(e2, n2) + lift], t
TR = {k: track3d(v['ll']) for k, v in PR.items()}
KM = [p for p in kml() if p['kind'] == 'line']
KMZ3 = [track3d([q for q in p['pts']], 4.0)[0] for p in KM]

def items(focus=None, pulse=None, dimothers=False):
    it = []
    for P in KMZ3:
        x, y, v = S.visible(P); it.append(dict(xy=np.c_[x, y], vis=v, col=COL['KMZ'], w=2.5, glow=0.35, ghost=False))
    for k in ['T1', 'T2', 'T3', 'T4', 'T5']:
        P, _ = TR[k]; x, y, v = S.visible(P); hot = (k == focus)
        it.append(dict(xy=np.c_[x, y], vis=v, col=tuple(int(c * (0.55 if (dimothers and not hot) else 1)) for c in COL[k]), w=6 if hot else (2.2 if dimothers else 4.2), glow=1.6 if hot else (0.2 if dimothers else 0.8),
                       pulse=pulse if hot else None))
    return it

def heading(eye, tgt): return float(np.degrees(np.arctan2(tgt[0] - eye[0], tgt[1] - eye[1])))

def end_xy(k, frac=1.0):
    P, _ = TR[k]; i = int(frac * (len(P) - 1)); x, y, v = S.visible(P[i:i + 1]); return (x[0], y[0], v[0])

# ---------------- SF1 : orbital establishing, all tracks
eye = (pe - 1500, pn - 2350, 1050); tgt = (pe + 150, pn + 250, pz - 60)
img = S.render(eye, tgt, fov=36, sun_az=115, sun_el=20)
img = glow_tracks(grade(img), items(), s)
b = to_pil(img)
x, y, v = S.visible(np.array([[pe, pn, pz + 2]])); pin(b, (x[0], y[0]), 'KHABRI-1 HILL POST', 'RL 133 m  ·  25°25\'38.6"N 63°26\'23.2"E', s=s, up=150)
for k, fr, dx, dy in [('T1', 0.15, -60, 40), ('T2', 0.35, -120, 0), ('T3', 0.25, -40, -60), ('T4', 0.3, 110, 30), ('T5', 0.45, -40, -60)]:
    x, y, v = end_xy(k, fr)
    if v: tag(b, (x, y), k, COL[k], s, dx, dy)
title_bar(b, 'TRACK RECCE  ·  KHABRI-1 HILL POST', 'Five alignments considered  ·  Cop GLO-30 terrain, VE 1.0  ·  Esri imagery', s)
north_arrow(b, (W - 110 * s, H - 110 * s), heading(eye, tgt), s)
lg = [('T1', 'Direct climb – S spur'), ('T2', 'Graded S spur 1:7'), ('T3', 'W spur / ridge'), ('T4', 'E flank'), ('T5', 'Rear / N foothill'), ('KMZ', 'KMZ tr (existing / planned)')]
panel(b, (60 * s, H - 400 * s, 560 * s, H - 60 * s), 'ALIGNMENTS', s=s)
d = ImageDraw.Draw(b)
for i, (k, t) in enumerate(lg):
    yy = H - 330 * s + i * 42 * s; d.line((90 * s, yy + 12 * s, 140 * s, yy + 12 * s), fill=COL[k], width=int(6 * s)); d.text((160 * s, yy), f'{k if k != "KMZ" else ""}  {t}'.strip(), font=F(24 * s, 'Medium'), fill=(235, 238, 245))
b.convert('RGB').save(f'{SP}/styleframe_1_establishing.png')
print('sf1')

# ---------------- SF2 : terrain analysis (slope + drainage) with drone PiP
eye = (pe + 700, pn - 1500, 520); tgt = (pe - 150, pn + 200, pz - 50)
img = S.render(eye, tgt, fov=40, slope_mix=1.0, drain_mix=1.0, sun_az=115, sun_el=24)
img = glow_tracks(grade(img), items(), s * 0.8)
b = to_pil(img)
x, y, v = S.visible(np.array([[pe, pn, pz + 2]])); pin(b, (x[0], y[0]), 'HILL POST', 'RL 133', s=s, up=120)
title_bar(b, 'TERRAIN  ·  SLOPE & DRAINAGE', 'Slope from Cop GLO-30 (30 m)  ·  D8 flow lines > 2 ha', s)
# slope legend
panel(b, (60 * s, H - 330 * s, 620 * s, H - 60 * s), 'SLOPE (deg)', s=s)
ramp = np.array([[26, 153, 77], [253, 224, 102], [245, 110, 66], [166, 0, 38]], float)
bar = np.zeros((int(28 * s), int(480 * s), 3), np.uint8)
for i in range(bar.shape[1]):
    t = i / bar.shape[1] * 3; k = min(int(t), 2); bar[:, i] = ramp[k] + (ramp[k + 1] - ramp[k]) * (t - k)
b.paste(Image.fromarray(bar), (int(90 * s), int(H - 245 * s)))
for i, lab in enumerate(['0', '10', '20', '30', '40+']): text(b, (90 * s + i * 120 * s, H - 205 * s), lab, F(22 * s, 'Medium'), anchor='ma', sc=s)
d = ImageDraw.Draw(b); d.line((90 * s, H - 135 * s, 150 * s, H - 135 * s), fill=(64, 191, 255), width=int(6 * s)); text(b, (165 * s, H - 150 * s), 'Drainage line / nala', F(24 * s, 'Medium'), sc=s)
d.text((90 * s, H - 110 * s), 'Gentle (<6°) ground left untinted', font=F(20 * s, 'Regular'), fill=(190, 195, 205))
# drone PiP (WhatsApp 01:03) with geotag
dr = Image.open('/tmp/claude-0/-home-user-Aftab-Machine/d35c83c0-ed16-5ab8-ac1e-72068dbafa01/scratchpad/wa1/f064.jpg').convert('RGB'); dr = dr.crop((0, 0, 848, 400))
dr = Image.fromarray((grade(np.asarray(dr).astype(np.float32) / 255, 0.6) * 255).astype(np.uint8)).resize((int(1100 * s / 2 * 1.0), int(1100 * s / 2 * 400 / 848)), Image.LANCZOS)
px, py = W - dr.size[0] - 70 * s, 170 * s
panel(b, (px - 18 * s, py - 18 * s, px + dr.size[0] + 18 * s, py + dr.size[1] + 150 * s), None, s=s)
b.paste(dr, (int(px), int(py)))
text(b, (px, py + dr.size[1] + 18 * s), 'DRONE 01:03  ·  post ridge S face, looking N', F(24 * s, 'Bold'), fill=GOLD, sc=s)
text(b, (px, py + dr.size[1] + 56 * s), 'Bedding outcrops along S face · strike ENE–WSW', F(22 * s, 'Medium'), sc=s)
text(b, (px, py + dr.size[1] + 92 * s), 'ASSESSED · clip has no GPS telemetry', F(20 * s, 'SemiBold'), fill=(255, 170, 120), sc=s)
north_arrow(b, (W - 110 * s, H - 110 * s), heading(eye, tgt), s)
b.convert('RGB').save(f'{SP}/styleframe_2_terrain.png'); print('sf2')

# ---------------- SF3 : reveal – low chase on T5 (rear / N foothill)
P, t = TR['T5']; i = int(0.42 * (len(P) - 1)); a = P[max(0, i - 40)]; c = P[i]
fwd = (c[:2] - a[:2]); fwd /= np.linalg.norm(fwd)
eye = (c[0] - fwd[0] * 330 - 120, c[1] - fwd[1] * 330 + 160, c[2] + 210); tgt = ((c[0] + pe) / 2, (c[1] + pn) / 2, pz - 30)
img = S.render(eye, tgt, fov=44, sun_az=115, sun_el=26)
img = glow_tracks(grade(img), items('T5', pulse=0.42, dimothers=True), s)
b = to_pil(img)
x, y, v = S.visible(np.array([[pe, pn, pz + 2]])); pin(b, (x[0], y[0]), 'KHABRI-1 HILL POST', 'RL 133', s=s, up=60)
title_bar(b, 'THE REAR APPROACH  ·  T5 N FOOTHILL', 'Skirts the mount to the rear, runs N along the foothill, climbs to the post from the N', s)
pr = PR['T5']; ss_ = np.array(pr['s']); zz = np.array(pr['z']); gg = np.abs(np.array(pr['g'])) * 100; k = int(0.42 * (len(ss_) - 1))
jch = MT['T5']['junction_ch_km']
panel(b, (W - 720 * s, 170 * s, W - 70 * s, 500 * s), 'T5  ·  LIVE', s=s)
for j, (lab, val) in enumerate([('CH', f'{jch + ss_[k] / 1000:.2f} km'), ('ELEV', f'{zz[k]:.0f} m'), ('GRADE', f'1:{100 / max(gg[k], 0.5):.0f}  ({gg[k]:.1f}%)')]):
    yy = 250 * s + j * 90 * s; text(b, (W - 690 * s, yy), lab, F(26 * s, 'SemiBold'), fill=(170, 178, 192), sc=s); text(b, (W - 100 * s, yy - 6 * s), val, MONO(44 * s), fill=(255, 255, 255), anchor='ra', sc=s)
# mini profile with all tracks muted, T5 gold + playhead
px0, py0, pw, ph = 60 * s, H - 420 * s, 900 * s, 330 * s
panel(b, (px0, py0, px0 + pw, py0 + ph), 'ELEVATION PROFILE', s=s)
d = ImageDraw.Draw(b); gx0_, gy0_, gw, gh = px0 + 40 * s, py0 + 80 * s, pw - 80 * s, ph - 120 * s
mx = max(np.array(p['s'])[-1] for p in PR.values())
for kk, p in PR.items():
    q = [(gx0_ + si / mx * gw, gy0_ + gh - (zi - 20) / 140 * gh) for si, zi in zip(p['s'][::4], p['z'][::4])]
    d.line(q, fill=COL[kk] + ((255,) if kk == 'T5' else (110,)), width=int((5 if kk == 'T5' else 2) * s))
hx = gx0_ + ss_[k] / mx * gw; hy = gy0_ + gh - (zz[k] - 20) / 140 * gh
d.ellipse((hx - 9 * s, hy - 9 * s, hx + 9 * s, hy + 9 * s), fill=(255, 255, 255))
for zl in (40, 80, 120, 160):
    yl = gy0_ + gh - (zl - 20) / 140 * gh; d.line((gx0_, yl, gx0_ + gw, yl), fill=(255, 255, 255, 40), width=1); d.text((gx0_ - 8 * s, yl), f'{zl}', font=F(18 * s), fill=(170, 178, 192), anchor='rm')
d.text((gx0_ + gw, py0 + 30 * s), 'm  vs  km from junction', font=F(18 * s), fill=(170, 178, 192), anchor='ra'); d.text((gx0_, gy0_ + gh + 6 * s), '0', font=F(20 * s), fill=(180, 186, 198))
d.text((gx0_ + gw, gy0_ + gh + 6 * s), f'{mx / 1000:.1f} km', font=F(20 * s), fill=(180, 186, 198), anchor='ra')
north_arrow(b, (W - 110 * s, H - 110 * s), heading(eye, tgt), s)
text(b, (W - 190 * s, H - 60 * s), 'ALIGNMENT: LCP-DERIVED · ASSESSED', F(22 * s, 'SemiBold'), fill=(220, 220, 220), anchor='ra', sc=s)
b.convert('RGB').save(f'{SP}/styleframe_3_reveal.png'); print('sf3')
