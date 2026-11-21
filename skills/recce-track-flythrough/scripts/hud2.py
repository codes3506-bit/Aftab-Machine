"""HUD / graphics pass for both videos (VID=1 recced tr amended, VID=2 proposed Opt 2).
usage: VID=1|2 hud2.py TERRAIN.mp4 OUT.mp4 [--stills t1,t2]
"""
import sys, json, math, subprocess, argparse, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
sys.path.insert(0, '/home/user/recce/work')
from timeline import *

ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--stills', default='')
args = ap.parse_args() if __name__ == '__main__' else ap.parse_args(['x', 'y'])
W, H = 1920, 1080
FD = '/home/user/recce/assets'
def fpath(name, fallback):
    p = f'{FD}/{name}'; return p if os.path.exists(p) else fallback
F_REG = fpath('Candara.ttf', '/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf')
F_BOLD = fpath('Candarab.ttf', '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf')
F_IT = fpath('Candarai.ttf', '/usr/share/fonts/truetype/crosextra/Carlito-Italic.ttf')
F_BI = fpath('Candaraz.ttf', '/usr/share/fonts/truetype/crosextra/Carlito-BoldItalic.ttf')
_fc = {}
def F(sz, w='r'):
    k = (sz, w)
    if k not in _fc: _fc[k] = ImageFont.truetype({'r': F_REG, 'b': F_BOLD, 'i': F_IT, 'bi': F_BI}[w], sz)
    return _fc[k]

NAVY = (0, 32, 96); NAVY2 = (8, 22, 58); GOLD = (255, 197, 26); WHITE = (255, 255, 255); GREY = (200, 208, 222)
RED = (232, 40, 40); BLUE = (30, 108, 255); GREEN = (16, 200, 90); MAG = (190, 70, 255); ORANGE = (255, 150, 30); YEL = (255, 230, 60)
WCOL = {0: BLUE, 1: RED, 2: GREEN}; WNAME = {0: 'Levelling (new fmn)', 1: 'Cut & fill (hy const – rock)', 2: 'Nullah filling'}
GR_DATE = 'Gr recce – 20 Nov 26'

# ---------------- data ----------------
A1 = json.load(open(f'{R}/work/analysis.json')); R1 = A1['res']
A2 = json.load(open(f'{R}/work/an_v1.json')); R2 = A2['res']
POL1 = json.load(open(f'{R}/work/pol_recce.json')); POL1F = json.load(open(f'{R}/work/pol_fleet.json'))
POL2 = json.load(open(f'{R}/work/pol_v1_1.json')); POL2F = json.load(open(f'{R}/work/pol_v1_F.json'))
SC1 = json.load(open(f'{R}/work/scene.json'))
A = A1 if VID == 1 else A2
CH = np.array(A['CH']); Z = np.array(A['Z']); TYP = SC['track']['typ']; G50 = np.array(SC['track']['g'])
def hrs(P, pred): return sum(r['q'] for r in P['rows'] if pred(r))
def summ(P):
    ex = hrs(P, lambda r: r['g'] == 'exc'); dz = hrs(P, lambda r: r['d'].startswith('Dozer'))
    ml = sum(r['l'] for r in P['rows'] if r['g'] == 'veh'); mk = sum(r['q'] for r in P['rows'] if r['g'] == 'veh')
    el = sum(r['l'] for r in P['rows'] if r['g'] == 'exc'); dl = sum(r['l'] for r in P['rows'] if r['d'].startswith('Dozer'))
    return dict(ex=ex, dz=dz, ml=ml, mk=mk, el=el, dl=dl, tot=P['total'], veh=[r for r in P['rows'] if r['g'] == 'veh'])
S1, S1F, S2, S2F = summ(POL1), summ(POL1F), summ(POL2), summ(POL2F)
D1 = math.ceil(max(S1['ex'], S1['dz']) / 8); D1F = math.ceil(max(S1['ex'] / 24, S1['dz'] / 16))
D2 = math.ceil(max(S2['ex'], S2['dz']) / 8); D2F = math.ceil(max(S2['ex'] / 16, S2['dz'] / 16))
ROCK1 = R1['bench_m3'] + R1['grade_m3']; ROCK2 = R2['bench_m3'] + R2['grade_m3']
hm = np.load(f'{R}/work/hm.npy'); HMm = json.load(open(f'{R}/work/meta.json'))['hm']; VE = 1.5
def hgt(x, y):
    i = int(np.clip((x - HMm['x0']) / 6, 0, HMm['nx'] - 1)); j = int(np.clip((y - HMm['y0']) / 6, 0, HMm['ny'] - 1)); return float(hm[j, i])

def ease(x): return smooth(x)
def fade(t, a, b, fi=0.6, fo=0.6):
    if t < a or t > b: return 0.0
    return min(1.0, (t - a) / fi if fi else 1, (b - t) / fo if fo else 1)

# ---------------- primitives ----------------
def panel(w, h, bg=NAVY2, alpha=0.9, r=16, border=GOLD, bw=0):
    S = 2; im = Image.new('RGBA', (w * S, h * S), bg + (255,))
    m = Image.new('L', (w * S, h * S), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w * S - 1, h * S - 1), r * S, fill=int(255 * alpha))
    im.putalpha(m)
    if bw: ImageDraw.Draw(im).rounded_rectangle((0, 0, w * S - 1, h * S - 1), r * S, outline=border + (255,), width=bw * S)
    return im.resize((w, h), Image.LANCZOS)
_sh = {}
def shadowed(im, glow=True):
    key = (id(im), glow)
    if key in _sh: return _sh[key]
    b = 18; w, h = im.size; s = Image.new('RGBA', (w + 4 * b, h + 4 * b), (0, 0, 0, 0))
    a = im.split()[3]
    sh = Image.new('RGBA', im.size, (0, 0, 0, 255)); sh.putalpha(a.point(lambda v: int(v * 0.5)))
    s.alpha_composite(sh, (2 * b, 2 * b + 8)); s = s.filter(ImageFilter.GaussianBlur(14))
    if glow:   # professional gold glow on the border
        g = Image.new('RGBA', s.size, (0, 0, 0, 0)); gl = Image.new('RGBA', im.size, GOLD + (255,)); gl.putalpha(a.point(lambda v: 255 if v > 10 else 0))
        g.alpha_composite(gl, (2 * b, 2 * b)); g = g.filter(ImageFilter.GaussianBlur(9)); ga = g.split()[3].point(lambda v: int(v * 0.75)); g.putalpha(ga)
        s.alpha_composite(g)
    s.alpha_composite(im, (2 * b, 2 * b)); _sh[key] = (s, 2 * b)
    if len(_sh) > 60: _sh.pop(next(iter(_sh)))
    return s, 2 * b
def opacity(im, o):
    if o >= 0.999: return im
    im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * o))); return im
def put(base, im, x, y, o=1.0, sh=True, glow=True):
    if o <= 0.003: return
    if sh: im, pad = shadowed(im, glow)
    else: pad = 0
    base.alpha_composite(opacity(im, o), (int(x - pad), int(y - pad)))
def tw(d, s, f): return d.textlength(s, font=f)

# ---------------- logos (from PPTX) ----------------
def badge(src, white_bg, size=150):
    S = 4; n = size * S; im = Image.new('RGBA', (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    e = Image.open(src).convert('RGBA')
    if white_bg:   # 23 KS crest on white square -> white disc with gold ring
        d.ellipse((0, 0, n - 1, n - 1), fill=GOLD + (255,)); d.ellipse((4 * S, 4 * S, n - 4 * S, n - 4 * S), fill=(255, 255, 255, 255))
        k = (n - 18 * S) / max(e.size); e = e.resize((int(e.size[0] * k), int(e.size[1] * k)), Image.LANCZOS)
        im.alpha_composite(e, ((n - e.size[0]) // 2, (n - e.size[1]) // 2 + 2 * S))
    else:          # 44 Div emblem is already a disc
        d.ellipse((0, 0, n - 1, n - 1), fill=GOLD + (255,))
        k = (n - 8 * S) / max(e.size); e = e.resize((int(e.size[0] * k), int(e.size[1] * k)), Image.LANCZOS)
        im.alpha_composite(e, ((n - e.size[0]) // 2, (n - e.size[1]) // 2))
    return im
_L = badge(f'{FD}/pptx/x/ppt/media/image1.png', False); _R = badge(f'{FD}/pptx/x/ppt/media/image2.png', True)
def logo_sz(im, s): return im.resize((s, s), Image.LANCZOS)
TITLE = 'RECCE ALTN TR CONST - B3 TO HARYAAN BOO' if VID == 1 else 'PROPOSED ALTN TR (OPT 2) - B3 TO HARYAAN BOO'

def title_big(o, t):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); f = F(70, 'b'); d0 = ImageDraw.Draw(ov); tl = tw(d0, TITLE, f)
    LS = 150; bw = int(tl + 2 * LS + 150); bh = 210
    p = panel(bw, bh, NAVY, 0.92, 22, GOLD, 3); d = ImageDraw.Draw(p)
    d.text((bw / 2, bh / 2 - 6), TITLE, font=f, fill=WHITE, anchor='mm')
    u = ease((t - 1.4) / 1.2); lw = int(tl * u); d.rectangle((bw / 2 - lw / 2, bh / 2 + 44, bw / 2 + lw / 2, bh / 2 + 48), fill=GOLD)
    p.alpha_composite(logo_sz(_L, LS), (30, (bh - LS) // 2)); p.alpha_composite(logo_sz(_R, LS), (bw - 30 - LS, (bh - LS) // 2))
    s = min(1.0, (W - 80) / bw) * (0.94 + 0.06 * ease(t / 1.6))
    p = p.resize((int(bw * s), int(bh * s)), Image.LANCZOS)
    put(ov, p, (W - p.size[0]) / 2, (H - p.size[1]) / 2 - 40, o)
    return ov
def topbar():
    bh = 80; p = Image.new('RGBA', (W, bh), NAVY + (232,)); d = ImageDraw.Draw(p); d.rectangle((0, bh - 3, W, bh), fill=GOLD)
    p.alpha_composite(logo_sz(_L, 68), (16, 6)); p.alpha_composite(logo_sz(_R, 68), (W - 84, 6))
    d.text((W / 2, bh / 2 - 1), TITLE, font=F(40, 'b'), fill=WHITE, anchor='mm'); return p
TOPBAR = topbar()
FOOT = ('Imagery © Esri, Maxar, Earthstar Geographics  ·  Terrain: Copernicus GLO-30 DEM  ·  Alignment, strata & N xings: KMZ  ·  ' + GR_DATE + '  ·  Vertical exaggeration ×1.5') if VID == 1 else \
       ('Imagery © Esri, Maxar, Earthstar Geographics  ·  Terrain: Copernicus GLO-30 DEM  ·  Opt 2 alignment: terrain-model route study (1:7 design grade) – gr recce to confirm  ·  Vertical exaggeration ×1.5')
def footer(ov, o):
    d = ImageDraw.Draw(ov); f = F(17, 'i'); x = W / 2; y = H - 16
    d.text((x + 1, y + 1), FOOT, font=f, fill=(0, 0, 0, int(200 * o)), anchor='mm'); d.text((x, y), FOOT, font=f, fill=(235, 235, 235, int(235 * o)), anchor='mm')

# ---------------- labels with collision avoidance ----------------
KIND = {'post': (RED, WHITE, 30), 'place': (NAVY, WHITE, 26), 'khor': ((20, 20, 20), YEL, 24), 'road': (RED, WHITE, 24),
        'km': ((255, 255, 255), NAVY, 21), 'nx': (YEL, (0, 0, 0), 20), 'crest': (MAG, WHITE, 26), 'ghost': ((70, 74, 86), WHITE, 22), 'opt2': ((10, 150, 70), WHITE, 26)}
_last = {}
class Placer:
    def __init__(s, reserved): s.rects = [tuple(r) for r in reserved]
    def free(s, r):
        if r[0] < 6 or r[2] > W - 6 or r[1] < 86 or r[3] > H - 34: return False
        return all(r[2] + 8 < q[0] or q[2] + 8 < r[0] or r[3] + 6 < q[1] or q[3] + 6 < r[1] for q in s.rects)
    def place(s, lid, x, y, w, h, lift):
        opts = [(0, lift)] + [(dx, lift + dl) for dl in (0, 45, 90, 135, 180, 225) for dx in (0, -0.65 * w, 0.65 * w)] + [(0, lift - 40), (0, -lift - h + 10)]
        if lid in _last: opts = [_last[lid]] + opts
        for dx, ly in opts:
            r = (x + dx - w / 2, y - ly - h, x + dx + w / 2, y - ly)
            if s.free(r): s.rects.append(r); _last[lid] = (dx, ly); return r
        return None
def draw_pill(ov, x, y, r, txt, kind, o, it=False):
    bg, fg, sz = KIND[kind]; d = ImageDraw.Draw(ov); a = int(255 * o); f = F(sz, 'bi' if it else 'b')
    cx = (r[0] + r[2]) / 2; by = r[3] if r[3] < y else r[1]
    d.line((x, y, cx, by), fill=(255, 255, 255, a), width=2)
    if kind == 'nx': d.polygon([(x, y - 14), (x - 10, y + 4), (x + 10, y + 4)], fill=YEL + (a,), outline=(0, 0, 0, a))
    else: d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=bg + (a,), outline=(255, 255, 255, a), width=2)
    d.rounded_rectangle(r, 8, fill=bg + (a,), outline=(255, 255, 255, int(a * 0.8)), width=2)
    d.text((cx, (r[1] + r[3]) / 2), txt, font=f, fill=fg + (a,), anchor='mm')
def labels(ov, cam, items, o, placer):
    d = ImageDraw.Draw(ov)
    for lid, txt, kind, lift, t_on in items:
        if lid not in cam['L'] or o * t_on <= 0.01: continue
        x, y, vis = cam['L'][lid]
        if not vis and kind not in ('post',): continue
        if not (0 <= x <= W and 80 <= y <= H): continue
        sz = KIND[kind][2]; f = F(sz, 'bi' if kind == 'khor' else 'b'); w = tw(d, txt, f) + 26; h = sz + 16
        r = placer.place(lid, x, y, w, h, lift)
        if r: draw_pill(ov, x, y, r, txt, kind, o * t_on, it=(kind == 'khor'))

# ---------------- Gwd / Kci arrows ----------------
CHW = json.load(open(f'{R}/work/chw.json'))
def arrow_img(txt, left):
    S = 3; L_, Hh = 330 * S, 76 * S; im = Image.new('RGBA', (L_ + 8 * S, Hh + 8 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    o = 4 * S; head = 70 * S; body = Hh * 0.62; y0 = o + (Hh - body) / 2
    poly = [(o, y0), (o + L_ - head, y0), (o + L_ - head, o), (o + L_, o + Hh / 2), (o + L_ - head, o + Hh), (o + L_ - head, y0 + body), (o, y0 + body)]
    d.polygon(poly, fill=(34, 74, 28, 255)); d.line(poly + [poly[0]], fill=(190, 230, 140, 255), width=3 * S)
    hl = [(o + 6 * S, y0 + 5 * S), (o + L_ - head - 4 * S, y0 + 5 * S), (o + L_ - head - 4 * S, y0 + body * 0.42), (o + 6 * S, y0 + body * 0.42)]
    d.polygon(hl, fill=(80, 130, 50, 120))
    if left: im = ImageOps.mirror(im)
    d = ImageDraw.Draw(im); cx = im.size[0] / 2 + (head / 3 if left else -head / 3)
    d.text((cx, im.size[1] / 2), txt, font=F(34 * S, 'bi'), fill=(255, 236, 90, 255), anchor='mm', stroke_width=2 * S, stroke_fill=(20, 40, 10, 255))
    return im.resize((im.size[0] // S, im.size[1] // S), Image.LANCZOS)
ARW = (arrow_img('Gwd 290 Kms', True), arrow_img('Kci 210 Kms', False))
def project(M, p):
    v = np.array(M) @ np.array([p[0], p[1], p[2], 1.0])
    if v[3] <= 0: return None
    return np.array([(v[0] / v[3] * 0.5 + 0.5) * W, (1 - (v[1] / v[3] * 0.5 + 0.5)) * H])
def arrows(ov, cam, o, placer):
    if o <= 0.01: return
    M = cam['M']; E_, N_ = CHW['E'], CHW['N']
    b1 = [l['p'] for l in SC1['labels'] if l['id'] == 'B-1'][0]
    for k, (pa, pb) in enumerate((((E_[len(E_) // 2], N_[len(N_) // 2]), (E_[-1], N_[-1])), ((E_[0], N_[0]), tuple(b1)))):
        A_ = project(M, (pa[0], pa[1], hgt(*pa) * VE)); B_ = project(M, (pb[0], pb[1], hgt(*pb) * VE))
        if A_ is None or B_ is None: continue
        v = B_ - A_; ang = math.degrees(math.atan2(-v[1], abs(v[0]) + 1e-6)) * (1 if k == 1 else -1)
        ang = float(np.clip(ang, -22, 22)); im = ARW[k].rotate(ang, Image.BICUBIC, expand=True)
        x = float(np.clip(B_[0], 30 + im.size[0] / 2, W - 30 - im.size[0] / 2)); y = float(np.clip(B_[1] + 40, 160, H - 120))
        r = (x - im.size[0] / 2, y - im.size[1] / 2, x + im.size[0] / 2, y + im.size[1] / 2); placer.rects.append(r)
        put(ov, im, r[0], r[1], o, glow=False)

# ---------------- profile chart ----------------
def profile_img(w, h, big=True, ghost=None):
    S = 2; im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ml, mr, mt, mb = (90 * S, 30 * S, 34 * S, 62 * S) if big else (50 * S, 12 * S, 10 * S, 30 * S)
    pw, ph = w * S - ml - mr, h * S - mt - mb; z0, z1 = 60, 260; LX = 9.0
    X = lambda c: ml + c / LX * pw; Y = lambda z: mt + (1 - (z - z0) / (z1 - z0)) * ph
    fs = F((19 if big else 14) * S, 'r')
    for z in range(60, 261, 50):
        d.line((ml, Y(z), ml + pw, Y(z)), fill=(255, 255, 255, 50), width=S); d.text((ml - 8 * S, Y(z)), f'{z}', font=fs, fill=GREY, anchor='rm')
    for c in range(0, 10):
        d.line((X(c), mt + ph, X(c), mt + ph + 5 * S), fill=GREY, width=S); d.text((X(c), mt + ph + 8 * S), f'{c}', font=fs, fill=GREY, anchor='mt')
    st = np.abs(G50) > 0.14
    for i in range(len(CH) - 1):
        if st[i]: d.rectangle((X(CH[i]), mt, X(CH[i + 1]) + 1, mt + ph), fill=(255, 40, 40, 46))
    for i in range(len(CH) - 1):
        d.polygon([(X(CH[i]), Y(Z[i])), (X(CH[i + 1]), Y(Z[i + 1])), (X(CH[i + 1]), mt + ph), (X(CH[i]), mt + ph)], fill=WCOL[TYP[i]] + (150,))
    if ghost is not None:
        gc, gz = ghost; pts = [(X(c), Y(z)) for c, z in zip(gc, gz)]
        for k in range(0, len(pts) - 1, 6): d.line(pts[k:k + 4], fill=(235, 235, 240, 220), width=3 * S)
    d.line([(X(c), Y(z)) for c, z in zip(CH, Z)], fill=(255, 255, 255, 255), width=(4 if big else 3) * S, joint='curve')
    if big:
        d.text((ml + pw / 2, h * S - 8 * S), 'CH (km)', font=F(20 * S, 'r'), fill=GREY, anchor='mb')
        d.text((ml - 8 * S, mt - 12 * S), 'Elev (m)', font=F(19 * S, 'r'), fill=GREY, anchor='rb')
        i = int(np.argmax(Z)); cx, cy = X(CH[i]), Y(Z[i]); d.ellipse((cx - 7 * S, cy - 7 * S, cx + 7 * S, cy + 7 * S), fill=MAG + (255,))
        nm = 'Ridge crest' if VID == 1 else 'Saddle'
        d.text((cx + 12 * S, cy - 6 * S), f'{nm} {Z[i]:.0f} m (CH {CH[i]:.2f})', font=F(19 * S, 'b'), fill=WHITE, anchor='lb')
        d.text((X(0.05), Y(Z[0]) - 40 * S), f'B-3  {Z[0]:.0f} m', font=F(18 * S, 'b'), fill=WHITE, anchor='lb')
        d.text((X(CH[-1]) - 4 * S, Y(Z[-1]) - 16 * S), f'Haryan BOO  {Z[-1]:.0f} m', font=F(18 * S, 'b'), fill=WHITE, anchor='rb')
    return im.resize((w, h), Image.LANCZOS), (ml / S, mt / S, pw / S, ph / S, z0, z1, LX)

# ---------------- panels ----------------
def text_panel(w, title, rows, sub=None, fs=25, rowh=38, tfs=30):
    h = 64 + (32 if sub else 0) + rowh * len(rows) + 18
    p = panel(w, h, NAVY2, 0.92, 16, GOLD, 2); d = ImageDraw.Draw(p)
    d.text((22, 16), title, font=F(tfs, 'b'), fill=GOLD); y = 58
    if sub: d.text((22, y), sub, font=F(21, 'i'), fill=GREY); y += 32
    for r in rows:
        if isinstance(r, tuple) and len(r) == 3: k, v, c = r
        elif isinstance(r, tuple): k, v = r; c = WHITE
        else: k, v, c = r, None, WHITE
        if v is None:
            d.ellipse((24, y + 13, 34, y + 23), fill=GOLD); d.text((44, y + 18), k, font=F(fs, 'r'), fill=c, anchor='lm')
        else:
            d.text((24, y + 18), k, font=F(fs, 'r'), fill=GREY, anchor='lm'); d.text((w - 22, y + 18), v, font=F(fs, 'b'), fill=c, anchor='rm')
        y += rowh
    return p
def table_panel(w, title, head, rows, colw, sub=None, fs=22, rowh=40, hl=(), note=None, tfs=28):
    h = 66 + (30 if sub else 0) + rowh * (len(rows) + 1) + (30 if note else 0) + 20
    p = panel(w, h, NAVY2, 0.94, 16, GOLD, 2); d = ImageDraw.Draw(p)
    d.text((20, 16), title, font=F(tfs, 'b'), fill=GOLD); y = 58
    if sub: d.text((20, y), sub, font=F(19, 'i'), fill=GREY); y += 30
    xs = np.cumsum([14] + colw)
    d.rectangle((12, y, w - 12, y + rowh), fill=(180, 20, 20))
    for j, s in enumerate(head):
        d.text(((xs[j] + 10) if j == 0 else (xs[j] + xs[j + 1]) / 2, y + rowh / 2), s, font=F(fs, 'b'), fill=WHITE, anchor='lm' if j == 0 else 'mm')
    y += rowh
    for i, r in enumerate(rows):
        bg = (90, 70, 10) if i in hl else ((30, 44, 84) if i % 2 == 0 else (20, 32, 66)); d.rectangle((12, y, w - 12, y + rowh), fill=bg)
        for j, s in enumerate(r):
            col = GREY if j == 0 else (WHITE if j == 1 else (255, 220, 90))
            if isinstance(s, tuple): s, col = s
            d.text(((xs[j] + 10) if j == 0 else (xs[j] + xs[j + 1]) / 2, y + rowh / 2), s, font=F(fs, 'b' if j else 'r'), fill=col, anchor='lm' if j == 0 else 'mm')
        y += rowh
    if note: d.text((20, y + 8), note, font=F(17, 'i'), fill=GREY)
    return p
def plant_panel(Sx, days, fleet_txt):
    v = Sx['veh']; kms = {r['d']: r['q'] for r in v}
    rows = [['Excavator / Jack hammer', f"{Sx['ex']:,} hrs", '20', f"{Sx['el']:,}"], ['Dozer', f"{Sx['dz']:,} hrs", '27', f"{Sx['dl']:,}"],
            ['Misc (veh)', f"{Sx['mk']:,} km", '–', f"{Sx['ml']:,}"], ['TOTAL POL (lits)', '', '', f"{Sx['tot']:,}"]]
    note = 'Misc: ' + ', '.join(f"{k.replace('Single Cabin', 'single cabin').replace('Double Cabin', 'double cabin').replace('Civ Trk', 'civ trk')} {q:,} km" for k, q in kms.items())
    return table_panel(600, 'PLT / EQPT, POL & TIME CALC', ['Description', 'Qty', 'LPH', 'Lits'], rows, [262, 130, 70, 110], hl=(3,), note=note, fs=21, rowh=40)
def fleet_panel(items, days, tot):
    return text_panel(600, 'MACHINERY TO BE EMP', items + [('Engr effort', f'{days} working days', GOLD), ('Total POL', f'{tot:,} lits', GOLD)], fs=23, rowh=36)

PROF_BIG, PB = profile_img(1160, 420, True, None if VID == 1 else (np.array(A1['CH']), np.array(A1['Z'])))
def prof_panel():
    p = panel(1200, 500, NAVY2, 0.92, 16, GOLD, 2); d = ImageDraw.Draw(p)
    d.text((22, 16), 'ELEVATION PROFILE  (B-3 → HARYAN BOO)', font=F(30, 'b'), fill=GOLD); p.alpha_composite(PROF_BIG, (20, 64))
    x = 660
    for k in (0, 1, 2):
        nm = WNAME[k].split(' (')[0]; d.rectangle((x, 28, x + 24, 40), fill=WCOL[k]); d.text((x + 30, 34), nm, font=F(19, 'r'), fill=WHITE, anchor='lm'); x += 30 + tw(d, nm, F(19, 'r')) + 20
    if VID == 2: d.line((x, 34, x + 26, 34), fill=(235, 235, 240), width=3); d.text((x + 32, 34), 'Opt 1', font=F(19, 'r'), fill=WHITE, anchor='lm')
    else: d.rectangle((x, 26, x + 24, 42), fill=(120, 40, 40)); d.text((x + 30, 34), '>1:7', font=F(19, 'r'), fill=WHITE, anchor='lm')
    return p
PROF_PANEL = prof_panel()
STRIP, SB = profile_img(560, 170, False)

if VID == 1:
    SCOPE = text_panel(600, 'SCOPE OF WORK – RECCE', [
        ('Tr length (LU recce)', '9.0 km'), ('Measured on imagery', f"{R1['len_img_km']:.2f} km"),
        ('Levelling (new fmn)', '4.06 km', (120, 170, 255)), ('Cut & fill (hy const – rock)', '3.93 km', (255, 110, 110)),
        ('Nullah filling', '1.01 km', (90, 230, 140)), ('N xings (minor / medium)', '17  (13 / 4)'),
        ('Hy const areas (LU marking)', '2'), ('Strata', 'Gravel + mixed / rock')], sub='B-3 to Haryan BOO (442 Bde)  ·  ' + GR_DATE)
    STATS = text_panel(600, 'TERRAIN – WHAT THE GROUND SAYS', [
        ('Elevation range', f"{R1['elev_min']:.0f} – {R1['elev_max']:.0f} m"), ('Total climb / descent', f"{R1['climb_m']:.0f} m / {R1['descent_m']:.0f} m"),
        ('Max grade (over 100 m)', '26.6 %', (255, 110, 110)), ('Steepest pitch (over 50 m)', '45 %', (255, 110, 110)),
        ('Length steeper than 1:10', f"{R1['len_gt10_km']:.2f} km"), ('Length steeper than 1:7', f"{R1['len_gt14_km']:.2f} km", (255, 170, 80)),
        ('Critical pass', 'CH 3.0 – 5.3 km', GOLD)])
    PH = {k: Image.open(f'{R}/photos/img{k:02d}.jpeg').convert('RGB') for k in (3, 4, 5, 6, 7)}
    def polaroid(k, cap, h=520, rot=0):
        im = PH[k]; s = h / im.size[1]; im = im.resize((int(im.size[0] * s), h), Image.LANCZOS)
        w_ = im.size[0] + 24; h_ = h + 74; p = Image.new('RGBA', (w_, h_), (250, 250, 246, 255)); p.paste(im, (12, 12))
        ImageDraw.Draw(p).text((w_ / 2, h + 44), cap, font=F(22, 'bi'), fill=(20, 20, 30), anchor='mm')
        return p.rotate(rot, Image.BICUBIC, expand=True) if rot else p
    CARDS = {'ascent': (text_panel(700, 'CH 3.0 – 4.05 km  ·  ASCENT TO RIDGE', [
        'Climb 187 → 247 m in about 1 km', 'Pitches of 35 – 41 % (over 50 m)', 'Side slopes up to 26°, loose scree on rock',
        'LU hy const areas: CH 2.6–3.3 & 4.0–5.9', 'Rock strata – Excavator with hy breaker req', 'Grade cuts up to 15.7 m deep to get 1:7'], sub=GR_DATE, fs=25),
        [polaroid(3, 'Loose scree gully – ascent', 520, 3), polaroid(6, 'V-gully, rock & scree slopes', 520, -2.5)]),
        'crest': (text_panel(700, 'CH 4.05 km  ·  RIDGE CREST 247 m', [
        'Descent 100 m in < 1 km on far side', 'Steepest pitch 45 % (over 50 m)', 'Narrow rock gorge – foot mov only at present',
        'Recce party needed rope over rock slabs', 'Massive rock – breaking, not dozing', '≈ 48,500 cu M rock to cut, CH 3.0 – 5.0 alone'], sub=GR_DATE, fs=25),
        [polaroid(4, 'Recce party in rock gorge', 470, 2.5), polaroid(7, 'Rope descent over rock slabs', 470, -2), polaroid(5, 'Narrow rock gorge on alignment', 470, 1.5)])}
    GRADE_CARD = text_panel(560, 'SLOPE ANALYSIS – CURRENT TR', [
        ('Steeper than 1:10', f"{R1['len_gt10_km']:.2f} km"), ('Steeper than 1:7', f"{R1['len_gt14_km']:.2f} km", (255, 170, 80)),
        ('Steeper than 1:5', f"{R1['len_gt20_km']:.2f} km", (255, 110, 110)), ('Max grade (100 m)', '26.6 %', (255, 110, 110)), ('Max pitch (50 m)', '45 %', (255, 110, 110))], fs=24)
    CMP = table_panel(600, 'WORK ASSESSMENT', ['', 'Slide Opt 1', 'Gr recce', '×'], [
        ['Rock cutting (lakh cft)', '3.21', f'{ROCK1 * 35.32 / 1e5:.1f}', f'{ROCK1 * 35.32 / 321494:.1f}'],
        ['Excavator (hrs)', '268', f"{S1['ex']:,}", f"{S1['ex'] / 268:.1f}"], ['Dozer (hrs)', '300', f"{S1['dz']:,}", f"{S1['dz'] / 300:.1f}"],
        ['POL (lits)', '19,660', f"{S1['tot']:,}", f"{S1['tot'] / 19660:.1f}"],
        ['Days – 1 Dozer + 1 Excavator', '40', f'{D1}', f'{D1 / 40:.1f}'], ['Days – 3 Excavator + 2 Dozer', '–', f'{D1F}', '']],
        [252, 110, 110, 92], sub='Recce quantities from terrain model along KMZ alignment', hl=(3, 5), fs=21, rowh=42)
    PLANT = plant_panel(S1F, D1F, '')
    FLEET = fleet_panel([('Excavator c/w hy breaker / Jack hammer', '3'), ('Dozer', '2'), ('FBT (plt mov, 300 km)', '5 trips')], D1F, S1F['tot'])
    CONCL = text_panel(600, 'ASSESSMENT', [
        'Marked tr crosses a 247 m rock ridge', '(CH 3.0 – 5.3): grades 26 – 45 % vs 1:7',
        f'≈ {ROCK1:,.0f} cu M rock to cut –', f'{ROCK1 * 35.32 / 321494:.0f} × the slide estimate',
        f'{S1["tot"]:,} lits POL; {D1} days with', f'1 Dozer + 1 Excavator ({D1F} days with 3 + 2)',
        'Rock breaking in gorge; 17 N xings', '– flash-flood dependent progress'], fs=23, rowh=36)
else:
    KMZ2 = R2['km']
    SCOPE = text_panel(600, 'SCOPE OF WORK – OPT 2 (WEST)', [
        ('Tr length (est on ground)', f"{R2['len_est_km']:.1f} km"), ('Measured on imagery', f"{R2['len_img_km']:.2f} km"),
        ('Levelling (new fmn)', f"{KMZ2['level']:.2f} km", (120, 170, 255)), ('Cut & fill (hy const – rock)', f"{KMZ2['cutfill']:.2f} km", (255, 110, 110)),
        ('Nullah filling / N bed', f"{KMZ2['nullah']:.2f} km", (90, 230, 140)), ('N xings', '3  (+ 1.55 km N bed)'),
        ('Take-off', 'B-3 Post (CHW)'), ('Strata', 'Gravel, mixed; rock at saddle')], sub='B-3 to Haryan BOO – west of recced tr')
    STATS = text_panel(600, 'TERRAIN – OPT 2', [
        ('Elevation range', f"{R2['elev_min']:.0f} – {R2['elev_max']:.0f} m"), ('Total climb / descent', f"{R2['climb_m']:.0f} m / {R2['descent_m']:.0f} m"),
        ('Max grade (over 100 m)', f"{R2['grade100']:.1f} %", (255, 170, 80)), ('Steepest pitch (over 50 m)', f"{R2['grade50']:.0f} %", (255, 170, 80)),
        ('Length steeper than 1:10', f"{R2['len_gt10_km']:.2f} km"), ('Length steeper than 1:7', f"{R2['len_gt14_km']:.2f} km", (255, 170, 80)),
        ('Highest point (saddle)', f"{R2['elev_max']:.0f} m  vs  247 m", GOLD)])
    CARDS = {'saddle': (text_panel(720, f"CH {CREST:.2f} km  ·  SADDLE {R2['elev_max']:.0f} m", [
        f"Crosses ridge band at a saddle – {247 - R2['elev_max']:.0f} m lower than Opt 1 crest", f"Max grade {R2['grade100']:.1f} % (100 m) vs 26.6 % on Opt 1",
        f"Grade cuts up to {R2['grade_cut_max_m']:.1f} m deep (vs 15.7 m)", f"Rock to cut ≈ {ROCK2:,.0f} cu M (vs {ROCK1:,.0f})",
        'No gorge – Excavator + Dozer can work from both ends', 'Gr recce of saddle to confirm strata'], sub='Terrain model – Copernicus 30 m DEM', fs=25), None),
        'nullah': (text_panel(720, 'CH 3.13 – 4.68 km  ·  DESCENT ALONG NULLAH BED', [
        'Gentle descent 160 → 97 m along gravel N bed', 'Dozer levelling – no rock cutting', '3 N xings: CH 3.27 (minor), 4.57 & 6.03 (medium)',
        'Stone pitching / Irish xing at medium xings', 'Flash-flood risk – const outside rain spells', 'Joins open valley floor to Haryan BOO'], sub='Terrain model – drainage analysis', fs=25), None)}
    def bars_panel():
        rows = [('Highest point (m)', 247, R2['elev_max'], 260), ('Max grade 100 m (%)', 26.6, R2['grade100'], 30), ('Rock cutting (\'000 cu M)', ROCK1 / 1000, ROCK2 / 1000, 60),
                ('POL (\'000 lits)', S1['tot'] / 1000, S2['tot'] / 1000, 70), ('Days (1 Dozer + 1 Excavator)', D1, D2, 230)]
        p = panel(940, 70 + 92 * len(rows) + 30, NAVY2, 0.92, 16, GOLD, 2); d = ImageDraw.Draw(p)
        d.text((22, 16), 'OPT 1 (RECCED)  vs  OPT 2 (WEST)', font=F(30, 'b'), fill=GOLD); y = 70
        for nm, a, b, mx in rows:
            d.text((24, y), nm, font=F(22, 'r'), fill=GREY)
            for k, (v, c, lab) in enumerate(((a, (200, 70, 70), 'Opt 1'), (b, (40, 190, 100), 'Opt 2'))):
                yy = y + 30 + k * 26; L_ = int(560 * v / mx); d.rectangle((150, yy, 150 + L_, yy + 20), fill=c)
                d.text((24 + 60, yy + 10), lab, font=F(19, 'b'), fill=WHITE, anchor='lm'); d.text((160 + L_, yy + 10), (f'{v:,.0f}' if nm.startswith('Days') or v >= 100 else f'{v:,.1f}'), font=F(20, 'b'), fill=WHITE, anchor='lm')
            y += 92
        return p
    CARDS['saddle'] = (CARDS['saddle'][0], [bars_panel()])
    GRADE_CARD = text_panel(560, 'SLOPE ANALYSIS – OPT 2', [
        ('Steeper than 1:10', f"{R2['len_gt10_km']:.2f} km  (2.06)"), ('Steeper than 1:7', f"{R2['len_gt14_km']:.2f} km  (1.18)", (255, 170, 80)),
        ('Steeper than 1:5', f"{R2['len_gt20_km']:.2f} km  (0.62)"), ('Max grade (100 m)', f"{R2['grade100']:.1f} %  (26.6)"), ('Max pitch (50 m)', f"{R2['grade50']:.0f} %  (45)")],
        sub='( ) = Opt 1 recced tr', fs=23)
    CMP = table_panel(600, 'COMPARISON  –  OPT 1 vs OPT 2', ['', 'Opt 1', 'Opt 2', 'Saving'], [
        ['Tr length (km)', '9.0', f"{R2['len_est_km']:.1f}", f"{9.0 - R2['len_est_km']:.1f} km"],
        ['Highest point (m)', '247', f"{R2['elev_max']:.0f}", f"{247 - R2['elev_max']:.0f} m"],
        ['Max grade 100 m (%)', '26.6', f"{R2['grade100']:.1f}", ''],
        ['Rock cutting (cu M)', f'{ROCK1:,.0f}', f'{ROCK2:,.0f}', f'{(1 - ROCK2 / ROCK1) * 100:.0f} %'],
        ['N xings', '17', '3 + N bed', ''],
        ['Excavator (hrs)', f"{S1['ex']:,}", f"{S2['ex']:,}", f"{(1 - S2['ex'] / S1['ex']) * 100:.0f} %"],
        ['Dozer (hrs)', f"{S1['dz']:,}", f"{S2['dz']:,}", f"{(1 - S2['dz'] / S1['dz']) * 100:.0f} %"],
        ['POL (lits)', f"{S1['tot']:,}", f"{S2['tot']:,}", f"{(1 - S2['tot'] / S1['tot']) * 100:.0f} %"],
        ['Days (1 Dozer + 1 Excavator)', f'{D1}', f'{D2}', f'{(1 - D2 / D1) * 100:.0f} %'],
        ['Fleet / days', f'3 + 2 / {D1F}', f'2 + 2 / {D2F}', f'{D1F - D2F} days']],
        [228, 108, 108, 118], sub='Same terrain model & POL standards for both', hl=(7, 8), fs=20, rowh=38)
    PLANT = plant_panel(S2F, D2F, '')
    FLEET = fleet_panel([('Excavator c/w hy breaker / Jack hammer', '2'), ('Dozer', '2'), ('FBT (plt mov, 300 km)', '4 trips')], D2F, S2F['tot'])
    CONCL = text_panel(600, 'RECOMMENDATION', [
        'Opt 2 (west) avoids the 247 m rock', 'ridge & gorge of the recced tr',
        f'POL {S2["tot"]:,} vs {S1["tot"]:,} lits  (−{(1 - S2["tot"] / S1["tot"]) * 100:.0f} %)', f'Days {D2} vs {D1}  (1 Dozer + 1 Excavator)',
        f'{D2F} days with 2 Excavator + 2 Dozer', 'Gr recce of saddle & N bed', 'before approval of Opt 2'], fs=23, rowh=36)

def grade_legend():
    p = panel(560, 226, NAVY2, 0.92, 16, GOLD, 2); d = ImageDraw.Draw(p)
    d.text((22, 14), 'TR GRADE', font=F(26, 'b'), fill=GOLD); d.text((290, 14), 'GROUND SLOPE', font=F(26, 'b'), fill=GOLD)
    rows = [((64, 240, 115), '< 5 %'), ((255, 235, 64), '5 – 10 %'), ((255, 148, 26), '10 – 14 %'), ((255, 40, 36), '14 – 25 %'), ((190, 64, 255), '> 25 %')]
    for i, (c, s) in enumerate(rows):
        y = 58 + i * 32; d.rectangle((24, y, 66, y + 18), fill=c); d.text((78, y + 9), s, font=F(21, 'r'), fill=WHITE, anchor='lm')
        if i: d.rectangle((292, y, 334, y + 18), fill=c); d.text((346, y + 9), s, font=F(21, 'r'), fill=WHITE, anchor='lm')
    return p
GRADE_LEG = grade_legend()
AREA = text_panel(560, 'AREA ORIENTATION', [('Tr', 'B-3 Post → Haryan BOO'), ('Indicated by', '25 FF / 442 Bde'), ('Haryan – Keisher', '9 km'),
                  ('Keisher – B5 / Darband', '7 km / 5 km'), ('Gwd / Kci (via CHW)', '290 / 210 km')] +
                  ([('Hy const areas (LU)', '2 (red dashed)')] if VID == 1 else [('Opt 1 (recced)', 'grey line'), ('Opt 2 (proposed)', 'west of Opt 1')]), fs=23, rowh=36)

# ---------------- live HUD ----------------
def live_hud(ov, c, o, placer):
    if o <= 0.01: return
    i = int(np.clip(np.searchsorted(CH, c), 0, len(CH) - 1))
    p = panel(590, 200, NAVY2, 0.86, 14, GOLD, 2); p.alpha_composite(STRIP, (14, 16)); d = ImageDraw.Draw(p)
    ml, mt, pw, ph, z0, z1, LX = SB; x = 14 + ml + c / LX * pw; y = 16 + mt + (1 - (Z[i] - z0) / (z1 - z0)) * ph
    d.line((x, 16 + mt, x, 16 + mt + ph), fill=GOLD, width=2); d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=GOLD, outline=WHITE, width=2)
    put(ov, p, 40, H - 200 - 48, o); placer.rects.append((40, H - 248, 630, H - 48))
    q = panel(420, 262, NAVY2, 0.88, 14, GOLD, 2); d = ImageDraw.Draw(q)
    g = G50[i] * 100; g = 0.0 if abs(g) < 0.5 else g; gc = (64, 240, 115) if abs(g) < 5 else YEL if abs(g) < 10 else ORANGE if abs(g) < 14 else RED if abs(g) < 25 else MAG
    for k, (a, b, col) in enumerate([('CH', f'{c:5.2f} km', WHITE), ('ELEV', f'{Z[i]:.0f} m', WHITE), ('GRADE', f'{g:+.0f} %', gc)]):
        d.text((24, 32 + k * 54), a, font=F(26, 'b'), fill=GREY, anchor='lm'); d.text((396, 32 + k * 54), b, font=F(40, 'b'), fill=col, anchor='rm')
    t_ = TYP[i]; d.rectangle((24, 198, 52, 226), fill=WCOL[t_]); d.text((64, 212), WNAME[t_], font=F(25, 'b'), fill=WHITE, anchor='lm')
    put(ov, q, W - 460, 110, o); placer.rects.append((W - 460, 110, W - 40, 372))

# ---------------- composer ----------------
T_TITLE_OUT = 9.4; FIN = SHOTS[6][0]; FLY0, FLY1 = SHOTS[4][0], SHOTS[4][1]; GR0 = SHOTS[5][0]; BR0, BR1 = PAUSES[0][0], PAUSES[0][1]
CACHE = {}
def compose(t, frame, cam):
    base = Image.fromarray(frame).convert('RGBA')
    pz = pause_at(t)
    if pz:
        k, dt, dur = pz; key = ('blur', k)
        if key not in CACHE:
            b = base.filter(ImageFilter.GaussianBlur(5)); b.alpha_composite(Image.new('RGBA', (W, H), (4, 10, 28, 140))); CACHE[key] = b
        u = ease(dt / 0.8) * (1 - ease((dt - dur + 0.8) / 0.8)); base = Image.blend(base, CACHE[key], u)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if 'vig' not in CACHE:
        v = Image.new('L', (W, H), 0); ImageDraw.Draw(v).ellipse((-260, -200, W + 260, H + 200), fill=255); v = v.filter(ImageFilter.GaussianBlur(160))
        vig = Image.new('RGBA', (W, H), (0, 0, 0, 255)); vig.putalpha(v.point(lambda a: int((255 - a) * 0.5))); CACHE['vig'] = vig
    base.alpha_composite(CACHE['vig'])
    reserved = [(0, 0, W, 84)]
    if t < T_TITLE_OUT:
        ov.alpha_composite(title_big(ease(t / 0.9) * (1 - ease((t - 8.3) / 0.9)), t))
    else:
        put(ov, TOPBAR, 0, 0, ease((t - 8.8) / 0.8) * (1 - ease((t - DUR + 1.4) / 1.2)), sh=False)
    P = Placer(reserved)
    # area orientation
    if 10 <= t < 27:
        o = fade(t, 10.5, 26.5, 0.8, 1.0)
        ao = ease((t - 13) / 0.8) * fade(t, 13, 26.5, 0.01, 1.0)
        if ao > 0.01: put(ov, AREA, 40, H - AREA.size[1] - 50, ao); P.rects.append((40, H - AREA.size[1] - 50, 600, H - 50))
        arrows(ov, cam, ease((t - 11.5) / 0.8) * fade(t, 11.5, 26.5, 0.01, 1.0), P)
        seq = [('B-3 Post', 'B-3 Post', 'post', 90), ('Haryan BOO', 'Haryan BOO', 'post', 110), ('Keisher', 'Keisher', 'place', 80), ('B5', 'B5', 'place', 70),
               ('Darband', 'Darband', 'place', 80), ('CHW (N10)', 'CHW (N10)', 'road', 60), ('B-1', 'B-1', 'place', 70),
               ('Maneji K', 'Maneji K', 'khor', 50), ('Haryan K', 'Haryan K', 'khor', 50), ('Hatti K', 'Hatti K', 'khor', 50)]
        if VID == 2: seq.append(('Opt 1 crest', 'Opt 1 – recced tr', 'ghost', 70))
        labels(ov, cam, [(a, b, c_, d_, ease((t - 11 - n_ * 0.45) / 0.5)) for n_, (a, b, c_, d_) in enumerate(seq)], o, P)
    if 25 <= t < BR0 + 1:
        labels(ov, cam, [('B-3 Post', 'B-3 Post  ·  CH 0', 'post', 110, 1), ('Haryan BOO', f'Haryan BOO  ·  CH {LEN:.1f}', 'post', 110, 1)], fade(t, 27, BR0 + 0.6, 0.6, 0.5), P)
    # brief pause (background frozen)
    if BR0 <= t < BR1 + 0.5:
        dt = t - BR0; oo = 1 - ease((t - BR1 + 0.9) / 0.6)
        put(ov, SCOPE, 48, 112, ease((dt - 0.5) / 0.7) * oo); put(ov, STATS, 48, 112 + SCOPE.size[1] + 22, ease((dt - 1.6) / 0.7) * oo)
        put(ov, PROF_PANEL, W - 1200 - 48, 112, ease((dt - 2.6) / 0.7) * oo)
        if dt > 4:
            f = F(30, 'bi'); s = 'Commencing fly-through recce of the complete tr' if VID == 1 else 'Commencing fly-through of proposed Opt 2'
            p = panel(int(ImageDraw.Draw(ov).textlength(s, font=f) + 60), 64, (150, 20, 20), 0.95, 32); ImageDraw.Draw(p).text((p.size[0] / 2, 32), s, font=f, fill=WHITE, anchor='mm')
            put(ov, p, W - 1200 - 48 + (1200 - p.size[0]) / 2, 112 + 500 + 40, ease((dt - 8.6) / 0.6) * oo)
    # fly-through
    if FLY0 <= t < FLY1 + 1:
        c = ch(t); o = fade(t, FLY0 + 0.2, FLY1 + 0.5, 0.8, 0.8); pz_ = pause_at(t)
        o_live = o if not pz_ else o * ((1 - ease(pz_[1] / 0.5)) + ease((pz_[1] - pz_[2] + 0.5) / 0.5))
        live_hud(ov, c, o_live, P)
        items = []
        for l in SC['labels']:
            k = l['kind']
            if k == 'km' and l['ch'] <= c + 0.02: items.append((l['id'], l['id'].upper(), 'km', 46, ease((c - l['ch'] + 0.3) / 0.3)))
            if k == 'nx' and l['ch'] <= c + 0.05 and l['ch'] > c - 1.2:
                items.append((l['id'], ('Med N xing' if l['med'] else 'N xing') + f" CH {l['ch']:.2f}", 'nx', 64, ease((c - l['ch'] + 0.05) / 0.12) * (1 - ease((c - l['ch'] - 0.9) / 0.3))))
            if k == 'crest' and c > l['ch'] - 0.5 and c < l['ch'] + 2.5:
                nm = (f"Ridge crest {l['z']:.0f} m" if VID == 1 else (f"Saddle {l['z']:.0f} m" if l['id'] == 'Saddle' else 'Nullah bed descent'))
                items.append((l['id'], nm, 'crest', 120, ease((c - l['ch'] + 0.5) / 0.2)))
        items.append(('Haryan BOO', 'Haryan BOO', 'post', 110, ease((c - LEN + 0.7) / 0.3)))
        if VID == 2: items.append(('Opt 1 crest', 'Opt 1 – recced tr', 'ghost', 70, 1))
        items.sort(key=lambda it: {'post': 0, 'crest': 1, 'nx': 2, 'km': 3, 'ghost': 4}.get(it[2], 5))
        labels(ov, cam, items, o_live, P)
    # detail pauses
    for a, b, k in PAUSES[1:]:
        if a <= t < b + 0.2:
            dt = t - a; oo = 1 - ease((t - b + 0.7) / 0.6); card, phs = CARDS[k]
            put(ov, card, 48, 120, ease((dt - 0.4) / 0.6) * oo)
            if phs:
                x = 48 + card.size[0] + 40
                for j, ph_ in enumerate(phs):
                    u = ease((dt - 1.0 - 0.7 * j) / 0.7)
                    if len(phs) == 1: put(ov, ph_, x, 120 + (1 - u) * 40, u * oo)
                    else: put(ov, ph_, x + j * (ph_.size[0] - 10 if len(phs) == 3 else ph_.size[0] + 30), 120 + (1 - u) * 60 + (j % 2) * 40, u * oo, glow=False)
            elif k == 'nullah':
                put(ov, PROF_PANEL, W - 1200 - 48, 470, ease((dt - 1.0) / 0.7) * oo)
    # grade overview (side panels)
    if GR0 <= t < FIN + 1:
        o = fade(t, GR0 + 1, FIN + 0.6, 0.8, 0.6)
        put(ov, GRADE_CARD, 40, 112, o); put(ov, GRADE_LEG, 40, 112 + GRADE_CARD.size[1] + 20, o)
        P.rects += [(40, 112, 600, 112 + GRADE_CARD.size[1] + 20 + 226)]
        it = [('B-3 Post', 'B-3 Post', 'post', 90, 1), ('Haryan BOO', 'Haryan BOO', 'post', 90, 1)]
        it += [('Ridge crest', 'Ridge crest 247 m', 'crest', 120, 1)] if VID == 1 else [('Saddle', f"Saddle {R2['elev_max']:.0f} m", 'crest', 120, 1), ('Opt 1 crest', 'Opt 1 crest 247 m', 'ghost', 80, 1)]
        labels(ov, cam, it, o, P)
    # finale – everything in side columns
    if t >= FIN + 0.5:
        L0 = FIN + 1; Lx, Rx = 40, W - 640
        if VID == 1:
            put(ov, CMP, Lx, 110, fade(t, L0, DUR - 6.4, 0.8, 0.6))
            put(ov, PLANT, Rx, 110, fade(t, L0 + 8, DUR - 0.8, 0.8, 0.8)); put(ov, FLEET, Rx, 110 + PLANT.size[1] + 24, fade(t, L0 + 9, DUR - 0.8, 0.8, 0.8))
            put(ov, CONCL, Lx, 110, fade(t, DUR - 6, DUR - 0.8, 0.8, 0.8))
        else:
            put(ov, CMP, Lx, 110, fade(t, L0, DUR - 0.8, 0.8, 0.8))
            put(ov, PLANT, Rx, 110, fade(t, L0 + 6, DUR - 11.2, 0.8, 0.6)); put(ov, FLEET, Rx, 110 + PLANT.size[1] + 24, fade(t, L0 + 7, DUR - 11.2, 0.8, 0.6))
            put(ov, CONCL, Rx, 110, fade(t, DUR - 10.6, DUR - 0.8, 0.8, 0.8))
    footer(ov, 1 - ease((t - DUR + 1.5) / 1.0))
    base.alpha_composite(ov)
    if t > DUR - 1.4: base = Image.blend(base, Image.new('RGBA', (W, H), (0, 12, 40, 255)), ease((t - DUR + 1.4) / 1.4))
    return np.asarray(base.convert('RGB'))

if __name__ == '__main__':
    cams = json.load(open(args.src.replace('.mp4', '_cams.json')))
    if args.stills:
        for s in args.stills.split(','):
            t = float(s); f = int(round(t * FPS))
            fr = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', args.src, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
            img = np.frombuffer(fr, np.uint8).reshape(H, W, 3)
            Image.fromarray(compose(t, img, cams[min(f, len(cams) - 1)])).save(f'{args.out}_{t:06.2f}.jpg', quality=90); print('hud still', t)
        sys.exit()
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', args.src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', args.out], stdin=subprocess.PIPE)
    for f in range(len(cams)):
        fr = dec.stdout.read(W * H * 3)
        if len(fr) < W * H * 3: break
        enc.stdin.write(compose(f / FPS, np.frombuffer(fr, np.uint8).reshape(H, W, 3), cams[f]).tobytes())
        if f % 150 == 0: print('hud', f, flush=True)
    enc.stdin.close(); enc.wait()
