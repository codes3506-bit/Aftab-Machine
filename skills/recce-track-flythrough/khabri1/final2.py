"""Khabri-1 hill post - TRACK OPTIONS film v3 (B3-Haryaan look). 2:52, 2560x1440 native, 30 fps -> 1440p + 1080p.
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

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--t0', type=float, default=0); ap.add_argument('--t1', type=float, default=172)
ap.add_argument('--stills', default=''); ap.add_argument('--post', default=''); args = ap.parse_args()
FPS = 30; W, H = 2560, 1440; U.init(W, H); s = W / 1920
WA = '/root/.claude/uploads/d35c83c0-ed16-5ab8-ac1e-72068dbafa01/cf77cbb6-WhatsApp_Video_2026-11-25_at_10.26.14.mp4'
PH = '/tmp/claude-0/-home-user-Aftab-Machine/d35c83c0-ed16-5ab8-ac1e-72068dbafa01/images'
MT = {t['name']: t for t in json.load(open(f'{R}/work/metrics.json'))['tracks']}; PR = json.load(open(f'{R}/work/profiles.json')); POL = json.load(open(f'{R}/work/pol.json'))
ORDER = ['T1', 'T2', 'T3', 'T4', 'T5']
DESC = {'T1': 'Direct climb – S spur', 'T2': 'Graded S spur', 'T3': 'W spur / ridge', 'T4': 'E flank', 'T5': 'Rear / N foothill'}
LONG = {'T1': 'Climbs straight up the S spur from the saddle', 'T2': 'Zig-zags up the S spur at a ruling 1:7',
        'T3': 'Leaves the KMZ new tr W, climbs the W spur along the ridge', 'T4': 'Leaves the take-off NE, climbs the E flank, arrives along the crest neck',
        'T5': 'Skirts the mount to the rear, runs N along the foothill, climbs from the N'}
TITLE = 'TRACK RECCE - KHABRI-1 HILL POST - OPTIONS'
FOOT = 'Imagery © Esri, Maxar (World Imagery Wayback, 15 Aug 2024)  ·  Terrain: Copernicus GLO-30 DEM  ·  Vertical exaggeration ×1.5  ·  Alignments: least-cost study – confirm by gr recce'
RL_POST = 133; GRID = '25°25′38.6″N  63°26′23.2″E'                                   # user input

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
cap = cv2.VideoCapture(WA)
def drone(tsrc):
    cap.set(cv2.CAP_PROP_POS_MSEC, tsrc * 1000); ok, fr = cap.read()
    fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)[0:398, 70:778]                     # 16:9, clear of the player bar and the source's OS watermark
    up = cv2.resize(fr, (W, H), interpolation=cv2.INTER_LANCZOS4).astype(np.float32) / 255
    bl = cv2.GaussianBlur(up, (0, 0), 2.2); up = np.clip(up + 0.5 * (up - bl), 0, 1)
    return grade(up, 0.5)
def drone_shot(src0, t, zoom=0.06, dur=8):
    img = drone(src0 + t); z = 1 + zoom * sm(t / dur); M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z); return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR)
def drone_chip(b, txt, o=1.0):
    f = F(19, 'b'); w = U.tw(txt, f) + q(30); p = panel_img(w, q(36), NAVY2, 0.88, 8, GOLD, 1.5); ImageDraw.Draw(p).text((q(15), q(7)), txt, font=f, fill=YEL)
    put(b, p, q(24), H - q(96), o)

# ---------------------------------------------------------------- 0-9 cold open: drone + B3 title card
def shot1(t):
    b = to_pil(drone_shot(0.5, t, 0.07, 9) * seg(t, 0, 1.0))
    U.title_big(b, 'TRACK RECCE - KHABRI-1 HILL POST', 'Five alignments to the post  ·  options for decision', win(t, 2.2, 8.4, 0.9, 0.8), t - 2.2)
    drone_chip(b, 'DRONE 00:00 – 00:09  ·  Taloband Rg  ·  view assessed (no telemetry)', seg(t, 1.0, 1.8))
    return b

# ---------------------------------------------------------------- 9-21 establishing orbit + area orientation
K2 = [rel(300, -2300, 520), rel(-500, -2350, 760), rel(-1100, -2150, 900), rel(-1500, -1550, 880)]
T2_ = [rel(0, 400, 160), rel(60, 280, pz - 40), rel(130, 230, pz - 60), rel(140, 200, pz - 60)]
def shot2(t):
    u = seg(t, 0, 12); eye, tgt = catmull(K2, u), catmull(T2_, u); img = render3d(eye, tgt, 40)
    items = []
    if t > 5.5:
        for P in KMZ3:
            fr = seg(t, 5.5, 9.5); n = max(2, int(len(P) * fr)); xy, v = vis(P[:n]); items.append(dict(xy=xy, vis=v, col=COL['KMZ'], w=3.0, glow=0.5, ghost=False, pulse=fr if fr < 1 else None))
    b = to_pil(glow(img, items) if items else img)
    post_label(b, lift=90, o=seg(t, 2.0, 2.8))
    xy2, ok2 = point_xy(*TAKEOFF_EN)
    if ok2: label(b, xy2, f'T4 take-off  CH {TAKEOFF_CH:.2f}', 'km', lift=50, o=seg(t, 9.3, 10))
    rows = [('Post', 'Khabri-1 hill post'), ('RL (given)', f'{RL_POST} m'), ('Grid', GRID), ('Range', 'Taloband Rg'),
            ('KMZ tr (existing / planned)', f'{KMZ_KM:.2f} km', (205, 210, 220)), ('Options studied', '5 x alns'), ('Post face slopes S / N', f'{FACE_S:.0f}° / {FACE_N:.0f}°')]
    put(b, table_panel('AREA ORIENTATION', rows, w=470, sub='Desk study on imagery, DEM, drone and gr recce photos'), q(30), H - q(330), seg(t, 1.0, 1.8))
    chrome(b, eye=eye, tgt=tgt); return b

# ---------------------------------------------------------------- 21-29 drone: the ground from the air
def shot3(t):
    b = to_pil(drone_shot(26.0, t, 0.06, 8))
    put(b, text_panel('FROM THE AIR – DRONE', ['Taloband Rg and its badlands foothills', 'Shadi K Nadi beyond (user annotation)', 'Eroded shale spurs, deep gullies',
                                               'Bedding exposed on the faces', ('No telemetry – view assessed', GREY, 'i')], w=470), q(30), q(110), seg(t, 0.6, 1.4))
    drone_chip(b, 'DRONE 00:26 – 00:34', seg(t, 0.3, 1.0)); U.topbar(b, TITLE); return b

# ---------------------------------------------------------------- 29-39 slope + drainage
K3 = [rel(900, -1450, 640), rel(400, -1600, 610), rel(-150, -1550, 600)]; T3_ = [rel(-150, 200, pz - 60), rel(-50, 230, pz - 60), rel(0, 250, pz - 60)]
def cam3(t): u = seg(t, 0, 10); return catmull(K3, u), catmull(T3_, u)
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
        eye, tgt = cam3(10); SECT['bg'] = cv2.GaussianBlur(render3d(eye, tgt, 40), (0, 0), 20) * 0.5
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
        if t >= a: fr = seg(t, a, b_); items.append(track_item(k, max(fr, 0.01), w=4.6, glow=1.0 if t < b_ + 0.5 else 0.8, pulse=fr if fr < 1 else ((t - b_) * 0.25) % 1))
    b = to_pil(glow(img, items)); post_label(b, 80)
    for k in ORDER:
        if t >= DRAW[k][1]:
            P, _ = TR[k]; i = int(0.35 * len(P)); xy2, v2 = vis(P[i:i + 1])
            if v2[0]: label(b, xy2[0], k, col=COL[k], lift=TAGOFF[k], o=seg(t, DRAW[k][1], DRAW[k][1] + 0.5))
    upto = max([ORDER.index(k) for k in ORDER if t >= DRAW[k][0]] + [-1]); put(b, legend_al(upto), q(30), H - q(300), seg(t, 0.2, 1))
    chrome(b, 'FIVE ALIGNMENTS', 'Least-cost corridors on the terrain model  ·  five distinct approaches', eye=eye, tgt=tgt); return b

# ---------------------------------------------------------------- 63-69 drone: the post from the air
def shot6b(t):
    b = to_pil(drone_shot(62.6, t, 0.05, 6))
    put(b, text_panel('THE POST FROM THE AIR', ['Khabri I on the crest line (user annotation, 01:06)', 'Steep, gullied faces below the post', ('View assessed – no telemetry', GREY, 'i')], w=520),
        q(30), q(110), seg(t, 0.4, 1.2))
    drone_chip(b, 'DRONE 01:02 – 01:08', seg(t, 0.2, 0.9)); U.topbar(b, TITLE); return b

# ---------------------------------------------------------------- 69-154 five options: fly 6 s - STOP 6 s (gr recce) - fly 5 s
SMP = {}
for k in ORDER:
    P, _ = TR[k]; Q = P.copy(); sg = max(8, min(30, len(P) // 12))
    for c in range(3): Q[:, c] = gaussian_filter1d(P[:, c], sg, mode='nearest')
    SMP[k] = Q
FLY, STOP0, STOP1, OPT = 11.0, 6.0, 12.0, 17.0
def ftime(t): return t if t < STOP0 else (STOP0 if t < STOP1 else t - (STOP1 - STOP0))
def cam_fly(k, tf):
    Q = SMP[k]; n = len(Q); u = 0.04 + 0.88 * seg(tf, 0, FLY - 0.4); i = int(u * (n - 1)); c = Q[i]; lk = 60
    a = Q[max(0, i - lk)]; bq = Q[min(n - 1, i + lk)]; fwd = bq[:2] - a[:2]; fwd /= (np.linalg.norm(fwd) + 1e-9); side = np.array([-fwd[1], fwd[0]])
    exy = c[:2] - fwd * 640 + side * 120
    ez = max(c[2] + 470, float(Sc.height(np.array([exy[0]]), np.array([exy[1]]))[0]) + 220)
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
    pr = PR[k]; ss_ = np.array(pr['s']); zz = np.array(pr['z']); gg = np.array(pr['g']) * 100; jch = MT[k]['junction_ch_km']
    def base(tf):
        eye, tgt, u = cam_fly(k, tf); img = render3d(eye, tgt, 44)
        items = kmz_items(0.45) + [track_item(j, w=2.2, glow=0.2, col=tuple(int(c * 0.5) for c in COL[j])) for j in ORDER if j != k] + [track_item(k, w=6, glow=1.4, pulse=u)]
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

# ---------------------------------------------------------------- 154-164 comparison (plan + B3 table, no scores)
PLAN = {}
def plan_base():
    if PLAN: return PLAN['b'], PLAN['mpp']
    ce, cn = pe + 200, pn - 700; eye = (ce, cn - 30, 5200); tgt = (ce, cn, 0)
    img = Sc.render(eye, tgt, fov=34, sun_az=135, sun_el=42, haze=0.2).astype(np.float32); img = grade(img, 0.6) * 0.9
    items = [dict(xy=vis(P)[0], vis=np.ones(len(P), bool), col=COL['KMZ'], w=2.2, glow=0.3, ghost=False) for P in KMZ3]
    items += [dict(xy=vis(TR[k][0])[0], vis=np.ones(len(TR[k][0]), bool), col=COL[k], w=4.5, glow=0.7) for k in ORDER]
    b = to_pil(glow(img, items))
    LIFT = {'T1': 40, 'T2': 60, 'T3': 50, 'T4': 50, 'T5': 45}
    for k in ORDER:
        P = TR[k][0]; xy = vis(P[int(0.55 * len(P)):int(0.55 * len(P)) + 1])[0][0]; label(b, xy, k, col=COL[k], lift=LIFT[k])
    xy0, _ = vis(np.array([[pe, pn, pz]])); label(b, xy0[0], 'POST', 'post', lift=40)
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
    base, mpp = plan_base(); z = 1 + 0.03 * sm(t / 10)
    arr = np.asarray(base.convert('RGB')).astype(np.float32) / 255; M = cv2.getRotationMatrix2D((W * 0.5, H * 0.5), 0, z); arr = cv2.warpAffine(arr, M, (W, H))
    b = to_pil(arr)
    tb = cmp_table(min(5, max(0, int((t - 0.6) / 0.45) + 1)) if t > 0.6 else 0); put(b, tb, (W - tb.size[0]) / 2, H - tb.size[1] - q(190), seg(t, 0.2, 0.8))
    put(b, text_panel('KEY', ['New km: new const incl KMZ new tr portion  ·  Max %: steepest 50 m  ·  >1:x: share of length steeper', 'Expo: share of length seen from assumed OPs (Taloband crests / W–NW low gnd)',
                              ('Cut, POL, days: 30 m DEM, ±50 % (assessed)  ·  Days: 1 Dozer + 1 Excavator  ·  Confirm all alns by gr recce', GOLD)], w=1150, fs=17, lh=24),
        (W - q(1150)) / 2, H - q(178), seg(t, 3.5, 4.3))
    L_ = 500 / (mpp / z); d = ImageDraw.Draw(b); x, y = W - q(300), q(130); d.rectangle((x, y, x + L_, y + q(8)), fill=WHITE); d.rectangle((x + L_ / 2, y, x + L_, y + q(8)), fill=(20, 20, 20), outline=WHITE)
    d.text((x, y + q(12)), '0', font=F(17, 'b'), fill=WHITE); d.text((x + L_, y + q(12)), '500 m', font=F(17, 'b'), fill=WHITE, anchor='ra')
    U.topbar(b, TITLE); U.compass(b, 0); U.footer(b, FOOT); return b

# ---------------------------------------------------------------- 164-172 options for decision (no recommendation)
def shot9(t):
    base, _ = plan_base(); arr = cv2.GaussianBlur(np.asarray(base.convert('RGB')).astype(np.float32) / 255, (0, 0), 26) * 0.45
    fade = 1 - seg(t, 6.6, 8); b = to_pil(arr * fade); a = seg(t, 0.2, 1.0) * fade
    d = ImageDraw.Draw(b)
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
    put(b, text_panel('NOTE', [('All alignments are least-cost corridors on a 30 m DEM · figures assessed · confirm by gr recce before pegging', GOLD, 'b')], w=1300, fs=20),
        (W - q(1300)) / 2, H - q(190), seg(t, 2.0, 2.8) * fade)
    U.topbar(b, TITLE); return b

SHOTS = [(0, 9, shot1), (9, 21, shot2), (21, 29, shot3), (29, 39, shot4), (39, 49, shot5), (49, 63, shot6), (63, 69, shot6b)] + \
        [(69 + OPT * i, 69 + OPT * (i + 1), fly(k)) for i, k in enumerate(ORDER)] + [(154, 164, shot8), (164, 172, shot9)]
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
if args.post:
    # finishing pass over the full-length render: re-render the drone / title shots (logos + watermark-free crop),
    # stamp the unit logos onto the top bar of every other frame
    REDO = [(0, 9.5), (21, 29.5), (39, 49.5), (63, 69.5)]
    lg = U.logos(q(68)); dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', args.post, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '12',
                            '-pix_fmt', 'yuv420p', args.out], stdin=subprocess.PIPE)
    f = 0; t_ = time.time()
    while True:
        raw = dec.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: break
        T = f / FPS
        if any(a <= T < b for a, b in REDO): im = frame(T)
        else:
            im = Image.frombytes('RGB', (W, H), raw).convert('RGBA'); im.alpha_composite(lg[0], (q(16), q(6))); im.alpha_composite(lg[1], (W - q(16) - q(68), q(6))); im = im.convert('RGB')
        enc.stdin.write(np.asarray(im).tobytes()); f += 1
        if f % 150 == 0: print(f'post {f} {time.time() - t_:.0f}s', flush=True)
    enc.stdin.close(); enc.wait(); print('done post', f, flush=True); sys.exit()
f0, f1 = int(round(args.t0 * FPS)), int(round(args.t1 * FPS))
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '12',
                        '-pix_fmt', 'yuv420p', args.out], stdin=subprocess.PIPE)
t_ = time.time()
for f in range(f0, f1):
    enc.stdin.write(np.asarray(frame(f / FPS)).tobytes())
    if f % 30 == 0: print(f'frame {f} {time.time() - t_:.0f}s', flush=True)
enc.stdin.close(); enc.wait(); print('done', args.out, flush=True)
