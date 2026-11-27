"""Pack the design spec (+ real terrain mesh) into a lossless PNG for the SketchUp sandbox.

The SketchUp build_model sandbox can read uploaded PNG/JPEG files but cannot import modules,
so the JSON spec travels as raw bytes in an uncompressed (stored-deflate) grayscale PNG and
adapter.py decodes it in pure Python.
"""
import json, math, os, sys, zlib, struct
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..'); B = os.path.join(ROOT, 'build')
info = json.load(open(os.path.join(B, 'terrain.json')))
dem = np.load(os.path.join(B, 'dem_near.npy')).astype(float) - info['pad_level_m']
g = info['grids']['near']
env = {'math': math}
exec(open(os.path.join(ROOT, 'design', 'glyphs_arialbd.py')).read(), env)
exec(open(os.path.join(ROOT, 'design', 'complex.py')).read(), env)

def raw(x, y):
    c = min(max((x + g['half']) / g['step'], 0), g['n'] - 1.001); r = min(max((y + g['half']) / g['step'], 0), g['n'] - 1.001)
    r0, c0 = int(r), int(c); fr, fc = r - r0, c - c0
    return float(dem[r0, c0] * (1 - fr) * (1 - fc) + dem[r0 + 1, c0] * fr * (1 - fc) + dem[r0, c0 + 1] * (1 - fr) * fc + dem[r0 + 1, c0 + 1] * fr * fc)
H = lambda x, y: env['pad_blend'](x, y, raw(x, y))

HALF, STEP = 900, 20
xs = np.arange(-HALF, HALF + 0.1, STEP); n = len(xs)
# road sits on the triangulated SketchUp terrain, so sample the same triangles (+ clearance)
grid = np.array([[H(x, y) for x in xs] for y in xs])
def tri_h(x, y):
    c = (x + HALF) / STEP; r = (y + HALF) / STEP
    c0, r0 = min(int(c), n - 2), min(int(r), n - 2); fc, fr = c - c0, r - r0
    z00, z10, z01, z11 = grid[r0, c0], grid[r0, c0 + 1], grid[r0 + 1, c0], grid[r0 + 1, c0 + 1]
    return z00 + (z10 - z00) * fc + (z11 - z10) * fr if fc >= fr else z00 + (z11 - z01) * fc + (z01 - z00) * fr
spec = env['build_spec'](lambda x, y: max(tri_h(x, y), H(x, y)) + 0.15)
spec.pop('meta', None)
# terrain node: local coords 0..1800 so the default texture projection lines the image up
verts = [[round(float(x + HALF), 2), round(float(y + HALF), 2), round(float(grid[r, c]), 2)] for r, y in enumerate(xs) for c, x in enumerate(xs)]
faces = []
for r in range(n - 1):
    for c in range(n - 1):
        a, b, d, e = r * n + c, r * n + c + 1, (r + 1) * n + c, (r + 1) * n + c + 1
        faces += [[a, b, e], [a, e, d]]
spec['terrain'] = {'name': 'Terrain_GR_Copernicus_GLO30', 'pos': [-HALF, -HALF, 0], 'size': 2 * HALF,
                   'mesh': {'k': 'mesh', 'v': verts, 'f': faces, 'm': 'Terrain_Imagery'}}
from PIL import Image
spec['portraits'] = {}
for key, f in (('Portrait_Quaid', 'portrait_quaid.jpg'), ('Portrait_Iqbal', 'portrait_iqbal.jpg')):
    im = Image.open(os.path.join(ROOT, 'assets', f)).convert('RGB').resize((236, 200), Image.LANCZOS)
    spec['portraits'][key] = {'w': 236, 'h': 200, 'hex': im.tobytes().hex()}
spec['site'] = {'lat': info['gr']['lat'], 'lon': info['gr']['lon'], 'pad_level_m': info['pad_level_m']}
txt = json.dumps(spec, separators=(',', ':'), ensure_ascii=True)
assert '\\' not in txt
data = txt.encode('ascii')
data = str(len(data)).encode().rjust(12, b'0') + data
Wd = 4096; Hh = -(-len(data) // Wd)
data = data.ljust(Wd * Hh, b' ')
rows = b''.join(b'\x00' + data[i * Wd:(i + 1) * Wd] for i in range(Hh))
def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', Wd, Hh, 8, 0, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows, 0)) + chunk(b'IEND', b'')
open(os.path.join(B, 'spec_payload.png'), 'wb').write(png)
print('json', len(txt) // 1024, 'KB; png', len(png) // 1024, 'KB', Wd, 'x', Hh, '; terrain verts', len(verts))
