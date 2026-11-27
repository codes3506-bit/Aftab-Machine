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
const SHOTS = [
  { name: 'approach', dur: 9, fov: 45, eye: [[-1400, 1500, 650], [-760, 780, 400], [-300, 330, 170], [-170, 190, 95]],
    look: [[0, 0, 0], [0, 0, 0], [0, 4, 3], [0, 4, 4]], shadowR: 120 },
  { name: 'orbit', dur: 12, fov: 42, eye: orbit(80, 66, 34, 18, 160, 22), look: [[0, 0, 6], [0, 2, 5.5], [0, 4, 5]], shadowR: 95 },
  { name: 'rotor', dur: 7, fov: 40, eye: [[36, 22, 13.5], [33, 30, 12.5], [27, 36, 11.5]], look: [[16.4, 10.4, 9.4], [16.4, 10.4, 9.3]], shadowR: 40 },
  { name: 'takeoff', dur: 8, fov: 42, eye: Array.from({ length: 6 }, (_, k) => { const a = (-90 + k * 9) * Math.PI / 180, h = 55 + k * 17; return [Math.cos(a) * 9, Math.sin(a) * 9, h]; }),
    look: [[0, 0, 0]], rpm: [160, 520], dust: [0, 1], shadowR: 70 },
  { name: 'entrance', dur: 6, fov: 50, eye: [[2.4, 50, 2.4], [1.8, 34, 2.2], [1.0, 19.5, 2.0]], look: [[0, 0, 4.6], [0, 6, 4.0], [0, 0, 2.4]], shadowR: 45 },
  { name: 'foyer', dur: 5, fov: 62, interior: 1, eye: [[-1.2, 11.2, 1.7], [-1.6, 7.5, 1.7], [-2.0, 4.2, 1.75]], look: [[0.5, 6.8, 1.1], [0.0, 5.5, 1.3], [-4.0, 5.2, 1.8]], shadowR: 30 },
  { name: 'hall', dur: 9, fov: 62, interior: 1, eye: [[-3.7, 5.2, 2.4], [-5.5, 3.6, 3.0], [-8.0, -1.5, 3.1], [-10.2, -4.4, 2.8]], look: [[-14, 1, 2.3], [-15, 0, 2.6], [-17, 0, 2.8], [-16.5, 2.5, 2.4]], shadowR: 30 },
  { name: 'simulator', dur: 9, fov: 62, interior: 1, eye: [[5.0, 8.6, 2.6], [7.0, 3.6, 2.1], [9.6, 3.6, 1.9], [11.4, 3.5, 1.85]], look: [[14, -2, 1.4], [15, 0, 1.6], [17.5, 0.5, 2.4], [17.5, -1.0, 2.5]], shadowR: 30 },
  { name: 'departure', dur: 10, fov: 45, eye: [[0, 72, 10], [-40, 170, 60], [-150, 380, 190], [-300, 700, 380]], look: [[0, 0, 5], [0, 0, 3], [0, 0, 0], [0, 0, 0]], shadowR: 120 },
];
function stateAt(shot, t) {               // t seconds inside the shot
  const u = ease(Math.min(Math.max(t / shot.dur, 0), 1));
  const lin = t / shot.dur;
  const rpm = shot.rpm ? shot.rpm[0] + (shot.rpm[1] - shot.rpm[0]) * Math.min(1, lin * 1.15) : 160;
  const dust = shot.dust ? shot.dust[0] + (shot.dust[1] - shot.dust[0]) * Math.min(1, lin * 1.4) : 0;
  return { eye: path(shot.eye, u), look: path(shot.look, u), fov: shot.fov, interior: shot.interior || 0, rpm, dust, shadowR: shot.shadowR,
           shadowAt: path(shot.look, u) };
}
module.exports = { SHOTS, stateAt };
