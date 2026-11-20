// 灵魂积分「星级」与「稀有度」到底有没有关系 —— 全部量化，不做印象判断
const fs = require('fs');
const D = JSON.parse(fs.readFileSync('data.json', 'utf8'));
const rows = JSON.parse(fs.readFileSync('_soul_rows.json', 'utf8'));
const N = rows.nd;                       // 70,127 天
const S = D.SOUL_SCORE_DB;

const daysOf = {};
rows.rows.forEach(r => daysOf[r.g] = r.days);

const starVal = s => (s.indexOf('+') >= 0 ? 5.5 : (s.match(/★/g) || []).length);
const rarScore = d => 100 * Math.log(N / d) / Math.log(N);      // 页面第 9 页的子分 S

const lab = rows.labelled.map(x => x.g).filter(g => daysOf[g] !== undefined);
const pts = lab.map(g => ({
  g, days: daysOf[g], star: starVal(S[g].stars), level: S[g].level, name: S[g].name
}));

/* ---------- 统计工具（秩用平均秩，处理并列） ---------- */
function avgRank(a) {
  const idx = a.map((v, i) => [v, i]).sort((p, q) => p[0] - q[0]);
  const r = new Array(a.length);
  let i = 0;
  while (i < idx.length) {
    let j = i;
    while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++;
    const avg = (i + j) / 2 + 1;
    for (let k = i; k <= j; k++) r[idx[k][1]] = avg;
    i = j + 1;
  }
  return r;
}
function pearson(x, y, rx, ry) {
  const n = x.length;
  const mx = x.reduce((a, b) => a + b) / n, my = y.reduce((a, b) => a + b) / n;
  let sxy = 0, sxx = 0, syy = 0;
  for (let i = 0; i < n; i++) { const a = x[i] - mx, b = y[i] - my; sxy += a * b; sxx += a * a; syy += b * b; }
  return sxy / Math.sqrt(sxx * syy);
}
const spearman = (x, y) => pearson(avgRank(x), avgRank(y));
// 置换检验：打乱星级，看 |rho| 超过观测值的比例（20000 次）
function permP(x, y, obs, times) {
  const M = Math.abs(obs); let hit = 0;
  const yy = y.slice();
  for (let t = 0; t < times; t++) {
    for (let i = yy.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1));[yy[i], yy[j]] = [yy[j], yy[i]]; }
    if (Math.abs(spearman(x, yy)) >= M) hit++;
  }
  return hit / times;
}

/* ---------- 1. 两个相关系数 ---------- */
const days = pts.map(p => p.days), stars = pts.map(p => p.star), rar = pts.map(p => rarScore(p.days));
const rDays = spearman(days, stars), rRar = spearman(rar, stars);
console.log('样本：82 条中既合法阳格又能统计天数的 =', pts.length, '条\n');
console.log('=== 1. 星级 vs 稀有度 ===');
console.log('  Pearson (天数 vs 星级)      =', pearson(days, stars).toFixed(4));
console.log('  Spearman(天数 vs 星级)      =', rDays.toFixed(4), ' 置换检验 p =', permP(days, stars, rDays, 20000).toFixed(4));
console.log('  Pearson (稀有度分 vs 星级)  =', pearson(rar, stars).toFixed(4));
console.log('  Spearman(稀有度分 vs 星级)  =', rRar.toFixed(4), ' 置换检验 p =', permP(rar, stars, rRar, 20000).toFixed(4));
console.log('  （稀有度分是天数的单调减函数，所以两者只是同一个量的两张皮）');

/* ---------- 2. 按页面等级分档，看星级分布 ---------- */
console.log('\n=== 2. 按第 9 页的稀有度等级分档 ===');
const grade = d => {
  const s = rarScore(d);
  return s >= 82 ? '极稀' : s >= 74 ? '稀有' : s >= 64 ? '少见' : s >= 52 ? '常见' : '高频';
};
const buckets = {};
pts.forEach(p => (buckets[grade(p.days)] = buckets[grade(p.days)] || []).push(p.star));
['极稀', '稀有', '少见', '常见', '高频'].forEach(k => {
  const v = buckets[k] || [];
  if (!v.length) { console.log('  ' + k + '：无样本'); return; }
  const m = v.reduce((a, b) => a + b) / v.length;
  console.log('  ' + k.padEnd(3) + '  n=' + String(v.length).padStart(2) +
    '  星级均值 ' + m.toFixed(2) + '  区间 ' + Math.min(...v) + '~' + Math.max(...v) +
    '  明细 [' + v.slice().sort().join(',') + ']');
});

/* ---------- 3. 反过来问：库里是不是偏爱稀有格 ---------- */
console.log('\n=== 3. 库本身是否偏爱稀有格（71 条 vs 全区间 605 种） ===');
const allDays = rows.rows.map(r => r.days);
const mean = a => a.reduce((x, y) => x + y) / a.length;
const med = a => { const s = a.slice().sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
console.log('  已收录 71 条：日均天数 ' + mean(days).toFixed(1) + '  中位 ' + med(days) + '  稀有度分均值 ' + mean(rar).toFixed(1));
console.log('  全区间 605 种：日均天数 ' + mean(allDays).toFixed(1) + '  中位 ' + med(allDays) +
  '  稀有度分均值 ' + mean(allDays.map(rarScore)).toFixed(1));
console.log('  ⟹ 差异 = ' + (mean(rar) - mean(allDays.map(rarScore))).toFixed(1) + ' 分（满分 100）');

/* ---------- 4. 星级同分内部的天数跨度：最能说明问题的一张表 ---------- */
console.log('\n=== 4. 同一星级内部的天数跨度（若星级由稀有度决定，这里应当很窄） ===');
const byStar = {};
pts.forEach(p => (byStar[p.star] = byStar[p.star] || []).push(p));
Object.keys(byStar).map(Number).sort().forEach(k => {
  const v = byStar[k].map(p => p.days).sort((a, b) => a - b);
  const ratio = (v[v.length - 1] / v[0]);
  console.log('  ' + String(k).padEnd(4) + ' n=' + String(v.length).padStart(2) +
    '  天数 ' + String(v[0]).padStart(5) + ' ~ ' + String(v[v.length - 1]).padStart(5) +
    '  最稀有/最常见 = ' + ratio.toFixed(1) + '×');
});

/* ---------- 5. 极端对撞：最稀有 vs 最常见 ---------- */
console.log('\n=== 5. 两端的实际条目 ===');
const sorted = pts.slice().sort((a, b) => a.days - b.days);
console.log('  最稀有 6 条（天数最少）：');
sorted.slice(0, 6).forEach(p => console.log('    ' + p.g.padEnd(8) + String(p.days).padStart(5) + '天  ' +
  '★'.repeat(Math.floor(p.star)) + (p.star % 1 ? '+' : '') + '  ' + p.name + '  [' + p.level + ']'));
console.log('  最常见 6 条（天数最多）：');
sorted.slice(-6).forEach(p => console.log('    ' + p.g.padEnd(8) + String(p.days).padStart(5) + '天  ' +
  '★'.repeat(Math.floor(p.star)) + (p.star % 1 ? '+' : '') + '  ' + p.name + '  [' + p.level + ']'));

/* ---------- 6. 星级到底跟什么走：层级 ---------- */
console.log('\n=== 6. 星级 vs 层级（level 文本里的「维度」） ===');
const lv = {};
pts.forEach(p => (lv[p.level] = lv[p.level] || []).push(p.star));
Object.keys(lv).sort((a, b) => mean(lv[b]) - mean(lv[a])).forEach(k => {
  const v = lv[k];
  console.log('  ' + k.padEnd(34) + ' n=' + String(v.length).padStart(2) +
    '  星级均值 ' + mean(v).toFixed(2) + '  区间 ' + Math.min(...v) + '~' + Math.max(...v));
});
