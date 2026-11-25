"""Compact GPU terrain engine (moderngl, headless under xvfb-run).
Real Cop GLO-30 terrain (VE 1.0) textured with Esri z18/z17/z16 imagery, aerial haze, optional slope / drainage tint.
Overlays (tracks, pins, labels) are drawn in image space and depth-tested against the GL depth buffer, so lines
sit on the ground and hide correctly behind ridges.
"""
import json, math, numpy as np, moderngl, cv2
from PIL import Image
from scipy.ndimage import gaussian_filter
from geo import *

import os
VE = float(os.environ.get('VE', '1.5'))
SKY_TOP = np.array([0.42, 0.62, 0.86]); SKY_HOR = np.array([0.86, 0.84, 0.80])


def axis(a0, a1, w0, w1, fine, coarse):
    xs = list(np.arange(a0, w0, coarse)) + list(np.arange(w0, w1, fine)) + list(np.arange(w1, a1, coarse)) + [a1]
    return np.array(sorted(set(np.round(xs, 2))), dtype=np.float64)


class Scene:
    def __init__(s, W, H, ss=1):
        s.W, s.H = W, H; s.focus = (0.0, 0.0)
        s.ctx = moderngl.create_standalone_context(require=330)
        # ---- textures (crop z18/z17 to useful extents to stay inside GL limits)
        s.tex = {}; s.ext = {}
        for z, box in ((18, (63.410, 63.460, 25.392, 25.438)), (17, (63.395, 63.475, 25.380, 25.450)), (16, (63.36, 63.51, 25.35, 25.48))):
            import os, pickle
            cp = f'{R}/work/texcache_{z}.pkl'
            if os.path.exists(cp): im, mx0, my0, x0, y0, x1, y1 = pickle.load(open(cp, 'rb'))
            else:
                m = Mos(z); x0, y0 = m.px(box[0], box[3]); x1, y1 = m.px(box[1], box[2]); mx0, my0 = m.x0, m.y0
                im = m.im.crop((int(x0), int(y0), int(x1), int(y1))); pickle.dump((im, mx0, my0, x0, y0, x1, y1), open(cp, 'wb'))
            # grade: Esri olive cast -> neutral warm desert (matches drone footage)
            a = np.asarray(im).astype(np.float32) / 255
            a = a * np.array([1.02, 0.985, 1.12]); lum = a.mean(2, keepdims=True); a = lum + (a - lum) * 0.95
            a = np.clip((a - 0.02) * 1.10, 0, 1) ** 1.06
            im = Image.fromarray((a * 255).astype(np.uint8))
            if max(im.size) > 16000: im = im.resize((im.size[0] // 2, im.size[1] // 2), Image.LANCZOS)
            t = s.ctx.texture(im.size, 3, im.tobytes()); t.build_mipmaps()
            t.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR); t.anisotropy = 16.0
            s.tex[z] = t
            tx0, ty0 = tile_xy(box[0], box[3], z); tx1, ty1 = tile_xy(box[1], box[2], z)
            s.ext[z] = (int(x0) / 256 + mx0, int(y0) / 256 + my0, (int(x1) - int(x0)) / 256, (int(y1) - int(y0)) / 256)
        # ---- mesh (fine 6 m in the core, 30 m outside)
        Wd, Ed, Sd, Nd = 63.365, 63.505, 25.355, 25.475
        ex0, ny0 = en(Wd, Sd); ex1, ny1 = en(Ed, Nd)
        cx0, cy0 = en(63.418, 25.398); cx1, cy1 = en(63.462, 25.440)
        xs = axis(float(ex0), float(ex1), float(cx0), float(cx1), 6.0, 30.0)
        ys = axis(float(ny0), float(ny1), float(cy0), float(cy1), 6.0, 30.0)
        GX, GY = np.meshgrid(xs, ys); LO, LA = ll(GX, GY)
        Z = dem(LO, LA).astype(np.float64) * VE
        s.grid = (xs, ys, Z)
        gy, gx = np.gradient(Z, ys, xs)
        nrm = np.dstack([-gx, -gy, np.ones_like(Z)]); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
        slope = np.degrees(np.arctan(np.hypot(gx, gy) / VE))
        t16 = np.dstack(tile_xy_np(LO, LA, 16))
        s.acc = None
        v = np.dstack([GX, GY, Z, nrm, t16, slope[..., None], np.zeros_like(Z)[..., None]]).reshape(-1, 10).astype('f4')
        ny, nx = Z.shape
        i = np.arange(ny - 1)[:, None] * nx + np.arange(nx - 1)[None]
        idx = np.stack([i, i + 1, i + nx, i + 1, i + nx + 1, i + nx], -1).reshape(-1).astype('i4')
        s.vbo = s.ctx.buffer(v.tobytes()); s.ibo = s.ctx.buffer(idx.tobytes())
        s.prog = s.ctx.program(vertex_shader=VS, fragment_shader=FS)
        s.vao = s.ctx.vertex_array(s.prog, [(s.vbo, '3f 3f 2f 1f 1f', 'p', 'nrm', 't16', 'slope', 'acc')], s.ibo)
        for k, z in enumerate((18, 17, 16)):
            s.tex[z].use(k); s.prog[f'tex{z}'].value = k
            s.prog[f'ext{z}'].value = tuple(float(a) for a in s.ext[z])
        sam = 2
        s.fbo = s.ctx.framebuffer([s.ctx.renderbuffer((W, H), 4, samples=sam)], s.ctx.depth_renderbuffer((W, H), samples=sam))
        s.fbo2 = s.ctx.framebuffer([s.ctx.renderbuffer((W, H), 4)], s.ctx.depth_texture((W, H)))
        s.fbo_d = s.ctx.framebuffer(depth_attachment=s.ctx.depth_texture((W, H)))

    def set_acc(s, acc_fn):
        """per-vertex drainage value (log10 catchment ha) for the drainage tint"""
        xs, ys, Z = s.grid; GX, GY = np.meshgrid(xs, ys)
        a = acc_fn(GX, GY).astype('f4')
        v = np.frombuffer(s.vbo.read(), 'f4').reshape(-1, 10).copy(); v[:, 9] = a.ravel(); s.vbo.write(v.tobytes())

    def height(s, e, n):
        xs, ys, Z = s.grid
        from scipy.ndimage import map_coordinates
        fi = np.interp(n, ys, np.arange(len(ys))); fj = np.interp(e, xs, np.arange(len(xs)))
        return map_coordinates(Z, [fi, fj], order=1)

    def height_m(s, e, n): return s.height(e, n) / VE

    def matrices(s, eye, tgt, fov):
        eye = np.asarray(eye, float); tgt = np.asarray(tgt, float); up = np.array([0, 0, 1.0])
        f = tgt - eye; f /= np.linalg.norm(f); r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
        V = np.eye(4); V[0, :3] = r; V[1, :3] = u; V[2, :3] = -f; V[:3, 3] = -V[:3, :3] @ eye
        near, far = 5.0, 40000.0; a = s.W / s.H; t = 1 / math.tan(math.radians(fov) / 2)
        P = np.zeros((4, 4)); P[0, 0] = t / a; P[1, 1] = t; P[2, 2] = (far + near) / (near - far); P[2, 3] = 2 * far * near / (near - far); P[3, 2] = -1
        return P @ V, near, far

    def render(s, eye, tgt, fov=40, slope_mix=0.0, drain_mix=0.0, sun_az=120, sun_el=22, haze=1.0, dim=0.0):
        MVP, near, far = s.matrices(eye, tgt, fov); s.MVP = MVP; s.eye = np.asarray(eye, float)
        s.prog['mvp'].write(MVP.T.astype('f4').tobytes()); s.prog['eye'].value = tuple(map(float, eye))
        sa, se = math.radians(sun_az), math.radians(sun_el)
        s.prog['sun'].value = (math.sin(sa) * math.cos(se), math.cos(sa) * math.cos(se), math.sin(se))
        s.prog['slope_mix'].value = slope_mix; s.prog['drain_mix'].value = drain_mix; s.prog['haze'].value = haze; s.prog['dim'].value = dim
        try: s.prog['focus'].value = s.focus
        except Exception: pass
        s.fbo.use(); s.ctx.enable(moderngl.DEPTH_TEST); s.ctx.clear(0, 0, 0, 0)
        s.vao.render()
        s.ctx.copy_framebuffer(s.fbo2, s.fbo)
        img = np.frombuffer(s.fbo2.read(components=4), np.uint8).reshape(s.H, s.W, 4)[::-1].astype(np.float32) / 255
        dep = np.frombuffer(s.fbo2.depth_attachment.read(), 'f4').reshape(s.H, s.W)[::-1]
        # sky behind terrain
        yy = np.linspace(0, 1, s.H)[:, None, None]; sky = SKY_TOP * (1 - yy) ** 1.4 + SKY_HOR * (1 - (1 - yy) ** 1.4)
        a = img[..., 3:4]; rgb = img[..., :3] * a + sky * (1 - a)
        s.depth = dep; s.near, s.far = near, far
        return rgb

    def project(s, P):
        """P (n,3) world -> screen x,y, ndc depth (0..1), in-front mask"""
        P = np.asarray(P, float); h = np.c_[P, np.ones(len(P))] @ s.MVP.T
        w = h[:, 3]; x = (h[:, 0] / w * 0.5 + 0.5) * s.W; y = (1 - (h[:, 1] / w * 0.5 + 0.5)) * s.H; d = h[:, 2] / w * 0.5 + 0.5
        return x, y, d, w > 1

    def visible(s, P, bias=0.0006):
        x, y, d, fr = s.project(P)
        xi = np.clip(x.astype(int), 0, s.W - 1); yi = np.clip(y.astype(int), 0, s.H - 1)
        ins = fr & (x >= 0) & (x < s.W) & (y >= 0) & (y < s.H)
        # sample min depth in a 3x3 to be tolerant of the line sitting on the surface
        dz = s.depth[yi, xi]
        return x, y, ins & (d <= dz + bias)


def tile_xy_np(lon, lat, z):
    n = 2 ** z; return (lon + 180) / 360 * n, (1 - np.arcsinh(np.tan(np.radians(lat))) / np.pi) / 2 * n


VS = '''#version 330
uniform mat4 mvp;
in vec3 p; in vec3 nrm; in vec2 t16; in float slope; in float acc;
out vec3 wp; out vec3 wn; out vec2 vt; out float vs; out float va;
void main(){ wp=p; wn=nrm; vt=t16; vs=slope; va=acc; gl_Position=mvp*vec4(p,1.0); }'''
FS = '''#version 330
uniform sampler2D tex18; uniform sampler2D tex17; uniform sampler2D tex16;
uniform vec4 ext18; uniform vec4 ext17; uniform vec4 ext16;
uniform vec3 sun; uniform vec3 eye; uniform vec2 focus; uniform float slope_mix; uniform float drain_mix; uniform float haze; uniform float dim;
in vec3 wp; in vec3 wn; in vec2 vt; in float vs; in float va; out vec4 o;
vec3 smp(sampler2D t, vec4 e, float zf, out float ok){
  vec2 q=vt*zf; vec2 uv=(q-e.xy)/e.zw; ok=step(0.0,uv.x)*step(uv.x,1.0)*step(0.0,uv.y)*step(uv.y,1.0);
  return texture(t,uv,-0.7).rgb; }
vec3 ramp(float s){ // slope 0..40 deg: green-yellow-orange-red
  vec3 a=vec3(0.10,0.60,0.30), b=vec3(0.99,0.88,0.40), c=vec3(0.96,0.43,0.26), d=vec3(0.65,0.0,0.15);
  float t=clamp(s/40.0,0.0,1.0)*3.0; return t<1.0?mix(a,b,t):(t<2.0?mix(b,c,t-1.0):mix(c,d,t-2.0)); }
void main(){
  float k18,k17,k16; vec3 c18=smp(tex18,ext18,4.0,k18); vec3 c17=smp(tex17,ext17,2.0,k17); vec3 c16=smp(tex16,ext16,1.0,k16);
  vec3 col=mix(mix(c16,c17,k17),c18,k18);
  vec3 n=normalize(wn); float dif=max(dot(n,normalize(sun)),0.0);
  float shade=(0.55+0.62*dif)/(0.55+0.62*max(sun.z,0.3)); col*=mix(1.0,shade,0.9);
  if(slope_mix>0.0){ float m=slope_mix*smoothstep(6.0,14.0,vs)*0.5*(1.0-smoothstep(1300.0,2200.0,length(wp.xy-focus))); col=mix(col,ramp(vs)*(0.75+0.35*dif),m); }
  if(drain_mix>0.0){ float m=drain_mix*smoothstep(0.9,1.4,va)*(1.0-smoothstep(1500.0,2500.0,length(wp.xy-focus))); col=mix(col,vec3(0.2,0.78,1.0),m*0.95); }
  col*=1.0-dim;
  float d=length(wp-eye); float f=1.0-exp(-pow(d/(26000.0/haze),1.4));
  col=mix(col,vec3(0.82,0.83,0.84),f*0.75);
  float l=dot(col,vec3(0.299,0.587,0.114)); col=(col-0.5)*1.07+0.5;
  o=vec4(col,1.0); }'''
