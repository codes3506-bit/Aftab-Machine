"""Run the sandbox-style design generator in CPython and export build/spec.json for the renderer."""
import json, math, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
B = os.path.join(ROOT, 'build')
info = json.load(open(os.path.join(B, 'terrain.json')))
dem = np.load(os.path.join(B, 'dem_near.npy')).astype(float) - info['pad_level_m']
g = info['grids']['near']

env = {'math': math}
exec(open(os.path.join(ROOT, 'design', 'glyphs_arialbd.py')).read(), env)
exec(open(os.path.join(ROOT, 'design', 'complex.py')).read(), env)

def raw_height(x, y):
    c = (x + g['half']) / g['step']; r = (y + g['half']) / g['step']
    c = min(max(c, 0), g['n'] - 1.001); r = min(max(r, 0), g['n'] - 1.001)
    r0, c0 = int(r), int(c); fr, fc = r - r0, c - c0
    return float(dem[r0, c0] * (1 - fr) * (1 - fc) + dem[r0 + 1, c0] * fr * (1 - fc) + dem[r0, c0 + 1] * (1 - fr) * fc + dem[r0 + 1, c0 + 1] * fr * fc)

spec = env['build_spec'](lambda x, y: env['pad_blend'](x, y, raw_height(x, y)))
json.dump(spec, open(os.path.join(B, 'spec.json'), 'w'), separators=(',', ':'))

def count(n, acc):
    acc['nodes'] += 1; acc['parts'] += len(n['parts']); acc['insts'] += len(n['insts'])
    for c in n['children']: count(c, acc)
    return acc
acc = count(spec['root'], {'nodes': 0, 'parts': 0, 'insts': 0})
acc['def_parts'] = sum(len(d['parts']) for d in spec['defs'].values())
print(acc, os.path.getsize(os.path.join(B, 'spec.json')) // 1024, 'KB')

# ---- terrain for the renderer (heights relative to pad level, compound flattened) ----
xs = np.arange(-g['half'], g['half'] + 0.1, g['step'])
near = np.array([[env['pad_blend'](x, y, float(dem[r, c])) for c, x in enumerate(xs)] for r, y in enumerate(xs)], np.float32)
near.tofile(os.path.join(B, 'terrain_near.f32'))
gf = info['grids']['far']
far = np.load(os.path.join(B, 'dem_far.npy')).astype(np.float32) - info['pad_level_m']
xf = np.arange(-gf['half'], gf['half'] + 0.1, gf['step'])
XF, YF = np.meshgrid(xf, xf)
far[(np.abs(XF) < g['half'] - 50) & (np.abs(YF) < g['half'] - 50)] -= 15.0      # tuck under the near tile
far.tofile(os.path.join(B, 'terrain_far.f32'))

# ---- sun position (NOAA approximation) for the GR, 27 Nov 2026 15:00 PKT (UTC+5) ----
def sun(lat, lon, y, mo, d, hh_utc):
    import datetime
    doy = datetime.date(y, mo, d).timetuple().tm_yday
    gam = 2 * math.pi / 365 * (doy - 1 + (hh_utc - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(gam) - 0.032077 * math.sin(gam) - 0.014615 * math.cos(2 * gam) - 0.040849 * math.sin(2 * gam))
    decl = 0.006918 - 0.399912 * math.cos(gam) + 0.070257 * math.sin(gam) - 0.006758 * math.cos(2 * gam) + 0.000907 * math.sin(2 * gam)
    tst = hh_utc * 60 + eqt + 4 * lon
    ha = math.radians(tst / 4 - 180)
    la = math.radians(lat)
    cz = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    zen = math.acos(cz)
    az = math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(la) - math.tan(decl) * math.cos(la))) + 180
    return round(az % 360, 1), round(90 - math.degrees(zen), 1)
az, el = sun(info['gr']['lat'], info['gr']['lon'], 2026, 11, 27, 10.0)
json.dump({'near': {'half': g['half'], 'step': g['step'], 'n': g['n']}, 'far': {'half': gf['half'], 'step': gf['step'], 'n': gf['n']},
           'sun': {'azimuth': az, 'elevation': el, 'when': '27 Nov 2026 15:00 PKT'}}, open(os.path.join(B, 'render_meta.json'), 'w'))
print('sun', az, el)
