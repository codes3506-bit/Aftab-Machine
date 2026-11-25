"""Image-space overlays: additive-bloom glow tracks (depth-tested), pins, labels, panels, HUD, north arrow, scale bar."""
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FD = '/usr/share/fonts/opentype/inter/'
def F(sz, w='SemiBold', disp=False): return ImageFont.truetype(f'{FD}{"InterDisplay" if disp else "Inter"}-{w}.otf', int(sz))
def MONO(sz): return ImageFont.truetype('/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf', int(sz))
GOLD = (245, 183, 0); PANEL = (11, 18, 32)
COL = {'T1': (150, 156, 168), 'T2': (91, 141, 239), 'T3': (63, 184, 175), 'T4': (199, 125, 255), 'T5': (245, 183, 0), 'KMZ': (205, 210, 220)}


def hexc(c): return tuple(int(x) for x in c)


def glow_tracks(img, items, scale=1.0):
    """img float HxWx3 0..1. items: list of dict(xy=(n,2), vis=(n,), col, w, glow, pulse=None (0..1), dash)"""
    H, W = img.shape[:2]
    core = np.zeros((H, W, 3), np.float32); halo = np.zeros((H, W, 3), np.float32); occl = np.zeros((H, W, 3), np.float32)
    for it in items:
        xy = it['xy']; vis = it['vis']; c = np.array(it['col'], np.float32) / 255; w = it['w'] * scale; g = it.get('glow', 1.0)
        segs = []; cur = []
        for k in range(len(xy)):
            if vis[k]: cur.append(xy[k])
            elif cur: segs.append(cur); cur = []
        if cur: segs.append(cur)
        for sgm in segs:
            if len(sgm) < 2: continue
            p = (np.array(sgm) * 8).astype(np.int32).reshape(-1, 1, 2)
            cv2.polylines(core, [p], False, c.tolist(), max(1, int(w)), cv2.LINE_AA, shift=3)
            cv2.polylines(halo, [p], False, (c * g).tolist(), max(2, int(w * 3)), cv2.LINE_AA, shift=3)
        # hidden parts: faint dotted ghost so the viewer keeps continuity
        hid = [xy[k] for k in range(len(xy)) if not it['vis'][k] and it.get('ghost', True) and 0 <= xy[k][0] < W and 0 <= xy[k][1] < H]
        for q in hid[::3]: cv2.circle(occl, (int(q[0]), int(q[1])), max(1, int(w * 0.25)), (c * 0.5).tolist(), -1, cv2.LINE_AA)
        if it.get('pulse') is not None and len(xy) > 3:
            k = int(it['pulse'] * (len(xy) - 1)); r = int(w * 2.2)
            for j in range(max(0, k - 25), k + 1):
                if vis[j]:
                    a = (1 - (k - j) / 25) ** 2
                    cv2.circle(core, (int(xy[j][0]), int(xy[j][1])), max(1, int(r * a)), (np.minimum(1, c * 0.4 + 0.75) * a).tolist(), -1, cv2.LINE_AA)
    out = img.copy()
    out = out * (1 - 0.35 * np.clip(halo.max(2, keepdims=True) * 2, 0, 1))      # slight darkening under line = contrast
    L = sum(cv2.GaussianBlur(halo, (0, 0), s_) * k for s_, k in ((4 * scale, 0.45), (14 * scale, 0.3), (38 * scale, 0.2)))
    cm = core.max(2, keepdims=True); out = out * (1 - np.clip(cm * 1.2, 0, 1)) + core   # opaque coloured core
    out += L + cv2.GaussianBlur(core, (0, 0), 1.2 * scale) * 0.25 + occl * 0.6
    m = np.maximum(out.max(2, keepdims=True), 1.0); return np.clip(out / m ** 0.85, 0, 1)   # hue-preserving soft clip


def to_pil(a): return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert('RGBA')


def panel(base, box, title=None, accent=GOLD, alpha=0.82, blur=True, s=1.0):
    x0, y0, x1, y1 = [int(v) for v in box]
    if blur:
        reg = base.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(18 * s)); base.paste(reg, (x0, y0))
    ov = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle(box, radius=int(14 * s), fill=PANEL + (int(255 * alpha),), outline=accent + (200,), width=max(1, int(2 * s)))
    d.rectangle((x0 + int(14 * s), y0, x0 + int(120 * s), y0 + int(5 * s)), fill=accent + (255,))
    base.alpha_composite(ov)
    if title:
        ImageDraw.Draw(base).text((x0 + int(26 * s), y0 + int(22 * s)), title, font=F(30 * s, 'Bold'), fill=accent)


def text(base, xy, s, f, fill=(255, 255, 255), anchor='la', shadow=True, sc=1.0):
    d = ImageDraw.Draw(base)
    if shadow: d.text((xy[0] + 2 * sc, xy[1] + 2 * sc), s, font=f, fill=(0, 0, 0, 170), anchor=anchor)
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def pin(base, xy, label, sub=None, col=(255, 255, 255), s=1.0, up=180):
    x, y = xy; d = ImageDraw.Draw(base)
    glow = Image.new('RGBA', base.size, (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    g.ellipse((x - 26 * s, y - 26 * s, x + 26 * s, y + 26 * s), fill=GOLD + (120,)); glow = glow.filter(ImageFilter.GaussianBlur(14 * s)); base.alpha_composite(glow)
    d.line((x, y, x, y - up * s), fill=(255, 255, 255, 230), width=int(3 * s))
    d.ellipse((x - 9 * s, y - 9 * s, x + 9 * s, y + 9 * s), fill=GOLD + (255,), outline=(255, 255, 255, 255), width=int(3 * s))
    f1 = F(34 * s, 'Bold'); w = d.textlength(label, font=f1); f2 = F(24 * s, 'Medium'); w2 = d.textlength(sub, font=f2) if sub else 0
    bw = max(w, w2) + 40 * s; bh = (60 if not sub else 96) * s; bx = x - bw / 2; by = y - up * s - bh
    d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=int(10 * s), fill=PANEL + (225,), outline=GOLD + (255,), width=int(3 * s))
    d.text((x, by + 14 * s), label, font=f1, fill=(255, 255, 255), anchor='ma')
    if sub: d.text((x, by + 58 * s), sub, font=f2, fill=GOLD, anchor='ma')


def tag(base, xy, s_, col, s=1.0, dx=0, dy=-46):
    d = ImageDraw.Draw(base); x, y = xy[0] + dx * s, xy[1] + dy * s; f = F(26 * s, 'Bold'); w = d.textlength(s_, font=f)
    d.line((xy[0], xy[1], x, y + 18 * s), fill=col + (220,), width=int(2 * s))
    d.rounded_rectangle((x - w / 2 - 14 * s, y - 18 * s, x + w / 2 + 14 * s, y + 20 * s), radius=int(8 * s), fill=PANEL + (215,), outline=col + (255,), width=int(2 * s))
    d.text((x, y + 1 * s), s_, font=f, fill=col, anchor='mm')


def north_arrow(base, c, heading_deg, s=1.0):
    """heading_deg: camera azimuth (0 = looking N). Arrow shows screen direction of north."""
    x, y = c; r = 44 * s; a = np.radians(-heading_deg)
    d = ImageDraw.Draw(base); d.ellipse((x - r, y - r, x + r, y + r), fill=PANEL + (200,), outline=(255, 255, 255, 200), width=int(2 * s))
    tip = (x + np.sin(a) * r * 0.75, y - np.cos(a) * r * 0.75); l = (x + np.sin(a + 2.6) * r * 0.5, y - np.cos(a + 2.6) * r * 0.5); rr = (x + np.sin(a - 2.6) * r * 0.5, y - np.cos(a - 2.6) * r * 0.5)
    d.polygon([tip, l, (x, y), rr], fill=GOLD + (255,)); d.text((x + np.sin(a) * r * 1.35, y - np.cos(a) * r * 1.35), 'N', font=F(26 * s, 'Bold'), fill=(255, 255, 255), anchor='mm')


def title_bar(base, t, sub=None, s=1.0):
    W, H = base.size; d = ImageDraw.Draw(base)
    ov = Image.new('RGBA', base.size, (0, 0, 0, 0)); g = ImageDraw.Draw(ov)
    for i in range(int(200 * s)): g.line((0, i, W, i), fill=(5, 10, 20, int(150 * (1 - i / (200 * s)) ** 1.5)))
    base.alpha_composite(ov)
    d.text((70 * s, 46 * s), t, font=F(46 * s, 'Bold', True), fill=(255, 255, 255))
    d.rectangle((70 * s, 112 * s, 190 * s, 117 * s), fill=GOLD)
    if sub: d.text((210 * s, 104 * s), sub, font=F(26 * s, 'Medium'), fill=(220, 225, 235))


def grade(img, warm=1.0):
    """shared look for 3D + drone: lifted blacks, gentle S-curve, warm highlights"""
    a = np.clip(img, 0, 1); a = a * 0.94 + 0.025
    a = a + 0.08 * (a - 0.5) * (1 - np.abs(2 * a - 1))
    a = a * np.array([1.03, 1.0, 0.95]) ** warm
    yy = np.linspace(0, 1, a.shape[0])[:, None]; xx = np.linspace(-1, 1, a.shape[1])[None]
    vig = 1 - 0.22 * (xx ** 2 * 0.6 + (2 * yy - 1) ** 2 * 0.5); return np.clip(a * vig[..., None], 0, 1)
