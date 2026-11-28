// DRONE TRG COMPLEX - 44 DIV : proposal video timeline v4 (30 fps, 0.5 s crossfades, 4K).
// Each clip returns the full renderer state for a local time t (seconds). ENU metres; label offsets in px.
const XF = 0.5;
const SLOW = 1 / 0.75;                 // interior shots at 0.75x speed
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const ease = x => { x = clamp(x); return x * x * (3 - 2 * x); };
const easeIO = x => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const ramp = (t, a, b) => ease((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
function cr(p0, p1, p2, p3, t) { const t2 = t * t, t3 = t2 * t; return p1.map((_, i) => 0.5 * (2 * p1[i] + (-p0[i] + p2[i]) * t + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t2 + (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t3)); }
function path(keys, u) { if (keys.length === 1) return keys[0]; const n = keys.length - 1, x = Math.min(u * n, n - 1e-9), i = Math.floor(x); return cr(keys[Math.max(i - 1, 0)], keys[i], keys[i + 1], keys[Math.min(i + 2, n)], x - i); }
const orbitPt = (r, h, deg, c = [0, 0]) => [c[0] + Math.cos(deg * Math.PI / 180) * r, c[1] + Math.sin(deg * Math.PI / 180) * r, h];
const lab = (id, t, s, p, t0, o, extra) => ({ id, t, s, p, t0, o: o || [0, -70], ...(extra || {}) });
function labels(list, t, dur) { return list.filter(L => t >= L.t0 - 0.01).map(L => ({ ...L, a: Math.min(ramp(t, L.t0, L.t0 + 0.5), 1 - ramp(t, dur - 0.55, dur - 0.15)) })); }
const hdr = (k, v, t) => ({ k, v, a: ramp(t, 0.2, 0.8) });
function kf(keys, t) { if (t <= keys[0][0]) return keys[0][1]; for (let i = 1; i < keys.length; i++) if (t <= keys[i][0]) { const [a, va] = keys[i - 1], [b, vb] = keys[i], k = (t - a) / (b - a), e = k * k * (3 - 2 * k); return va + (vb - va) * e; } return keys[keys.length - 1][1]; }
// sun position from local solar hour (GR latitude 25.3 N, late November: noon elevation ~ 44 deg)
function sunAt(hour) { const h = ((hour % 24) + 24) % 24, a = (h - 12) / 12 * Math.PI; const el = Math.asin(Math.sin(25.3 * Math.PI / 180) * Math.sin(-21 * Math.PI / 180) + Math.cos(25.3 * Math.PI / 180) * Math.cos(-21 * Math.PI / 180) * Math.cos(a)) * 180 / Math.PI;
  const az = 180 + Math.atan2(Math.sin(a), Math.cos(a) * Math.sin(25.3 * Math.PI / 180) - Math.tan(-21 * Math.PI / 180) * Math.cos(25.3 * Math.PI / 180)) * 180 / Math.PI; return [az, el]; }
const CARD = { title: 'PROPOSAL DRONE TRG COMPLEX - 44 DIV', sub: '23 Engineer Battalion Kashmir Sappers' };

const EMPTY = { pad: 0, land: 0, core: 0, interior: 0, road: 0, finish: -1, hShell: 0, hRoof: 0, hCol: 0, foot: 0, crane: 0, beam: 0, scaf: 0, shutter: 0, plant: 0, chalk: 0 };
const GR = 'GR 25°19\'47.62"N   62°30\'33.00"E';
const TW = { NE: { c: [16.42, 10.42], phi: Math.PI / 4 }, NW: { c: [-16.42, 10.42], phi: 3 * Math.PI / 4 },
             SW: { c: [-16.42, -10.42], phi: -3 * Math.PI / 4 }, SE: { c: [16.42, -10.42], phi: -Math.PI / 4 } };
const RI = 3.2, F = 0.3;
const inT = (k, dist, da, z) => { const w = TW[k]; return [w.c[0] + Math.cos(w.phi + da) * dist, w.c[1] + Math.sin(w.phi + da) * dist, z]; };

// interior walk-through of one rotor-tower room: stand inside the doorway, pan across the room
function towerShot(k, dur, title, sub, items) {
  // eye-level: stand just inside the doorway (hall side), slow pan across the room
  return t => {
    const u = easeIO(t / dur), w = TW[k], back = w.phi + Math.PI;
    const eye = [w.c[0] + Math.cos(back) * 2.45, w.c[1] + Math.sin(back) * 2.45, 1.62];
    const yaw = w.phi + lerp(-0.62, 0.62, u);
    const look = [eye[0] + Math.cos(yaw) * 5, eye[1] + Math.sin(yaw) * 5, lerp(1.25, 1.35, u)];
    return { eye, look, fov: 80, near: 0.05, interior: 1, tower: k, shadowR: 12, shadowAt: [w.c[0], w.c[1], 1], hdr: hdr(title, sub, t),
             labels: labels(items.map(([id, tt, s, da, dist, z, t0, o]) => lab(id, tt, s, inT(k, dist, da, z), t0, o, { occ: false })), t, dur) };
  };
}

const DAY = { sun: [219.9, 32.3] };
const CON_PH = [[0, 2.8, 'SITE CLEARANCE & SETTING OUT', 'Grubbing and clearance · compound 110 m × 92 m and building lines set out from the GR'],
                [2.8, 6.6, 'EARTHWORK', 'Cut ≈ 7,500 m³ · fill ≈ 5,000 m³ · compacted in 200 mm layers to 95 % MDD (Modified AASHTO)'],
                [6.6, 9.8, 'FOUNDATIONS & PLINTH', 'PCC 1:4:8 blinding · RCC 4000 psi footings & plinth beam · bitumen + APP membrane, anti-termite (coastal saline zone)'],
                [9.8, 13.8, 'RCC FRAME', 'Rebar cages lifted by mobile crane · column formwork · RCC 4000 psi columns & ring beams · Grade 60 steel'],
                [13.8, 17.4, 'MASONRY & ROTOR TOWERS', 'Stone masonry in CM 1:4 from scaffolding · four rotor-tower drums with RCC ring beams'],
                [17.4, 19.8, 'ROOF SLAB', 'Shuttering and top/bottom rebar mesh · RCC slab poured · insulation + waterproofing'],
                [19.8, 22.4, 'DRONE CORE, GLASS DOME & ROTOR PODS', 'Steel-framed glass dome · composite arms · motor housings and 11 m propellers lifted into place'],
                [22.4, 27.5, 'FINISHES, SERVICES & LANDSCAPING', 'Weather-shield paint · tiles & terrazzo · E&M services · roads, lawns and flying field']];
const CS = 27.5;
// time-lapse clock and weather: two nights, a dust storm and a rain shower
const HOUR = [[0, 8.5], [4.4, 17.3], [5.6, 19.2], [8.4, 28.6], [9.6, 31.0], [18.4, 41.2], [19.6, 43.4], [21.6, 52.4], [22.6, 54.9], [27.75, 61.5]];
const CLOUD = [[0, 0.12], [9.6, 0.2], [10.6, 0.55], [13.0, 0.55], [14.6, 0.4], [15.4, 0.92], [17.8, 0.92], [18.6, 0.3], [23, 0.15], [27.75, 0.12]];
const DUST = [[0, 0], [10.4, 0], [11.2, 0.85], [12.4, 0.85], [13.3, 0]];
const RAIN = [[0, 0], [15.4, 0], [15.9, 0.95], [17.4, 0.95], [18.0, 0]];
const WET = [[0, 0], [15.6, 0], [16.6, 1], [18.5, 1], [21.0, 0.25], [24, 0]];
const titleCard = (t, a0) => ({ ban: ramp(t, a0, a0 + 0.8), logo: ramp(t, a0 + 0.4, a0 + 1.6), title: ramp(t, a0 + 1.1, a0 + 2.3), rule: ramp(t, a0 + 1.9, a0 + 2.9), subA: ramp(t, a0 + 2.4, a0 + 3.4), ...CARD });

const CLIPS = [
  { name: 'title', dur: 6.5, fn: t => ({
      eye: path([[-1100, -1500, 950], [-980, -1330, 860]], t / 6.5), look: [0, 0, 0], fov: 45, near: 2, build: EMPTY, rpm: 0, shadowR: 200, ao: false, card: titleCard(t, 0.2) }) },
  { name: 'site_location', dur: 10.0, fn: t => {
      const u = easeIO(t / 10);
      const L = [lab('pin', 'Proposed site', 'Drone Trg Complex - 44 Div', [0, 0, 8], 1.0, [90, -90]),
                 lab('road', 'Existing metalled road', null, [-407, 560, 0], 3.4, [-40, -60]),
                 lab('appr', 'Proposed approach road', '≈ 410 m to site', [-230, 61, 0.5], 5.4, [-60, 70]),
                 lab('area', 'Demarcated area', '110 m × 92 m  (≈ 1.01 ha)', [55, 52, 1], 6.6, [110, -70]),
                 lab('mtn', 'Hill ranges to the north', 'up to ≈ 950 m', [-2500, 14500, 1400], 7.2, [0, -60], { occ: false }),
                 lab('lvl', 'Ground level 23.8 m', 'Mean slope 2° · relief 5.7 m within 100 m', [55, -40, 1], 7.8, [120, 60])];
      return { eye: path([[-2600, -9600, 10500], [-1300, -4300, 4200], [-420, -1300, 1050], [-150, -330, 190]], u), look: path([[0, 0, 0], [0, 600, 0], [0, 900, 120], [0, 300, 40]], u), fov: 45, near: t < 6 ? 6 : 0.5,
               build: { ...EMPTY, road: 1 }, demarc: 1, rpm: 0, shadowR: 160, north: 1, hdr: hdr('SITE LOCATION', GR, t), labels: labels(L, t, 10) }; } },
  { name: 'construction', dur: 28.0, fn: t => {
      const s = clamp(t - 0.25, 0, CS);
      let pi = CON_PH.findIndex(p => s < p[1]); if (pi < 0) pi = CON_PH.length - 1;
      const p = CON_PH[pi], last = pi === CON_PH.length - 1, pu = clamp((s - p[0]) / (p[1] - p[0]));
      const capA = Math.min(ramp(s, p[0], p[0] + 0.3), last ? 1 : 1 - ramp(s, p[1] - 0.22, p[1]));
      const P = k => CON_PH[k][0], Q = k => CON_PH[k][1];
      const b = { chalk: s < P(2) + 0.6 ? 1 : 0, plant: 1, pad: ramp(s, P(1), Q(1)), foot: ramp(s, P(2) + 0.6, Q(2) - 0.4),
                  hShell: s < Q(2) - 0.4 ? 0 : s < P(4) ? lerp(0.01, 0.3, ramp(s, Q(2) - 0.4, Q(2) + 0.8)) : lerp(0.3, 7.6, ramp(s, P(4), Q(4))),
                  hCol: s > P(3) ? lerp(0.3, 7.45, ramp(s, P(3) + 0.6, Q(3) - 0.6)) : 0, beam: ramp(s, Q(3) - 0.8, Q(3)),
                  scaf: s < P(7) ? ramp(s, P(4) - 0.2, P(4) + 0.6) : 1 - ramp(s, P(7), P(7) + 0.7), shutter: s > P(5) && s < Q(5) ? (s > P(5) + 0.5 ? 1 : 0.2) : 0,
                  hRoof: lerp(5.3, 6.75, ramp(s, P(5) + 0.4, Q(5))), core: ramp(s, P(6) + 0.3, Q(6)), finish: lerp(-0.5, 12, ramp(s, P(7) + 0.2, P(7) + 3.0)),
                  land: ramp(s, P(7) + 0.5, Q(7) - 0.6), interior: s > P(7) ? 1 : 0, road: s > P(7) + 0.4 ? 1 : 0 };
      const u = easeIO(t / 28);
      const hour = kf(HOUR, t), sun = sunAt(hour);
      return { eye: orbitPt(lerp(96, 66, u), lerp(52, 26, u), lerp(-150, -38, u)), look: [0, lerp(-4, 4, u), 3], fov: 44, build: b, site: { s, ph: pi, u: pu },
               demarc: s < P(1) + 0.4 ? 1 : 0, dust: s > P(1) && s < Q(1) ? 1 : 0, rpm: lerp(0, 80, ramp(s, P(7), P(7) + 1.5)), shadowR: 105, shadowAt: [0, 0, 0],
               env: { sun, moon: [150, 48], cloud: kf(CLOUD, t), dust: kf(DUST, t), rain: kf(RAIN, t), wet: kf(WET, t), skySpeed: 7, wind: 1.4, windows: s > P(7) ? 1 : 0 },
               hdr: hdr('CONSTRUCTION SEQUENCE', 'Time-lapse  ·  day and night, all weather', t),
               prog: { month: clamp(s / CS) * 12 * 0.999, phase: pi, a: ramp(t, 0.3, 0.9) },
               cap: { n: String(pi + 1), h: p[2], d: p[3], a: capA } }; } },
  { name: 'night_reveal', dur: 10.0, fn: t => {
      const u = easeIO(t / 10);
      return { eye: path([[60, 58, 5.5], [24, 66, 9], [-26, 62, 13], [-54, 40, 16]], u), look: path([[4, 6, 6], [0, 4, 6.5], [-2, 2, 6.5], [-4, 0, 6]], u), fov: 42, shadowR: 90, shadowAt: [0, 0, 0],
               env: { sun: [250, -32], moon: [215, 24], cloud: 0.12, skySpeed: 0.4, exposure: 1.05 }, rpm: 60,
               hdr: hdr('NIGHT VIEW', 'Under moonlight  ·  facade and site lighting', t) }; } },
  { name: 'scope_of_work', dur: 8.0, fn: t => {
      const u = easeIO(t / 8);
      const rows = [['MAIN BUILDING', null], ['Covered area (incl. rotor towers)', '932 m²'], ['Lecture hall — 100 seats, stage', '302 m²'],
                    ['Simulator complex — 8 stations', '279 m²'], ['Foyer & reception', '158 m²'], ['Office (NE tower)', '≈ 22 m²'],
                    ['Community washrooms × 3 (NW tower)', '≈ 22 m²'], ['Drone & equipment store (SE tower)', '≈ 22 m²'],
                    ['Battery charging & maint room (SW tower)', '≈ 22 m²'], ['Glass dome (steel frame) over drone core', 'Ø 9.2 m'], ['SITE', null], ['Demarcated plot', '110 × 92 m · 1.01 ha'],
                    ['Drone flying field — 2 pads, 4 race gates', '25 × 56 m'], ['GCS vehicle bay · comms mast 18 m', '—'],
                    ['Parking', '6 bays'], ['Boundary wall with main gate', '404 m'], ['Approach road (8 m wide)', '410 m']];
      const th = lerp(-125, -85, u) * Math.PI / 180, c = orbitPt(lerp(84, 74, u), lerp(32, 26, u), th * 180 / Math.PI);
      const rx = -Math.sin(th) * 17, ry = Math.cos(th) * 17;
      return { eye: [c[0] + rx, c[1] + ry, c[2]], look: [rx, ry, 4], fov: 42, shadowR: 90, env: { sun: [205, 40] },
               hdr: hdr('SCOPE OF WORK', 'Drone Trg Complex - 44 Div', t), scope: { rows, a: ramp(t, 0.3, 1.0), rowsA: ramp(t, 0.6, 4.2) } }; } },
  { name: 'fly_exterior', dur: 8.0, fn: t => {
      const u = easeIO(t / 8);
      const L = [lab('ne', 'Office', null, [16.42, 10.42, 10.6], 0.6, [110, -60], { occ: false }), lab('nw', 'Community washrooms × 3', null, [-16.42, 10.42, 9.6], 1.0, [-110, -60]),
                 lab('ent', 'Main entrance', null, [0, 16.8, 0.6], 1.6, [0, 90]), lab('dome', 'Glass dome', 'steel frame · Ø 9.2 m', [0, 0, 10.6], 2.2, [0, -150], { occ: false }),
                 lab('se', 'Drone & equipment store', null, [16.42, -10.42, 10.6], 3.0, [140, -40], { occ: false }), lab('sw', 'Battery charging & maint room', null, [-16.42, -10.42, 10.6], 3.4, [-150, -40], { occ: false })];
      return { eye: orbitPt(lerp(64, 50, u), lerp(24, 13, u), lerp(128, 62, u)), look: [0, 1, 6], fov: 46, shadowR: 85, convoy: lerp(0.86, 0.995, ramp(t, 0, 7.6)),
               hdr: hdr('FLY-THROUGH', 'Rotor towers, glass dome & main entrance', t), labels: labels(L, t, 8) }; } },
  { name: 'fly_field', dur: 5.0, fn: t => {
      const u = easeIO(t / 5);
      const L = [lab('fld', 'Drone flying field', '25 m × 56 m', [39.5, -14, 0.2], 0.4, [-120, 80]), lab('gate', 'Race gates × 4', null, [45, 0, 3.0], 0.9, [90, -90]),
                 lab('pad', 'Landing pads × 2', null, [45.5, -30, 0.3], 1.3, [110, 50]), lab('gcs', 'Ground control station', 'army shelter vehicle', [22.5, -31.5, 4.2], 1.8, [-90, -80]),
                 lab('sock', 'Windsock', null, [51.3, 17.5, 5.9], 2.4, [90, -50]), lab('mast', 'Comms mast 18 m', null, [48, 40, 17.5], 2.8, [100, 40])];
      return { eye: path([[66, -54, 11], [65, -16, 10], [60, 16, 13]], u), look: path([[38, -26, 1], [37, -6, 2], [34, 6, 4]], u), fov: 52, shadowR: 60,
               hdr: hdr('FLY-THROUGH', 'Drone flying field', t), labels: labels(L, t, 5) }; } },
  { name: 'fly_cutaway', dur: 6.0, fn: t => {
      const u = easeIO(t / 6), o = { occ: false };
      const L = [lab('lh', 'Lecture hall', '100 students', [-9, 0, 2], 0.5, [0, -60], o), lab('sc', 'Simulator complex', '8 pilot stations', [11, 0, 2], 0.8, [0, -60], o),
                 lab('fy', 'Foyer & reception', null, [0.5, 4, 1.5], 1.1, [0, 70], o), lab('ne2', 'Office', null, [16.42, 10.42, 1.5], 1.4, [70, -40], o),
                 lab('nw2', 'Washrooms × 3', null, [-16.42, 10.42, 1.5], 1.6, [-70, -40], o), lab('se2', 'Store', null, [16.42, -10.42, 1.5], 1.8, [70, 40], o),
                 lab('sw2', 'Battery room', null, [-16.42, -10.42, 1.5], 2.0, [-70, 40], o)];
      return { eye: orbitPt(lerp(40, 34, u), lerp(46, 40, u), lerp(-112, -72, u)), look: [0, 0, 0], fov: 44, noRoof: 1, interior: 1, shadowR: 45, env: { sun: [200, 52] },
               hdr: hdr('LAYOUT', 'Roof removed', t), labels: labels(L, t, 6) }; } },
  { name: 'foyer', dur: 3.5 * SLOW, fn: t => {
      const D = 3.5 * SLOW, u = easeIO(t / D);
      const L = [lab('rec', 'Reception', null, [0.5, 1.6, 1.2], 0.5, [-80, -60]), lab('dq', 'Display quadcopter', null, [0.5, 6.8, 1.6], 0.9, [110, -50]),
                 lab('toh', 'To lecture hall', null, [-3, 5.2, 2.3], 2.2, [-90, -40])];
      return { eye: path([[2.4, 11.0, 1.65], [0.6, 9.4, 1.65], [-0.8, 8.0, 1.7]], u), look: path([[0.3, 2.0, 1.2], [-0.6, 3.0, 1.4], [-3.4, 4.6, 1.8]], u), fov: 64, interior: 1, shadowR: 30,
               hdr: hdr('INTERIOR', 'Foyer & reception', t), labels: labels(L, t, D) }; } },
  { name: 'simulator', dur: 4.0 * SLOW, fn: t => {
      const D = 4.0 * SLOW, u = easeIO(t / D);
      const L = [lab('st', 'Simulator stations × 8', 'Triple monitors · RC & FPV', [9.6, 1.8, 1.4], 0.6, [-60, -110]), lab('vw', 'Video wall', null, [17.4, 2.6, 4.4], 1.2, [80, -50]),
                 lab('ic', 'Instructor console', null, [5.6, -1.5, 1.3], 1.8, [-110, 40]), lab('ms', 'Motion simulator', null, [7.0, -8.8, 3.0], 2.4, [-80, -60])];
      return { eye: path([[5.0, 8.6, 2.6], [8.0, 3.6, 2.1], [11.4, 3.5, 1.9]], u), look: path([[14, -2, 1.4], [16, 0, 1.8], [17.5, -1.0, 2.5]], u), fov: 64, interior: 1, shadowR: 30,
               hdr: hdr('INTERIOR', 'Simulator complex', t), labels: labels(L, t, D) }; } },
  { name: 'tower_office', dur: 0, fn: null },
  { name: 'tower_store', dur: 0, fn: null },
  { name: 'tower_washrooms', dur: 0, fn: null },
  { name: 'tower_battery', dur: 0, fn: null },
  { name: 'hall_360', dur: 12.5 * SLOW, fn: t => {
      const D = 12.5 * SLOW, yaw = Math.PI + 2 * Math.PI * easeIO(t / D);
      const eye = [-7.6, 0, 2.95], look = [eye[0] + Math.cos(yaw) * 10, eye[1] + Math.sin(yaw) * 10, 2.3];
      const L = [lab('scr', 'Projection screen', null, [-17.4, 1.9, 4.9], 0.3, [120, -40]), lab('stg', 'Stage', null, [-14.2, -5.4, 1.05], 0.3, [60, 70]),
                 lab('qa', 'Quaid-e-Azam', 'Muhammad Ali Jinnah', [-17.5, -4.55, 2.55], 0.4, [-30, 120]), lab('ai', 'Allama Muhammad Iqbal', null, [-17.5, 4.55, 2.55], 0.4, [30, 120]),
                 lab('lec', 'Lectern', null, [-14.4, 4.0, 2.2], 0.5, [90, 60]), lab('vip', 'VIP panel table', null, [-15.6, -1.2, 1.5], 0.5, [-40, 90]),
                 lab('wc', 'To community washrooms', null, [-15.2, 9.2, 3.1], 0.5, [60, -50]), lab('bat', 'To battery charging & maint room', null, [-15.2, -9.2, 3.1], 0.5, [-60, -50]),
                 lab('seat', '100-seat tiered seating', '10 rows × 10 · centre aisle', [-4.6, -2.2, 1.9], 0.5, [0, -120], { occ: false }),
                 lab('ac', 'Acoustic wall panelling', null, [-7.0, 11.5, 4.3], 0.5, [0, -50]), lab('ac2', 'Acoustic wall panelling', null, [-7.0, -11.5, 4.3], 0.5, [0, -50]),
                 lab('av', 'AV control desk', null, [-4.0, 8.6, 1.3], 0.5, [70, 60]), lab('ent2', 'Entry from foyer', null, [-3.1, 5.2, 2.6], 0.5, [-80, -50]),
                 lab('led', 'LED ceiling lighting', null, [-11.0, -6.0, 5.32], 0.5, [0, 60])];
      return { eye, look, fov: 74, interior: 1, shadowR: 30, shadowAt: [-9, 0, 2], hdr: hdr('MAIN LECTURE HALL', '100 students  ·  360° view', t), labels: labels(L, t, D) }; } },
  { name: 'dusk_closing', dur: 11.0, fn: t => {
      const u = easeIO(t / 11), el = lerp(5, -9, clamp(t / 7.5));
      return { eye: path([[-46, 70, 6], [-10, 86, 12], [30, 104, 24], [70, 150, 48]], u), look: path([[-4, 10, 6], [0, 8, 7], [0, 4, 7], [0, 0, 6]], u), fov: 44, shadowR: 110, shadowAt: [0, 0, 0],
               env: { sun: [252, el], moon: [120, 30], cloud: 0.3, skySpeed: 1.2 }, rpm: 70, ao: t < 6.8,
               card: t > 6.0 ? Object.assign(titleCard(t, 6.0), { tint: ramp(t, 6.0, 7.2) }) : null }; } },
];
// tower rooms (6 s at 0.75x = 8 s each), fixture labels: [id, title, sub, angle from outward axis, distance from centre, z, t0, offset]
const TD_ = 7.0;
const towerClips = {
  tower_office: towerShot('NE', TD_, 'OFFICE', 'North-east rotor tower', [
    ['od', 'Executive desk', null, 0, 1.3, 1.1, 0.5, [-70, -90]], ['oc', 'High-back chair', null, 0, 2.2, 1.5, 1.0, [60, -100]],
    ['os', 'Sofa set & coffee table', null, -1.45, 2.1, 0.9, 1.6, [-60, -80]], ['ob', 'Bookcase', null, 1.45, 2.95, 1.9, 2.6, [70, -60]],
    ['of', 'National flag', null, 0.85, 2.6, 2.3, 3.2, [80, -40]], ['om', 'Area map', null, -0.55, 3.15, 2.2, 3.8, [-70, -60]],
    ['oa', 'Split AC', null, 0.55, 3.05, 2.9, 4.4, [80, -30]]]),
  tower_store: towerShot('SE', TD_, 'DRONE & EQUIPMENT STORE', 'South-east rotor tower', [
    ['sr', 'Steel racking with bins', null, 0, 2.9, 2.0, 0.5, [0, -110]], ['sq', 'Training drones', null, -0.85, 2.88, 2.15, 1.2, [-80, -60]],
    ['sc', 'Drone transport cases', null, 1.65, 2.8, 1.2, 2.0, [80, -60]], ['sp', 'Spare propellers', null, -1.65, 3.15, 1.8, 2.8, [-80, -50]],
    ['sf', 'Fixed-wing UAV (cased)', null, -0.9, 1.6, 0.75, 3.4, [-60, 80]], ['si', 'Issue counter', null, 0, 0.95, 1.35, 4.2, [60, 90]],
    ['st', 'Tool cabinet', null, -1.65, 2.95, 1.35, 4.8, [-90, 40]]]),
  tower_washrooms: towerShot('NW', TD_, 'COMMUNITY WASHROOMS × 3', 'North-west rotor tower', [
    ['w1', 'Washroom cubicles × 3', null, 0, 2.0, 2.2, 0.5, [0, -100]], ['w2', 'Vanity — 3 basins & mirror', null, -1.55, 2.9, 1.9, 1.5, [-80, -60]],
    ['w3', 'Wuzu (ablution) area', null, 1.55, 2.7, 0.9, 2.6, [90, 50]], ['w4', 'Hand dryer', null, 1.05, 3.1, 1.6, 3.4, [90, -40]],
    ['w5', 'Exhaust fan', null, 0, 3.15, 2.9, 4.2, [70, -30]], ['w6', 'Wall & floor tiling', null, -0.9, 3.15, 0.6, 4.8, [-80, 60]]]),
  tower_battery: towerShot('SW', TD_, 'BATTERY CHARGING & MAINT ROOM', 'South-west rotor tower', [
    ['b1', 'Fire-safe charging cabinets', 'LiPo charging indicators', 0, 2.7, 2.15, 0.5, [0, -110]], ['b2', 'Battery rack', null, 1.45, 2.85, 1.7, 1.4, [80, -60]],
    ['b3', 'Workbench & tool board', null, -1.45, 2.7, 1.3, 2.2, [-80, -60]], ['b4', 'Drone on repair stand', null, 0, 1.0, 1.25, 3.0, [70, 70]],
    ['b5', 'Sand buckets', null, 1.82, 2.85, 0.95, 3.8, [80, 40]], ['b6', 'Fire extinguisher', null, -1.85, 3.05, 0.9, 4.4, [-80, 40]],
    ['b7', 'Ventilation louver', null, 0, 3.15, 2.85, 5.0, [60, -30]]]),
};
for (const c of CLIPS) if (towerClips[c.name]) { c.dur = TD_; c.fn = towerClips[c.name]; }
// order: interiors flow foyer -> simulator -> office (NE) -> store (SE) -> washrooms (NW) -> battery (SW) -> lecture hall
const total = CLIPS.reduce((a, c) => a + c.dur, 0) - XF * (CLIPS.length - 1);
module.exports = { CLIPS, XF, total };
