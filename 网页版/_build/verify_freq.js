/* 用页面自己的 JS 引擎重跑 1910–2101 逐日统计，与 Python 实算的 freq.json / freq_joint.json 全量比对 */
const fs = require('fs');
const path = require('path');
const dir = __dirname;

eval(fs.readFileSync(path.join(dir, 'src/engine.js'), 'utf8'));
const M = globalThis.MAGIC;
M.lunarInit(JSON.parse(fs.readFileSync(path.join(dir, 'lunar_table.json'), 'utf8')));

const f = JSON.parse(fs.readFileSync(path.join(dir, 'freq.json'), 'utf8'));
const jt = JSON.parse(fs.readFileSync(path.join(dir, 'freq_joint.json'), 'utf8'));

const yg = {}, ig = {}, pair = {};
let n = 0, fail = 0;
const pad = x => String(x).padStart(2, '0');

for (let y = 1910; y <= 2101; y++) {
  for (let m = 1; m <= 12; m++) {
    const dim = new Date(Date.UTC(y, m, 0)).getUTCDate();
    for (let d = 1; d <= dim; d++) {
      const r = M.calc(y + '/' + pad(m) + '/' + pad(d), '午时', 'male', 'v5');
      if (!r || !r.yang) { fail++; continue; }
      yg[r.yang] = (yg[r.yang] || 0) + 1;
      ig[r.yin] = (ig[r.yin] || 0) + 1;
      const k = r.yang + '|' + r.yin;
      pair[k] = (pair[k] || 0) + 1;
      n++;
    }
  }
}

let ok = 0, bad = 0;
function chk(tag, a, b) {
  if (String(a) === String(b)) { ok++; return; }
  bad++;
  if (bad <= 12) console.log('  ✗ ' + tag + '  JS=' + a + '  PY=' + b);
}

console.log('JS 天数 ' + n + ' | Python 天数 ' + f.days + ' | 失败 ' + fail);
chk('天数', n, f.days);
chk('阳格种数', Object.keys(yg).length, Object.keys(f.yang).length);
chk('阴格种数', Object.keys(ig).length, Object.keys(f.yin).length);
chk('阳格合计', Object.values(yg).reduce((a, b) => a + b, 0), Object.values(f.yang).reduce((a, b) => a + b, 0));
chk('阴格合计', Object.values(ig).reduce((a, b) => a + b, 0), Object.values(f.yin).reduce((a, b) => a + b, 0));

/* 逐格比对 */
const allY = new Set(Object.keys(yg).concat(Object.keys(f.yang)));
allY.forEach(k => chk('阳格 ' + k, yg[k] || 0, f.yang[k] || 0));
const allI = new Set(Object.keys(ig).concat(Object.keys(f.yin)));
allI.forEach(k => chk('阴格 ' + k, ig[k] || 0, f.yin[k] || 0));

/* 联合分布：map / hist / single */
const jm = jt.map, hist = {};
Object.values(pair).forEach(c => { hist[c] = (hist[c] || 0) + 1; });
chk('联合去重种数', Object.keys(pair).length, Object.keys(hist).reduce((a, c) => a + hist[c], 0));
chk('单次组合数', (hist[1] || 0), jt.single);
Object.keys(hist).forEach(c => chk('直方图 ' + c + ' 次', hist[c], jt.hist[c] || 0));
let mapBad = 0;
Object.keys(jm).forEach(k => { if (pair[k] !== jm[k]) mapBad++; });
chk('map 项数', Object.keys(jm).length, Object.keys(pair).filter(k => pair[k] >= 2).length);
chk('map 内容不一致项', mapBad, 0);

console.log('★ 比对 ' + (ok + bad) + ' 项   OK ' + ok + ' / FAIL ' + bad);
process.exitCode = bad ? 1 : 0;
