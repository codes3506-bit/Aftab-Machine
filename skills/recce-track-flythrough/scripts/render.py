"""GPU terrain renderer (moderngl, headless under xvfb-run).
Writes terrain+track video (no HUD) and per-frame camera / label projections for the HUD pass.
usage: render.py OUT.mp4 [--stills t1,t2,..] [--scale 0.5] [--t0 T] [--t1 T]
"""
import sys, json, math, subprocess, argparse, time
import numpy as np, moderngl
from PIL import Image
sys.path.insert(0, '/home/user/recce/work')
from timeline import *
from geo import en, ll, LAT0, LON0

Image.MAX_IMAGE_PIXELS = None
ap = argparse.ArgumentParser()
ap.add_argument('out'); ap.add_argument('--stills', default=''); ap.add_argument('--scale', type=float, default=1.0)
ap.add_argument('--t0', type=float, default=0); ap.add_argument('--t1', type=float, default=DUR)
args = ap.parse_args()
WID, HEI = int(1920 * args.scale), int(1080 * args.scale)
VE = 1.5
META = json.load(open(f'{R}/work/meta.json'))
HM = META['hm']

ctx = moderngl.create_standalone_context(require=430)
print(ctx.info['GL_RENDERER'], ctx.info['GL_VERSION'])

# ---------------- textures ----------------
def tex_from_png(path):
    im = Image.open(path).convert('RGB')
    t = ctx.texture(im.size, 3, im.tobytes())
    t.build_mipmaps(); t.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR); t.anisotropy = 16.0
    t.repeat_x = t.repeat_y = False
    return t
TEX = {z: tex_from_png(f'{R}/work/tex{z}.png') for z in (16, 17, 18)}
hm = np.load(f'{R}/work/hm.npy').astype(np.float32)
HMT = ctx.texture((HM['nx'], HM['ny']), 1, hm.tobytes(), dtype='f4')
HMT.filter = (moderngl.LINEAR, moderngl.LINEAR); HMT.repeat_x = HMT.repeat_y = False

from scipy.ndimage import distance_transform_edt, zoom as _zoom
_tr = SC['track']; _m = np.ones((HM['ny'] // 5 + 1, HM['nx'] // 5 + 1), bool)
for _e, _n in zip(_tr['e'], _tr['n']):
    _m[int((_n - HM['y0']) / HM['step'] / 5), int((_e - HM['x0']) / HM['step'] / 5)] = False
_d = distance_transform_edt(_m) * HM['step'] * 5
_mk = np.clip((1300 - _d) / 700, 0, 1).astype('f4')
MSK = ctx.texture((_mk.shape[1], _mk.shape[0]), 1, _mk.tobytes(), dtype='f4'); MSK.filter = (moderngl.LINEAR, moderngl.LINEAR)

def hgt(x, y):
    """bilinear terrain height (real metres) at local x,y"""
    fx = (np.asarray(x) - HM['x0']) / HM['step']; fy = (np.asarray(y) - HM['y0']) / HM['step']
    fx = np.clip(fx, 0, HM['nx'] - 1.001); fy = np.clip(fy, 0, HM['ny'] - 1.001)
    i = fx.astype(int); j = fy.astype(int); u = fx - i; v = fy - j
    return (hm[j, i] * (1 - u) * (1 - v) + hm[j, i + 1] * u * (1 - v) + hm[j + 1, i] * (1 - u) * v + hm[j + 1, i + 1] * u * v)

# ---------------- terrain mesh (rectilinear, dense near track) ----------------
def axis(a0, a1, w0, w1, fine, coarse):
    xs = list(np.arange(a0, w0, coarse)) + list(np.arange(w0, w1, fine)) + list(np.arange(w1, a1, coarse)) + [a1]
    return np.array(sorted(set(np.round(xs, 3))), dtype=np.float32)
X1 = HM['x0'] + (HM['nx'] - 1) * HM['step']; Y1 = HM['y0'] + (HM['ny'] - 1) * HM['step']
xs = axis(HM['x0'], X1, -3600, 3600, 9.0, 36.0); ys = axis(HM['y0'], Y1, -2400, 2600, 9.0, 36.0)
GX, GY = np.meshgrid(xs, ys)
verts = np.stack([GX.ravel(), GY.ravel()], 1).astype('f4')
nx_, ny_ = len(xs), len(ys)
idx = np.arange(nx_ * ny_, dtype=np.uint32).reshape(ny_, nx_)
q = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, :-1], idx[1:, 1:]], -1).reshape(-1, 4)
ind = np.concatenate([q[:, [0, 1, 2]], q[:, [1, 3, 2]]]).astype(np.uint32)
print('terrain verts', len(verts), 'tris', len(ind))

def zinfo(z):
    m = META[f'z{z}']
    mer = lambda la: math.log(math.tan(math.pi / 4 + math.radians(la) / 2))
    return (m['lonW'], m['lonE'], mer(m['latN']), mer(m['latS']))

TER_VS = '''#version 430
in vec2 in_xy; uniform mat4 mvp; uniform sampler2D hm; uniform vec4 hmg; uniform float VE;
out vec3 wp;
void main(){ vec2 uv=(in_xy-hmg.xy)/hmg.zw; float h=textureLod(hm,uv,0).r; wp=vec3(in_xy,h*VE); gl_Position=mvp*vec4(wp,1.0);}'''
TER_FS = '''#version 430
in vec3 wp; out vec4 fc;
uniform sampler2D t16,t17,t18,hm; uniform vec4 z16,z17,z18; uniform vec4 hmg; uniform float VE;
uniform vec3 cam; uniform vec2 ll0; uniform vec2 mll; uniform float smode; uniform float dim; uniform vec3 sun; uniform sampler2D msk;
float mer(float la){return log(tan(0.78539816+la*0.5));}
vec2 tuv(vec4 z,float lon,float m){return vec2((lon-z.x)/(z.y-z.x),(z.z-m)/(z.z-z.w));}
float inside(vec2 uv,float e){vec2 a=smoothstep(vec2(0.0),vec2(e),uv)*smoothstep(vec2(0.0),vec2(e),1.0-uv);return a.x*a.y;}
void main(){
 float lon=ll0.x+wp.x/mll.x; float lat=radians(ll0.y+wp.y/mll.y); float m=mer(lat);
 vec2 u16=tuv(z16,lon,m),u17=tuv(z17,lon,m),u18=tuv(z18,lon,m);
 vec3 c=texture(t16,u16).rgb;
 c=mix(c,texture(t17,u17).rgb,inside(u17,0.02));
 c=mix(c,texture(t18,u18).rgb,inside(u18,0.03));
 vec2 huv=(wp.xy-hmg.xy)/hmg.zw; vec2 px=1.0/vec2(textureSize(hm,0));
 float hl=texture(hm,huv-vec2(px.x,0)).r, hr=texture(hm,huv+vec2(px.x,0)).r, hd=texture(hm,huv-vec2(0,px.y)).r, hu=texture(hm,huv+vec2(0,px.y)).r;
 float st=hmg.z*px.x; vec2 gr=vec2(hr-hl,hu-hd)/(2.0*st);
 vec3 n=normalize(vec3(-gr*VE,1.0));
 float lam=max(dot(n,sun),0.0); float sh=(0.62+0.58*lam)/(0.62+0.58*sun.z);
 c=c*vec3(1.0,0.99,1.13); c=pow(c,vec3(1.06))*mix(1.0,sh,0.85);
 // slope tint (KMZ legend): yellow 5-10, orange 10-14, red 14-25, purple >25 %
 float sp=length(gr)*100.0; vec3 tc=vec3(0); float ta=0.0;
 if(sp>25.0){tc=vec3(0.62,0.18,0.85);ta=1.0;} else if(sp>14.0){tc=vec3(0.95,0.15,0.12);ta=1.0;} else if(sp>10.0){tc=vec3(1.0,0.55,0.1);ta=0.9;} else if(sp>5.0){tc=vec3(1.0,0.9,0.2);ta=0.7;}
 float mk=texture(msk,huv).r; c=mix(c,tc*mix(0.7,1.15,lam),ta*smode*0.36*mk);
 // grade: saturation/contrast
 float l=dot(c,vec3(0.299,0.587,0.114)); c=mix(vec3(l),c,1.04); c=(c-0.5)*1.08+0.5;
 float d=length(wp-cam); float f=1.0-exp(-pow(d/30000.0,1.3));
 vec3 haze=vec3(0.84,0.84,0.83); c=mix(c,haze,f*0.8);
 fc=vec4(c*dim,1.0);}'''
ter = ctx.program(vertex_shader=TER_VS, fragment_shader=TER_FS)
vbo = ctx.buffer(verts.tobytes()); ibo = ctx.buffer(ind.tobytes())
vao_t = ctx.vertex_array(ter, [(vbo, '2f', 'in_xy')], ibo)
for i, z in enumerate((16, 17, 18)):
    ter[f't{z}'] = i; ter[f'z{z}'] = zinfo(z)
ter['hm'] = 3
ter['msk'] = 4
ter['hmg'] = (HM['x0'], HM['y0'], (HM['nx'] - 1) * HM['step'] + HM['step'], (HM['ny'] - 1) * HM['step'] + HM['step'])
ter['VE'] = VE
from geo import MLON, MLAT
ter['ll0'] = (LON0, LAT0); ter['mll'] = (MLON, MLAT)
az, el = math.radians(135), math.radians(48)
ter['sun'] = (math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el))

# ---------------- sky ----------------
SKY_VS = '''#version 430
in vec2 p; out vec2 v; void main(){v=p; gl_Position=vec4(p,0.9999,1);}'''
SKY_FS = '''#version 430
in vec2 v; out vec4 fc; uniform mat4 ivp; uniform float dim;
void main(){ vec4 a=ivp*vec4(v,1,1); vec3 d=normalize(a.xyz/a.w); float e=d.z;
 vec3 hz=vec3(0.84,0.84,0.83), top=vec3(0.33,0.52,0.80);
 vec3 c=mix(hz,top,smoothstep(-0.02,0.45,e)); fc=vec4(c*dim,1);}'''
sky = ctx.program(vertex_shader=SKY_VS, fragment_shader=SKY_FS)
vao_s = ctx.vertex_array(sky, [(ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], 'f4').tobytes()), '2f', 'p')])

# ---------------- ribbons (track + hy const areas) ----------------
TR = SC['track']
TE, TN, TZ = np.array(TR['e']), np.array(TR['n']), hgt(np.array(TR['e']), np.array(TR['n']))
TCH = np.array(TR['ch']); TTY = np.array(TR['typ'], float); TG = np.array(TR['g'])

def ribbon(E, N, Z, CHv, TY, G):
    tx = np.gradient(E); ty = np.gradient(N); l = np.hypot(tx, ty) + 1e-9; sx, sy = -ty / l, tx / l
    rows = []
    for k in range(len(E)):
        for s in (-1.0, 1.0):
            rows.append([E[k], N[k], Z[k], sx[k], sy[k], s, CHv[k], TY[k], G[k]])
    return np.array(rows, 'f4')
trk = ribbon(TE, TN, TZ, TCH, TTY, TG)
hyrows = []
for poly in SC['hy']:
    P = np.array(poly + [poly[0]]); E, N = P[:, 0], P[:, 1]
    d = np.r_[0, np.cumsum(np.hypot(np.diff(E), np.diff(N)))]
    s = np.arange(0, d[-1], 4.0); E2 = np.interp(s, d, E); N2 = np.interp(s, d, N)
    hyrows.append(ribbon(E2, N2, hgt(E2, N2), -np.ones_like(s), 3 * np.ones_like(s), s))
hyr = np.concatenate(hyrows)
RB_VS = '''#version 430
in vec3 p; in vec2 sd; in float s; in float ch; in float ty; in float g;
uniform mat4 mvp; uniform vec3 cam; uniform float VE, wbase, kpx, wmul, lm;
out float vch; out float vty; out float vg; out float vs;
void main(){ vec3 P=vec3(p.xy,p.z*VE); float d=length(P-cam); float w=max(wbase,d*kpx)*wmul;
 float lift=(2.5+d*0.0045)*lm; vec3 Q=P+vec3(sd*s*w,lift);
 vch=ch; vty=ty; vg=g; vs=s; gl_Position=mvp*vec4(Q,1);}'''
RB_FS = '''#version 430
in float vch; in float vty; in float vg; in float vs; out vec4 fc;
uniform float prog, gmode, pmode, alpha, pass_, hyA, t;
vec3 gcol(float g){ g=abs(g)*100.0; if(g>25.0)return vec3(0.75,0.25,1.0); if(g>14.0)return vec3(1.0,0.16,0.14); if(g>10.0)return vec3(1.0,0.58,0.1); if(g>5.0)return vec3(1.0,0.92,0.25); return vec3(0.25,0.95,0.45);}
void main(){
 if(vty>2.5){ // hy const area dashed outline
   if(fract(vg/40.0)>0.6 || hyA<0.01) discard;
   if(pass_<0.5){fc=vec4(0.05,0.0,0.0,0.5*hyA);return;}
   if(pass_>1.5){fc=vec4(1.0,0.2,0.15,0.08*hyA);return;}
   fc=vec4(1.0,0.22,0.16,0.85*hyA); return;}
 float vis=pmode>0.5?1.0:step(vch,prog);
 if(vis<0.5||alpha<0.01) discard;
 vec3 c = vty<0.5? vec3(0.12,0.45,1.0) : (vty<1.5? vec3(1.0,0.12,0.12): vec3(0.05,0.85,0.35));
 c=mix(c,gcol(vg),gmode);
 if(pmode>0.5){ c=vec3(1.0,0.92,0.15); if(fract(vch*14.0)>0.62) discard; }
 float head=(pmode>0.5)?0.0:smoothstep(0.06,0.0,prog-vch);
 if(pass_<0.5){fc=vec4(0.02,0.02,0.04,0.9*alpha);return;}
 if(pass_>1.5){fc=vec4(mix(c,vec3(1),0.3),(0.16+0.5*head)*alpha);return;}
 float edge=smoothstep(0.75,1.0,abs(vs));
 c=mix(c,vec3(1.0),0.55*head); c=mix(c,c*0.75,edge*0.0);
 fc=vec4(c,alpha);}'''
rb = ctx.program(vertex_shader=RB_VS, fragment_shader=RB_FS)
def rvao(arr):
    return ctx.vertex_array(rb, [(ctx.buffer(arr.tobytes()), '3f 2f 1f 1f 1f 1f', 'p', 'sd', 's', 'ch', 'ty', 'g')], mode=moderngl.TRIANGLE_STRIP)
vao_trk = rvao(trk); vao_hy = [rvao(h) for h in hyrows]
rb['VE'] = VE

# ---------------- framebuffers ----------------
fbo_ms = ctx.framebuffer(color_attachments=[ctx.renderbuffer((WID, HEI), 4, samples=4)], depth_attachment=ctx.depth_renderbuffer((WID, HEI), samples=4))
fbo = ctx.framebuffer(color_attachments=[ctx.texture((WID, HEI), 4)])
DW, DH = 480, 270
fbo_d = ctx.framebuffer(depth_attachment=ctx.depth_texture((DW, DH)))

# ---------------- camera math ----------------
def look(eye, tgt, fov=42.0):
    f = tgt - eye; f /= np.linalg.norm(f); up = np.array([0, 0, 1.0])
    s = np.cross(f, up); s /= np.linalg.norm(s); u = np.cross(s, f)
    V = np.eye(4); V[0, :3] = s; V[1, :3] = u; V[2, :3] = -f; V[:3, 3] = -V[:3, :3] @ eye
    a = WID / HEI; n, fa = 8.0, 80000.0; t_ = 1 / math.tan(math.radians(fov) / 2)
    P = np.zeros((4, 4)); P[0, 0] = t_ / a; P[1, 1] = t_; P[2, 2] = -(fa + n) / (fa - n); P[2, 3] = -2 * fa * n / (fa - n); P[3, 2] = -1
    return P @ V

from scipy.ndimage import gaussian_filter1d
SE = gaussian_filter1d(TE, 60); SN = gaussian_filter1d(TN, 60)   # 300 m smoothed rail for camera

def track_pt(c, smooth_=False):
    E_, N_ = (SE, SN) if smooth_ else (TE, TN)
    return np.array([np.interp(c, TCH, E_), np.interp(c, TCH, N_)])

def clear_h(p, r=250):
    pts = [p + r * np.array([math.cos(a), math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 9)] + [p]
    return max(hgt(q[0], q[1]) for q in pts)

def cam_title(t):
    u = smooth(t / 9.0)
    eye = np.array([-1500 + 700 * u, -10500 + 1800 * u, 4300 - 700 * u]); tgt = np.array([-1800, 300, 120])
    return eye, tgt, 40
def cam_area(t):
    u = smooth((t - 9) / 16.0); a = math.radians(-98 + 14 * u); C = np.array([-3500 + 500 * u, -700, 150])
    R_ = 10200 - 1600 * u
    eye = C + np.array([R_ * math.cos(a), R_ * math.sin(a), 5200 - 900 * u]); return eye, C, 50 - 4 * u
def cam_chase(t, c=None):
    c = ch(frozen(t)) if c is None else c
    head = track_pt(c); ahead = track_pt(min(9.0, c + 0.32), True); back = track_pt(max(0.0, c - 0.25), True)
    d = ahead - back; d /= (np.linalg.norm(d) + 1e-9)
    side = np.array([-d[1], d[0]])
    eyexy = head - d * 520 + side * 140
    tgxy = head + d * 260
    hz = hgt(*head) * VE
    ez = max(hz + 360, clear_h(eyexy) * VE + 170)
    eye = np.array([eyexy[0], eyexy[1], ez]); tgt = np.array([tgxy[0], tgxy[1], hgt(*tgxy) * VE + 20])
    return eye, tgt, 50
def cam_grade(t):
    u = smooth((t - 115) / 13.0); a = math.radians(-150 + 45 * u)
    cp = 0.55 * track_pt(CREST) + 0.45 * np.array([0.0, 0.0]); C = np.array([cp[0], cp[1], 190 * VE])
    R_ = 4300 - 700 * u
    return C + np.array([R_ * math.cos(a), R_ * math.sin(a), 2500 - 200 * u]), C, 44
def cam_finale(t):
    u = (t - 128) / 24.0; a = math.radians(-90 + 26 * u); C = np.array([-400, 150, 170 * VE])
    R_ = 5000 + 400 * u
    return C + np.array([R_ * math.cos(a), R_ * math.sin(a), 3400 + 300 * u]), C, 44

FUN = {'title': cam_title, 'area': cam_area, 'descend': None, 'brief': cam_chase, 'fly': cam_chase, 'grade': cam_grade, 'finale': cam_finale}
def shot(t):
    for a, b, k in SHOTS:
        if a <= t < b: return k
    return 'finale'
def named(k, t):
    if k == 'descend':   # from end of area to chase start (ease, slight arc)
        u = smooth((t - 25) / 7.0)
        e0, g0, f0 = cam_area(25.0); e1, g1, f1 = cam_chase(t, 0.0)
        e = e0 * (1 - u) + e1 * u; e[2] += math.sin(u * math.pi) * 400
        return e, g0 * (1 - u) + g1 * u, f0 * (1 - u) + f1 * u
    return FUN[k](t)
def raw_cam(t):
    return named(shot(t), t)
def camera(t):
    t = frozen(t)
    for b, w in ((9.0, 1.6), (115.0, 2.5), (128.0, 2.0)):
        if abs(t - b) < w:
            u = smooth((t - b + w) / (2 * w))
            e0, g0, f0 = named(shot(b - 0.01), t); e1, g1, f1 = named(shot(b + 0.01), t)
            return e0 * (1 - u) + e1 * u, g0 * (1 - u) + g1 * u, f0 * (1 - u) + f1 * u
    return raw_cam(t)

# subtle handheld drift (deterministic)
def drift(t):
    return np.array([math.sin(t * 0.37) * 6 + math.sin(t * 0.91) * 2.5, math.cos(t * 0.29) * 6, math.sin(t * 0.53) * 3])

def state(t):
    tf = frozen(t); k = shot(tf)
    prog = ch(tf) if tf >= 45 else (9.0 if tf >= 115 else -1)
    gm = smooth((tf - 116) / 2.5) if tf >= 115 else 0.0
    if tf >= 128: gm = 1.0 - 0.0
    pm = 1.0 if 9.5 <= tf < 45 else 0.0
    alpha = smooth((tf - 10.5) / 2) if tf < 45 else 1.0
    hyA = smooth((tf - 14) / 2) * (1 - smooth((tf - 112) / 3)) if tf < 128 else 0.0
    sm = smooth((tf - 117) / 3) * (1 - smooth((tf - 130) / 3))
    return dict(prog=prog, gmode=gm, pmode=pm, alpha=alpha, hyA=hyA, smode=sm)

LBL = SC['labels']
def project(M, p):
    v = M @ np.array([p[0], p[1], p[2], 1.0]);
    if v[3] <= 0: return None
    return np.array([(v[0] / v[3] * 0.5 + 0.5) * WID, (1 - (v[1] / v[3] * 0.5 + 0.5)) * HEI, v[2] / v[3]])

def render(t):
    tf = frozen(t)
    eye, tgt, fov = camera(tf); eye = eye + drift(tf); M = look(eye, tgt, fov)
    st = state(t)
    mvp = M.T.astype('f4').tobytes()
    # depth pass (terrain only, small) for label occlusion
    fbo_d.use(); ctx.viewport = (0, 0, DW, DH); ctx.enable(moderngl.DEPTH_TEST); fbo_d.clear(depth=1.0)
    ter['mvp'].write(mvp); ter['cam'] = tuple(eye); ter['smode'] = st['smode']; ter['dim'] = 1.0
    for i, z in enumerate((16, 17, 18)): TEX[z].use(i)
    HMT.use(3); MSK.use(4); vao_t.render()
    dep = np.frombuffer(fbo_d.depth_attachment.read(), dtype='f4').reshape(DH, DW)
    # main pass
    fbo_ms.use(); ctx.viewport = (0, 0, WID, HEI); fbo_ms.clear(0, 0, 0, 1, depth=1.0)
    ctx.disable(moderngl.DEPTH_TEST); sky['ivp'].write(np.linalg.inv(M).T.astype('f4').tobytes()); sky['dim'] = 1.0
    vao_s.render(moderngl.TRIANGLE_STRIP)
    ctx.enable(moderngl.DEPTH_TEST); vao_t.render()
    rb['mvp'].write(mvp); rb['cam'] = tuple(eye); rb['kpx'] = 3.4 / HEI * math.tan(math.radians(fov) / 2) * 2
    rb['wbase'] = 3.0; rb['prog'] = st['prog']; rb['gmode'] = st['gmode']; rb['pmode'] = st['pmode']; rb['alpha'] = st['alpha']; rb['hyA'] = st['hyA']
    ctx.enable(moderngl.BLEND); ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
    gw = 1.0 + 0.9 * st['gmode']
    for pas, wm, lm in ((0, 1.6, 1.0), (1, 1.0, 1.35)):
        wm *= gw; rb['pass_'] = pas; rb['wmul'] = wm; rb['lm'] = lm
        ctx.depth_mask = pas == 1
        rb['wmul'] = wm * 0.45
        for v in vao_hy: v.render()
        rb['wmul'] = wm
        vao_trk.render()
    ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE; ctx.depth_mask = False
    rb['pass_'] = 2; rb['wmul'] = 3.4 * gw; rb['lm'] = 1.35; vao_trk.render()
    for v in vao_hy: v.render()
    ctx.depth_mask = True; ctx.disable(moderngl.BLEND)
    ctx.copy_framebuffer(fbo, fbo_ms)
    img = np.frombuffer(fbo.read(components=3), dtype=np.uint8).reshape(HEI, WID, 3)[::-1]
    # labels
    L = {}
    for lb in LBL:
        x, y = lb['p']; z = hgt(x, y) * VE
        pr = project(M, (x, y, z))
        if pr is None or not (-50 < pr[0] < WID + 50 and -50 < pr[1] < HEI + 50): continue
        dx, dy = int(pr[0] / WID * DW), int((1 - pr[1] / HEI) * DH)
        vis = True
        if 0 <= dx < DW and 0 <= dy < DH:
            zz = pr[2] * 0.5 + 0.5; vis = bool(zz <= dep[dy, dx] + 2e-4)
        L[lb["id"]] = [float(round(pr[0], 1)), float(round(pr[1], 1)), bool(vis)]
    hp = None
    if st['prog'] >= 0:
        h = track_pt(min(st['prog'], 9.0)); pr = project(M, (h[0], h[1], hgt(*h) * VE)); hp = None if pr is None else [float(pr[0]), float(pr[1])]
    return img, dict(t=t, eye=eye.tolist(), M=M.tolist(), L=L, head=hp, ch=float(st["prog"]), st={k: float(v) for k, v in st.items()})

if args.stills:
    for s in args.stills.split(','):
        t = float(s); t0 = time.time(); img, info = render(t)
        Image.fromarray(img).save(f'{args.out}_{t:06.2f}.jpg', quality=92)
        json.dump(info, open(f'{args.out}_{t:06.2f}.json', 'w'))
        print('still', t, round(time.time() - t0, 2), 's')
    sys.exit()

ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{WID}x{HEI}', '-r', str(FPS), '-i', '-',
                       '-c:v', 'libx264', '-preset', 'medium', '-crf', '10', '-pix_fmt', 'yuv444p', args.out], stdin=subprocess.PIPE)
cams = []; last_tf = None; last = None; T0 = time.time()
nf0, nf1 = int(round(args.t0 * FPS)), int(round(args.t1 * FPS))
for f in range(nf0, nf1):
    t = f / FPS; tf = frozen(t)
    if last_tf is not None and tf == last_tf:
        img, info = last; info = dict(info, t=t)
    else:
        img, info = render(t); last_tf = tf
    last = (img, info)
    ff.stdin.write(img.tobytes()); cams.append(info)
    if f % 30 == 0:
        el = time.time() - T0; done = f - nf0 + 1
        print(f'frame {f}/{nf1} t={t:.1f} {el / done:.2f}s/f eta {(nf1 - f) * el / done / 60:.1f} min', flush=True)
ff.stdin.close(); ff.wait()
json.dump(cams, open(args.out.replace('.mp4', '_cams.json'), 'w'))
print('done', time.time() - T0)
