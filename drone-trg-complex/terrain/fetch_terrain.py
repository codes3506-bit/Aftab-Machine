"""Fetch real terrain + imagery around the GR and run a site terrain analysis.

GR 25°19'47.62"N 62°30'33.00"E  (Copernicus GLO-30 DEM, Esri World Imagery)
Outputs (in ../build):
  dem_near.npy   heights, local ENU grid, +-1500 m @ 20 m   (row 0 = south)
  dem_far.npy    heights, +-8000 m @ 100 m
  img_near.jpg   imagery +-1500 m, 4096 px (row 0 = north)
  img_far.jpg    imagery +-8000 m, 4096 px
  terrain.json   grid metadata + site analysis
"""
import io, json, math, os, sys, urllib.request
import numpy as np, tifffile
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

LAT = 25 + 19 / 60 + 47.62 / 3600
LON = 62 + 30 / 60 + 33.00 / 3600
OUT = os.path.join(os.path.dirname(__file__), '..', 'build')
CACHE = os.path.join(OUT, 'cache'); os.makedirs(CACHE, exist_ok=True)
M_LAT = 111132.92 - 559.82 * math.cos(2 * math.radians(LAT))
M_LON = 111412.84 * math.cos(math.radians(LAT)) - 93.5 * math.cos(3 * math.radians(LAT))

def get(url, path):
    if not os.path.exists(path):
        req = urllib.request.Request(url, headers={'User-Agent': 'terrain-fetch/1.0'})
        data = urllib.request.urlopen(req, timeout=120).read()
        open(path, 'wb').write(data)
    return path

def to_ll(e, n): return LAT + n / M_LAT, LON + e / M_LON

def bilinear(a, r, c):
    r = np.clip(r, 0, a.shape[0] - 1.001); c = np.clip(c, 0, a.shape[1] - 1.001)
    r0, c0 = np.floor(r).astype(int), np.floor(c).astype(int); fr, fc = r - r0, c - c0
    if a.ndim == 3: fr, fc = fr[..., None], fc[..., None]
    return (a[r0, c0] * (1 - fr) * (1 - fc) + a[r0 + 1, c0] * fr * (1 - fc)
            + a[r0, c0 + 1] * (1 - fr) * fc + a[r0 + 1, c0 + 1] * fr * fc)

# ---------- DEM ----------
name = 'Copernicus_DSM_COG_10_N25_00_E062_00_DEM'
tif = get(f'https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif', os.path.join(CACHE, name + '.tif'))
dem = tifffile.imread(tif).astype(np.float64)          # row 0 = 26N, col 0 = 62E (pixel centres)
H, Wd = dem.shape

def dem_grid(half, step):
    xs = np.arange(-half, half + 0.1, step)
    E, N = np.meshgrid(xs, xs)                            # row 0 = south
    lat, lon = to_ll(E, N)
    return bilinear(dem, (26 - lat) * H - 0.5, (lon - 62) * Wd - 0.5), xs

near, xs_near = dem_grid(1500, 20)
far, xs_far = dem_grid(8000, 100)
np.save(os.path.join(OUT, 'dem_near.npy'), near.astype(np.float32))
np.save(os.path.join(OUT, 'dem_far.npy'), far.astype(np.float32))

# ---------- Imagery (Esri World Imagery, web mercator) ----------
def merc_px(lat, lon, z):
    s = 256 * 2 ** z
    x = (lon + 180) / 360 * s
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * s if np.isscalar(lat) else \
        (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / np.pi) / 2 * s
    return x, y

def imagery(half, z, size, fname):
    la0, lo0 = to_ll(-half, -half); la1, lo1 = to_ll(half, half)
    x0, y1 = merc_px(la0, lo0, z); x1, y0 = merc_px(la1, lo1, z)
    tx0, tx1, ty0, ty1 = int(x0 // 256), int(x1 // 256), int(y0 // 256), int(y1 // 256)
    mosaic = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256, 3), np.uint8)
    def tile(t):
        tx, ty = t
        p = get(f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{ty}/{tx}',
                os.path.join(CACHE, f'esri_{z}_{tx}_{ty}.jpg'))
        return t, np.array(Image.open(p).convert('RGB'))
    with ThreadPoolExecutor(12) as ex:
        for (tx, ty), im in ex.map(tile, [(a, b) for a in range(tx0, tx1 + 1) for b in range(ty0, ty1 + 1)]):
            mosaic[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = im
    v = np.linspace(half, -half, size); u = np.linspace(-half, half, size)
    E, N = np.meshgrid(u, v)                              # row 0 = north
    lat, lon = to_ll(E, N)
    px, py = merc_px(lat, lon, z)
    out = bilinear(mosaic.astype(np.float32), py - ty0 * 256, px - tx0 * 256)
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(OUT, fname), quality=92)

imagery(1500, 17, 4096, 'img_near.jpg')
imagery(8000, 14, 4096, 'img_far.jpg')

# ---------- Site terrain analysis ----------
c = len(xs_near) // 2
gy, gx = np.gradient(near, 20.0)
slope = np.degrees(np.arctan(np.hypot(gx, gy)))
aspect = (np.degrees(np.arctan2(-gx, -gy)) + 360) % 360     # direction the slope faces
R = np.hypot(*np.meshgrid(xs_near, xs_near))
site = R <= 60                                               # compound footprint ~120 m
pad = float(np.median(near[site]))
cutfill = near[site] - pad
cell = 20 * 20
rings = {f'{r} m': {'min': round(float(near[R <= r].min()), 1), 'max': round(float(near[R <= r].max()), 1),
                    'relief': round(float(np.ptp(near[R <= r])), 1)} for r in (100, 250, 500, 1000, 1500)}
dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
info = {
    'gr': {'lat': LAT, 'lon': LON, 'dms': "25°19'47.62\"N 62°30'33.00\"E"},
    'source': {'dem': 'Copernicus GLO-30 DSM (30 m)', 'imagery': 'Esri World Imagery z17 / z14'},
    'grids': {'near': {'half': 1500, 'step': 20, 'n': len(xs_near)}, 'far': {'half': 8000, 'step': 100, 'n': len(xs_far)}},
    'elevation_at_gr_m': round(float(near[c, c]), 1),
    'pad_level_m': round(pad, 1),
    'site_slope_deg': {'mean': round(float(slope[site].mean()), 2), 'max': round(float(slope[site].max()), 2)},
    'site_aspect': dirs[int(((float(np.degrees(np.arctan2(-gx[site].mean(), -gy[site].mean()))) + 360) % 360 + 22.5) // 45) % 8],
    'earthwork_m3': {'cut': round(float(cutfill[cutfill > 0].sum() * cell)), 'fill': round(float(-cutfill[cutfill < 0].sum() * cell))},
    'relief_rings': rings,
    'area_slope_pct_over_10deg_1km': round(float((slope[R <= 1000] > 10).mean() * 100), 1),
    'highest_point_1500m': {'elev_m': round(float(near.max()), 1),
                            'bearing_deg': round(float((math.degrees(math.atan2(*[xs_near[i] for i in np.unravel_index(near.argmax(), near.shape)[::-1]])) + 360) % 360)),
                            'dist_m': round(float(R.flat[near.argmax()]))},
}
json.dump(info, open(os.path.join(OUT, 'terrain.json'), 'w'), indent=1)
print(json.dumps(info, indent=1))
