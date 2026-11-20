// 灵魂库查表口径校验：改完必须全绿
// 用法：node verify_soul.js
const fs = require('fs');
const path = require('path');
const HERE = __dirname;
require(path.join(HERE, 'src', 'engine.js'));
const M = globalThis.MAGIC;
M.lunarInit(JSON.parse(fs.readFileSync(path.join(HERE, 'lunar_table.json'), 'utf8')));
const D = JSON.parse(fs.readFileSync(path.join(HERE, 'data.json'), 'utf8'));
const DB = D.SOUL_SCORE_DB, SV = D.SOUL_DB;
const rows = JSON.parse(fs.readFileSync(path.join(HERE, '_soul_rows.json'), 'utf8'));
const N = rows.nd;

let ok = 0, fail = 0;
function t(name, cond, extra) {
  if (cond) { ok++; }
  else { fail++; console.log('  FAIL ' + name + (extra ? '  ' + extra : '')); }
}

/* ── 1. 三态计数 ── */
const tally = {}, days = {};
rows.rows.forEach(r => {
  const x = M.lookupSoulScore(r.g, DB);
  const how = x ? x.conf : 'null';
  tally[how] = (tally[how] || 0) + 1;
  days[how] = (days[how] || 0) + r.days;
});
console.log('SOUL_SCORE_DB 三态：');
['exact', 'same-root', 'near', 'null'].forEach(k => {
  console.log(`  ${k.padEnd(10)} 种类 ${String(tally[k] || 0).padStart(3)}  天数 ${String(days[k] || 0).padStart(5)}  ${(100 * (days[k] || 0) / N).toFixed(2)}%`);
});
t('exact 应为 71 种', tally['exact'] === 71, String(tally['exact']));
t('same-root 应为 17 种', tally['same-root'] === 17, String(tally['same-root']));
t('near 应为 173 种', tally['near'] === 173, String(tally['near']));
t('null 应为 344 种', tally['null'] === 344, String(tally['null']));
t('三态合计 605', (tally['exact'] || 0) + (tally['same-root'] || 0) + (tally['near'] || 0) + (tally['null'] || 0) === 605);
t('exact 天数 37593', days['exact'] === 37593, String(days['exact']));
t('near 天数 4946（原误配规模）', days['near'] === 4946, String(days['near']));

/* ── 2. 不变量：near 绝不给星级 / 名称 ── */
let nearBad = 0, exactKeyDrift = 0;
rows.rows.forEach(r => {
  const x = M.lookupSoulScore(r.g, DB);
  if (x && x.conf === 'near') {
    if (x.rec !== null || x.key !== null) nearBad++;
    if (!x.near || !x.near.key) nearBad++;
  }
  if (x && x.conf === 'exact' && x.key !== r.g) exactKeyDrift++;
});
t('near 必须 rec=null 且 key=null', nearBad === 0, '违例 ' + nearBad);
t('exact 必须 key===输入', exactKeyDrift === 0, '违例 ' + exactKeyDrift);

/* ── 3. 反例锁死（原误配现场） ── */
const cases = [
  ['02167', 'near'], ['02145', 'near'], ['02134', 'near'], ['02189', 'near'],
  ['02178', 'near'], ['02123', 'near'], ['02112', 'near'],
  ['1246', 'near'], ['1235', 'near'], ['2246', 'near'], ['1347', 'near'],
  ['0213', 'same-root'], ['0189', 'same-root'], ['0235', 'same-root'], ['0112', 'same-root'],
  ['033393', 'exact'], ['0123', 'exact'], ['19101', 'exact'], ['0314', 'exact'],
];
cases.forEach(([g, want]) => {
  const x = M.lookupSoulScore(g, DB);
  const got = x ? x.conf : 'null';
  t(`lookupSoulScore('${g}') 应为 ${want}`, got === want, '实际 ' + got);
});
// 具体到「不再是 0219101」
const p = M.lookupSoulScore('02167', DB);
t('02167 不得再判成 0219101', !(p && p.rec && p.rec.name.indexOf('一清') >= 0), p && p.rec ? p.rec.name : 'ok');
const q = M.lookupSoulScore('1246', DB);
t('1246 不得再判成新维度播种玉皇', !(q && q.rec && q.rec.name.indexOf('新维度') >= 0), q && q.rec ? q.rec.name : 'ok');
// 剥零推定仍要给出正确同源
const s = M.lookupSoulScore('0213', DB);
t('0213 剥零应指向 213', s && s.key === '213', s ? s.key : 'null');
t('0213 剥零星级应为 ★★★☆☆', s && s.rec.stars === '★★★☆☆', s && s.rec ? s.rec.stars : 'null');

/* ── 4. 精确命中必须与原库逐字一致 ── */
let drift = 0;
Object.keys(DB).forEach(k => {
  const x = M.lookupSoulScore(k, DB);
  if (!x || x.conf !== 'exact' || x.rec !== DB[k]) drift++;
});
t('82 个 key 自身必须 exact 且对象同一', drift === 0, '违例 ' + drift);

/* ── 5. SOUL_DB 同口径 ── */
const t2 = {}, d2 = {};
rows.rows.forEach(r => {
  const x = M.lookupSoulV5(r.g, SV);
  const how = x ? x.conf : 'null';
  t2[how] = (t2[how] || 0) + 1;
  d2[how] = (d2[how] || 0) + r.days;
});
console.log('SOUL_DB 三态：');
Object.keys(t2).sort().forEach(k => console.log(`  ${k.padEnd(10)} 种类 ${String(t2[k]).padStart(3)}  天数 ${String(d2[k] || 0).padStart(5)}`));
t('SOUL_DB exact 应为 57 种', t2['exact'] === 57, String(t2['exact']));
t('SOUL_DB near 应为 159 种', t2['near'] === 159, String(t2['near']));
let v5bad = 0;
rows.rows.forEach(r => {
  const x = M.lookupSoulV5(r.g, SV);
  if (x && x.conf === 'near' && (x.rec !== null || x.key !== null)) v5bad++;
});
t('SOUL_DB near 必须 rec=null', v5bad === 0, '违例 ' + v5bad);
t("lookupSoulV5('1235') 不得给出名字", (() => { const x = M.lookupSoulV5('1235', SV); return !(x && x.rec); })());

/* ── 6. 天数为 0 的异常（防止把 605 算错） ── */
const sumd = rows.rows.reduce((a, r) => a + r.days, 0);
t('阳格天数合计 = 70127', sumd === 70127, String(sumd));

/* ── 7. 报告层：毒格不得出现误配名（引擎层对了不代表报告层对了） ── */
eval(fs.readFileSync(path.join(HERE, 'src', 'reports.js'), 'utf8'));
const NOW = new Date(2026, 9, 27, 10, 5, 0);
function findDate(target, y0, y1) {
  for (let y = y0; y <= y1; y++) for (let m = 1; m <= 12; m++) for (let d = 1; d <= 28; d++) {
    if (M.yangCalc(y, m, d).grid === target) {
      return y + '/' + String(m).padStart(2, '0') + '/' + String(d).padStart(2, '0');
    }
  }
  return null;
}
[['1246', '新维度'], ['02167', '一清'], ['1235', '大心神'], ['1347', '134系列']].forEach(function (pr) {
  const g = pr[0], bad = pr[1];
  const dt = findDate(g, 1980, 2015);
  t('能构造 ' + g + ' 的日期', !!dt, String(dt));
  if (!dt) return;
  let md;
  try {
    md = M.REPORTS.comprehensive(Object.assign({}, D, {
      name: '毒格', birth: dt, shichen: '午时', gender: 'male',
      location: '深圳', now: NOW, targetDate: '2026/10/27', rule: 'book'
    }));
  } catch (e) { md = 'ERR ' + e.message; }
  t('报告不含「' + bad + '」(' + g + ' @' + dt + ')', md.indexOf(bad) < 0,
    md.indexOf(bad) >= 0 ? '报告里出现了' : '');
  t('报告不是异常(' + g + ')', md.indexOf('ERR ') !== 0, md.slice(0, 60));
});

console.log(`\n灵魂库口径校验：OK ${ok} / FAIL ${fail}`);
process.exit(fail ? 1 : 0);
