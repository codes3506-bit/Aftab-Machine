"""HUD / graphics pass: composites titles, labels, data panels and photos over the terrain render.
usage: hud.py TERRAIN.mp4 OUT.mp4 [--stills t1,t2]   (font + logos configurable below)
"""
import sys, json, math, subprocess, argparse, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, '/home/user/recce/work')
from timeline import *

ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--stills', default='')
args = ap.parse_args()
W, H = 1920, 1080

# ---------- assets (swap here) ----------
FD = '/home/user/recce/assets'
def fpath(name, fallback):
    p = f'{FD}/{name}'
    return p if os.path.exists(p) else fallback
F_REG = fpath('Candara.ttf', '/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf')
F_BOLD = fpath('Candarab.ttf', '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf')
F_IT = fpath('Candarai.ttf', '/usr/share/fonts/truetype/crosextra/Carlito-Italic.ttf')
F_BI = fpath('Candaraz.ttf', '/usr/share/fonts/truetype/crosextra/Carlito-BoldItalic.ttf')
LOGO_L = f'{FD}/logo_23eb.png'; LOGO_R = f'{FD}/logo_44div.png'
_fc = {}
def F(sz, w='r'):
    k = (sz, w)
    if k not in _fc: _fc[k] = ImageFont.truetype({'r': F_REG, 'b': F_BOLD, 'i': F_IT, 'bi': F_BI}[w], sz)
    return _fc[k]

NAVY = (0, 32, 96); NAVY2 = (8, 22, 58); GOLD = (255, 197, 26); WHITE = (255, 255, 255); GREY = (200, 208, 222)
RED = (232, 40, 40); BLUE = (30, 108, 255); GREEN = (16, 200, 90); MAG = (190, 70, 255); ORANGE = (255, 150, 30); YEL = (255, 230, 60)
WCOL = {0: BLUE, 1: RED, 2: GREEN}; WNAME = {0: 'Levelling (new fmn)', 1: 'Cut & fill (hy const – rock)', 2: 'Nullah filling'}

A = json.load(open(f'{R}/work/analysis.json')); RES = A['res']
CH = np.array(A['CH']); Z = np.array(A['Z']); TYP = SC['track']['typ']; G50 = np.array(SC['track']['g'])
POL1 = json.load(open(f'{R}/work/pol_recce.json')); POLF = json.load(open(f'{R}/work/pol_fleet.json'))
NULL = [l for l in SC['labels'] if l['kind'] == 'nx']

def ease(x): return smooth(x)
def fade(t, a, b, fi=0.6, fo=0.6):
    if t < a or t > b: return 0.0
    return min(1.0, (t - a) / fi if fi else 1, (b - t) / fo if fo else 1)

# ---------- primitives ----------
def panel(w, h, bg=NAVY2, alpha=0.9, r=16, border=GOLD, bw=0):
    im = Image.new('RGBA', (w, h), bg + (255,))
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=int(255 * alpha))
    im.putalpha(m)
    if bw:
        d = ImageDraw.Draw(im); d.rounded_rectangle((0, 0, w - 1, h - 1), r, outline=border + (255,), width=bw)
    return im
def shadowed(im, off=8, blur=14, op=0.55):
    w, h = im.size; s = Image.new('RGBA', (w + 4 * blur, h + 4 * blur), (0, 0, 0, 0))
    a = im.split()[3].point(lambda v: int(v * op)); sh = Image.new('RGBA', im.size, (0, 0, 0, 255)); sh.putalpha(a)
    s.alpha_composite(sh, (2 * blur, 2 * blur + off)); s = s.filter(ImageFilter.GaussianBlur(blur))
    s.alpha_composite(im, (2 * blur, 2 * blur)); return s, 2 * blur
def opacity(im, o):
    if o >= 0.999: return im
    im = im.copy(); a = im.split()[3].point(lambda v: int(v * o)); im.putalpha(a); return im
def put(base, im, x, y, o=1.0, sh=True):
    if o <= 0.003: return
    if sh: im, pad = shadowed(im)
    else: pad = 0
    base.alpha_composite(opacity(im, o), (int(x - pad), int(y - pad)))
def tw(d, s, f): return d.textlength(s, font=f)

# ---------- logos ----------
def logo(path, txt, sub):
    if os.path.exists(path):
        im = Image.open(path).convert('RGBA'); s = 118 / max(im.size); return im.resize((int(im.size[0] * s), int(im.size[1] * s)), Image.LANCZOS)
    S = 4; n = 118 * S; im = Image.new('RGBA', (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, n - 1, n - 1), fill=GOLD + (255,)); d.ellipse((5 * S, 5 * S, n - 5 * S, n - 5 * S), fill=NAVY + (255,))
    d.ellipse((10 * S, 10 * S, n - 10 * S, n - 10 * S), outline=GOLD + (255,), width=2 * S)
    f = F(34 * S, 'b'); d.text((n / 2, n / 2 - 8 * S), txt, font=f, fill=WHITE, anchor='mm')
    d.text((n / 2, n / 2 + 24 * S), sub, font=F(14 * S, 'b'), fill=GOLD, anchor='mm')
    return im.resize((118, 118), Image.LANCZOS)
LOGOS = (logo(LOGO_L, '23', 'EB'), logo(LOGO_R, '44', 'DIV'))
TITLE = 'Recce Altn Tr Const - B3 to Haryaan BOO'

def title_big(o, t):
    """centre title with logos either side"""
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    f = F(76, 'b'); d0 = ImageDraw.Draw(ov); tl = tw(d0, TITLE, f)
    bw = int(tl + 2 * 118 + 160); bh = 190
    p = panel(bw, bh, NAVY, 0.9, 22, GOLD, 3); d = ImageDraw.Draw(p)
    d.text((bw / 2, bh / 2 - 4), TITLE, font=f, fill=WHITE, anchor='mm')
    u = ease((t - 1.4) / 1.2); lw = int(tl * u)
    d.rectangle((bw / 2 - lw / 2, bh / 2 + 48, bw / 2 + lw / 2, bh / 2 + 52), fill=GOLD)
    p.alpha_composite(LOGOS[0], (36, (bh - 118) // 2)); p.alpha_composite(LOGOS[1], (bw - 36 - 118, (bh - 118) // 2))
    s = 0.92 + 0.08 * ease(t / 1.6)
    p = p.resize((int(bw * s), int(bh * s)), Image.LANCZOS)
    put(ov, p, (W - p.size[0]) / 2, (H - p.size[1]) / 2 - 40, o)
    return ov

def topbar():
    bh = 74; p = Image.new('RGBA', (W, bh), (0, 0, 0, 0))
    g = Image.new('RGBA', (W, bh), NAVY + (255,)); m = Image.linear_gradient('L').rotate(0).resize((W, bh))
    m = Image.new('L', (W, bh), 228); g.putalpha(m); p.alpha_composite(g)
    d = ImageDraw.Draw(p); d.rectangle((0, bh - 3, W, bh), fill=GOLD)
    sl = LOGOS[0].resize((60, 60), Image.LANCZOS); sr = LOGOS[1].resize((60, 60), Image.LANCZOS)
    p.alpha_composite(sl, (18, 6)); p.alpha_composite(sr, (W - 78, 6))
    d.text((W / 2, bh / 2 - 1), TITLE, font=F(40, 'b'), fill=WHITE, anchor='mm')
    return p
TOPBAR = topbar()

FOOT = 'Imagery © Esri, Maxar, Earthstar Geographics  ·  Terrain: Copernicus GLO-30 DEM  ·  Alignment, strata & N xings: KMZ (recce 4 Nov 26)  ·  Vertical exaggeration ×1.5  ·  Chainage scaled to 9 km LU recce'
def footer(ov, o):
    d = ImageDraw.Draw(ov); f = F(17, 'i'); x = W / 2; y = H - 16
    d.text((x + 1, y + 1), FOOT, font=f, fill=(0, 0, 0, int(200 * o)), anchor='mm'); d.text((x, y), FOOT, font=f, fill=(235, 235, 235, int(235 * o)), anchor='mm')

# ---------- labels ----------
KIND = {'post': (RED, WHITE, 30), 'place': (NAVY, WHITE, 26), 'khor': ((20, 20, 20), YEL, 24), 'road': (RED, WHITE, 24),
        'km': ((255, 255, 255), NAVY, 20), 'nx': (YEL, (0, 0, 0), 19), 'crest': (MAG, WHITE, 26)}
def pill(ov, x, y, txt, kind, o, lift=70, it=False):
    if o <= 0.01: return
    bg, fg, sz = KIND[kind]; d = ImageDraw.Draw(ov)
    f = F(sz, 'bi' if it else 'b'); w_ = tw(d, txt, f) + 24; h_ = sz + 16
    a = int(255 * o)
    ly = y - lift
    d.line((x, y, x, ly), fill=(255, 255, 255, a), width=2)
    if kind == 'nx':
        d.polygon([(x, y - 14), (x - 10, y + 4), (x + 10, y + 4)], fill=YEL + (a,), outline=(0, 0, 0, a))
    else:
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=bg + (a,), outline=(255, 255, 255, a), width=2)
    d.rounded_rectangle((x - w_ / 2, ly - h_, x + w_ / 2, ly), 8, fill=bg + (a,), outline=(255, 255, 255, int(a * 0.8)), width=2)
    d.text((x, ly - h_ / 2), txt, font=f, fill=fg + (a,), anchor='mm')

def label_set(ov, cam, items, o):
    for lid, txt, kind, lift, t_on in items:
        if lid not in cam['L']: continue
        x, y, vis = cam['L'][lid]
        if not vis and kind not in ('post',): continue
        pill(ov, x, y, txt, kind, o * t_on, lift, it=(kind == 'khor'))

# ---------- elevation profile ----------
def profile_img(w, h, big=True):
    S = 2; im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ml, mr, mt, mb = (90 * S, 30 * S, 30 * S, 62 * S) if big else (54 * S, 14 * S, 10 * S, 34 * S)
    pw, ph = w * S - ml - mr, h * S - mt - mb
    z0, z1 = 60, 260
    X = lambda c: ml + c / 9.0 * pw; Y = lambda z: mt + (1 - (z - z0) / (z1 - z0)) * ph
    fs = F((19 if big else 15) * S, 'r')
    for z in range(60, 261, 50):
        d.line((ml, Y(z), ml + pw, Y(z)), fill=(255, 255, 255, 50), width=S); d.text((ml - 10 * S, Y(z)), f'{z}', font=fs, fill=GREY, anchor='rm')
    for c in range(0, 10):
        d.line((X(c), mt + ph, X(c), mt + ph + 6 * S), fill=GREY, width=S); d.text((X(c), mt + ph + 9 * S), f'{c}', font=fs, fill=GREY, anchor='mt')
    # steep shading (>14 % over 50 m)
    st = np.abs(G50) > 0.14
    for i in range(len(CH) - 1):
        if st[i]: d.rectangle((X(CH[i]), mt, X(CH[i + 1]) + 1, mt + ph), fill=(255, 40, 40, 46))
    # fill under curve by work type
    for i in range(len(CH) - 1):
        c = WCOL[TYP[i]]
        d.polygon([(X(CH[i]), Y(Z[i])), (X(CH[i + 1]), Y(Z[i + 1])), (X(CH[i + 1]), mt + ph), (X(CH[i]), mt + ph)], fill=c + (150,))
    pts = [(X(c), Y(z)) for c, z in zip(CH, Z)]
    d.line(pts, fill=(255, 255, 255, 255), width=4 * S if big else 3 * S, joint='curve')
    if big:
        d.text((ml + pw / 2, h * S - 8 * S), 'Chainage (km)', font=F(20 * S, 'r'), fill=GREY, anchor='mb')
        d.text((ml - 10 * S, mt - 14 * S), 'Elev (m)', font=F(19 * S, 'r'), fill=GREY, anchor='rb')
        i = int(np.argmax(Z)); cx, cy = X(CH[i]), Y(Z[i])
        d.ellipse((cx - 7 * S, cy - 7 * S, cx + 7 * S, cy + 7 * S), fill=MAG + (255,))
        d.text((cx + 12 * S, cy - 6 * S), f'Ridge crest {Z[i]:.0f} m (Ch {CH[i]:.2f})', font=F(19 * S, 'b'), fill=WHITE, anchor='lb')
        d.text((X(0.05), Y(Z[0]) - 40 * S), f'B-3  {Z[0]:.0f} m', font=F(18 * S, 'b'), fill=WHITE, anchor='lb')
        d.text((X(8.95), Y(Z[-1]) - 16 * S), f'Haryan BOO  {Z[-1]:.0f} m', font=F(18 * S, 'b'), fill=WHITE, anchor='rb')
    im = im.resize((w, h), Image.LANCZOS)
    return im, (ml / S, mt / S, pw / S, ph / S, z0, z1)

# ---------- static panels ----------
def text_panel(w, title, rows, sub=None, title_col=GOLD, fs=26, rowh=40, bg=NAVY2):
    h = 70 + (34 if sub else 0) + rowh * len(rows) + 20
    p = panel(w, h, bg, 0.92, 16, GOLD, 2); d = ImageDraw.Draw(p)
    d.text((24, 18), title, font=F(32, 'b'), fill=title_col)
    y = 62
    if sub: d.text((24, y), sub, font=F(22, 'i'), fill=GREY); y += 34
    for r in rows:
        if isinstance(r, tuple) and len(r) == 3:
            k, v, c = r
        elif isinstance(r, tuple): k, v = r; c = WHITE
        else: k, v, c = r, None, WHITE
        if v is None:
            d.ellipse((26, y + 13, 36, y + 23), fill=GOLD); d.text((48, y + 18), k, font=F(fs, 'r'), fill=c, anchor='lm')
        else:
            d.text((26, y + 18), k, font=F(fs, 'r'), fill=GREY, anchor='lm'); d.text((w - 24, y + 18), v, font=F(fs, 'b'), fill=c, anchor='rm')
        y += rowh
    return p

R_ = RES
LEN_KM = {'level': 4.06, 'cutfill': 3.93, 'nullah': 1.01}   # as per KMZ (Ser a)
SCOPE = text_panel(600, 'SCOPE OF WORK – RECCE', [
    ('Tr length (LU recce)', '9.0 km'), ('Measured on imagery', f"{R_['len_img_km']:.2f} km"),
    ('Levelling (new fmn)', f"{LEN_KM['level']:.2f} km", (120, 170, 255)), ('Cut & fill (hy const – rock)', f"{LEN_KM['cutfill']:.2f} km", (255, 110, 110)),
    ('Nullah filling', f"{LEN_KM['nullah']:.2f} km", (90, 230, 140)), ('N xings (minor / medium)', '17  (13 / 4)'),
    ('Hy const areas (LU marking)', '2'), ('Strata', 'Gravel + mixed / rock')], sub='Ser a – B-3 to Haryan BOO (442 Bde)')
STATS = text_panel(600, 'TERRAIN – WHAT THE GROUND SAYS', [
    ('Elevation range', f"{R_['elev_min']:.0f} – {R_['elev_max']:.0f} m"), ('Total climb / descent', f"{R_['climb_m']:.0f} m / {R_['descent_m']:.0f} m"),
    ('Max grade (over 100 m)', '26.6 %', (255, 110, 110)), ('Steepest pitch (over 50 m)', '45 %', (255, 110, 110)),
    ('Length steeper than 1:10', f"{R_['len_gt10_km']:.2f} km"), ('Length steeper than 1:7', f"{R_['len_gt14_km']:.2f} km", (255, 170, 80)),
    ('Critical pass', 'Ch 3.0 – 5.3 km', GOLD)])
PROF_BIG, PB = profile_img(1160, 420)
def prof_panel():
    p = panel(1200, 500, NAVY2, 0.92, 16, GOLD, 2); d = ImageDraw.Draw(p)
    d.text((24, 16), 'ELEVATION PROFILE  (B-3 → Haryan BOO)', font=F(32, 'b'), fill=GOLD)
    p.alpha_composite(PROF_BIG, (20, 64))
    x = 640
    for k, c in ((0, BLUE), (1, RED), (2, GREEN)):
        d.rectangle((x, 28, x + 26, 40), fill=c); d.text((x + 34, 34), WNAME[k].split(' (')[0], font=F(20, 'r'), fill=WHITE, anchor='lm'); x += 34 + tw(d, WNAME[k].split(' (')[0], F(20, 'r')) + 26
    d.rectangle((x, 26, x + 26, 42), fill=(120, 40, 40)); d.text((x + 34, 34), '>1:7', font=F(20, 'r'), fill=WHITE, anchor='lm')
    return p
PROF_PANEL = prof_panel()

# photos
PH = {k: Image.open(f'{R}/photos/img{k:02d}.jpeg').convert('RGB') for k in (3, 4, 5, 6, 7)}
def polaroid(k, cap, h=560, rot=0):
    im = PH[k]; s = h / im.size[1]; im = im.resize((int(im.size[0] * s), h), Image.LANCZOS)
    w_ = im.size[0] + 24; h_ = h + 74
    p = Image.new('RGBA', (w_, h_), (250, 250, 246, 255)); p.paste(im, (12, 12))
    d = ImageDraw.Draw(p); d.text((w_ / 2, h + 44), cap, font=F(22, 'bi'), fill=(20, 20, 30), anchor='mm')
    if rot: p = p.rotate(rot, Image.BICUBIC, expand=True)
    return p

ASC_CARD = text_panel(700, 'Ch 3.0 – 4.05 km  ·  ASCENT TO RIDGE', [
    'Climb 187 → 247 m in about 1 km', 'Pitches of 35 – 41 % (over 50 m)', 'Side slopes up to 26°, loose scree on rock',
    'LU hy const areas: Ch 2.6–3.3 & 4.0–5.9', 'Rock strata – excavator with hy breaker req', 'Grade cuts up to 15.7 m deep to get 1:7'],
    sub='Ground recce – 4 Nov 26', fs=25)
CREST_CARD = text_panel(700, 'Ch 4.05 km  ·  RIDGE CREST 247 m', [
    'Descent 100 m in < 1 km on far side', 'Steepest pitch 45 % (over 50 m)', 'Narrow rock gorge – foot mov only at present',
    'Recce party needed rope over rock slabs', 'Massive rock – breaking, not dozing', '≈ 48,500 cu M rock to cut, Ch 3.0 – 5.0 alone'],
    sub='Ground recce – 4 Nov 26', fs=25)
ASC_PH = [polaroid(3, 'Loose scree gully – ascent', 520, 3), polaroid(6, 'V-gully, rock & scree slopes', 520, -2.5)]
CREST_PH = [polaroid(4, 'Recce party in rock gorge', 470, 2.5), polaroid(7, 'Rope descent over rock slabs', 470, -2), polaroid(5, 'Narrow rock gorge on alignment', 470, 1.5)]

GRADE_CARD = text_panel(600, 'SLOPE ANALYSIS – CURRENT TR', [
    ('Steeper than 1:20 (5 %)', ''), ('Steeper than 1:10', f"{R_['len_gt10_km']:.2f} km"), ('Steeper than 1:7', f"{R_['len_gt14_km']:.2f} km", (255, 170, 80)),
    ('Steeper than 1:5', f"{R_['len_gt20_km']:.2f} km", (255, 110, 110)), ('Max grade (100 m)', '26.6 %', (255, 110, 110)), ('Max pitch (50 m)', '45 %', (255, 110, 110))], fs=25)
def grade_legend():
    p = panel(600, 230, NAVY2, 0.92, 16, GOLD, 2); d = ImageDraw.Draw(p)
    d.text((24, 16), 'TR GRADE', font=F(28, 'b'), fill=GOLD); d.text((310, 16), 'GROUND SLOPE', font=F(28, 'b'), fill=GOLD)
    rows = [((64, 240, 115), '< 5 %'), ((255, 235, 64), '5 – 10 %'), ((255, 148, 26), '10 – 14 %'), ((255, 40, 36), '14 – 25 %'), ((190, 64, 255), '> 25 %')]
    for i, (c, s) in enumerate(rows):
        y = 62 + i * 32; d.rectangle((26, y, 70, y + 18), fill=c); d.text((84, y + 9), s, font=F(22, 'r'), fill=WHITE, anchor='lm')
        if i: d.rectangle((312, y, 356, y + 18), fill=c); d.text((370, y + 9), s, font=F(22, 'r'), fill=WHITE, anchor='lm')
    return p
GRADE_LEG = grade_legend()

def table_panel(w, title, head, rows, colw, sub=None, fs=27, rowh=50, hl=None):
    h = 78 + (36 if sub else 0) + rowh * (len(rows) + 1) + 24
    p = panel(w, h, NAVY2, 0.94, 16, GOLD, 2); d = ImageDraw.Draw(p)
    d.text((26, 18), title, font=F(34, 'b'), fill=GOLD); y = 70
    if sub: d.text((26, y), sub, font=F(22, 'i'), fill=GREY); y += 36
    xs = np.cumsum([20] + colw)
    d.rectangle((16, y, w - 16, y + rowh), fill=(180, 20, 20))
    for j, s in enumerate(head):
        d.text(((xs[j] + 12) if j == 0 else (xs[j] + xs[j + 1]) / 2, y + rowh / 2), s, font=F(fs, 'b'), fill=WHITE, anchor='lm' if j == 0 else 'mm')
    y += rowh
    for i, r in enumerate(rows):
        bg = (30, 44, 84) if i % 2 == 0 else (20, 32, 66)
        if hl is not None and i in hl: bg = (90, 70, 10)
        d.rectangle((16, y, w - 16, y + rowh), fill=bg)
        for j, s in enumerate(r):
            col = WHITE if j < 2 else (255, 220, 90)
            if j == 0: col = GREY
            d.text(((xs[j] + 12) if j == 0 else (xs[j] + xs[j + 1]) / 2, y + rowh / 2), s, font=F(fs, 'b' if j else 'r'), fill=col, anchor='lm' if j == 0 else 'mm')
        y += rowh
    return p

rock = R_['bench_m3'] + R_['grade_m3']
fl = {r['d']: r for r in POLF['rows']}; r1 = {r['d']: r for r in POL1['rows']}
exc_h = r1['Excavator (excavation)']['q']; doz_h = r1['Dozer']['q'] + r1['Dozer – dozing / disposal of cut rock']['q']
days1 = math.ceil(POL1['dur']); daysF = math.ceil(max(exc_h / (8 * 3), doz_h / (8 * 2)))
CMP = table_panel(1360, 'WORK ASSESSMENT  –  SLIDE (OPT 1)  vs  GROUND RECCE', ['', 'Slide – Opt 1', 'Recce – current tr', 'Factor'], [
    ['Rock cutting', '3.21 lakh cft', f'{rock * 35.32 / 1e5:.1f} lakh cft', f'× {rock * 35.32 / 321494:.1f}'],
    ['Excavator (hy breaker)', '268 hrs', f'{exc_h:,} hrs', f'× {exc_h / 268:.1f}'],
    ['Dozer', '300 hrs', f'{doz_h:,} hrs', f'× {doz_h / 300:.1f}'],
    ['POL', '19,660 lits', f"{POL1['total']:,} lits", f"× {POL1['total'] / 19660:.1f}"],
    ['Days (1 dozer + 1 exc)', '40', f'{days1}', f'× {days1 / 40:.1f}'],
    ['Days (3 exc + 2 dozers)', '–', f'{daysF}', '']],
    [400, 300, 330, 260], sub='Recce quantities from terrain model along KMZ alignment; POL & days by Div POL Calculator (current stds, 8 hr/day, 10 % margin)', hl=[3, 5])
def plant_panel():
    rows = [[r['d'].replace(' (excavation)', ' – rock cutting (hy breaker)'), f"{r['q']:,} {r['au']}", f"{r['rate']}", f"{r['l']:,}"] for r in POLF['rows']]
    rows.append(['TOTAL POL', '', '', f"{POLF['total']:,} lits"])
    p = table_panel(1180, 'PLT / EQPT, POL & TIME  (POL CALCULATOR)', ['Description', 'Qty', 'KMPL / LPH', 'Lits'], rows, [520, 210, 190, 220], hl=[len(rows) - 1], fs=25, rowh=44)
    return p
PLANT = plant_panel()
FLEET = text_panel(600, 'MACHINERY TO BE EMP', [
    ('Excavator c/w hy breaker', '3'), ('Dozer', '2'), ('FBT (plt mov, 300 km)', '5 trips'), ('Single / Double cabin', '1 / 1'), ('Civ trk (POL lift)', '6 trips'),
    ('Engr effort', f'{daysF} working days', GOLD), ('Total POL', f"{POLF['total']:,} lits", GOLD)], fs=25)
CONCL = text_panel(1360, 'ASSESSMENT', [
    'Marked tr crosses a 247 m rock ridge between Ch 3.0 and 5.3 km – grades of 26 – 45 % against 1:7 desirable',
    f'≈ {rock:,.0f} cu M of rock to be cut – about {rock * 35.32 / 321494:.0f} times the slide estimate',
    f'Const on current alignment: {POL1["total"]:,} lits POL; {days1} days with 1 dozer + 1 exc, or {daysF} days with 3 exc + 2 dozers',
    'Gorge sections need rock breaking / blasting – progress weather & flash-flood dependent (17 N xings)'], fs=27, rowh=46)

# ---------- live HUD (fly) ----------
STRIP, SB = profile_img(1000, 170, big=False)
def live_hud(ov, c, o):
    if o <= 0.01: return
    i = int(np.clip(np.searchsorted(CH, c), 0, len(CH) - 1))
    p = panel(1040, 200, NAVY2, 0.86, 14, GOLD, 2); p.alpha_composite(STRIP, (20, 18)); d = ImageDraw.Draw(p)
    ml, mt, pw, ph, z0, z1 = SB; x = 20 + ml + c / 9 * pw; y = 18 + mt + (1 - (Z[i] - z0) / (z1 - z0)) * ph
    d.line((x, 18 + mt, x, 18 + mt + ph), fill=GOLD, width=2); d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=GOLD, outline=WHITE, width=2)
    put(ov, p, 40, H - 200 - 48, o)
    q = panel(420, 260, NAVY2, 0.88, 14, GOLD, 2); d = ImageDraw.Draw(q)
    g = G50[i] * 100; gc = (64, 240, 115) if abs(g) < 5 else YEL if abs(g) < 10 else ORANGE if abs(g) < 14 else RED if abs(g) < 25 else MAG
    rows = [('CH', f'{c:5.2f} km', WHITE), ('ELEV', f'{Z[i]:.0f} m', WHITE), ('GRADE', f'{g:+.0f} %', gc)]
    for k, (a, b, col) in enumerate(rows):
        d.text((24, 30 + k * 54), a, font=F(26, 'b'), fill=GREY, anchor='lm'); d.text((396, 30 + k * 54), b, font=F(40, 'b'), fill=col, anchor='rm')
    t_ = TYP[i]; d.rectangle((24, 196, 52, 224), fill=WCOL[t_]); d.text((64, 210), WNAME[t_], font=F(26, 'b'), fill=WHITE, anchor='lm')
    put(ov, q, W - 420 - 40, 110, o)

# ---------- frame composer ----------
cams = None; CACHE = {}
def compose(t, frame, cam):
    base = Image.fromarray(frame).convert('RGBA')
    pz = pause_at(t)
    if pz:
        k, dt, dur = pz
        key = ('blur', k)
        if key not in CACHE:
            b = base.filter(ImageFilter.GaussianBlur(5)); dk = Image.new('RGBA', (W, H), (4, 10, 28, 140)); b.alpha_composite(dk); CACHE[key] = b
        u = ease(dt / 0.8) * (1 - ease((dt - dur + 0.8) / 0.8)); base = Image.blend(base, CACHE[key], u)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # vignette
    if 'vig' not in CACHE:
        v = Image.new('L', (W, H), 0); ImageDraw.Draw(v).ellipse((-260, -200, W + 260, H + 200), fill=255); v = v.filter(ImageFilter.GaussianBlur(160))
        vig = Image.new('RGBA', (W, H), (0, 0, 0, 255)); vig.putalpha(v.point(lambda a: int((255 - a) * 0.55))); CACHE['vig'] = vig
    base.alpha_composite(CACHE['vig'])
    # ---- title ----
    if t < 9.4:
        o = ease(t / 0.9) * (1 - ease((t - 8.3) / 0.9))
        ov.alpha_composite(title_big(o, t))
    else:
        o = ease((t - 8.8) / 0.8) * (1 - ease((t - 150.6) / 1.2))
        put(ov, opacity(TOPBAR, 1), 0, 0, o, sh=False)
    # ---- area orientation ----
    if 10 <= t < 27:
        o = fade(t, 10.5, 26.5, 0.8, 1.0); items = []
        seq = [('Keisher', 'Keisher', 'place', 80), ('B5', 'B5', 'place', 70), ('Darband', 'Darband', 'place', 80), ('CHW (N10)', 'CHW (N10)', 'road', 60),
               ('B-3 Post', 'B-3 Post', 'post', 90), ('B-1', 'B-1', 'place', 70), ('Haryan BOO', 'Haryan BOO', 'post', 150),
               ('Maneji K', 'Maneji K', 'khor', 50), ('Haryan K', 'Haryan K', 'khor', 50), ('Hatti K', 'Hatti K', 'khor', 50)]
        for n_, (lid, txt, kd, lf) in enumerate(seq): items.append((lid, txt, kd, lf, ease((t - 11 - n_ * 0.45) / 0.5)))
        label_set(ov, cam, items, o)
        card = text_panel(640, 'AREA ORIENTATION', [('Tr', 'B-3 Post → Haryan BOO'), ('Indicated by', '25 FF / 442 Bde'), ('Haryan – Keisher', '9 km'),
                         ('Keisher – B5 / Darband', '7 km / 5 km'), ('Alignment (LU recce)', '9 km'), ('Hy const areas (LU)', '2 (red dashed)')], fs=24, rowh=38)
        put(ov, card, 48, H - card.size[1] - 70, ease((t - 13) / 0.8) * fade(t, 13, 26.5, 0.01, 1.0))
    # ---- descend ----
    if 25 <= t < 33:
        o = fade(t, 27, 32.6, 0.6, 0.5)
        label_set(ov, cam, [('B-3 Post', 'B-3 Post  ·  Ch 0', 'post', 110, 1), ('Haryan BOO', 'Haryan BOO  ·  Ch 9', 'post', 110, 1)], o)
    # ---- brief pause ----
    if 32 <= t < 45.5:
        dt = t - 32
        oo = 1 - ease((t - 44.1) / 0.6)
        put(ov, SCOPE, 48, 112, ease((dt - 0.5) / 0.7) * oo)
        put(ov, STATS, 48, 112 + SCOPE.size[1] + 22, ease((dt - 1.6) / 0.7) * oo)
        put(ov, PROF_PANEL, W - 1200 - 48, 112, ease((dt - 2.6) / 0.7) * oo)
        if dt > 4:
            f = F(30, 'bi'); d = ImageDraw.Draw(ov); s = 'Commencing fly-through recce of the complete tr'
            a = int(255 * ease((dt - 8.6) / 0.6) * oo)
            p = panel(int(tw(d, s, f) + 60), 64, (150, 20, 20), 0.95, 32); ImageDraw.Draw(p).text((p.size[0] / 2, 32), s, font=f, fill=WHITE, anchor='mm')
            put(ov, p, W - 1200 - 48 + (1200 - p.size[0]) / 2, 112 + 500 + 40, a / 255)
    # ---- fly-through ----
    if 45 <= t < 116:
        c = ch(t); o = fade(t, 45.2, 115.5, 0.8, 0.8)
        pz_ = pause_at(t); o_live = o * (0.0 if pz_ else 1.0)
        if pz_:
            k_, dt_, du_ = pz_; o_live = o * (1 - ease(dt_ / 0.5)) + o * ease((dt_ - du_ + 0.5) / 0.5)
        live_hud(ov, c, o_live)
        items = []
        for l in SC['labels']:
            if l['kind'] == 'km' and l['ch'] <= c + 0.02: items.append((l['id'], l['id'], 'km', 46, ease((c - l['ch'] + 0.3) / 0.3)))
            if l['kind'] == 'nx' and l['ch'] <= c + 0.05 and l['ch'] > c - 1.2:
                items.append((l['id'], ('Med N xing' if l['med'] else 'N xing') + f" Ch {l['ch']:.2f}", 'nx', 64, ease((c - l['ch'] + 0.05) / 0.12) * (1 - ease((c - l['ch'] - 0.9) / 0.3))))
            if l['kind'] == 'crest' and c > l['ch'] - 0.5: items.append((l['id'], f"Ridge crest {l['z']:.0f} m", 'crest', 120, ease((c - l['ch'] + 0.5) / 0.2)))
        items.append(('Haryan BOO', 'Haryan BOO', 'post', 110, ease((c - 8.3) / 0.3)))
        label_set(ov, cam, items, o_live)
    # ---- ascent pause ----
    for (a, b, card, phs) in ((63, 74, ASC_CARD, ASC_PH), (81, 93, CREST_CARD, CREST_PH)):
        if a <= t < b + 0.2:
            dt = t - a; oo = 1 - ease((t - b + 0.7) / 0.6)
            put(ov, card, 48, 120, ease((dt - 0.4) / 0.6) * oo)
            x = 48 + card.size[0] + 40
            for j, ph_ in enumerate(phs):
                u = ease((dt - 1.0 - 0.7 * j) / 0.7)
                put(ov, ph_, x + j * (ph_.size[0] - 10 if len(phs) == 3 else ph_.size[0] + 30), 120 + (1 - u) * 60 + (j % 2) * 40, u * oo)
    # ---- grade analysis ----
    if 116 <= t < 129:
        o = fade(t, 117, 128.6, 0.8, 0.6)
        put(ov, GRADE_CARD, 48, 112, o); put(ov, GRADE_LEG, 48, 112 + GRADE_CARD.size[1] + 20, o)
        label_set(ov, cam, [('Ridge crest', 'Ridge crest 247 m', 'crest', 120, 1), ('B-3 Post', 'B-3 Post', 'post', 90, 1), ('Haryan BOO', 'Haryan BOO', 'post', 90, 1)], o)
    # ---- finale ----
    if t >= 128.5:
        o1 = fade(t, 129, 136.6, 0.8, 0.6); put(ov, CMP, (W - CMP.size[0]) / 2, 150, o1)
        o2 = fade(t, 137, 144.6, 0.8, 0.6); put(ov, PLANT, 48, 130, o2); put(ov, FLEET, W - FLEET.size[0] - 48, 130, o2)
        o3 = fade(t, 145, 151.2, 0.8, 1.0); put(ov, CONCL, (W - CONCL.size[0]) / 2, 260, o3)
    footer(ov, 1 - ease((t - 150.5) / 1.0))
    base.alpha_composite(ov)
    if t > 150.6:
        k = ease((t - 150.6) / 1.4); base = Image.blend(base, Image.new('RGBA', (W, H), (0, 12, 40, 255)), k)
    return np.asarray(base.convert('RGB'))

if __name__ == '__main__':
    cams = json.load(open(args.src.replace('.mp4', '_cams.json')))
    if args.stills:
        for s in args.stills.split(','):
            t = float(s); f = int(round(t * FPS))
            fr = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', args.src, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
            img = np.frombuffer(fr, np.uint8).reshape(H, W, 3)
            Image.fromarray(compose(t, img, cams[min(f, len(cams) - 1)])).save(f'{args.out}_{t:06.2f}.jpg', quality=90)
            print('hud still', t)
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
