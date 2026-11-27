// Shot list for the DRONE TRG COMPLEX - 44 DIV video. Coordinates: ENU metres (x east, y north, z up).
// Each shot: duration (s), keyframed eye/look paths (Catmull-Rom, eased), fov and scene flags.
const ease = t => t * t * (3 - 2 * t);
function cr(p0, p1, p2, p3, t) {
  const t2 = t * t, t3 = t2 * t;
  return p1.map((_, i) => 0.5 * ((2 * p1[i]) + (-p0[i] + p2[i]) * t + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t2 + (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t3));
}
function path(keys, u) {
  if (keys.length === 1) return keys[0];
  const n = keys.length - 1, x = Math.min(u * n, n - 1e-9), i = Math.floor(x), t = x - i;
  return cr(keys[Math.max(i - 1, 0)], keys[i], keys[i + 1], keys[Math.min(i + 2, n)], t);
}
const orbit = (r0, r1, h0, h1, a0, a1, n = 7) => Array.from({ length: n }, (_, k) => {
  const u = k / (n - 1), a = (a0 + (a1 - a0) * u) * Math.PI / 180, r = r0 + (r1 - r0) * u;
  return [Math.cos(a) * r, Math.sin(a) * r, h0 + (h1 - h0) * u];
});
// 30-second showcase: 11 shots, 0.4 s crossfades (sum of durations 34.0 s -> 30.0 s final)
const XF = 0.4;
const SHOTS = [
  { name: 'approach', dur: 3.2, fov: 45, eye: [[-900, 1000, 450], [-300, 330, 170], [-120, 140, 70]], look: [[0, 0, 0], [0, 3, 2], [0, 4, 4]], shadowR: 120 },
  { name: 'orbit_title', dur: 4.0, fov: 42, eye: orbit(72, 60, 30, 15, 160, 25), look: [[0, 0, 6], [0, 3, 5.5], [0, 4, 5]], shadowR: 95 },
  { name: 'rotor', dur: 2.8, fov: 40, eye: [[36, 22, 13.5], [32, 31, 12.5], [26, 37, 11.5]], look: [[16.4, 10.4, 9.4], [16.4, 10.4, 9.3]], shadowR: 40 },
  { name: 'takeoff', dur: 3.2, fov: 42, eye: Array.from({ length: 5 }, (_, k) => { const a = (-90 + k * 8) * Math.PI / 180, h = 50 + k * 18; return [Math.cos(a) * 9, Math.sin(a) * 9, h]; }),
    look: [[0, 0, 0]], rpm: [160, 520], dust: [0, 1], shadowR: 70 },
  { name: 'flying_field', dur: 3.4, fov: 50, eye: [[64, -48, 9], [63, -12, 8], [55, 28, 11]], look: [[38, -26, 1], [38, -4, 1.5], [22, 0, 4]], shadowR: 60 },
  { name: 'entrance_flag', dur: 2.8, fov: 50, eye: [[2.2, 46, 2.6], [1.0, 20, 2.0]], look: [[0, 0, 5.0], [0, 0, 2.6]], shadowR: 45 },
  { name: 'foyer', dur: 2.6, fov: 62, interior: 1, eye: [[-1.2, 11.2, 1.7], [-2.0, 4.2, 1.75]], look: [[0.5, 6.8, 1.1], [-4.0, 5.2, 1.8]], shadowR: 30 },
  { name: 'lecture_hall', dur: 3.2, fov: 62, interior: 1, eye: [[-3.7, 5.2, 2.6], [-7.0, 0.5, 3.1], [-10.2, -4.4, 2.8]], look: [[-14, 1, 2.3], [-16, 0, 2.7], [-16.5, 2.5, 2.4]], shadowR: 30 },
  { name: 'simulator', dur: 3.2, fov: 62, interior: 1, eye: [[5.0, 8.6, 2.6], [8.0, 3.6, 2.0], [11.4, 3.5, 1.85]], look: [[14, -2, 1.4], [16, 0, 1.8], [17.5, -1.0, 2.5]], shadowR: 30 },
  { name: 'cutaway', dur: 3.0, fov: 42, interior: 1, noRoof: 1, eye: orbit(40, 36, 38, 30, -70, 40, 5), look: [[0, 0, 1]], shadowR: 50 },
  { name: 'departure', dur: 2.6, fov: 45, eye: [[0, 70, 10], [-120, 300, 160], [-260, 600, 330]], look: [[0, 0, 5], [0, 0, 1], [0, 0, 0]], shadowR: 120 },
];
function stateAt(shot, t) {               // t seconds inside the shot
  const u = ease(Math.min(Math.max(t / shot.dur, 0), 1));
  const lin = t / shot.dur;
  const rpm = shot.rpm ? shot.rpm[0] + (shot.rpm[1] - shot.rpm[0]) * Math.min(1, lin * 1.15) : 160;
  const dust = shot.dust ? shot.dust[0] + (shot.dust[1] - shot.dust[0]) * Math.min(1, lin * 1.4) : 0;
  return { eye: path(shot.eye, u), look: path(shot.look, u), fov: shot.fov, interior: shot.interior || 0, noRoof: shot.noRoof || 0, rpm, dust, shadowR: shot.shadowR,
           shadowAt: path(shot.look, u) };
}
module.exports = { SHOTS, stateAt, XF };
