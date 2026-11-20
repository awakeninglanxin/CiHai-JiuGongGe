/* 三份报告：JS Markdown vs Python Markdown 逐行比对 */
const fs = require('fs');
const path = require('path');
const HERE = __dirname;

eval(fs.readFileSync(path.join(HERE, 'src', 'engine.js'), 'utf8'));
eval(fs.readFileSync(path.join(HERE, 'src', 'reports.js'), 'utf8'));
const M = globalThis.MAGIC;

M.lunarInit(JSON.parse(fs.readFileSync(path.join(HERE, 'lunar_table.json'), 'utf8')));
const data = JSON.parse(fs.readFileSync(path.join(HERE, 'data.json'), 'utf8'));
const G = JSON.parse(fs.readFileSync(path.join(HERE, 'report_golden.json'), 'utf8'));

const NOW = new Date(2026, 9, 27, 10, 5, 0);   // 与 Python 冻结值一致

function opts(c) {
  return Object.assign({}, data, {
    name: c.name, birth: c.birth, shichen: c.shichen, gender: c.gender,
    location: c.location, now: NOW, targetDate: '2026/10/27',
    /* 显式传 v5：Python 侧的 完整综合命理报告v3.9.py 走 core_v5 口径，
       这里要复现的就是那份历史基线，不是本页的新默认值。 */
    rule: 'v5'
  });
}

let ok = 0, fail = 0;

/* v3.9 报告里的 `[来源]` 字段用 '+'.join(set(...))，Python 字符串 set 顺序
   受哈希随机化影响，同一输入两次运行结果不同（已实测）。因此该括号内容
   只比「集合是否相同」，不比顺序；JS 版固定用 当天→调整→当天阴→调整阴。 */
function normalize(md) {
  return md.replace(/\[((?:当天阴|调整阴|当天|调整)(?:\+(?:当天阴|调整阴|当天|调整))*)\]/g,
    function (m0, inner) {
      return '[' + inner.split('+').sort().join('+') + ']';
    });
}

function diffLines(tag, a0, b0) {
  const a = normalize(a0), b = normalize(b0);
  if (a === b) { ok++; console.log('  OK   ' + tag + '  (' + a0.length + ' 字符)'); return true; }
  fail++;
  const A = a.split('\n'), B = b.split('\n');
  console.log('  FAIL ' + tag + '  js=' + a.length + ' py=' + b.length);
  let shown = 0;
  for (let i = 0; i < Math.max(A.length, B.length) && shown < 6; i++) {
    if (A[i] !== B[i]) {
      console.log('       行 ' + (i + 1));
      console.log('         js: ' + JSON.stringify(A[i]));
      console.log('         py: ' + JSON.stringify(B[i]));
      shown++;
    }
  }
  return false;
}

for (const c of G.cases) {
  const tag = c.name + ' ' + c.birth + ' ' + c.shichen + ' ' + c.gender;
  const o = opts(c);
  let js1, js2, js3;
  try { js1 = M.REPORTS.comprehensive(o); } catch (e) { js1 = 'ERR ' + e.message; }
  try { js2 = M.REPORTS.shiliao(o); } catch (e) { js2 = 'ERR ' + e.message; }
  try { js3 = M.REPORTS.ni(o); } catch (e) { js3 = 'ERR ' + e.message; }

  diffLines(tag + ' | 命理报告', js1, c.md_comprehensive);
  diffLines(tag + ' | 食疗动功', js2, c.md_shiliao);
  diffLines(tag + ' | 倪海厦', js3, c.md_ni);
}

console.log('========================================');
console.log('报告比对： OK ' + ok + '   FAIL ' + fail);
console.log('========================================');
