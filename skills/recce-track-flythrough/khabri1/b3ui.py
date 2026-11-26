"""B3-Haryaan visual language (ported from scripts/hud2.py) at any resolution.
Navy top bar with gold rule, navy panels with gold glow, Carlito (Candara metric-compatible), coloured label boxes,
B3 live HUD (CH / ELEV / GRADE) and profile strip. Layout is written in 1920x1080 units and scaled by S."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CF = '/usr/share/fonts/truetype/crosextra/'
_fc = {}
S = 1.0; W = 1920; H = 1080
def init(w, h):
    global S, W, H; W, H = w, h; S = w / 1920.0
def F(sz, w='r'):
    k = (int(sz * S), w)
    if k not in _fc: _fc[k] = ImageFont.truetype(CF + {'r': 'Carlito-Regular.ttf', 'b': 'Carlito-Bold.ttf', 'i': 'Carlito-Italic.ttf', 'bi': 'Carlito-BoldItalic.ttf'}[w], k[0])
    return _fc[k]
def q(v): return int(round(v * S))

NAVY = (0, 32, 96); NAVY2 = (8, 22, 58); GOLD = (255, 197, 26); WHITE = (255, 255, 255); GREY = (200, 208, 222)
RED = (232, 40, 40); YEL = (255, 230, 60); GREEN = (16, 200, 90); BLUE = (30, 108, 255); AMBER = (255, 150, 30)


def panel_img(w, h, bg=NAVY2, alpha=0.9, r=16, border=GOLD, bw=0):
    w, h = int(w), int(h); k = 2; im = Image.new('RGBA', (w * k, h * k), bg + (255,))
    m = Image.new('L', (w * k, h * k), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w * k - 1, h * k - 1), q(r) * k, fill=int(255 * alpha)); im.putalpha(m)
    if bw: ImageDraw.Draw(im).rounded_rectangle((0, 0, w * k - 1, h * k - 1), q(r) * k, outline=border + (255,), width=max(1, q(bw)) * k)
    return im.resize((w, h), Image.LANCZOS)


def shadowed(im, glow=True):
    b = q(18); w, h = im.size; s = Image.new('RGBA', (w + 4 * b, h + 4 * b), (0, 0, 0, 0)); a = im.split()[3]
    sh = Image.new('RGBA', im.size, (0, 0, 0, 255)); sh.putalpha(a.point(lambda v: int(v * 0.5)))
    s.alpha_composite(sh, (2 * b, 2 * b + q(8))); s = s.filter(ImageFilter.GaussianBlur(q(14)))
    if glow:
        g = Image.new('RGBA', s.size, (0, 0, 0, 0)); gl = Image.new('RGBA', im.size, GOLD + (255,)); gl.putalpha(a.point(lambda v: 255 if v > 10 else 0))
        g.alpha_composite(gl, (2 * b, 2 * b)); g = g.filter(ImageFilter.GaussianBlur(q(9))); g.putalpha(g.split()[3].point(lambda v: int(v * 0.75))); s.alpha_composite(g)
    s.alpha_composite(im, (2 * b, 2 * b)); return s, 2 * b


def opacity(im, o):
    if o >= 0.999: return im
    im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * o))); return im


def put(base, im, x, y, o=1.0, sh=True, glow=True):
    if o <= 0.003: return
    pad = 0
    if sh: im, pad = shadowed(im, glow)
    base.alpha_composite(opacity(im, o), (int(x - pad), int(y - pad)))


def tw(s, f): return ImageDraw.Draw(Image.new('L', (1, 1))).textlength(s, font=f)


# ------------------------------------------------------------------ logos (user PPTX, slide order: 44 Div left, 23 KS right)
import os
_AD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
def badge(src, white_bg, size=150):
    k = 4; n = size * k; im = Image.new('RGBA', (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im); e = Image.open(src).convert('RGBA')
    if white_bg:   # crest on a white square -> white disc with gold ring
        d.ellipse((0, 0, n - 1, n - 1), fill=GOLD + (255,)); d.ellipse((4 * k, 4 * k, n - 4 * k, n - 4 * k), fill=(255, 255, 255, 255))
        a = np.asarray(e).copy(); wht = (a[..., :3].min(2) > 235)
        from scipy.ndimage import label as _lab
        lb, _ = _lab(wht); edge = set(np.unique(np.r_[lb[0], lb[-1], lb[:, 0], lb[:, -1]])) - {0}
        a[np.isin(lb, list(edge)), 3] = 0; e = Image.fromarray(a)
        sc = (n - 22 * k) / max(e.size); e = e.resize((int(e.size[0] * sc), int(e.size[1] * sc)), Image.LANCZOS)
        im.alpha_composite(e, ((n - e.size[0]) // 2, (n - e.size[1]) // 2 + 2 * k))
    else:          # emblem already a disc
        d.ellipse((0, 0, n - 1, n - 1), fill=GOLD + (255,))
        sc = (n - 8 * k) / max(e.size); e = e.resize((int(e.size[0] * sc), int(e.size[1] * sc)), Image.LANCZOS)
        im.alpha_composite(e, ((n - e.size[0]) // 2, (n - e.size[1]) // 2))
    return im
_LG = {}
def logos(sz):
    if sz not in _LG:
        if not os.path.exists(f'{_AD}/logo_44div.png'): _LG[sz] = None
        else: _LG[sz] = (badge(f'{_AD}/logo_44div.png', False).resize((sz, sz), Image.LANCZOS), badge(f'{_AD}/logo_23ks.png', True).resize((sz, sz), Image.LANCZOS))
    return _LG[sz]


# ------------------------------------------------------------------ bars
def topbar(base, title):
    bh = q(80); p = Image.new('RGBA', (W, bh), NAVY + (232,)); d = ImageDraw.Draw(p); d.rectangle((0, bh - q(3), W, bh), fill=GOLD)
    lg = logos(q(68))
    if lg: p.alpha_composite(lg[0], (q(16), q(6))); p.alpha_composite(lg[1], (W - q(16) - q(68), q(6)))
    d.text((W / 2, bh / 2 - q(1)), title, font=F(40, 'b'), fill=WHITE, anchor='mm'); base.alpha_composite(p)


def footer(base, txt, o=1.0):
    d = ImageDraw.Draw(base); f = F(17, 'i'); x = W / 2; y = H - q(16)
    d.text((x + 1, y + 1), txt, font=f, fill=(0, 0, 0, int(200 * o)), anchor='mm'); d.text((x, y), txt, font=f, fill=(235, 235, 235, int(235 * o)), anchor='mm')


def section(base, txt, col=GOLD, o=1.0, sub=None):
    """small chip under the top bar naming the current section"""
    f = F(26, 'b'); w = tw(txt, f) + q(40); h = q(46) if not sub else q(76)
    if sub: w = max(w, tw(sub, F(19, 'i')) + q(40))
    p = panel_img(w, h, NAVY2, 0.9, 10, col, 2); d = ImageDraw.Draw(p); d.text((q(20), q(10)), txt, font=f, fill=WHITE)
    if sub: d.text((q(20), q(44)), sub, font=F(19, 'i'), fill=GREY)
    put(base, p, q(24), q(98), o)


# ------------------------------------------------------------------ panels
def table_panel(title, rows, w=440, sub=None, vcol=WHITE, title_col=GOLD, lh=27, fs=19, accent=None):
    """rows: (label, value[, colour]). Returns RGBA panel image (B3 SCOPE OF WORK style)."""
    top = q(20) + q(30) + (q(24) if sub else 0); h = top + q(lh) * len(rows) + q(16)
    p = panel_img(q(w), h, NAVY2, 0.9, 16, accent or GOLD, 2 if accent else 0); d = ImageDraw.Draw(p)
    d.text((q(20), q(14)), title, font=F(24, 'b'), fill=title_col)
    if sub: d.text((q(20), q(46)), sub, font=F(16, 'i'), fill=GREY)
    for i, r in enumerate(rows):
        y = top + q(lh) * i; lab, val = r[0], r[1]; c = r[2] if len(r) > 2 else vcol
        d.text((q(20), y), lab, font=F(fs), fill=(225, 230, 240))
        d.text((q(w) - q(20), y), val, font=F(fs, 'b'), fill=c, anchor='ra')
    return p


def text_panel(title, lines, w=520, title_col=GOLD, fs=19, lh=27, accent=None):
    h = q(20) + q(34) + q(lh) * len(lines) + q(14); p = panel_img(q(w), h, NAVY2, 0.9, 16, accent or GOLD, 2 if accent else 0); d = ImageDraw.Draw(p)
    d.text((q(20), q(14)), title, font=F(24, 'b'), fill=title_col)
    for i, ln in enumerate(lines):
        c = (225, 230, 240); f = F(fs)
        if isinstance(ln, tuple): ln, c, f = ln[0], ln[1], F(fs, ln[2] if len(ln) > 2 else 'r')
        d.text((q(20), q(54) + q(lh) * i), ln, font=f, fill=c)
    return p


def photo_panel(img, title, caption, w=760, accent=GOLD, tag=None):
    """ground photo framed B3-style. img: PIL RGB."""
    iw = q(w) - q(28); ih = int(iw * img.size[1] / img.size[0])
    cap = caption if isinstance(caption, list) else [caption]
    h = q(52) + ih + q(14) + q(26) * len(cap) + q(14)
    p = panel_img(q(w), h, NAVY2, 0.92, 16, accent, 2); d = ImageDraw.Draw(p)
    d.text((q(14), q(12)), title, font=F(24, 'b'), fill=GOLD)
    ph = img.resize((iw, ih), Image.LANCZOS).convert('RGBA'); m = Image.new('L', ph.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, iw - 1, ih - 1), q(8), fill=255); ph.putalpha(m)
    p.alpha_composite(ph, (q(14), q(50)))
    if tag:
        f = F(17, 'b'); tw_ = tw(tag, f) + q(20); ImageDraw.Draw(p).rounded_rectangle((q(26), q(62), q(26) + tw_, q(62) + q(28)), q(6), fill=(0, 0, 0, 170))
        ImageDraw.Draw(p).text((q(36), q(65)), tag, font=f, fill=YEL)
    for i, c in enumerate(cap):
        col = (225, 230, 240); fw = 'r'
        if isinstance(c, tuple): c, col, fw = c[0], c[1], (c[2] if len(c) > 2 else 'r')
        d.text((q(16), q(50) + ih + q(12) + q(26) * i), c, font=F(18, fw), fill=col)
    return p


# ------------------------------------------------------------------ labels (B3 KIND boxes)
KIND = {'post': (RED, WHITE, 30), 'place': (NAVY, WHITE, 24), 'km': ((255, 255, 255), NAVY, 20), 'nx': (YEL, (0, 0, 0), 19),
        'crest': ((190, 70, 255), WHITE, 24), 'face': ((20, 20, 20), YEL, 21)}
def label(base, xy, txt, kind='place', lift=60, col=None, sub=None, o=1.0):
    bg, fg, fs = KIND[kind]
    if col is not None: bg, fg = col, (WHITE if sum(col) < 560 else (0, 0, 0))
    f = F(fs, 'b'); w = tw(txt, f) + q(22); h = q(fs + 14)
    if sub: fsub = F(fs * 0.62, 'b'); w = max(w, tw(sub, fsub) + q(22)); h += q(fs * 0.7)
    x, y = xy; bx = x - w / 2; by = y - q(lift) - h
    L = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.line((x, y, x, by + h), fill=(255, 255, 255, 230), width=max(1, q(2)))
    d.ellipse((x - q(5), y - q(5), x + q(5), y + q(5)), fill=bg + (255,), outline=(255, 255, 255, 255), width=max(1, q(2)))
    d.rounded_rectangle((bx + q(2), by + q(3), bx + w + q(2), by + h + q(3)), q(7), fill=(0, 0, 0, 110))
    d.rounded_rectangle((bx, by, bx + w, by + h), q(7), fill=bg + (245,), outline=(255, 255, 255, 230), width=max(1, q(1.5)))
    d.text((x, by + q(5)), txt, font=f, fill=fg, anchor='ma')
    if sub: d.text((x, by + q(fs + 8)), sub, font=fsub, fill=fg, anchor='ma')
    if o < 1: L.putalpha(L.getchannel('A').point(lambda v: int(v * o)))
    base.alpha_composite(L)


# ------------------------------------------------------------------ B3 live HUD + profile strip
def hud(base, ch, elev, grade_txt, grade_col, wlabel, wcol, o=1.0):
    w, h = q(270), q(150); p = panel_img(w, h, NAVY2, 0.9, 14); d = ImageDraw.Draw(p)
    for i, (a, v, c) in enumerate((('CH', ch, WHITE), ('ELEV', elev, WHITE), ('GRADE', grade_txt, grade_col))):
        y = q(12) + q(30) * i; d.text((q(16), y + q(6)), a, font=F(17, 'b'), fill=GREY); d.text((w - q(16), y), v, font=F(30, 'b'), fill=c, anchor='ra')
    d.rectangle((q(16), q(116), q(32), q(132)), fill=wcol); d.text((q(42), q(113)), wlabel, font=F(19), fill=WHITE)
    put(base, p, W - w - q(22), q(98), o)


def profile_strip(base, s_m, z_m, g_abs, frac, col, o=1.0, w=700, h=150, title=None):
    """elevation profile (m) along chainage, filled by grade class: <=1:10 blue, 1:10-1:7 amber, >1:7 red; cursor at frac"""
    pw, ph = q(w), q(h); p = panel_img(pw, ph, NAVY2, 0.9, 14); d = ImageDraw.Draw(p)
    gx0, gy0, gw, gh = q(46), q(14), pw - q(66), ph - q(40)
    zmin, zmax = 20, 160; L = s_m[-1]
    X = gx0 + np.asarray(s_m) / L * gw; Y = gy0 + gh - (np.asarray(z_m) - zmin) / (zmax - zmin) * gh
    for zl in (40, 80, 120, 160):
        yl = gy0 + gh - (zl - zmin) / (zmax - zmin) * gh; d.line((gx0, yl, gx0 + gw, yl), fill=(255, 255, 255, 40), width=1); d.text((gx0 - q(6), yl), str(zl), font=F(13), fill=GREY, anchor='rm')
    for i in range(len(X) - 1):
        g = g_abs[i]; c = BLUE if g <= 10 else (AMBER if g <= 100 / 7 else RED)
        d.polygon([(X[i], gy0 + gh), (X[i], Y[i]), (X[i + 1], Y[i + 1]), (X[i + 1], gy0 + gh)], fill=c + (220,))
    d.line(list(zip(X, Y)), fill=WHITE, width=max(1, q(2)))
    stp = 100 if L <= 1000 else (200 if L <= 2000 else 250)
    for k_ in range(0, int(L // stp) + 1):
        xx = gx0 + k_ * stp / L * gw; d.line((xx, gy0 + gh, xx, gy0 + gh + q(4)), fill=GREY, width=1)
        if k_ * stp <= L - stp * 0.6: d.text((xx, gy0 + gh + q(5)), f'{k_ * stp / 1000:.1f}', font=F(13), fill=GREY, anchor='ma')
    d.text((gx0 + gw, gy0 + gh + q(5)), f'{L / 1000:.2f} km', font=F(13, 'b'), fill=WHITE, anchor='ra')
    d.text((gx0 + gw - q(4), Y[-1] - q(6)), 'POST', font=F(13, 'b'), fill=GOLD, anchor='rb')
    xc = gx0 + frac * gw; d.line((xc, gy0, xc, gy0 + gh), fill=GOLD, width=max(1, q(2)))
    j = int(frac * (len(Y) - 1)); d.ellipse((xc - q(5), Y[j] - q(5), xc + q(5), Y[j] + q(5)), fill=GOLD)
    put(base, p, q(22), H - ph - q(40), o)


def legend_grade(base, o=1.0):
    items = [(BLUE, '≤ 1:10'), (AMBER, '1:10 – 1:7'), (RED, '> 1:7')]
    f = F(16, 'b'); w = sum(tw(t, f) + q(44) for _, t in items) + q(20); p = panel_img(w, q(32), NAVY2, 0.85, 8); d = ImageDraw.Draw(p); x = q(12)
    for c, t in items: d.rectangle((x, q(9), x + q(14), q(23)), fill=c); d.text((x + q(20), q(7)), t, font=f, fill=WHITE); x += tw(t, f) + q(44)
    put(base, p, q(22) + q(700) - w, H - q(150) - q(40) - q(40), o, sh=False)


def title_big(base, title, sub, o, t):
    f = F(70, 'b'); tl = tw(title, f); LS = q(150); bw = int(tl + 2 * LS + q(150)); bh = q(210) if sub else q(170)
    p = panel_img(bw, bh, NAVY, 0.92, 22, GOLD, 3); d = ImageDraw.Draw(p)
    lg = logos(LS)
    if lg: p.alpha_composite(lg[0], (q(30), (bh - LS) // 2)); p.alpha_composite(lg[1], (bw - q(30) - LS, (bh - LS) // 2))
    d.text((bw / 2, q(70)), title, font=f, fill=WHITE, anchor='mm')
    u = min(1, max(0, (t - 1.4) / 1.2)); u = u * u * (3 - 2 * u); lw = int(tl * u); d.rectangle((bw / 2 - lw / 2, q(116), bw / 2 + lw / 2, q(120)), fill=GOLD)
    if sub: d.text((bw / 2, q(158)), sub, font=F(30, 'i'), fill=(225, 230, 240), anchor='mm')
    sc = min(1.0, (W - q(80)) / bw); p = p.resize((int(bw * sc), int(bh * sc)), Image.LANCZOS)
    put(base, p, (W - p.size[0]) / 2, (H - p.size[1]) / 2 - q(40), o)


def compass(base, heading_deg, o=1.0):
    x, y = W - q(70), H - q(90); r = q(30); a = math.radians(-heading_deg)
    L = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.ellipse((x - r, y - r, x + r, y + r), fill=NAVY2 + (220,), outline=GOLD + (255,), width=max(1, q(2)))
    tip = (x + math.sin(a) * r * 0.75, y - math.cos(a) * r * 0.75); l = (x + math.sin(a + 2.6) * r * 0.5, y - math.cos(a + 2.6) * r * 0.5); rr = (x + math.sin(a - 2.6) * r * 0.5, y - math.cos(a - 2.6) * r * 0.5)
    d.polygon([tip, l, (x, y), rr], fill=GOLD); d.text((x + math.sin(a) * r * 1.45, y - math.cos(a) * r * 1.45), 'N', font=F(18, 'b'), fill=WHITE, anchor='mm')
    if o < 1: L.putalpha(L.getchannel('A').point(lambda v: int(v * o)))
    base.alpha_composite(L)
