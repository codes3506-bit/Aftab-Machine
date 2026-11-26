"""Khabri-1 hill post - TRACK OPTIONS film v4: voice-over-timed, AI-upscaled drone, ground climb + crest + 40' x 40' post pad section.
Sharp Esri Wayback (15 Aug 2024) imagery, VE 1.5, B3 panels / fonts / HUD, drone used at five points,
gr recce photos shown at a stop on every option. No recommendation, no ranking.
usage: xvfb-run -a python3 final2.py OUT.mp4 --t0 A --t1 B   |   --stills t1,t2,..
Every figure is read from work/*.json or computed from the DEM here - nothing typed by hand except the post RL / grid (user input).
"""
import json, sys, math, argparse, subprocess, time, glob, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy.ndimage import map_coordinates, gaussian_filter1d
from engine import *
from overlay import glow_tracks, to_pil, grade, COL
import b3ui as U
from b3ui import q, F, put, panel_img, table_panel, text_panel, photo_panel, label, GOLD, WHITE, GREY, NAVY, NAVY2, RED, YEL, BLUE, AMBER

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--t0', type=float, default=0); ap.add_argument('--t1', type=float, default=1e9)
ap.add_argument('--stills', default=''); ap.add_argument('--timeline', action='store_true'); args = ap.parse_args()
FPS = 30; W, H = 2560, 1440; U.init(W, H); s = W / 1920
WA = '/root/.claude/uploads/d35c83c0-ed16-5ab8-ac1e-72068dbafa01/cf77cbb6-WhatsApp_Video_2026-11-25_at_10.26.14.mp4'
PH = '/tmp/claude-0/-home-user-Aftab-Machine/d35c83c0-ed16-5ab8-ac1e-72068dbafa01/images'
MT = {t['name']: t for t in json.load(open(f'{R}/work/metrics.json'))['tracks']}; PR = json.load(open(f'{R}/work/profiles.json')); POL = json.load(open(f'{R}/work/pol.json')); PAD = json.load(open(f'{R}/work/pad.json'))
VO = json.load(open(f'{R}/work/vo/vo.json')); VOD = {k: v[1] for k, v in VO.items()}
ORDER = ['T1', 'T2', 'T3', 'T4', 'T5']
DESC = {'T1': 'Direct climb – S spur', 'T2': 'Graded S spur', 'T3': 'W spur / ridge', 'T4': 'E flank', 'T5': 'Rear / N foothill'}
LONG = {'T1': 'Climbs straight up the S spur from the saddle', 'T2': 'Zig-zags up the S spur at a ruling 1:7',
        'T3': 'Leaves the KMZ new tr W, climbs the W spur along the ridge', 'T4': 'Leaves the take-off NE, climbs the E flank, arrives along the crest neck',
        'T5': 'Skirts the mount to the rear, runs N along the foothill, climbs from the N'}
TITLE = 'TRACK RECCE - KHABRI-1 HILL POST - OPTIONS'
FOOT = 'Imagery © Esri, Maxar (World Imagery Wayback, 15 Aug 2024)  ·  Terrain: Copernicus GLO-30 DEM  ·  Vertical exaggeration ×1.5  ·  Alignments: least-cost study – confirm by gr recce'
RL_POST = 133; GRID = '25°25\'38.6"N  63°26\'23.2"E'                                   # user input

Sc = Scene(W, H)
G = np.load(f'{R}/work/grid.npz'); gx0, gy0, gst = float(G['x0']), float(G['y0']), float(G['st']); LACC = np.log10(np.maximum(G['ACC'], 0.01))
def acc_fn(X, Y):
    fi = (Y - gy0) / gst; fj = (X - gx0) / gst; v = map_coordinates(LACC, [fi, fj], order=1, mode='constant', cval=-2)
    return np.where((fi < 0) | (fj < 0) | (fi > LACC.shape[0] - 1) | (fj > LACC.shape[1] - 1), -2, v)
Sc.set_acc(acc_fn)
pe, pn = [float(v) for v in en(63.43978, 25.42739)]; Sc.focus = (pe, pn)
pz = float(Sc.height(np.array([pe]), np.array([pn]))[0])              # scene height (x VE)
pz_m = float(Sc.height_m(np.array([pe]), np.array([pn]))[0])          # DEM metres
DSM_BIAS = pz_m - RL_POST
def track3d(llz, step=2.0, lift=1.8):
    a = np.array(llz); e, n = en(a[:, 0], a[:, 1]); P = np.c_[e, n]
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; t = np.arange(0, d[-1], step)
    e2 = np.interp(t, d, e); n2 = np.interp(t, d, n); return np.c_[e2, n2, Sc.height(e2, n2) + lift], t
TR = {k: track3d(v['ll']) for k, v in PR.items()}
def _faces():
    xs = np.arange(-300, 301, 10.0); X, Y = np.meshgrid(xs, xs); Z = dem(*ll(pe + X, pn + Y))          # bicubic Cop GLO-30, not the render mesh
    gy, gx = np.gradient(Z, 10.0); S_ = np.degrees(np.arctan(np.hypot(gx, gy))); Rr = np.hypot(X, Y); band = (Rr > 30) & (Rr < 250)
    return float(S_[band & (Y < -np.abs(X) * 0.5)].mean()), float(S_[band & (Y > np.abs(X) * 0.5)].mean())
FACE_S, FACE_N = _faces()
TAKEOFF_CH = MT['T4']['junction_ch_km']; TAKEOFF_EN = TR['T4'][0][0, :2]
KMZL = [p for p in kml() if p['kind'] == 'line']; KMZ3 = [track3d(p['pts'], 4.0)[0] for p in KMZL]
KMZ_KM = sum(float(np.sum(np.hypot(*np.diff(np.c_[en(np.array(p['pts'])[:, 0], np.array(p['pts'])[:, 1])], axis=0).T))) for p in KMZL) / 1000

def sm(x): x = np.clip(x, 0, 1); return x * x * x * (x * (6 * x - 15) + 10)
def seg(t, a, b): return float(sm((t - a) / (b - a)))
def win(t, a, b, fi=0.6, fo=0.6): return seg(t, a, a + fi) * (1 - seg(t, b - fo, b))
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
def kmz_items(a=1.0, w=2.6):
    return [dict(xy=vis(P)[0], vis=vis(P)[1], col=tuple(int(c * a) for c in COL['KMZ']), w=w, glow=0.3 * a, ghost=False) for P in KMZ3]
def point_xy(e, n, lift=2.0):
    z = float(Sc.height(np.array([e]), np.array([n]))[0]) + lift; xy, v = vis(np.array([[e, n, z]])); return xy[0], bool(v[0])
def render3d(eye, tgt, fov, **kw):
    img = Sc.render(eye, tgt, fov=fov, sun_az=135, sun_el=kw.pop('sun_el', 42), **kw).astype(np.float32)
    bl = cv2.GaussianBlur(img, (0, 0), 1.2); img = img + 0.28 * (img - bl)
    bl2 = cv2.resize(cv2.GaussianBlur(cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3), (W, H)); img = np.clip(img + 0.14 * (img - bl2), 0, 1)
    return grade(img, 0.6)
def glow(img, items): return glow_tracks(img, items, s)
def chrome(b, sec=None, sub=None, so=1.0, eye=None, tgt=None, foot=True):
    U.topbar(b, TITLE)
    if sec: U.section(b, sec, o=so, sub=sub)
    if eye is not None: U.compass(b, heading(eye, tgt))
    if foot: U.footer(b, FOOT)
def post_label(b, lift=70, o=1.0):
    xy, ok = point_xy(pe, pn)
    if ok and q(250) < xy[1] < H - q(60) and q(80) < xy[0] < W - q(80): label(b, xy, 'KHABRI-1 HILL POST', 'post', lift=lift, sub=f'RL {RL_POST} m', o=o)
    return xy, ok

# ---------------------------------------------------------------- drone
import os
ESR = {'A': (0.0, '/home/user/khabri/drone/esr_A.mp4'), 'B': (23.0, '/home/user/khabri/drone/esr_B.mp4'), 'C': (55.0, '/home/user/khabri/drone/esr_C.mp4')}
DC = {}
def _esr(tsrc):
    for k, (a, p) in ESR.items():
        if not os.path.exists(p) or os.path.getsize(p) < 10000: continue
        if k not in DC: c = cv2.VideoCapture(p); DC[k] = [c, -1, int(c.get(cv2.CAP_PROP_FRAME_COUNT)), None]
        c, last, n, fr = DC[k]
        if a - 0.01 <= tsrc < a + n / FPS + 0.5:
            fi = int(min(n - 1, max(0, round((tsrc - a) * FPS))))
            if fi == last: return fr
            if fi != last + 1: c.set(cv2.CAP_PROP_POS_FRAMES, fi)
            ok, fr = c.read()
            if not ok: continue
            DC[k][1], DC[k][3] = fi, fr; return fr
    return None
cap = cv2.VideoCapture(WA)
def drone(tsrc, x0=268):
    """AI-upscaled (Real-ESRGAN x4) master, 16:9 window clear of the player bar and the OS watermark; fallback: source + Lanczos."""
    fr = _esr(tsrc)
    if fr is not None:
        up = cv2.resize(cv2.cvtColor(fr[0:1600, x0:x0 + 2844], cv2.COLOR_BGR2RGB), (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    else:
        cap.set(cv2.CAP_PROP_POS_MSEC, tsrc * 1000); ok, fr = cap.read(); x = x0 // 4
        up = cv2.resize(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)[0:400, x:x + 711], (W, H), interpolation=cv2.INTER_LANCZOS4).astype(np.float32) / 255
    return grade(up, 0.5)
def drone_shot(src0, t, zoom=0.06, dur=8, x0=268):
    img = drone(src0 + t, x0); z = 1 + zoom * sm(t / dur); M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z); return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR)
def drone_chip(b, txt, o=1.0):
    f = F(19, 'b'); w = U.tw(txt, f) + q(30); p = panel_img(w, q(36), NAVY2, 0.88, 8, GOLD, 1.5); ImageDraw.Draw(p).text((q(15), q(7)), txt, font=f, fill=YEL)
    put(b, p, q(24), H - q(96), o)

# ---------------------------------------------------------------- shot durations: set by the voice-over (vo.json) with fixed minimums
def vd(k, pad, mn): return max(mn, VOD[k] + pad)
DUR = dict(open=11.0, orient=vd('orient', 1.6, 14), air=vd('air', 1.6, 9), slope=vd('slope', 1.6, 10), section=vd('section', 1.6, 11), climb=vd('climb', 2.0, 12),
           align=14.0, postair=vd('postair', 1.4, 7), **{k: vd(k, 2.6, 17) for k in ['T1', 'T2', 'T3', 'T4', 'T5']}, top1=vd('top1', 2.2, 15), top2=vd('top2', 2.6, 26),
           compare=vd('compare', 2.0, 15), close=vd('close', 3.2, 12))

# ---------------------------------------------------------------- cold open: drone + B3 title card
def shot1(t):
    D = DUR['open']; b = to_pil(drone_shot(0.0, t, 0.07, D) * seg(t, 0, 1.0))
    U.title_big(b, 'TRACK RECCE - KHABRI-1 HILL POST', 'Five alignments to the post  ·  options for decision', win(t, 1.6, D - 0.5, 0.9, 0.8), t - 1.6)
    drone_chip(b, 'DRONE  ·  Taloband Rg  ·  AI-enhanced  ·  view assessed (no telemetry)', seg(t, 1.0, 1.8))
    return b

# ---------------------------------------------------------------- 9-21 establishing orbit + area orientation
K2 = [rel(300, -2300, 520), rel(-500, -2350, 760), rel(-1100, -2150, 900), rel(-1500, -1550, 880)]
T2_ = [rel(0, 400, 160), rel(60, 280, pz - 40), rel(130, 230, pz - 60), rel(140, 200, pz - 60)]
def shot2(t):
    D = DUR['orient']; u = seg(t, 0, D); eye, tgt = catmull(K2, u), catmull(T2_, u); img = render3d(eye, tgt, 40)
    items = []
    if t > 5.5:
        for P in KMZ3:
            fr = seg(t, 5.5, 9.5); n = max(2, int(len(P) * fr)); xy, v = vis(P[:n]); items.append(dict(xy=xy, vis=v, col=COL['KMZ'], w=3.0, glow=0.5, ghost=False, pulse=fr if fr < 1 else None))
    b = to_pil(glow(img, items) if items else img)
    post_label(b, lift=90, o=seg(t, 2.0, 2.8))
    xy2, ok2 = point_xy(*TAKEOFF_EN)
    if ok2: label(b, xy2, f'Take-off  CH {TAKEOFF_CH:.2f}', 'km', lift=50, o=seg(t, 9.3, 10))
    rows = [('Post', 'Khabri-1 hill post'), ('RL (given)', f'{RL_POST} m'), ('Grid', GRID), ('Range', 'Taloband Rg'),
            ('KMZ tr (existing / planned)', f'{KMZ_KM:.2f} km', (205, 210, 220)), ('Options studied', '5 x alns'), ('Post face slopes S / N', f'{FACE_S:.0f}° / {FACE_N:.0f}°')]
    put(b, table_panel('AREA ORIENTATION', rows, w=470, sub='Desk study on imagery, DEM, drone and gr recce photos'), q(30), H - q(330), seg(t, 1.0, 1.8))
    chrome(b, eye=eye, tgt=tgt); return b

# ---------------------------------------------------------------- 21-29 drone: the ground from the air
def shot3(t):
    b = to_pil(drone_shot(26.0, t, 0.06, DUR['air'], x0=0))
    put(b, text_panel('FROM THE AIR – DRONE', ['Taloband Rg and its badlands foothills', 'Shadi K Nadi beyond (user annotation)', 'Eroded shale spurs, deep gullies',
                                               'Bedding exposed on the faces', ('No telemetry – view assessed', GREY, 'i')], w=470), q(30), q(110), seg(t, 0.6, 1.4))
    drone_chip(b, 'DRONE 00:26 – 00:35  ·  AI-enhanced', seg(t, 0.3, 1.0)); U.topbar(b, TITLE); return b

# ---------------------------------------------------------------- 29-39 slope + drainage
K3 = [rel(900, -1450, 640), rel(400, -1600, 610), rel(-150, -1550, 600)]; T3_ = [rel(-150, 200, pz - 60), rel(-50, 230, pz - 60), rel(0, 250, pz - 60)]
def cam3(t): u = seg(t, 0, DUR['slope']); return catmull(K3, u), catmull(T3_, u)
def slope_legend():
    p = panel_img(q(430), q(150), NAVY2, 0.9, 16); d = ImageDraw.Draw(p); d.text((q(20), q(12)), 'SLOPE (deg)', font=F(24, 'b'), fill=GOLD)
    ramp = np.array([[26, 153, 77], [253, 224, 102], [245, 110, 66], [166, 0, 38]], float); bw = q(390)
    for i in range(bw):
        qq = i / bw * 3; k = min(int(qq), 2); c = ramp[k] + (ramp[k + 1] - ramp[k]) * (qq - k); d.line((q(20) + i, q(50), q(20) + i, q(70)), fill=tuple(int(x) for x in c))
    for i, lab in enumerate(['0', '10', '20', '30', '40+']): d.text((q(20) + i * bw / 4, q(74)), lab, font=F(16), fill=GREY, anchor='ma')
    d.line((q(20), q(124), q(60), q(124)), fill=(64, 191, 255), width=q(5)); d.text((q(72), q(113)), 'Drainage line / nala (> 2 ha)', font=F(18), fill=WHITE); return p
SL = slope_legend()
def shot4(t):
    eye, tgt = cam3(t); img = render3d(eye, tgt, 40, slope_mix=seg(t, 0.5, 2.5), drain_mix=seg(t, 3, 5))
    b = to_pil(glow(img, kmz_items(0.6))); post_label(b, 70)
    put(b, SL, q(30), H - q(230), seg(t, 0.8, 1.6))
    xs, oks = point_xy(pe - 60, pn - 260); xn, okn = point_xy(pe + 40, pn + 230)
    if oks: label(b, xs, f'S FACE ≈ {FACE_S:.0f}°  (mean, 250 m)', 'face', lift=40, o=seg(t, 5.5, 6.2))
    if okn: label(b, xn, f'N FACE ≈ {FACE_N:.0f}°  (mean, 250 m)', 'face', lift=110, o=seg(t, 6.3, 7))
    chrome(b, 'TERRAIN – SLOPE & DRAINAGE', 'Slope from Cop GLO-30  ·  D8 flow lines', eye=eye, tgt=tgt); return b

# ---------------------------------------------------------------- 39-49 strata: section + drone
SECT = {}
def shot5(t):
    if not SECT:
        eye, tgt = cam3(DUR['slope']); SECT['bg'] = cv2.GaussianBlur(render3d(eye, tgt, 40), (0, 0), 20) * 0.5
        d_ = np.arange(-450, 451, 5); SECT['d'] = d_; SECT['z'] = dem(*ll(pe + 0 * d_, pn + d_))
    img = SECT['bg'].copy(); b = to_pil(img)
    # section panel (left)
    pw, ph = q(1000), q(700); p = panel_img(pw, ph, NAVY2, 0.9, 16); d = ImageDraw.Draw(p); d.text((q(22), q(14)), 'N–S SECTION THROUGH THE POST  (Cop GLO-30, true scale)', font=F(24, 'b'), fill=GOLD)
    d_, z_ = SECT['d'], SECT['z']; gx, gy, gw, gh = q(80), q(80), pw - q(120), ph - q(150); n = max(2, int(len(d_) * seg(t, 0.4, 3.5)))
    X = gx + (d_ + 450) / 900 * gw; Y = gy + gh - (z_ - 20) / 150 * gh
    for zl in (40, 80, 120, 160): yl = gy + gh - (zl - 20) / 150 * gh; d.line((gx, yl, gx + gw, yl), fill=(255, 255, 255, 45), width=1); d.text((gx - q(8), yl), f'{zl} m', font=F(15), fill=GREY, anchor='rm')
    d.polygon([(X[0], gy + gh)] + list(zip(X[:n], Y[:n])) + [(X[n - 1], gy + gh)], fill=(150, 125, 95, 255)); d.line(list(zip(X[:n], Y[:n])), fill=GOLD, width=q(3))
    d.text((gx, gy + gh + q(10)), 'S', font=F(24, 'b'), fill=WHITE); d.text((gx + gw, gy + gh + q(10)), 'N', font=F(24, 'b'), fill=WHITE, anchor='ra')
    xp = gx + gw / 2; d.line((xp, gy, xp, gy + gh), fill=(255, 255, 255, 140), width=q(1.5)); d.text((xp + q(8), gy + q(4)), 'POST', font=F(18, 'b'), fill=WHITE)
    put(b, p, q(30), q(110), seg(t, 0, 0.6))
    iS = int(np.argmin(np.abs(d_ + 120))); iN = int(np.argmin(np.abs(d_ - 120)))
    label(b, (q(30) + X[iS], q(110) + Y[iS]), f'S face ≈ {FACE_S:.0f}°', 'face', lift=60, o=seg(t, 3.5, 4.2))
    label(b, (q(30) + X[iN], q(110) + Y[iN]), f'N face ≈ {FACE_N:.0f}°', 'face', lift=70, o=seg(t, 4.3, 5))
    # drone inset (right)
    dr = (drone(58 + t) * 255).astype(np.uint8); dw = q(800); di = Image.fromarray(dr).resize((dw, int(dw * 9 / 16)), Image.LANCZOS)
    put(b, photo_panel(di, 'DRONE 00:58 – 01:08  ·  post ridge, S face', [('Bedding crops out on the face (assessed)', WHITE)], w=828, tag='DRONE'), W - q(860), q(110), seg(t, 0.3, 1.2))
    put(b, text_panel('READING THE STRATA – ASSESSED', ['Bedding strikes ENE–WSW along the ridge', 'Bedding crops out on BOTH faces', '→ beds gently dipping / near-horizontal',
                                                        'No dip-slope (planar slide) face identified', ('Confirm dip on the ground', (255, 170, 120), 'b')], w=828), W - q(860), q(700), seg(t, 5, 6))
    chrome(b); return b

# ---------------------------------------------------------------- 49-63 five alignments draw on
DRAW = {k: (0.3 + 2.6 * i, 2.6 + 2.6 * i) for i, k in enumerate(ORDER)}
def cam6(t):
    u = seg(t, 0, 14); az = math.radians(212 + 38 * u); r = 2300 - 350 * u
    return (pe + r * math.sin(az), pn + r * math.cos(az), 1100 - 150 * u), (pe + 120, pn + 220, pz - 70)
def legend_al(upto):
    rows = [k for i, k in enumerate(ORDER) if i <= upto] + ['KMZ']; h = q(60) + q(30) * len(rows) + q(10)
    p = panel_img(q(400), h, NAVY2, 0.9, 16); d = ImageDraw.Draw(p); d.text((q(20), q(14)), 'ALIGNMENTS', font=F(24, 'b'), fill=GOLD)
    for i, k in enumerate(rows):
        y = q(56) + q(30) * i; d.line((q(20), y + q(11), q(56), y + q(11)), fill=COL[k], width=q(5))
        d.text((q(68), y), f'{k}   {DESC[k]}' if k != 'KMZ' else 'KMZ tr (existing / planned)', font=F(19, 'b' if k != 'KMZ' else 'r'), fill=WHITE)
    return p
TAGOFF = {'T1': 50, 'T2': 70, 'T3': 60, 'T4': 60, 'T5': 60}
def shot6(t):
    eye, tgt = cam6(t); img = render3d(eye, tgt, 38); items = kmz_items(0.7)
    for k in ORDER:
        a, b_ = DRAW[k]
        if t >= a: fr = seg(t, a, b_); items.append(dict(track_item(k, max(fr, 0.01), w=5.2, glow=1.0 if t < b_ + 0.5 else 0.8, pulse=fr if fr < 1 else ((t - b_) * 0.25) % 1), outline=0.8))
    b = to_pil(glow(img, items)); post_label(b, 80)
    for k in ORDER:
        if t >= DRAW[k][1]:
            P, _ = TR[k]; i = int(0.35 * len(P)); xy2, v2 = vis(P[i:i + 1])
            if v2[0]: label(b, xy2[0], k, col=COL[k], lift=TAGOFF[k], o=seg(t, DRAW[k][1], DRAW[k][1] + 0.5))
    upto = max([ORDER.index(k) for k in ORDER if t >= DRAW[k][0]] + [-1]); put(b, legend_al(upto), q(30), H - q(300), seg(t, 0.2, 1))
    chrome(b, 'FIVE ALIGNMENTS', 'Least-cost corridors on the terrain model  ·  five distinct approaches', eye=eye, tgt=tgt); return b

# ---------------------------------------------------------------- 63-69 drone: the post from the air
def shot6b(t):
    b = to_pil(drone_shot(62.6, t, 0.05, DUR['postair']))
    put(b, text_panel('THE POST FROM THE AIR', ['Khabri I on the crest line (user annotation, 01:06)', 'Steep, gullied faces below the post', ('View assessed – no telemetry', GREY, 'i')], w=520),
        q(30), q(110), seg(t, 0.4, 1.2))
    drone_chip(b, 'DRONE 01:02 – 01:09  ·  AI-enhanced', seg(t, 0.2, 0.9)); U.topbar(b, TITLE); return b

# ---------------------------------------------------------------- 69-154 five options: fly 6 s - STOP 6 s (gr recce) - fly 5 s
SMP = {}
for k in ORDER:
    P, _ = TR[k]; Q = P.copy(); sg = max(8, min(30, len(P) // 12))
    for c in range(3): Q[:, c] = gaussian_filter1d(P[:, c], sg, mode='nearest')
    SMP[k] = Q
FLY, STOP0 = 11.0, 6.0
def cam_fly(k, tf):
    Q = SMP[k]; n = len(Q); u = 0.04 + 0.88 * seg(tf, 0, FLY - 0.4); i = int(u * (n - 1)); c = Q[i]; lk = 60
    a = Q[max(0, i - lk)]; bq = Q[min(n - 1, i + lk)]; fwd = bq[:2] - a[:2]; fwd /= (np.linalg.norm(fwd) + 1e-9); side = np.array([-fwd[1], fwd[0]])
    exy = c[:2] - fwd * 760 + side * 140
    ez = max(c[2] + 560, float(Sc.height(np.array([exy[0]]), np.array([exy[1]]))[0]) + 280)
    ahead = Q[min(n - 1, i + 110)]; w_ = seg(tf, 5.0, FLY); tgt = ahead * (1 - w_) + np.array([pe, pn, pz]) * w_; tgt = tgt - np.array([0, 0, 20])
    return (exy[0], exy[1], ez), tuple(tgt), u
PHOTO = {'T1': (1, 'Post on the crest above a scree-covered wadi', 'Loose shale scree and slabs on a firm silty floor'),
         'T2': (2, 'Recce party moving up the wadi towards the post', 'Shale debris and boulders; eroded shale spurs either side'),
         'T3': (3, 'Firm, fine-grained floor between eroded shale ridges', 'Compact silt with shale chips – good going when dry (assessed)'),
         'T4': (5, 'Platy shale slabs and debris on the slope', 'Loose on slopes, rippable by dozer / Excavator (assessed)'),
         'T5': (4, 'Nala bed with loose shale and boulders', f"T5 crosses {MT['T5']['nala_xings']} nalas – bed material of this type (assessed)")}
PIMG = {k: Image.open(f'{PH}/{v[0]}.jpg').convert('RGB') for k, v in PHOTO.items()}
def gtxt(g):
    return (f'+{g:.0f} %' if g >= 0.5 else f'{g:.0f} %'), ((120, 175, 255) if abs(g) <= 10 else (AMBER if abs(g) <= 100 / 7 else (255, 80, 80)))
def facts(k):
    m = MT[k]; p = POL[k]; red = (255, 95, 95); amb = AMBER
    rows = [('New const', f"{m['new_const_m'] / 1000:.2f} km"), ('Take-off on KMZ tr', f"CH {m['junction_ch_km']:.2f} km"), ('Climb', f"{m['gain_m']:.0f} m"),
            ('Max / mean grade', f"{m['max_grade_pct']:.1f} / {m['mean_grade_pct']:.1f} %", red if m['max_grade_pct'] > 100 / 7 else WHITE),
            ('Length > 1:10 / > 1:7 / > 1:5', f"{m['pct_gt_1in10']:.0f} / {m['pct_gt_1in7']:.0f} / {m['pct_gt_1in5']:.0f} %"),
            ('Hairpins', f"{m['hairpins']}"), ('Nala xings', f"{m['nala_xings']}", amb if m['nala_xings'] else WHITE),
            ('Cut (assessed, ±50 %)', f"{p['cut_total']:,.0f} cu M"), ('Exposure crest / low gnd', f"{m['expo_dominating_pct']:.0f} / {m['expo_plain_road_pct']:.0f} %"),
            ('POL', f"{p['total']:,} lits", GOLD), ('Work days (1 Dozer + 1 Excavator)', f"{p['dur']}", GOLD)]
    return table_panel(f'{k}  –  {DESC[k].upper()}', rows, w=560, sub=LONG[k], accent=COL[k], lh=29, fs=19)
FROZ = {}
def fly(k):
    D = DUR[k]; STOP1 = D - 5.0
    def ftime(t): return t if t < STOP0 else (STOP0 if t < STOP1 else t - (STOP1 - STOP0))
    pr = PR[k]; ss_ = np.array(pr['s']); zz = np.array(pr['z']); gg = np.array(pr['g']) * 100; jch = MT[k]['junction_ch_km']
    def base(tf):
        eye, tgt, u = cam_fly(k, tf); img = render3d(eye, tgt, 44)
        items = kmz_items(0.55) + [dict(track_item(j, w=3.4, glow=0.35, col=tuple(int(c * 0.72) for c in COL[j])), outline=0.6) for j in ORDER if j != k] + [dict(track_item(k, w=7, glow=1.4, pulse=u), outline=0.9)]
        return glow(img, items), eye, tgt, u
    def f(t):
        tf = ftime(t); stop = STOP0 <= t < STOP1
        if stop:
            if k not in FROZ: FROZ[k] = base(STOP0)
            img, eye, tgt, u = FROZ[k]; a = seg(t, STOP0, STOP0 + 0.7) * (1 - seg(t, STOP1 - 0.6, STOP1))
            if a > 0.003: img = img * (1 - a) + cv2.GaussianBlur(img, (0, 0), 14) * 0.45 * a
        else: img, eye, tgt, u = base(tf)
        b = to_pil(img); ov = 1 - (seg(t, STOP0, STOP0 + 0.5) * (1 - seg(t, STOP1 - 0.5, STOP1)))
        if ov > 0.01:
            post_label(b, 80, o=ov)
            j = int(u * (len(ss_) - 1)); gt, gc = gtxt(gg[j])
            U.hud(b, f'{jch + ss_[j] / 1000:.2f} km', f'{zz[j]:.0f} m', gt, gc, f'{k} · {DESC[k]}', COL[k], o=seg(t, 0.3, 1.0) * ov)
            U.profile_strip(b, ss_, zz, np.abs(gg), u, COL[k], o=seg(t, 0.5, 1.2) * ov); U.legend_grade(b, o=seg(t, 0.5, 1.2) * ov)
        if stop:
            a2 = seg(t, STOP0 + 0.3, STOP0 + 1.0) * (1 - seg(t, STOP1 - 0.6, STOP1)); n_, cap1, cap2 = PHOTO[k]
            put(b, facts(k), q(30), q(200), a2)
            put(b, photo_panel(PIMG[k], 'GR RECCE – WHAT THE GROUND LOOKS LIKE', [(cap1, WHITE, 'b'), (cap2, (225, 230, 240)), ('Photo not geotagged – representative of the ground on the approaches', GREY, 'i')],
                               w=800, accent=COL[k], tag='GR RECCE PHOTO'), W - q(830), q(110), seg(t, STOP0 + 0.6, STOP0 + 1.3) * (1 - seg(t, STOP1 - 0.6, STOP1)))
        chrome(b, f'OPTION {k[1]}  ·  {DESC[k].upper()}', LONG[k], eye=eye, tgt=tgt); return b
    return f


# ---------------------------------------------------------------- ground photos (AI-enhanced copies if present)
PE = '/home/user/khabri/photos_esr'
def photo(n): p = f'{PE}/{n}.jpg'; return Image.open(p if os.path.exists(p) else f'{PH}/{n}.jpg').convert('RGB')
PIMG = {k: photo(v[0]) for k, v in PHOTO.items()}
PCACHE = {}
def cover(n, z, cx, cy):
    """full-frame crop of photo n at zoom z centred on (cx, cy) (fractions). returns float img and photo->screen mapper (photo px in 1600x1200 frame)."""
    if n not in PCACHE: PCACHE[n] = photo(n)
    im = PCACHE[n]; iw, ih = im.size; k0 = iw / 1600.0
    sc = max(W / iw, H / ih) * z; vw, vh = W / sc, H / sc
    x0 = float(np.clip(cx * iw - vw / 2, 0, iw - vw)); y0 = float(np.clip(cy * ih - vh / 2, 0, ih - vh))
    out = np.asarray(im.transform((W, H), Image.EXTENT, (x0, y0, x0 + vw, y0 + vh), Image.BICUBIC)).astype(np.float32) / 255
    return grade(out, 0.35), (lambda px, py: ((px * k0 - x0) * sc, (py * k0 - y0) * sc))
def photo_seq(t, D, seq):
    """seq: [(n, z0, z1, (cx0, cy0), (cx1, cy1), labels)] shown in equal parts with 0.8 s dissolves; labels (px, py, txt, kind, lift)"""
    n_ = len(seq); part = D / n_; i = min(n_ - 1, int(t / part)); tl = t - i * part
    def one(j, tl_):
        n, z0, z1, c0, c1, labs = seq[j]; u = sm(tl_ / (part + 0.8)); img, mp = cover(n, z0 + (z1 - z0) * u, c0[0] + (c1[0] - c0[0]) * u, c0[1] + (c1[1] - c0[1]) * u)
        return img, mp, labs
    img, mp, labs = one(i, tl)
    if i + 1 < n_ and tl > part - 0.8:
        a = float(sm((tl - (part - 0.8)) / 0.8)); img2, mp2, labs2 = one(i + 1, tl - part); img = img * (1 - a) + img2 * a
        if a > 0.5: mp, labs, tl = mp2, labs2, tl - part
    b = to_pil(img * seg(t, 0, 0.5) if i == 0 else img)
    for (px, py, txt, kind, lift) in labs:
        label(b, mp(px, py), txt, kind, lift=lift, o=seg(tl, 1.0, 1.6) * (1 - seg(tl, part - 0.9, part - 0.5)))
    return b
def climb(t):
    D = DUR['climb']
    b = photo_seq(t, D, [(7, 1.0, 1.14, (0.47, 0.42), (0.47, 0.40), [(742, 512, 'KHABRI-1 POST ON THE SKYLINE', 'post', 70)]),
                         (6, 1.12, 1.0, (0.45, 0.55), (0.5, 0.5), [(330, 760, 'Loose shale scree & slabs', 'place', 60), (860, 470, 'Gullied white silt-shale spur', 'place', 80)])])
    put(b, text_panel('ON THE GROUND – THE CLIMB', ['Loose shale scree and slabs underfoot', 'Steep, gullied silt-shale spurs either side', 'Post on the skyline throughout the climb',
                                                     ('Gr recce photos – not geotagged', GREY, 'i')], w=520), q(30), q(110), seg(t, 0.6, 1.4))
    drone_chip(b, 'GR RECCE PHOTOS  ·  going up', seg(t, 0.3, 1.0)); U.topbar(b, TITLE); return b
def top1(t):
    D = DUR['top1']
    b = photo_seq(t, D, [(10, 1.0, 1.08, (0.55, 0.45), (0.6, 0.42), [(1390, 300, "EXISTING ROOM  32' × 32'", 'post', 40), (930, 330, 'Mast', 'place', 140), (900, 960, 'Platy shale – loose surface layer', 'place', 40)]),
                         (9, 1.06, 1.0, (0.5, 0.5), (0.45, 0.5), [(600, 560, 'Badlands below the crest', 'place', 60), (760, 930, 'Shale slab surface on the crest', 'place', 40)])])
    put(b, text_panel('AT THE TOP', ['Narrow crest of platy shale, running ENE', "Existing room 32' × 32' with mast", "40' × 40' pad req alongside, for the post",
                                     ('Gr recce photos – not geotagged', GREY, 'i')], w=520), q(30), q(110), seg(t, 0.6, 1.4))
    drone_chip(b, 'GR RECCE PHOTOS  ·  the crest', seg(t, 0.3, 1.0)); U.topbar(b, TITLE); return b

# ---------------------------------------------------------------- the 40' x 40' post pad (3D crest + cut / fill + scope + POL)
PC = np.array(PAD['centre_en']); PU = np.array(PAD['u']); PV = np.array(PAD['v']); HP = PAD['pad_m'] / 2; HW = PAD['work_m'] / 2; HR = PAD['room_ft'] * 0.3048 / 2
RCN = np.array([pe, pn]); FORM = PAD['z_max'] - PAD['formation_below_high']
def pad_plan_panel():
    """engineering plan of the crest: DEM hillshade + 0.5 m contours, cut / fill over the pad, room, pad, dims. Frame aligned to the crest axis (ENE to the right)."""
    w_, h_ = 1180, 600; p = panel_img(q(w_), q(h_), NAVY2, 0.92, 16); d = ImageDraw.Draw(p)
    d.text((q(20), q(14)), 'PLAN – POST PAD ON THE CREST', font=F(24, 'b'), fill=GOLD)
    d.text((q(w_ - 20), q(18)), 'Contours 0.5 m (index 2 m)  ·  Cop GLO-30  ·  pad site assessed', font=F(16, 'i'), fill=GREY, anchor='ra')
    ix, iy, iw, ih = q(20), q(56), q(w_ - 40), q(h_ - 76); C = (RCN + PC) / 2; Lx = 84.0; mpx = Lx / iw; Ly = ih * mpx
    xs = (np.arange(iw) + 0.5) * mpx - Lx / 2; ys = (np.arange(ih) + 0.5) * mpx - Ly / 2; X, Y = np.meshgrid(xs, ys)
    E = C[0] + X * PU[0] + Y * PV[0]; N = C[1] + X * PU[1] + Y * PV[1]; Z = dem(*ll(E, N)).astype(np.float32)
    gy, gx = np.gradient(Z, mpx); sh = np.clip(0.55 + 0.45 * (-gx * 0.6 - gy * 0.8) / np.sqrt(1 + gx ** 2 + gy ** 2), 0, 1)
    zt = (Z - Z.min()) / max(1e-3, Z.max() - Z.min()); base = np.stack([0.55 + 0.25 * zt, 0.50 + 0.22 * zt, 0.42 + 0.18 * zt], -1) * sh[..., None]
    lp = (X - (PC - C) @ PU); lq = (Y - (PC - C) @ PV); inW = (np.abs(lp) <= HW) & (np.abs(lq) <= HW); dz = Z - FORM
    a = np.clip(np.abs(dz) / 3.5, 0.25, 0.85)[..., None] * inW[..., None]
    col = np.where((dz > 0)[..., None], np.array([0.92, 0.24, 0.20]), np.array([0.24, 0.55, 1.0])); base = base * (1 - a) + col * a
    ql = np.floor(Z / 0.5); edge = np.zeros_like(Z, bool); edge[:, 1:] |= ql[:, 1:] != ql[:, :-1]; edge[1:] |= ql[1:] != ql[:-1]
    idx = edge & (np.abs(np.mod(ql * 0.5, 2.0)) < 0.25)
    base[edge] = base[edge] * 0.55; base[idx] = np.array([0.98, 0.95, 0.85])
    im = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)); m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, iw - 1, ih - 1), q(8), fill=255)
    im = im.convert('RGBA'); im.putalpha(m); p.alpha_composite(im, (ix, iy))
    def S(e_n): v_ = np.asarray(e_n) - C; return (ix + (v_ @ PU + Lx / 2) / mpx, iy + (v_ @ PV + Ly / 2) / mpx)
    def rect(c, h, **kw):
        pts = [S(c + a_ * PU + b_ * PV) for a_, b_ in ((-h, -h), (h, -h), (h, h), (-h, h))]; d.polygon(pts, **kw); return pts
    ax0, ax1 = S(PC - PU * 41), S(PC + PU * 41); d.line((ax0, ax1), fill=(255, 215, 100), width=q(2))
    d.text((ax1[0] - q(6), ax1[1] - q(8)), f"Crest axis {PAD['crest_az']:03d}°", font=F(16, 'b'), fill=(255, 215, 100), anchor='rb')
    pts = rect(RCN, HR, fill=(235, 235, 235, 235), outline=(40, 40, 40), width=q(2))
    rc = S(RCN); d.text(rc, "EXISTING\nROOM 32' x 32'", font=F(15, 'b'), fill=(20, 20, 20), anchor='mm', align='center')
    wp = rect(PC, HW, outline=(255, 255, 255));
    for k in range(4):
        x0_, y0_ = wp[k]; x1_, y1_ = wp[(k + 1) % 4]
        for s0 in np.arange(0, 1, 0.1): d.line((x0_ + (x1_ - x0_) * s0, y0_ + (y1_ - y0_) * s0, x0_ + (x1_ - x0_) * (s0 + 0.05), y0_ + (y1_ - y0_) * (s0 + 0.05)), fill=WHITE, width=q(2))
    pp = rect(PC, HP, outline=GOLD, width=q(4)); pc_ = S(PC)
    d.text((pc_[0], pc_[1]), "POST PAD\n40' x 40'", font=F(20, 'b'), fill=WHITE, anchor='mm', align='center', stroke_width=q(2), stroke_fill=(0, 0, 0))
    tm = ((pp[0][0] + pp[1][0]) / 2, (pp[0][1] + pp[1][1]) / 2 - q(14)); d.text(tm, "40'", font=F(16, 'b'), fill=GOLD, anchor='mb')
    nv = np.array([PU[1], PV[1]]); nv /= np.linalg.norm(nv); nx, ny = ix + iw - q(60), iy + q(70)
    d.line((nx - nv[0] * q(30), ny - nv[1] * q(30), nx + nv[0] * q(30), ny + nv[1] * q(30)), fill=WHITE, width=q(3))
    d.polygon([(nx + nv[0] * q(38), ny + nv[1] * q(38)), (nx + nv[0] * q(22) - nv[1] * q(8), ny + nv[1] * q(22) + nv[0] * q(8)), (nx + nv[0] * q(22) + nv[1] * q(8), ny + nv[1] * q(22) - nv[0] * q(8))], fill=WHITE)
    d.text((nx + nv[0] * q(50), ny + nv[1] * q(50)), 'N', font=F(18, 'b'), fill=WHITE, anchor='mm')
    sx, sy = ix + q(24), iy + ih - q(30); L10 = 10 / mpx; d.rectangle((sx, sy, sx + L10, sy + q(7)), fill=WHITE); d.rectangle((sx + L10 / 2, sy, sx + L10, sy + q(7)), fill=(20, 20, 20), outline=WHITE)
    d.text((sx, sy - q(4)), '0', font=F(14, 'b'), fill=WHITE, anchor='lb'); d.text((sx + L10, sy - q(4)), '10 m', font=F(14, 'b'), fill=WHITE, anchor='rb')
    lx = ix + iw - q(250); ly = iy + ih - q(34)
    d.rounded_rectangle((lx - q(10), ly - q(8), ix + iw - q(10), ly + q(24)), q(6), fill=(8, 22, 58, 220))
    d.rectangle((lx, ly, lx + q(16), ly + q(16)), fill=(235, 60, 50)); d.text((lx + q(22), ly - q(1)), 'Cut', font=F(16, 'b'), fill=WHITE)
    d.rectangle((lx + q(80), ly, lx + q(96), ly + q(16)), fill=(60, 140, 255)); d.text((lx + q(102), ly - q(1)), 'Fill', font=F(16, 'b'), fill=WHITE)
    d.line((lx + q(160), ly + q(8), lx + q(190), ly + q(8)), fill=GOLD, width=q(4)); d.text((lx + q(196), ly - q(1)), 'Pad', font=F(16, 'b'), fill=WHITE)
    return p
def pad_section_panel():
    w_, h_ = 1180, 300; p = panel_img(q(w_), q(h_), NAVY2, 0.9, 16); d = ImageDraw.Draw(p)
    d.text((q(20), q(14)), 'SECTION ACROSS THE PAD  (normal to the crest, through pad centre)', font=F(22, 'b'), fill=GOLD)
    s_ = np.linspace(-30, 30, 241); P = PC[None] + s_[:, None] * PV[None]; z = dem(*ll(P[:, 0], P[:, 1])); f = FORM
    gx, gy, gw, gh = q(80), q(56), q(w_ - 120), q(h_ - 104); zlo, zhi = min(z.min(), f) - 1, max(z.max(), f) + 1
    sc_ = min(gw / 60, gh / (zhi - zlo)); X = lambda v_: gx + gw / 2 + v_ * sc_; Y = lambda zz: gy + gh - (zz - zlo) * sc_
    for i in range(len(s_) - 1):
        if abs(s_[i]) <= HW:
            c = (235, 60, 50, 210) if z[i] > f else (60, 140, 255, 210)
            d.polygon([(X(s_[i]), Y(z[i])), (X(s_[i + 1]), Y(z[i + 1])), (X(s_[i + 1]), Y(f)), (X(s_[i]), Y(f))], fill=c)
    d.line([(X(a_), Y(b_)) for a_, b_ in zip(s_, z)], fill=WHITE, width=q(3)); d.line((X(-HW), Y(f), X(HW), Y(f)), fill=GOLD, width=q(4))
    for zl in range(int(np.ceil(zlo)), int(zhi) + 1, 2): d.text((X(-30) - q(10), Y(zl)), f'{zl} m', font=F(14), fill=GREY, anchor='rm')
    d.text((X(0), Y(f) + q(8)), 'FORMATION (level)', font=F(15, 'b'), fill=GOLD, anchor='ma')
    d.text((X(-30), gy + gh + q(10)), 'N', font=F(18, 'b'), fill=WHITE, anchor='ma'); d.text((X(30), gy + gh + q(10)), 'S', font=F(18, 'b'), fill=WHITE, anchor='ma')
    d.text((X(0), gy + gh + q(12)), f"{PAD['work_m']:.1f} m working width  ·  true scale (no exaggeration)  ·  DEM elevations", font=F(15, 'i'), fill=GREY, anchor='ma')
    return p
def pol_panel():
    cols = [('Description', 300), ('A/U', 60), ('Qty', 60), ('LPH', 60), ('Lits', 90)]; tw_ = sum(c[1] for c in cols) + 24; rh = 36
    rows = [(r['d'].split(' (')[0], r['au'], str(r['q']), f"{r['r']:g}", f"{r['l']:,}") for r in PAD['rows']]
    h = q(54) + q(rh) * (len(rows) + 3) + q(76); p = panel_img(q(tw_), h, NAVY2, 0.92, 16, GOLD, 2); d = ImageDraw.Draw(p)
    d.text((q(16), q(14)), "POL REQ – POST PAD 40' x 40'", font=F(24, 'b'), fill=GOLD); y0 = q(54)
    def row(y, vals, fill, fc=WHITE, bold=False):
        d.rectangle((q(10), y, q(tw_ - 10), y + q(rh)), fill=fill); x = q(10)
        for i, (v, (c, w_)) in enumerate(zip(vals, cols)):
            if i == 0: d.text((x + q(8), y + q(rh / 2)), v, font=F(17, 'b' if bold else 'r'), fill=fc, anchor='lm')
            else: d.text((x + q(w_) - q(8), y + q(rh / 2)), v, font=F(17, 'b'), fill=fc, anchor='rm')
            x += q(w_)
    row(y0, [c for c, _ in cols], (200, 30, 30), bold=True)
    for i, r in enumerate(rows): row(y0 + q(rh) * (i + 1), list(r), (18, 38, 84) if i % 2 == 0 else (12, 28, 66))
    yt = y0 + q(rh) * (len(rows) + 1); row(yt, ['Total', '', '', '', f"{PAD['total']:,}"], (40, 46, 20), GOLD, True)
    c_ = PAD['contingency']; row(yt + q(rh), ['Jack Hammer (contingency)', c_['au'], str(c_['q']), f"{c_['r']:g}", f"{c_['l']:,}"], (12, 28, 66), AMBER)
    d.text((q(16), yt + q(rh) * 2 + q(12)), f"Work days: {PAD['days']}  (1 Excavator + 1 Dozer, once a tr reaches the top)", font=F(17, 'b'), fill=WHITE)
    d.text((q(16), yt + q(rh) * 2 + q(40)), 'Qty incl 10 % margin  ·  user POL stds  ·  contingency: hard shale bands, 20 % of cut', font=F(15, 'i'), fill=GREY)
    return p
PADP = {}
def top2(t):
    D = DUR['top2']; T9 = 8.0
    def cam(tt):
        u = sm(tt / T9); az = math.radians(150 + 25 * u); el = math.radians(30 + 6 * u); r = 1700 - 500 * u; zc = float(Sc.height(np.array([RCN[0]]), np.array([RCN[1]]))[0])
        tgt = (RCN[0], RCN[1], zc); return (RCN[0] + r * math.cos(el) * math.sin(az), RCN[1] + r * math.cos(el) * math.cos(az), zc + r * math.sin(el)), tgt
    if t < T9: eye, tgt = cam(t); img = render3d(eye, tgt, 34)
    else:
        if 'bg' not in PADP: e_, g_ = cam(T9); PADP['bg'] = (render3d(e_, g_, 34), e_, g_)
        img, eye, tgt = PADP['bg']
    a = seg(t, T9 - 0.4, T9 + 0.6)
    if a > 0: img = img * (1 - a) + cv2.GaussianBlur(img, (0, 0), 16) * 0.4 * a
    b = to_pil(img); o = 1 - a
    if o > 0.01:
        xy_r, _ = point_xy(*RCN); label(b, xy_r, 'KHABRI-1 POST – EXISTING ROOM', 'post', lift=120, o=seg(t, 1.0, 1.6) * o)
        xy_p, _ = point_xy(*PC); label(b, xy_p, "PROPOSED PAD 40' x 40'", 'place', lift=40, o=seg(t, 2.4, 3.0) * o, col=GOLD)
    if not PADP.get('plan'):
        PADP['plan'] = pad_plan_panel(); PADP['sect'] = pad_section_panel(); PADP['pol'] = pol_panel()
        PADP['scope'] = table_panel('POST PAD – SCOPE OF WORK', [('Pad', "40' x 40'  (12.2 x 12.2 m)"), ('Working area (1 m margin)', f"{PAD['work_m']:.1f} x {PAD['work_m']:.1f} m"),
            ('Siting', 'on crest, alongside room, least earthwork'), ('Ground relief over pad', f"{PAD['relief']:.1f} m"), ('Formation (level, balanced)', f"{PAD['formation_below_high']:.1f} m below high pt"),
            ('Cut', f"{PAD['cut']:,.0f} cu M", (255, 110, 100)), ('Fill', f"{PAD['fill']:,.0f} cu M", (120, 175, 255)),
            ('Balance', 'cut = fill, no import / spoil'), ('Toe of fill', 'dry-stone wall, shale slabs'), ('30 m DEM smooths a narrow crest', 'confirm by levels on gr', AMBER)],
            w=640, sub='Cop GLO-30 at 0.25 m  ·  ±50 % (assessed)', lh=28, fs=18)
    put(b, PADP['plan'], q(30), q(110), seg(t, T9, T9 + 0.8))
    put(b, PADP['sect'], q(30), q(730), seg(t, T9 + 6.0, T9 + 6.8))
    put(b, PADP['scope'], W - q(30) - PADP['scope'].size[0], q(110), seg(t, T9 + 2.0, T9 + 2.8))
    put(b, PADP['pol'], W - q(30) - PADP['pol'].size[0], q(520), seg(t, T9 + 10.0, T9 + 10.8))
    chrome(b, "POST PAD 40' x 40' – LEVEL OF WORK" if t < T9 else None, 'Pad alongside the existing room on the crest', so=1 - a, eye=eye if t < T9 else None, tgt=tgt); return b


# ---------------------------------------------------------------- comparison (plan + B3 table, no scores)
RX = np.vstack([TR[k][0][:, :2] for k in ORDER]); RC = (RX.min(0) + RX.max(0)) / 2
PLAN = {}
def tag(b, xy, txt, col, dx, dy, o=1.0):
    L = Image.new('RGBA', b.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L); f = F(24, 'b'); w_ = U.tw(txt, f) + q(22); h_ = q(38)
    x, y = xy; bx, by = x + q(dx) - w_ / 2, y + q(dy) - h_ / 2
    d.line((x, y, x + q(dx), y + q(dy)), fill=(255, 255, 255, 235), width=q(2)); d.ellipse((x - q(6), y - q(6), x + q(6), y + q(6)), fill=col + (255,), outline=(255, 255, 255, 255), width=q(2))
    d.rounded_rectangle((bx + q(2), by + q(3), bx + w_ + q(2), by + h_ + q(3)), q(7), fill=(0, 0, 0, 120))
    d.rounded_rectangle((bx, by, bx + w_, by + h_), q(7), fill=col + (245,), outline=(255, 255, 255, 230), width=q(1.5))
    d.text((bx + w_ / 2, by + h_ / 2), txt, font=f, fill=WHITE if sum(col) < 560 else (0, 0, 0), anchor='mm')
    if o < 1: L.putalpha(L.getchannel('A').point(lambda v: int(v * o)))
    b.alpha_composite(L)
TAGS = {'T1': (0.45, 60, 150), 'T2': (0.75, -170, 120), 'T3': (0.5, -150, -90), 'T4': (0.6, 170, 40), 'T5': (0.62, -230, 40)}
def plan_base():
    if PLAN: return PLAN['b'], PLAN['mpp']
    ce, cn = RC[0] + 60, RC[1] + 40; eye = (ce, cn - 20, 2700); tgt = (ce, cn, 0)
    img = Sc.render(eye, tgt, fov=34, sun_az=135, sun_el=42, haze=0.2).astype(np.float32); img = grade(img, 0.6) * 0.92
    items = [dict(xy=vis(P)[0], vis=np.ones(len(P), bool), col=COL['KMZ'], w=3.0, glow=0.3, ghost=False, outline=0.6) for P in KMZ3]
    items += [dict(xy=vis(TR[k][0])[0], vis=np.ones(len(TR[k][0]), bool), col=COL[k], w=6.5, glow=0.7, outline=0.9) for k in ORDER]
    b = to_pil(glow(img, items))
    for k in ORDER:
        fr, dx, dy = TAGS[k]; P = TR[k][0]; i = int(fr * (len(P) - 1)); xy = vis(P[i:i + 1])[0][0]; tag(b, xy, f'{k}  {DESC[k]}', COL[k], dx, dy)
    xy0, _ = vis(np.array([[pe, pn, pz]])); label(b, xy0[0], 'KHABRI-1 POST', 'post', lift=70)
    xy1, _ = vis(np.array([[pe + 500, pn, pz]])); PLAN['b'] = b; PLAN['mpp'] = 500 / abs(xy1[0, 0] - xy0[0, 0])
    return PLAN['b'], PLAN['mpp']
COLS = [('Option', 92), ('New km', 78), ('Max %', 72), ('>1:10', 64), ('>1:7', 58), ('>1:5', 58), ('Hairpins', 80), ('Nala', 56), ('Cut cu M', 96), ('Expo crest/low', 124), ('POL lits', 90), ('Days', 58)]
def cmp_table(nrows):
    tw_ = sum(c[1] for c in COLS) + 24; rh = 40; h = q(70) + q(rh) * 6 + q(20)
    p = panel_img(q(tw_), h, NAVY2, 0.92, 16); d = ImageDraw.Draw(p)
    d.text((q(18), q(14)), 'COMPARISON OF OPTIONS  –  factual figures, no weighting, no ranking', font=F(24, 'b'), fill=GOLD)
    y0 = q(56); d.rectangle((q(12), y0, q(tw_ - 12), y0 + q(rh)), fill=(200, 30, 30)); x = q(12)
    for i, (c, w_) in enumerate(COLS):
        d.text((x + (q(10) if i == 0 else q(w_) - q(8)), y0 + q(rh / 2)), c, font=F(17, 'b'), fill=WHITE, anchor='lm' if i == 0 else 'rm'); x += q(w_)
    for r, k in enumerate(ORDER[:nrows]):
        m = MT[k]; p_ = POL[k]; y = y0 + q(rh) * (r + 1)
        d.rectangle((q(12), y, q(tw_ - 12), y + q(rh)), fill=(18, 38, 84) if r % 2 == 0 else (12, 28, 66))
        vals = [k, f"{m['new_const_m'] / 1000:.2f}", f"{m['max_grade_pct']:.1f}", f"{m['pct_gt_1in10']:.0f}%", f"{m['pct_gt_1in7']:.0f}%", f"{m['pct_gt_1in5']:.0f}%", f"{m['hairpins']}",
                f"{m['nala_xings']}", f"{p_['cut_total']:,.0f}", f"{m['expo_dominating_pct']:.0f} / {m['expo_plain_road_pct']:.0f}%", f"{p_['total']:,}", f"{p_['dur']}"]
        x = q(12)
        for i, (v, (c, w_)) in enumerate(zip(vals, COLS)):
            if i == 0: d.rectangle((x + q(10), y + q(14), x + q(26), y + q(30)), fill=COL[k]); d.text((x + q(34), y + q(rh / 2)), v, font=F(20, 'b'), fill=COL[k], anchor='lm')
            else: d.text((x + q(w_) - q(8), y + q(rh / 2)), v, font=F(19, 'b'), fill=WHITE, anchor='rm')
            x += q(w_)
    return p
def shot8(t):
    D = DUR['compare']; base, mpp = plan_base(); z = 1 + 0.03 * sm(t / D)
    arr = np.asarray(base.convert('RGB')).astype(np.float32) / 255; M = cv2.getRotationMatrix2D((W * 0.5, H * 0.5), 0, z); arr = cv2.warpAffine(arr, M, (W, H))
    dim = seg(t, 5.0, 6.0); arr = arr * (1 - 0.35 * dim)
    b = to_pil(arr)
    tb = cmp_table(min(5, max(0, int((t - 5.6) / 0.45) + 1)) if t > 5.6 else 0); put(b, tb, (W - tb.size[0]) / 2, H - tb.size[1] - q(200), seg(t, 5.2, 5.8))
    put(b, text_panel('KEY', ['New km: new const incl KMZ new tr portion  ·  Max %: steepest 50 m  ·  >1:x: share of length steeper', 'Expo: share of length seen from assumed OPs (Taloband crests / W–NW low gnd)',
                              ('Cut, POL, days: 30 m DEM, ±50 % (assessed)  ·  Days: 1 Dozer + 1 Excavator  ·  Confirm all alns by gr recce', GOLD)], w=1150, fs=18, lh=26),
        (W - q(1150)) / 2, H - q(196), seg(t, 8.0, 8.8))
    L_ = 200 / (mpp / z); d = ImageDraw.Draw(b); x, y = W - q(60) - L_, q(130); d.rectangle((x, y, x + L_, y + q(8)), fill=WHITE); d.rectangle((x + L_ / 2, y, x + L_, y + q(8)), fill=(20, 20, 20), outline=WHITE)
    d.text((x, y + q(12)), '0', font=F(17, 'b'), fill=WHITE); d.text((x + L_, y + q(12)), '200 m', font=F(17, 'b'), fill=WHITE, anchor='ra')
    U.section(b, 'COMPARISON OF OPTIONS', o=seg(t, 0.3, 1.0), sub='Plan  ·  five alignments from the KMZ tr to the post')
    U.topbar(b, TITLE); U.compass(b, 0); U.footer(b, FOOT); return b

# ---------------------------------------------------------------- options for decision (no recommendation)
def shot9(t):
    D = DUR['close']; base, _ = plan_base(); arr = cv2.GaussianBlur(np.asarray(base.convert('RGB')).astype(np.float32) / 255, (0, 0), 26) * 0.45
    fade = 1 - seg(t, D - 1.6, D); b = to_pil(arr * fade); a = seg(t, 0.2, 1.0) * fade
    def hdr(L):
        dd = ImageDraw.Draw(L); dd.text((W / 2, q(120)), 'OPTIONS FOR DECISION', font=F(54, 'b'), fill=WHITE, anchor='ma')
        dd.text((W / 2, q(185)), f'Khabri-1 hill post (RL {RL_POST} m)  ·  five alignments  ·  in no order of preference', font=F(24, 'i'), fill=(225, 230, 240), anchor='ma')
    L = Image.new('RGBA', b.size, (0, 0, 0, 0)); hdr(L); b.alpha_composite(U.opacity(L, a))
    cw = (1920 - 200) / 5
    for i, k in enumerate(ORDER):
        m = MT[k]; p_ = POL[k]
        rows = [('New const', f"{m['new_const_m'] / 1000:.2f} km"), ('Max grade', f"{m['max_grade_pct']:.1f} %"), ('> 1:10', f"{m['pct_gt_1in10']:.0f} %"), ('> 1:5', f"{m['pct_gt_1in5']:.0f} %"),
                ('Hairpins', f"{m['hairpins']}"), ('Nala xings', f"{m['nala_xings']}"), ('Cut', f"{p_['cut_total']:,.0f} cu M"), ('Expo crest', f"{m['expo_dominating_pct']:.0f} %"),
                ('Expo low gnd', f"{m['expo_plain_road_pct']:.0f} %"), ('POL', f"{p_['total']:,} lits", GOLD), ('Work days', f"{p_['dur']}", GOLD)]
        p = table_panel(f'{k}  –  {DESC[k]}', rows, w=cw - 16, accent=COL[k], lh=36, fs=18, title_col=COL[k])
        put(b, p, q(100 + i * cw + 8), q(250), seg(t, 0.4 + i * 0.25, 1.1 + i * 0.25) * fade)
    put(b, text_panel('COMMON TO ALL OPTIONS', [(f"Post pad 40' × 40' on the crest: {PAD['cut']:,.0f} cu M cut / {PAD['fill']:,.0f} cu M fill  ·  POL {PAD['total']:,} lits  ·  {PAD['days']} work day  (+{PAD['contingency']['l']:,} lits jack hammer contingency)", WHITE, 'b'),
                                                ('All alignments are least-cost corridors on a 30 m DEM  ·  figures assessed  ·  confirm by gr recce before pegging', GOLD, 'b')], w=1500, fs=20, lh=30),
        (W - q(1500)) / 2, H - q(220), seg(t, 2.0, 2.8) * fade)
    U.topbar(b, TITLE); return b

# ---------------------------------------------------------------- timeline (VO-driven)
SEQ = [('open', shot1), ('orient', shot2), ('air', shot3), ('slope', shot4), ('section', shot5), ('climb', climb), ('align', shot6), ('postair', shot6b)] + \
      [(k, fly(k)) for k in ORDER] + [('top1', top1), ('top2', top2), ('compare', shot8), ('close', shot9)]
VO_OFF = {'open': 1.4, 'align': 0.9, **{k: 0.9 for k in ORDER}}
SHOTS = []; T_ = 0.0
for key, fn in SEQ: SHOTS.append((round(T_, 3), round(T_ + DUR[key], 3), fn, key)); T_ += DUR[key]
TOTAL = T_
TL = dict(total=TOTAL, shots=[dict(key=k, t0=a, t1=b_, vo=(a + VO_OFF.get(k, 0.6)) if k in VOD else None, vo_dur=VOD.get(k)) for a, b_, _, k in SHOTS])
XF = 0.5
def frame(T):
    for i, (a, b_, fn, key) in enumerate(SHOTS):
        if a <= T < b_:
            im = fn(T - a)
            if i > 0 and T - a < XF:
                pa, pb, pf, _ = SHOTS[i - 1]; prev = pf(T - pa); return Image.blend(prev.convert('RGB'), im.convert('RGB'), float(sm((T - a) / XF)))
            return im.convert('RGB')
    return Image.new('RGB', (W, H))

if args.timeline:
    json.dump(TL, open(f'{R}/work/timeline_v4.json', 'w'), indent=1)
    for s_ in TL['shots']: print(f"{s_['key']:8s} {s_['t0']:7.2f} {s_['t1']:7.2f}  vo@{s_['vo']}")
    print('TOTAL', round(TOTAL, 2), 'frames', int(round(TOTAL * FPS))); sys.exit()
if args.stills:
    for T in [float(x) for x in args.stills.split(',')]:
        t_ = time.time(); frame(T).resize((1920, 1080), Image.LANCZOS).save(f'{args.out}_{T:06.2f}.jpg', quality=90); print('still', T, round(time.time() - t_, 1), 's', flush=True)
    sys.exit()
f0, f1 = int(round(args.t0 * FPS)), int(round(min(args.t1, TOTAL) * FPS))
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '10',
                        '-pix_fmt', 'yuv420p', args.out], stdin=subprocess.PIPE)
t_ = time.time()
for f in range(f0, f1):
    enc.stdin.write(np.asarray(frame(f / FPS)).tobytes())
    if f % 30 == 0: print(f'frame {f} {time.time() - t_:.0f}s', flush=True)
enc.stdin.close(); enc.wait(); print('done', args.out, flush=True)
