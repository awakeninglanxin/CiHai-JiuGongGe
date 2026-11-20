// 分析：阳格结构特征 vs 灵魂库星级，检验是否存在可外推的通项
// 用法：node analyze_soul_rule.js
const fs = require('fs');
const path = require('path');

const HERE = __dirname;
require(path.join(HERE, 'src', 'engine.js'));
const M = globalThis.MAGIC;

const lunar = JSON.parse(fs.readFileSync(path.join(HERE, 'lunar_table.json'), 'utf8'));
M.lunarInit(lunar);
const D = JSON.parse(fs.readFileSync(path.join(HERE, 'data.json'), 'utf8'));
const DB = D.SOUL_SCORE_DB;

function val(st) { return st.indexOf('+') >= 0 ? 5.5 : st.split('').filter(c => c === '★').length; }

// 遍历全区间，收集 阳格 -> {days, 结构特征集合}
const start = D.FREQ.start, end = D.FREQ.end;
const map = new Map();
let nd = 0;
let d = M.parseDate(start);
const END = M.parseDate(end);
while (true) {
  const y = d.y, mo = d.m, da = d.d;
  const g = M.yangCalc(y, mo, da);
  const k = g.grid;
  let rec = map.get(k);
  if (!rec) {
    const po = [];
    String(y).split('').forEach(c => po.push(+c));
    String(mo).padStart(2, '0').split('').forEach(c => po.push(+c));
    String(da).padStart(2, '0').split('').forEach(c => po.push(+c));
    rec = { grid: k, days: 0, route: g.route, main: g.main, up: g.up.slice(), parts: g.parts.slice(),
            tot: po.reduce((a, b) => a + b, 0), poLen: po.length, sample: `${y}-${mo}-${da}` };
    map.set(k, rec);
  }
  rec.days++;
  nd++;
  // 下一天
  const dt = new Date(Date.UTC(y, mo - 1, da));
  dt.setUTCDate(dt.getUTCDate() + 1);
  d = { y: dt.getUTCFullYear(), m: dt.getUTCMonth() + 1, d: dt.getUTCDate() };
  if (d.y > END.y || (d.y === END.y && (d.m > END.m || (d.m === END.m && d.d > END.d)))) break;
}

const rows = Array.from(map.values());
console.log(`区间 ${start} … ${end}  天数 ${nd}  阳格种类 ${rows.length}`);

// 覆盖率
const labelled = rows.filter(r => DB[r.grid]);
const labelledDays = labelled.reduce((a, r) => a + r.days, 0);
console.log(`已收录阳格 ${labelled.length} / ${rows.length} = ${(100 * labelled.length / rows.length).toFixed(1)}%`);
console.log(`按天数覆盖 ${labelledDays} / ${nd} = ${(100 * labelledDays / nd).toFixed(2)}%`);

// 特征 -> 星级 的可分性
function group(fn, name) {
  const g = new Map();
  labelled.forEach(r => {
    const key = fn(r);
    if (!g.has(key)) g.set(key, []);
    g.get(key).push(val(DB[r.grid].stars));
  });
  let pure = 0, tot = 0, wspan = 0;
  const detail = [];
  Array.from(g.keys()).sort().forEach(k => {
    const v = g.get(k);
    const set = Array.from(new Set(v)).sort();
    tot += v.length;
    if (set.length === 1) pure += v.length;
    wspan = Math.max(wspan, set[set.length - 1] - set[0]);
    detail.push(`    ${String(k).padEnd(14)} n=${String(v.length).padStart(2)} 星级${JSON.stringify(set)}`);
  });
  console.log(`\n[${name}] 分组 ${g.size} 个 · 组内纯度高(=组内星级全同) ${pure}/${tot} = ${(100 * pure / tot).toFixed(1)}% · 最大组内跨度 ${wspan}`);
  detail.forEach(x => console.log(x));
  return { pure, tot, span: wspan };
}

console.log('\n================ 特征判别力（仅用 71 个已标注阳格）================');
group(r => r.route, 'route 路线');
group(r => 'len=' + r.grid.length, '位数');
group(r => 'main=' + r.main, '数字根 main');
group(r => 'len+main=' + r.grid.length + '/' + r.main, '位数+数字根');
group(r => 'up=' + (r.up.length || 'none'), '升级魂个数');
group(r => 'len+up=' + r.grid.length + '/' + (r.up.length || 0), '位数+升级魂个数');

// 同核心（剥前导零）分组
group(r => r.grid.replace(/^0+/, ''), '剥前导零后的核心串');

// 输出未收录阳格按天数排序的头部
const un = rows.filter(r => !DB[r.grid]).sort((a, b) => b.days - a.days);
console.log(`\n================ 未收录阳格 ${un.length} 个，按出现天数前 20 ================`);
un.slice(0, 20).forEach(r => {
  console.log(`  ${r.grid.padEnd(10)} ${String(r.days).padStart(5)}天  ${(100 * r.days / nd).toFixed(2)}%  route=${r.route} len=${r.grid.length} main=${r.main} up=${r.up.join('') || '-'} parts=${r.parts.join('|')}`);
});

// 输出结构化结果供 python 进一步用
fs.writeFileSync(path.join(HERE, '_soul_rows.json'), JSON.stringify({
  nd, rows: rows.map(r => ({ g: r.grid, days: r.days, route: r.route, main: r.main, up: r.up, parts: r.parts, tot: r.tot })),
  labelled: rows.filter(r => DB[r.grid]).map(r => ({ g: r.grid, days: r.days, stars: DB[r.grid].stars, level: DB[r.grid].level, name: DB[r.grid].name }))
}, null, 0), 'utf8');
console.log('\n已写出 _soul_rows.json');
