/* DRONE TRG COMPLEX - 44 DIV : detailed procedural vehicles for the proposal renderer.
   Built from the reference photographs supplied: tracked dozer (elevated sprocket, blade, ripper), hydraulic excavator,
   backhoe loader, 4-axle all-terrain mobile crane, army pickup with troops, 6x6 MRAP, army cargo/shelter truck.
   Local axes (ENU): x forward, y left, z up, origin on the ground at the vehicle centre. Units metres.
   Every vehicle returns { g, set(p) } where set() poses joints, rolls wheels / runs track plates and lights. */
(function () {
const V = {};
const cache = {};
function M(hex, o) {
  const k = hex + JSON.stringify(o || {});
  if (!cache[k]) cache[k] = new THREE.MeshStandardMaterial(Object.assign({ color: new THREE.Color(hex).convertSRGBToLinear(), roughness: 0.55, metalness: 0.05, envMapIntensity: 0.7 }, o || {}));
  return cache[k];
}
const MAT = {
  cat: () => M(0xf3b51a, { roughness: 0.42, envMapIntensity: 0.9 }), yel: () => M(0xf0b414, { roughness: 0.45, envMapIntensity: 0.9 }),
  dark: () => M(0x2b2b2c, { roughness: 0.6, metalness: 0.3 }), steel: () => M(0x8d9094, { roughness: 0.35, metalness: 0.85 }),
  chrome: () => M(0xd8dadc, { roughness: 0.15, metalness: 1.0 }), rubber: () => M(0x161616, { roughness: 0.92 }),
  black: () => M(0x0f0f10, { roughness: 0.5 }), glass: () => M(0x2a3a44, { roughness: 0.04, metalness: 0.2, transparent: true, opacity: 0.55, envMapIntensity: 1.6 }),
  white: () => M(0xf2f2ee, { roughness: 0.45 }), red: () => M(0xc8201e, { roughness: 0.45 }), rust: () => M(0x5a4a3a, { roughness: 0.9, metalness: 0.2 }),
  olive: () => M(0x4a5230, { roughness: 0.78 }), oliveD: () => M(0x3a4126, { roughness: 0.8 }), tan: () => M(0xc9b58c, { roughness: 0.72 }),
  tanD: () => M(0xa8946c, { roughness: 0.75 }), canvas: () => M(0x5b5f3a, { roughness: 0.95 }),
  lamp: () => new THREE.MeshStandardMaterial({ color: 0xfff4d8, emissive: 0xfff1cc, emissiveIntensity: 0.25, roughness: 0.2 }),
  tail: () => new THREE.MeshStandardMaterial({ color: 0x881111, emissive: 0xff2222, emissiveIntensity: 0.2, roughness: 0.3 }),
  amber: () => new THREE.MeshStandardMaterial({ color: 0xc87a10, emissive: 0xffa020, emissiveIntensity: 0.2, roughness: 0.3 }),
};
V.MAT = MAT;
const lamps = [];      // emissive materials switched on at night / dusk
V.setNight = k => { MAT.lamp().emissiveIntensity = 0.25 + 3.5 * k; MAT.tail().emissiveIntensity = 0.2 + 2.0 * k; MAT.amber().emissiveIntensity = 0.2 + 2.5 * k; };

/* ---------- geometry helpers ---------- */
function mesh(geo, mat, x = 0, y = 0, z = 0, parent) { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; if (parent) parent.add(m); return m; }
// rounded box centred at (x,y,z): w along x, d along y, h along z, edge radius r
function rbox(w, d, h, r, mat, x, y, z, parent) {
  r = Math.min(r, w / 2 - 1e-3, d / 2 - 1e-3, h / 2 - 1e-3);
  const s = new THREE.Shape(), a = w / 2 - r, b = d / 2 - r;
  s.moveTo(-a, -d / 2); s.lineTo(a, -d / 2); s.quadraticCurveTo(w / 2, -d / 2, w / 2, -b); s.lineTo(w / 2, b); s.quadraticCurveTo(w / 2, d / 2, a, d / 2);
  s.lineTo(-a, d / 2); s.quadraticCurveTo(-w / 2, d / 2, -w / 2, b); s.lineTo(-w / 2, -b); s.quadraticCurveTo(-w / 2, -d / 2, -a, -d / 2);
  const g = new THREE.ExtrudeGeometry(s, { depth: h - 2 * r, bevelEnabled: r > 0.005, bevelSize: r, bevelThickness: r, bevelSegments: 2, curveSegments: 3 });
  g.translate(0, 0, -(h - 2 * r) / 2);
  return mesh(g, mat, x, y, z, parent);
}
// side profile [[x,z],...] extruded across y (width w) centred at y0; bevel b
function side(pts, w, mat, y0 = 0, parent, b = 0.02) {
  const s = new THREE.Shape(pts.map(p => new THREE.Vector2(p[0], p[1])));
  const g = new THREE.ExtrudeGeometry(s, { depth: Math.max(w - 2 * b, 0.001), bevelEnabled: b > 0, bevelSize: b, bevelThickness: b, bevelSegments: 1, curveSegments: 6 });
  g.rotateX(Math.PI / 2); g.translate(0, y0 + w - b, 0);
  return mesh(g, mat, 0, 0, 0, parent);
}
// plan profile [[x,y],...] extruded up from z0 by h
function plan(pts, z0, h, mat, parent, b = 0.02) {
  const s = new THREE.Shape(pts.map(p => new THREE.Vector2(p[0], p[1])));
  const g = new THREE.ExtrudeGeometry(s, { depth: Math.max(h - 2 * b, 0.001), bevelEnabled: b > 0, bevelSize: b, bevelThickness: b, bevelSegments: 1, curveSegments: 8 });
  g.translate(0, 0, z0 + b); return mesh(g, mat, 0, 0, 0, parent);
}
function cylY(r, w, mat, x, y, z, parent, seg = 24) { const g = new THREE.CylinderGeometry(r, r, w, seg); return mesh(g, mat, x, y, z, parent); }
function cylZ(r, h, mat, x, y, z, parent, seg = 20, r2) { const g = new THREE.CylinderGeometry(r2 === undefined ? r : r2, r, h, seg); g.rotateX(Math.PI / 2); return mesh(g, mat, x, y, z, parent); }
function cylX(r, l, mat, x, y, z, parent, seg = 16) { const g = new THREE.CylinderGeometry(r, r, l, seg); g.rotateZ(Math.PI / 2); return mesh(g, mat, x, y, z, parent); }
// a bar between two points (local to parent)
function bar(a, b, r, mat, parent, seg = 10) {
  const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b), L = A.distanceTo(B);
  const g = new THREE.CylinderGeometry(r, r, L, seg); const m = mesh(g, mat, 0, 0, 0, parent);
  m.position.copy(A).add(B).multiplyScalar(0.5); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), B.clone().sub(A).normalize()); return m;
}
// lugged off-road tyre (axis along y) with rim and hub nuts; returns a group to spin about y
function wheel(r, w, rimCol, parent, x, y, z, lug = 0.035) {
  const g = new THREE.Group(); g.position.set(x, y, z); parent.add(g);
  // tyre carcass: rounded lathe profile; tread: chevron lug blocks merged into one mesh
  const prof = [], rs = 0.16 * w, ri = r * 0.62;
  prof.push(new THREE.Vector2(ri, -w / 2));
  for (let i = 0; i <= 6; i++) { const a = -Math.PI / 2 + i / 6 * Math.PI / 2; prof.push(new THREE.Vector2(r - lug - rs + Math.cos(a) * rs, -w / 2 + rs + Math.sin(a) * rs)); }
  for (let i = 0; i <= 6; i++) { const a = i / 6 * Math.PI / 2; prof.push(new THREE.Vector2(r - lug - rs + Math.cos(a) * rs, w / 2 - rs + Math.sin(a) * rs)); }
  prof.push(new THREE.Vector2(ri, w / 2));
  mesh(new THREE.LatheGeometry(prof, 48), MAT.rubber(), 0, 0, 0, g);
  const n = Math.round(2 * Math.PI * r / (lug * 3.4)), lugs = [];
  for (let k = 0; k < n; k++) for (const sd of [-1, 1]) {
    const b = new THREE.BoxGeometry(lug * 1.5, w * 0.42, lug * 1.6); b.rotateZ(sd * 0.45 * (k % 2 ? 1 : -1) * 0 + sd * 0.35);
    b.translate(0, sd * w * 0.23, r - lug * 0.75); b.rotateX(0); const a = (k + (sd > 0 ? 0.5 : 0)) / n * Math.PI * 2;
    b.applyMatrix4(new THREE.Matrix4().makeRotationY(a)); lugs.push(b.toNonIndexed());
  }
  const tl = new THREE.Mesh(THREE.BufferGeometryUtils.mergeBufferGeometries(lugs), MAT.rubber()); tl.castShadow = true; g.add(tl);
  // lathe axis is y already (LatheGeometry revolves about y)
  for (const s of [-1, 1]) {   // sidewalls (lathe ring) and rims
    const rim = new THREE.CylinderGeometry(r * 0.6, r * 0.62, 0.04, 28); mesh(rim, rimCol, 0, s * (w / 2 - 0.05), 0, g);
    const hub = new THREE.CylinderGeometry(r * 0.22, r * 0.26, 0.08, 16); mesh(hub, MAT.dark(), 0, s * (w / 2 - 0.02), 0, g);
    for (let k = 0; k < 8; k++) { const a = k / 8 * Math.PI * 2; cylY(0.022, 0.05, MAT.steel(), Math.cos(a) * r * 0.36, s * (w / 2 - 0.01), Math.sin(a) * r * 0.36, g, 6); }
    const back = new THREE.CircleGeometry(r * 0.6, 28); back.rotateX(s * Math.PI / 2); mesh(back, rimCol, 0, s * (w / 2 - 0.08), 0, g);
  }
  return g;
}
// hydraulic ram between two objects' local anchor points (barrel from A, rod from B); call .update() each frame
function ram(parent, objA, pA, objB, pB, rB, rR) {
  const barrel = mesh(new THREE.CylinderGeometry(rB, rB, 1, 14), MAT.yel(), 0, 0, 0, parent);
  const rod = mesh(new THREE.CylinderGeometry(rR, rR, 1, 12), MAT.chrome(), 0, 0, 0, parent);
  const A = new THREE.Vector3(), B = new THREE.Vector3(), Y = new THREE.Vector3(0, 1, 0), inv = new THREE.Matrix4();
  return { barrel, rod, update() {
    parent.updateMatrixWorld(true); inv.copy(parent.matrixWorld).invert();
    A.set(...pA).applyMatrix4(objA.matrixWorld).applyMatrix4(inv); B.set(...pB).applyMatrix4(objB.matrixWorld).applyMatrix4(inv);
    const L = A.distanceTo(B), dir = B.clone().sub(A).normalize(), q = new THREE.Quaternion().setFromUnitVectors(Y, dir);
    const lb = L * 0.58; barrel.scale.set(1, lb, 1); barrel.position.copy(A).addScaledVector(dir, lb / 2); barrel.quaternion.copy(q);
    const lr = L * 0.5; rod.scale.set(1, lr, 1); rod.position.copy(B).addScaledVector(dir, -lr / 2); rod.quaternion.copy(q);
  } };
}
// crawler track: loop around wheel circles [[x,z,r],...] in the x-z plane at lateral offset y; plates run with distance s
function track(parent, wheels, y, width, pitch = 0.24) {
  const pts = [];
  for (const [cx, cz, r] of wheels) for (let i = 0; i < 48; i++) { const a = i / 48 * Math.PI * 2; pts.push([cx + Math.cos(a) * (r + 0.06), cz + Math.sin(a) * (r + 0.06)]); }
  pts.sort((a, b) => a[0] - b[0] || a[1] - b[1]);                            // convex hull (monotone chain)
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]), lo = [], up = [];
  for (const p of pts) { while (lo.length >= 2 && cross(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p); }
  for (const p of pts.slice().reverse()) { while (up.length >= 2 && cross(up[up.length - 2], up[up.length - 1], p) <= 0) up.pop(); up.push(p); }
  const hull = lo.slice(0, -1).concat(up.slice(0, -1)); const seg = []; let per = 0;
  for (let i = 0; i < hull.length; i++) { const a = hull[i], b = hull[(i + 1) % hull.length], L = Math.hypot(b[0] - a[0], b[1] - a[1]); seg.push([a, b, L, per]); per += L; }
  const n = Math.floor(per / pitch), P = per / n;
  const plateG = new THREE.BoxGeometry(P * 0.92, width, 0.05); const lugG = new THREE.BoxGeometry(0.045, width, 0.06); lugG.translate(0, 0, -0.05);
  const geo = THREE.BufferGeometryUtils.mergeBufferGeometries([plateG.toNonIndexed(), lugG.toNonIndexed()]);
  const im = new THREE.InstancedMesh(geo, MAT.dark(), n); im.castShadow = im.receiveShadow = true; parent.add(im);
  const at = d => { d = ((d % per) + per) % per; let k = 0; while (k < seg.length - 1 && seg[k][3] + seg[k][2] < d) k++; const [a, b, L, s0] = seg[k], u = (d - s0) / L; return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, Math.atan2(b[1] - a[1], b[0] - a[0])]; };
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), pos = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1);
  const t = { per, set(s) { for (let i = 0; i < n; i++) { const [x, z, ang] = at(i * P - s); e.set(0, -ang, 0); q.setFromEuler(e); pos.set(x, y, z); m4.compose(pos, q, one); im.setMatrixAt(i, m4); } im.instanceMatrix.needsUpdate = true; } };
  t.set(0); return t;
}
function trackWheels(parent, wheels, y, w, mat) { return wheels.map(([x, z, r]) => { const g = new THREE.Group(); g.position.set(x, y, z); parent.add(g); cylY(r, w, mat, 0, 0, 0, g, 24); for (let k = 0; k < 6; k++) { const a = k / 6 * Math.PI * 2; cylY(0.03, w + 0.02, MAT.steel(), Math.cos(a) * r * 0.55, 0, Math.sin(a) * r * 0.55, g, 6); } return { g, r }; }); }
function glassBox(w, d, h, x, y, z, parent) { return rbox(w, d, h, 0.03, MAT.glass(), x, y, z, parent); }
function lamp(parent, x, y, z, r = 0.09, dir = 'x') { const m = dir === 'x' ? cylX(r, 0.08, MAT.lamp(), x, y, z, parent, 14) : cylZ(r, 0.08, MAT.lamp(), x, y, z, parent, 14); return m; }
function stripes(w, h, nStripe = 4) {     // red / white chevron safety panel texture
  const c = document.createElement('canvas'); c.width = 128; c.height = 256; const g = c.getContext('2d'); g.fillStyle = '#f4f4f0'; g.fillRect(0, 0, 128, 256);
  g.fillStyle = '#c8201e'; for (let i = -4; i < 10; i++) { g.beginPath(); g.moveTo(0, i * 48); g.lineTo(128, i * 48 + 64); g.lineTo(128, i * 48 + 88); g.lineTo(0, i * 48 + 24); g.fill(); }
  const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; return new THREE.MeshStandardMaterial({ map: t, roughness: 0.5 });
}

/* ---------- people ---------- */
const skin = () => M(0x8a5a3c, { roughness: 0.7 });
function person(o) {          // o: {uniform:'worker'|'soldier', seated, rifle}
  const g = new THREE.Group(), sol = o.uniform === 'soldier';
  const cloth = sol ? M(0x5f6440, { roughness: 0.95 }) : M(0x4a5d78, { roughness: 0.9 }), vest = sol ? M(0x4c5233, { roughness: 0.9 }) : M(0xff7a12, { roughness: 0.6, emissive: 0x401800, emissiveIntensity: 0.2 });
  const hat = sol ? M(0x50553a, { roughness: 0.85 }) : M(0xffffff, { roughness: 0.35 }), boot = M(0x2a2018, { roughness: 0.8 });
  const hip = new THREE.Group(); hip.position.z = o.seated ? 0.48 : 0.92; g.add(hip);
  const legs = [];
  for (const s of [-1, 1]) {
    const L = new THREE.Group(); L.position.set(0, s * 0.1, 0); hip.add(L);
    rbox(0.16, 0.15, 0.46, 0.05, cloth, 0, 0, -0.23, L); const kn = new THREE.Group(); kn.position.z = -0.46; L.add(kn);
    rbox(0.14, 0.13, 0.44, 0.05, cloth, 0, 0, -0.22, kn); rbox(0.26, 0.12, 0.1, 0.03, boot, 0.05, 0, -0.46, kn);
    if (o.seated) { L.rotation.y = -Math.PI / 2; kn.rotation.y = Math.PI / 2; }
    legs.push({ L, kn });
  }
  const torso = new THREE.Group(); hip.add(torso);
  rbox(0.24, 0.38, 0.56, 0.08, cloth, 0, 0, 0.3, torso); rbox(0.27, 0.41, 0.4, 0.07, vest, 0, 0, 0.33, torso);
  if (!sol) for (const z of [0.25, 0.4]) rbox(0.275, 0.415, 0.04, 0.01, M(0xd8d8d0, { roughness: 0.2, metalness: 0.3, emissive: 0x666660, emissiveIntensity: 0.3 }), 0, 0, z, torso);
  mesh(new THREE.SphereGeometry(0.105, 16, 12), skin(), 0.02, 0, 0.72, torso);
  if (sol) { const h = mesh(new THREE.SphereGeometry(0.135, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2), hat, 0.0, 0, 0.75, torso); h.rotation.x = Math.PI / 2; h.scale.set(1, 0.8, 1); }
  else { const h = mesh(new THREE.SphereGeometry(0.13, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2), hat, 0.01, 0, 0.77, torso); h.rotation.x = Math.PI / 2; cylZ(0.17, 0.015, hat, 0.03, 0, 0.775, torso, 18); }
  const arms = [];
  for (const s of [-1, 1]) { const A = new THREE.Group(); A.position.set(0, s * 0.23, 0.55); torso.add(A); rbox(0.11, 0.11, 0.3, 0.04, cloth, 0, 0, -0.15, A); const el = new THREE.Group(); el.position.z = -0.3; A.add(el); rbox(0.1, 0.1, 0.28, 0.04, cloth, 0, 0, -0.14, el); mesh(new THREE.SphereGeometry(0.05, 8, 6), skin(), 0, 0, -0.3, el); arms.push({ A, el }); }
  if (o.rifle) { const r = new THREE.Group(); r.position.set(0.22, 0, 0.32); r.rotation.y = -1.1; torso.add(r); rbox(0.75, 0.05, 0.08, 0.01, M(0x1b1b1b, { roughness: 0.5, metalness: 0.4 }), 0, 0, 0, r); rbox(0.1, 0.05, 0.18, 0.01, M(0x1b1b1b), 0.05, 0, -0.1, r);
    arms[0].A.rotation.y = -0.9; arms[0].el.rotation.y = -0.8; arms[1].A.rotation.y = -0.6; arms[1].el.rotation.y = -1.2; }
  if (o.seated) { arms.forEach(a => { if (!o.rifle) { a.A.rotation.y = -0.4; a.el.rotation.y = -0.9; } }); }
  g.traverse(m => { if (m.isMesh) m.castShadow = true; });
  return { g, walk(ph, amp = 1) { if (o.seated) return; legs.forEach((l, i) => { const s = Math.sin(ph + i * Math.PI) * 0.45 * amp; l.L.rotation.y = s; l.kn.rotation.y = Math.max(0, -s) * 1.1; });
    if (!o.rifle) arms.forEach((a, i) => { a.A.rotation.y = -Math.sin(ph + i * Math.PI) * 0.4 * amp; a.el.rotation.y = -0.25; }); hip.position.z = 0.92 + Math.abs(Math.sin(ph)) * 0.025 * amp; },
    work(ph) { arms.forEach((a, i) => { a.A.rotation.y = -1.0 - Math.sin(ph * 2 + i) * 0.35; a.el.rotation.y = -0.6; }); torso.rotation.y = 0.35 + Math.sin(ph * 2) * 0.12; } };
}
V.person = person;

/* ---------- 1. tracked dozer (D8 class: elevated sprocket, semi-U blade, single-shank ripper) ---------- */
V.dozer = function () {
  const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  const Y = 1.12, TW = 0.61;
  const wh = [[-1.55, 1.42, 0.58], [1.72, 0.44, 0.42], [-1.42, 0.44, 0.42], [-0.7, 0.3, 0.26], [0.0, 0.3, 0.26], [0.7, 0.3, 0.26], [1.15, 0.3, 0.26]];
  const tracks = [], rollers = [];
  for (const s of [-1, 1]) {
    tracks.push(track(g, wh, s * Y, TW));
    rollers.push(...trackWheels(g, wh, s * Y, TW - 0.1, MAT.dark()));
    side([[-1.75, 0.55], [1.55, 0.55], [1.7, 0.75], [-1.0, 1.05], [-1.7, 0.85]], 0.36, MAT.cat(), s * (Y - 0.02) - 0.18, g, 0.03);   // track roller frame
    // sprocket segments (teeth)
    for (let k = 0; k < 11; k++) { const a = k / 11 * Math.PI * 2; rbox(0.12, TW - 0.15, 0.08, 0.02, MAT.dark(), -1.55 + Math.cos(a) * 0.6, s * Y, 1.42 + Math.sin(a) * 0.6, g); }
  }
  // main frame, engine hood, radiator guard, fuel tank, fenders
  rbox(3.2, 1.3, 0.55, 0.05, MAT.dark(), 0.1, 0, 0.82, body);
  side([[-0.25, 1.05], [2.25, 1.05], [2.3, 1.95], [2.1, 2.18], [-0.25, 2.25]], 1.36, MAT.cat(), -0.68, body, 0.05);
  for (let k = 0; k < 7; k++) rbox(0.05, 1.1, 0.06, 0.01, MAT.black(), 2.33, 0, 1.2 + k * 0.12, body);   // radiator grille slats
  rbox(0.08, 1.24, 0.98, 0.02, MAT.cat(), 2.36, 0, 1.6, body);
  for (const s of [-1, 1]) { rbox(0.07, 0.07, 0.98, 0.02, MAT.cat(), 2.38, s * 0.58, 1.6, body); rbox(2.6, 0.06, 0.05, 0.01, MAT.dark(), 0.95, s * 0.69, 2.12, body); }
  for (let k = 0; k < 5; k++) rbox(0.5, 0.02, 0.03, 0.005, MAT.black(), 0.6 + k * 0.32, 0.69, 1.65, body);   // engine side louvres
  for (let k = 0; k < 5; k++) rbox(0.5, 0.02, 0.03, 0.005, MAT.black(), 0.6 + k * 0.32, -0.69, 1.65, body);
  cylZ(0.09, 1.0, MAT.black(), 1.65, -0.35, 2.7, body, 14); cylZ(0.11, 0.08, MAT.black(), 1.65, -0.35, 3.2, body, 14);         // exhaust stack
  cylZ(0.14, 0.5, MAT.cat(), 1.65, 0.35, 2.45, body, 16); cylZ(0.17, 0.12, MAT.dark(), 1.65, 0.35, 2.75, body, 16);           // air pre-cleaner
  for (const s of [-1, 1]) side([[-2.1, 1.55], [2.0, 1.55], [2.0, 1.62], [-2.1, 1.62]], 0.75, MAT.cat(), s * 1.18 - 0.375, body, 0.01);   // fenders / walkways
  rbox(0.9, 1.9, 0.75, 0.05, MAT.cat(), -1.75, 0, 1.55, body);       // rear fuel tank
  // ROPS cab
  rbox(1.75, 1.7, 0.2, 0.04, MAT.cat(), -0.95, 0, 2.2, body);
  for (const [x, y] of [[-1.78, -0.8], [-1.78, 0.8], [-0.12, -0.8], [-0.12, 0.8]]) rbox(0.12, 0.12, 1.3, 0.03, MAT.cat(), x, y, 2.95, body);
  rbox(1.95, 1.9, 0.14, 0.05, MAT.cat(), -0.95, 0, 3.66, body); rbox(1.7, 1.7, 0.08, 0.03, MAT.dark(), -0.95, 0, 3.77, body);
  glassBox(1.6, 1.56, 1.25, -0.95, 0, 2.92, body);
  rbox(0.5, 0.55, 0.12, 0.03, MAT.black(), -1.1, 0, 2.55, body); rbox(0.12, 0.5, 0.6, 0.03, MAT.black(), -1.32, 0, 2.85, body);    // seat
  for (const [x, y] of [[-0.05, 0.75], [-0.05, -0.75], [-1.85, 0.75], [-1.85, -0.75]]) lamp(body, x + (x > -1 ? 0.06 : -0.06), y, 3.55, 0.08, 'x');
  lamp(body, 2.38, 0.45, 2.0, 0.09); lamp(body, 2.38, -0.45, 2.0, 0.09);
  cylZ(0.07, 0.12, MAT.amber(), -0.95, 0.5, 3.86, body, 12);          // beacon
  for (const s of [-1, 1]) { for (let k = 0; k < 4; k++) rbox(0.03, 0.03, 0.4, 0.01, MAT.black(), -0.15 + k * 0.03, s * 1.5, 1.9, body); bar([-2.0, s * 1.5, 1.62], [-2.0, s * 1.5, 2.6], 0.025, MAT.cat(), body); bar([-2.0, s * 1.5, 2.6], [-0.2, s * 1.5, 2.6], 0.025, MAT.cat(), body); }
  // blade on push arms
  const blade = new THREE.Group(); blade.position.set(3.0, 0, 0.0); body.add(blade);
  const prof = []; for (let i = 0; i <= 12; i++) { const a = -0.2 + i / 12 * 1.9; prof.push([0.3 - Math.sin(a) * 0.55, 0.05 + (1 - Math.cos(a)) * 0.72]); }
  const back = prof.slice().reverse().map(([x, z]) => [x + 0.12, z]);
  side(prof.concat(back), 4.25, MAT.cat(), -2.125, blade, 0.02);
  for (const s of [-1, 1]) side([[0.15, 0.0], [0.6, 0.0], [0.62, 1.65], [0.12, 1.55]], 0.08, MAT.cat(), s * 2.12 - 0.04, blade, 0.01);   // end bits / wings
  rbox(0.1, 4.25, 0.12, 0.01, MAT.steel(), 0.35, 0, 0.06, blade);   // cutting edge
  for (const s of [-1, 1]) { side([[-2.9, 0.62], [-0.1, 0.45], [-0.05, 0.85], [-2.9, 0.82]], 0.22, MAT.cat(), s * 1.48 - 0.11, blade, 0.02); }   // push arms
  const liftR = [-1, 1].map(s => ram(body, body, [1.9, s * 0.62, 2.1], blade, [-0.1, s * 0.62, 1.42], 0.11, 0.065));
  const tiltR = ram(body, body, [2.2, 0.4, 1.3], blade, [-0.05, 1.2, 1.5], 0.08, 0.05);
  // ripper
  const rip = new THREE.Group(); rip.position.set(-2.25, 0, 1.05); body.add(rip);
  rbox(0.9, 1.6, 0.28, 0.04, MAT.cat(), -0.55, 0, 0, rip); side([[-0.55, 0.1], [-0.35, 0.1], [-0.2, -1.05], [-0.42, -1.15], [-0.6, -1.0]], 0.14, MAT.cat(), -0.07, rip, 0.01);
  rbox(0.14, 0.1, 0.2, 0.02, MAT.steel(), -0.36, 0, -1.12, rip);
  const ripR = [-1, 1].map(s => ram(body, body, [-2.05, s * 0.5, 2.05], rip, [-0.3, s * 0.5, 0.12], 0.09, 0.055));
  body.traverse(m => { if (m.isMesh) m.castShadow = true; });
  let last = 0;
  return { g, set(p) {
    const s = p.s || 0; tracks.forEach(t => t.set(s)); rollers.forEach(w => { w.g.rotation.y = s / w.r; });
    blade.position.z = (p.blade || 0); blade.rotation.y = (p.bladeTilt || 0); rip.rotation.y = p.ripper || 0;
    body.position.z = Math.sin(s * 3.1) * 0.012; body.rotation.y = Math.sin(s * 1.7) * 0.004;
    liftR.forEach(r => r.update()); tiltR.update(); ripR.forEach(r => r.update());
  }, load: null };
};

/* ---------- 2. hydraulic excavator (PC300 class) ---------- */
V.excavator = function () {
  const g = new THREE.Group();
  const Y = 1.3, TW = 0.6, wh = [[-2.05, 0.45, 0.42], [2.05, 0.45, 0.42], [-1.2, 0.27, 0.22], [-0.4, 0.27, 0.22], [0.4, 0.27, 0.22], [1.2, 0.27, 0.22], [-0.8, 0.82, 0.12], [0.8, 0.82, 0.12]];
  const tracks = [], rollers = [];
  for (const s of [-1, 1]) { tracks.push(track(g, wh, s * Y, TW, 0.2)); rollers.push(...trackWheels(g, wh, s * Y, TW - 0.1, MAT.dark()));
    side([[-2.0, 0.3], [2.0, 0.3], [2.1, 0.55], [1.8, 0.75], [-1.8, 0.75], [-2.1, 0.55]], 0.3, MAT.dark(), s * Y - 0.15, g, 0.03); }
  rbox(1.6, 2.1, 0.45, 0.06, MAT.dark(), 0, 0, 0.82, g); cylZ(0.75, 0.2, MAT.dark(), 0, 0, 1.12, g, 32);      // car body, swing ring
  const up = new THREE.Group(); up.position.z = 1.22; g.add(up);
  rbox(3.4, 2.75, 0.22, 0.05, MAT.yel(), -0.35, 0, 0.11, up);                                                   // deck
  side([[-2.25, 0.22], [-0.35, 0.22], [-0.35, 1.25], [-2.05, 1.35], [-2.3, 1.15]], 2.7, MAT.yel(), -1.35, up, 0.06);   // engine hood & counterweight
  plan([[-2.05, -1.38], [-2.35, -1.0], [-2.45, 0], [-2.35, 1.0], [-2.05, 1.38], [-1.6, 1.38], [-1.6, -1.38]], 0.1, 1.0, MAT.yel(), up, 0.06);
  for (let k = 0; k < 6; k++) rbox(0.04, 0.9, 0.03, 0.01, MAT.black(), -1.7 + k * 0.2, -0.3, 1.27, up);         // engine grille
  rbox(1.0, 1.0, 0.06, 0.02, MAT.dark(), -0.6, -0.75, 1.3, up);
  cylZ(0.08, 0.6, MAT.black(), -0.95, -1.05, 1.55, up, 12);                                                     // exhaust
  rbox(1.4, 0.95, 0.95, 0.05, MAT.yel(), 0.25, -0.85, 0.7, up);                                                  // tool box / tank (right front)
  for (const [x, y, z] of [[-1.2, 1.36, 0.8], [-0.7, 1.36, 0.8]]) rbox(0.3, 0.02, 0.3, 0.01, MAT.black(), x, y, z, up);
  // cab (left front)
  const cab = new THREE.Group(); cab.position.set(0.9, 0.78, 0.22); up.add(cab);
  side([[-0.9, 0], [0.85, 0], [0.9, 1.15], [0.75, 1.62], [-0.9, 1.62]], 0.98, MAT.yel(), -0.49, cab, 0.05);
  side([[-0.78, 0.55], [0.78, 0.55], [0.82, 1.12], [0.7, 1.52], [-0.78, 1.52]], 1.0, MAT.glass(), -0.5, cab, 0.0);
  rbox(1.8, 1.02, 0.08, 0.03, MAT.dark(), 0, 0, 1.66, cab); rbox(0.08, 1.0, 0.12, 0.02, MAT.yel(), 0.85, 0, 0.5, cab);
  rbox(0.5, 0.5, 0.5, 0.06, MAT.black(), -0.25, 0, 0.75, cab);    // operator seat seen through glass
  lamp(cab, 0.92, 0.3, 1.5, 0.06); lamp(cab, 0.92, -0.3, 1.5, 0.06); lamp(up, 0.95, -0.35, 1.2, 0.08);
  cylZ(0.06, 0.1, MAT.amber(), -1.0, 0.7, 1.4, up, 12);
  for (let k = 0; k < 5; k++) rbox(0.3, 0.02, 0.06, 0.01, M(0x1a1a1a), 0.3 + k * 0.07, 1.36, 0.2, up);
  // boom (banana), stick, bucket with linkage
  const boom = new THREE.Group(); boom.position.set(0.55, -0.2, 0.55); up.add(boom);
  side([[-0.25, -0.2], [0.2, -0.35], [2.6, 0.95], [3.4, 1.15], [5.6, 0.3], [5.75, 0.55], [3.4, 1.65], [2.5, 1.55], [-0.2, 0.3]], 0.62, MAT.yel(), -0.31, boom, 0.05);
  cylY(0.18, 0.7, MAT.dark(), 0, 0, 0, boom, 16); cylY(0.16, 0.7, MAT.dark(), 5.6, 0, 0.45, boom, 16);
  const stick = new THREE.Group(); stick.position.set(5.6, 0, 0.45); boom.add(stick);
  side([[-0.55, 0.35], [-0.1, -0.25], [3.0, -0.18], [3.05, 0.12], [0.2, 0.42]], 0.48, MAT.yel(), -0.24, stick, 0.04);
  const bucket = new THREE.Group(); bucket.position.set(3.0, 0, 0); stick.add(bucket);
  const bp = []; for (let i = 0; i <= 10; i++) { const a = i / 10 * 2.1; bp.push([Math.sin(a) * 0.75 + 0.05, -Math.cos(a) * 0.62 + 0.02]); }
  side(bp.concat([[0.25, 0.25], [-0.15, 0.2]]), 1.4, M(0x5c5c5e, { roughness: 0.6, metalness: 0.4 }), -0.7, bucket, 0.03);
  for (let k = 0; k < 5; k++) rbox(0.28, 0.12, 0.1, 0.02, MAT.steel(), 0.9, -0.56 + k * 0.28, 0.32, bucket).rotation.y = -0.5;
  for (const s of [-1, 1]) side([[-0.2, 0.2], [0.35, 0.3], [0.85, 0.32], [0.8, 0.45], [-0.2, 0.32]], 0.03, MAT.dark(), s * 0.7, bucket, 0.005);
  const rBoom = [-1, 1].map(s => ram(up, up, [0.85, -0.2 + s * 0.45, 0.35], boom, [2.3, s * 0.42, 0.6], 0.13, 0.075));
  const rStick = ram(up, boom, [2.9, 0, 1.6], stick, [-0.5, 0, 0.42], 0.12, 0.07);
  const rBucket = ram(up, stick, [0.2, 0, 0.45], bucket, [-0.1, 0, 0.32], 0.1, 0.06);
  g.traverse(m => { if (m.isMesh) m.castShadow = true; });
  return { g, up, bucket, set(p) {
    const s = p.s || 0; tracks.forEach(t => t.set(s)); rollers.forEach(w => { w.g.rotation.y = s / w.r; });
    up.rotation.z = p.swing || 0; boom.rotation.y = -(p.boom ?? 0.35); stick.rotation.y = p.stick ?? 1.4; bucket.rotation.y = p.bucket ?? 1.2;
    rBoom.forEach(r => r.update()); rStick.update(); rBucket.update();
  } };
};

/* ---------- 3. backhoe loader (3CX class) ---------- */
V.backhoe = function () {
  const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  const rimY = MAT.yel(), wheels = [];
  for (const s of [-1, 1]) { wheels.push(wheel(0.78, 0.52, rimY, g, -1.05, s * 0.95, 0.78, 0.045)); wheels.push(wheel(0.53, 0.38, rimY, g, 1.35, s * 0.88, 0.53, 0.035)); }
  rbox(3.6, 0.9, 0.45, 0.05, MAT.dark(), 0.1, 0, 0.75, body);
  side([[0.35, 0.85], [2.05, 0.85], [2.2, 1.25], [2.0, 1.62], [0.35, 1.72]], 1.0, MAT.yel(), -0.5, body, 0.06);     // engine hood
  for (let k = 0; k < 6; k++) rbox(0.03, 0.8, 0.03, 0.01, MAT.black(), 2.2, 0, 1.0 + k * 0.08, body);
  lamp(body, 2.1, 0.38, 1.55, 0.08); lamp(body, 2.1, -0.38, 1.55, 0.08);
  cylZ(0.06, 0.6, MAT.black(), 1.5, -0.3, 1.95, body, 12);
  for (const s of [-1, 1]) { side([[-1.9, 1.3], [-0.25, 1.3], [-0.2, 1.72], [-1.85, 1.72]], 0.4, MAT.yel(), s * 1.0 - 0.2, body, 0.02); side([[0.85, 0.95], [1.85, 0.95], [1.9, 1.1], [0.8, 1.1]], 0.4, MAT.dark(), s * 0.9 - 0.2, body, 0.01); }
  // cab: four posts, full glazing, white roof
  rbox(2.0, 1.7, 0.15, 0.04, MAT.yel(), -0.55, 0, 1.3, body);
  for (const [x, y] of [[-1.5, -0.8], [-1.5, 0.8], [0.4, -0.8], [0.4, 0.8]]) rbox(0.1, 0.1, 1.45, 0.03, MAT.dark(), x, y, 2.08, body);
  glassBox(1.85, 1.55, 1.38, -0.55, 0, 2.06, body);
  rbox(2.25, 1.9, 0.14, 0.06, MAT.white(), -0.55, 0, 2.86, body);
  rbox(0.5, 0.5, 0.15, 0.04, MAT.black(), -0.6, 0, 1.75, body); rbox(0.12, 0.5, 0.55, 0.04, MAT.black(), -0.85, 0, 2.05, body);
  cylZ(0.06, 0.1, MAT.amber(), -1.2, 0.6, 2.98, body, 12); lamp(body, 0.55, 0.7, 2.75, 0.06); lamp(body, 0.55, -0.7, 2.75, 0.06);
  // loader arms and bucket
  const la = new THREE.Group(); la.position.set(0.1, 0, 1.75); body.add(la);
  for (const s of [-1, 1]) side([[0, -0.1], [0.4, -0.12], [2.55, -0.9], [2.65, -0.7], [0.4, 0.15]], 0.14, MAT.yel(), s * 0.98 - 0.07, la, 0.02);
  rbox(0.18, 2.0, 0.18, 0.03, MAT.yel(), 1.9, 0, -0.65, la);
  const lb = new THREE.Group(); lb.position.set(2.6, 0, -0.85); la.add(lb);
  const lbp = []; for (let i = 0; i <= 8; i++) { const a = i / 8 * 1.6; lbp.push([0.25 + Math.sin(a) * 0.55, -0.45 + (1 - Math.cos(a)) * 0.55]); }
  side([[0.25, -0.45], [1.0, -0.5]].concat(lbp.reverse()).concat([[0.05, 0.25]]), 2.3, MAT.yel(), -1.15, lb, 0.03);
  rbox(0.08, 2.3, 0.06, 0.01, MAT.steel(), 1.0, 0, -0.48, lb);
  const rLift = [-1, 1].map(s => ram(body, body, [0.25, s * 0.85, 1.0], la, [1.3, s * 0.98, -0.42], 0.08, 0.05));
  // rear backhoe: stabilisers, swing post, boom, dipper, bucket
  const stab = [];
  for (const s of [-1, 1]) { const st = new THREE.Group(); st.position.set(-2.05, s * 0.95, 1.05); body.add(st); side([[0, 0], [0.2, 0], [0.15, -0.95], [-0.05, -0.95]], 0.18, MAT.yel(), -0.09, st, 0.02); rbox(0.45, 0.4, 0.06, 0.02, MAT.dark(), 0.05, 0, -0.98, st); st.rotation.x = s * 0.35; stab.push(st); }
  const post = new THREE.Group(); post.position.set(-2.2, 0, 1.15); body.add(post);
  rbox(0.35, 0.55, 0.65, 0.05, MAT.yel(), -0.15, 0, 0, post);
  const bm = new THREE.Group(); bm.position.set(-0.25, 0, 0.2); post.add(bm);
  side([[0.1, -0.12], [-1.0, 1.4], [-2.4, 1.85], [-2.5, 1.6], [-1.1, 1.05], [0.05, 0.18]], 0.36, MAT.yel(), -0.18, bm, 0.04);
  const dp = new THREE.Group(); dp.position.set(-2.45, 0, 1.72); bm.add(dp);
  side([[0.25, 0.15], [0.0, -0.1], [-0.05, -1.95], [0.15, -2.0], [0.3, -0.1]], 0.28, MAT.yel(), -0.14, dp, 0.03);
  const bk = new THREE.Group(); bk.position.set(0.05, 0, -1.95); dp.add(bk);
  const bkp = []; for (let i = 0; i <= 8; i++) { const a = i / 8 * 2.0; bkp.push([-Math.sin(a) * 0.4, -Math.cos(a) * 0.35]); }
  side(bkp.concat([[0.15, 0.1]]), 0.6, M(0x5c5c5e, { roughness: 0.6, metalness: 0.4 }), -0.3, bk, 0.02);
  const rBm = ram(body, post, [0.1, 0, 0.3], bm, [-1.0, 0, 1.3], 0.08, 0.05), rDp = ram(body, bm, [-1.0, 0, 1.6], dp, [0.25, 0, 0.12], 0.07, 0.045), rBk = ram(body, dp, [0.25, 0, -0.3], bk, [0.12, 0, 0.12], 0.06, 0.04);
  g.traverse(m => { if (m.isMesh) m.castShadow = true; });
  return { g, set(p) {
    const s = p.s || 0; wheels.forEach((w, i) => { w.rotation.y = s / (i % 2 ? 0.53 : 0.78); });
    la.rotation.y = -(p.lift ?? 0.0); lb.rotation.y = p.tip ?? 0.0;
    post.rotation.z = p.hoeSwing || 0; bm.rotation.y = p.hoeBoom ?? 0; dp.rotation.y = p.hoeDip ?? 0.3; bk.rotation.y = p.hoeBucket ?? 0.6;
    stab.forEach((st, i) => { st.rotation.x = (i ? 1 : -1) * (0.35 - 0.3 * (p.stab || 0)); });
    rLift.forEach(r => r.update()); rBm.update(); rDp.update(); rBk.update();
  } };
};

/* ---------- 4. all-terrain mobile crane (4 axles, telescopic boom, outriggers) ---------- */
V.mobileCrane = function () {
  const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  const wheels = [], stripe = stripes();
  for (const x of [-4.1, -2.5, 1.3, 2.9]) for (const s of [-1, 1]) wheels.push(wheel(0.72, 0.58, MAT.steel(), g, x, s * 1.12, 0.72, 0.05));
  rbox(11.2, 2.5, 0.8, 0.06, MAT.yel(), -0.6, 0, 1.55, body);                                                   // carrier deck
  rbox(11.2, 2.3, 0.35, 0.04, MAT.dark(), -0.6, 0, 1.05, body);
  for (const x of [-3.3, 2.1]) for (const s of [-1, 1]) side([[x - 1.15, 1.15], [x + 1.15, 1.15], [x + 1.15, 1.6], [x - 1.15, 1.6]], 0.12, MAT.yel(), s * 1.3 - 0.06, body, 0.02);
  // driver cab (front, right side)
  const cab = new THREE.Group(); cab.position.set(4.6, -0.35, 1.9); body.add(cab);
  side([[-0.4, 0], [1.25, 0], [1.4, 0.7], [1.2, 1.55], [-0.4, 1.55]], 1.75, MAT.yel(), -0.875, cab, 0.06);
  side([[-0.2, 0.75], [1.2, 0.75], [1.28, 0.78], [1.12, 1.45], [-0.2, 1.45]], 1.78, MAT.glass(), -0.89, cab, 0);
  rbox(0.2, 2.5, 0.5, 0.04, MAT.dark(), 5.8, 0, 1.4, body); lamp(body, 5.92, 0.95, 1.45, 0.1); lamp(body, 5.92, -0.95, 1.45, 0.1);
  rbox(0.05, 0.9, 0.5, 0.01, stripe, 5.92, 0, 1.45, body);
  // outriggers
  const outs = [];
  for (const x of [-5.4, 3.6]) for (const s of [-1, 1]) { const o = new THREE.Group(); o.position.set(x, s * 1.0, 1.55); body.add(o);
    rbox(0.35, 1.0, 0.3, 0.03, MAT.yel(), 0, s * 0.5, 0, o); rbox(0.36, 0.3, 0.32, 0.02, stripe, 0, s * 0.95, 0, o);
    const jack = cylZ(0.1, 1.3, MAT.chrome(), 0, s * 0.95, -0.7, o, 12); const pad = cylZ(0.35, 0.08, MAT.dark(), 0, s * 0.95, -1.5, o, 20); outs.push({ o, s, jack, pad }); }
  // superstructure: turntable, operator cab, counterweight, boom
  const sup = new THREE.Group(); sup.position.set(-2.4, 0, 1.95); body.add(sup);
  cylZ(1.2, 0.25, MAT.dark(), 0, 0, 0.12, sup, 32);
  rbox(4.2, 2.3, 0.9, 0.06, MAT.yel(), -0.6, 0, 0.7, sup); rbox(1.6, 2.4, 1.0, 0.08, M(0x3a3a3a, { roughness: 0.7 }), -2.4, 0, 0.75, sup);  // counterweight
  for (let k = 0; k < 4; k++) rbox(0.05, 2.42, 0.08, 0.01, stripe, -3.21, 0, 0.45 + k * 0.18, sup);
  const oc = new THREE.Group(); oc.position.set(0.6, 1.15, 0.3); sup.add(oc);
  side([[-0.6, 0], [0.9, 0], [1.05, 0.8], [0.8, 1.55], [-0.6, 1.55]], 0.85, MAT.yel(), -0.1, oc, 0.04);
  side([[-0.45, 0.55], [0.9, 0.55], [1.0, 0.82], [0.78, 1.45], [-0.45, 1.45]], 0.88, MAT.glass(), -0.12, oc, 0);
  const boom = new THREE.Group(); boom.position.set(-1.3, -0.15, 1.35); sup.add(boom);
  const secs = [];
  const sizes = [[9.6, 1.25, 1.05], [9.2, 1.05, 0.88], [8.8, 0.88, 0.72], [8.4, 0.72, 0.58]];
  let parent = boom;
  sizes.forEach(([L, w, h], i) => { const sg = new THREE.Group(); parent.add(sg); rbox(L, w, h, 0.12, i % 2 ? M(0xf6c22a, { roughness: 0.4 }) : MAT.yel(), L / 2, 0, 0, sg); secs.push({ sg, L }); parent = sg; });
  const head = new THREE.Group(); secs[3].sg.add(head); head.position.set(8.5, 0, 0);
  for (const dy of [-0.18, 0.18]) cylY(0.32, 0.1, MAT.dark(), 0.1, dy, -0.1, head, 20);
  const cable = mesh(new THREE.CylinderGeometry(0.025, 0.025, 1, 6), MAT.black(), 0, 0, 0, g);
  const hook = new THREE.Group(); g.add(hook);
  rbox(0.55, 0.45, 0.7, 0.05, stripe, 0, 0, 0, hook); cylY(0.22, 0.48, MAT.dark(), 0, 0, 0.15, hook, 16);
  const hk = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.045, 8, 16, Math.PI * 1.4), MAT.dark()); hk.rotation.x = Math.PI / 2; hk.position.z = -0.6; hook.add(hk); bar([0, 0, -0.35], [0, 0, -0.45], 0.05, MAT.dark(), hook);
  const luff = new THREE.Group(); sup.add(luff);
  const rLuff = ram(sup, sup, [0.9, -0.15, 0.6], secs[0].sg, [4.0, 0, -0.5], 0.2, 0.13);
  g.traverse(m => { if (m.isMesh) m.castShadow = true; });
  const tip = new THREE.Vector3(), inv = new THREE.Matrix4();
  return { g, hook, set(p) {
    const s = p.s || 0; wheels.forEach(w => { w.rotation.y = s / 0.72; });
    const ex = p.extend ?? 0, out = p.outrig ?? 0;
    outs.forEach(({ o, s: sd, jack, pad }) => { o.children[0].position.y = sd * (0.5 + out * 1.6); o.children[1].position.y = sd * (0.95 + out * 1.6); jack.position.y = pad.position.y = sd * (0.95 + out * 1.6); jack.position.z = -0.7 - out * 0.15; pad.position.z = -1.5 + (1 - out) * 0.9; });
    body.position.z = out * 0.12;
    sup.rotation.z = p.slew || 0; boom.rotation.y = -(p.luff ?? 0.05);
    for (let i = 1; i < 4; i++) secs[i].sg.position.x = 0.6 + ex * (secs[i - 1].L - 1.6) * (i === 1 ? 1 : ex > 0 ? 1 : 0);
    rLuff.update();
    g.updateMatrixWorld(true); inv.copy(g.matrixWorld).invert(); tip.set(0.1, 0, -0.1).applyMatrix4(head.matrixWorld).applyMatrix4(inv);
    const drop = p.hookDrop ?? 3; hook.position.set(tip.x, tip.y, Math.max(0.6, tip.z - drop)); hook.rotation.z = p.slew || 0;
    cable.position.set(tip.x, tip.y, (tip.z + hook.position.z + 0.35) / 2); cable.scale.y = Math.max(0.01, tip.z - hook.position.z - 0.35);
  } };
};

/* ---------- 5. army pickup (4x4 double/single cab, roll cage, troops in the bed) ---------- */
V.pickup = function (troops = 4) {
  const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  const wheels = [], col = MAT.olive();
  for (const x of [-1.6, 1.45]) for (const s of [-1, 1]) wheels.push(wheel(0.39, 0.27, MAT.oliveD(), g, x, s * 0.78, 0.39, 0.03));
  side([[-2.6, 0.45], [2.55, 0.45], [2.65, 0.62], [2.6, 0.95], [2.15, 1.08], [1.0, 1.14], [-2.6, 1.14]], 1.8, col, -0.9, body, 0.06);    // lower body
  for (const x of [-1.6, 1.45]) for (const s of [-1, 1]) { const arch = new THREE.Mesh(new THREE.TorusGeometry(0.47, 0.06, 6, 18, Math.PI), MAT.oliveD()); arch.rotation.x = Math.PI / 2; arch.position.set(x, s * 0.9, 0.42); body.add(arch); }
  // cab
  side([[-0.55, 1.1], [1.0, 1.1], [0.55, 1.78], [-0.45, 1.82]], 1.7, col, -0.85, body, 0.06);
  side([[-0.45, 1.22], [0.93, 1.18], [0.52, 1.72], [-0.38, 1.74]], 1.72, MAT.glass(), -0.86, body, 0);
  rbox(0.06, 1.72, 0.08, 0.01, col, 0.05, 0, 1.45, body);          // B-pillar shadow line
  rbox(0.08, 1.4, 0.24, 0.02, MAT.black(), 2.62, 0, 0.8, body);    // grille
  for (let k = 0; k < 4; k++) rbox(0.02, 1.3, 0.025, 0.005, M(0x2a2a2a), 2.67, 0, 0.72 + k * 0.05, body);
  rbox(0.2, 1.84, 0.16, 0.03, MAT.black(), 2.66, 0, 0.5, body);    // bumper
  lamp(body, 2.63, 0.62, 0.86, 0.075); lamp(body, 2.63, -0.62, 0.86, 0.075);
  for (const s of [-1, 1]) { rbox(0.1, 0.05, 0.08, 0.01, MAT.tail(), -2.62, s * 0.78, 0.95, body); rbox(0.08, 0.18, 0.12, 0.02, MAT.black(), 0.85, s * 0.98, 1.45, body); }
  rbox(0.05, 0.36, 0.1, 0.01, MAT.white(), 2.7, 0, 0.5, body);    // number plate
  // bed with sides and roll cage
  rbox(3.0, 1.62, 0.06, 0.01, MAT.oliveD(), -1.12, 0, 1.12, body);
  for (const [x, y, w, d] of [[-1.12, 0.79, 3.05, 0.06], [-1.12, -0.79, 3.05, 0.06], [-2.6, 0, 0.06, 1.64]]) rbox(w, d, 0.42, 0.01, col, x, y, 1.35, body);
  for (const x of [-0.75, -2.45]) { bar([x, 0.78, 1.55], [x, 0.78, 2.35], 0.035, MAT.black(), body); bar([x, -0.78, 1.55], [x, -0.78, 2.35], 0.035, MAT.black(), body); bar([x, -0.78, 2.35], [x, 0.78, 2.35], 0.035, MAT.black(), body); }
  bar([-0.75, 0.78, 2.35], [-2.45, 0.78, 2.35], 0.03, MAT.black(), body); bar([-0.75, -0.78, 2.35], [-2.45, -0.78, 2.35], 0.03, MAT.black(), body);
  rbox(2.4, 0.28, 0.06, 0.01, MAT.oliveD(), -1.55, 0, 1.45, body);         // centre bench
  bar([0.3, 0.7, 1.8], [0.2, 0.7, 2.9], 0.012, MAT.black(), body);        // antenna
  const men = [];
  for (let i = 0; i < troops; i++) { const sd = i % 2 ? 1 : -1, x = -1.0 - Math.floor(i / 2) * 0.85; const pp = person({ uniform: 'soldier', seated: true, rifle: true }); pp.g.position.set(x, sd * 0.25, 1.1); pp.g.rotation.z = sd * Math.PI / 2; body.add(pp.g); men.push(pp); }
  const drv = person({ uniform: 'soldier', seated: true }); drv.g.position.set(0.25, 0.42, 0.75); drv.g.scale.setScalar(0.95); body.add(drv.g);
  g.traverse(m => { if (m.isMesh) m.castShadow = true; });
  return { g, set(p) { const s = p.s || 0; wheels.forEach(w => { w.rotation.y = s / 0.39; }); body.position.z = Math.sin(s * 2.3) * 0.015; body.rotation.y = Math.sin(s * 1.3) * 0.006; } };
};

/* ---------- 6. 6x6 MRAP (V-hull, armoured windows, roof turret) ---------- */
V.mrap = function () {
  const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  const col = MAT.tan(), colD = MAT.tanD(), wheels = [];
  for (const x of [2.35, -0.95, -2.45]) for (const s of [-1, 1]) wheels.push(wheel(0.62, 0.42, colD, g, x, s * 1.05, 0.62, 0.05));
  // V-hull and lower body
  side([[-3.4, 0.75], [3.0, 0.75], [3.5, 1.05], [3.55, 1.55], [-3.4, 1.55]], 2.3, col, -1.15, body, 0.05);
  rbox(5.6, 1.2, 0.5, 0.05, colD, -0.3, 0, 0.62, body);
  // armoured hood with vertical-slat grille
  side([[2.0, 1.5], [3.55, 1.5], [3.5, 2.15], [2.0, 2.3]], 2.2, col, -1.1, body, 0.05);
  for (let k = 0; k < 11; k++) rbox(0.04, 0.05, 0.6, 0.01, MAT.black(), 3.56, -0.75 + k * 0.15, 1.82, body);
  rbox(0.06, 1.7, 0.66, 0.02, colD, 3.55, 0, 1.82, body);
  for (const s of [-1, 1]) { lamp(body, 3.55, s * 0.95, 1.95, 0.08); rbox(0.25, 0.6, 0.12, 0.02, colD, 3.4, s * 0.95, 1.35, body); }
  rbox(0.3, 2.6, 0.35, 0.04, colD, 3.6, 0, 1.0, body);           // bumper
  // crew cabin: angled sides, flat roof
  const cabPts = [[-3.45, 1.5], [2.05, 1.5], [2.4, 2.3], [2.15, 3.05], [-3.45, 3.05]];
  const cabin = side(cabPts, 2.45, col, -1.225, body, 0.06);
  // windows (dark armoured glass with thick frames)
  const win = (x, y, w, h, z, rot) => { const f = rbox(w + 0.1, 0.06, h + 0.1, 0.02, colD, x, y, z, body); const gl = rbox(w, 0.07, h, 0.01, M(0x1a252c, { roughness: 0.05, metalness: 0.4, envMapIntensity: 1.8 }), x, y, z, body); if (rot) { f.rotation.z = rot; gl.rotation.z = rot; } };
  for (const s of [-1, 1]) { win(1.45, s * 1.24, 0.9, 0.62, 2.55); win(0.2, s * 1.24, 0.7, 0.55, 2.6); win(-1.0, s * 1.24, 0.6, 0.5, 2.62); win(-2.3, s * 1.24, 0.6, 0.5, 2.62); }
  const ws = new THREE.Group(); ws.position.set(2.3, 0, 2.65); ws.rotation.y = -0.33; body.add(ws);
  for (const s of [-1, 1]) { rbox(0.06, 0.95, 0.7, 0.02, colD, 0, s * 0.55, 0, ws); rbox(0.07, 0.85, 0.6, 0.01, M(0x1a252c, { roughness: 0.05, metalness: 0.4, envMapIntensity: 1.8 }), 0.01, s * 0.55, 0, ws); }
  // doors outlines, hinges, side boxes, spare tyre, rear door
  for (const s of [-1, 1]) { for (const x of [1.5, 0.2]) rbox(1.05, 0.03, 1.4, 0.01, colD, x, s * 1.235, 2.25, body); rbox(1.4, 0.4, 0.55, 0.04, colD, -1.6, s * 1.32, 1.3, body); }
  const sp = wheel(0.6, 0.38, colD, body, -1.45, -1.52, 2.25, 0.05); sp.rotation.x = 0;
  rbox(0.06, 1.3, 1.5, 0.02, colD, -3.48, 0, 2.2, body); rbox(0.05, 0.4, 0.4, 0.01, M(0x1a252c, { roughness: 0.05, metalness: 0.4 }), -3.5, 0, 2.6, body);
  for (const s of [-1, 1]) { rbox(0.06, 0.12, 0.1, 0.01, MAT.tail(), -3.5, s * 1.0, 1.4, body); rbox(0.2, 0.08, 0.35, 0.02, MAT.black(), 2.05, s * 1.35, 2.85, body); }
  // roof: hatches, turret ring with gunner shield and MG, antennas
  rbox(5.2, 2.2, 0.1, 0.03, colD, -0.6, 0, 3.08, body);
  const tur = new THREE.Group(); tur.position.set(-0.6, 0, 3.12); body.add(tur);
  cylZ(0.75, 0.22, colD, 0, 0, 0.11, tur, 28);
  for (let k = 0; k < 5; k++) { const a = -0.9 + k * 0.45; const p = rbox(0.06, 0.62, 0.75, 0.02, col, Math.cos(a) * 0.78, Math.sin(a) * 0.78, 0.55, tur); p.rotation.z = a; }
  rbox(0.9, 0.08, 0.08, 0.01, MAT.black(), 0.95, 0, 0.62, tur); cylX(0.025, 0.7, MAT.black(), 1.6, 0, 0.64, tur, 8); rbox(0.25, 0.15, 0.18, 0.02, MAT.black(), 0.55, 0, 0.6, tur);
  const gun = person({ uniform: 'soldier' }); gun.g.position.set(-0.1, 0, -0.85); tur.add(gun.g); gun.walk(0, 0);
  for (const [x, y, h] of [[-2.8, 1.0, 2.6], [-2.8, -1.0, 2.2], [1.6, 1.0, 1.6]]) { bar([x, y, 3.1], [x, y, 3.1 + h], 0.012, MAT.black(), body); }
  g.traverse(m => { if (m.isMesh) m.castShadow = true; });
  return { g, tur, set(p) { const s = p.s || 0; wheels.forEach(w => { w.rotation.y = s / 0.62; }); body.position.z = Math.sin(s * 1.9) * 0.02; body.rotation.y = Math.sin(s * 1.1) * 0.008; tur.rotation.z = p.turret || 0; } };
};

/* ---------- 7. army 4x4 truck (canvas cargo body or GCS shelter with mast) ---------- */
V.armyTruck = function (shelter) {
  const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  const col = MAT.olive(), wheels = [];
  for (const x of [2.2, -1.5]) for (const s of [-1, 1]) wheels.push(wheel(0.55, 0.38, MAT.oliveD(), g, x, s * 0.95, 0.55, 0.045));
  rbox(6.6, 1.0, 0.3, 0.03, MAT.dark(), 0.2, 0, 0.85, body);
  side([[2.0, 1.0], [3.45, 1.0], [3.5, 1.7], [3.15, 1.95], [2.0, 2.0]], 1.9, col, -0.95, body, 0.05);      // bonnet
  for (let k = 0; k < 6; k++) rbox(0.03, 1.1, 0.04, 0.01, MAT.black(), 3.51, 0, 1.2 + k * 0.08, body);
  side([[0.9, 1.0], [2.15, 1.0], [2.25, 2.0], [2.1, 2.85], [0.9, 2.85]], 2.25, col, -1.125, body, 0.05);  // cab
  side([[1.0, 2.05], [2.18, 2.05], [2.1, 2.72], [1.0, 2.72]], 2.28, MAT.glass(), -1.14, body, 0);
  rbox(0.18, 2.35, 0.25, 0.03, MAT.black(), 3.55, 0, 0.85, body); lamp(body, 3.5, 0.75, 1.55, 0.09); lamp(body, 3.5, -0.75, 1.55, 0.09);
  for (const x of [2.2, -1.5]) for (const s of [-1, 1]) { const arch = new THREE.Mesh(new THREE.TorusGeometry(0.66, 0.06, 6, 18, Math.PI), MAT.oliveD()); arch.rotation.x = Math.PI / 2; arch.position.set(x, s * 1.12, 0.62); body.add(arch); }
  if (shelter) {
    rbox(3.9, 2.35, 2.15, 0.06, col, -1.35, 0, 2.2, body); rbox(0.05, 0.9, 1.8, 0.01, MAT.oliveD(), -3.31, 0.4, 2.1, body);
    for (const y of [-0.5, 0.5]) rbox(0.6, 0.05, 0.4, 0.01, MAT.oliveD(), -1.0, y > 0 ? 1.18 : -1.18, 2.6, body);
    cylZ(0.08, 3.5, MAT.dark(), -3.0, -0.95, 4.0, body, 10); cylZ(0.05, 2.5, MAT.dark(), -3.0, -0.95, 6.8, body, 10);
    const dish = new THREE.Mesh(new THREE.SphereGeometry(0.45, 20, 10, 0, Math.PI * 2, 0, 0.7), MAT.white()); dish.position.set(-3.0, -0.95, 8.1); dish.rotation.x = -1.2; body.add(dish);
    rbox(0.6, 0.4, 0.5, 0.03, MAT.dark(), -0.2, 0.8, 3.45, body); bar([-2.4, 0.7, 3.3], [-2.4, 0.7, 5.6], 0.015, MAT.black(), body);
  } else {
    rbox(3.9, 2.35, 0.65, 0.03, col, -1.35, 0, 1.4, body);
    const sh = new THREE.Shape(); sh.moveTo(-1.18, 0); sh.lineTo(1.18, 0); sh.lineTo(1.18, 0.95);
    for (let i = 0; i <= 14; i++) { const a = i / 14 * Math.PI; sh.lineTo(Math.cos(a) * 1.18, 0.95 + Math.sin(a) * 0.4); }
    const cg = new THREE.ExtrudeGeometry(sh, { depth: 3.85, bevelEnabled: true, bevelSize: 0.03, bevelThickness: 0.03, bevelSegments: 1, curveSegments: 12 });
    cg.applyMatrix4(new THREE.Matrix4().set(0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1)); cg.translate(-3.27, 0, 1.72);
    mesh(cg, MAT.canvas(), 0, 0, 0, body);
    for (let k = 0; k < 5; k++) rbox(0.05, 2.42, 0.05, 0.01, MAT.oliveD(), -3.2 + k * 0.92, 0, 3.08, body);
  }
  g.traverse(m => { if (m.isMesh) m.castShadow = true; });
  return { g, set(p) { const s = p.s || 0; wheels.forEach(w => { w.rotation.y = s / 0.55; }); body.position.z = Math.sin(s * 1.6) * 0.012; } };
};

/* ---------- path follower: place a vehicle along a polyline [[x,y],...] at distance d ---------- */
V.along = function (pts) {
  const seg = []; let L = 0;
  for (let i = 0; i < pts.length - 1; i++) { const l = Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]); seg.push([pts[i], pts[i + 1], l, L]); L += l; }
  return { L, at(d) { d = Math.max(0, Math.min(L - 1e-6, d)); let k = 0; while (k < seg.length - 1 && seg[k][3] + seg[k][2] < d) k++; const [a, b, l, s0] = seg[k], u = (d - s0) / l;
    const x = a[0] + (b[0] - a[0]) * u, y = a[1] + (b[1] - a[1]) * u; let h = Math.atan2(b[1] - a[1], b[0] - a[0]);
    if (k < seg.length - 1 && u > 0.7) { const [c, e] = seg[k + 1]; const h2 = Math.atan2(e[1] - c[1], e[0] - c[0]); let dh = h2 - h; while (dh > Math.PI) dh -= 2 * Math.PI; while (dh < -Math.PI) dh += 2 * Math.PI; h += dh * (u - 0.7) / 0.6; }
    if (k > 0 && u < 0.3) { const [c, e] = seg[k - 1]; const h0 = Math.atan2(e[1] - c[1], e[0] - c[0]); let dh = h - h0; while (dh > Math.PI) dh -= 2 * Math.PI; while (dh < -Math.PI) dh += 2 * Math.PI; h -= dh * (0.3 - u) / 0.6; }
    return [x, y, h]; } };
};
window.VEH = V;
})();
