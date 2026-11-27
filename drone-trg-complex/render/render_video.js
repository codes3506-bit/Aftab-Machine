// node render/render_video.js OUTDIR [shotIndices] [--scale 0.5]
// Renders each shot with headless Chromium (three.js) and pipes JPEG frames into ffmpeg.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const http = require('http'), fs = require('fs'), path = require('path');
const { SHOTS, stateAt } = require('./timeline');
const ROOT = path.join(__dirname, '..');
const OUT = process.argv[2]; fs.mkdirSync(OUT, { recursive: true });
const only = process.argv[3] && process.argv[3] !== 'all' ? process.argv[3].split(',').map(Number) : SHOTS.map((_, i) => i);
const scale = process.argv.includes('--scale') ? +process.argv[process.argv.indexOf('--scale') + 1] : 1;
const W = Math.round(1920 * scale), H = Math.round(1080 * scale), FPS = 30;
const PORT = 8800 + Math.floor(Math.random() * 150);
(async () => {
  const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'application/javascript' : f.endsWith('.json') ? 'application/json' : f.endsWith('.jpg') ? 'image/jpeg' : 'application/octet-stream' }); r.end(d); } }); }).listen(PORT);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: W, height: H } });
  p.on('pageerror', e => console.error('pageerror', e.message));
  await p.goto(`http://localhost:${PORT}/render/viewer.html?headless=1&w=${W}&h=${H}`);
  await p.waitForFunction('window.R && window.R.ready', null, { timeout: 180000 });
  let tGlobal = 0;
  for (let si = 0; si < SHOTS.length; si++) {
    const shot = SHOTS[si], n = Math.round(shot.dur * FPS);
    if (!only.includes(si)) { tGlobal += shot.dur; continue; }
    const file = path.join(OUT, `shot_${String(si).padStart(2, '0')}_${shot.name}.mp4`);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', file]);
    const t0 = Date.now();
    for (let f = 0; f < n; f++) {
      const t = f / FPS;
      await p.evaluate(([tt, s]) => window.R.frame(tt, s), [tGlobal + t, stateAt(shot, t)]);
      const buf = await p.screenshot({ type: 'jpeg', quality: 93 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 60 === 0) console.log(shot.name, f, '/', n, ((Date.now() - t0) / (f + 1) / 1000).toFixed(2), 's/frame');
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    console.log('done', file, ((Date.now() - t0) / 1000).toFixed(0), 's');
    tGlobal += shot.dur;
  }
  await b.close(); srv.close();
})();
