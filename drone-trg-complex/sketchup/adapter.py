# SketchUp adapter for the DRONE TRG COMPLEX - 44 DIV design spec.
# Runs inside the SketchUp build_model sandbox (Python, SketchUp SDK preloaded, no imports).
# Reads spec_payload.png (JSON in a stored-deflate PNG made by pack_spec.py) and builds native
# SketchUp groups, component definitions/instances, lofted solids and the textured terrain.

IN = 39.37007874   # metres -> inches (SketchUp API unit)

def payload_text(name):
    d = session_files.read_bytes(name)
    p, idat = 8, []
    w = 0
    while p < len(d):
        ln = (d[p] << 24) | (d[p + 1] << 16) | (d[p + 2] << 8) | d[p + 3]
        typ = d[p + 4:p + 8]
        body = d[p + 8:p + 8 + ln]
        if typ == b'IHDR':
            w = (body[0] << 24) | (body[1] << 16) | (body[2] << 8) | body[3]
        elif typ == b'IDAT':
            idat.append(body)
        p += 12 + ln
    z = b''.join(idat)
    q, out = 2, []
    while True:                                  # stored deflate blocks only
        final = z[q] & 1
        ln = z[q + 1] | (z[q + 2] << 8)
        out.append(z[q + 5:q + 5 + ln])
        q += 5 + ln
        if final:
            break
    raw = b''.join(out)
    rows = [raw[i + 1:i + 1 + w] for i in range(0, len(raw), w + 1)]
    data = b''.join(rows)
    n = int(data[:12].decode('ascii'))
    return data[12:12 + n].decode('ascii')

def parse_json(s):
    pos = [0]
    num_chars = '0123456789+-.eE'
    def ws():
        while s[pos[0]] in ' \n\r\t':
            pos[0] += 1
    def val():
        ws()
        c = s[pos[0]]
        if c == '{':
            pos[0] += 1
            o = {}
            ws()
            if s[pos[0]] == '}':
                pos[0] += 1
                return o
            while True:
                ws()
                k = val()
                ws()
                pos[0] += 1          # ':'
                o[k] = val()
                ws()
                c2 = s[pos[0]]
                pos[0] += 1
                if c2 == '}':
                    return o
        if c == '[':
            pos[0] += 1
            a = []
            ws()
            if s[pos[0]] == ']':
                pos[0] += 1
                return a
            while True:
                a.append(val())
                ws()
                c2 = s[pos[0]]
                pos[0] += 1
                if c2 == ']':
                    return a
        if c == '"':
            e = s.find('"', pos[0] + 1)
            r = s[pos[0] + 1:e]
            pos[0] = e + 1
            return r
        if s.startswith('true', pos[0]):
            pos[0] += 4
            return True
        if s.startswith('false', pos[0]):
            pos[0] += 5
            return False
        if s.startswith('null', pos[0]):
            pos[0] += 4
            return None
        st = pos[0]
        while s[pos[0]] in num_chars:
            pos[0] += 1
        t = s[st:pos[0]]
        if '.' in t or 'e' in t or 'E' in t:
            return float(t)
        return int(t)
    return val()

def sarea(p):
    a = 0.0
    for i in range(len(p)):
        q = p[(i + 1) % len(p)]
        a += p[i][0] * q[1] - q[0] * p[i][1]
    return a / 2

def clean_ring(r):
    out = []
    for p in r:
        if len(out) == 0 or abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1]) > 1e-4:
            out.append(p)
    if len(out) > 2 and abs(out[0][0] - out[-1][0]) + abs(out[0][1] - out[-1][1]) <= 1e-4:
        out = out[:-1]
    return out

def map_pt(ax, u, v, w):
    if ax == 'z':
        return SUPoint3D(u * IN, v * IN, w * IN)
    if ax == 'y':
        return SUPoint3D(u * IN, w * IN, v * IN)
    return SUPoint3D(w * IN, u * IN, v * IN)

def loop_of(ids, flip):
    L = LoopInput()
    seq = ids[::-1] if flip else ids
    for i in seq:
        L.add_vertex_index(i)
    return L

def prism_geom(part):
    pts = clean_ring(part['pts'])
    if sarea(pts) < 0:
        pts = pts[::-1]
    rings = [pts]
    for h in part['holes']:
        h = clean_ring(h)
        if sarea(h) > 0:
            h = h[::-1]
        rings.append(h)
    ax, flip = part['ax'], part['ax'] == 'y'
    z0, z1 = part['z'], part['z'] + part['h']
    verts, idx = [], []
    for r in rings:
        b = len(verts)
        for u, v in r:
            verts.append(map_pt(ax, u, v, z0))
        t = len(verts)
        for u, v in r:
            verts.append(map_pt(ax, u, v, z1))
        idx.append((b, t, len(r)))
    geom = GeometryInput()
    geom.set_vertices(verts)
    b, t, n = idx[0]
    fi, geom = geom.add_face(loop_of([t + i for i in range(n)], flip))
    for hb, ht, hn in idx[1:]:
        geom = geom.face_add_inner_loop(fi, loop_of([ht + i for i in range(hn)], flip))
    fi, geom = geom.add_face(loop_of([b + i for i in range(n)][::-1], flip))
    for hb, ht, hn in idx[1:]:
        geom = geom.face_add_inner_loop(fi, loop_of([hb + i for i in range(hn)][::-1], flip))
    for b, t, n in idx:
        for i in range(n):
            j = (i + 1) % n
            _, geom = geom.add_face(loop_of([b + i, b + j, t + j, t + i], flip))
    return geom

def mesh_geom(part):
    geom = GeometryInput()
    geom.set_vertices([SUPoint3D(v[0] * IN, v[1] * IN, v[2] * IN) for v in part['v']])
    for f in part['f']:
        _, geom = geom.add_face(loop_of(f, False))
    return geom

MATS = {}
def mat(name):
    return MATS[name]

def make_materials(spec):
    for name, c in spec['materials'].items():
        MATS[name] = get_or_create_material(name, c[0], c[1], c[2], c[3])

def add_part(part, ents, name):
    g = Group()
    ents.add_group(g)
    k = part['k']
    if k == 'prism':
        g.get_entities().fill(prism_geom(part), weld_vertices=True)
    elif k == 'mesh':
        g.get_entities().fill(mesh_geom(part), weld_vertices=True)
    else:
        prof = [(a * IN, b * IN) for a, b in part['prof']]
        g.get_entities().fill(build_lofted_solid(prof, n=part['seg']), weld_vertices=True)
        clean_geometry(g, prof, smooth=True)
        c = part['c']
        g.set_transform(translation(c[0] * IN, c[1] * IN, c[2] * IN))
    m = mat(part['m'])
    apply_material(g, m)
    g.set_material(m)
    g.set_name(name)
    return g

DEFS = {}
def build_defs(spec):
    for dname, dn in spec['defs'].items():
        cd, is_new = get_or_create_definition(dname)
        if is_new:
            ents = cd.get_entities()
            for i, p in enumerate(dn['parts']):
                add_part(p, ents, dname + '_' + p['m'] + '_' + str(i + 1))
        DEFS[dname] = cd

LAYERS = {}
def layer(name):
    if name not in LAYERS:
        L = Layer()
        L.set_name(name)
        model.add_layers([L])
        LAYERS[name] = L
    return LAYERS[name]

def place(obj, pos, rot):
    obj.set_transform(rotation_z(rot or 0.0, pos[0] * IN, pos[1] * IN, pos[2] * IN))

def build_node(nd, parent_ents):
    g = Group()
    parent_ents.add_group(g)
    g.set_name(nd['name'])
    ents = g.get_entities()
    count = 0
    for i, p in enumerate(nd['parts']):
        add_part(p, ents, nd['name'] + '_' + p['m'] + '_' + str(i + 1))
        count += 1
    for it in nd['insts']:
        ci = DEFS[it['d']].create_instance()
        ci.set_name(it['name'])
        place(ci, it['pos'], it['rot'])
        ents.add_instance(ci)
        count += 1
    for ch in nd['children']:
        count += build_node(ch, ents)
    place(g, nd['pos'], nd['rot'])
    if nd['layer']:
        g.set_layer(layer(nd['layer']))
    return count
