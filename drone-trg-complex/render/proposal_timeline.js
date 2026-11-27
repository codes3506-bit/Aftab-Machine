// DRONE TRG COMPLEX - 44 DIV : proposal video timeline (65 s at 30 fps, 0.5 s crossfades).
// Each clip returns the full renderer state for a local time t (seconds). ENU metres.
const XF = 0.5;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const ease = x => { x = clamp(x); return x * x * (3 - 2 * x); };
const ramp = (t, a, b) => ease((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
function cr(p0, p1, p2, p3, t) { const t2 = t * t, t3 = t2 * t; return p1.map((_, i) => 0.5 * (2 * p1[i] + (-p0[i] + p2[i]) * t + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t2 + (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t3)); }
function path(keys, u) { if (keys.length === 1) return keys[0]; const n = keys.length - 1, x = Math.min(u * n, n - 1e-9), i = Math.floor(x); return cr(keys[Math.max(i - 1, 0)], keys[i], keys[i + 1], keys[Math.min(i + 2, n)], x - i); }
const orbitPt = (r, h, deg, c = [0, 0]) => [c[0] + Math.cos(deg * Math.PI / 180) * r, c[1] + Math.sin(deg * Math.PI / 180) * r, h];
// label helper: fades in at t0, out at t1 (local seconds)
const lab = (id, t, s, p, t0, t1, extra) => ({ id, t, s, p, t0, t1: t1 === undefined ? 1e9 : t1, ...(extra || {}) });
function labels(list, t, dur) { return list.filter(L => t >= L.t0 - 0.01 && t <= Math.min(L.t1, dur) + 0.01).map(L => ({ ...L, a: Math.min(ramp(t, L.t0, L.t0 + 0.45), 1 - ramp(t, Math.min(L.t1, dur - 0.3), Math.min(L.t1, dur - 0.3) + 0.35)) })); }

const EMPTY = { pad: 0, land: 0, core: 0, interior: 0, road: 0, finish: -1, hShell: 0, hRoof: 0, hCol: 0, foot: 0, crane: 0 };
const GR = 'GR 25°19\'47.62"N   62°30\'33.00"E';
const TOWER = { NE: [16.42, 10.42], NW: [-16.42, 10.42], SW: [-16.42, -10.42], SE: [16.42, -10.42] };

const CLIPS = [
  { name: 'title', dur: 5.5, fn: t => ({
      eye: path([[-1100, -1500, 950], [-980, -1330, 860]], t / 5.5), look: [0, 0, 0], fov: 45, near: 2, build: EMPTY, shade: 0.58, rpm: 0, shadowR: 200,
      card: { logo: ramp(t, 0.3, 1.3), title: ramp(t, 0.9, 2.1), rule: ramp(t, 1.5, 2.6), subA: ramp(t, 2.1, 3.0), sub: 'PROPOSAL', sub2: 'Siting  ·  Construction Sequence  ·  Layout & Facilities' } }) },
  { name: 'site_location', dur: 10.5, fn: t => {
      const u = ease(t / 10.5);
      const L = [lab('pin', 'PROPOSED SITE', 'Drone Trg Complex - 44 Div', [0, 0, 8], 1.0),
                 lab('road', 'EXISTING METALLED ROAD', null, [-407, 420, 0], 3.6),
                 lab('appr', 'PROPOSED APPROACH ROAD', '≈ 410 m to site', [-210, 61, 0], 5.8),
                 lab('area', 'DEMARCATED AREA', '110 m × 92 m  (≈ 1.01 ha)', [55, 52, 0], 7.0),
                 lab('lvl', 'GROUND LEVEL 23.8 m', 'Mean slope 2° · relief 5.7 m within 100 m', [-55, -40, 0], 8.0)];
      return { eye: path([[-2600, -7600, 10500], [-1300, -3300, 4200], [-420, -1000, 1250], [-150, -250, 230]], u), look: [0, 0, 0], fov: 45, near: t < 6 ? 6 : 0.5,
               build: { ...EMPTY, road: 1 }, demarc: 1, rpm: 0, shadowR: 160, north: 1,
               hdr: { k: 'SITE LOCATION', v: GR, a: ramp(t, 0.3, 1.0) }, labels: labels(L, t, 10.5) }; } },
  { name: 'construction', dur: 15.5, fn: t => {
      const s = t - 0.25;
      const phases = [
        [0, 1.5, '1', 'SITE CLEARANCE & SETTING OUT', 'Grubbing and clearance · compound 110 m × 92 m pegged out from the GR'],
        [1.5, 3.5, '2', 'EARTHWORK', 'Cut ≈ 7,500 m³ · fill ≈ 5,000 m³ · compacted in 200 mm layers to 95 % MDD (Modified AASHTO)'],
        [3.5, 5.5, '3', 'FOUNDATIONS & PLINTH', 'PCC 1:4:8 blinding · RCC 4000 psi footings & plinth beam · bitumen + APP membrane, anti-termite (coastal saline zone)'],
        [5.5, 8.0, '4', 'RCC FRAME', 'RCC columns & beams 4000 psi · Grade 60 steel · vibrated, 7-day curing'],
        [8.0, 10.2, '5', 'MASONRY & ROTOR TOWERS', 'Stone masonry in CM 1:4 · four rotor-tower drums with RCC ring beams'],
        [10.2, 11.6, '6', 'ROOF SLAB', 'RCC slab with insulation, waterproofing and heat-reflective coat'],
        [11.6, 13.2, '7', 'DRONE CORE & ROTOR PODS', 'Composite arms, motor housings and 11 m two-blade propellers'],
        [13.2, 15.5, '8', 'FINISHES, SERVICES & LANDSCAPING', 'Weather-shield paint · tiles & terrazzo · E&M services · roads, lawns and flying field']];
      const ph = phases.find(p => s < p[1]) || phases[phases.length - 1];
      const capA = Math.min(ramp(s, ph[0], ph[0] + 0.3), 1 - ramp(s, ph[1] - 0.25, ph[1]) * (ph === phases[phases.length - 1] ? 0 : 1));
      const b = { pad: ramp(s, 1.5, 3.4), foot: ramp(s, 3.5, 4.6), hShell: s < 4.5 ? 0 : s < 8 ? lerp(0.01, 0.3, ramp(s, 4.5, 5.4)) : lerp(0.3, 7.6, ramp(s, 8.0, 10.2)),
                  hCol: lerp(0.3, 7.45, ramp(s, 5.5, 8.0)) * (s > 5.5 ? 1 : 0), hRoof: lerp(5.3, 6.75, ramp(s, 10.2, 11.6)), core: ramp(s, 11.6, 13.2),
                  finish: lerp(-0.5, 12, ramp(s, 13.2, 15.0)), land: ramp(s, 13.4, 15.2), interior: s > 13.2 ? 1 : 0, road: s > 13.6 ? 1 : 0, crane: s > 3.5 && s < 13.4 ? 1 : 0 };
      return { eye: orbitPt(lerp(82, 66, ease(t / 15.5)), lerp(44, 30, ease(t / 15.5)), lerp(-150, 62, ease(t / 15.5))), look: [0, 0, 3], fov: 44,
               build: b, demarc: s < 3.0 ? 1 : 0, dust: s > 1.5 && s < 3.6 ? 1 : 0, rpm: lerp(0, 80, ramp(s, 13.2, 14.5)), shadowR: 90,
               hdr: { k: 'CONSTRUCTION SEQUENCE', v: 'Earthwork to finishes, bottom to top', a: ramp(t, 0.2, 0.8) },
               cap: { n: ph[2], h: ph[3], d: ph[4], a: capA } }; } },
  { name: 'fly_exterior', dur: 5.5, fn: t => {
      const L = [lab('ne', 'OFFICE', 'OIC Drone Trg', [...TOWER.NE, 7.9], 0.5), lab('nw', 'WASHROOMS', null, [...TOWER.NW, 7.9], 0.9),
                 lab('ent', 'MAIN ENTRANCE', null, [0, 15.6, 4.6], 1.4), lab('se', 'DRONE & EQPT STORE', null, [...TOWER.SE, 7.9], 1.9),
                 lab('sw', 'BATTERY CHARGING & MAINT', null, [...TOWER.SW, 7.9], 2.3), lab('rot', 'ROTOR PODS', '11 m propellers · counter-rotating', [0, 0, 8.4], 3.0)];
      return { eye: orbitPt(lerp(60, 50, ease(t / 5.5)), lerp(24, 15, ease(t / 5.5)), lerp(128, 58, ease(t / 5.5))), look: [0, 1, 5.5], fov: 46, shadowR: 80,
               hdr: { k: 'FLY-THROUGH', v: 'Rotor Towers & Main Entrance', a: ramp(t, 0.2, 0.7) }, labels: labels(L, t, 5.5) }; } },
  { name: 'fly_field', dur: 4.5, fn: t => {
      const u = ease(t / 4.5);
      const L = [lab('fld', 'DRONE FLYING FIELD', '25 m × 56 m', [39.5, -5, 0.2], 0.3), lab('gate', 'RACE GATES', null, [34, -10, 3.1], 0.8),
                 lab('pad', 'LANDING PADS', null, [39.5, -30, 0.3], 1.2), lab('gcs', 'GROUND CONTROL STATION', null, [22.5, -30, 4.6], 1.6),
                 lab('sock', 'WINDSOCK', null, [51.3, 17.5, 5.9], 2.2), lab('mast', 'COMMS MAST', null, [48, 40, 18], 2.6)];
      return { eye: path([[66, -52, 10], [64, -14, 9], [58, 18, 12]], u), look: path([[38, -26, 1], [37, -6, 2], [34, 6, 4]], u), fov: 50, shadowR: 60,
               hdr: { k: 'FLY-THROUGH', v: 'Drone Flying Field', a: ramp(t, 0.2, 0.7) }, labels: labels(L, t, 4.5) }; } },
  { name: 'fly_cutaway', dur: 4.5, fn: t => {
      const o = { occ: false };
      const L = [lab('lh', 'LECTURE HALL', '100 students', [-9, 0, 3], 0.4, 1e9, o), lab('sc', 'SIMULATOR COMPLEX', '8 pilot stations', [11, 0, 3], 0.7, 1e9, o),
                 lab('fy', 'FOYER & RECEPTION', null, [0.5, 3, 2.5], 1.0, 1e9, o), lab('ne2', 'OFFICE', null, [...TOWER.NE, 2.5], 1.3, 1e9, o),
                 lab('nw2', 'WASHROOMS', null, [...TOWER.NW, 2.5], 1.5, 1e9, o), lab('se2', 'STORE', null, [...TOWER.SE, 2.5], 1.7, 1e9, o),
                 lab('sw2', 'BATTERY ROOM', null, [...TOWER.SW, 2.5], 1.9, 1e9, o)];
      return { eye: orbitPt(lerp(42, 36, ease(t / 4.5)), lerp(42, 36, ease(t / 4.5)), lerp(-112, -68, ease(t / 4.5))), look: [0, 0, 1], fov: 44, noRoof: 1, interior: 1, shadowR: 45,
               hdr: { k: 'FLY-THROUGH', v: 'Layout — Roof Removed', a: ramp(t, 0.2, 0.7) }, labels: labels(L, t, 4.5) }; } },
  { name: 'fly_foyer', dur: 3.5, fn: t => {
      const u = ease(t / 3.5);
      const L = [lab('rec', 'RECEPTION', null, [0.5, 1.6, 1.4], 0.3), lab('dq', 'DISPLAY QUADCOPTER', null, [0.5, 6.8, 1.9], 0.6), lab('toh', 'TO LECTURE HALL', null, [-3, 5.2, 2.5], 1.4)];
      return { eye: path([[-1.2, 11.2, 1.7], [-2.0, 4.2, 1.75]], u), look: path([[0.5, 6.8, 1.1], [-4.0, 5.2, 1.8]], u), fov: 62, interior: 1, shadowR: 30,
               hdr: { k: 'FLY-THROUGH', v: 'Foyer', a: ramp(t, 0.2, 0.7) }, labels: labels(L, t, 3.5) }; } },
  { name: 'fly_simulator', dur: 4.0, fn: t => {
      const u = ease(t / 4.0);
      const L = [lab('st', 'SIMULATOR STATIONS × 8', 'Triple monitors · RC & FPV', [9.6, 1.8, 1.5], 0.4), lab('vw', 'VIDEO WALL', null, [17.4, 0, 3.6], 0.9),
                 lab('ic', 'INSTRUCTOR CONSOLE', null, [5.6, -1.5, 1.4], 1.3), lab('ms', 'MOTION SIMULATOR', null, [7.0, -8.8, 3.0], 1.7)];
      return { eye: path([[5.0, 8.6, 2.6], [8.0, 3.6, 2.1], [11.4, 3.5, 1.9]], u), look: path([[14, -2, 1.4], [16, 0, 1.8], [17.5, -1.0, 2.5]], u), fov: 64, interior: 1, shadowR: 30,
               hdr: { k: 'FLY-THROUGH', v: 'Simulator Complex', a: ramp(t, 0.2, 0.7) }, labels: labels(L, t, 4.0) }; } },
  { name: 'hall_360', dur: 12.5, fn: t => {
      const yaw = Math.PI + 2 * Math.PI * ease(t / 12.5) - 0.0;
      const eye = [-7.6, 0, 2.95];
      const look = [eye[0] + Math.cos(yaw) * 10, eye[1] + Math.sin(yaw) * 10, 2.3];
      const dn = { down: true };
      const L = [lab('stg', 'STAGE', null, [-15.0, -5.0, 1.1], 0.2), lab('scr', 'PROJECTION SCREEN', null, [-17.3, 1.6, 5.1], 0.3),
                 lab('qa', 'QUAID-E-AZAM', 'Muhammad Ali Jinnah', [-17.5, -4.55, 2.5], 0.4, 1e9, dn), lab('ai', 'ALLAMA MUHAMMAD IQBAL', null, [-17.5, 4.55, 2.5], 0.5, 1e9, dn),
                 lab('lec', 'LECTERN', null, [-14.4, 4.0, 2.2], 0.6), lab('vip', 'VIP PANEL TABLE', null, [-15.6, -1.2, 1.9], 0.7),
                 lab('wc', 'TO WASHROOMS', null, [-15.2, 9.2, 3.0], 0.5), lab('bat', 'TO BATTERY CHARGING & MAINT', null, [-15.2, -9.2, 3.0], 0.5),
                 lab('seat', '100-SEAT TIERED SEATING', '10 rows × 10 · centre aisle', [-6.0, -2.2, 1.9], 0.5, 1e9, { occ: false }),
                 lab('ac', 'ACOUSTIC WALL PANELLING', null, [-7.0, 11.5, 3.6], 0.5), lab('ac2', 'ACOUSTIC WALL PANELLING', null, [-7.0, -11.5, 3.6], 0.5),
                 lab('av', 'AV CONTROL DESK', null, [-4.0, 8.6, 1.5], 0.5), lab('ent2', 'ENTRY FROM FOYER', null, [-3.1, 5.2, 2.7], 0.5),
                 lab('led', 'LED CEILING LIGHTING', null, [-11.0, -6.0, 5.3], 0.5)];
      return { eye, look, fov: 74, interior: 1, shadowR: 30, shadowAt: [-9, 0, 2],
               hdr: { k: 'MAIN LECTURE HALL', v: '100 Students  ·  360° View', a: ramp(t, 0.2, 0.7) }, labels: labels(L, t, 12.5) }; } },
  { name: 'closing', dur: 3.5, fn: t => ({
      eye: path([[-140, 230, 120], [-180, 300, 160]], t / 3.5), look: [0, 0, 3], fov: 42, shade: 0.55, shadowR: 150,
      card: { logo: ramp(t, 0.2, 1.0), title: ramp(t, 0.5, 1.3), rule: ramp(t, 0.9, 1.6), subA: ramp(t, 1.2, 1.9), sub: 'PROPOSED FOR APPROVAL', sub2: GR } }) },
];
const total = CLIPS.reduce((a, c) => a + c.dur, 0) - XF * (CLIPS.length - 1);
module.exports = { CLIPS, XF, total };
