"""Esri World Imagery Wayback release 32553 (2024-08-15): a sharper, low-sun Maxar capture of the AOI than the current
default (2026 release). Same extents as fetch.py. Tiles that fail fall back to the current-release tile."""
import os, shutil, urllib.request, concurrent.futures as cf
from fetch import t
R = '/home/user/khabri'; REL = 32553
U = 'https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/{r}/{z}/{y}/{x}'
def job(z, W, E_, S, N):
    d = f'{R}/tiles_wb/z{z}'; old = f'{R}/tiles_v1/z{z}'; os.makedirs(d, exist_ok=True)
    x0, y1 = t(W, S, z); x1, y0 = t(E_, N, z); bad = []
    def get(xy):
        x, y = xy; f = f'{d}/{z}_{x}_{y}.jpg'
        if os.path.exists(f) and os.path.getsize(f) > 0: return
        for k in range(4):
            try: open(f, 'wb').write(urllib.request.urlopen(U.format(r=REL, z=z, y=y, x=x), timeout=30).read()); return
            except Exception as e: err = e
        bad.append(xy); shutil.copy(f'{old}/{z}_{x}_{y}.jpg', f)
    with cf.ThreadPoolExecutor(12) as ex: list(ex.map(get, [(x, y) for x in range(int(x0), int(x1) + 1) for y in range(int(y0), int(y1) + 1)]))
    print(z, 'fallback tiles', len(bad), flush=True)
if __name__ == '__main__':
    job(16, 63.36, 63.51, 25.35, 25.48); job(17, 63.395, 63.475, 25.38, 25.45); job(18, 63.410, 63.460, 25.392, 25.438)
