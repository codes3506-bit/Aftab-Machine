"""Khabri-1 hill post track recce film - 2:00, 3840x2160, 30 fps.
usage: xvfb-run -a python3 film.py OUT.mp4 --t0 A --t1 B [--stills t1,t2]
All figures are read from work/*.json written by the analysis scripts - nothing typed by hand.
"""
import json, sys, math, argparse, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import map_coordinates, gaussian_filter1d
from engine import *
from overlay import *

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--t0', type=float, default=0); ap.add_argument('--t1', type=float, default=120)
ap.add_argument('--stills', default=''); args = ap.parse_args()
FPS = 30; DUR = 120.0; W, H = 3840, 2160; RW, RH = 2560, 1440; K = W / RW; s = 2.0
WA = '/root/.claude/uploads/d35c83c0-ed16-5ab8-ac1e-72068dbafa01/cf77cbb6-WhatsApp_Video_2026-11-25_at_10.26.14.mp4'
MT = {t['name']: t for t in json.load(open(f'{R}/work/metrics.json'))['tracks']}; PR = json.load(open(f'{R}/work/profiles.json'))
MC = json.load(open(f'{R}/work/mcda.json')); POL = json.load(open(f'{R}/work/pol.json'))
TOT = dict(zip(MC['ids'], MC['total'])); RECOM, ALTN = 'T5', 'T4'
DESC = {'T1': 'Direct climb – S spur', 'T2': 'Graded S spur 1:7', 'T3': 'W spur / ridge', 'T4': 'E flank', 'T5': 'Rear / N foothill'}

# ------------------------------------------------------------------ scene
Sc = Scene(RW, RH)
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
KMZ3 = [track3d(p['pts'], 4.0)[0] for p in kml() if p['kind'] == 'line']

# ------------------------------------------------------------------ helpers
def sm(x): x = np.clip(x, 0, 1); return x * x * x * (x * (6 * x - 15) + 10)          # smootherstep (eased, zero accel at ends)
def seg(t, a, b): return float(sm((t - a) / (b - a)))
def catmull(P, u):
    """centripetal Catmull-Rom through key points P (n,3) at u in [0,1]"""
    P = np.asarray(P, float); n = len(P)
    if n == 2: return P[0] + (P[1] - P[0]) * u
    Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]]); f = u * (n - 1); i = min(int(f), n - 2); t = f - i
    p0, p1, p2, p3 = Q[i], Q[i + 1], Q[i + 2], Q[i + 3]
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
def rel(dx, dy, z): return (pe + dx, pn + dy, z)
def heading(eye, tgt): return float(np.degrees(np.arctan2(tgt[0] - eye[0], tgt[1] - eye[1])))
def vis(P):
    x, y, v = Sc.visible(P); return np.c_[x * K, y * K], v
def track_item(k, frac=1.0, w=4.2, glow=0.8, pulse=None, col=None):
    P, _ = TR[k]; n = max(2, int(frac * len(P))); xy, v = vis(P[:n])
    return dict(xy=xy, vis=v, col=col or COL[k], w=w, glow=glow, pulse=pulse)
def kmz_items(alpha=1.0):
    out = []
    for P in KMZ3:
        xy, v = vis(P); out.append(dict(xy=xy, vis=v, col=tuple(int(c * alpha) for c in COL['KMZ']), w=2.5, glow=0.3 * alpha, ghost=False))
    return out
def point_xy(e, n, lift=2.0):
    z = float(Sc.height(np.array([e]), np.array([n]))[0]) + lift; xy, v = vis(np.array([[e, n, z]])); return xy[0], bool(v[0])
def layer_alpha(base, fn, a):
    if a <= 0: return
    L = Image.new('RGBA', base.size, (0, 0, 0, 0)); fn(L)
    if a < 1: L.putalpha(L.getchannel('A').point(lambda v: int(v * a)))
    base.alpha_composite(L)
def render3d(eye, tgt, fov, **kw):
    img = Sc.render(eye, tgt, fov=fov, sun_az=115, sun_el=kw.pop('sun_el', 22), **kw)
    return grade(cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC))
def glow(img, items): return glow_tracks(img, items, s)
def chip(base, xy, txt, sub=None):
    d = ImageDraw.Draw(base); f = F(30 * s, 'Bold'); f2 = F(22 * s, 'Medium'); w = max(d.textlength(txt, font=f), d.textlength(sub, font=f2) if sub else 0) + 40 * s
    x, y = xy; h = (56 if not sub else 92) * s
    d.rounded_rectangle((x, y, x + w, y + h), radius=int(10 * s), fill=PANEL + (225,), outline=GOLD + (255,), width=int(2 * s))
    d.text((x + 20 * s, y + 12 * s), txt, font=f, fill=(255, 255, 255))
    if sub: d.text((x + 20 * s, y + 54 * s), sub, font=f2, fill=GOLD)
def scale_bar(base, m_per_px, xy=(70, 2000)):
    L = 500 / m_per_px; x, y = xy[0] * s / 2 * 2, xy[1]; d = ImageDraw.Draw(base)
    d.rectangle((x, y, x + L, y + 10 * s), fill=(255, 255, 255)); d.rectangle((x + L / 2, y, x + L, y + 10 * s), fill=(20, 20, 20), outline=(255, 255, 255))
    text(base, (x, y - 40 * s), '0', F(22 * s, 'SemiBold'), sc=s); text(base, (x + L, y - 40 * s), '500 m', F(22 * s, 'SemiBold'), anchor='ra', sc=s)

# drone reader (848x480 -> letterboxed 2.39:1 insert, clean of player bar)
cap = cv2.VideoCapture(WA)
def drone(tsrc, full=True):
    cap.set(cv2.CAP_PROP_POS_MSEC, tsrc * 1000); ok, fr = cap.read()
    fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)[20:375]            # 848x355 = 2.39:1, above the player bar
    up = cv2.resize(fr, (W, int(W / 848 * 355)), interpolation=cv2.INTER_LANCZOS4).astype(np.float32) / 255
    bl = cv2.GaussianBlur(up, (0, 0), 3); up = np.clip(up + 0.6 * (up - bl), 0, 1)       # unsharp
    rng = np.random.default_rng(int(tsrc * 30)); up = np.clip(up + rng.normal(0, 0.012, up.shape[:2])[..., None], 0, 1)   # fine grain (deterministic)
    up = grade(up, 0.7)
    if not full: return up
    out = np.zeros((H, W, 3), np.float32); y0 = (H - up.shape[0]) // 2; out[y0:y0 + up.shape[0]] = up; return out

# ------------------------------------------------------------------ shots
def shot1(t):            # 0-10 cold open: drone 00:37 -> 00:47, slow push-in
    img = drone(37 + t); z = 1 + 0.08 * sm(t / 10); M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
    img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR); img *= seg(t, 0, 1.2)
    b = to_pil(img)
    def ttl(L):
        d = ImageDraw.Draw(L); d.text((W / 2, H / 2 - 70 * s), 'TRACK RECCE', font=F(30 * s, 'SemiBold'), fill=GOLD, anchor='mm')
        d.text((W / 2, H / 2), 'KHABRI-1 HILL POST', font=F(84 * s, 'Bold', True), fill=(255, 255, 255), anchor='mm')
        d.text((W / 2, H / 2 + 74 * s), 'Selecting the alignment to the post', font=F(30 * s, 'Medium'), fill=(225, 228, 235), anchor='mm')
    layer_alpha(b, ttl, seg(t, 3.5, 5) * (1 - seg(t, 8.6, 9.6)))
    layer_alpha(b, lambda L: chip(L, (70 * s, H - 300 * s), f'DRONE 00:{37 + int(t):02d}', 'Taloband Rg S face · looking N · ASSESSED'), seg(t, 1, 2))
    return b

K2 = [rel(250, -2550, 380), rel(-700, -2650, 720), rel(-1450, -2400, 980), rel(-1850, -1750, 960)]
T2 = [rel(0, 450, 140), rel(60, 300, pz - 30), rel(140, 250, pz - 55), rel(150, 200, pz - 60)]
def cam2(t): u = seg(t, 0, 15); return catmull(K2, u), catmull(T2, u)
def shot2(t):            # 10-25 orbit establishing, pin, AOI, KMZ track
    eye, tgt = cam2(t); img = render3d(eye, tgt, 36)
    km_a = seg(t, 8, 9); items = []
    if t > 8:
        for P in KMZ3:
            n = max(2, int(len(P) * seg(t, 8, 13))); xy, v = vis(P[:n]); items.append(dict(xy=xy, vis=v, col=COL['KMZ'], w=2.8, glow=0.4, ghost=False, pulse=seg(t, 8, 13) if t < 13 else None))
    img = glow(img, items) if items else img
    b = to_pil(img)
    if t > 5:   # AOI outline 2.2 x 1.6 km around post draws on
        a = seg(t, 5, 8); box = [(-1300, -1000), (1100, -1000), (1100, 900), (-1300, 900), (-1300, -1000)]
        pts = []
        for (x0, y0), (x1, y1) in zip(box[:-1], box[1:]):
            for q in np.linspace(0, 1, 60): pts.append((pe + x0 + (x1 - x0) * q, pn + y0 + (y1 - y0) * q))
        pts = np.array(pts[:max(2, int(len(pts) * a))]); z = Sc.height(pts[:, 0], pts[:, 1]) + 3; xy, v = vis(np.c_[pts, z])
        d = ImageDraw.Draw(b)
        for i in range(len(xy) - 1):
            if v[i] and v[i + 1]: d.line((*xy[i], *xy[i + 1]), fill=(255, 255, 255, 170), width=int(2 * s))
        if a > 0.9: xy0, ok = point_xy(pe - 1300, pn + 900); ok and text(b, (xy0[0] + 12 * s, xy0[1] - 40 * s), 'AOI', F(24 * s, 'Bold'), sc=s)
    xy, ok = point_xy(pe, pn)
    layer_alpha(b, lambda L: pin(L, xy, 'KHABRI-1 HILL POST', 'RL 133 m  ·  25°25\'38.6"N 63°26\'23.2"E', s=s, up=150 * seg(t, 3, 4.2) + 1), seg(t, 3, 3.8))
    if t > 8.5:
        xy2, ok2 = point_xy(*en(63.43863, 25.42365)); ok2 and layer_alpha(b, lambda L: tag(L, xy2, 'Take-off Ch 3.92', COL['KMZ'], s, 160, 40), seg(t, 12, 13))
    title_bar(b, 'KHABRI-1 HILL POST', 'Taloband Rg · above the Shadi Kaur · Cop GLO-30 terrain, VE 1.0', s) if t > 1 else None
    north_arrow(b, (W - 110 * s, H - 110 * s), heading(eye, tgt), s)
    return b

K3 = [rel(950, -1550, 560), rel(450, -1750, 520), rel(-150, -1700, 500)]; T3 = [rel(-150, 200, pz - 50), rel(-50, 230, pz - 50), rel(0, 250, pz - 50)]
def cam3(t): u = seg(t, 0, 12); return catmull(K3, u), catmull(T3, u)
def shot3(t):            # 25-37 slope + drainage
    eye, tgt = cam3(t); img = render3d(eye, tgt, 40, slope_mix=seg(t, 0.5, 3), drain_mix=seg(t, 3.5, 6), sun_el=24)
    img = glow(img, kmz_items(0.6)); b = to_pil(img)
    xy, ok = point_xy(pe, pn); pin(b, xy, 'HILL POST', 'RL 133', s=s, up=110)
    title_bar(b, 'TERRAIN · SLOPE & DRAINAGE', 'Slope from Cop GLO-30 · D8 flow lines > 2 ha', s)
    def legend(L):
        panel(L, (60 * s, H - 330 * s, 620 * s, H - 60 * s), 'SLOPE (deg)', s=s, blur=False)
        ramp = np.array([[26, 153, 77], [253, 224, 102], [245, 110, 66], [166, 0, 38]], float); bar = np.zeros((int(28 * s), int(480 * s), 4), np.uint8); bar[..., 3] = 255
        for i in range(bar.shape[1]):
            q = i / bar.shape[1] * 3; k = min(int(q), 2); bar[:, i, :3] = ramp[k] + (ramp[k + 1] - ramp[k]) * (q - k)
        L.alpha_composite(Image.fromarray(bar, 'RGBA'), (int(90 * s), int(H - 245 * s)))
        for i, lab in enumerate(['0', '10', '20', '30', '40+']): text(L, (90 * s + i * 120 * s, H - 205 * s), lab, F(22 * s, 'Medium'), anchor='ma', sc=s)
        d = ImageDraw.Draw(L); d.line((90 * s, H - 135 * s, 150 * s, H - 135 * s), fill=(64, 191, 255), width=int(6 * s)); text(L, (165 * s, H - 150 * s), 'Drainage line / nala', F(24 * s, 'Medium'), sc=s)
    layer_alpha(b, legend, seg(t, 1, 2))
    xs, oks = point_xy(pe - 60, pn - 260); xn, okn = point_xy(pe + 40, pn + 230)
    layer_alpha(b, lambda L: tag(L, xs, 'S FACE ≈ 21°  (scarp)', (255, 130, 90), s, 380, -40), seg(t, 6.5, 7.3))
    layer_alpha(b, lambda L: tag(L, xn, 'N SIDE ≈ 8°  · strike hollow', (120, 220, 255), s, 260, -120), seg(t, 7.5, 8.3))
    north_arrow(b, (W - 110 * s, H - 110 * s), heading(eye, tgt), s)
    return b

SECT = None
def shot4(t):            # 37-50 strata: animated DEM section + drone 00:58-01:10
    global SECT
    if SECT is None:
        eye, tgt = cam3(12); bg = render3d(eye, tgt, 40, slope_mix=0.0); SECT = cv2.GaussianBlur(bg, (0, 0), 25) * 0.45
        d_ = np.arange(-450, 451, 5); a = 0.0; SECT_P = dem(*ll(pe + d_ * np.sin(a), pn + d_ * np.cos(a))); globals()['SECT_D'] = (d_, SECT_P)
    img = SECT.copy()
    dr = drone(58 + t * 12 / 13, full=False); hh, ww = dr.shape[:2]; sc_ = 0.46; dr = cv2.resize(dr, (int(ww * sc_), int(hh * sc_)), interpolation=cv2.INTER_AREA)
    x0, y0 = W - dr.shape[1] - 120, 330; a = seg(t, 0.3, 1.2); img[y0:y0 + dr.shape[0], int(x0):int(x0) + dr.shape[1]] = img[y0:y0 + dr.shape[0], int(x0):int(x0) + dr.shape[1]] * (1 - a) + dr * a
    b = to_pil(img); title_bar(b, 'STRATA · ASSESSED', 'DEM cross-section through the post  ·  drone footage of the same ridge', s)
    # section graph
    d_, z_ = SECT_D; gx, gy, gw, gh = 260, 560, 1480, 1260
    panel(b, (gx - 160, gy - 260, gx + gw + 80, gy + gh + 170), 'N–S SECTION THROUGH THE POST', s=s, blur=False)
    dd = ImageDraw.Draw(b); n = max(2, int(len(d_) * seg(t, 0.5, 4)))
    X = gx + (d_ + 450) / 900 * gw; Y = gy + gh - (z_ - 20) / 150 * gh
    poly = [(X[0], gy + gh)] + list(zip(X[:n], Y[:n])) + [(X[n - 1], gy + gh)]
    dd.polygon(poly, fill=(150, 125, 95, 255))
    for k in range(1, 7):   # schematic bedding lines (gently dipping, assessed) clipped under the ground surface
        zl = 30 + k * 18
        for i in range(n - 1):
            if zl < z_[i]: dd.line((X[i], gy + gh - (zl - 20 + 0.004 * d_[i]) / 150 * gh, X[i + 1], gy + gh - (zl - 20 + 0.004 * d_[i + 1]) / 150 * gh), fill=(110, 90, 68, 255), width=3)
    dd.line(list(zip(X[:n], Y[:n])), fill=GOLD, width=8)
    for zl in (40, 80, 120, 160): yl = gy + gh - (zl - 20) / 150 * gh; dd.line((gx, yl, gx + gw, yl), fill=(255, 255, 255, 50), width=2); dd.text((gx - 14, yl), f'{zl} m', font=F(22 * s), fill=(180, 186, 198), anchor='rm')
    text(b, (gx, gy + gh + 20), 'S', F(34 * s, 'Bold'), sc=s); text(b, (gx + gw, gy + gh + 20), 'N', F(34 * s, 'Bold'), anchor='ra', sc=s)
    xp = gx + gw / 2; dd.line((xp, gy, xp, gy + gh), fill=(255, 255, 255, 140), width=3); text(b, (xp + 16, gy + 10), 'POST', F(26 * s, 'Bold'), anchor='la', sc=s)
    layer_alpha(b, lambda L: tag(L, (gx + gw * 0.3, gy + gh * 0.55), 'Steep S face ≈ 21° – scarp', (255, 130, 90), s, -60, -160), seg(t, 4, 4.8))
    layer_alpha(b, lambda L: tag(L, (gx + gw * 0.72, gy + gh * 0.42), 'N side · strike hollow', (120, 220, 255), s, 60, -170), seg(t, 5, 5.8))
    text(b, (x0, y0 + dr.shape[0] + 20), 'DRONE 00:58–01:10 · post ridge, S face · ASSESSED', F(24 * s, 'Bold'), fill=GOLD, sc=s)
    def notes(L):
        panel(L, (x0 - 20, y0 + dr.shape[0] + 110, W - 100, y0 + dr.shape[0] + 680), 'READING THE STRATA', s=s, blur=False)
        for i, ln in enumerate(['Bedding strikes ENE–WSW along the ridge', 'Bedding crops out on BOTH faces:', '   S face – drone 01:03  ·  N side – recce oblique',
                                '→ beds gently dipping / near-horizontal', 'No dip-slope (planar slide) face identified', 'ASSESSED – confirm dip on the ground']):
            text(L, (x0 + 30, y0 + dr.shape[0] + 230 + i * 66), ln, F(25 * s, 'Medium' if i != 5 else 'Bold'), fill=(255, 170, 120) if i == 5 else (235, 238, 245), sc=s)
    layer_alpha(b, notes, seg(t, 6, 7))
    return b

K5_AZ = (212, 252); K5_R = (2600, 2050); K5_Z = (1050, 820)
ORDER = ['T1', 'T2', 'T3', 'T4', 'T5']; DRAW = {k: (0.5 + 4 * i, 3.8 + 4 * i) for i, k in enumerate(ORDER)}
def cam5(t):
    u = seg(t, 0, 25); az = math.radians(K5_AZ[0] + (K5_AZ[1] - K5_AZ[0]) * u); r = K5_R[0] + (K5_R[1] - K5_R[0]) * u
    return (pe + r * math.sin(az), pn + r * math.cos(az), K5_Z[0] + (K5_Z[1] - K5_Z[0]) * u), (pe + 120, pn + 220, pz - 60)
def mini_profile(L, k, box):
    x0, y0, x1, y1 = box; d = ImageDraw.Draw(L); p = PR[k]; S_ = np.array(p['s']); Z_ = np.array(p['z']); mx = 2500
    q = [(x0 + si / mx * (x1 - x0), y1 - (zi - 20) / 140 * (y1 - y0)) for si, zi in zip(S_[::3], Z_[::3])]
    d.line(q, fill=COL[k] + (255,), width=int(4 * s))
    for zl in (40, 80, 120): yl = y1 - (zl - 20) / 140 * (y1 - y0); d.line((x0, yl, x1, yl), fill=(255, 255, 255, 40), width=1); d.text((x0 - 6 * s, yl), str(zl), font=F(16 * s), fill=(170, 178, 192), anchor='rm')
def card(L, k):
    m = MT[k]; x0, y0 = W - 760 * s, 170 * s
    panel(L, (x0, y0, W - 70 * s, y0 + 560 * s), f'{k}  ·  {DESC[k].upper()}', accent=COL[k], s=s, blur=False)
    rows = [('New const', f"{m['new_const_m'] / 1000:.2f} km"), ('Max / mean grade', f"{m['max_grade_pct']:.1f} / {m['mean_grade_pct']:.1f} %"),
            ('Length > 1:10', f"{m['pct_gt_1in10']:.0f} %"), ('Length > 1:5', f"{m['pct_gt_1in5']:.0f} %"), ('Hairpins · nala xings', f"{m['hairpins']} · {m['nala_xings']}")]
    for i, (a, v) in enumerate(rows):
        yy = y0 + 90 * s + i * 52 * s; text(L, (x0 + 30 * s, yy), a, F(24 * s, 'Medium'), fill=(170, 178, 192), sc=s); text(L, (W - 100 * s, yy - 4 * s), v, MONO(30 * s), anchor='ra', sc=s)
    mini_profile(L, k, (x0 + 70 * s, y0 + 370 * s, W - 110 * s, y0 + 530 * s))
def legend5(L, upto):
    panel(L, (60 * s, H - 400 * s, 600 * s, H - 60 * s), 'ALIGNMENTS', s=s, blur=False); d = ImageDraw.Draw(L)
    for i, k in enumerate(ORDER + ['KMZ']):
        if k != 'KMZ' and ORDER.index(k) > upto: continue
        yy = H - 330 * s + i * 42 * s; d.line((90 * s, yy + 12 * s, 140 * s, yy + 12 * s), fill=COL[k], width=int(6 * s))
        d.text((160 * s, yy), (f'{k}  {DESC[k]}' if k != 'KMZ' else 'KMZ tr (existing / planned)'), font=F(24 * s, 'Medium'), fill=(235, 238, 245))
def shot5(t):            # 50-75 five tracks draw on and stay
    eye, tgt = cam5(t); img = render3d(eye, tgt, 36)
    items = kmz_items(0.7); cur = None
    for k in ORDER:
        a, b_ = DRAW[k]
        if t >= a:
            fr = seg(t, a, b_); items.append(track_item(k, max(fr, 0.01), w=5 if t < b_ + 0.4 else 4.2, glow=1.2 if t < b_ + 0.5 else 0.8, pulse=(fr if fr < 1 else ((t - b_) * 0.25) % 1)))
            if a <= t < a + 4: cur = k
    img = glow(img, items); b = to_pil(img)
    xy, ok = point_xy(pe, pn); pin(b, xy, 'HILL POST', 'RL 133', s=s, up=120)
    for k in ORDER:
        if t >= DRAW[k][1]:
            P, _ = TR[k]; i = int(0.35 * len(P)); xy2, v2 = vis(P[i:i + 1])
            if v2[0]: layer_alpha(b, lambda L, k=k, xy2=xy2: tag(L, xy2[0], k, COL[k], s, {'T1': -60, 'T2': -130, 'T3': -60, 'T4': 120, 'T5': -60}[k], -50), seg(t, DRAW[k][1], DRAW[k][1] + 0.5))
    if cur: layer_alpha(b, lambda L: card(L, cur), seg(t, DRAW[cur][0], DRAW[cur][0] + 0.6) * (1 - seg(t, DRAW[cur][0] + 3.5, DRAW[cur][0] + 4)))
    upto = max([ORDER.index(k) for k in ORDER if t >= DRAW[k][0]] + [-1]); layer_alpha(b, lambda L: legend5(L, upto), seg(t, 0.2, 1))
    title_bar(b, 'FIVE ALIGNMENTS', 'Least-cost analysis on the terrain model · each forced to arrive from a different side', s)
    north_arrow(b, (W - 110 * s, H - 110 * s), heading(eye, tgt), s)
    return b

P5, S5 = TR['T5']; P5s = P5.copy(); P5s[:, 0] = gaussian_filter1d(P5[:, 0], 30, mode='nearest'); P5s[:, 1] = gaussian_filter1d(P5[:, 1], 30, mode='nearest')
def cam6(t):
    if t < 16:
        u = seg(t, 0, 16); i = int(u * (len(P5s) - 1)); c = P5s[i]; j = max(0, i - 60); fwd = c[:2] - P5s[j][:2] if i > 5 else P5s[min(60, len(P5s) - 1)][:2] - P5s[0][:2]
        fwd = fwd / (np.linalg.norm(fwd) + 1e-9); back = 300 - 80 * u; up = 190 - 40 * u
        eye = np.array([c[0] - fwd[0] * back - fwd[1] * 60, c[1] - fwd[1] * back + fwd[0] * 60, c[2] + up])
        ahead = P5s[min(len(P5s) - 1, i + 120)]; w_ = seg(t, 9, 15); tgt = ahead * (1 - w_) + np.array([pe, pn, pz]) * w_; tgt[2] -= 20
        return tuple(eye), tuple(tgt), i / (len(P5s) - 1)
    e16, t16, _ = cam6(15.999); u = seg(t, 16, 20); eye = np.array(e16) * (1 - u) + np.array([pe - 450, pn + 650, pz + 520]) * u
    return tuple(eye), (pe, pn, pz), 1.0
def shot6(t):            # 75-95 reveal: chase along T5
    eye, tgt, u = cam6(t); img = render3d(eye, tgt, 44, sun_el=26)
    items = kmz_items(0.45)
    for k in ORDER:
        if k != 'T5': items.append(track_item(k, w=2.2, glow=0.2, col=tuple(int(c * 0.55) for c in COL[k])))
    items.append(track_item('T5', w=6.5, glow=1.7, pulse=u)); img = glow(img, items); b = to_pil(img)
    xy, ok = point_xy(pe, pn); (ok and xy[1] > 420 and 300 < xy[0] < W - 1500) and pin(b, xy, 'KHABRI-1 HILL POST', 'RL 133', s=s, up=70)
    pr = PR['T5']; ss_ = np.array(pr['s']); zz = np.array(pr['z']); gg = np.abs(np.array(pr['g'])) * 100; k = int(u * (len(ss_) - 1)); jch = MT['T5']['junction_ch_km']
    def hud(L):
        panel(L, (W - 720 * s, 170 * s, W - 70 * s, 500 * s), 'T5  ·  LIVE', s=s, blur=False)
        for j, (lab, val) in enumerate([('CH', f'{jch + ss_[k] / 1000:.2f} km'), ('ELEV', f'{zz[k]:.0f} m'), ('GRADE', f'1:{100 / max(gg[k], 0.5):.0f}  ({gg[k]:.1f}%)')]):
            yy = 250 * s + j * 82 * s; text(L, (W - 690 * s, yy), lab, F(26 * s, 'SemiBold'), fill=(170, 178, 192), sc=s); text(L, (W - 100 * s, yy - 6 * s), val, MONO(44 * s), anchor='ra', sc=s)
        px0, py0, pw, ph = 60 * s, H - 420 * s, 900 * s, 330 * s; panel(L, (px0, py0, px0 + pw, py0 + ph), 'ELEVATION PROFILE', s=s, blur=False)
        d = ImageDraw.Draw(L); gx_, gy_, gw, gh = px0 + 60 * s, py0 + 80 * s, pw - 100 * s, ph - 120 * s; mx = max(np.array(p['s'])[-1] for p in PR.values())
        for kk, p in PR.items():
            q = [(gx_ + si / mx * gw, gy_ + gh - (zi - 20) / 140 * gh) for si, zi in zip(p['s'][::4], p['z'][::4])]; d.line(q, fill=COL[kk] + ((255,) if kk == 'T5' else (90,)), width=int((5 if kk == 'T5' else 2) * s))
        for zl in (40, 80, 120): yl = gy_ + gh - (zl - 20) / 140 * gh; d.line((gx_, yl, gx_ + gw, yl), fill=(255, 255, 255, 40), width=1); d.text((gx_ - 8 * s, yl), str(zl), font=F(18 * s), fill=(170, 178, 192), anchor='rm')
        hx = gx_ + ss_[k] / mx * gw; hy = gy_ + gh - (zz[k] - 20) / 140 * gh; d.ellipse((hx - 9 * s, hy - 9 * s, hx + 9 * s, hy + 9 * s), fill=(255, 255, 255))
        d.text((gx_ + gw, py0 + 30 * s), 'm  vs  km from junction', font=F(18 * s), fill=(170, 178, 192), anchor='ra')
    layer_alpha(b, hud, seg(t, 0.3, 1.2) * (1 - seg(t, 17, 18)))
    for a_, b_, msg in [(0.5, 4.5, f"Leaves KMZ new tr at Ch {jch:.2f}"), (4.8, 8.8, 'Runs N along the foothill'), (9, 13, f"{MT['T5']['nala_xings']} nala xings on the foothill – culverts / Irish xings"),
                        (13.2, 16.5, 'Climbs to the post through the N strike hollow')]:
        layer_alpha(b, lambda L, msg=msg: chip(L, (70 * s, 200 * s), msg), seg(t, a_, a_ + 0.5) * (1 - seg(t, b_ - 0.5, b_)))
    title_bar(b, 'THE REAR APPROACH · T5', 'Skirts the mount to the rear, runs N along the foothill, climbs to the post from the N', s)
    north_arrow(b, (W - 110 * s, H - 110 * s), heading(eye, tgt), s)
    return b

PLAN = None
def plan_base():
    global PLAN
    if PLAN is not None: return PLAN
    S2 = Scene(W, H); S2.focus = (pe, pn); S2.set_acc(acc_fn)
    ce, cn = pe + 250, pn - 350; alt = 4200; eye = (ce, cn - 30, alt); tgt = (ce, cn, 0)
    img = S2.render(eye, tgt, fov=34, sun_az=115, sun_el=35, haze=0.2); img = grade(img) * 0.82
    def pv(P): x, y, v = S2.visible(P); return np.c_[x, y], v
    items = []
    for P in KMZ3: xy, v = pv(P); items.append(dict(xy=xy, vis=np.ones(len(xy), bool), col=COL['KMZ'], w=2, glow=0.3, ghost=False))
    for k in ORDER:
        P, _ = TR[k]; xy, v = pv(P); items.append(dict(xy=xy, vis=np.ones(len(xy), bool), col=COL[k], w=6 if k == RECOM else 4, glow=1.4 if k == RECOM else 0.6))
    img = glow_tracks(img, items, s); b = to_pil(img); d = ImageDraw.Draw(b)
    for k in ORDER:   # exposure: per 5 m sample from metrics profiles
        p = PR[k]; a = np.array(p['ll']); e, n = en(a[:, 0], a[:, 1]); z = Sc.height(e, n) + 2; xy, v = pv(np.c_[e, n, z])
        for (x, y), vA, vB in list(zip(xy, p['visA'], p['visB']))[::2]:
            if vA: d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(255, 40, 40, 255))
            elif vB: d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(255, 160, 30, 255))
    xy0, _ = pv(np.array([[pe, pn, pz]])); xy1, _ = pv(np.array([[pe + 500, pn, pz]])); mpp = 500 / abs(xy1[0, 0] - xy0[0, 0])
    PLAN = (b, mpp, (0, 0)); del S2
    return PLAN
def shot7(t):            # 95-112 comparison: plan + exposure + table + radar
    base, mpp, (px, py) = plan_base(); z = 1 + 0.05 * sm(t / 17)
    arr = np.asarray(base.convert('RGB')).astype(np.float32) / 255; M = cv2.getRotationMatrix2D((W * 0.33, H * 0.5), 0, z); arr = cv2.warpAffine(arr, M, (W, H))
    grad = np.clip((np.arange(W) - W * 0.50) / (W * 0.12), 0, 1)[None, :, None] * 0.72; arr = arr * (1 - grad)
    b = to_pil(arr); title_bar(b, 'COMPARISON', 'Plan view, N up · exposure from assumed observation points', s)
    d = ImageDraw.Draw(b); lx, ly = 70 * s, H - 330 * s
    panel(b, (lx - 10 * s, ly - 20 * s, lx + 700 * s, H - 60 * s), 'EXPOSURE (ASSESSED OPs)', s=s, blur=False)
    d.ellipse((lx + 20 * s, ly + 80 * s, lx + 40 * s, ly + 100 * s), fill=(255, 40, 40)); text(b, (lx + 60 * s, ly + 72 * s), 'Seen from dominating crests (Taloband Rg)', F(22 * s, 'Medium'), sc=s)
    d.ellipse((lx + 20 * s, ly + 130 * s, lx + 40 * s, ly + 150 * s), fill=(255, 160, 30)); text(b, (lx + 60 * s, ly + 122 * s), 'Seen from W/NW low ground (plain, Turbat Rd)', F(22 * s, 'Medium'), sc=s)
    north_arrow(b, (W * 0.47, 250 * s), 0, s); scale_bar(b, mpp / z, (70, H - 380 * s))
    # table
    tx, ty = W * 0.53, 190 * s; cols = [('', 360), ('New km', 130), ('Max %', 130), ('>1:10', 120), ('Nala', 100), ('Cut m³', 150), ('Crest', 110), ('Low gnd', 140), ('POL lit', 150), ('Score', 120)]
    CW = 0.58; xx = [tx]; [xx.append(xx[-1] + c[1] * s * CW) for c in cols]
    for i, (c, w_) in enumerate(cols): text(b, (xx[i] + (0 if i == 0 else w_ * s * CW - 10), ty), c, F(17 * s, 'SemiBold'), fill=(170, 178, 192), anchor='la' if i == 0 else 'ra', sc=s)
    for r, k in enumerate(ORDER):
        a = seg(t, 1 + r * 0.8, 1.6 + r * 0.8)
        if a <= 0: continue
        m = MT[k]; vals = [f'{k} {DESC[k]}', f"{m['new_const_m'] / 1000:.2f}", f"{m['max_grade_pct']:.1f}", f"{m['pct_gt_1in10']:.0f}%", f"{m['nala_xings']}", f"{m['cut_m3']:,.0f}",
                           f"{m['expo_dominating_pct']:.0f}%", f"{m['expo_plain_road_pct']:.0f}%", f"{POL[k]['total']:,}", f"{TOT[k]:.2f}"]
        yy = ty + (60 + r * 54) * s
        def row(L, vals=vals, yy=yy, k=k):
            dd = ImageDraw.Draw(L)
            if k == RECOM: dd.rounded_rectangle((tx - 16 * s, yy - 12 * s, xx[-1] + 10 * s, yy + 40 * s), radius=int(8 * s), outline=GOLD + (255,), width=int(3 * s), fill=(245, 183, 0, 30))
            for i, v in enumerate(vals):
                text(L, (xx[i] + (0 if i == 0 else cols[i][1] * s * CW - 10), yy), v, F(18 * s, 'Bold') if i == 0 else MONO(19 * s), fill=COL[k] if i == 0 else (240, 242, 246), anchor='la' if i == 0 else 'ra', sc=s)
        layer_alpha(b, row, a)
    # radar (scores) bottom-right
    def radar(L):
        cx, cy, rr = W * 0.70, 1420, 135 * s; dd0 = ImageDraw.Draw(L); dd0.text((W * 0.53, 1110), 'MCDA SCORES (outer = best)', font=F(20 * s, 'Bold'), fill=GOLD); dd = ImageDraw.Draw(L); crit = MC['criteria']; n = len(crit)
        for q in (0.25, 0.5, 0.75, 1): dd.polygon([(cx + rr * q * math.sin(2 * math.pi * i / n), cy - rr * q * math.cos(2 * math.pi * i / n)) for i in range(n)], outline=(255, 255, 255, 50))
        for i, c in enumerate(crit):
            ax_, ay_ = cx + rr * 1.18 * math.sin(2 * math.pi * i / n), cy - rr * 1.18 * math.cos(2 * math.pi * i / n); dd.text((ax_, ay_), c, font=F(15 * s, 'Medium'), fill=(200, 205, 215), anchor='mm')
        for k in ORDER:
            sc = MC['scores'][MC['ids'].index(k)]; pts = [(cx + rr * max(v, 0.03) * math.sin(2 * math.pi * i / n), cy - rr * max(v, 0.03) * math.cos(2 * math.pi * i / n)) for i, v in enumerate(sc)]
            dd.polygon(pts, outline=COL[k] + (255 if k in (RECOM, ALTN) else 110,), width=int((4 if k in (RECOM, ALTN) else 2) * s))
    layer_alpha(b, radar, seg(t, 5, 6.5))
    def sens(L):
        txt = f"Weights fixed before scoring · ±20 % on each of 8 weights: {', '.join(f'{k} first in {v}/16' for k, v in MC['sens_winners'].items())}"
        panel(L, (W * 0.53 - 16 * s, H - 170 * s, W - 70 * s, H - 50 * s), None, s=s, blur=False); text(L, (W * 0.53, H - 145 * s), txt, F(19 * s, 'SemiBold'), sc=s)
        text(L, (W * 0.53, H - 100 * s), f"Score = weighted MCDA (1 = best on all) · T4 {TOT['T4']:.2f} v T5 {TOT['T5']:.2f}: equal within desk-study accuracy", F(18 * s, 'Medium'), fill=GOLD, sc=s)
    layer_alpha(b, sens, seg(t, 9, 10))
    return b

def shot8(t):            # 112-120 recommendation
    base, _, _ = plan_base(); arr = cv2.GaussianBlur(np.asarray(base.convert('RGB')).astype(np.float32) / 255, (0, 0), 30) * 0.35
    b = to_pil(arr * (1 - seg(t, 6.3, 8))); m = MT[RECOM]; p = POL[RECOM]; a = (1 - seg(t, 6.3, 7.8))
    def crd(L):
        x0, y0, x1, y1 = 230 * s, 120 * s, W - 230 * s, H - 90 * s; panel(L, (x0, y0, x1, y1), None, s=s, blur=False); d = ImageDraw.Draw(L)
        d.text((W / 2, y0 + 60 * s), 'RECOMMENDATION', font=F(28 * s, 'SemiBold'), fill=GOLD, anchor='ma')
        d.text((W / 2, y0 + 110 * s), f'RECOM: {RECOM} (REAR / N FOOTHILL ALN)', font=F(54 * s, 'Bold', True), fill=(255, 255, 255), anchor='ma')
        figs = [('New const', f"{m['new_const_m'] / 1000:.2f} km"), ('Max grade', f"{m['max_grade_pct']:.1f} %"), ('> 1:10 / > 1:5', f"{m['pct_gt_1in10']:.0f} % / {m['pct_gt_1in5']:.0f} %"),
                ('Cut incl KMZ new tr (assessed)', f"{p['cut_total']:,.0f} m³"), ('POL', f"{p['total']:,} lit"), ('Work days', f"{p['dur']}  (1 Dozer + 1 Excavator)"), ('', f"{p['dur_2doz']}  with 2 Dozers")]
        for i, (k_, v) in enumerate(figs):
            yy = y0 + (230 + i * 58) * s; d.text((W / 2 - 30 * s, yy), k_, font=F(28 * s, 'Medium'), fill=(170, 178, 192), anchor='ra'); d.text((W / 2 + 10 * s, yy - 4 * s), v, font=MONO(32 * s), fill=(255, 255, 255))
        lines = [f"Why: gentlest grades for loaded veh in all weather; least cut; lowest exposure to the dominating crests ({m['expo_dominating_pct']:.0f} %)",
                 f"Desk study ranks T4 and T5 equal (score {TOT['T4']:.2f} v {TOT['T5']:.2f}; POL {POL['T4']['total']:,} v {p['total']:,} lit)",
                 f"ALTN: T4 E flank – {MT['T4']['new_const_m'] / 1000:.2f} km, no nala xings, but {MT['T4']['pct_gt_1in10']:.0f} % > 1:10",
                 f"T5 needs protection at {m['nala_xings']} nala xings · Confirm both by gr recce before pegging"]
        for i, ln in enumerate(lines): d.text((W / 2, y0 + (680 + i * 50) * s), ln, font=F(23 * s, 'Medium' if i < 3 else 'Bold'), fill=(230, 233, 240) if i < 3 else GOLD, anchor='ma')
    layer_alpha(b, crd, seg(t, 0.2, 1.2) * a); return b

SHOTS = [(0, 10, shot1), (10, 25, shot2), (25, 37, shot3), (37, 50, shot4), (50, 75, shot5), (75, 95, shot6), (95, 112, shot7), (112, 120, shot8)]
XF = 0.5   # crossfade length at every cut (s)
def frame(T):
    for i, (a, b_, fn) in enumerate(SHOTS):
        if a <= T < b_:
            im = fn(T - a)
            if i > 0 and T - a < XF:       # dissolve from previous shot (previous shot continues past its end)
                pa, pb, pf = SHOTS[i - 1]; prev = pf(T - pa); w_ = float(sm((T - a) / XF))
                return Image.blend(prev.convert('RGB'), im.convert('RGB'), w_)
            return im.convert('RGB')
    return Image.new('RGB', (W, H))

if args.stills:
    for T in [float(x) for x in args.stills.split(',')]:
        frame(T).resize((1920, 1080), Image.LANCZOS).save(f'{args.out}_{T:06.2f}.jpg', quality=90); print('still', T, flush=True)
    sys.exit()
f0, f1 = int(round(args.t0 * FPS)), int(round(args.t1 * FPS))
enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '12',
                        '-pix_fmt', 'yuv420p', args.out], stdin=subprocess.PIPE)
import time; t_ = time.time()
for f in range(f0, f1):
    enc.stdin.write(np.asarray(frame(f / FPS)).tobytes())
    if f % 30 == 0: print(f'frame {f} {time.time() - t_:.0f}s', flush=True)
enc.stdin.close(); enc.wait(); print('done', args.out)
