"""Khabri-1 hill post - TRACK OPTIONS film (no recommendation). 2:00, 3840x2160 native, 30 fps.
usage: xvfb-run -a python3 final.py OUT.mp4 --t0 A --t1 B   |   --stills t1,t2,..
Every figure is read from work/*.json produced by the analysis scripts - nothing typed by hand.
"""
import json, sys, math, argparse, subprocess, time, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy.ndimage import map_coordinates, gaussian_filter1d
from engine import *
from overlay import *

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--t0', type=float, default=0); ap.add_argument('--t1', type=float, default=120)
ap.add_argument('--stills', default=''); args = ap.parse_args()
FPS = 30; W, H = 3840, 2160; s = 2.0
WA = '/root/.claude/uploads/d35c83c0-ed16-5ab8-ac1e-72068dbafa01/cf77cbb6-WhatsApp_Video_2026-11-25_at_10.26.14.mp4'
MT = {t['name']: t for t in json.load(open(f'{R}/work/metrics.json'))['tracks']}; PR = json.load(open(f'{R}/work/profiles.json'))
MC = json.load(open(f'{R}/work/mcda.json')); POL = json.load(open(f'{R}/work/pol.json'))
ORDER = ['T1', 'T2', 'T3', 'T4', 'T5']
DESC = {'T1': 'Direct climb – S spur', 'T2': 'Graded S spur', 'T3': 'W spur / ridge', 'T4': 'E flank', 'T5': 'Rear / N foothill'}
LONG = {'T1': 'Climbs straight up the S spur from the saddle', 'T2': 'Zig-zags up the S spur at a ruling 1:7',
        'T3': 'Leaves the KMZ new tr W, climbs the W spur along the ridge', 'T4': 'Leaves the take-off NE, climbs the E flank, arrives along the crest neck',
        'T5': 'Skirts the mount to the rear, runs N along the foothill, climbs from the N'}

Sc = Scene(W, H)
G = np.load(f'{R}/work/grid.npz'); gx0, gy0, gst = float(G['x0']), float(G['y0']), float(G['st']); LACC = np.log10(np.maximum(G['ACC'], 0.01))
def acc_fn(X, Y):
    fi = (Y - gy0) / gst; fj = (X - gx0) / gst; v = map_coordinates(LACC, [fi, fj], order=1, mode='constant', cval=-2)
    return np.where((fi < 0) | (fj < 0) | (fi > LACC.shape[0] - 1) | (fj > LACC.shape[1] - 1), -2, v)
Sc.set_acc(acc_fn)
pe, pn = [float(v) for v in en(63.43978, 25.42739)]; Sc.focus = (pe, pn); pz = float(Sc.height(np.array([pe]), np.array([pn]))[0])
def track3d(llz, step=2.0, lift=1.2):
    a = np.array(llz); e, n = en(a[:, 0], a[:, 1]); P = np.c_[e, n]
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; t = np.arange(0, d[-1], step)
    e2 = np.interp(t, d, e); n2 = np.interp(t, d, n); return np.c_[e2, n2, Sc.height(e2, n2) + lift], t
TR = {k: track3d(v['ll']) for k, v in PR.items()}
RL_POST = 133                                                    # post RL as given by the user (destination input, not computed)
DSM_BIAS = pz - RL_POST                                          # Cop GLO-30 is a surface model: reading at the post vs the given RL
def _faces():                                                    # mean slope of the S / N faces, 30-250 m from the post (Cop GLO-30, 10 m sampling)
    xs = np.arange(-300, 301, 10.0); X, Y = np.meshgrid(xs, xs); Z = Sc.height(pe + X.ravel(), pn + Y.ravel()).reshape(X.shape)
    gy, gx = np.gradient(Z, 10.0); S_ = np.degrees(np.arctan(np.hypot(gx, gy))); Rr = np.hypot(X, Y); band = (Rr > 30) & (Rr < 250)
    return float(S_[band & (Y < -np.abs(X) * 0.5)].mean()), float(S_[band & (Y > np.abs(X) * 0.5)].mean())
FACE_S, FACE_N = _faces()
TAKEOFF_CH = MT['T4']['junction_ch_km']; TAKEOFF_EN = TR['T4'][0][0, :2]
KMZ3 = [track3d(p['pts'], 4.0)[0] for p in kml() if p['kind'] == 'line']

def sm(x): x = np.clip(x, 0, 1); return x * x * x * (x * (6 * x - 15) + 10)
def seg(t, a, b): return float(sm((t - a) / (b - a)))
def catmull(P, u):
    P = np.asarray(P, float); n = len(P)
    if n == 2: return P[0] + (P[1] - P[0]) * u
    Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]]); f = u * (n - 1); i = min(int(f), n - 2); t = f - i
    p0, p1, p2, p3 = Q[i], Q[i + 1], Q[i + 2], Q[i + 3]
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
def rel(dx, dy, z): return (pe + dx, pn + dy, z)
def heading(eye, tgt): return float(np.degrees(np.arctan2(tgt[0] - eye[0], tgt[1] - eye[1])))
def vis(P): x, y, v = Sc.visible(P); return np.c_[x, y], v
def track_item(k, frac=1.0, w=4.2, glow=0.8, pulse=None, col=None):
    P, _ = TR[k]; n = max(2, int(frac * len(P))); xy, v = vis(P[:n]); return dict(xy=xy, vis=v, col=col or COL[k], w=w, glow=glow, pulse=pulse)
def kmz_items(a=1.0):
    out = []
    for P in KMZ3: xy, v = vis(P); out.append(dict(xy=xy, vis=v, col=tuple(int(c * a) for c in COL['KMZ']), w=2.5, glow=0.3 * a, ghost=False))
    return out
def point_xy(e, n, lift=2.0):
    z = float(Sc.height(np.array([e]), np.array([n]))[0]) + lift; xy, v = vis(np.array([[e, n, z]])); return xy[0], bool(v[0])
def layer_alpha(base, fn, a):
    if a <= 0.003: return
    L = Image.new('RGBA', base.size, (0, 0, 0, 0)); fn(L)
    if a < 1: L.putalpha(L.getchannel('A').point(lambda v: int(v * a)))
    base.alpha_composite(L)
def render3d(eye, tgt, fov, **kw):
    img = Sc.render(eye, tgt, fov=fov, sun_az=115, sun_el=kw.pop('sun_el', 24), **kw).astype(np.float32)
    bl = cv2.GaussianBlur(img, (0, 0), 1.6); img = img + 0.35 * (img - bl)                       # crispening of the 0.6 m imagery
    bl2 = cv2.resize(cv2.GaussianBlur(cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3), (W, H)); img = np.clip(img + 0.22 * (img - bl2), 0, 1)   # clarity (local contrast)
    return grade(img)
def glow(img, items): return glow_tracks(img, items, s)
def chip(base, xy, txt, sub=None, col=GOLD):
    d = ImageDraw.Draw(base); f = F(30 * s, 'Bold'); f2 = F(22 * s, 'Medium'); w = max(d.textlength(txt, font=f), d.textlength(sub, font=f2) if sub else 0) + 40 * s
    x, y = xy; h = (56 if not sub else 92) * s
    d.rounded_rectangle((x, y, x + w, y + h), radius=int(10 * s), fill=PANEL + (225,), outline=col + (255,), width=int(2 * s))
    d.text((x + 20 * s, y + 12 * s), txt, font=f, fill=(255, 255, 255))
    if sub: d.text((x + 20 * s, y + 54 * s), sub, font=f2, fill=col)
def compass(b, eye, tgt): north_arrow(b, (W - 110 * s, H - 110 * s), heading(eye, tgt), s)

cap = cv2.VideoCapture(WA)
def drone(tsrc, full=True):
    cap.set(cv2.CAP_PROP_POS_MSEC, tsrc * 1000); ok, fr = cap.read()
    fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)[20:375]
    up = cv2.resize(fr, (W, int(W / 848 * 355)), interpolation=cv2.INTER_LANCZOS4).astype(np.float32) / 255
    bl = cv2.GaussianBlur(up, (0, 0), 3); up = np.clip(up + 0.6 * (up - bl), 0, 1)
    rng = np.random.default_rng(int(tsrc * 30)); up = np.clip(up + rng.normal(0, 0.012, up.shape[:2]).astype(np.float32)[..., None], 0, 1)
    up = grade(up, 0.7)
    if not full: return up
    out = np.zeros((H, W, 3), np.float32); y0 = (H - up.shape[0]) // 2; out[y0:y0 + up.shape[0]] = up; return out

# ---------------------------------------------------------------- 0-8 cold open (drone)
def shot1(t):
    img = drone(37 + t); z = 1 + 0.07 * sm(t / 8); M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
    img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR) * seg(t, 0, 1.2); b = to_pil(img)
    def ttl(L):
        d = ImageDraw.Draw(L); d.text((W / 2, H / 2 - 74 * s), 'TRACK RECCE  ·  OPTIONS', font=F(30 * s, 'SemiBold'), fill=GOLD, anchor='mm')
        d.text((W / 2, H / 2), 'KHABRI-1 HILL POST', font=F(84 * s, 'Bold', True), fill=(255, 255, 255), anchor='mm')
        d.text((W / 2, H / 2 + 76 * s), 'Five alignments to the post · desk study for decision', font=F(30 * s, 'Medium'), fill=(225, 228, 235), anchor='mm')
    layer_alpha(b, ttl, seg(t, 2.5, 3.8) * (1 - seg(t, 6.8, 7.8)))
    layer_alpha(b, lambda L: chip(L, (70 * s, H - 300 * s), f'DRONE 00:{37 + int(t):02d}', 'Taloband Rg S face · looking N · ASSESSED'), seg(t, 0.8, 1.6))
    return b

# ---------------------------------------------------------------- 8-20 establishing orbit
K2 = [rel(200, -2050, 330), rel(-600, -2100, 600), rel(-1150, -1900, 780), rel(-1450, -1350, 760)]
T2_ = [rel(0, 400, 130), rel(60, 280, pz - 30), rel(130, 230, pz - 50), rel(140, 200, pz - 55)]
def shot2(t):
    u = seg(t, 0, 12); eye, tgt = catmull(K2, u), catmull(T2_, u); img = render3d(eye, tgt, 38)
    items = []
    if t > 6.5:
        for P in KMZ3:
            fr = seg(t, 6.5, 10.5); n = max(2, int(len(P) * fr)); xy, v = vis(P[:n]); items.append(dict(xy=xy, vis=v, col=COL['KMZ'], w=2.8, glow=0.4, ghost=False, pulse=fr if fr < 1 else None))
    img = glow(img, items) if items else img; b = to_pil(img)
    if t > 4:
        a = seg(t, 4, 6.5); box = [(-1300, -1000), (1100, -1000), (1100, 900), (-1300, 900), (-1300, -1000)]; pts = []
        for (x0, y0), (x1, y1) in zip(box[:-1], box[1:]):
            for q in np.linspace(0, 1, 80): pts.append((pe + x0 + (x1 - x0) * q, pn + y0 + (y1 - y0) * q))
        pts = np.array(pts[:max(2, int(len(pts) * a))]); z = Sc.height(pts[:, 0], pts[:, 1]) + 3; xy, v = vis(np.c_[pts, z]); d = ImageDraw.Draw(b)
        for i in range(len(xy) - 1):
            if v[i] and v[i + 1]: d.line((*xy[i], *xy[i + 1]), fill=(255, 255, 255, 170), width=int(2 * s))
    xy, ok = point_xy(pe, pn)
    layer_alpha(b, lambda L: pin(L, xy, 'KHABRI-1 HILL POST', f'RL {RL_POST} m  ·  25°25\'38.6"N 63°26\'23.2"E', s=s, up=150 * seg(t, 2.5, 3.6) + 1), seg(t, 2.5, 3.2))
    xy2, ok2 = point_xy(*TAKEOFF_EN)
    if ok2: layer_alpha(b, lambda L: tag(L, xy2, f'T4 take-off CH {TAKEOFF_CH:.2f}', COL['KMZ'], s, 170, 50), seg(t, 9.5, 10.3))
    title_bar(b, 'KHABRI-1 HILL POST', 'Taloband Rg · above the Shadi Kaur · Cop GLO-30 terrain (VE 1.0) · Esri 0.6 m imagery', s)
    compass(b, eye, tgt); return b

# ---------------------------------------------------------------- 20-30 slope + drainage
K3 = [rel(800, -1300, 470), rel(350, -1450, 440), rel(-150, -1400, 430)]; T3_ = [rel(-150, 200, pz - 50), rel(-50, 230, pz - 50), rel(0, 250, pz - 50)]
def cam3(t): u = seg(t, 0, 10); return catmull(K3, u), catmull(T3_, u)
def shot3(t):
    eye, tgt = cam3(t); img = render3d(eye, tgt, 40, slope_mix=seg(t, 0.5, 2.5), drain_mix=seg(t, 3, 5))
    b = to_pil(glow(img, kmz_items(0.6))); xy, ok = point_xy(pe, pn); pin(b, xy, 'HILL POST', f'RL {RL_POST}', s=s, up=110)
    title_bar(b, 'TERRAIN · SLOPE & DRAINAGE', 'Slope from Cop GLO-30 · D8 flow lines > 2 ha', s)
    def legend(L):
        panel(L, (60 * s, H - 330 * s, 620 * s, H - 60 * s), 'SLOPE (deg)', s=s, blur=False)
        ramp = np.array([[26, 153, 77], [253, 224, 102], [245, 110, 66], [166, 0, 38]], float); bar = np.zeros((int(28 * s), int(480 * s), 4), np.uint8); bar[..., 3] = 255
        for i in range(bar.shape[1]):
            q = i / bar.shape[1] * 3; k = min(int(q), 2); bar[:, i, :3] = ramp[k] + (ramp[k + 1] - ramp[k]) * (q - k)
        L.alpha_composite(Image.fromarray(bar, 'RGBA'), (int(90 * s), int(H - 245 * s)))
        for i, lab in enumerate(['0', '10', '20', '30', '40+']): text(L, (90 * s + i * 120 * s, H - 205 * s), lab, F(22 * s, 'Medium'), anchor='ma', sc=s)
        d = ImageDraw.Draw(L); d.line((90 * s, H - 135 * s, 150 * s, H - 135 * s), fill=(64, 191, 255), width=int(6 * s)); text(L, (165 * s, H - 150 * s), 'Drainage line / nala', F(24 * s, 'Medium'), sc=s)
    layer_alpha(b, legend, seg(t, 0.8, 1.6))
    xs, _ = point_xy(pe - 60, pn - 260); xn, _ = point_xy(pe + 40, pn + 230)
    layer_alpha(b, lambda L: tag(L, xs, f'S FACE ≈ {FACE_S:.0f}° (mean, 250 m)', (255, 130, 90), s, 380, -40), seg(t, 5.5, 6.2))
    layer_alpha(b, lambda L: tag(L, xn, f'N FACE ≈ {FACE_N:.0f}° (mean, 250 m)', (120, 220, 255), s, 260, -120), seg(t, 6.3, 7))
    compass(b, eye, tgt); return b

# ---------------------------------------------------------------- 30-40 strata
SECT = {}
def shot4(t):
    if not SECT:
        eye, tgt = cam3(10); SECT['bg'] = cv2.GaussianBlur(render3d(eye, tgt, 40), (0, 0), 25) * 0.45
        d_ = np.arange(-450, 451, 5); SECT['d'] = d_; SECT['z'] = dem(*ll(pe + 0 * d_, pn + d_))
    img = SECT['bg'].copy()
    dr = drone(58 + t, full=False); dr = cv2.resize(dr, (int(dr.shape[1] * 0.46), int(dr.shape[0] * 0.46)), interpolation=cv2.INTER_AREA)
    x0, y0 = W - dr.shape[1] - 120, 330; a = seg(t, 0.3, 1.2); img[y0:y0 + dr.shape[0], x0:x0 + dr.shape[1]] = img[y0:y0 + dr.shape[0], x0:x0 + dr.shape[1]] * (1 - a) + dr * a
    b = to_pil(img); title_bar(b, 'STRATA · ASSESSED', 'DEM cross-section through the post  ·  drone footage of the same ridge', s)
    d_, z_ = SECT['d'], SECT['z']; gx, gy, gw, gh = 260, 560, 1480, 1260
    panel(b, (gx - 160, gy - 260, gx + gw + 80, gy + gh + 170), 'N–S SECTION THROUGH THE POST', s=s, blur=False)
    dd = ImageDraw.Draw(b); n = max(2, int(len(d_) * seg(t, 0.4, 3.5)))
    X = gx + (d_ + 450) / 900 * gw; Y = gy + gh - (z_ - 20) / 150 * gh
    dd.polygon([(X[0], gy + gh)] + list(zip(X[:n], Y[:n])) + [(X[n - 1], gy + gh)], fill=(150, 125, 95, 255))
    dd.line(list(zip(X[:n], Y[:n])), fill=GOLD, width=8)
    for zl in (40, 80, 120, 160): yl = gy + gh - (zl - 20) / 150 * gh; dd.line((gx, yl, gx + gw, yl), fill=(255, 255, 255, 50), width=2); dd.text((gx - 14, yl), f'{zl} m', font=F(22 * s), fill=(180, 186, 198), anchor='rm')
    text(b, (gx, gy + gh + 20), 'S', F(34 * s, 'Bold'), sc=s); text(b, (gx + gw, gy + gh + 20), 'N', F(34 * s, 'Bold'), anchor='ra', sc=s)
    xp = gx + gw / 2; dd.line((xp, gy, xp, gy + gh), fill=(255, 255, 255, 140), width=3); text(b, (xp + 16, gy + 10), 'POST', F(26 * s, 'Bold'), sc=s)
    iS = int(np.argmin(np.abs(d_ + 120))); iN = int(np.argmin(np.abs(d_ - 120)))
    layer_alpha(b, lambda L: tag(L, (X[iS], Y[iS]), f'S face ≈ {FACE_S:.0f}°', (255, 130, 90), s, -60, -160), seg(t, 3.5, 4.2))
    layer_alpha(b, lambda L: tag(L, (X[iN], Y[iN]), f'N face ≈ {FACE_N:.0f}°', (120, 220, 255), s, 60, -170), seg(t, 4.3, 5))
    text(b, (x0, y0 + dr.shape[0] + 20), 'DRONE 00:58–01:08 · post ridge, S face · ASSESSED', F(24 * s, 'Bold'), fill=GOLD, sc=s)
    def notes(L):
        panel(L, (x0 - 20, y0 + dr.shape[0] + 110, W - 100, y0 + dr.shape[0] + 680), 'READING THE STRATA', s=s, blur=False)
        for i, ln in enumerate(['Bedding strikes ENE–WSW along the ridge', 'Bedding crops out on BOTH faces:', '   S face – drone 01:03  ·  N side – recce oblique',
                                '→ beds gently dipping / near-horizontal', 'No dip-slope (planar slide) face identified', 'ASSESSED – confirm dip on the ground']):
            text(L, (x0 + 30, y0 + dr.shape[0] + 230 + i * 66), ln, F(25 * s, 'Medium' if i != 5 else 'Bold'), fill=(255, 170, 120) if i == 5 else (235, 238, 245), sc=s)
    layer_alpha(b, notes, seg(t, 5, 6)); return b

# ---------------------------------------------------------------- 40-55 five alignments draw on
DRAW = {k: (0.3 + 2.6 * i, 2.6 + 2.6 * i) for i, k in enumerate(ORDER)}
def cam5(t):
    u = seg(t, 0, 15); az = math.radians(212 + 38 * u); r = 2150 - 350 * u
    return (pe + r * math.sin(az), pn + r * math.cos(az), 900 - 150 * u), (pe + 120, pn + 220, pz - 60)
def legend5(L, upto):
    panel(L, (60 * s, H - 400 * s, 600 * s, H - 60 * s), 'ALIGNMENTS', s=s, blur=False); d = ImageDraw.Draw(L)
    for i, k in enumerate(ORDER + ['KMZ']):
        if k != 'KMZ' and ORDER.index(k) > upto: continue
        yy = H - 330 * s + i * 42 * s; d.line((90 * s, yy + 12 * s, 140 * s, yy + 12 * s), fill=COL[k], width=int(6 * s))
        d.text((160 * s, yy), (f'{k}  {DESC[k]}' if k != 'KMZ' else 'KMZ tr (existing / planned)'), font=F(24 * s, 'Medium'), fill=(235, 238, 245))
TAGOFF = {'T1': (-60, 40), 'T2': (-130, 0), 'T3': (-60, -60), 'T4': (120, 30), 'T5': (-60, -60)}
def shot5(t):
    eye, tgt = cam5(t); img = render3d(eye, tgt, 36); items = kmz_items(0.7)
    for k in ORDER:
        a, b_ = DRAW[k]
        if t >= a: fr = seg(t, a, b_); items.append(track_item(k, max(fr, 0.01), w=4.6, glow=1.0 if t < b_ + 0.5 else 0.8, pulse=fr if fr < 1 else ((t - b_) * 0.25) % 1))
    b = to_pil(glow(img, items)); xy, ok = point_xy(pe, pn); pin(b, xy, 'HILL POST', f'RL {RL_POST}', s=s, up=120)
    for k in ORDER:
        if t >= DRAW[k][1]:
            P, _ = TR[k]; i = int(0.35 * len(P)); xy2, v2 = vis(P[i:i + 1])
            if v2[0]: layer_alpha(b, lambda L, k=k, xy2=xy2: tag(L, xy2[0], k, COL[k], s, *TAGOFF[k]), seg(t, DRAW[k][1], DRAW[k][1] + 0.5))
    upto = max([ORDER.index(k) for k in ORDER if t >= DRAW[k][0]] + [-1]); layer_alpha(b, lambda L: legend5(L, upto), seg(t, 0.2, 1))
    title_bar(b, 'FIVE ALIGNMENTS', 'Least-cost corridors on the terrain model · five distinct approaches to the post', s)
    compass(b, eye, tgt); return b

# ---------------------------------------------------------------- 55-105 one fly-through per option (10 s each)
SMP = {}
for k in ORDER:
    P, _ = TR[k]; Q = P.copy(); sg = max(8, min(30, len(P) // 12))
    Q[:, 0] = gaussian_filter1d(P[:, 0], sg, mode='nearest'); Q[:, 1] = gaussian_filter1d(P[:, 1], sg, mode='nearest'); Q[:, 2] = gaussian_filter1d(P[:, 2], sg, mode='nearest'); SMP[k] = Q
def cam_fly(k, t):
    Q = SMP[k]; n = len(Q); L_ = n * 2.0
    u = 0.04 + 0.86 * seg(t, 0, 9.2); i = int(u * (n - 1)); c = Q[i]; lk = max(10, int(120 / 2))
    a = Q[max(0, i - lk)]; bq = Q[min(n - 1, i + lk)]; fwd = bq[:2] - a[:2]; fwd /= (np.linalg.norm(fwd) + 1e-9)
    back = 520; up = 430
    eye = np.array([c[0] - fwd[0] * back - fwd[1] * 50, c[1] - fwd[1] * back + fwd[0] * 50, max(c[2] + up, Sc.height(np.array([c[0] - fwd[0] * back]), np.array([c[1] - fwd[1] * back]))[0] + 90)])
    ahead = Q[min(n - 1, i + int(160 / 2))]; w_ = seg(t, 4.5, 9.5); tgt = ahead * (1 - w_) + np.array([pe, pn, pz]) * w_; tgt = tgt - np.array([0, 0, 15])
    return tuple(eye), tuple(tgt), u
def card(L, k):
    m = MT[k]; p = POL[k]; x0, y0 = W - 760 * s, 170 * s
    panel(L, (x0, y0, W - 70 * s, y0 + 690 * s), f'{k}  ·  {DESC[k].upper()}', accent=COL[k], s=s, blur=False)
    rows = [('New const', f"{m['new_const_m'] / 1000:.2f} km"), ('Max / mean grade', f"{m['max_grade_pct']:.1f} / {m['mean_grade_pct']:.1f} %"),
            ('Length > 1:10 / > 1:5', f"{m['pct_gt_1in10']:.0f} / {m['pct_gt_1in5']:.0f} %"), ('Hairpins · nala xings', f"{m['hairpins']} · {m['nala_xings']}"),
            ('Cut (assessed)', f"{p['cut_total']:,.0f} m³"), ('Exposure crest / low gnd', f"{m['expo_dominating_pct']:.0f} / {m['expo_plain_road_pct']:.0f} %"),
            ('POL · work days', f"{p['total']:,} lit · {p['dur']}")]
    for i, (a, v) in enumerate(rows):
        yy = y0 + 90 * s + i * 50 * s; text(L, (x0 + 30 * s, yy), a, F(22 * s, 'Medium'), fill=(170, 178, 192), sc=s); text(L, (W - 100 * s, yy - 4 * s), v, MONO(27 * s), anchor='ra', sc=s)
    text(L, (x0 + 30 * s, y0 + 455 * s), LONG[k], F(19 * s, 'Medium'), fill=COL[k], sc=s)
    gx_, gy_, gw, gh = x0 + 70 * s, y0 + 510 * s, 760 * s - 200 * s, 150 * s; d = ImageDraw.Draw(L); pr = PR[k]
    q = [(gx_ + si / 2500 * gw, gy_ + gh - (zi - 20) / 140 * gh) for si, zi in zip(pr['s'][::3], pr['z'][::3])]; d.line(q, fill=COL[k] + (255,), width=int(4 * s))
    for zl in (40, 80, 120): yl = gy_ + gh - (zl - 20) / 140 * gh; d.line((gx_, yl, gx_ + gw, yl), fill=(255, 255, 255, 40), width=1); d.text((gx_ - 6 * s, yl), str(zl), font=F(16 * s), fill=(170, 178, 192), anchor='rm')
    d.text((gx_ + gw, gy_ + gh + 8 * s), '2.5 km', font=F(16 * s), fill=(170, 178, 192), anchor='ra')
    text(L, (x0 + 30 * s, y0 + 492 * s), f'Elev: Cop GLO-30 surface model, reads {pz:.0f} m at the post vs RL {RL_POST} (≈ +{DSM_BIAS:.0f} m)', F(17 * s, 'Medium'), fill=(200, 205, 215), sc=s)
def fly(k):
    def f(t):
        eye, tgt, u = cam_fly(k, t); img = render3d(eye, tgt, 40, sun_el=26)
        items = kmz_items(0.45) + [track_item(j, w=2.2, glow=0.2, col=tuple(int(c * 0.5) for c in COL[j])) for j in ORDER if j != k] + [track_item(k, w=6, glow=1.4, pulse=u)]
        b = to_pil(glow(img, items))
        xy, ok = point_xy(pe, pn)
        if ok and xy[1] > 420 and 300 < xy[0] < W - 1700: pin(b, xy, 'KHABRI-1 HILL POST', f'RL {RL_POST}', s=s, up=170)
        pr = PR[k]; ss_ = np.array(pr['s']); zz = np.array(pr['z']); gg = np.abs(np.array(pr['g'])) * 100; j = int(u * (len(ss_) - 1)); jch = MT[k]['junction_ch_km']
        def hud(L):
            panel(L, (60 * s, H - 330 * s, 760 * s, H - 60 * s), f'{k}  ·  LIVE', accent=COL[k], s=s, blur=False)
            for r, (lab, val) in enumerate([('CH', f'{jch + ss_[j] / 1000:.2f} km'), ('ELEV (DSM)', f'{zz[j]:.0f} m'), ('GRADE', (f'1:{100 / gg[j]:.0f}  ({gg[j]:.1f}%)' if gg[j] >= 1 else 'Level (<1 %)'))]):
                yy = H - 250 * s + r * 62 * s; text(L, (90 * s, yy), lab, F(24 * s, 'SemiBold'), fill=(170, 178, 192), sc=s); text(L, (730 * s, yy - 6 * s), val, MONO(38 * s), anchor='ra', sc=s)
        layer_alpha(b, hud, seg(t, 0.3, 1.0)); layer_alpha(b, lambda L: card(L, k), seg(t, 0.6, 1.4))
        title_bar(b, f'OPTION {k[1]}  ·  {DESC[k].upper()}', LONG[k], s); compass(b, eye, tgt); return b
    return f

# ---------------------------------------------------------------- 105-114 factual comparison (no scores)
PLAN = {}
def plan_base():
    if PLAN: return PLAN['b'], PLAN['mpp']
    ce, cn = pe + 250, pn - 350; eye = (ce, cn - 30, 4200); tgt = (ce, cn, 0)
    img = Sc.render(eye, tgt, fov=34, sun_az=115, sun_el=35, haze=0.2).astype(np.float32); img = grade(img) * 0.85
    items = [dict(xy=vis(P)[0], vis=np.ones(len(P), bool), col=COL['KMZ'], w=2, glow=0.3, ghost=False) for P in KMZ3]
    items += [dict(xy=vis(TR[k][0])[0], vis=np.ones(len(TR[k][0]), bool), col=COL[k], w=4.5, glow=0.7) for k in ORDER]
    b = to_pil(glow(img, items))
    PLANOFF = {'T1': (90, -40), 'T2': (-120, 40), 'T3': (-110, -50), 'T4': (-30, 110), 'T5': (110, 40)}
    for k in ORDER:
        P = TR[k][0]; xy = vis(P[int(0.55 * len(P)):int(0.55 * len(P)) + 1])[0][0]; tag(b, xy, k, COL[k], s, *PLANOFF[k])
    xy0, _ = vis(np.array([[pe, pn, pz]])); xy1, _ = vis(np.array([[pe + 500, pn, pz]])); PLAN['b'] = b; PLAN['mpp'] = 500 / abs(xy1[0, 0] - xy0[0, 0])
    return PLAN['b'], PLAN['mpp']
def shot7(t):
    base, mpp = plan_base(); z = 1 + 0.04 * sm(t / 9)
    arr = np.asarray(base.convert('RGB')).astype(np.float32) / 255; M = cv2.getRotationMatrix2D((W * 0.33, H * 0.5), 0, z); arr = cv2.warpAffine(arr, M, (W, H))
    grad = np.clip((np.arange(W) - W * 0.50) / (W * 0.12), 0, 1)[None, :, None] * 0.75; b = to_pil(arr * (1 - grad))
    title_bar(b, 'COMPARISON OF OPTIONS', 'Plan view, N up · factual figures only · no weighting, no ranking', s)
    legend5(b, 4); d = ImageDraw.Draw(b)
    north_arrow(b, (W * 0.47, 250 * s), 0, s)
    L_ = 500 / (mpp / z); x, y = 140, H - 400 * s; d.rectangle((x, y, x + L_, y + 10 * s), fill=(255, 255, 255)); d.rectangle((x + L_ / 2, y, x + L_, y + 10 * s), fill=(20, 20, 20), outline=(255, 255, 255))
    text(b, (x, y - 40 * s), '0', F(22 * s, 'SemiBold'), sc=s); text(b, (x + L_, y - 40 * s), '500 m', F(22 * s, 'SemiBold'), anchor='ra', sc=s)
    tx, ty = W * 0.535, 200 * s; cols = [('', 80), ('New km', 165), ('Max %', 140), ('>1:10', 140), ('>1:5', 125), ('Nala', 115), ('Cut m³', 215), ('Crest', 155), ('Low gnd', 195), ('POL lit', 205), ('Days', 120)]
    CW = 1 / s; xx = [tx]; [xx.append(xx[-1] + c[1] * s * CW) for c in cols]
    for i, (c, w_) in enumerate(cols): text(b, (xx[i] + (0 if i == 0 else w_ * s * CW - 10), ty), c, F(20 * s, 'SemiBold'), fill=(170, 178, 192), anchor='la' if i == 0 else 'ra', sc=s)
    for r, k in enumerate(ORDER):
        a = seg(t, 0.8 + r * 0.6, 1.3 + r * 0.6)
        m = MT[k]; vals = [k, f"{m['new_const_m'] / 1000:.2f}", f"{m['max_grade_pct']:.1f}", f"{m['pct_gt_1in10']:.0f}%", f"{m['pct_gt_1in5']:.0f}%", f"{m['nala_xings']}",
                           f"{POL[k]['cut_total']:,.0f}", f"{m['expo_dominating_pct']:.0f}%", f"{m['expo_plain_road_pct']:.0f}%", f"{POL[k]['total']:,}", f"{POL[k]['dur']}"]
        yy = ty + (75 + r * 72) * s
        def row(L, vals=vals, yy=yy, k=k):
            for i, v in enumerate(vals):
                text(L, (xx[i] + (0 if i == 0 else cols[i][1] * s * CW - 10), yy), v, F(26 * s, 'Bold') if i == 0 else MONO(21 * s), fill=COL[k] if i == 0 else (240, 242, 246), anchor='la' if i == 0 else 'ra', sc=s)
        layer_alpha(b, row, a)
    def key(L):
        for i, ln in enumerate(['New km: new construction incl KMZ new tr portion  ·  Max %: steepest 50 m window', '>1:10, >1:5: share of length steeper than that grade',
                                'Crest / Low gnd: share of length seen from assumed OPs (Taloband crests / W–NW plain)',
                                'Cut: assessed from 30 m DEM, 14 ft formation  ·  POL and days: engr plt stds + 10 % margin']):
            text(L, (W * 0.535, ty + 470 * s + i * 44 * s), ln, F(19 * s, 'Medium'), fill=(190, 196, 208), sc=s)
    layer_alpha(b, key, seg(t, 3.8, 4.6))
    def foot(L):
        panel(L, (W * 0.53 - 16 * s, H - 170 * s, W - 70 * s, H - 50 * s), None, s=s, blur=False)
        text(L, (W * 0.53, H - 150 * s), 'Cut, POL and work days: 30 m DEM, ±50 % (assessed) · Days: 1 Dozer + 1 Excavator', F(18 * s, 'Medium'), fill=(230, 233, 240), sc=s)
        text(L, (W * 0.53, H - 112 * s), 'Confirm all alignments by gr recce before pegging', F(18 * s, 'Medium'), fill=GOLD, sc=s)
    layer_alpha(b, foot, seg(t, 5, 5.8)); return b

# ---------------------------------------------------------------- 114-120 options summary (no recommendation)
def shot8(t):
    base, _ = plan_base(); arr = cv2.GaussianBlur(np.asarray(base.convert('RGB')).astype(np.float32) / 255, (0, 0), 30) * 0.35
    fade = 1 - seg(t, 4.6, 6); b = to_pil(arr * fade)
    def crd(L):
        d = ImageDraw.Draw(L); d.text((W / 2, 150 * s), 'OPTIONS FOR DECISION', font=F(54 * s, 'Bold', True), fill=(255, 255, 255), anchor='ma')
        d.text((W / 2, 225 * s), f'Khabri-1 hill post (RL {RL_POST}) · five alignments · desk study on Cop GLO-30 and 0.6 m imagery', font=F(24 * s, 'Medium'), fill=(200, 205, 215), anchor='ma')
        cw = (W - 300 * s) / 5
        for i, k in enumerate(ORDER):
            x0 = 150 * s + i * cw; m = MT[k]; p = POL[k]
            panel(L, (x0 + 10 * s, 300 * s, x0 + cw - 10 * s, H - 200 * s), None, accent=COL[k], s=s, blur=False)
            d.text((x0 + cw / 2, 330 * s), k, font=F(48 * s, 'Bold', True), fill=COL[k], anchor='ma'); d.text((x0 + cw / 2, 395 * s), DESC[k], font=F(22 * s, 'SemiBold'), fill=(235, 238, 245), anchor='ma')
            rows = [('New const', f"{m['new_const_m'] / 1000:.2f} km"), ('Max grade', f"{m['max_grade_pct']:.1f} %"), ('> 1:10', f"{m['pct_gt_1in10']:.0f} %"), ('> 1:5', f"{m['pct_gt_1in5']:.0f} %"),
                    ('Hairpins', f"{m['hairpins']}"), ('Nala xings', f"{m['nala_xings']}"), ('Cut', f"{p['cut_total']:,.0f} m³"), ('Exposure crest', f"{m['expo_dominating_pct']:.0f} %"),
                    ('Exposure low gnd', f"{m['expo_plain_road_pct']:.0f} %"), ('POL', f"{p['total']:,} lit"), ('Work days', f"{p['dur']}")]
            for r, (a, v) in enumerate(rows):
                yy = 450 * s + r * 38 * s; d.text((x0 + 30 * s, yy), a, font=F(19 * s, 'Medium'), fill=(170, 178, 192)); d.text((x0 + cw - 30 * s, yy - 2 * s), v, font=MONO(22 * s), fill=(255, 255, 255), anchor='ra')
        d.text((W / 2, H - 150 * s), 'All alignments are least-cost corridors on a 30 m DEM · figures assessed · confirm by gr recce before pegging', font=F(23 * s, 'SemiBold'), fill=GOLD, anchor='ma')
    layer_alpha(b, crd, seg(t, 0.2, 1.0) * fade); return b

SHOTS = [(0, 8, shot1), (8, 20, shot2), (20, 30, shot3), (30, 40, shot4), (40, 55, shot5)] + [(55 + 10 * i, 65 + 10 * i, fly(k)) for i, k in enumerate(ORDER)] + [(105, 114, shot7), (114, 120, shot8)]
XF = 0.5
def frame(T):
    for i, (a, b_, fn) in enumerate(SHOTS):
        if a <= T < b_:
            im = fn(T - a)
            if i > 0 and T - a < XF:
                pa, pb, pf = SHOTS[i - 1]; prev = pf(T - pa); return Image.blend(prev.convert('RGB'), im.convert('RGB'), float(sm((T - a) / XF)))
            return im.convert('RGB')
    return Image.new('RGB', (W, H))

if args.stills:
    for T in [float(x) for x in args.stills.split(',')]:
        t_ = time.time(); frame(T).resize((1920, 1080), Image.LANCZOS).save(f'{args.out}_{T:06.2f}.jpg', quality=90); print('still', T, round(time.time() - t_, 1), 's', flush=True)
    sys.exit()
f0, f1 = int(round(args.t0 * FPS)), int(round(args.t1 * FPS))
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '12',
                        '-pix_fmt', 'yuv420p', args.out], stdin=subprocess.PIPE)
t_ = time.time()
for f in range(f0, f1):
    enc.stdin.write(np.asarray(frame(f / FPS)).tobytes())
    if f % 30 == 0: print(f'frame {f} {time.time() - t_:.0f}s', flush=True)
enc.stdin.close(); enc.wait(); print('done', args.out, flush=True)
