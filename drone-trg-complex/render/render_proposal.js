// node render/render_proposal.js OUTDIR [clipIdx,..|all] [--stills 0.1,0.5,0.9] [--scale 0.5]
// Renders proposal clips through headless Chromium (three.js + DOM overlays) and pipes frames to ffmpeg.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const http = require('http'), fs = require('fs'), path = require('path');
const { CLIPS, XF } = require('./proposal_timeline');
const ROOT = path.join(__dirname, '..');
const OUT = process.argv[2]; fs.mkdirSync(OUT, { recursive: true });
const arg = k => process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : null;
const spec = process.argv[3] && process.argv[3] !== 'all' ? process.argv[3].split(',') : CLIPS.map((_, i) => String(i));
// entries: "13" (whole clip) or "13:0/2" (part 0 of 2 -> clip_13_name.p0.mp4)
const jobs = {}; for (const e of spec) { const [c, pr] = e.split(':'); (jobs[+c] = jobs[+c] || []).push(pr ? pr.split('/').map(Number) : null); }
const only = Object.keys(jobs).map(Number);
const scale = +(arg('--scale') || 1), stills = arg('--stills'), SS = +(arg('--ss') || 1.5), OVR = JSON.parse(arg('--ovr') || '{}');
const W = Math.round(1920 * scale), H = Math.round(1080 * scale), FPS = 30;
const PORT = 8800 + Math.floor(Math.random() * 150);
const TYPES = { html: 'text/html', js: 'application/javascript', json: 'application/json', jpg: 'image/jpeg', png: 'image/png', TTF: 'font/ttf', f32: 'application/octet-stream' };
(async () => {
  const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'Content-Type': TYPES[f.split('.').pop()] || 'application/octet-stream' }); r.end(d); } }); }).listen(PORT);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: stills ? scale : SS });
  p.on('pageerror', e => console.error('pageerror', e.message)); p.on('console', m => { if ((m.type() === 'error' || m.type() === 'warning') && !/GPU stall/.test(m.text())) console.error('console', m.text().slice(0, 300)); });
  await p.goto(`http://localhost:${PORT}/render/proposal.html?ss=${stills ? scale : SS}`);
  await p.waitForFunction('window.R && window.R.ready', null, { timeout: 240000 });
  let tStart = 0;
  for (let ci = 0; ci < CLIPS.length; ci++) {
    const clip = CLIPS[ci];
    if (only.includes(ci)) {
      if (stills) {
        for (const k of stills.split(',').map(Number)) {
          const t = k * clip.dur;
          await p.evaluate(([tt, s]) => window.R.frame(tt, s), [tStart + t, Object.assign(clip.fn(t), OVR)]);
          await p.screenshot({ path: path.join(OUT, `still_${String(ci).padStart(2, '0')}_${clip.name}_${k}${arg('--tag') || ''}.jpg`), type: 'jpeg', quality: 88 });
        }
      } else for (const part of jobs[ci]) {
        const n = Math.round(clip.dur * FPS);
        const f0 = part ? Math.floor(n * part[0] / part[1]) : 0, f1 = part ? Math.floor(n * (part[0] + 1) / part[1]) : n;
        const file = path.join(OUT, `clip_${String(ci).padStart(2, '0')}_${clip.name}${part ? '.p' + part[0] : ''}.mp4`);
        for (let w = Math.max(0, f0 - 20); w < f0; w++) await p.evaluate(([tt, s]) => window.R.frame(tt, s), [tStart + w / FPS, clip.fn(w / FPS)]);
        const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
          '-vf', `scale=${Math.round(1920 * Math.min(SS, 2))}:${Math.round(1080 * Math.min(SS, 2))}:flags=lanczos`, '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', file]);
        const t0 = Date.now();
        for (let f = f0; f < f1; f++) {
          const t = f / FPS;
          await p.evaluate(([tt, s]) => window.R.frame(tt, s), [tStart + t, clip.fn(t)]);
          const buf = await p.screenshot({ type: 'jpeg', quality: 95, timeout: 0 });
          if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
          if (f % 30 === 0) console.log(clip.name, f, '/', n, ((Date.now() - t0) / (f - f0 + 1) / 1000).toFixed(2), 's/frame');
        }
        ff.stdin.end(); await new Promise(r => ff.on('close', r));
        console.log('done', file, ((Date.now() - t0) / 1000).toFixed(0), 's');
      }
    }
    tStart += clip.dur - XF;
  }
  await b.close(); srv.close();
})();
