// 第二轮：星级到底跟什么走 —— 层级（维度）还是稀有度
const fs = require('fs');
const D = JSON.parse(fs.readFileSync('data.json', 'utf8'));
const rows = JSON.parse(fs.readFileSync('_soul_rows.json', 'utf8'));
const N = rows.nd, S = D.SOUL_SCORE_DB;
const daysOf = {}; rows.rows.forEach(r => daysOf[r.g] = r.days);
const starVal = s => (s.indexOf('+') >= 0 ? 5.5 : (s.match(/★/g) || []).length);
const rarScore = d => 100 * Math.log(N / d) / Math.log(N);

// 维度带排序（原书层级文本里的维度）
const BAND = [
  ['特殊课题组', 0],
  ['基础职能层', 1],
  ['多魂后天精英层', 2],
  ['先天童子体系', 3],
  ['多维创世管理层', 4],
  ['先天神圣本源', 5],
];
const bandOf = lv => { for (const [k, v] of BAND) if (lv.indexOf(k) >= 0) return v; return -1; };

const pts = rows.labelled.map(x => x.g).filter(g => daysOf[g] !== undefined).map(g => ({
  g, days: daysOf[g], star: starVal(S[g].stars), level: S[g].level, band: bandOf(S[g].level), name: S[g].name
}));

const mean = a => a.reduce((x, y) => x + y) / a.length;
function avgRank(a) {
  const idx = a.map((v, i) => [v, i]).sort((p, q) => p[0] - q[0]);
  const r = new Array(a.length); let i = 0;
  while (i < idx.length) { let j = i; while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++;
    const avg = (i + j) / 2 + 1; for (let k = i; k <= j; k++) r[idx[k][1]] = avg; i = j + 1; }
  return r;
}
function pearson(x, y) {
  const n = x.length, mx = mean(x), my = mean(y);
  let sxy = 0, sxx = 0, syy = 0;
  for (let i = 0; i < n; i++) { const a = x[i] - mx, b = y[i] - my; sxy += a * b; sxx += a * a; syy += b * b; }
  return sxy / Math.sqrt(sxx * syy);
}
const spearman = (x, y) => pearson(avgRank(x), avgRank(y));

console.log('样本 ' + pts.length + ' 条\n');

/* ---- A. 单调性：低维度条目的星级会不会高过高维度条目 ---- */
console.log('=== A. 维度带 ⇄ 星级 是否单调（两两对拍） ===');
let disc = 0, tie = 0, conc = 0;
for (let i = 0; i < pts.length; i++) for (let j = i + 1; j < pts.length; j++) {
  const a = pts[i], b = pts[j];
  if (a.band === b.band) continue;
  const hi = a.band > b.band ? a : b, lo = a.band > b.band ? b : a;
  if (hi.star > lo.star) conc++;
  else if (hi.star < lo.star) disc++;
  else tie++;
}
console.log('  高维带星级更高（一致）=' + conc + '   相等=' + tie + '   高维带星级更低（违反）=' + disc);
console.log('  违反对总数 = ' + disc + ' / ' + (conc + tie + disc) + ' = ' + (100 * disc / (conc + tie + disc)).toFixed(2) + '%');

/* ---- B. 用维度带预测星级：准确率 ---- */
console.log('\n=== B. 只用「维度带」预测星级（不碰天数） ===');
const modeOf = {};
BAND.forEach(([k, v]) => {
  const v2 = pts.filter(p => p.band === v).map(p => p.star);
  if (!v2.length) return;
  const c = {}; v2.forEach(s => c[s] = (c[s] || 0) + 1);
  let best = null, bn = -1;
  Object.keys(c).forEach(s => { if (c[s] > bn) { bn = c[s]; best = +s; } });
  modeOf[v] = { mode: best, n: v2.length, hit: bn, mean: mean(v2) };
  console.log('  ' + k.padEnd(18) + ' n=' + String(v2.length).padStart(2) +
    '  众数 ' + best + '★ 命中 ' + bn + '/' + v2.length +
    ' = ' + (100 * bn / v2.length).toFixed(0) + '%  均值 ' + mean(v2).toFixed(2));
});
let hit = 0, within1 = 0;
pts.forEach(p => { if (modeOf[p.band] && modeOf[p.band].mode === p.star) hit++;
  if (modeOf[p.band] && Math.abs(modeOf[p.band].mode - p.star) <= 1) within1++; });
console.log('  ⟹ 总体：完全命中 ' + hit + '/' + pts.length + ' = ' + (100 * hit / pts.length).toFixed(1) +
  '%   ±1 星内 ' + within1 + '/' + pts.length + ' = ' + (100 * within1 / pts.length).toFixed(1) + '%');
console.log('  Spearman(维度带, 星级) = ' + spearman(pts.map(p => p.band), pts.map(p => p.star)).toFixed(4));

/* ---- C. 同样的方法用稀有度分预测星级 ---- */
console.log('\n=== C. 用「稀有度分」分 6 档预测星级（对照组） ===');
const sortedRar = pts.map(p => rarScore(p.days)).sort((a, b) => a - b);
const cuts = [0, 1, 2, 3, 4, 5].map(k => sortedRar[Math.floor(k * sortedRar.length / 6)]);
const rarBand = d => { const s = rarScore(d); let b = 0; for (let i = 0; i < 6; i++) if (s >= cuts[i]) b = i; return b; };
const rMode = {};
pts.forEach(p => { const b = rarBand(p.days); (rMode[b] = rMode[b] || []).push(p.star); });
let rhit = 0, r1 = 0;
Object.keys(rMode).forEach(b => {
  const v = rMode[b], c = {}; v.forEach(s => c[s] = (c[s] || 0) + 1);
  let best = null, bn = -1; Object.keys(c).forEach(s => { if (c[s] > bn) { bn = c[s]; best = +s; } });
  console.log('  第' + (+b + 1) + '档 n=' + String(v.length).padStart(2) + '  众数 ' + best + '★ 命中 ' +
    bn + '/' + v.length + ' = ' + (100 * bn / v.length).toFixed(0) + '%  均值 ' + mean(v).toFixed(2));
  rhit += bn; v.forEach(s => { if (Math.abs(best - s) <= 1) r1++; });
});
console.log('  ⟹ 总体：完全命中 ' + rhit + '/' + pts.length + ' = ' + (100 * rhit / pts.length).toFixed(1) +
  '%   ±1 星内 ' + r1 + '/' + pts.length + ' = ' + (100 * r1 / pts.length).toFixed(1) + '%');

/* ---- D. 剔除层级后，稀有度还剩多少解释力（只在高频档内部看） ---- */
console.log('\n=== D. 控制层级后，稀有度还有没有残余作用 ===');
BAND.forEach(([k, v]) => {
  const sub = pts.filter(p => p.band === v);
  if (sub.length < 6) return;
  const d = sub.map(p => p.days), s = sub.map(p => p.star);
  const sd = new Set(s).size;
  console.log('  ' + k.padEnd(18) + ' n=' + String(sub.length).padStart(2) +
    '  星级取值 ' + sd + ' 种' +
    '  Spearman(天数,星级) = ' + (sd < 2 ? '——（星级全同，无方差）' : spearman(d, s).toFixed(3)));
});

/* ---- E. 库的选区偏差 ---- */
console.log('\n=== E. 选区偏差：库里收的是常见格还是稀有格 ===');
const allD = rows.rows.map(r => r.days);
console.log('  71 条中位天数 ' + pts.map(p => p.days).sort((a, b) => a - b)[Math.floor(pts.length / 2)] +
  ' 天 ；605 种中位 ' + allD.slice().sort((a, b) => a - b)[Math.floor(allD.length / 2)] + ' 天');
const gr = d => { const s = rarScore(d); return s >= 82 ? '极稀' : s >= 74 ? '稀有' : s >= 64 ? '少见' : s >= 52 ? '常见' : '高频'; };
const cntAll = {}, cntLib = {};
allD.forEach(d => cntAll[gr(d)] = (cntAll[gr(d)] || 0) + 1);
pts.forEach(p => cntLib[gr(p.days)] = (cntLib[gr(p.days)] || 0) + 1);
['极稀', '稀有', '少见', '常见', '高频'].forEach(k => {
  console.log('  ' + k.padEnd(3) + ' 全区间 ' + String(cntAll[k] || 0).padStart(3) + ' 种（' +
    (100 * (cntAll[k] || 0) / allD.length).toFixed(0) + '%）  库内 ' + String(cntLib[k] || 0).padStart(2) + ' 条（' +
    (100 * (cntLib[k] || 0) / pts.length).toFixed(0) + '%）');
});
console.log('  ⟹ 全区间 605 种里有 ' + (cntAll['极稀'] + cntAll['稀有']) + ' 种是稀有/极稀（占 ' +
  (100 * (cntAll['极稀'] + cntAll['稀有']) / allD.length).toFixed(0) + '%），库却只收了 ' +
  (cntLib['极稀'] + cntLib['稀有']) + ' 条 ⟹ 星际相关性被「选区」压掉了');
