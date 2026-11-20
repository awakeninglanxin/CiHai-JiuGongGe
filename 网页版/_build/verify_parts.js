/* 校验「成串」中间数组：parts.join('') 必须等于最终阳格，main 必须等于主魂，extra 必须等于追加位。
   这一条是页面「10.1 阳格怎么算」那 8 步推导的立身之本 —— 步骤与结果必须能对上。 */
const fs = require('fs');
const path = require('path');
const HERE = __dirname;

eval(fs.readFileSync(path.join(HERE, 'src', 'engine.js'), 'utf8'));
const M = globalThis.MAGIC;
M.lunarInit(JSON.parse(fs.readFileSync(path.join(HERE, 'lunar_table.json'), 'utf8')));
const golden = JSON.parse(fs.readFileSync(path.join(HERE, 'golden.json'), 'utf8'));

let ok = 0, fail = 0, routeCount = { A: 0, B: 0, MultiSoul: 0 };
const fails = [];

function check(label, cond, msg) {
  if (cond) { ok++; return; }
  fail++;
  if (fails.length < 20) fails.push(label + '  ' + msg);
}

for (const c of golden.cases) {
  if (c.error) continue;
  const r = M.calc(c.date, c.shichen, c.gender, 'v5');
  const a = r.a;
  const tag = c.date + '|' + c.shichen + '|' + c.gender;
  routeCount[a.route] = (routeCount[a.route] || 0) + 1;

  check(tag, !!a.parts && a.parts.length > 0, '缺少 parts');
  check(tag, a.parts.join('') === r.yang,
    'parts 拼接 ' + a.parts.join('') + ' ≠ 阳格 ' + r.yang + ' route=' + a.route);
  // 主魂（源码定义）= 阳格末位，与「末位数根」是两个概念，这里分别锁死
  check(tag, String(a.soulDetail.mainSoul) === r.yang.charAt(r.yang.length - 1),
    '主魂 ' + a.soulDetail.mainSoul + ' ≠ 阳格末位 ' + r.yang.charAt(r.yang.length - 1));
  check(tag, a.parts.map(String).indexOf(String(a.main)) >= 0,
    '末位数根 ' + a.main + ' 根本没出现在 parts 里');
  if (!a.extra.length && a.route !== 'MultiSoul') {
    check(tag, String(a.parts[a.parts.length - 1]) === String(a.main),
      '无追加时末位应为末位数根，实际 ' + a.parts[a.parts.length - 1] + ' vs ' + a.main);
  }
  check(tag, Array.isArray(a.extra), 'extra 不是数组');
  // extra 必须是「成串后凑满 3 个、且不等于主魂」的数字
  const cnt = {};
  a.parts.join('').split('').forEach(ch => cnt[ch] = (cnt[ch] || 0) + 1);
  a.extra.forEach(d => {
    check(tag, cnt[String(d)] >= 3, 'extra 里的 ' + d + ' 在成串中只出现 ' + (cnt[String(d)] || 0) + ' 次');
    check(tag, String(d) !== String(a.main), 'extra 不应包含主魂 ' + d);
  });
}

console.log('成串数组校验：OK ' + ok + ' / FAIL ' + fail);
console.log('路线分布：', routeCount);
if (fails.length) { console.log(fails.join('\n')); process.exit(1); }
