"""40' x 40' post pad on the Khabri-1 crest: balanced level formation on Cop GLO-30 (bicubic, 0.5 m), crest axis from DEM,
plant / POL by the pol-work-days-calculator engine with the user's saved standards. Location assessed (alongside existing 32' x 32' room)."""
import json, math, numpy as np
from geo import *
S = {**json.load(open('../scripts/userstd.json'))}; M = 1 + S['margin_pct'] / 100
pe, pn = [float(v) for v in en(63.43978, 25.42739)]
best = None
for a in range(0, 180, 1):
    r = np.radians(a); d = np.arange(-20, 21, 1.0); z = dem(*ll(pe + d * np.sin(r), pn + d * np.cos(r))); rel = float(z.max() - z.min())
    if best is None or rel < best[1]: best = (a, rel)
AZ = best[0]; u = np.array([np.sin(np.radians(AZ)), np.cos(np.radians(AZ))]); v = np.array([u[1], -u[0]])
FT = 0.3048; PAD = 40 * FT; ROOM = 32 * FT; MARG = 1.0                      # 1 m working margin each side
h = PAD / 2 + MARG; g = np.arange(-h, h + 1e-6, 0.25); A, B = np.meshgrid(g, g); cell = 0.25 ** 2
from scipy.ndimage import map_coordinates
PG = np.arange(-45, 45.01, 0.25); PX, PY = np.meshgrid(PG, PG); PZ = dem(*ll(pe + PX, pn + PY))          # one bicubic call, local patch
def zloc(E, N): return map_coordinates(PZ, [(N - pn + 45) / 0.25, (E - pe + 45) / 0.25], order=1)
def earth(c):
    E = c[0] + A * u[0] + B * v[0]; N = c[1] + A * u[1] + B * v[1]; Z = zloc(E, N); lo, hi = float(Z.min()), float(Z.max())
    for _ in range(30):                                                    # balanced formation: cut volume = fill volume
        f = (lo + hi) / 2
        if np.clip(Z - f, 0, None).sum() > np.clip(f - Z, 0, None).sum(): lo = f
        else: hi = f
    return float(np.clip(Z - f, 0, None).sum() * cell), float(np.clip(f - Z, 0, None).sum() * cell), E, N, Z, f
# site the pad on the crest to least earthwork, alongside the existing room (room = user grid), >= 2 m clear of it
best = None; clr = ROOM / 2 + 2.0 + PAD / 2
for du in np.arange(-(clr + 4), clr + 4.01, 0.5):                    # alongside: 2-6 m clear of the room on any side
    for dv in np.arange(-(clr + 4), clr + 4.01, 0.5):
        if abs(du) < clr and abs(dv) < clr: continue
        c_ = np.array([pe, pn]) + u * du + v * dv; ct, fl, *_ = earth(c_)
        if best is None or ct + fl < best[0]: best = (ct + fl, du, dv)
DU, DV = best[1], best[2]; c = np.array([pe, pn]) + u * DU + v * DV; OFF = DU
cut, fill, E, N, Z, f = earth(c)
area = (2 * h) ** 2
exc_rate = S['exc_cut_cfthr'] / S['cft_per_m3']
exc_h = math.ceil(cut / exc_rate * M)
wf = (2 * h * S['ft_per_m']) / S['doz_ref_width_ft']
doz_h = math.ceil((min(cut, fill) / S['doz_spread_m3hr'] + (2 * h / 1000) * S['doz_level_hr_km'] * wf) * M)
jh_cu = round(0.2 * cut); jh_h = math.ceil(jh_cu / 1.0 * M); jh_lph = 10 / max(1, math.floor(185 / 75))
rows = [dict(d='Excavator (cutting to formation)', au='Hrs', q=exc_h, r=S['exc_lph'], l=round(exc_h * S['exc_lph']), rm=f'{cut:,.0f} cu M cut @ {exc_rate:.0f} cu M/hr'),
        dict(d='Dozer (spread, level, compact by tracking)', au='Hrs', q=doz_h, r=S['doz_lph'], l=round(doz_h * S['doz_lph']), rm=f'{min(cut, fill):,.0f} cu M moved into fill + levelling')]
tot = sum(r['l'] for r in rows)
cont = dict(d='Jack Hammer – contingency (hard shale bands, 20 % of cut, assessed)', au='Hrs', q=jh_h, r=jh_lph, l=round(jh_h * jh_lph))
days = max(math.ceil(exc_h / S['hrs_per_day']), math.ceil(doz_h / S['hrs_per_day']))
out = dict(du=DU, dv=DV, crest_az=AZ, pad_ft=40, room_ft=32, pad_m=PAD, work_m=2 * h, centre_en=c.tolist(), u=u.tolist(), v=v.tolist(), off_m=OFF,
           z_min=float(Z.min()), z_max=float(Z.max()), relief=float(Z.max() - Z.min()), formation_below_high=float(Z.max() - f),
           area_m2=area, cut=cut, fill=fill, rows=rows, total=tot, contingency=cont, days=days, grid=dict(E=E.tolist(), N=N.tolist(), dz=(Z - f).tolist()))
json.dump(out, open(f'{R}/work/pad.json', 'w'))
print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in out.items() if k not in ('grid', 'rows', 'centre_en', 'u', 'v')}); print(rows, cont)
