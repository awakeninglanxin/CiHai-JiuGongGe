/* 逐字段比对：JS 引擎 vs Python 黄金样本 */
const fs = require('fs');
const path = require('path');
const HERE = __dirname;

const src = fs.readFileSync(path.join(HERE, 'src', 'engine.js'), 'utf8');
eval(src);
const M = globalThis.MAGIC;

const lunar = JSON.parse(fs.readFileSync(path.join(HERE, 'lunar_table.json'), 'utf8'));
M.lunarInit(lunar);
const golden = JSON.parse(fs.readFileSync(path.join(HERE, 'golden.json'), 'utf8'));
const data = JSON.parse(fs.readFileSync(path.join(HERE, 'data.json'), 'utf8'));

let ok = 0, fail = 0;
const fails = [];
const byField = {};

function cmp(field, label, a, b) {
  const A = JSON.stringify(a), B = JSON.stringify(b);
  if (A === B) { ok++; return true; }
  fail++;
  byField[field] = (byField[field] || 0) + 1;
  if (fails.length < 25) fails.push('[' + field + '] ' + label + '\n     js=' + A + '\n     py=' + B);
  return false;
}

// ===== 1. 主结果逐字段 =====
for (const c of golden.cases) {
  if (c.error) { cmp('python报错', c.date + ' ' + c.shichen, c.error, '无'); continue; }
  let r;
  try {
    r = M.calc(c.date, c.shichen, c.gender, 'v5');
  } catch (e) {
    cmp('JS抛错', c.date + ' ' + c.shichen, e.message, '无'); continue;
  }
  const tag = c.date + '|' + c.shichen + '|' + c.gender;
  cmp('type', tag, r.type, c.type);
  cmp('阳格', tag, r.yang, c.yang);
  cmp('阴格', tag, r.yin, c.yin);
  cmp('阳缺', tag, r.yangQue, c.yangQue);
  cmp('阴缺', tag, r.yinQue, c.yinQue);
  cmp('半补', tag, r.half, c.half);
  /* 原引擎在「子时双格」分支不把 魄/up/路线 写到顶层 ⟹ py=null 表示「未提供」，跳过 */
  if (c.route !== null) {
    cmp('路线', tag, r.a.route, c.route);
    cmp('魄', tag, r.a.po, c.po);
    cmp('up', tag, r.a.up, c.up);
  }
  if ('yang1' in c) {
    cmp('阳格1', tag, r.yang1, c.yang1);
    cmp('阴格1', tag, r.yin1, c.yin1);
    cmp('阳缺1', tag, r.yangQue1, c.yangQue1);
    cmp('阴缺1', tag, r.yinQue1, c.yinQue1);
    cmp('半补1', tag, r.half1, c.half1);
    cmp('调整日期', tag, r.adjDate, c.adjDate);
    cmp('说明', tag, r.note, c.note);
  }
  const by = parseInt(c.date.slice(0, 4), 10);
  const lc = M.calcLifeCycle(by, c.gender, golden.curYear);
  cmp('年龄', tag, lc.age, c.life['年龄']);
  cmp('当前阶段', tag, lc.phase, c.life['当前阶段']);
  cmp('当前类型', tag, lc.type, c.life['当前类型']);
  cmp('阶段开始', tag, lc.start, c.life['当前阶段开始']);
  cmp('阶段结束', tag, lc.end, c.life['当前阶段结束']);
  cmp('下次换魂', tag, lc.nextPhase, c.life['下次换魂']);
  cmp('下次换魂年龄', tag, lc.nextAge, c.life['下次换魂年龄']);
  cmp('距下次换魂', tag, lc.toNext, c.life['距下次换魂']);
}

// ===== 2. 组合 / 单格解读（照查询工具的真实匹配规则） =====
for (const c of golden.combos) {
  const g = M.getCombo(c.yg, c.ig, data.COMBO);
  cmp('组合命中', c.yg + '-' + c.ig, !!g, c.res.hit);
  cmp('组合名', c.yg + '-' + c.ig, g ? g.rec.combo_name : null, c.res.name);
  cmp('纯格标记', c.yg + '-' + c.ig, g ? !!g.rec.is_pure : null, c.res.isPure);
}
for (const c of golden.singles) {
  const s = M.getSingle(c.g, data.SINGLE);
  cmp('单格命中', c.g, !!s, c.res.hit);
  cmp('单格名', c.g, s ? s.rec.name : null, c.res.name);
}

// ===== 3. 农历全量自检 =====
{
  let bad = 0;
  const start = Date.UTC(1900, 0, 1);
  for (let i = 0; i < 73414; i++) {
    const dt = new Date(start + i * 86400000);
    const y = dt.getUTCFullYear(), m = dt.getUTCMonth() + 1, d = dt.getUTCDate();
    const lu = M.solar2lunar(y, m, d);
    if (!lu || lu.d < 1 || lu.d > 30 || lu.m < 1 || lu.m > 12) {
      bad++; if (bad < 4) fails.push('农历异常 ' + y + '-' + m + '-' + d + ' ' + JSON.stringify(lu));
    }
  }
  cmp('农历合法', '1900-2100 全 73414 天', bad, 0);
}

console.log('========================================');
console.log('OK ' + ok + '   FAIL ' + fail);
console.log('失败按字段：', JSON.stringify(byField));
if (fails.length) {
  console.log('--- 前若干失败 ---');
  fails.forEach(f => console.log(f));
}
console.log('========================================');
