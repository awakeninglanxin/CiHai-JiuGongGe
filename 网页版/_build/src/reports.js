/* ============================================================
 * 三份报告的 Markdown 生成器（JS 移植）
 * 逐行对照：
 *   核心引擎/完整综合命理报告v3.9.py   → MAGIC.REPORTS.comprehensive
 *   核心引擎/倪海厦中医建议生成器.py   → MAGIC.REPORTS.ni
 *   核心引擎/食疗动功生成器v3.3.py     → MAGIC.REPORTS.shiliao
 * 输出与 Python 写出的 .md 逐字节一致（除文件名），由 verify_reports.js 校验。
 * ============================================================ */
(function (root) {
  'use strict';
  var M = root.MAGIC;

  function p2(n) { return String(n).padStart(2, '0'); }
  function ts(d) {
    return d.getFullYear() + '-' + p2(d.getMonth() + 1) + '-' + p2(d.getDate()) +
      ' ' + p2(d.getHours()) + ':' + p2(d.getMinutes());
  }
  function ds2(d) { return d.getFullYear() + '/' + p2(d.getMonth() + 1) + '/' + p2(d.getDate()); }
  function f1(x) { return Math.round(x * 10) / 10; }
  /** Python round(x,1) 的显示：整数也要带 .1（'11.9' / '12.0'） */
  function pyf1(x) { var v = Math.round(x * 10) / 10; return v.toFixed(1); }

  function uniqSorted(str) {
    var s = {};
    for (var i = 0; i < str.length; i++) if (/\d/.test(str[i])) s[str[i]] = 1;
    return Object.keys(s).sort();
  }
  function setOf(str) {
    var s = {};
    for (var i = 0; i < str.length; i++) if (/\d/.test(str[i])) s[str[i]] = 1;
    return s;
  }
  function inter(a, b) { return Object.keys(a).filter(function (k) { return b[k]; }).sort(); }

  var ZANGFU_SIMPLE = { '0': '小肠', '1': '肺', '2': '大肠', '3': '心', '4': '肝', '5': '胆', '6': '肾', '7': '胃', '8': '脾', '9': '膀胱' };
  var QUE_FIX = {
    '0': '分清泌浊', '1': '多做深呼吸', '2': '腹式呼吸+蔬菜配方', '3': '通心轮（小白瓶）',
    '4': 'A杯+蔬菜配方', '5': '宁化府饺子醋', '6': '黑米套餐+动功', '7': '小绿瓶+情感和谐',
    '8': '铁棍山药+忌甜食', '9': '开天门+黑豆黑木耳'
  };
  var DIGIT_ORGAN = { '1': '肺', '2': '大肠', '3': '心', '4': '肝', '5': '胆', '6': '肾', '7': '胃', '8': '脾', '9': '膀胱', '0': '小肠' };
  var YANG_MEANING = { '1': '肺气', '2': '大肠传导', '3': '心神', '4': '肝疏', '5': '胆决', '6': '肾藏', '7': '胃纳', '8': '脾运', '9': '膀胱气化', '0': '小肠分清' };
  var YIN_MEANING = { '1': '肺阴', '2': '大肠津液', '3': '心阴', '4': '肝阴', '5': '胆阴', '6': '肾阴', '7': '胃阴', '8': '脾阴', '9': '三焦水火', '0': '心包护心' };
  var SHICHEN_LIST = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时', '午时', '未时', '申时', '酉时', '戌时', '亥时'];

  /* ══════════════════════════════════════════════════════════
   * 一、完整综合命理报告 v3.9
   * ══════════════════════════════════════════════════════════ */
  function comprehensive(o) {
    var birth = o.birth, birthTime = o.shichen, gender = o.gender;
    var name = o.name || '蓝馨';
    var now = o.now;
    var targetDate = o.targetDate || ds2(now);
    var RULE = o.rule || 'book';   /* 缺省与原书一致；校验脚本显式传 'v5' 复现 Python 基线 */

    var r = M.calc(birth, birthTime, gender, RULE);
    var isZishi = !!r.isZishi;
    var R = [];

    var yang_que = r.yangQue || '', yin_que = r.yinQue || '';
    var yang_ge = r.yang || '', yin_ge = r.yin || '', banbu = r.half || '';
    var yang_que1 = '', yin_que1 = '', yang_ge1 = '', yin_ge1 = '', banbu1 = '', adj_date = '', zishi_note = '';
    if (isZishi) {
      yang_que1 = r.yangQue1 || ''; yin_que1 = r.yinQue1 || '';
      yang_ge1 = r.yang1 || ''; yin_ge1 = r.yin1 || '';
      banbu1 = r.half1 || ''; adj_date = r.adjDate || ''; zishi_note = r.note || '';
    }

    var trend = (r.yyYang && r.yyYang.trend) || '平衡';
    var trend_desc = '';   // 原引擎该字段从不赋值（analyze 只返回 阴阳倾向）

    var bd = M.parseDate(birth);
    var age = now.getFullYear() - bd.y - (((now.getMonth() + 1) < bd.m || ((now.getMonth() + 1) === bd.m && now.getDate() < bd.d)) ? 1 : 0);

    R.push('# ' + name + ' · 综合命理报告');
    R.push('');
    R.push('**生辰**: ' + birth + ' ' + birthTime);
    R.push('**性别**: ' + (gender === 'male' ? '男' : '女'));
    R.push('**生成时间**: ' + ts(now) + ' | **年龄**: ' + age + '岁');
    R.push('');

    if (isZishi) {
      R.push('### 命盘概要（子时双格）');
      R.push('');
      R.push('| 类型 | 阳格 | 阴格 | 阳缺 | 阴缺 | 半补 |');
      R.push('|:----:|:-----:|:-----:|:-----:|:-----:|:-----:|');
      R.push('| **当天格** | ' + yang_ge + ' | ' + yin_ge + ' | ' + yang_que + ' | ' + yin_que + ' | ' + banbu + ' |');
      R.push('| **调整格** | ' + yang_ge1 + ' | ' + yin_ge1 + ' | ' + yang_que1 + ' | ' + yin_que1 + ' | ' + banbu1 + ' |');
      R.push('');
      R.push('> **' + zishi_note + '** | 调整日期: ' + adj_date);
      R.push('');
      var alY = uniqSorted(yang_que).concat(uniqSorted(yang_que1));
      var alI = uniqSorted(yin_que).concat(uniqSorted(yin_que1));
      var allSets = {};
      alY.forEach(function (d) { allSets[d] = 1; });
      alI.forEach(function (d) { allSets[d] = 1; });
      var all_que = Object.keys(allSets).sort();
      var all_que_str = all_que.join('');
      var all_que_organs = all_que.map(function (n) { return ZANGFU_SIMPLE[n] || '?'; }).join('、');
      R.push('> **综合缺格**: ' + all_que_str + ' → ' + all_que_organs);
    } else {
      R.push('**命盘**: 阳格' + yang_ge + ' | 阴格' + yin_ge);
      R.push('**缺格**: 阳缺' + yang_que + ' | 阴缺' + yin_que + ' | 半补' + banbu);
    }
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 一、基本信息');
    R.push('');
    var soulN = '', soulT = '';
    var sv = M.lookupSoulV5(yang_ge, o.SOUL_DB);
    if (sv && sv.rec) { soulN = sv.rec.n || ''; soulT = sv.rec.t || ''; }
    if (soulN) R.push('- **灵魂**: ' + soulN + '（' + soulT + '）');
    R.push('- **类型**: ' + (r.type || '普通阴阳双格'));
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 二、阴阳格周期');
    R.push('');
    if (trend === '平衡') R.push('您的阳格和阴格处于**平衡期**，阴阳同调为佳。');
    else if (trend === '阳') R.push('当前处于**阳格期**：以' + yang_ge + '为主导能量。' + trend_desc);
    else R.push('当前处于**阴格期**：以' + yin_ge + '为主导能量。' + trend_desc);

    var lc = r.life;
    if (lc) {
      R.push('');
      R.push('**生命周期状态**:');
      R.push('- 年龄: ' + lc.age + '岁');
      R.push('- 当前阶段: ' + lc.phase);
      R.push('- 当前类型: ' + lc.type);
      R.push('- 阶段区间: ' + pyf1(lc.start) + ' ~ ' + pyf1(lc.end) + '岁');
      R.push('- 下次换魂: ' + lc.nextPhase + '（' + pyf1(lc.toNext) + '年后）');
    }
    R.push('');
    R.push('---');
    R.push('');

    /* 三、缺格修正方案 */
    var allQueSet = {};
    if (isZishi) {
      R.push('## 三、缺格修正方案（双格合并）');
      R.push('');
      R.push('当天格缺格: 阳缺' + yang_que + ' + 阴缺' + yin_que);
      R.push('调整格缺格: 阳缺' + yang_que1 + ' + 阴缺' + yin_que1);
      R.push('');
      uniqSorted(yang_que).forEach(function (d) { allQueSet[d] = 1; });
      uniqSorted(yang_que1).forEach(function (d) { allQueSet[d] = 1; });
      uniqSorted(yin_que).forEach(function (d) { allQueSet[d] = 1; });
      uniqSorted(yin_que1).forEach(function (d) { allQueSet[d] = 1; });
      Object.keys(allQueSet).sort().forEach(function (num) {
        var organ = ZANGFU_SIMPLE[num] || '未知';
        var desc = QUE_FIX[num] || '对应食疗动功调理';
        var src = [];
        if (yang_que.indexOf(num) >= 0) src.push('当天');
        if (yang_que1.indexOf(num) >= 0) src.push('调整');
        if (yin_que.indexOf(num) >= 0) src.push('当天阴');
        if (yin_que1.indexOf(num) >= 0) src.push('调整阴');
        var uniq = Array.from(new Set(src));
        R.push('**' + num + '（' + organ + '）** [' + uniq.join('+') + ']: ' + desc);
      });
      R.push('');
    } else {
      R.push('## 三、缺格修正方案');
      R.push('');
      var s3 = {};
      (yang_que + yin_que).split('').forEach(function (c) { if (/\d/.test(c)) s3[c] = 1; });
      Object.keys(s3).sort().forEach(function (num) {
        var organ = ZANGFU_SIMPLE[num] || '未知';
        var desc = QUE_FIX[num] || '对应食疗动功调理';
        R.push('**' + num + '（' + organ + '）**: ' + desc);
      });
      R.push('');
    }

    R.push('---');
    R.push('');
    R.push('## 四、脏腑详解（缺格对应）');
    R.push('');

    var missingList;
    if (isZishi) missingList = Object.keys(allQueSet).sort();
    else {
      var s4 = {};
      (yang_que + yin_que).split('').forEach(function (c) { if (/\d/.test(c)) s4[c] = 1; });
      missingList = Object.keys(s4).sort();
    }
    missingList.forEach(function (num) {
      var organ = ZANGFU_SIMPLE[num] || '未知';
      var isYang = (yang_que.indexOf(num) >= 0) || (yang_que1.indexOf(num) >= 0);
      var isYin = (yin_que.indexOf(num) >= 0) || (yin_que1.indexOf(num) >= 0);
      var queType;
      if (isZishi) {
        var ys = (yang_que.indexOf(num) >= 0 ? 1 : 0) + (yang_que1.indexOf(num) >= 0 ? 1 : 0);
        var is = (yin_que.indexOf(num) >= 0 ? 1 : 0) + (yin_que1.indexOf(num) >= 0 ? 1 : 0);
        queType = ys ? ('阳缺' + (ys === 2 ? '(双)' : '(单)')) : '';
        queType += is ? (' 阴缺' + (is === 2 ? '(双)' : '(单)')) : '';
      } else {
        queType = isYang ? '阳缺' : '阴缺';
      }
      R.push('### ' + num + '（' + organ + '）');
      R.push('- 类型：' + queType.trim());
      R.push('- 修正：' + (QUE_FIX[num] || '请参考缺格修正方案'));
      R.push('');
    });

    R.push('---');
    R.push('');
    R.push('## 五、命盘整体分析');
    R.push('');
    if (isZishi) {
      var miss = Object.keys(allQueSet).sort();
      var missOrg = miss.map(function (n) { return ZANGFU_SIMPLE[n] || '?'; });
      R.push('命盘缺格共 ' + miss.length + ' 个数字（阳缺合集' + yang_que + '/' + yang_que1 +
        '、阴缺合集' + yin_que + '/' + yin_que1 + '），涉及脏腑：' + missOrg.join('、') + '。');
    } else {
      var qm = yang_que + yin_que, s5 = {};
      qm.split('').forEach(function (c) { if (/\d/.test(c)) s5[c] = 1; });
      var miss2 = Object.keys(s5).sort();
      var missOrg2 = miss2.map(function (n) { return ZANGFU_SIMPLE[n] || '?'; });
      R.push('命盘缺格共 ' + miss2.length + ' 个数字（阳缺' + yang_que + '、阴缺' + yin_que +
        '），涉及脏腑：' + missOrg2.join('、') + '。');
    }
    R.push('');
    R.push('---');
    R.push('');

    /* 六、今日行运 */
    R.push('## 六、今日行运分析 (' + targetDate + ')');
    var nowShichen = SHICHEN_LIST[Math.floor((now.getHours() + 1) / 2)];
    var dayR = M.calc(targetDate, nowShichen, gender, RULE);
    var day_yang = dayR.yang || '', day_yin = dayR.yin || '';
    var day_yang_que = dayR.yangQue || '', day_yin_que = dayR.yinQue || '';
    var day_banbu = dayR.half || '';
    var level1, level2;

    if (isZishi) {
      var dYQ = setOf(day_yang_que), dIQ = setOf(day_yin_que);
      var bYQ = setOf(yang_que); uniqSorted(yang_que1).forEach(function (d) { bYQ[d] = 1; });
      var bIQ = setOf(yin_que); uniqSorted(yin_que1).forEach(function (d) { bIQ[d] = 1; });
      level1 = inter(dYQ, bYQ).concat(inter(dIQ, bIQ)).sort();
      level1 = Array.from(new Set(level1)).sort();
      level2 = inter(dYQ, bIQ).concat(inter(dIQ, bYQ)).sort();
      level2 = Array.from(new Set(level2)).sort();

      R.push('');
      R.push('**今日天时**:');
      R.push('- 天时阳格: ' + day_yang + ' | 天时阴格: ' + day_yin);
      R.push('- 天时阳缺: ' + day_yang_que + ' | 天时阴缺: ' + day_yin_que);
      R.push('- 天时半补: ' + (day_banbu || '无'));
      R.push('');
      R.push('| 数字 | 脏腑 | 天时 | 命盘(当天) | 命盘(调整) | 共振 |');
      R.push('|:----:|:----:|------|:----------:|:----------:|:-----:|');
      for (var n = 0; n <= 9; n++) {
        var ns = String(n);
        var organ = ZANGFU_SIMPLE[ns] || '未知';
        var day_tz = (day_yang_que.indexOf(ns) >= 0 ? '阳缺 ' : '') + (day_yin_que.indexOf(ns) >= 0 ? '阴缺' : '正常');
        var birth_y = yang_que.indexOf(ns) >= 0 ? '缺' : '正常';
        var birth_y1 = yang_que1.indexOf(ns) >= 0 ? '缺' : '正常';
        var birth_i = yin_que.indexOf(ns) >= 0 ? '缺' : '正常';
        var birth_i1 = yin_que1.indexOf(ns) >= 0 ? '缺' : '正常';
        var res = level1.indexOf(ns) >= 0 ? '🔴 一级' : (level2.indexOf(ns) >= 0 ? '🟡 二级' : '⚪ 潜伏');
        R.push('| **' + ns + '** | ' + organ + ' | ' + day_tz + ' | ' + birth_y + '/' + birth_i + ' | ' + birth_y1 + '/' + birth_i1 + ' | ' + res + ' |');
      }
    } else {
      var dYQ2 = setOf(day_yang_que), dIQ2 = setOf(day_yin_que);
      var bYQ2 = setOf(yang_que), bIQ2 = setOf(yin_que);
      level1 = Array.from(new Set(inter(dYQ2, bYQ2).concat(inter(dIQ2, bIQ2)))).sort();
      level2 = Array.from(new Set(inter(dYQ2, bIQ2).concat(inter(dIQ2, bYQ2)))).sort();

      R.push('');
      R.push('| 数字 | 脏腑 | 今日天时 | 命盘 | 共振强度 |');
      R.push('|------|------|----------|------|----------|');
      for (var n2 = 0; n2 <= 9; n2++) {
        var ns2 = String(n2);
        var organ2 = ZANGFU_SIMPLE[ns2] || '未知';
        var day_tz2 = (day_yang_que.indexOf(ns2) >= 0 ? '阳缺 ' : '') + (day_yin_que.indexOf(ns2) >= 0 ? '阴缺' : '正常');
        var inBirth = (yang_que.indexOf(ns2) >= 0 || yin_que.indexOf(ns2) >= 0) ? '命盘缺' : '命盘正常';
        var res2 = level1.indexOf(ns2) >= 0 ? '🔴 一级共振' : (level2.indexOf(ns2) >= 0 ? '🟡 二级共振' : '⚪ 潜伏期');
        R.push('| **' + ns2 + '** | ' + organ2 + ' | ' + day_tz2 + ' | ' + inBirth + ' | ' + res2 + ' |');
      }
    }
    R.push('');
    R.push('> 📌 共振等级分档：🔴 一级共振（双重缺格，核心关注）| 🟡 二级共振（单层缺格，辅助关注）| ⚪ 潜伏期（能量休眠）');
    R.push('');
    if (level1.length) {
      R.push('**🔴 一级共振器官（需重点关注）**:');
      level1.forEach(function (num) {
        var organ = ZANGFU_SIMPLE[num] || '未知';
        var corr = QUE_FIX[num] || '请参考缺格修正方案';
        R.push('- ' + organ + '(' + num + '): 天时+命盘双重缺格，能量缺口最大 -> ' + corr);
      });
    }
    if (level2.length) {
      var l2u = level2.filter(function (x) { return level1.indexOf(x) < 0; });
      if (l2u.length) {
        R.push('**🟡 二级共振器官（需留意）**:');
        l2u.forEach(function (num) {
          var organ = ZANGFU_SIMPLE[num] || '未知';
          var corr = QUE_FIX[num] || '请参考缺格修正方案';
          R.push('- ' + organ + '(' + num + '): 单层共振，能量有缺口 -> ' + corr);
        });
      }
    }
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 七、GDV数据分析');
    R.push('');
    R.push('本部分内容请参考详细GDV趋势分析报告。');
    R.push('');

    return R.join('\n');
  }

  /* ══════════════════════════════════════════════════════════
   * 二、倪海厦中医建议
   * ══════════════════════════════════════════════════════════ */
  function ni(o) {
    var birth = o.birth, birthTime = o.shichen, gender = o.gender;
    var name = o.name || '蓝馨', location = o.location || null;
    var now = o.now;
    var g = (gender === 'male' || gender === '男') ? 'male' : 'female';
    var genderText = g === 'male' ? '男' : '女';
    var RULE = o.rule || 'book';

    var r = M.calc(birth, birthTime, g, RULE);
    var isZishi = !!r.isZishi;

    var yang_que = r.yangQue || '', yin_que = r.yinQue || '';
    var yang_ge = r.yang || '', yin_ge = r.yin || '';
    var yang_que1 = '', yin_que1 = '', yang_ge1 = '', yin_ge1 = '', zishi_note = '', adj_date = '';
    if (isZishi) {
      yang_que1 = r.yangQue1 || ''; yin_que1 = r.yinQue1 || '';
      yang_ge1 = r.yang1 || ''; yin_ge1 = r.yin1 || '';
      zishi_note = r.note || ''; adj_date = r.adjDate || '';
    }

    var lc = r.life;
    var trend = (r.yyYang && r.yyYang.trend) || '平衡';
    var bd = M.parseDate(birth);
    var age = now.getFullYear() - bd.y;

    var nowShichen = M.hourToShichen(now.getHours());
    var rNow = M.calc(ds2(now), nowShichen, g, RULE);
    var today_yang = rNow.yang || '', today_yin = rNow.yin || '';
    var today_yang_que = rNow.yangQue || '', today_yin_que = rNow.yinQue || '';

    var natalYQ = setOf(yang_que), natalIQ = setOf(yin_que);
    var todayYQ = setOf(today_yang_que), todayIQ = setOf(today_yin_que);
    var resonance_yang = inter(natalYQ, todayYQ);
    var resonance_yin = inter(natalIQ, todayIQ);
    var resonance_all = Array.from(new Set(resonance_yang.concat(resonance_yin))).sort();

    var allYQ, allIQ, allMissing;
    if (isZishi) {
      allYQ = Array.from(new Set(uniqSorted(yang_que).concat(uniqSorted(yang_que1)))).sort();
      allIQ = Array.from(new Set(uniqSorted(yin_que).concat(uniqSorted(yin_que1)))).sort();
    } else {
      allYQ = uniqSorted(yang_que); allIQ = uniqSorted(yin_que);
    }
    allMissing = Array.from(new Set(allYQ.concat(allIQ))).sort();

    var ZF = o.ZANGFU_MAP, SIX = o.SIX_DIVISION, DIET = o.NI_DIET, EX = o.NI_EXERCISE;
    var R = [];
    R.push('# ' + name + ' · 倪海厦中医养生建议');
    R.push('');
    R.push('> **说明**：本报告整合九宫格命理分析 + 倪海厦经方体系，从六经辨证角度提供个性化中医养生方案。');
    R.push('> ');
    R.push('> :warning: **免责声明**：以下内容仅供学习参考，如有不适请咨询当地中医师。');
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 一、基本信息');
    R.push('| 项目 | 内容 |');
    R.push('|:----:|:----|');
    R.push('| 姓名 | ' + name + ' |');
    R.push('| 出生日期 | ' + birth + ' ' + birthTime + ' |');
    R.push('| 性别 | ' + genderText + ' |');
    R.push('| 年龄 | ' + age + '岁 |');
    if (isZishi) {
      R.push('| 命盘类型 | 子时双格 |');
      R.push('| 当天格 | 阳格' + yang_ge + ' / 阴格' + yin_ge + ' / 阳缺' + yang_que + ' / 阴缺' + yin_que + ' |');
      R.push('| 调整格 | 阳格' + yang_ge1 + ' / 阴格' + yin_ge1 + ' / 阳缺' + yang_que1 + ' / 阴缺' + yin_que1 + ' |');
      R.push('| 综合缺格 | 阳缺合集' + allYQ.join('') + ' / 阴缺合集' + allIQ.join('') + ' |');
      R.push('| ' + zishi_note + ' | 调整日期: ' + adj_date + ' |');
    } else {
      R.push('| 命盘 | 阳缺' + yang_que + ' / 阴缺' + yin_que + ' |');
    }
    R.push('| 今日天时 | ' + today_yang + ' / ' + today_yin + ' |');
    R.push('| 今日行运缺 | 阳缺' + today_yang_que + ' / 阴缺' + today_yin_que + ' |');
    if (resonance_all.length) {
      R.push('| ⚡ 共振缺 | 阳缺' + (resonance_yang.length ? resonance_yang.join('') : '无') +
        ' / 阴缺' + (resonance_yin.length ? resonance_yin.join('') : '无') + ' |');
    } else {
      R.push('| 共振状态 | 本命与今天无缺格共振，今日相对平稳 |');
    }
    if (location) R.push('| 出生地 | ' + location + ' |');
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 二、⚡ 当天行运共振分析（为重点照顾）');
    R.push('');
    if (resonance_all.length) {
      R.push('> **原理**：当天行运的阴缺/阳缺与本命命盘的阴缺/阳缺产生信息共振时，');
      R.push('> 对应的脏腑经络在今日格外敏感脆弱，需优先养护。');
      R.push('');
      R.push('| 共振数字 | 对应脏腑 | 六经 | 提示 |');
      R.push('|:---:|------|------|------|');
      resonance_all.forEach(function (num) {
        var zf = ZF[num] || { name: '未知', yin: '' };
        var six = SIX[num] || { jing: '未知', desc: '' };
        var tags = [];
        if (resonance_yang.indexOf(num) >= 0) tags.push('阳缺共振');
        if (resonance_yin.indexOf(num) >= 0) tags.push('阴缺共振');
        R.push('| **' + num + '** | ' + zf.name + ' | ' + six.jing + ' | ⚠️ ' + tags.join('·') + ' |');
      });
      R.push('');
      R.push('**今日重点照顾建议**：');
      R.push('');
      resonance_all.forEach(function (num) {
        var zf = ZF[num] || { name: '未知', yin: '' };
        var orgName = zf.name, yinType = zf.yin || '';
        if (yinType.indexOf('阴') >= 0) R.push('- **' + num + '→' + orgName + '**：避寒就温，可艾灸、姜汤暖胃，忌生冷。');
        else if (yinType.indexOf('阳') >= 0) R.push('- **' + num + '→' + orgName + '**：疏泄为主，避免情绪压抑，可饮菊花决明茶。');
        else R.push('- **' + num + '→' + orgName + '**：作息规律，避免过劳，适度按摩。');
      });
      R.push('');
    } else {
      R.push('> 今日行运缺格与本命命盘无交集共振，各脏腑经络处于平稳状态。');
      R.push('> 但仍需注意日常养护，不因安稳而放纵。');
      R.push('');
    }
    R.push('---');
    R.push('');
    R.push('## 三、命理脏腑分析');
    R.push('');
    R.push('### 3.1 缺格脏腑（需重点养护）');
    R.push('');

    var displayYang = isZishi ? allYQ.join('') : yang_que;
    var displayYin = isZishi ? allIQ.join('') : yin_que;

    if (displayYang) {
      R.push('**阳缺（' + displayYang + '）**：');
      displayYang.split('').forEach(function (num) {
        var zf = ZF[num] || { name: '未知', yin: '' };
        var six = SIX[num] || { jing: '未知', desc: '' };
        var src = [];
        if (yang_que.indexOf(num) >= 0) src.push('当天');
        if (yang_que1.indexOf(num) >= 0) src.push('调整');
        if (resonance_yang.indexOf(num) >= 0) src.push('⚡共振');
        var srcStr = src.length ? ' [' + src.join('+') + ']' : '';
        R.push('- **' + num + ' → ' + zf.name + '**' + srcStr + '：' + six.jing + '，' + six.desc);
      });
      R.push('');
    }
    if (displayYin) {
      R.push('**阴缺（' + displayYin + '）**：');
      displayYin.split('').forEach(function (num) {
        var zf = ZF[num] || { name: '未知', yin: '' };
        var six = SIX[num] || { jing: '未知', desc: '' };
        var src = [];
        if (yin_que.indexOf(num) >= 0) src.push('当天');
        if (yin_que1.indexOf(num) >= 0) src.push('调整');
        if (resonance_yin.indexOf(num) >= 0) src.push('⚡共振');
        var srcStr = src.length ? ' [' + src.join('+') + ']' : '';
        R.push('- **' + num + ' → ' + zf.name + '**' + srcStr + '：' + six.jing + '，' + six.desc);
      });
      R.push('');
    }
    R.push('### 3.2 当前周期状态');
    R.push('');
    if (trend === '平衡') R.push('- 当前处于**阴阳平衡期**，适合全面调理');
    else if (trend === '阳') R.push('- 当前处于**阳格期**：' + yang_ge + '能量为主导，');
    else R.push('- 当前处于**阴格期**：' + yin_ge + '能量为主导，');
    R.push('');
    R.push('### 3.3 生命周期（各年龄段重点）');
    R.push('');
    if (lc) {
      var items = [
        ['年龄', lc.age], ['当前阶段', lc.phase], ['当前类型', lc.type],
        ['当前阶段开始', lc.start], ['当前阶段结束', lc.end],
        ['下次换魂', lc.nextPhase], ['下次换魂年龄', lc.nextAge], ['距下次换魂', lc.toNext]
      ];
      items.forEach(function (kv) {
        var val = kv[1];
        if (typeof val === 'number' && !Number.isInteger(val)) val = pyf1(val);
        R.push('- **' + kv[0] + '**：' + val);
      });
      /* 原引擎此处把「周期参数」字典直接 repr 出来；此处按 Python repr 逐字复现 */
      var pp = lc.params;
      R.push('- **周期参数**：{' + "'yang_years': " + pp.yang + ", 'yin_years': " + pp.yin +
        ", 'transition': " + pp.trans + ", 'desc': '" + pp.desc + "'}");
    }
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 四、六经辨证分析（倪海厦经方体系）');
    R.push('');
    R.push('> 倪海厦老师常说："治病必须先明六经辨证，才能对症下药！"');
    R.push('');
    var j = 0;
    allMissing.forEach(function (num) {
      var zf = ZF[num] || { name: '未知', yin: '未知' };
      var six = SIX[num] || { jing: '未知', formula: '待定', desc: '' };
      var diet = DIET[num] || { formula: '待定', diet: [], avoid: [] };
      var ex = EX[num] || [];
      var rson = resonance_all.indexOf(num) >= 0 ? '⚡ 今日共振！' : '';
      R.push('### 4.' + (j + 1) + ' ' + zf.name + '（' + six.jing + '）' + rson);
      R.push('');
      R.push('**六经辨证**：' + six.jing);
      R.push('');
      R.push('**病机分析**：' + six.desc);
      R.push('');
      R.push('**推荐经方**：' + six.formula);
      R.push('');
      R.push('**食疗方案**：');
      R.push('- 宜食：`' + diet.diet.slice(0, 4).join('、') + '`');
      R.push('- 忌食：`' + diet.avoid.join('、') + '`');
      R.push('');
      R.push('**动功建议**：');
      ex.forEach(function (x) { R.push('- ' + x); });
      R.push('');
      R.push('---');
      R.push('');
      j++;
    });

    R.push('## 四、综合养生方案（倪海厦六诊养生）');
    R.push('');
    R.push('### 倪师六健康标准自检');
    R.push('');
    R.push('| 标准 | 正常表现 | 自我检测 |');
    R.push('|:----:|:--------:|:--------:|');
    R.push('| 睡眠 | 一觉到天亮 | 入睡困难？易醒？噩梦？ |');
    R.push('| 食欲 | 三餐定时定量 | 食欲不振？暴饮暴食？ |');
    R.push('| 大便 | 每日一次成形 | 便秘？稀溏？不规律？ |');
    R.push('| 小便 | 每日5-7次淡黄 | 尿频？夜尿？浑浊？ |');
    R.push('| 口渴 | 渴而欲饮 | 不渴？多饮？喜冷/热？ |');
    R.push('| 体温 | 手足温热 | 手脚冰凉？发热？ |');
    R.push('');
    R.push('### 日常养生要点');
    R.push('');
    var has = function (a, b) { return allMissing.indexOf(a) >= 0 || allMissing.indexOf(b) >= 0; };
    if (has('6', '9')) {
      R.push('**肾与膀胱养护**：');
      R.push('- 早睡（23点前）最关键！倪师说："熬夜伤肾，这是第一杀手！"');
      R.push('- 踮脚尖走路，每天50次，刺激肾经');
      R.push('- 搓腰眼（肾俞穴），每天100下');
      R.push('');
    }
    if (has('3', '0')) {
      R.push('**心与小肠养护**：');
      R.push('- 中午小憩30分钟，养心阴');
      R.push('- 避免下午剧烈运动耗伤心气');
      R.push('- 莲子心泡水喝，清心火');
      R.push('');
    }
    if (has('4', '5')) {
      R.push('**肝与胆养护**：');
      R.push('- 凌晨1-3点是肝经值班，必须熟睡！');
      R.push('- 疏肝理气：拍打肝经（大腿内侧）');
      R.push('- 保持情绪舒畅，怒伤肝！');
      R.push('');
    }
    if (has('7', '8')) {
      R.push('**脾与胃养护**：');
      R.push('- 三餐定时，七八分饱');
      R.push('- 饭后散步30分钟，帮助消化');
      R.push('- 倪师强调："小米粥是最好的健脾食物！"');
      R.push('');
    }
    if (has('1', '2')) {
      R.push('**肺与大肠养护**：');
      R.push('- 每天深呼吸，早起50次，宣肺气');
      R.push('- 大肠经值班（早5-7点），养成排便习惯');
      R.push('- 白色食物入肺：梨、百合、银耳');
      R.push('');
    }
    R.push('### 节气养生提醒');
    R.push('');
    R.push('- **春**：早睡早起，多做户外活动，疏肝为主');
    R.push('- **夏**：晚睡早起，午休养心，清热解暑');
    R.push('- **秋**：早睡早起，润肺生津，适当秋冻');
    R.push('- **冬**：早睡晚起，藏精养肾，保暖防寒');
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 五、常用保健穴位');
    R.push('');
    R.push('| 脏腑 | 推荐穴位 | 按摩方法 |');
    R.push('|:----:|:--------:|:--------:|');
    R.push('| 心 | 神门、内关 | 每穴按揉2分钟 |');
    R.push('| 肝 | 太冲、三阴交 | 每穴按揉3分钟 |');
    R.push('| 脾 | 足三里、阴陵泉 | 每穴按揉2分钟 |');
    R.push('| 肺 | 列缺、太渊 | 每穴按揉2分钟 |');
    R.push('| 肾 | 涌泉、肾俞 | 搓热为宜 |');
    R.push('| 胃 | 中脘、天枢 | 顺时针揉腹 |');
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 六、结语');
    R.push('');
    R.push('倪海厦老师常说：');
    R.push('');
    R.push('> "中医的精髓在于治未病！你们要学会倾听身体的声音，在疾病萌芽时就把它解决掉。"');
    R.push('');
    R.push('本报告结合您的命理特点，建议：');
    R.push('1. **坚持六健康标准自检**，发现问题及时调理');
    R.push('2. **顺应节气养生**，春疏肝、夏清心、秋润肺、冬补肾');
    R.push('3. **缺格脏腑重点养护**，食疗+动功+穴位三管齐下');
    R.push('4. **保持良好生活习惯**，这是养生最重要的！');
    R.push('');
    R.push('---');
    R.push('');
    R.push('*报告生成时间：' + ts(now) + '*');
    R.push('*数据来源：慈海九宫格 + 倪海厦经方体系*');
    R.push('');
    R.push('---');
    R.push(':warning: **免责声明**：本报告仅供学习参考，不能替代专业中医诊断。如有不适，请咨询当地中医师！');
    return R.join('\n');
  }

  /* ══════════════════════════════════════════════════════════
   * 三、食疗动功方案 v3.3
   * ══════════════════════════════════════════════════════════ */
  function shiliao(o) {
    var name = o.name || '蓝馨', birth = o.birth, shichen = o.shichen, gender = o.gender;
    var now = o.now;
    var todayStr = ds2(now);
    var nowShichen = M.hourToShichen(now.getHours());
    var nowRange = M.shichenRange(nowShichen);
    var RULE = o.rule || 'book';

    var jgg = M.calc(birth, shichen, gender, RULE);
    var isZishi = !!jgg.isZishi;

    var yangM, yinM, yangM1 = [], yinM1 = [], allM;
    if (isZishi) {
      yangM = uniqSorted(jgg.yangQue || '');
      yinM = uniqSorted(jgg.yinQue || '');
      yangM1 = uniqSorted(jgg.yangQue1 || '');
      yinM1 = uniqSorted(jgg.yinQue1 || '');
      allM = Array.from(new Set(yangM.concat(yangM1, yinM, yinM1))).sort();
    } else {
      yangM = uniqSorted(jgg.yangQue || '');
      yinM = uniqSorted(jgg.yinQue || '');
      allM = Array.from(new Set(yangM.concat(yinM))).sort();
    }
    var halfSup = (jgg.half || '').split('').filter(function (c) { return /\d/.test(c); });
    var halfSup1 = (jgg.half1 || '').split('').filter(function (c) { return /\d/.test(c); });

    var dayAllR = M.calc(todayStr, shichen, gender, RULE);
    var dayNowR = M.calc(todayStr, nowShichen, gender, RULE);
    var dayAll = M.analyzeYun(dayAllR, isZishi ? yangM.join('') + yangM1.join('') : yangM.join(''),
      isZishi ? yinM.join('') + yinM1.join('') : yinM.join(''));
    var dayNow = M.analyzeYun(dayNowR, isZishi ? yangM.join('') + yangM1.join('') : yangM.join(''),
      isZishi ? yinM.join('') + yinM1.join('') : yinM.join(''));

    var R = [];
    R.push('# ' + name + ' · 综合食疗动功方案 v3.3');
    R.push('');
    R.push('**生成时间**：' + ts(now) + '（' + nowShichen + ' ' + nowRange + '）');

    if (isZishi) {
      R.push('**命盘（子时双格）**：');
      R.push('| 类型 | 阳格 | 阴格 | 阳缺 | 阴缺 | 半补 |');
      R.push('|:----:|:-----:|:-----:|:-----:|:-----:|:-----:|');
      R.push('| 当天格 | ' + (jgg.yang || '') + ' | ' + (jgg.yin || '') + ' | ' + yangM.join('') + ' | ' + yinM.join('') + ' | ' + (jgg.half || '') + ' |');
      R.push('| 调整格 | ' + (jgg.yang1 || '') + ' | ' + (jgg.yin1 || '') + ' | ' + yangM1.join('') + ' | ' + yinM1.join('') + ' | ' + (jgg.half1 || '') + ' |');
      R.push('> ' + (jgg.note || '') + ' | 调整日期: ' + (jgg.adjDate || ''));
      R.push('> **综合缺格**：' + Array.from(new Set(yangM.concat(yangM1))).sort().join('') + '/' +
        Array.from(new Set(yinM.concat(yinM1))).sort().join('') + ' → ' +
        allM.map(function (d) { return DIGIT_ORGAN[d] || ''; }).join('、'));
    } else {
      R.push('**命盘**：' + birth + ' ' + shichen + ' | 阳缺' + yangM.join('') + ' 阴缺' + yinM.join('') + ' | 半补' + halfSup.join(''));
    }
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 一、取长补短核心原则');
    R.push('');
    R.push('### 1. 取长（利用半补优势）');
    R.push('');
    if (halfSup.length) {
      R.push('您的命盘**半补数字**：' + halfSup.map(function (d) { return '**' + d + '（' + (DIGIT_ORGAN[d] || '') + '）**'; }).join('、'));
      R.push('**当前时辰（' + nowShichen + '）天时半补**：**' + (dayNow.half || '无') + '**');
      R.push('');
      R.push('**原理**：半补数字代表当前天时环境中该数字的能量得到额外支持，是当下的**天然优势**。');
      R.push('');
      R.push('**当前时辰建议**：');
      halfSup.forEach(function (d) {
        var organ = DIGIT_ORGAN[d] || '';
        var fdb = (o.FOOD_DB[d] || []);
        if (fdb.length) {
          R.push('- **' + d + '（' + organ + '）**：此时段适合进食**' + fdb[0][0] + '**（' + fdb[0][1] + '，' + fdb[0][2] + '），或进行' + organ + '经对应动功');
        }
        R.push('  - 💨 **呼吸练习**：逆腹式呼吸或爱的呼吸（通' + organ + '轮）');
      });
      R.push('');
      var overlap = halfSup.filter(function (d) { return (dayNow.half || '').indexOf(d) >= 0; });
      if (overlap.length) {
        R.push('**天时半补利用**：命盘半补' + overlap[0] + '与天时半补' + dayNow.half + '重叠，此时段（' + nowRange + '）是调理' + overlap[0] + '（' + (DIGIT_ORGAN[overlap[0]] || '') + ')的**黄金时段**。');
      }
    } else {
      R.push('当前无特别半补，参照命盘主导缺格进行日常调理。');
    }
    R.push('');
    R.push('### 2. 补短（补足先天短板）');
    R.push('');
    if (isZishi) {
      R.push('**当天格缺漏**：阳缺**' + yangM.join('') + '**（' + yangM.map(function (d) { return DIGIT_ORGAN[d] || ''; }).join('、') + '）、阴缺**' + yinM.join('') + '**（' + yinM.map(function (d) { return DIGIT_ORGAN[d] || ''; }).join('、') + '）');
      R.push('**调整格缺漏**：阳缺**' + yangM1.join('') + '**（' + yangM1.map(function (d) { return DIGIT_ORGAN[d] || ''; }).join('、') + '）、阴缺**' + yinM1.join('') + '**（' + yinM1.map(function (d) { return DIGIT_ORGAN[d] || ''; }).join('、') + '）');
      R.push('**综合缺格**：阳缺合集**' + Array.from(new Set(yangM.concat(yangM1))).sort().join('') + '**、阴缺合集**' + Array.from(new Set(yinM.concat(yinM1))).sort().join('') + '** → **' + allM.map(function (d) { return DIGIT_ORGAN[d] || ''; }).join('、') + '**');
    } else {
      R.push('**命盘缺漏**：阳缺**' + yangM.join('') + '**（' + yangM.map(function (d) { return DIGIT_ORGAN[d] || ''; }).join('、') + '）、阴缺**' + yinM.join('') + '**（' + yinM.map(function (d) { return DIGIT_ORGAN[d] || ''; }).join('、') + '）');
    }
    R.push('');
    if (allM.length <= 2) R.push('缺格≤2个，**直接针对性补漏**。');
    else R.push('缺格' + allM.length + '个，涉及多个脏腑，需**系统执行食疗+动功双轨并进**方案。');
    R.push('');
    R.push('**行运格的影响**：当前天时阳格**' + dayNow.yang + '**（' + yangMeaning(dayNow.yang) + '）、阴格**' + dayNow.yin + '**（' + yinMeaning(dayNow.yin) + '）。');
    R.push('这些能量正在环境中流动，会暂时影响命盘相关数字的特质。**补漏核心仍应围绕命盘固有缺漏进行**。');
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 二、现状分析与行运共振');
    R.push('');
    R.push('### 今日（' + todayStr + '）行运与命盘共振');
    R.push('');
    if (isZishi) {
      R.push('| 数字 | 脏腑 | 今日天时 | 当天格 | 调整格 | 共振 |');
      R.push('|:----:|:----:|----------|:------:|:------:|:-----:|');
      for (var i = 0; i <= 9; i++) {
        var d = String(i), organ = DIGIT_ORGAN[d] || '';
        var dYq = (dayNow.yangQue || '').indexOf(d) >= 0 ? '阳缺' : '';
        var dIq = (dayNow.yinQue || '').indexOf(d) >= 0 ? '阴缺' : '';
        var tz = (dYq || dIq) ? (dYq + ' ' + dIq).trim() : '正常';
        var bd = (yangM.indexOf(d) >= 0 || yinM.indexOf(d) >= 0) ? '缺' : '正常';
        var bd1 = (yangM1.indexOf(d) >= 0 || yinM1.indexOf(d) >= 0) ? '缺' : '正常';
        var rs = dayNow.l1.indexOf(d) >= 0 ? '🔴 一级' : (dayNow.l2.indexOf(d) >= 0 ? '🟡 二级' : '⚪ 潜伏');
        R.push('| **' + d + '** | ' + organ + ' | ' + tz + ' | ' + bd + ' | ' + bd1 + ' | ' + rs + ' |');
      }
    } else {
      R.push('| 数字 | 脏腑 | 今日天时 | 命盘 | 共振 |');
      R.push('|:----:|:----:|----------|:------|');
      for (var i2 = 0; i2 <= 9; i2++) {
        var d2 = String(i2), organ2 = DIGIT_ORGAN[d2] || '';
        var inB = (yangM.indexOf(d2) >= 0 || yinM.indexOf(d2) >= 0) ? '命盘缺' : '命盘正常';
        var dYq2 = (dayNow.yangQue || '').indexOf(d2) >= 0 ? '阳缺✓' : '';
        var dIq2 = (dayNow.yinQue || '').indexOf(d2) >= 0 ? '阴缺✓' : '';
        var tz2 = (dYq2 || dIq2) ? (dYq2 + ' ' + dIq2).trim() : '正常';
        var rs2 = dayNow.l1.indexOf(d2) >= 0 ? '🔴 一级共振' : (dayNow.l2.indexOf(d2) >= 0 ? '🟡 二级共振' : '⚪ 潜伏期');
        R.push('| **' + d2 + '** | **' + organ2 + '** | ' + tz2 + ' | ' + inB + ' | ' + rs2 + ' |');
      }
    }
    R.push('');
    if (dayNow.l1.length) {
      R.push('**🔴 一级共振器官**（需重点关注）：' + dayNow.l1.map(function (d) { return d + '（' + (DIGIT_ORGAN[d] || '') + ')'; }).join(', '));
      R.push('> 天时缺格与命盘缺格**同类**（阳缺∩阳缺或阴缺∩阴缺），能量缺口最大，需**优先执行**对应食疗+动功方案。');
      R.push('');
    }
    if (dayNow.l2.length) {
      R.push('**🟡 二级共振器官**（需留意）：' + dayNow.l2.map(function (d) { return d + '（' + (DIGIT_ORGAN[d] || '') + ')'; }).join(', '));
      R.push('> 天时缺格与命盘缺格**交叉**（阳缺∩阴缺或阴缺∩阳缺），存在中等能量缺口，需配合日常养护。');
      R.push('');
    }
    R.push('### 今日天时九宫格详情');
    R.push('');
    R.push('- **天时阳格**：**' + dayNow.yang + '** → ' + (dayNow.yang || '').split('').filter(function (c) { return /\d/.test(c); }).map(function (d) { return DIGIT_ORGAN[d] || ''; }).join(''));
    R.push('- **天时阴格**：**' + dayNow.yin + '** → ' + (dayNow.yin || '').split('').filter(function (c) { return /\d/.test(c); }).map(function (d) { return DIGIT_ORGAN[d] || ''; }).join(''));
    R.push('- **天时阳缺**：' + (dayNow.yangQue || '无') + ' → ' + (dayNow.yangQue ? queOrgans(dayNow.yangQue) : '无缺格'));
    R.push('- **天时阴缺**：' + (dayNow.yinQue || '无') + ' → ' + (dayNow.yinQue ? queOrgans(dayNow.yinQue) : '无缺格'));
    R.push('- **天时半补**：' + (dayNow.half || '无'));
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 三、综合食疗建议（针对命盘缺漏）');
    R.push('');
    var pri = {};
    dayNow.l1.forEach(function (d) { pri[d] = '🔴'; });
    dayNow.l2.forEach(function (d) { pri[d] = '🟡'; });
    R.push('| 优先级 | 数字 | 脏腑 | 核心食疗方案 | 关键禁忌 |');
    R.push('|:-------:|:----:|:----:|-------------|----------|');
    for (var k = 0; k <= 9; k++) {
      var dk = String(k), orgk = DIGIT_ORGAN[dk] || '';
      var rdb = (o.REMEDY_DB[dk] || {});
      var core = rdb['核心'] || '对应食疗调理';
      var prohibitions = rdb['禁忌'] || [];
      var fdb2 = (o.FOOD_DB[dk] || []);
      var foodStr = fdb2.slice(0, 2).map(function (t) { return t[0] + '（' + t[1] + '）'; }).join('；');
      var proStr = prohibitions.slice(0, 2).join('；') || '参照各经脉禁忌';
      R.push('| **' + (pri[dk] || '⚪') + dk + '** | **' + dk + '** | **' + orgk + '** | ' + core + '。推荐：' + foodStr + ' | ' + proStr + ' |');
    }
    R.push('');
    R.push('### 食疗综合执行要点');
    R.push('');
    if (allM.indexOf('2') >= 0 || allM.indexOf('4') >= 0) R.push('**蔬菜配方**（2大肠+4肝联调）：紫色洋葱+西兰花+大白菜，蒸煮，连续34天为基础。');
    if (allM.indexOf('6') >= 0) R.push('**黑米套餐**（6肾核心）：黑米+黑豆+核桃+枸杞+黄精，发芽后熬粥，早晚各一份。');
    if (allM.indexOf('5') >= 0) R.push('**宁化府饺子醋**（5胆核心）：饭前15分钟20-30克，同时有助去半魄。');
    if (allM.indexOf('8') >= 0) R.push('**河南铁棍山药**（8脾特效）：带皮蒸食，每日约10公分段，配合发芽谷物。');
    if (allM.indexOf('3') >= 0 || halfSup.length) R.push('**小白瓶**（3心/通心轮）：按周期服用，配合莲子清心火。');
    R.push('');
    R.push('**通用禁忌**（执行期间严格遵守）：');
    o.PROHIBIT.forEach(function (p) { R.push('- ' + p); });
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 四、动功与呼吸练习建议');
    R.push('');
    R.push('### 核心动功（每日必练）');
    o.DG_CORE.forEach(function (dg) {
      R.push('**' + dg.name + '**');
      R.push('- 目标：' + dg.target + '，功效：' + dg.desc);
      R.push('- 要点：' + dg['要点'] + '，禁忌：' + dg['禁忌']);
      R.push('');
    });
    R.push('### 八段锦（辅助经脉调理）');
    o.DG_BADUANJIN.forEach(function (dg) { R.push('- **' + dg.name + '**：' + dg.target + '，' + dg.desc); });
    R.push('');
    R.push('### 呼吸练习（每日定时）');
    o.DG_HUXI.forEach(function (dg) { R.push('- **' + dg.name + '**：' + dg.target + '，' + dg.desc); });
    R.push('');
    R.push('### 莲花生动功（高级）');
    o.DG_LIANHUA.forEach(function (dg) { R.push('- **' + dg.name + '**：' + dg.target + '，' + dg.desc); });
    R.push('');
    R.push('**执行顺序**：熊经鸟伸 → 枯树盘根 → 八段锦 → 呼吸练习');
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 五、当前时辰活用建议');
    R.push('');
    R.push('**当前时辰**：**' + nowShichen + '**（' + nowRange + '）');
    R.push('');
    R.push('- 天时阳格：**' + dayNow.yang + '**（' + yangMeaning(dayNow.yang) + '）');
    R.push('- 天时阴格：**' + dayNow.yin + '**（' + yinMeaning(dayNow.yin) + '）');
    R.push('- 天时半补：**' + (dayNow.half || '无') + '**');
    R.push('- 天时阳缺：' + (dayNow.yangQue || '无') + ' → ' + (dayNow.yangQue ? queOrgans(dayNow.yangQue) : '无缺格'));
    R.push('- 天时阴缺：' + (dayNow.yinQue || '无') + ' → ' + (dayNow.yinQue ? queOrgans(dayNow.yinQue) : '无缺格'));
    R.push('');
    R.push('**此时段行动建议**：');
    if (dayNow.l1.length) {
      dayNow.l1.forEach(function (d) {
        var organ = DIGIT_ORGAN[d] || '';
        var fdb3 = (o.FOOD_DB[d] || []);
        var rdb2 = (o.REMEDY_DB[d] || {});
        if (fdb3.length) R.push('- 🔴 **优先处理' + d + '（' + organ + '）**：此时段适合进食**' + fdb3[0][0] + '**（' + fdb3[0][1] + '，' + fdb3[0][2] + '），或进行' + organ + '经对应动功');
        if (rdb2['方案'] && rdb2['方案'].length) R.push('  - 修正要点：' + rdb2['方案'][0]);
      });
    }
    if (dayNow.half) {
      (dayNow.half || '').split('').forEach(function (d) {
        if (dayNow.l1.indexOf(d) < 0) {
          var organ = DIGIT_ORGAN[d] || '';
          R.push('- 💪 **利用半补' + d + '（' + organ + '）优势**：此时段' + organ + '能量最旺，适合进行' + organ + '经对应动功或呼吸练习');
        }
      });
    }
    if (!dayNow.l1.length && !dayNow.half) R.push('- 📊 当前时辰能量平稳，进行日常呼吸练习和轻微动功即可');
    R.push('');
    R.push('---');
    R.push('');
    R.push('## 六、每日执行核心（精简版）');
    R.push('');
    Object.keys(o.DAILY).forEach(function (slot) { R.push('- **' + slot + '**：' + o.DAILY[slot]); });
    R.push('');
    if (dayNow.l1.length) {
      R.push('**本周重点**：一级共振器官 ' + dayNow.l1.map(function (d) { return d + '（' + (DIGIT_ORGAN[d] || '') + ')'; }).join(', ') + ' 需每日重点执行对应食疗+动功方案。');
    }
    R.push('');
    R.push('---');
    R.push('');
    R.push('*报告生成：' + ts(now) + ' · v3.3 · 基于nine_palace_core_v5*');
    return R.join('\n');
  }

  function yangMeaning(grid) {
    var out = [];
    (grid || '').split('').forEach(function (d) { if (/\d/.test(d)) out.push(YANG_MEANING[d] || d); });
    return out.length ? out.join('、') : '无';
  }
  function yinMeaning(grid) {
    var out = [];
    (grid || '').split('').forEach(function (d) { if (/\d/.test(d)) out.push(YIN_MEANING[d] || d); });
    return out.length ? out.join('、') : '无';
  }
  function queOrgans(queStr) {
    var out = [];
    (queStr || '').split('').forEach(function (d) { if (/\d/.test(d)) out.push(DIGIT_ORGAN[d] || ''); });
    return out.length ? out.join('、') : '无';
  }

  M.REPORTS = { comprehensive: comprehensive, ni: ni, shiliao: shiliao, ts: ts, ds2: ds2 };
})(typeof window !== 'undefined' ? window : globalThis);
