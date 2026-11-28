"""Distant horizon terrain (+-40 km @ 160 m) from the cached Copernicus tile, with the northern ranges
raised for legibility (vertical exaggeration ramps 1.0 -> 2.2 from 8 km to 20 km), plus a shaded-relief
desert texture. Outputs build/terrain_horizon.f32, build/img_horizon.jpg."""
import json, math, os
import numpy as np, tifffile
from PIL import Image
B = os.path.join(os.path.dirname(__file__), '..', 'build')
info = json.load(open(os.path.join(B, 'terrain.json')))
LAT, LON = info['gr']['lat'], info['gr']['lon']
M_LAT = 111132.92 - 559.82 * math.cos(2 * math.radians(LAT))
M_LON = 111412.84 * math.cos(math.radians(LAT)) - 93.5 * math.cos(3 * math.radians(LAT))
dem = tifffile.imread(os.path.join(B, 'cache', 'Copernicus_DSM_COG_10_N25_00_E062_00_DEM.tif')).astype(np.float64)
H, W = dem.shape
HALF, STEP = 40000, 160
xs = np.arange(-HALF, HALF + 0.1, STEP); n = len(xs)
E, N = np.meshgrid(xs, xs)
lat, lon = LAT + N / M_LAT, LON + E / M_LON
r = np.clip((26 - lat) * H - 0.5, 0, H - 1.001); c = np.clip((lon - 62) * W - 0.5, 0, W - 1.001)
r0, c0 = r.astype(int), c.astype(int); fr, fc = r - r0, c - c0
h = dem[r0, c0] * (1 - fr) * (1 - fc) + dem[r0 + 1, c0] * fr * (1 - fc) + dem[r0, c0 + 1] * (1 - fr) * fc + dem[r0 + 1, c0 + 1] * fr * fc
h = np.where(lat < 25.0, 0.0, h)                         # outside the tile (sea to the south)
h = np.maximum(h, 0.0) - info['pad_level_m']
d = np.hypot(E, N)
k = np.clip((d - 8000) / 12000, 0, 1); k = k * k * (3 - 2 * k)
h = np.where(h > 0, h * (1 + 1.2 * k), h)
h[(np.abs(E) < 7900) & (np.abs(N) < 7900)] -= 40.0       # tuck under the far tile
h.astype(np.float32).tofile(os.path.join(B, 'terrain_horizon.f32'))
# shaded relief texture (row 0 = north)
gy, gx = np.gradient(h, STEP)
lx, ly, lz = -0.55, 0.45, 0.70
shade = np.clip((-gx * lx - gy * ly + lz) / np.sqrt(gx ** 2 + gy ** 2 + 1), 0, 1)
slope = np.clip(np.hypot(gx, gy) * 2.2, 0, 1)
hn = np.clip(h / 900, 0, 1)
sand = np.array([214, 190, 150]); rock = np.array([150, 118, 86]); hi = np.array([120, 96, 76]); sea = np.array([60, 110, 130])
col = sand[None, None] * (1 - slope[..., None]) + rock[None, None] * slope[..., None]
col = col * (1 - 0.35 * hn[..., None]) + hi[None, None] * 0.35 * hn[..., None]
col = col * (0.55 + 0.6 * shade[..., None])
col = np.where((h < -info['pad_level_m'] + 0.5)[..., None], sea[None, None], col)
img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)[::-1]).resize((2048, 2048), Image.BICUBIC)
img.save(os.path.join(B, 'img_horizon.jpg'), quality=92)
m = json.load(open(os.path.join(B, 'render_meta.json'))); m['horizon'] = {'half': HALF, 'step': STEP, 'n': n}
json.dump(m, open(os.path.join(B, 'render_meta.json'), 'w'))
print(n, float(h.max()))
