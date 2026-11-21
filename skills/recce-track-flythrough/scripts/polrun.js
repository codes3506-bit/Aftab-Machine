// Runs the user's POL Calculator engine (calc() and standards, extracted verbatim) on a project JSON.
const fs=require('fs');
const src=fs.readFileSync(__dirname+'/../src/pol.js','utf8');
const lines=src.split('\n');
const engine=lines.slice(0,4).join('\n')+'\n'+src.slice(src.indexOf('/* ---------------- ENGINE'),src.indexOf('const cap='))+src.slice(src.indexOf('const cap='),src.indexOf('function ditch'))+src.slice(src.indexOf('function ditch')).split('\n').slice(0,2).join('\n');
const pre='const n=v=>{v=parseFloat(v);return isFinite(v)?v:0}, f0=x=>Math.round(x).toLocaleString("en-US"), f1=x=>(Math.round(x*100)/100).toLocaleString("en-US");const fq=x=>Number.isInteger(x)?f0(x):f1(x);let S,OTH;';
const fn=new Function('p',pre+engine.replace('const DEF=','var DEF=')+';S={...DEF,...(p.S||{})};OTH={...DEF_OTH};return calc(p);');
const p=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const r=fn(p); fs.writeFileSync(process.argv[3],JSON.stringify(r,null,1));
console.log('TOTAL',r.total,'days',r.dur); r.rows.forEach(x=>console.log(x.d,'|',x.q,x.au,'|',x.rate,'|',x.l,'|',x.rm)); console.log(r.days);
