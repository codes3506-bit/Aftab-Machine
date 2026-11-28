# DRONE TRG COMPLEX - 44 DIV : parametric design generator
#
# One source of truth for the SketchUp model and the video renderer.
# Units: metres. Axes: x = east, y = north, z = up. Origin = GR 25°19'47.62"N 62°30'33.00"E at pad level.
# Building front (title, entrance) faces north.
#
# Written for the SketchUp build_model sandbox: no imports (math is supplied), no str.format,
# no any/all/next, no dunder access. Runs unchanged in CPython via render/export_spec.py.
#
# build_spec(height_fn) -> {'materials': {...}, 'defs': {name: node}, 'root': node}
# node = {'name', 'pos': [x,y,z], 'rot': deg about z, 'parts': [...], 'children': [...],
#         'insts': [{'d', 'name', 'pos', 'rot'}], 'layer': str|None, 'anim': dict|None}
# part = prism {'k':'prism','pts','holes','z','h','m','ax'}  (ax 'z': pts=(x,y); 'y': pts=(x,z); 'x': pts=(y,z))
#        lathe {'k':'lathe','c':[x,y,z],'prof':[[dz,r],...],'seg','m'}
#        mesh  {'k':'mesh','v':[[x,y,z],...],'f':[[i,j,k],...],'m'}

PI = math.pi

MATERIALS = {
    'Stone': [214, 190, 150, 255], 'Stone_Band': [168, 140, 102, 255], 'Stone_Dark': [140, 116, 86, 255],
    'Plaster': [238, 233, 222, 255], 'Floor_Tile': [208, 204, 196, 255], 'Roof': [192, 189, 182, 255],
    'Glass': [70, 100, 115, 95], 'Glass_Dark': [28, 40, 48, 150], 'Metal_Dark': [46, 49, 52, 255],
    'Carbon': [30, 32, 36, 255], 'Composite_Grey': [96, 100, 106, 255], 'Aluminium': [176, 180, 184, 255],
    'Title_Band': [34, 38, 42, 255], 'Title_Letters': [250, 250, 246, 255],
    'Stage_Wood': [118, 76, 46, 255], 'Wood': [146, 102, 64, 255], 'Wood_Slat': [160, 116, 74, 255],
    'Seat_Fabric': [28, 52, 98, 255], 'Carpet': [64, 70, 84, 255], 'Curtain': [110, 24, 32, 255],
    'Screen_Off': [16, 20, 28, 255], 'Screen_Glow': [70, 140, 215, 255], 'Led_Blue': [60, 175, 255, 255],
    'Nav_Red': [235, 35, 35, 255], 'Nav_Green': [30, 225, 90, 255], 'Prop_Tip': [242, 122, 22, 255],
    'Olive': [86, 92, 56, 255], 'Tyre': [26, 26, 26, 255], 'Lawn': [92, 150, 62, 255], 'Shrub': [74, 116, 52, 255],
    'Sand_Field': [214, 188, 142, 255], 'Concrete': [186, 183, 176, 255], 'Asphalt': [66, 67, 70, 255],
    'Marking_White': [236, 236, 230, 255], 'Marking_Yellow': [240, 196, 40, 255], 'Gate_Orange': [240, 116, 24, 255],
    'Flag_Green': [1, 72, 32, 255], 'Flag_White': [250, 250, 250, 255], 'Leather_Black': [24, 24, 26, 255],
    'Upholstery_Grey': [92, 96, 104, 255], 'Plant_Pot': [120, 80, 56, 255], 'Light_Panel': [255, 248, 228, 255],
    'Terrain': [196, 176, 138, 255], 'Frame_Gold': [196, 156, 72, 255], 'Portrait_Quaid': [200, 200, 200, 255],
    'Portrait_Iqbal': [200, 200, 200, 255], 'Sanitary_White': [242, 244, 246, 255], 'Tile_Wet': [196, 210, 214, 255],
    'Mirror': [150, 170, 180, 255], 'Laminate': [158, 163, 168, 255], 'Cabinet_Yellow': [226, 176, 30, 255],
    'Fire_Red': [196, 30, 32, 255], 'Bin_Blue': [40, 92, 170, 255],
}

# ---------------------------------------------------------------- dimensions
W, D, C = 18.0, 12.0, 5.0        # hall half-width (E-W), half-depth (N-S), corner chamfer
T = 0.4                          # exterior wall
F = 0.3                          # finished floor level
HC, HR, HW = 5.4, 5.9, 6.6       # ceiling, roof top, parapet top
TR, TD = 3.6, 1.3                # tower radius, centre offset beyond chamfer
TOWER_TOP = 7.4
PROP_Z = 9.45
COMPOUND = (-55.0, -40.0, 55.0, 52.0)   # x0, y0, x1, y1
X_HALL, X_SIM = -3.0, 4.0        # partitions: hall | foyer | simulator complex

# ---------------------------------------------------------------- primitives
def prism(pts, z, h, m, holes=None, ax='z'):
    return {'k': 'prism', 'pts': [[round(p[0], 4), round(p[1], 4)] for p in pts],
            'holes': [[[round(p[0], 4), round(p[1], 4)] for p in hl] for hl in (holes or [])],
            'z': round(z, 4), 'h': round(h, 4), 'm': m, 'ax': ax}

def rect_pts(cx, cy, w, d, rot=0.0):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = []
    for u, v in [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]:
        out.append([cx + u * c - v * s, cy + u * s + v * c])
    return out

def box(cx, cy, z, w, d, h, m, rot=0.0):
    return prism(rect_pts(cx, cy, w, d, rot), z, h, m)

def circle_pts(cx, cy, r, n=24, a0=0.0):
    return [[cx + r * math.cos(a0 + 2 * PI * i / n), cy + r * math.sin(a0 + 2 * PI * i / n)] for i in range(n)]

def cyl(cx, cy, z, r, h, m, n=24):
    return prism(circle_pts(cx, cy, r, n), z, h, m)

def ring(cx, cy, z, ro, ri, h, m, n=48):
    return prism(circle_pts(cx, cy, ro, n), z, h, m, holes=[circle_pts(cx, cy, ri, n)[::-1]])

def arc_wall(cx, cy, z, ro, ri, h, a0, a1, m, n=28):
    outer = [[cx + ro * math.cos(a0 + (a1 - a0) * i / n), cy + ro * math.sin(a0 + (a1 - a0) * i / n)] for i in range(n + 1)]
    inner = [[cx + ri * math.cos(a1 - (a1 - a0) * i / n), cy + ri * math.sin(a1 - (a1 - a0) * i / n)] for i in range(n + 1)]
    return prism(outer + inner, z, h, m)

def lathe(cx, cy, z, prof, m, seg=24):
    return {'k': 'lathe', 'c': [cx, cy, z], 'prof': [[round(a, 4), round(b, 4)] for a, b in prof], 'seg': seg, 'm': m}

def node(name, parts=None, pos=None, rot=0.0, layer=None, anim=None):
    return {'name': name, 'pos': pos or [0, 0, 0], 'rot': rot, 'parts': parts or [], 'children': [], 'insts': [],
            'layer': layer, 'anim': anim}

def inst(d, name, x, y, z=0.0, rot=0.0):
    return {'d': d, 'name': name, 'pos': [round(x, 4), round(y, 4), round(z, 4)], 'rot': rot}

def add(parent, child):
    parent['children'].append(child)
    return child

# ---------------------------------------------------------------- walls
def wall(parts, a, b, openings, t, h, z0, m_out, m_in=None, lining=0.04):
    """Straight wall from a to b; outer face on the line a-b, thickness towards the building centre.
    openings: (s, e, zb, zt, kind) along the wall; kind 'door' (open), 'glass', 'window'."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux                                       # left normal
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if nx * (0 - mx) + ny * (0 - my) < 0:                  # make n point inwards (towards origin)
        nx, ny = -nx, -ny
    def quad(s, e, o0, o1):
        return [[a[0] + ux * s + nx * o0, a[1] + uy * s + ny * o0], [a[0] + ux * e + nx * o0, a[1] + uy * e + ny * o0],
                [a[0] + ux * e + nx * o1, a[1] + uy * e + ny * o1], [a[0] + ux * s + nx * o1, a[1] + uy * s + ny * o1]]
    def piece(s, e, zb, zt):
        if e - s < 0.005 or zt - zb < 0.005:
            return
        if m_in:
            parts.append(prism(quad(s, e, 0, t - lining), zb, zt - zb, m_out))
            ztop = min(zt, z0 + HC) if zb < z0 + HC else zb
            if ztop > zb:
                parts.append(prism(quad(s, e, t - lining, t), zb, ztop - zb, m_in))
            if zt > ztop:
                parts.append(prism(quad(s, e, t - lining, t), ztop, zt - ztop, m_out))
        else:
            parts.append(prism(quad(s, e, 0, t), zb, zt - zb, m_out))
    ops = sorted(openings, key=lambda o: o[0])
    cur = 0.0
    for s, e, zb, zt, kind in ops:
        piece(cur, s, z0, z0 + h)
        piece(s, e, z0, zb)
        piece(s, e, zt, z0 + h)
        if kind in ('glass', 'window'):
            parts.append(prism(quad(s, e, t * 0.45, t * 0.55), zb, zt - zb, 'Glass_Dark' if kind == 'window' else 'Glass'))
            fw = 0.07
            for fs, fe, fzb, fzt in [(s, s + fw, zb, zt), (e - fw, e, zb, zt), (s + fw, e - fw, zb, zb + fw), (s + fw, e - fw, zt - fw, zt)]:
                parts.append(prism(quad(fs, fe, t * 0.4, t * 0.6), fzb, fzt - fzb, 'Metal_Dark'))
        cur = e
    piece(cur, L, z0, z0 + h)
    return L

def opening(center, width, zb, zt, kind):
    return (center - width / 2, center + width / 2, zb, zt, kind)

# ---------------------------------------------------------------- building
def hall_polygon(inset=0.0):
    w, d, c = W - inset, D - inset, C - inset * (math.sqrt(2) - 1)
    return [[w - c, d], [-(w - c), d], [-w, d - c], [-w, -(d - c)], [-(w - c), -d], [w - c, -d], [w, -(d - c)], [w, d - c]]

TOWERS = []   # filled by build_towers: dicts with name, cx, cy, nx, ny, phi, spin
for sx, sy, nm, spin in [(1, 1, 'NE', 1), (-1, 1, 'NW', -1), (-1, -1, 'SW', 1), (1, -1, 'SE', -1)]:
    mx, my = sx * (W - C / 2), sy * (D - C / 2)
    nx, ny = sx * math.sqrt(0.5), sy * math.sqrt(0.5)
    TOWERS.append({'name': nm, 'cx': mx + nx * TD, 'cy': my + ny * TD, 'nx': nx, 'ny': ny,
                   'phi': math.atan2(ny, nx), 'spin': spin, 'front': sy > 0})

def build_shell(root):
    shell = add(root, node('Building_Shell'))
    P = hall_polygon()
    parts = shell['parts']
    zf = F
    for i in range(8):
        a, b = P[i], P[(i + 1) % 8]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        ops = []
        if i == 0:   # north front, a = (13, 12) -> b = (-13, 12): along-wall s measured from x = +13
            for c0, wd, zb, zt, kind in [(0, 2.4, zf, zf + 3.6, 'door'), (-2.35, 2.3, zf, zf + 3.6, 'glass'), (2.35, 2.3, zf, zf + 3.6, 'glass'),
                                          (-9.0, 2.0, zf + 1.2, zf + 3.2, 'window'), (9.0, 2.0, zf + 1.2, zf + 3.2, 'window')]:
                ops.append(opening(13 - c0, wd, zb, zt, kind))
        elif i in (1, 3, 5, 7):  # chamfers: doors into the rotor towers
            ops.append(opening(L / 2, 1.6, zf, zf + 2.6, 'door'))
        elif i == 4:  # south back: foyer rear exit and simulator exit, high clerestory glazing for the hall
            for xc, wd, zb, zt, kind in [(0.5, 1.8, zf, zf + 2.6, 'door'), (10.0, 1.6, zf, zf + 2.6, 'door'),
                                          (-6.0, 2.4, zf + 3.4, zf + 4.4, 'window'), (-10.5, 2.4, zf + 3.4, zf + 4.4, 'window')]:
                ops.append(opening(xc - a[0], wd, zb, zt, kind))
        elif i == 6:  # east side
            ops.append(opening(L / 2, 2.0, zf + 3.4, zf + 4.4, 'window'))
        wall(parts, a, b, ops, T, HW, 0.0, 'Stone', 'Plaster')
    # plinth / floor slab and ground-floor finishes
    parts.append(prism(P, 0.0, F, 'Floor_Tile'))
    # title band and letters on the north parapet
    band = add(shell, node('Title_Band'))
    band['parts'].append(prism([[12.6, 4.45], [-12.6, 4.45], [-12.6, 6.45], [12.6, 6.45]], D, 0.08, 'Title_Band', ax='y'))
    title = add(shell, node('Title_DRONE_TRG_COMPLEX_44_DIV'))
    title['parts'] = title_parts('DRONE TRG COMPLEX - 44 DIV', D + 0.08, 0.16, 4.62, 6.28, 23.6)
    # entrance canopy, columns and steps
    ent = add(shell, node('Entrance'))
    ep = ent['parts']
    ep.append(box(0, D + 1.8, 4.05, 10.4, 3.6, 0.32, 'Metal_Dark'))
    ep.append(box(0, D + 3.55, 3.9, 10.4, 0.1, 0.15, 'Led_Blue'))
    for x in (-4.8, 4.8):
        ep.append(cyl(x, D + 3.2, 0.0, 0.16, 4.05, 'Metal_Dark', 16))
    ep.append(box(0, D + 2.0, 0.0, 11.0, 4.0, F, 'Concrete'))
    ep.append(box(0, D + 4.35, 0.0, 11.0, 0.7, F * 0.5, 'Concrete'))
    for sx in (-1, 1):
        ep.append(box(sx * 7.6, D + 1.6, 0.0, 3.0, 1.2, 0.7, 'Stone_Dark'))
        ep.append(box(sx * 7.6, D + 1.6, 0.7, 2.8, 1.0, 0.05, 'Shrub'))
    # roof (hideable) with ceiling light panels
    roof = add(root, node('Roof', layer='Roof'))
    inner = hall_polygon(T)
    roof['parts'].append(prism(inner, HC, HR - HC, 'Roof'))
    for x in (-14.5, -11.0, -7.5, -4.5, 1.0, 7.0, 10.5, 14.0):
        for y in (-6.0, -2.0, 2.0, 6.0):
            roof['parts'].append(box(x, y, HC - 0.05, 1.2, 0.6, 0.05, 'Light_Panel'))
    # interior partitions
    part = add(root, node('Partitions'))
    pp = part['parts']
    for xw in (X_HALL, X_SIM):
        y0, y1 = -(D - T), D - T
        segs = [(y0, -5.0), (-3.0, 4.0), (6.4, y1)] if xw == X_HALL else [(y0, -5.0), (-3.0, 4.0), (6.4, y1)]
        for a0, a1 in segs:
            pp.append(box(xw, (a0 + a1) / 2, F, 0.2, a1 - a0, HC - F, 'Plaster'))
        for a0, a1 in [(-5.0, -3.0), (4.0, 6.4)]:
            pp.append(box(xw, (a0 + a1) / 2, F + 2.7, 0.2, a1 - a0, HC - F - 2.7, 'Plaster'))
    return shell

def title_parts(text, y0, depth, z0, z1, max_w):
    adv = 0.0
    for ch in text:
        adv += GLYPHS[ch][0]
    s = min(max_w / adv, (z1 - z0) / 1.0)
    width = adv * s
    x = width / 2
    zb = (z0 + z1) / 2 - s / 2
    out = []
    for ch in text:
        a, shapes = GLYPHS[ch]
        for outer, holes in shapes:
            pts = [[x - u * s, zb + v * s] for u, v in outer]
            hl = [[[x - u * s, zb + v * s] for u, v in h] for h in holes]
            out.append(prism(pts, y0, depth, 'Title_Letters', holes=hl, ax='y'))
        x -= a * s
    return out

def build_towers(root):
    for t in TOWERS:
        g = add(root, node('Rotor_Tower_' + t['name']))
        p = g['parts']
        cx, cy, phi = t['cx'], t['cy'], t['phi']
        al = math.acos(-TD / TR)
        a0, a1 = phi - al, phi + al
        # striped stone drum, open towards the hall
        z, k = 0.0, 0
        while z < HW - 0.001:
            hz = min(0.6, HW - z)
            p.append(arc_wall(cx, cy, z, TR, TR - (T - 0.04), hz, a0, a1, 'Stone' if k % 2 == 0 else 'Stone_Band'))
            z += hz
            k += 1
        p.append(arc_wall(cx, cy, F, TR - (T - 0.04), TR - T, HC - F, a0, a1, 'Plaster'))
        # upper drum above the hall parapet, ring cap
        p.append(ring(cx, cy, HW, TR + 0.06, TR - T, TOWER_TOP - HW - 0.15, 'Stone_Dark'))
        p.append(ring(cx, cy, TOWER_TOP - 0.15, TR + 0.15, 2.0, 0.15, 'Title_Band'))
        p.append(cyl(cx, cy, 0.0, TR - T + 0.01, F, 'Floor_Tile', 36))
        # slit windows
        for da in (-0.8, 0.0, 0.8):
            a = phi + da
            p.append(box(cx + math.cos(a) * (TR - T / 2), cy + math.sin(a) * (TR - T / 2), F + 1.4, T + 0.06, 0.5, 1.5,
                         'Glass_Dark', math.degrees(a)))
        # navigation light on the outer rim (red front, green rear)
        nl = 'Nav_Red' if t['front'] else 'Nav_Green'
        p.append(lathe(cx + math.cos(phi) * (TR + 0.05), cy + math.sin(phi) * (TR + 0.05), TOWER_TOP,
                       [[0, 0.18], [0.12, 0.2], [0.3, 0.12], [0.36, 0]], nl, 12))
        deck = add(root, node('Tower_Deck_' + t['name'], layer='Roof'))
        deck['parts'].append(cyl(cx, cy, HC, TR - T + 0.01, HW - HC, 'Roof', 36))
        # motor (component) and spinning propeller (component inside an animated group)
        g['insts'].append(inst('Rotor_Motor', 'Motor_' + t['name'], cx, cy, TOWER_TOP, 0))
        g['insts'].append(inst('Prop_Guard', 'Guard_' + t['name'], cx, cy, TOWER_TOP, math.degrees(phi)))
        prop = add(g, node('Propeller_' + t['name'], pos=[cx, cy, 0], rot=30 + 45 * TOWERS.index(t),
                           anim={'spin': t['spin'], 'rpm': 160}))
        prop['insts'].append(inst('Propeller_2B', 'Prop_' + t['name'], 0, 0, 0, 0))

def tube(pts, r, m):
    """Square-section rib along a 3D polyline (glass-dome frame members)."""
    verts, faces = [], []
    n = len(pts)
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        tx, ty, tz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        L = math.sqrt(tx * tx + ty * ty + tz * tz) or 1.0
        tx, ty, tz = tx / L, ty / L, tz / L
        ux, uy, uz = (0.0, 0.0, 1.0) if abs(tz) < 0.9 else (1.0, 0.0, 0.0)
        # side = t x up, nrm = side x t
        sx, sy, sz = ty * uz - tz * uy, tz * ux - tx * uz, tx * uy - ty * ux
        sl = math.sqrt(sx * sx + sy * sy + sz * sz) or 1.0
        sx, sy, sz = sx / sl, sy / sl, sz / sl
        nx, ny, nz = sy * tz - sz * ty, sz * tx - sx * tz, sx * ty - sy * tx
        x, y, z = pts[i]
        for cu, cv in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
            verts.append([round(x + (sx * cu + nx * cv) * r, 4), round(y + (sy * cu + ny * cv) * r, 4), round(z + (sz * cu + nz * cv) * r, 4)])
    for i in range(n - 1):
        for k in range(4):
            a0, a1 = 4 * i + k, 4 * i + (k + 1) % 4
            b0, b1 = a0 + 4, a1 + 4
            faces += [[a0, a1, b1], [a0, b1, b0]]
    return {'k': 'mesh', 'v': verts, 'f': faces, 'm': m}

DOME_R, DOME_H, DOME_Z = 4.6, 4.3, HR + 0.75     # glass dome on a low composite drum

def dome_prof(k):
    """Dome profile point at parameter k (0 = springing, 1 = crown): returns (dz, r)."""
    a = k * PI / 2
    return DOME_H * math.sin(a), DOME_R * math.cos(a)

def build_drone_core(root):
    """Flight-controller hub on the roof: a steel-framed glass dome on a composite drum, and four carbon arms out to the rotor towers."""
    g = add(root, node('Drone_Core'))
    p = g['parts']
    # drum (plinth) with LED band
    p.append(cyl(0, 0, HR, DOME_R + 0.45, 0.75, 'Composite_Grey', 64))
    p.append(ring(0, 0, HR + 0.5, DOME_R + 0.5, DOME_R + 0.38, 0.12, 'Led_Blue', 96))
    p.append(ring(0, 0, DOME_Z - 0.02, DOME_R + 0.2, DOME_R - 0.25, 0.14, 'Metal_Dark', 96))
    # glazing (one lathe shell, transparent)
    prof = [[0, 0.02]] + [[round(dome_prof(i / 16.0)[0], 4), round(max(dome_prof(i / 16.0)[1], 0.02), 4)] for i in range(17)]
    p.append(lathe(0, 0, DOME_Z, [[a, b * 0.995] for a, b in prof][1:], 'Glass', 64))
    # steel frame: 16 meridian ribs, 4 latitude rings, crown oculus
    for i in range(16):
        ang = 2 * PI * i / 16
        pts = []
        for j in range(15):
            dz, r = dome_prof(j / 15.0 * 0.93)
            pts.append([math.cos(ang) * (r + 0.03), math.sin(ang) * (r + 0.03), DOME_Z + dz])
        p.append(tube(pts, 0.055, 'Metal_Dark'))
    for k in (0.22, 0.45, 0.66, 0.84):
        dz, r = dome_prof(k)
        pts = [[math.cos(2 * PI * i / 64) * (r + 0.03), math.sin(2 * PI * i / 64) * (r + 0.03), DOME_Z + dz] for i in range(65)]
        p.append(tube(pts, 0.045, 'Metal_Dark'))
    dz, r = dome_prof(0.93)
    p.append(ring(0, 0, DOME_Z + dz - 0.05, r + 0.12, r - 0.1, 0.16, 'Metal_Dark', 48))
    p.append(lathe(0, 0, DOME_Z + DOME_H - 0.12, [[0, r * 0.95], [0.3, r * 0.7], [0.42, 0.1], [0.44, 0]], 'Glass', 32))
    # beacon finial
    p.append(cyl(0, 0, DOME_Z + DOME_H + 0.2, 0.06, 0.9, 'Aluminium', 10))
    p.append(lathe(0, 0, DOME_Z + DOME_H + 1.05, [[0, 0.14], [0.12, 0.16], [0.26, 0.1], [0.3, 0]], 'Nav_Red', 14))
    # inside the glass: flight-controller core on a lit plinth, ring of status LEDs
    p.append(cyl(0, 0, DOME_Z, 2.2, 0.35, 'Metal_Dark', 48))
    p.append(lathe(0, 0, DOME_Z + 0.35, [[0, 1.5], [1.2, 1.5], [1.6, 1.2], [1.85, 0.5], [1.9, 0]], 'Composite_Grey', 40))
    p.append(ring(0, 0, DOME_Z + 0.95, 1.56, 1.46, 0.1, 'Led_Blue', 48))
    p.append(cyl(0, 0, DOME_Z + 0.36, 2.18, 0.02, 'Light_Panel', 48))
    # gimbal camera at the front of the drum
    p.append(lathe(0, DOME_R + 0.75, HR + 0.1, [[0, 0], [0.1, 0.4], [0.4, 0.55], [0.7, 0.4], [0.8, 0]], 'Carbon', 20))
    p.append(cyl(0, DOME_R + 1.25, HR + 0.33, 0.15, 0.12, 'Glass_Dark', 16))
    for t in TOWERS:
        dist = math.hypot(t['cx'], t['cy'])
        ang = math.degrees(math.atan2(t['cy'], t['cx']))
        r0, r1 = DOME_R + 0.4, dist - TR + 0.05
        mid = (r0 + r1) / 2
        ux, uy = t['cx'] / dist, t['cy'] / dist
        p.append(box(ux * mid, uy * mid, HW + 0.1, r1 - r0, 1.3, 0.75, 'Carbon', ang))
        p.append(box(ux * mid, uy * mid, HW + 0.85, r1 - r0, 0.3, 0.06, 'Led_Blue', ang))
        for rr in (7.5, 12.0):
            p.append(cyl(ux * rr, uy * rr, HR, 0.28, HW + 0.1 - HR, 'Aluminium', 12))

# ---------------------------------------------------------------- component definitions
def defs_all():
    d = {}
    # rotor motor: base plate, finned stator can, bell, spinner shaft
    m = node('Rotor_Motor')
    m['parts'] += [cyl(0, 0, 0, 2.6, 0.3, 'Carbon', 40),
                   lathe(0, 0, 0.3, [[0, 2.25], [1.2, 2.25], [1.3, 2.05], [1.5, 1.95], [1.62, 1.6], [1.62, 0]], 'Metal_Dark', 40),
                   ring(0, 0, 1.0, 2.3, 2.24, 0.12, 'Led_Blue', 48),
                   cyl(0, 0, 1.62, 0.32, 0.4, 'Aluminium', 16)]
    for i in range(24):
        a = 2 * PI * i / 24
        m['parts'].append(box(math.cos(a) * 2.37, math.sin(a) * 2.37, 0.35, 0.26, 0.06, 0.8, 'Metal_Dark', math.degrees(a)))
    d['Rotor_Motor'] = m
    # propeller: two tapered carbon blades with orange tips and a spinner, blade plane at PROP_Z
    pr = node('Propeller_2B')
    zb = PROP_Z - TOWER_TOP - 0.06
    zr = PROP_Z
    blade = [[0.55, -0.42], [1.4, -0.66], [2.6, -0.62], [3.8, -0.48], [4.7, -0.34], [4.7, 0.2], [3.8, 0.28], [2.6, 0.38], [1.4, 0.44], [0.55, 0.32]]
    tip = [[4.7, -0.34], [5.25, -0.24], [5.5, -0.1], [5.55, 0.02], [5.45, 0.12], [5.2, 0.16], [4.7, 0.2]]
    for k in (0, 1):
        rot = [] ; rtip = []
        for u, v in blade:
            rot.append([u if k == 0 else -u, v if k == 0 else -v])
        for u, v in tip:
            rtip.append([u if k == 0 else -u, v if k == 0 else -v])
        pr['parts'].append(prism(rot, zr, 0.1, 'Carbon'))
        pr['parts'].append(prism(rtip, zr, 0.1, 'Prop_Tip'))
    pr['parts'].append(lathe(0, 0, zr - 0.2, [[0, 0.78], [0.35, 0.78], [0.7, 0.55], [0.95, 0.22], [1.02, 0]], 'Composite_Grey', 24))
    d['Propeller_2B'] = pr
    # guard ring on four struts
    gd = node('Prop_Guard')
    gd['parts'].append(ring(0, 0, PROP_Z - TOWER_TOP - 0.15, 6.15, 5.9, 0.34, 'Carbon', 72))
    gd['parts'].append(ring(0, 0, PROP_Z - TOWER_TOP + 0.19, 6.15, 5.9, 0.05, 'Gate_Orange', 72))
    for i in range(4):
        a = PI / 4 + i * PI / 2
        r0, r1 = TR - 0.2, 5.95
        gd['parts'].append(box(math.cos(a) * (r0 + r1) / 2, math.sin(a) * (r0 + r1) / 2, PROP_Z - TOWER_TOP - 0.15, r1 - r0, 0.22, 0.3, 'Carbon', math.degrees(a)))
        gd['parts'].append(box(math.cos(a) * (TR - 0.2), math.sin(a) * (TR - 0.2), 0.0, 0.25, 0.25, PROP_Z - TOWER_TOP - 0.15, 'Carbon', math.degrees(a)))
    d['Prop_Guard'] = gd
    # tiered lecture seat, faces -x (towards the stage in the west)
    s = node('Lecture_Seat')
    s['parts'] += [box(0, 0, 0.0, 0.42, 0.42, 0.1, 'Metal_Dark'),
                   box(0, 0, 0.1, 0.12, 0.12, 0.32, 'Metal_Dark'),
                   box(-0.02, 0, 0.42, 0.5, 0.5, 0.1, 'Seat_Fabric'),
                   box(0.26, 0, 0.42, 0.1, 0.52, 0.62, 'Seat_Fabric'),
                   box(0.3, 0, 0.42, 0.04, 0.52, 0.62, 'Metal_Dark')]
    for sy in (-0.29, 0.29):
        s['parts'] += [box(0.02, sy, 0.1, 0.5, 0.06, 0.55, 'Wood'), box(-0.02, sy, 0.65, 0.58, 0.08, 0.04, 'Wood')]
    d['Lecture_Seat'] = s
    # acoustic wall slat
    d['Acoustic_Slat'] = node('Acoustic_Slat', [box(0, 0, 0, 0.09, 0.05, 3.6, 'Wood_Slat')])
    # simulator station: pilot faces +x
    st = node('Simulator_Station')
    sp = st['parts']
    sp += [box(0.75, 0, 0.0, 0.8, 1.7, 0.04, 'Carpet'),
           box(0.75, 0, 0.72, 0.8, 1.7, 0.05, 'Composite_Grey'),
           box(0.42, -0.78, 0.0, 0.06, 0.08, 0.72, 'Metal_Dark'), box(0.42, 0.78, 0.0, 0.06, 0.08, 0.72, 'Metal_Dark'),
           box(1.08, -0.78, 0.0, 0.06, 0.08, 0.72, 'Metal_Dark'), box(1.08, 0.78, 0.0, 0.06, 0.08, 0.72, 'Metal_Dark'),
           box(1.08, 0, 0.3, 0.04, 1.5, 0.4, 'Metal_Dark')]
    for dy, ang in [(0, 0.0), (-0.66, -28.0), (0.66, 28.0)]:          # triple monitors
        cxm, cym = 1.0 - (0.1 if dy else 0), dy
        sp.append(box(cxm, cym, 0.95, 0.05, 0.62, 0.38, 'Carbon', ang))
        sp.append(box(cxm - 0.03 * math.cos(math.radians(ang)), cym - 0.03 * math.sin(math.radians(ang)), 0.97, 0.01, 0.58, 0.34, 'Screen_Glow', ang))
        sp.append(box(cxm + 0.04, cym, 0.77, 0.05, 0.05, 0.2, 'Metal_Dark', ang))
    sp += [box(0.62, 0, 0.77, 0.22, 0.32, 0.07, 'Carbon'),                       # RC transmitter
           cyl(0.62, -0.08, 0.84, 0.012, 0.08, 'Aluminium', 8), cyl(0.62, 0.08, 0.84, 0.012, 0.08, 'Aluminium', 8),
           box(0.62, 0.45, 0.77, 0.16, 0.2, 0.08, 'Carbon'),                      # FPV goggles
           box(0.62, -0.5, 0.77, 0.14, 0.22, 0.04, 'Metal_Dark')]                 # flight-controller pad
    # racing-style pilot seat
    sp += [cyl(-0.15, 0, 0.0, 0.28, 0.06, 'Metal_Dark', 5), cyl(-0.15, 0, 0.06, 0.05, 0.38, 'Aluminium', 10),
           box(-0.12, 0, 0.44, 0.52, 0.52, 0.1, 'Leather_Black'), box(-0.42, 0, 0.5, 0.1, 0.54, 0.85, 'Leather_Black'),
           box(-0.42, 0, 0.9, 0.11, 0.3, 0.3, 'Curtain'),
           box(-0.12, -0.3, 0.54, 0.4, 0.08, 0.16, 'Leather_Black'), box(-0.12, 0.3, 0.54, 0.4, 0.08, 0.16, 'Leather_Black')]
    d['Simulator_Station'] = st
    # display quadcopter (1.8 m span), sits on its own landing legs
    q = node('Display_Quad')
    qp = q['parts']
    qp += [box(0, 0, 0.32, 0.55, 0.38, 0.16, 'Carbon'), lathe(0, 0, 0.48, [[0, 0.2], [0.08, 0.18], [0.14, 0]], 'Composite_Grey', 16),
           lathe(0.3, 0, 0.22, [[0, 0], [0.05, 0.08], [0.12, 0.08], [0.16, 0]], 'Carbon', 12)]
    for i in range(4):
        a = PI / 4 + i * PI / 2
        ca, sa = math.cos(a), math.sin(a)
        qp.append(box(ca * 0.48, sa * 0.48, 0.36, 0.72, 0.07, 0.06, 'Carbon', math.degrees(a)))
        qp.append(cyl(ca * 0.82, sa * 0.82, 0.33, 0.07, 0.12, 'Metal_Dark', 12))
        qp.append(box(ca * 0.82, sa * 0.82, 0.46, 0.62, 0.06, 0.012, 'Carbon', math.degrees(a) + 60))
        qp.append(box(ca * 0.82, sa * 0.82, 0.455, 0.08, 0.08, 0.02, 'Prop_Tip'))
        qp.append(box(ca * 0.35, sa * 0.35, 0.0, 0.04, 0.04, 0.32, 'Metal_Dark'))
    q['parts'] = qp
    d['Display_Quad'] = q
    # small training quad for the landing pads
    sq = node('Training_Quad')
    sqp = sq['parts']
    sqp.append(box(0, 0, 0.1, 0.2, 0.16, 0.07, 'Carbon'))
    for i in range(4):
        a = PI / 4 + i * PI / 2
        sqp.append(box(math.cos(a) * 0.17, math.sin(a) * 0.17, 0.12, 0.26, 0.03, 0.025, 'Carbon', math.degrees(a)))
        sqp.append(cyl(math.cos(a) * 0.3, math.sin(a) * 0.3, 0.12, 0.13, 0.012, 'Prop_Tip', 16))
        sqp.append(box(math.cos(a) * 0.12, math.sin(a) * 0.12, 0.0, 0.02, 0.02, 0.1, 'Metal_Dark'))
    d['Training_Quad'] = sq
    # race gate (2.4 m opening), oriented across x
    g = node('Race_Gate')
    g['parts'] += [box(0, -1.35, 0, 0.3, 0.3, 2.7, 'Gate_Orange'), box(0, 1.35, 0, 0.3, 0.3, 2.7, 'Gate_Orange'),
                   box(0, 0, 2.7, 0.3, 3.0, 0.3, 'Gate_Orange'), box(0, 0, 2.45, 0.32, 2.4, 0.1, 'Carbon'),
                   box(0, -1.35, 0, 0.6, 0.6, 0.1, 'Carbon'), box(0, 1.35, 0, 0.6, 0.6, 0.1, 'Carbon')]
    d['Race_Gate'] = g
    # landing pad
    lp = node('Landing_Pad')
    lp['parts'] += [cyl(0, 0, 0, 3.2, 0.06, 'Concrete', 40), ring(0, 0, 0.06, 2.6, 2.3, 0.012, 'Marking_Yellow', 48),
                    box(0, 0, 0.06, 2.6, 0.22, 0.012, 'Marking_White'), box(0, 0, 0.06, 0.22, 2.6, 0.012, 'Marking_White')]
    d['Landing_Pad'] = lp
    # street light
    sl = node('Street_Light')
    sl['parts'] += [cyl(0, 0, 0, 0.18, 0.5, 'Concrete', 12), cyl(0, 0, 0.5, 0.08, 7.0, 'Metal_Dark', 12),
                    box(0.6, 0, 7.4, 1.3, 0.12, 0.1, 'Metal_Dark'), box(1.15, 0, 7.28, 0.6, 0.3, 0.12, 'Light_Panel')]
    d['Street_Light'] = sl
    # desert shrub
    d['Shrub'] = node('Shrub', [lathe(0, 0, 0, [[0, 0.5], [0.35, 0.95], [0.8, 0.8], [1.1, 0.35], [1.2, 0]], 'Shrub', 9)])
    # tactical vehicle (olive, 5 m)
    v = node('Tactical_Vehicle')
    vp = v['parts']
    vp += [box(0, 0, 0.45, 5.0, 2.1, 0.9, 'Olive'), box(-0.6, 0, 1.35, 2.4, 2.0, 0.85, 'Olive'),
           box(-0.6, 0, 1.45, 2.42, 1.9, 0.55, 'Glass_Dark'), box(1.7, 0, 1.35, 1.6, 2.0, 0.6, 'Olive'),
           box(2.55, 0, 0.5, 0.12, 1.9, 0.5, 'Metal_Dark')]
    for wx in (-1.6, 1.6):
        for wy in (-0.95, 0.95):
            vp.append(prism(circle_pts(wx, 0.45, 0.45, 16), wy - 0.15, 0.3, 'Tyre', ax='y'))
    d['Tactical_Vehicle'] = v
    # ground control station truck with dish
    gcs = node('GCS_Truck')
    gp = gcs['parts']
    gp += [box(0, 0, 0.5, 7.0, 2.4, 0.5, 'Metal_Dark'), box(2.6, 0, 1.0, 1.8, 2.4, 1.6, 'Olive'),
           box(2.9, 0, 1.9, 1.2, 2.42, 0.6, 'Glass_Dark'), box(-0.9, 0, 1.0, 4.6, 2.45, 2.3, 'Olive'),
           cyl(-2.2, 0, 3.3, 0.12, 1.2, 'Metal_Dark', 10),
           lathe(-2.2, 0, 4.4, [[0, 0.1], [0.25, 0.7], [0.4, 1.1], [0.42, 0]], 'Aluminium', 24),
           cyl(-0.2, 0.8, 3.3, 0.04, 2.5, 'Metal_Dark', 8)]
    for wx in (-2.4, -1.2, 2.5):
        for wy in (-1.05, 1.05):
            gp.append(prism(circle_pts(wx, 0.55, 0.55, 16), wy - 0.18, 0.36, 'Tyre', ax='y'))
    d['GCS_Truck'] = gcs
    # executive office desk (front edge at +x)
    od = node('Office_Desk')
    od['parts'] += [box(0, 0, 0.72, 0.9, 1.8, 0.05, 'Wood'), box(-0.4, 0, 0, 0.06, 1.7, 0.72, 'Wood'),
                    box(0, -0.85, 0, 0.85, 0.06, 0.72, 'Wood'), box(0, 0.85, 0, 0.85, 0.06, 0.72, 'Wood'),
                    box(0.15, 0.35, 0.77, 0.05, 0.5, 0.32, 'Carbon'), box(0.0, -0.4, 0.77, 0.3, 0.22, 0.03, 'Flag_White')]
    d['Office_Desk'] = od
    # high-back executive chair, sitter faces +x
    ec = node('Executive_Chair')
    ec['parts'] += [cyl(0, 0, 0, 0.32, 0.06, 'Metal_Dark', 5), cyl(0, 0, 0.06, 0.05, 0.38, 'Aluminium', 10),
                    box(0, 0, 0.44, 0.56, 0.56, 0.12, 'Leather_Black'), box(-0.3, 0, 0.5, 0.12, 0.58, 0.95, 'Leather_Black'),
                    box(0.02, -0.32, 0.6, 0.45, 0.08, 0.2, 'Leather_Black'), box(0.02, 0.32, 0.6, 0.45, 0.08, 0.2, 'Leather_Black')]
    d['Executive_Chair'] = ec
    return d

# ---------------------------------------------------------------- interiors
def build_interiors(root):
    it = add(root, node('Interiors'))
    # ----- lecture hall (west): stage, screen, 60 seats on tiers, acoustic slats
    hall = add(it, node('Lecture_Hall'))
    hp = hall['parts']
    xi = -W + T
    hall_floor = [[X_HALL - 0.1, D - T], [-(W - C) + 0.2, D - T], [xi, D - C + 0.1], [xi, -(D - C) - 0.1], [-(W - C) + 0.2, -(D - T)], [X_HALL - 0.1, -(D - T)]]
    hp.append(prism(hall_floor, F, 0.02, 'Carpet'))
    hp.append(prism([[xi, 6.2], [xi, -6.2], [-13.2, -6.2], [-13.2, 6.2]], F + 0.02, 0.68, 'Stage_Wood'))
    hp.append(box(-13.0, 0, F + 0.02, 0.4, 8.0, 0.34, 'Stage_Wood'))
    hp.append(box(-17.45, 0, F + 1.9, 0.12, 5.4, 3.0, 'Carbon'))           # screen frame (16:9)
    hp.append(box(-17.37, 0, F + 2.0, 0.04, 5.2, 2.8, 'Screen_Off'))
    for sy in (-1, 1):
        hp.append(box(-17.3, sy * 3.15, F + 0.7, 0.3, 0.6, HC - F - 0.75, 'Curtain'))
        hp.append(box(-16.9, sy * 6.05, F + 0.7, 0.55, 0.55, 1.5, 'Carbon'))         # speakers
    # portraits flanking the screen: Quaid-e-Azam (audience left, south), Allama Iqbal (north)
    for sy, who in ((-1, 'Portrait_Quaid'), (1, 'Portrait_Iqbal')):
        yc, z0, z1, w = sy * 4.55, F + 2.3, F + 3.49, 1.4
        hp.append(prism([[yc - w / 2 - 0.1, z0 - 0.1], [yc + w / 2 + 0.1, z0 - 0.1], [yc + w / 2 + 0.1, z1 + 0.1], [yc - w / 2 - 0.1, z1 + 0.1]],
                        -W + T, 0.06, 'Frame_Gold', holes=[[[yc - w / 2, z0], [yc - w / 2, z1], [yc + w / 2, z1], [yc + w / 2, z0]]], ax='x'))
        hp.append(prism([[yc - w / 2, z0], [yc + w / 2, z0], [yc + w / 2, z1], [yc - w / 2, z1]], -W + T, 0.025, who, ax='x'))
    hp.append(box(-14.4, 4.0, F + 0.7, 0.6, 0.7, 1.15, 'Wood'))                     # lectern
    hp.append(box(-14.5, 4.0, F + 1.85, 0.5, 0.75, 0.06, 'Wood', 0))
    hp.append(cyl(-14.25, 3.8, F + 1.91, 0.01, 0.35, 'Metal_Dark', 6))
    hp.append(box(-15.6, -1.2, F + 0.7, 1.0, 4.0, 0.76, 'Wood'))                    # panel table
    hp.append(box(-15.6, -1.2, F + 1.46, 1.1, 4.2, 0.04, 'Curtain'))
    hall['insts'] += [inst('Lecture_Seat', 'Panel_Chair_1', -16.5, -2.6, F + 0.7, 180), inst('Lecture_Seat', 'Panel_Chair_2', -16.5, -1.2, F + 0.7, 180),
                      inst('Lecture_Seat', 'Panel_Chair_3', -16.5, 0.2, F + 0.7, 180)]
    # tiers and seats: 10 rows x 10 seats = 100, centre aisle, side aisles at floor level, facing the stage
    rows = [-12.2 + 0.9 * i for i in range(10)]
    n = 0
    for ri, rx in enumerate(rows):
        zt = F + 0.02 + 0.12 * ri
        if ri > 0:
            hp.append(prism([[rx - 0.55, -3.75], [X_HALL - 0.12, -3.75], [X_HALL - 0.12, 3.75], [rx - 0.55, 3.75]], zt - 0.12, 0.12, 'Carpet'))
        for side in (-1, 1):
            for k in range(5):
                n += 1
                y = side * (0.85 + k * 0.62)
                hall['insts'].append(inst('Lecture_Seat', 'Seat_' + str(n).zfill(2), rx, y, zt, 0))
    # AV desk at the back, acoustic slats on the long walls
    hp.append(box(-4.0, 8.6, F, 1.6, 0.8, 0.76, 'Wood'))
    hp.append(box(-3.7, 8.6, F + 0.76, 0.05, 0.6, 0.4, 'Carbon'))
    for sy in (-1, 1):
        x = -11.0
        while x < -3.6:
            hall['insts'].append(inst('Acoustic_Slat', 'Slat', x, sy * (D - T - 0.03), F + 0.9, 0))
            x += 0.3
    # ----- foyer: reception, display drones, seating
    foy = add(it, node('Foyer'))
    fp = foy['parts']
    fp.append(prism([[X_HALL + 0.1, -D + T], [X_SIM - 0.1, -D + T], [X_SIM - 0.1, D - T], [X_HALL + 0.1, D - T]], F, 0.015, 'Floor_Tile'))
    fp.append(box(0.5, 1.6, F, 3.6, 0.7, 1.1, 'Wood'))
    fp.append(box(0.5, 1.6, F + 1.1, 3.8, 0.85, 0.05, 'Carbon'))
    fp.append(box(0.5, 1.2, F + 0.15, 3.4, 0.05, 0.1, 'Led_Blue'))
    fp.append(cyl(0.5, 6.8, F, 1.1, 0.75, 'Carbon', 40))
    fp.append(ring(0.5, 6.8, F + 0.75, 1.1, 1.0, 0.04, 'Led_Blue', 40))
    foy['insts'].append(inst('Display_Quad', 'Display_Quad_Foyer', 0.5, 6.8, F + 0.79, 20))
    # fixed-wing UAV model on a stand
    fp += [cyl(0.5, -6.0, F, 0.45, 0.1, 'Carbon', 20), cyl(0.5, -6.0, F + 0.1, 0.05, 1.3, 'Aluminium', 10),
           box(0.5, -6.0, F + 1.4, 2.2, 0.22, 0.22, 'Composite_Grey'), box(0.4, -6.0, F + 1.5, 0.5, 3.2, 0.04, 'Composite_Grey'),
           box(-0.55, -6.0, F + 1.45, 0.3, 1.0, 0.03, 'Composite_Grey'), box(-0.6, -6.0, F + 1.48, 0.25, 0.03, 0.35, 'Composite_Grey'),
           box(1.65, -6.0, F + 1.45, 0.12, 0.5, 0.04, 'Carbon')]
    for sy in (-1, 1):
        fp.append(box(X_HALL + 0.55, sy * 9.0, F, 0.8, 2.2, 0.42, 'Upholstery_Grey'))
        fp.append(box(X_HALL + 0.2, sy * 9.0, F + 0.42, 0.2, 2.2, 0.45, 'Upholstery_Grey'))
        fp.append(cyl(X_SIM - 0.6, sy * 10.2, F, 0.28, 0.45, 'Plant_Pot', 14))
        fp.append(lathe(X_SIM - 0.6, sy * 10.2, F + 0.45, [[0, 0.3], [0.4, 0.5], [0.9, 0.35], [1.2, 0]], 'Shrub', 10))
    fp.append(box(X_SIM - 0.12, -1.0, F + 1.4, 0.04, 2.8, 1.6, 'Screen_Off'))
    # ----- simulator complex (east): 8 stations facing a video wall, instructor console, motion pod
    sim = add(it, node('Simulator_Complex'))
    sp = sim['parts']
    sp.append(prism([[X_SIM + 0.1, -D + T], [W - C, -D + T], [W - T, -(D - C)], [W - T, D - C], [W - C, D - T], [X_SIM + 0.1, D - T]], F, 0.02, 'Carpet'))
    k = 0
    for rx in (8.6, 12.4):
        for ry in (-5.4, -1.8, 1.8, 5.4):
            k += 1
            sim['insts'].append(inst('Simulator_Station', 'Sim_Station_' + str(k), rx, ry, F + 0.02, 0))
    # video wall 3x2 on the east wall
    for i in range(3):
        for j in range(2):
            sp.append(box(W - T - 0.08, -2.6 + i * 2.6, F + 1.3 + j * 1.5, 0.1, 2.55, 1.45, 'Carbon'))
            sp.append(box(W - T - 0.14, -2.6 + i * 2.6, F + 1.35 + j * 1.5, 0.02, 2.45, 1.35, 'Screen_Glow'))
    # instructor console (L desk with 4 monitors)
    sp += [box(5.6, 0, F, 1.0, 4.2, 0.76, 'Wood'), box(5.6, 0, F + 0.76, 1.05, 4.3, 0.04, 'Carbon')]
    for i in range(4):
        y = -1.5 + i
        sp.append(box(5.95, y, F + 0.95, 0.05, 0.9, 0.52, 'Carbon'))
        sp.append(box(5.92, y, F + 0.98, 0.01, 0.85, 0.46, 'Screen_Glow'))
    sim['insts'].append(inst('Lecture_Seat', 'Instructor_Seat', 4.85, 0, F + 0.02, 180))
    # full-motion simulator pod on a hexapod
    sp += [cyl(7.0, -8.8, F, 1.3, 0.2, 'Metal_Dark', 6), ring(7.0, -8.8, F + 1.0, 1.25, 0.9, 0.12, 'Aluminium', 24)]
    for i in range(6):
        a = 2 * PI * i / 6
        sp.append(cyl(7.0 + math.cos(a) * 1.0, -8.8 + math.sin(a) * 1.0, F + 0.2, 0.07, 0.8, 'Aluminium', 8))
    sp.append(lathe(7.0, -8.8, F + 1.12, [[0, 1.1], [0.6, 1.2], [1.3, 1.0], [1.7, 0.55], [1.85, 0]], 'Flag_White', 28))
    sp.append(box(7.95, -8.8, F + 1.6, 0.2, 1.2, 0.6, 'Glass_Dark'))
    # ----- tower rooms (inner radius TR - T; door faces the hall at da = pi)
    RI = TR - T
    for t in TOWERS:
        tr = add(it, node('Tower_Room_' + t['name']))
        cx, cy, phi = t['cx'], t['cy'], t['phi']
        deg = math.degrees(phi)
        rp = tr['parts']
        def at(dist, da):
            return cx + math.cos(phi + da) * dist, cy + math.sin(phi + da) * dist
        def wall_box(da, gap, w, d, h, z, m):
            # box standing against the curved wall: width along the wall, depth towards the centre
            x, y = at(RI - gap - d / 2, da)
            return box(x, y, z, w, d, h, m, deg + math.degrees(da) + 90)
        def free_box(dist, da, w, d, h, z, m, extra=0.0):
            x, y = at(dist, da)
            return box(x, y, z, w, d, h, m, deg + math.degrees(da) + 90 + extra)
        rp.append(prism(circle_pts(cx, cy, RI + 0.01, 40), F, 0.012, 'Tile_Wet' if t['name'] == 'NW' else 'Floor_Tile'))
        rp.append(lathe(cx, cy, HC - 0.06, [[0, 0.45], [0.04, 0.45], [0.06, 0]], 'Light_Panel', 24))
        if t['name'] == 'NW':      # Washrooms: WC cubicles, urinals, vanity with basins, wuzu (ablution) area
            rp.append(arc_wall(cx, cy, F, RI, RI - 0.015, 2.1, phi - 2.45, phi + 2.45, 'Tile_Wet', 40))
            for k, da in enumerate((-0.55, 0.0, 0.55)):                       # three WC cubicles on the outer wall
                rp.append(wall_box(da, 0.0, 0.42, 0.2, 0.75, F + 0.38, 'Sanitary_White'))       # cistern
                rp.append(free_box(RI - 0.55, da, 0.4, 0.55, 0.4, F, 'Sanitary_White'))           # pan
                rp.append(free_box(RI - 0.55, da, 0.42, 0.5, 0.03, F + 0.4, 'Composite_Grey'))   # seat
                rp.append(free_box(RI - 1.38, da, 0.72, 0.04, 1.85, F + 0.15, 'Laminate'))        # cubicle door
            for da in (-0.825, -0.275, 0.275, 0.825):                         # cubicle partitions (radial)
                x, y = at(RI - 0.7, da)
                rp.append(box(x, y, F + 0.15, 1.4, 0.04, 1.85, 'Laminate', deg + math.degrees(da)))
            for da in (1.0, 1.15):                                            # hand dryer and towel dispenser
                rp.append(wall_box(da, 0.0, 0.28, 0.2, 0.35, F + 1.2, 'Aluminium'))
            rp.append(wall_box(-1.55, 0.0, 2.1, 0.55, 0.85, F, 'Laminate'))     # vanity counter
            rp.append(wall_box(-1.55, 0.0, 2.15, 0.6, 0.05, F + 0.85, 'Sanitary_White'))
            for dd in (-0.22, 0.0, 0.22):
                rp.append(wall_box(-1.55 + dd, 0.18, 0.42, 0.34, 0.06, F + 0.9, 'Tile_Wet'))   # basin bowls
                rp.append(wall_box(-1.55 + dd, 0.04, 0.05, 0.12, 0.22, F + 0.9, 'Aluminium'))  # taps
            rp.append(wall_box(-1.55, 0.005, 1.9, 0.02, 0.9, F + 1.25, 'Mirror'))
            rp.append(wall_box(1.55, 0.35, 1.1, 0.35, 0.38, F, 'Tile_Wet'))    # wuzu bench
            rp.append(wall_box(1.55, 0.0, 1.1, 0.12, 0.12, F + 0.75, 'Aluminium'))
            for dd in (-0.16, 0.0, 0.16):
                rp.append(wall_box(1.55 + dd, 0.1, 0.04, 0.12, 0.05, F + 0.7, 'Aluminium'))
            rp.append(wall_box(1.55, 0.75, 1.1, 0.12, 0.02, F + 0.01, 'Metal_Dark'))          # floor drain channel
            rp.append(wall_box(0.0, 0.0, 0.35, 0.08, 0.35, F + 2.55, 'Composite_Grey'))       # exhaust fan
        elif t['name'] == 'NE':    # Office (OIC Drone Trg)
            rp.append(prism(circle_pts(cx, cy, 2.3, 40), F + 0.012, 0.012, 'Curtain'))
            x, y = at(1.3, 0)
            tr['insts'].append(inst('Office_Desk', 'OIC_Desk', x, y, F, deg + 180))
            x, y = at(2.2, 0)
            tr['insts'].append(inst('Executive_Chair', 'OIC_Chair', x, y, F, deg + 180))
            for k, da in enumerate((-0.4, 0.4)):
                x, y = at(0.35, da)
                tr['insts'].append(inst('Lecture_Seat', 'Visitor_Chair_' + str(k + 1), x, y, F, deg + 180))
            rp.append(wall_box(-1.45, 0.05, 2.0, 0.8, 0.42, F, 'Leather_Black'))              # sofa
            rp.append(wall_box(-1.45, 0.05, 2.0, 0.2, 0.45, F + 0.42, 'Leather_Black'))
            rp.append(free_box(1.85, -1.45, 1.0, 0.55, 0.42, F, 'Wood'))                      # coffee table
            rp.append(wall_box(1.45, 0.0, 1.0, 0.4, 2.0, F, 'Wood'))                          # bookcase
            for lv in range(4):
                rp.append(wall_box(1.45, 0.05, 0.85, 0.25, 0.28, F + 0.25 + lv * 0.45, 'Curtain' if lv % 2 else 'Seat_Fabric'))
            x, y = at(2.6, 0.85)
            rp += [cyl(x, y, F, 0.18, 0.05, 'Metal_Dark', 12), cyl(x, y, F, 0.02, 2.1, 'Aluminium', 8)]
            rp.append(box(x + 0.25 * math.cos(phi + 0.85 + PI / 2), y + 0.25 * math.sin(phi + 0.85 + PI / 2), F + 1.45, 0.5, 0.01, 0.5, 'Flag_Green', deg + math.degrees(0.85) + 90))
            rp.append(wall_box(-0.55, 0.0, 0.9, 0.03, 0.65, F + 1.6, 'Frame_Gold'))           # framed map of the area
            rp.append(wall_box(-0.55, 0.02, 0.8, 0.02, 0.55, F + 1.65, 'Sand_Field'))
            rp.append(wall_box(0.0, 0.0, 0.36, 0.04, 0.36, F + 2.45, 'Flag_White'))           # wall clock
            rp.append(wall_box(0.55, 0.0, 0.95, 0.25, 0.3, F + 2.45, 'Sanitary_White'))       # split AC unit
        elif t['name'] == 'SE':    # Drone & Equipment Store
            for da in (-0.85, 0.0, 0.85):
                rp.append(wall_box(da, 0.0, 1.3, 0.55, 0.04, F, 'Aluminium'))
                for post in (-0.62, 0.62):
                    rp.append(wall_box(da + post / (RI - 0.3), 0.0, 0.05, 0.55, 2.2, F, 'Aluminium'))
                for lv in range(4):
                    rp.append(wall_box(da, 0.0, 1.3, 0.55, 0.03, F + 0.12 + lv * 0.55, 'Aluminium'))
                    for b in (-0.4, 0.0, 0.4):
                        rp.append(wall_box(da + b / (RI - 0.3), 0.05, 0.34, 0.42, 0.26, F + 0.15 + lv * 0.55, 'Bin_Blue' if (lv + int(b * 10)) % 2 == 0 else 'Gate_Orange'))
            for k in range(3):                                                # drone transport cases
                rp.append(wall_box(1.65, 0.05, 1.0, 0.6, 0.38, F + k * 0.38, 'Carbon'))
                rp.append(wall_box(1.65, 0.04, 0.12, 0.04, 0.08, F + k * 0.38 + 0.15, 'Gate_Orange'))
            for k, da in enumerate((-0.85, 0.0, 0.85)):                        # training drones on the top shelves
                x, y = at(RI - 0.32, da)
                tr['insts'].append(inst('Training_Quad', 'Shelf_Quad_' + str(k + 1), x, y, F + 1.82, 15 + 30 * k))
            x, y = at(1.6, -0.9)                                              # fixed-wing UAV in an open case
            rp += [box(x, y, F, 1.7, 0.7, 0.3, 'Carbon', deg + 30), box(x, y, F + 0.3, 1.3, 0.12, 0.1, 'Composite_Grey', deg + 30),
                   box(x, y, F + 0.42, 0.25, 1.4, 0.03, 'Composite_Grey', deg + 30)]
            rp.append(wall_box(-1.65, 0.0, 1.3, 0.03, 1.0, F + 1.2, 'Wood'))                  # pegboard with spare props
            for k in range(6):
                rp.append(wall_box(-1.65 + (k - 2.5) * 0.065, 0.03, 0.06, 0.02, 0.85, F + 1.27, 'Carbon'))
            rp.append(wall_box(-1.65, 0.0, 0.8, 0.5, 1.0, F, 'Fire_Red'))                     # tool cabinet (under the pegboard)
            rp.append(free_box(0.95, 0.0, 1.7, 0.6, 1.0, F, 'Wood'))                          # issue counter
            rp.append(free_box(0.95, 0.0, 1.8, 0.7, 0.04, F + 1.0, 'Laminate'))
            x, y = at(0.95, 0.3)
            tr['insts'].append(inst('Training_Quad', 'Store_Quad', x, y, F + 1.04, 20))
        else:                      # SW Battery Charging & Maintenance Room
            for da in (-0.7, 0.0, 0.7):                                       # fire-safe charging cabinets
                rp.append(wall_box(da, 0.0, 1.0, 0.55, 1.9, F, 'Cabinet_Yellow'))
                for lv in range(3):
                    rp.append(wall_box(da, 0.55, 0.8, 0.02, 0.05, F + 0.45 + lv * 0.55, 'Nav_Green'))
            for da in (-0.7, 0.0, 0.7):                                       # LiPo packs charging on cabinet tops
                for b in (-0.25, 0.0, 0.25):
                    rp.append(wall_box(da + b / (RI - 0.3), 0.12, 0.18, 0.28, 0.1, F + 1.9, 'Carbon'))
                    rp.append(wall_box(da + b / (RI - 0.3), 0.1, 0.06, 0.02, 0.02, F + 2.0, 'Nav_Green'))
            rp.append(wall_box(1.45, 0.0, 1.2, 0.45, 1.6, F, 'Aluminium'))                    # battery rack
            for lv in range(3):
                for b in (-0.35, 0.0, 0.35):
                    rp.append(wall_box(1.45 + b / (RI - 0.3), 0.08, 0.28, 0.2, 0.14, F + 0.2 + lv * 0.5, 'Carbon'))
            x, y = at(RI - 0.35, 1.82)
            rp.append(box(x, y, F, 0.95, 0.3, 0.5, 'Metal_Dark', deg + math.degrees(1.82) + 90))
            for dd in (-0.3, 0.0, 0.3):                                       # sand buckets
                xx, yy = at(RI - 0.35, 1.82 + dd / (RI - 0.35))
                rp.append(cyl(xx, yy, F + 0.5, 0.13, 0.28, 'Fire_Red', 14))
            x, y = at(RI - 0.15, -1.85)
            rp += [cyl(x, y, F + 0.15, 0.09, 0.55, 'Fire_Red', 14), cyl(x, y, F + 0.7, 0.03, 0.1, 'Carbon', 8)]   # extinguisher
            rp.append(wall_box(0.0, 0.0, 0.6, 0.06, 0.4, F + 2.35, 'Aluminium'))              # ventilation louver
            for k in range(4):
                rp.append(wall_box(0.0, 0.05, 0.55, 0.02, 0.03, F + 2.42 + k * 0.08, 'Metal_Dark'))
            rp.append(wall_box(-1.45, 0.0, 1.6, 0.7, 0.9, F, 'Wood'))                         # workbench
            rp.append(wall_box(-1.45, 0.0, 1.4, 0.03, 0.8, F + 1.2, 'Laminate'))              # tool board
            for k in range(5):
                rp.append(wall_box(-1.45 + (k - 2) * 0.09, 0.03, 0.04, 0.03, 0.3, F + 1.4, 'Metal_Dark'))
            x, y = at(1.0, 0.0)
            rp += [cyl(x, y, F, 0.3, 0.05, 'Metal_Dark', 16), cyl(x, y, F + 0.05, 0.04, 0.85, 'Aluminium', 8)]   # repair stand
            tr['insts'].append(inst('Training_Quad', 'Repair_Quad', x, y, F + 0.9, 30))

# ---------------------------------------------------------------- site
def build_site(root, height_fn):
    site = add(root, node('Site'))
    x0, y0, x1, y1 = COMPOUND
    # compound pad (gravel), raised plinth into the terrain
    site['parts'].append(prism([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], -2.5, 2.5, 'Sand_Field'))
    land = add(site, node('Landscape'))
    lp = land['parts']
    # front drive, roundabout with flagpole, lawns
    lp.append(prism([[-4, 16], [4, 16], [4, 23.5], [-4, 23.5]], 0, 0.03, 'Asphalt'))
    lp.append(prism([[-4, 39.2], [4, 39.2], [4, y1], [-4, y1]], 0, 0.03, 'Asphalt'))
    lp.append(ring(0, 31.5, 0, 8.2, 5.2, 0.03, 'Asphalt', 64))
    lp.append(cyl(0, 31.5, 0, 5.2, 0.06, 'Lawn', 48))
    for sx in (-1, 1):
        xa, xb = (9.0, 46.0) if sx > 0 else (-46.0, -9.0)
        lp.append(prism([[xa, 24.0], [xb, 24.0], [xb, 48.0], [xa, 48.0]], 0, 0.05, 'Lawn'))
    lp.append(ring(0, 31.5, 0, 8.45, 8.2, 0.12, 'Concrete', 64))
    lp.append(prism([[-28, 17], [-4, 17], [-4, 21], [-28, 21]], 0, 0.03, 'Asphalt'))
    # flagpole (national flag, no lettering)
    fl = add(site, node('Flag'))
    fl['parts'] += [cyl(0, 31.5, 0.06, 0.55, 0.5, 'Concrete', 20), cyl(0, 31.5, 0.56, 0.08, 11.5, 'Aluminium', 12),
                    lathe(0, 31.5, 12.06, [[0, 0.14], [0.12, 0.14], [0.22, 0]], 'Aluminium', 12)]
    fl['parts'] += flag_parts(0.09, 31.5, 9.4, 3.6, 2.4)
    # parking (west) with vehicles
    park = add(site, node('Parking'))
    park['parts'].append(prism([[-50, -6], [-28, -6], [-28, 21], [-50, 21]], 0, 0.03, 'Asphalt'))
    for i in range(6):
        park['parts'].append(box(-39, -4.5 + i * 3.7 + 1.85, 0.03, 9.0, 0.12, 0.01, 'Marking_White'))
    park['insts'] += [inst('Tactical_Vehicle', 'Vehicle_1', -42, 4.1, 0.03, 0), inst('Tactical_Vehicle', 'Vehicle_2', -42, 11.5, 0.03, 0)]
    # drone flying field (east): race gates, landing pads, windsock, GCS truck, comms mast
    fld = add(site, node('Drone_Flying_Field'))
    fld['parts'].append(prism([[27, -36], [52, -36], [52, 20], [27, 20]], 0, 0.04, 'Concrete'))
    fld['parts'].append(prism([[27.5, -35.5], [51.5, -35.5], [51.5, 19.5], [27.5, 19.5]], 0.04, 0.012, 'Sand_Field'))
    for i, (gx, gy, gr) in enumerate([(39.5, -22.0, 0), (34.0, -10.0, 30), (45.0, 0.0, -30), (39.5, 11.0, 0)]):
        fld['insts'].append(inst('Race_Gate', 'Race_Gate_' + str(i + 1), gx, gy, 0.05, gr + 90))
    for i, (px, py) in enumerate([(33.5, -30.0), (45.5, -30.0)]):
        fld['insts'].append(inst('Landing_Pad', 'Landing_Pad_' + str(i + 1), px, py, 0.05, 0))
        fld['insts'].append(inst('Training_Quad', 'Pad_Quad_' + str(i + 1), px, py, 0.12, 15 + i * 40))
    fld['parts'] += [cyl(50.5, 17.5, 0, 0.06, 6.0, 'Metal_Dark', 8), box(51.3, 17.5, 5.4, 1.6, 0.35, 0.4, 'Gate_Orange')]
    fld['insts'].append(inst('GCS_Truck', 'GCS_Truck', 22.5, -30.0, 0.0, 90))
    # comms mast with dishes
    mast = add(site, node('Comms_Mast'))
    mp = mast['parts']
    for i in range(3):
        a = 2 * PI * i / 3 + PI / 6
        mp.append(cyl(48 + math.cos(a) * 0.7, 40 + math.sin(a) * 0.7, 0, 0.07, 18.0, 'Aluminium', 8))
    for z in range(1, 18, 2):
        mp.append(ring(48, 40, float(z), 0.8, 0.7, 0.06, 'Aluminium', 12))
    mp.append(cyl(48, 40, 0, 1.2, 0.4, 'Concrete', 16))
    mp.append(lathe(48.9, 40, 14.0, [[0, 0.1], [0.2, 0.55], [0.32, 0.8], [0.34, 0]], 'Flag_White', 20))
    mp.append(lathe(47.1, 40, 11.5, [[0, 0.1], [0.15, 0.4], [0.24, 0.6], [0.25, 0]], 'Flag_White', 20))
    mp.append(lathe(48, 40, 18.0, [[0, 0.1], [0.3, 0.06], [0.35, 0]], 'Nav_Red', 10))
    # boundary wall with north gate
    bw = add(site, node('Boundary_Wall'))
    bp = bw['parts']
    def bwall(a, b, gaps):
        wall(bp, a, b, gaps, 0.3, 2.0, 0.0, 'Stone')
    bwall([x1, y1], [x0, y1], [opening(x1 - 0.0, 9.0, 0.0, 2.0, 'door')])
    bwall([x0, y1], [x0, y0], [])
    bwall([x0, y0], [x1, y0], [opening(10.0 - x0, 5.0, 0.0, 2.0, 'door')])
    bwall([x1, y0], [x1, y1], [])
    for sx in (-1, 1):
        bp.append(box(sx * 4.8, y1 - 0.15, 0, 0.9, 0.9, 2.8, 'Stone_Dark'))
        bp.append(lathe(sx * 4.8, y1 - 0.15, 2.8, [[0, 0.3], [0.2, 0.3], [0.35, 0]], 'Light_Panel', 12))
    bp.append(box(8.5, y1 + 0.2, 0, 7.0, 0.12, 1.8, 'Metal_Dark'))          # sliding gate, open
    # street lights and shrubs
    for i, (lx, ly, r) in enumerate([(-5.5, 19, 0), (5.5, 19, 180), (-5.5, 45, 0), (5.5, 45, 180), (-25, 3, 0), (24, 3, 180)]):
        site['insts'].append(inst('Street_Light', 'Street_Light_' + str(i + 1), lx, ly, 0.0, r))
    for i in range(22):
        sx = -1 if i % 2 else 1
        site['insts'].append(inst('Shrub', 'Shrub_' + str(i + 1), sx * (8.0 + 3.4 * (i // 2)), 49.5 if i < 22 else 26, 0.05, i * 37))
    # approach road from the metalled road ~410 m west, draped on the real terrain
    road = add(site, node('Approach_Road'))
    road['parts'].append(road_mesh(height_fn, [[-410.0, 61.0], [-120.0, 61.0], [-14.0, 61.0], [-4.0, 59.0], [0.0, 55.0], [0.0, y1]], 8.0))
    return site

def flag_parts(x, y, ztop, w, h):
    """National flag on the pole, in the y-z plane facing east-west; crescent and star as solid shapes."""
    z0 = ztop - h
    out = [prism([[y, z0], [y + w * 0.25, z0], [y + w * 0.25, ztop], [y, ztop]], x, 0.02, 'Flag_White', ax='x'),
           prism([[y + w * 0.25, z0], [y + w, z0], [y + w, ztop], [y + w * 0.25, ztop]], x, 0.02, 'Flag_Green', ax='x')]
    cyc, czc, R = y + w * 0.625, z0 + h * 0.5, h * 0.3
    ox, oz, r2 = cyc + R * 0.25, czc + R * 0.22, R * 0.85
    pts = []
    for i in range(41):                                  # outer arc not covered by the inner circle
        a = 2 * PI * i / 40
        px, pz = cyc + R * math.cos(a), czc + R * math.sin(a)
        if (px - ox) ** 2 + (pz - oz) ** 2 > r2 * r2:
            pts.append([px, pz])
    # walk back along the inner circle between the two intersection points
    a_s = math.atan2(pts[-1][1] - oz, pts[-1][0] - ox)
    a_e = math.atan2(pts[0][1] - oz, pts[0][0] - ox)
    while a_e > a_s:
        a_e -= 2 * PI
    for i in range(1, 30):
        a = a_s + (a_e - a_s) * i / 30
        pts.append([ox + r2 * math.cos(a), oz + r2 * math.sin(a)])
    out.append(prism(pts, x + 0.02, 0.01, 'Flag_White', ax='x'))
    sxc, szc = cyc + R * 0.55, czc + R * 0.5
    star = []
    for i in range(10):
        rr = R * (0.24 if i % 2 == 0 else 0.1)
        a = PI / 2 + i * PI / 5 + 0.5
        star.append([sxc + rr * math.cos(a), szc + rr * math.sin(a)])
    out.append(prism(star, x + 0.02, 0.01, 'Flag_White', ax='x'))
    return out

def road_mesh(height_fn, path, width, step=8.0):
    verts, faces = [], []
    pts = []
    for i in range(len(path) - 1):
        ax, ay = path[i]
        bx, by = path[i + 1]
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L / step))
        for k in range(n):
            pts.append([ax + (bx - ax) * k / n, ay + (by - ay) * k / n])
    pts.append(path[-1])
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L * width / 2, dx / L * width / 2
        for sgn in (1, -1):
            px, py = x + nx * sgn, y + ny * sgn
            verts.append([round(px, 3), round(py, 3), round(height_fn(px, py) + 0.1, 3)])
    for i in range(len(pts) - 1):
        a, b, c, d2 = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
        faces += [[a, b, d2], [a, d2, c]]
    return {'k': 'mesh', 'v': verts, 'f': faces, 'm': 'Asphalt'}

# ---------------------------------------------------------------- terrain shaping
def pad_blend(x, y, raw):
    """Terrain height relative to pad level, flattened under the compound and eased back to the DEM."""
    x0, y0, x1, y1 = COMPOUND
    dx = max(x0 - 4 - x, 0.0, x - x1 - 4)
    dy = max(y0 - 4 - y, 0.0, y - y1 - 4)
    d = math.hypot(dx, dy)
    t = min(d / 45.0, 1.0)
    t = t * t * (3 - 2 * t)
    return -0.3 + (raw + 0.3) * t

def build_spec(height_fn):
    root = node('DRONE_TRG_COMPLEX_44_DIV')
    build_shell(root)
    build_towers(root)
    build_drone_core(root)
    build_interiors(root)
    build_site(root, height_fn)
    return {'materials': MATERIALS, 'defs': defs_all(), 'root': root,
            'meta': {'gr': "25°19'47.62\"N 62°30'33.00\"E", 'front': 'north', 'units': 'm',
                     'towers': [{'name': t['name'], 'c': [t['cx'], t['cy']], 'spin': t['spin']} for t in TOWERS]}}
