/* 节气食养算法自测（Node）：校验节气判定与三方合参输出 */
const fs = require('fs'), vm = require('vm'), path = require('path');
const dir = path.join(__dirname, 'src');
const lib = require(path.join(dir, 'lunar.js'));
const ctx = Object.assign({}, lib, { console: console });
ctx.window = ctx;
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(dir, 'bazi.js'), 'utf8'), ctx);
const B = ctx.BAZI;

const dates = ['2026-11-21', '2026-11-22', '2026-12-07', '2026-06-21', '2026-04-20',
  '2026-03-05', '2026-10-23', '2027-02-03', '2026-01-01'];
dates.forEach(d => {
  const j = B.jieqiOf(d);
  console.log(d, '→', j ? j.name + ' (' + j.ymd + ', ' + j.info.wx + ')' : 'NULL');
});

const cityTable = require(path.join(dir, '..', 'data.json')).CITY;
console.log('地域判定：广州→', B.regionOfCity('广州'), ' 北京→', B.regionOfCity('北京'),
  ' 经纬度(39.9,116.4)→', B.regionOfLatLon(39.9, 116.4, cityTable),
  ' 经纬度(23.1,113.3)→', B.regionOfLatLon(23.1, 113.3, cityTable));

const fakeBazi = { ok: true, favor: ['水', '木'], avoid: ['火'], body: '身弱' };
const nine = { l1: ['4', '6'], l2: ['3'], digitOrgan: { '4': '肝', '6': '肾', '3': '心' } };
['2026-11-22', '2026-06-21', '2026-04-20'].forEach(d => {
  const adv = B.dayAdvice(fakeBazi, d, nine, '华南');
  console.log('\n=== ' + d + ' ===');
  console.log('日柱', adv.dayGz, '宜补', adv.best, '宜避', adv.avoid, '节气', adv.jieqi && adv.jieqi.name);
  const x = adv.diet;
  console.log('原则：', x.principle);
  console.log('当令：', x.food);
  console.log('命盘：', x.constitution);
  console.log('九宫：', x.nineText);
  console.log('食疗：', x.recipe);
  console.log('应地：', x.regional);
  console.log('食疗药膳：', x.therapy);
  console.log('每周药食：', x.weekly);
  console.log('忌口：', x.avoid);
  console.log('warning：', x.warning);
});
