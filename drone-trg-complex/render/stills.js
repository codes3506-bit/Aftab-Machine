// node render/stills.js out_prefix '[{"t":0,"eye":[..],"look":[..]}...]'  -> PNG stills via headless Chromium
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..');
const W = +(process.env.W || 1280), H = +(process.env.H || 720);
(async () => {
  const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'application/javascript' : f.endsWith('.json') ? 'application/json' : 'application/octet-stream' }); r.end(d); } }); }).listen(8765);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: W, height: H } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto(`http://localhost:8765/render/viewer.html?headless=1&w=${W}&h=${H}`);
  await p.waitForFunction('window.R && window.R.ready', null, { timeout: 120000 });
  const shots = JSON.parse(process.argv[3]);
  for (let i = 0; i < shots.length; i++) {
    const t0 = Date.now();
    await p.evaluate(s => window.R.frame(s.t || 0, s), shots[i]);
    await p.screenshot({ path: `${process.argv[2]}_${i}.png` });
    console.log('shot', i, Date.now() - t0, 'ms');
  }
  console.log('errors', errs);
  await b.close(); srv.close();
})();
