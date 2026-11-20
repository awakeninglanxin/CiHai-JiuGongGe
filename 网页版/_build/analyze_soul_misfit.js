// 检验：现有 lookupSoulScore 的模糊兜底在 605 个真实阳格上会造成多少误配
const fs = require('fs');
const path = require('path');
const HERE = __dirname;
require(path.join(HERE, 'src', 'engine.js'));
const M = globalThis.MAGIC;

const lunar = JSON.parse(fs.readFileSync(path.join(HERE, 'lunar_table.json'), 'utf8'));
M.lunarInit(lunar);
const D = JSON.parse(fs.readFileSync(path.join(HERE, 'data.json'), 'utf8'));
const DB = D.SOUL_SCORE_DB;
const N = D.FREQ.days;

const rows = JSON.parse(fs.readFileSync(path.join(HERE, '_soul_rows.json'), 'utf8'));
console.log(`阳格 ${rows.rows.length} 种，总天数 ${rows.nd}`);

const DB_KEYS = Object.keys(DB);
function classify(g) {
  if (DB[g]) return ['exact', g];
  if (/^\d+$/.test(g)) {
    const st = String(parseInt(g, 10));
    if (st !== g && DB[st]) return ['strip0-int', st];
  }
  const s2 = g.replace(/^0+/, '');
  if (s2 !== g && DB[s2]) return ['strip0-lstrip', s2];
  for (const k of DB_KEYS) if (g.indexOf(k) === 0 || k.indexOf(g) === 0) return ['prefix', k];
  if (g.length >= 4) {
    const pre3 = g.slice(0, 3);
    for (const k of DB_KEYS) if (k.indexOf(pre3) === 0) return ['pre3', k];
  }
  return ['null', null];
}

const tally = {};
let daysByPath = {};
for (const r of rows.rows) {
  const [how, key] = classify(r.g);
  tally[how] = (tally[how] || 0) + 1;
  daysByPath[how] = (daysByPath[how] || 0) + r.days;
  r.how = how; r.hitKey = key;
}
console.log('\n--- 605 个阳格的命中路径 ---');
Object.keys(tally).sort().forEach(h => {
  console.log(`  ${h.padEnd(14)} 种类 ${String(tally[h]).padStart(3)}  天数 ${String(daysByPath[h]).padStart(5)}  (${(100 * daysByPath[h] / N).toFixed(2)}%)`);
});
const bogus = (daysByPath['prefix'] || 0) + (daysByPath['pre3'] || 0);
console.log(`\n★ 靠「前缀 / 前3位」兜底给出的答案：${bogus} 天 = ${(100 * bogus / N).toFixed(2)}% —— 这些是最可疑的静默误配`);

console.log('\n--- pre3 / prefix 误配清单（按天数降序，前 25）---');
rows.rows.filter(r => r.how === 'prefix' || r.how === 'pre3')
  .sort((a, b) => b.days - a.days).slice(0, 25)
  .forEach(r => {
    const x = DB[r.hitKey];
    const alsoReal = !!rows.rows.find(q => q.g === r.hitKey);
    console.log(`  ${r.g.padEnd(10)} ${String(r.days).padStart(5)}天 ${(100 * r.days / N).toFixed(2)}%  ->  ${r.hitKey.padEnd(9)}「${x.name}」${x.stars} ${x.level}${alsoReal ? '  [命中的 key 本身也是真实阳格，含义不同]' : ''}`);
  });

console.log('\n--- strip0 误配清单（前 15）---');
rows.rows.filter(r => r.how.indexOf('strip0') === 0)
  .sort((a, b) => b.days - a.days).slice(0, 15)
  .forEach(r => {
    const x = DB[r.hitKey];
    console.log(`  ${r.g.padEnd(10)} ${String(r.days).padStart(5)}天  ->  ${r.hitKey.padEnd(9)}「${x.name}」${x.stars}`);
  });

// 星级 vs 稀有度
console.log('\n--- 星级 vs 该格出现天数 ---');
const lab = rows.labelled.map(r => {
  const g = r.g;
  return { g, days: r.days, stars: DB[g].stars.indexOf('+') >= 0 ? 5.5 : DB[g].stars.split('').filter(c => c === '★').length };
}).sort((a, b) => a.days - b.days);
// Spearman
function rank(arr) {
  const idx = arr.map((v, i) => [v, i]).sort((a, b) => a[0] - b[0]);
  const rk = new Array(arr.length);
  let i = 0;
  while (i < idx.length) {
    let j = i;
    while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++;
    const avg = (i + j) / 2 + 1;
    for (let k = i; k <= j; k++) rk[idx[k][1]] = avg;
    i = j + 1;
  }
  return rk;
}
const ra = rank(lab.map(x => x.days)), rb = rank(lab.map(x => x.stars));
const n = lab.length;
const mean = a => a.reduce((x, y) => x + y, 0) / a.length;
const ma = mean(ra), mb = mean(rb);
let num = 0, da = 0, db = 0;
for (let i = 0; i < n; i++) { num += (ra[i] - ma) * (rb[i] - mb); da += (ra[i] - ma) ** 2; db += (rb[i] - mb) ** 2; }
console.log(`  Spearman ρ(天数, 星级) = ${(num / Math.sqrt(da * db)).toFixed(3)}  n=${n}`);

// 各星级的天数分布
const byStar = {};
lab.forEach(x => { (byStar[x.stars] = byStar[x.stars] || []).push(x.days); });
Object.keys(byStar).sort((a, b) => a - b).forEach(s => {
  const v = byStar[s].sort((a, b) => a - b);
  console.log(`  ${s} 星 n=${String(v.length).padStart(2)} 天数中位 ${v[Math.floor(v.length / 2)]}  范围 ${v[0]}~${v[v.length - 1]}`);
});
