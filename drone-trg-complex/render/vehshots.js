const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..'), OUT = process.argv[2], shots = JSON.parse(process.argv[3]);
(async () => {
  const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'Content-Type': f.endsWith('.js') ? 'application/javascript' : 'text/html' }); r.end(d); } }); }).listen(8711);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 960, height: 600 } }); p.on('pageerror', e => console.error('ERR', e.message)); p.on('console', m => { if (m.type() === 'error') console.error('CON', m.text()); });
  for (const [name, qs] of shots) { await p.goto('http://localhost:8711/render/vehtest.html?' + qs); await p.waitForFunction('window.done', null, { timeout: 60000 }).catch(e => console.error(name, e.message)); await p.screenshot({ path: path.join(OUT, name + '.png') }); }
  await b.close(); srv.close();
})();
