/* 子时换日口径校验
 *
 * 目的有两个：
 *   ① 锁死原书的判据：前子时取 D+1、后子时取 D−1（《九宫解译历史人物》1-6「子时的人」）
 *   ② 防「AF 那类坑」：页面切换到 query 口径后，三份 .md 报告必须跟着变，
 *      不能出现「子时卡片显示 09336、报告里却写 0314」这种内部打架。
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const HERE = __dirname;
const ctx = { console, JSON, Date, Math, String, Number, Array, Object, parseInt, parseFloat, isNaN };
ctx.globalThis = ctx;
vm.createContext(ctx);
for (const f of ['src/engine.js', 'src/reports.js']) {
  vm.runInContext(fs.readFileSync(path.join(HERE, f), 'utf8'), ctx);
}
const M = ctx.MAGIC;
M.lunarInit(JSON.parse(fs.readFileSync(path.join(HERE, 'lunar_table.json'), 'utf8')));
const D = JSON.parse(fs.readFileSync(path.join(HERE, 'data.json'), 'utf8'));

let ok = 0, fail = 0;
function check(tag, cond, msg) {
  if (cond) { ok++; } else { fail++; console.log('  FAIL ' + tag + '：' + msg); }
}

const pad = n => (n < 10 ? '0' + n : '' + n);
const slash = d => d.getFullYear() + '/' + pad(d.getMonth() + 1) + '/' + pad(d.getDate());

/* ── ① 原书的那个例子，逐字锁死 ── */
const pdfCase = M.calc('1990/05/08', '前子时', 'male', 'book');
check('原书例-当天格', pdfCase.yang === '0325' && pdfCase.yin === '28101',
  '当天格应为 0325/28101，实际 ' + pdfCase.yang + '/' + pdfCase.yin);
check('原书例-调整格', pdfCase.yang1 === '09336' && pdfCase.yin1 === '29112',
  '调整格应为 09336/29112（=1990-05-09），实际 ' + pdfCase.yang1 + '/' + pdfCase.yin1);
check('原书例-调整日期', pdfCase.adjDate === '1990/05/09',
  '调整日期应为 1990/05/09，实际 ' + pdfCase.adjDate);

/* ── ② 方向律：前子时必为 D+1、后子时必为 D−1（全量对拍，不只挑样例）── */
let nDir = 0;
const SHIFT = {
  book:  { 前: +1, 后: -1 },
  v5:    { 前: -1, 后: +1 },
  query: { 前: +1, 后:  0 }
};
Object.keys(SHIFT).forEach(function (rule) {
  for (let off = 0; off < 400; off++) {
    const d = new Date(1990, 0, 1 + off);
    const cur = slash(d);
    ['前', '后'].forEach(function (k) {
      const sc = k + '子时', sign = SHIFT[rule][k];
      const adj = new Date(d.getFullYear(), d.getMonth(), d.getDate() + sign);
      const r = M.calc(cur, sc, 'male', rule);
      const direct = M.calc(slash(adj), '巳时', 'male', rule);
      check(rule + ' 位移 ' + cur + ' ' + sc,
        r.yang1 === direct.yang && r.yin1 === direct.yin,
        '调整格 ' + r.yang1 + '/' + r.yin1 + ' ≠ ' + slash(adj) + ' 的 ' + direct.yang + '/' + direct.yin);
      nDir++;
    });
  }
});

/* ②-b 关键性质：book 口径下两套格必然不同；query 的 后子时 反而必然相同 */
for (let off = 0; off < 200; off++) {
  const d = new Date(1990, 0, 1 + off);
  const cur = slash(d);
  const bk = M.calc(cur, '后子时', 'male', 'book');
  check('book 后子时两套不同 ' + cur, bk.yang1 !== bk.yang || bk.yin1 !== bk.yin,
    'book 口径下 后子时 两套格竟然相同');
  const qt = M.calc(cur, '后子时', 'male', 'query');
  check('query 后子时退化 ' + cur, qt.yang1 === qt.yang && qt.yin1 === qt.yin,
    'query 口径下 后子时 本应退化成与当天格相同（这是它的缺陷，需要被记录）');
}


/* ── ④ 缺省口径必须是 query（防止有人把默认值改回去）── */
const dflt = M.calc('1990/05/08', '前子时', 'male');
check('缺省口径', dflt.rule === 'book', '缺省 rule 应为 book，实际 ' + dflt.rule);
check('缺省结果', dflt.yang1 === '09336', '缺省调整格应为 09336，实际 ' + dflt.yang1);

/* ── ⑤ 报告透传：三份 .md 在 query 口径下必须出现 09336/29112，不得出现 0314/279 ── */
const NOW = new Date(2026, 9, 27, 10, 5, 0);
const base = Object.assign({}, D, {
  name: '测试', birth: '1990/05/08', shichen: '前子时', gender: 'male',
  location: null, now: NOW, targetDate: '2026/10/27'
});
const cases = [
  ['rp', function (o) { return M.REPORTS.comprehensive(o); }],
  ['tm', function (o) { return M.REPORTS.ni(o); }],
  ['sl', function (o) { return M.REPORTS.shiliao(o); }]
];
cases.forEach(function (c) {
  const mdQ = c[1](Object.assign({}, base, { rule: 'book' }));
  const mdV = c[1](Object.assign({}, base, { rule: 'v5' }));
  check('报告 ' + c[0] + ' book 含 09336', mdQ.indexOf('09336') >= 0,
    '这一份在 book 口径下没出现 09336 ⟹ rule 没透传进去');
  check('报告 ' + c[0] + ' book 不含 0314', mdQ.indexOf('0314') < 0,
    '出现了 v5 的 0314 ⟹ rule 混用');
  check('报告 ' + c[0] + ' v5 含 0314', mdV.indexOf('0314') >= 0,
    'v5 口径下应出现 0314');
  check('报告 ' + c[0] + ' 两口径不同', mdQ !== mdV,
    '两个口径产出一模一样 ⟹ rule 没生效');
});

/* ── ⑥ 非子时不受影响（0 回归）── */
const a = M.calc('2012/12/21', '巳时', 'male', 'query');
const b = M.calc('2012/12/21', '巳时', 'male', 'v5');
check('非子时两口径一致', a.yang === b.yang && a.yin === b.yin,
  '非子时不该受口径影响：' + a.yang + '/' + a.yin + ' vs ' + b.yang + '/' + b.yin);

console.log('三口径位移对拍 ' + nDir + ' 组');
console.log('子时口径校验：OK ' + ok + ' / FAIL ' + fail);
process.exit(fail ? 1 : 0);
