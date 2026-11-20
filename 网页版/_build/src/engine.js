/* ============================================================
 * 慈海九宫格 · 算法内核（JS 移植版）
 * 逐函数对照 核心引擎/nine_palace_core_v5.py + 查询工具/nine_palace_query.py
 * 任何改动都必须重跑 `比对引擎.py` 全量验证（见 _build/verify_engine.js）
 * ============================================================ */
(function (root) {
  'use strict';

  /* ---------- 农历表解码 ---------- */
  var B36 = '0123456789abcdefghijklmnopqrstuvwxyz';
  var L = { start: [], ly: [], lm: [], leap: [], ok: false };

  function lunarInit(t) {
    var s = t.s, n = t.n, y0 = t.y0;
    var cur = 0, ly = y0;
    L.start = new Array(n); L.ly = new Array(n); L.lm = new Array(n); L.leap = new Array(n);
    for (var i = 0; i < n; i++) {
      var mo = B36.indexOf(s.charAt(i * 3));
      var lp = s.charAt(i * 3 + 1) === '1';
      var len = B36.indexOf(s.charAt(i * 3 + 2));
      if (i > 0 && mo === 1 && !lp) ly += 1;
      L.start[i] = cur; L.ly[i] = ly; L.lm[i] = mo; L.leap[i] = lp;
      cur += len;
    }
    L.total = cur;
    L.ok = true;
  }

  function ord(y, m, d) {
    // 1900-01-01 为 0 的天序
    var a = Date.UTC(y, m - 1, d), b = Date.UTC(1900, 0, 1);
    return Math.round((a - b) / 86400000);
  }

  /** 公历 → 农历；超出表范围返回 null（对应 Python 的 except → '0'） */
  function solar2lunar(y, m, d) {
    if (!L.ok) return null;
    var o = ord(y, m, d);
    if (o < 0 || o >= L.total) return null;
    var lo = 0, hi = L.start.length - 1, idx = 0;
    while (lo <= hi) {
      var mid = (lo + hi) >> 1;
      if (L.start[mid] <= o) { idx = mid; lo = mid + 1; } else { hi = mid - 1; }
    }
    return { y: L.ly[idx], m: L.lm[idx], d: o - L.start[idx] + 1, leap: L.leap[idx] };
  }

  /* ---------- 基础工具（镜像 Python 语义） ---------- */
  function ds(n) {
    var s = String(n), t = 0;
    for (var i = 0; i < s.length; i++) if (s[i] >= '0' && s[i] <= '9') t += +s[i];
    return t;
  }
  function rds(n) { var s = n; while (s >= 10) s = ds(s); return s; }

  function digitsOf(v, width) {
    var s = width ? String(v).padStart(width, '0') : String(v), a = [];
    for (var i = 0; i < s.length; i++) if (s[i] >= '0' && s[i] <= '9') a.push(+s[i]);
    return a;
  }

  /** Counter：保留首次出现顺序（= Python dict 插入顺序） */
  function counter(arr) {
    var m = new Map();
    for (var i = 0; i < arr.length; i++) {
      var k = arr[i];
      m.set(k, (m.get(k) || 0) + 1);
    }
    return m;
  }

  /** getUpgraded：魄超过 3 个同数字 → 升为辅魂；按数字升序 */
  function getUpgraded(po) {
    var m = counter(po), keys = Array.from(m.keys()).sort(function (a, b) { return a - b; });
    var up = [];
    keys.forEach(function (d) {
      var c = m.get(d);
      if (c >= 3) for (var i = 0; i < Math.floor(c / 3); i++) up.push(d);
    });
    return up;
  }

  /* ---------- 阳格 ---------- */
  function yangCalc(y, m, d) {
    var po = digitsOf(y).concat(digitsOf(m, 2)).concat(digitsOf(d, 2));
    var tot = po.reduce(function (a, b) { return a + b; }, 0);
    var up = getUpgraded(po);

    if (tot < 10) {                                   // 路线 B
      var main = tot;
      var base = [ds(y), ds(m), ds(d)];
      var sB = up.concat(base).concat([main]).join('');
      var cB = counter(sB.split(''));
      var newB = [];
      cB.forEach(function (c, k) { if (c >= 3 && +k !== main) newB.push(+k); });
      var partsB = up.concat(base).concat([main]).concat(newB);
      return { grid: partsB.join(''), po: po, up: up, route: 'B',
               parts: partsB, main: main, extra: newB };
    }

    var main2 = rds(tot);                             // 路线 A / MultiSoul
    var ivs = [tot];
    var s = tot;
    while (s >= 10) { s = ds(s); if (s >= 10) ivs.push(s); }

    if (tot === 10 && up.length >= 2) {
      var dsY = ds(y), dsM = ds(m), dsD = ds(d);
      var day1 = +String(d).padStart(2, '0').charAt(0);
      var ivF = ivs.length ? +String(ivs[0]).charAt(0) : 0;
      var res = '' + up[0] + up[1] + dsY + dsM + day1 + main2 + up[0] + ivF + dsD;
      return { grid: res, po: po, up: up, route: 'MultiSoul',
               parts: String(res).split(''), main: main2, extra: [] };
    }

    var partsA = up.concat(ivs).concat([main2]);
    var cA = counter(partsA.join('').split(''));
    var newA = [];
    cA.forEach(function (c, k) { if (c >= 3 && +k !== main2) newA.push(+k); });
    var partsA2 = up.concat(ivs).concat([main2]).concat(newA);
    return { grid: partsA2.join(''), po: po, up: up, route: 'A',
             parts: partsA2, main: main2, extra: newA };
  }

  /* ---------- 阴格 ---------- */
  function yinCalc(y, m, d) {
    var lu = solar2lunar(y, m, d);
    if (!lu) return { grid: '0', po: [] };            // Python: except → ('0', [])
    var ly = lu.y, lm = lu.m, ld = lu.d;
    var po = digitsOf(ly).concat(digitsOf(lm, 2)).concat(digitsOf(ld, 2));
    var g = yangCalc(ly, lm, ld).grid;
    /* 注意：原引擎 `leap = lunarcalendar.month < 0` 恒为假（该库 month 恒正），
       故从不为闰月加 '1' 前缀。此处完全对齐，不做「修正」。 */
    return { grid: g, po: po };
  }

  /* ---------- 缺数 ---------- */
  function missingNum(g, poSet) {
    if (!g || g === '0') return '0123456789';
    var p = new Set();
    for (var i = 0; i < g.length; i++) if (g[i] >= '0' && g[i] <= '9') p.add(+g[i]);
    if (poSet && poSet.length) poSet.forEach(function (x) { p.add(+x); });
    var out = '';
    for (var dgt = 0; dgt <= 9; dgt++) if (!p.has(dgt)) out += dgt;
    return out;
  }

  var HALF_MAP = {
    '申时': '12', '酉时': '12', '寅时': '45', '卯时': '45',
    '亥时': '06', '子时': '06', '前子时': '06', '后子时': '06',
    '巳时': '3', '午时': '3', '辰时': '789', '戌时': '789',
    '丑时': '789', '未时': '789'
  };
  function halfSup(s) {
    if (!s || s === '未知时辰' || s === 'unknown' || s === '') return null;
    return HALF_MAP[s] || null;
  }

  /* ---------- 阴阳属性 ---------- */
  var DIGIT_YIN = { '1': '肺', '3': '心', '4': '肝', '6': '肾', '8': '脾' };
  var DIGIT_YANG = { '2': '大肠', '5': '胆', '7': '胃', '9': '膀胱', '0': '小肠' };

  function digitYinYang(d) {
    var k = String(d);
    if (DIGIT_YIN[k]) return { attr: '阴（脏）', organ: DIGIT_YIN[k] };
    if (DIGIT_YANG[k]) return { attr: '阳（腑）', organ: DIGIT_YANG[k] };
    return { attr: '未知', organ: '未知' };
  }

  function analyzeGridYinYang(grid) {
    var yin = 0, yang = 0, yinD = [], yangD = [];
    var s = String(grid);
    for (var i = 0; i < s.length; i++) {
      var c = s[i];
      if (DIGIT_YIN[c]) { yin++; yinD.push(c + '(' + DIGIT_YIN[c] + ')'); }
      else if (DIGIT_YANG[c]) { yang++; yangD.push(c + '(' + DIGIT_YANG[c] + ')'); }
    }
    var tot = yin + yang, trend;
    if (tot === 0) trend = '无';
    else {
      var r = yin / tot;
      trend = r > 0.6 ? '偏阴' : (r < 0.4 ? '偏阳' : '平衡');
    }
    return { yin: yin, yang: yang, yinD: yinD, yangD: yangD, trend: trend };
  }

  /* ---------- 灵魂详情（v5） ---------- */
  function calcSoulDetail(yang, po, up) {
    if (!yang) return {};
    var mainSoul = yang.charAt(yang.length - 1);
    var auxSoul = yang.length > 1 ? yang.slice(0, -1) : '';
    var m = counter(po), upd = [];
    Array.from(m.keys()).sort(function (a, b) { return a - b; }).forEach(function (num) {
      var c = m.get(num);
      if (c >= 3) upd.push(num + '出现' + c + '次→升级为辅魂' + num);
    });
    return {
      mainSoul: mainSoul, auxSoul: auxSoul,
      auxNote: auxSoul ? '共' + auxSoul.length + '位辅助能量' : '无辅魂',
      up: up, upNote: upd.length ? upd.join('; ') : '无魄升级为辅魂',
      poCount: po.length, poList: po.slice()
    };
  }

  /* ---------- 阴阳格生命周期（原样复刻，含命名重复） ---------- */
  var CYCLE_PARAMS = {
    male: { yang: 11.9, yin: 9.7, trans: 2.3, desc: '男性固定周期制' },
    female: { yang: 9.7, yin: 11.9, trans: 2.3, desc: '女性生育影响制' }
  };

  function calcLifeCycle(birthYear, gender, currentYear) {
    if (currentYear == null) currentYear = new Date().getFullYear();
    var age = currentYear - birthYear;
    var p = CYCLE_PARAMS[gender] || CYCLE_PARAMS.male;
    var cycles = [], cur = 0, k = 0;
    while (cur < 120) {
      cycles.push({ phase: '阳格' + (k + 1), start: cur, end: cur + p.yang, type: '阳格' });
      cur += p.yang;
      cycles.push({ phase: '换魂' + (k + 1), start: cur, end: cur + p.trans, type: '换魂' });
      cur += p.trans;
      cycles.push({ phase: '阴格' + (k + 1), start: cur, end: cur + p.yin, type: '阴格' });
      cur += p.yin;
      cycles.push({ phase: '换魂' + (k + 2), start: cur, end: cur + p.trans, type: '换魂' });
      cur += p.trans;
      k++;
    }
    var nowPhase = null, next = null;
    for (var i = 0; i < cycles.length; i++) {
      if (cycles[i].start <= age && age < cycles[i].end) { nowPhase = cycles[i]; break; }
    }
    for (var j = 0; j < cycles.length; j++) {
      if (cycles[j].type === '换魂' && cycles[j].start > age) { next = cycles[j]; break; }
    }
    return {
      age: age, cycles: cycles,
      phase: nowPhase ? nowPhase.phase : '未知',
      type: nowPhase ? nowPhase.type : '未知',
      start: nowPhase ? nowPhase.start : 0,
      end: nowPhase ? nowPhase.end : 0,
      nextPhase: next ? next.phase : '无',
      nextAge: next ? next.start : 0,
      toNext: next ? next.start - age : 0,
      params: p
    };
  }

  /* ---------- 主计算 ---------- */
  function parseDate(str) {
    var s = String(str).trim().replace(/\//g, '-');
    var m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(s);
    if (!m) return null;
    var y = +m[1], mo = +m[2], da = +m[3];
    var dt = new Date(Date.UTC(y, mo - 1, da));
    if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== mo - 1 || dt.getUTCDate() !== da) return null;
    return { y: y, m: mo, d: da };
  }

  function addDays(o, n) {
    var dt = new Date(Date.UTC(o.y, o.m - 1, o.d) + n * 86400000);
    return { y: dt.getUTCFullYear(), m: dt.getUTCMonth() + 1, d: dt.getUTCDate() };
  }

  /**
   * @param {string} dateStr  'YYYY/MM/DD' 或 'YYYY-MM-DD'
   * @param {string} shichen  '巳时' / '前子时' / … / '未知'
   * @param {string} gender   'male' / 'female'
   * @param {string} zishiRule
   *   'book'  前子时 +1 天 / 后子时 −1 天 —— 与卢先生原书一致（本页默认）
   *   'v5'    前子时 −1 天 / 后子时 +1 天 —— 核心引擎 v5，两个分支都反，仅供对齐历史 .md
   *   'query' 前子时 +1 天 / 后子时  0 天 —— 查询工具原样，后子时不换日（两套格退化相同）
   *   依据《九宫解译历史人物》1-6「子时的人」：前子时加一天算另一套、后子时减一天算另一套。
   */
  function calc(dateStr, shichen, gender, zishiRule) {
    var dt = parseDate(dateStr);
    if (!dt) throw new Error('日期格式错误：' + dateStr);
    /* 缺省用原书口径。'v5' 两个分支都反，只有三个 .md 报告生成器为了与
       完整综合命理报告v3.9.py 逐字节一致才显式传它。 */
    var rule = zishiRule || 'book';
    var y = dt.y, mo = dt.m, da = dt.d;
    var isZishi = !!(shichen && shichen.indexOf('子时') >= 0);
    var isQian = !!(shichen && shichen.indexOf('前子时') >= 0);

    function one(yy, mm, dd) {
      var yg = yangCalc(yy, mm, dd);
      var ig = yinCalc(yy, mm, dd);
      return {
        yang: yg.grid, yin: ig.grid,
        yangQue: missingNum(yg.grid, yg.po),
        yinQue: missingNum(ig.grid, ig.po.length ? ig.po : null),
        half: halfSup(shichen),
        po: yg.po, up: yg.up, route: yg.route,
        parts: yg.parts, main: yg.main, extra: yg.extra,
        soulDetail: calcSoulDetail(yg.grid, yg.po, yg.up),
        yyYang: analyzeGridYinYang(yg.grid),
        yyYin: analyzeGridYinYang(ig.grid),
        lunar: solar2lunar(yy, mm, dd),
        lunarPo: ig.po
      };
    }

    var res = {
      date: dateStr, shichen: shichen || '未知', gender: gender || '未指定',
      type: isZishi ? '子时双格' : '普通阴阳双格',
      solar: dt, rule: rule, isZishi: isZishi, isQian: isQian
    };

    if (isZishi) {
      var r1 = one(y, mo, da);
      /* 三套口径的位移表，见上方注释。'book' 是唯一让两套格必然不同的那个。 */
      var shift = rule === 'v5' ? (isQian ? -1 : 1)
                : rule === 'query' ? (isQian ? 1 : 0)
                : (isQian ? 1 : -1);
      var adj = addDays(dt, shift);
      var r2 = one(adj.y, adj.m, adj.d);
      var adjStr = adj.y + '/' + String(adj.m).padStart(2, '0') + '/' + String(adj.d).padStart(2, '0');
      res.a = r1; res.b = r2;
      res.yang = r1.yang; res.yin = r1.yin; res.yangQue = r1.yangQue; res.yinQue = r1.yinQue;
      res.half = r1.half;
      res.yang1 = r2.yang; res.yin1 = r2.yin; res.yangQue1 = r2.yangQue; res.yinQue1 = r2.yinQue;
      res.half1 = r2.half;
      res.adjDate = adjStr;
      if (rule === 'v5') {
        res.note = isQian ? '前子时实际属于前一天(' + adjStr + ')' : '后子时属于后一天(' + adjStr + ')';
      } else if (rule === 'query') {
        res.note = isQian ? '前子时：另一套取后一天(' + adjStr + ')' : '后子时：查询工具不换日，与当天格相同';
      } else {
        res.note = isQian ? '前子时：另一套取后一天(' + adjStr + ')' : '后子时：另一套取前一天(' + adjStr + ')';
      }
      res.yyYang = r1.yyYang; res.yyYin = r1.yyYin;
    } else {
      var r = one(y, mo, da);
      res.a = r;
      res.yang = r.yang; res.yin = r.yin; res.yangQue = r.yangQue; res.yinQue = r.yinQue;
      res.half = r.half;
      res.yyYang = r.yyYang; res.yyYin = r.yyYin;
    }

    if (gender) res.life = calcLifeCycle(y, gender);
    return res;
  }

  /* ---------- 灵魂库查询 ---------- */
  function normZero(s) {
    if (/^\d+$/.test(s)) return String(parseInt(s, 10));
    return s.replace(/^0+/, '');
  }

  /** 查灵魂积分。三档置信度（2026-10-27 修：前缀兜底不再给结论）
   *   conf='exact'      原库精确命中 —— 唯一可当原书结论用的
   *   conf='same-root'  剥前导零后命中（先天形态 / 后天落形态同源，如 0213 ↔ 213），推定
   *   conf='near'       rec=null，只回 near 供「疑似同族」提示，不出星级与名称
   *   null              未收录
   * 起因：原实现照抄 Python 的 startswith 兜底，在 605 种真实阳格上把 7.05% 的天数
   * 张冠李戴（02167/02145/02134/02189 全被判成 0219101；1246 被判成 12433101）。 */
  function lookupSoulScore(grid, DB) {
    var g = String(grid);
    if (DB[g]) return { key: g, rec: DB[g], conf: 'exact' };
    var stripped = /^\d+$/.test(g) ? String(parseInt(g, 10)) : g.replace(/^0+/, '');
    if (stripped && stripped !== g && DB[stripped]) return { key: stripped, rec: DB[stripped], conf: 'same-root' };
    var s2 = g.replace(/^0+/, '');
    if (s2 && s2 !== g && DB[s2]) return { key: s2, rec: DB[s2], conf: 'same-root' };
    var near = null, keys = Object.keys(DB), i;
    for (i = 0; i < keys.length; i++) {
      if (g.indexOf(keys[i]) === 0 || keys[i].indexOf(g) === 0) { near = { key: keys[i], how: 'prefix' }; break; }
    }
    if (!near && g.length >= 4) {
      var pre3 = g.slice(0, 3);
      for (i = 0; i < keys.length; i++) if (keys[i].indexOf(pre3) === 0) { near = { key: keys[i], how: 'pre3' }; break; }
    }
    if (near) return { key: null, rec: null, conf: 'near', near: near };
    return null;
  }

  /** v5 lookupSoul（用于补 天赋/使命）—— 同上：前缀只作提示，不当作身份 */
  function lookupSoulV5(grid, DB) {
    var g = String(grid);
    if (DB[g]) return { key: g, rec: DB[g], conf: 'exact' };
    var near = null, keys = Object.keys(DB), i;
    for (i = 0; i < keys.length; i++) {
      if (g.indexOf(keys[i]) === 0 || keys[i].indexOf(g) === 0) { near = { key: keys[i], how: 'prefix' }; break; }
    }
    if (!near && g.length >= 4) {
      var p3 = g.slice(0, 3);
      for (i = 0; i < keys.length; i++) if (keys[i].indexOf(p3) === 0) { near = { key: keys[i], how: 'pre3' }; break; }
    }
    if (near) return { key: null, rec: null, conf: 'near', near: near };
    return null;
  }

  /* ---------- 组合 / 单格解读 ---------- */
  function getCombo(yg, ig, COMBO) {
    var ys = String(yg), is = String(ig);
    var yn = normZero(ys), inn = normZero(is);
    var cand = [ys + '-' + is, is + '-' + ys, yn + '-' + inn, inn + '-' + yn];
    for (var i = 0; i < cand.length; i++) if (COMBO[cand[i]]) return { key: cand[i], rec: COMBO[cand[i]] };
    if (yn === inn && COMBO[yn + '-' + yn]) return { key: yn + '-' + yn, rec: COMBO[yn + '-' + yn] };
    return null;
  }

  function stripLeadingZeros(s) {
    if (!s) return s;
    if (/^\d+$/.test(s)) {
      for (var i = 0; i < s.length; i++) if (s[i] !== '0') return s.slice(i);
      return s.slice(-1);
    }
    return s.replace(/^0+/, '') || s;
  }

  function getSingle(grid, SINGLE) {
    if (!grid) return null;
    var gs = String(grid);
    if (SINGLE[gs]) return { key: gs, rec: SINGLE[gs] };
    var g2 = stripLeadingZeros(gs);
    if (g2 && g2 !== gs && SINGLE[g2]) return { key: g2, rec: SINGLE[g2] };
    var keys = Object.keys(SINGLE), hits = [];
    for (var i = 0; i < keys.length; i++) if (keys[i].length <= 5 && gs.indexOf(keys[i]) >= 0) hits.push(keys[i]);
    if (hits.length) { hits.sort(function (a, b) { return b.length - a.length; }); return { key: hits[0], rec: SINGLE[hits[0]] }; }
    for (var j = 0; j < keys.length; j++) if (keys[j].length <= 5 && gs.indexOf(keys[j]) === 0) return { key: keys[j], rec: SINGLE[keys[j]] };
    return null;
  }

  /* ---------- 行运共振 ----------
     注意：一级与二级**允许重叠**（同一数字可同时满足两类条件），
     原引擎用两个独立集合运算，不互斥 —— 不可写成 else if。 */
  function analyzeYun(day, birthYangQue, birthYinQue) {
    var dy = new Set((day.yangQue || '').split('').filter(function (c) { return /\d/.test(c); }));
    var di = new Set((day.yinQue || '').split('').filter(function (c) { return /\d/.test(c); }));
    var by = new Set((birthYangQue || '').split('').filter(function (c) { return /\d/.test(c); }));
    var bi = new Set((birthYinQue || '').split('').filter(function (c) { return /\d/.test(c); }));
    var l1 = [], l2 = [];
    for (var d = 0; d <= 9; d++) {
      var s = String(d);
      if ((dy.has(s) && by.has(s)) || (di.has(s) && bi.has(s))) l1.push(s);
      if ((dy.has(s) && bi.has(s)) || (di.has(s) && by.has(s))) l2.push(s);
    }
    return {
      yang: day.yang, yin: day.yin, yangQue: day.yangQue, yinQue: day.yinQue,
      half: day.half, l1: l1, l2: l2
    };
  }

  /* ---------- 时辰工具 ---------- */
  var SHICHEN_LIST = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时', '午时', '未时', '申时', '酉时', '戌时', '亥时'];
  function hourToShichen(h) {
    if (h === 23 || h < 1) return '子时';
    var i = Math.floor((h + 1) / 2);
    if (i >= 12) i = 11;
    return SHICHEN_LIST[i];
  }
  function shichenRange(sc) {
    var i = SHICHEN_LIST.indexOf(sc); if (i < 0) i = 0;
    if (i === 0) return '23:00-01:00';
    var a = i * 2 - 1, b = i * 2 + 1;
    return String(a).padStart(2, '0') + ':00-' + String(b).padStart(2, '0') + ':00';
  }

  /* ---------- 真太阳时 ---------- */
  function trueSolar(y, m, d, hour, minute, lat, lon, tz) {
    tz = tz || 8;
    var standardLon = tz * 15;
    var lonDiff = lon - standardLon;
    var doy = Math.floor((Date.UTC(y, m - 1, d) - Date.UTC(y, 0, 1)) / 86400000) + 1;
    var B = 2 * 3.14159 * (doy - 81) / 365;
    var EoT = 9.87 * Math.sin(2 * B) - 7.53 * Math.cos(B) - 1.5 * Math.sin(B);
    var diff = lonDiff * 4 + EoT;               // 分钟
    var base = new Date(Date.UTC(y, m - 1, d, hour, minute) + diff * 60000);
    var hh = base.getUTCHours(), mi = base.getUTCMinutes();
    return { hour: hh, minute: mi, shichen: hourToShichen(hh), diff: Math.round(diff * 10) / 10,
             iso: base.getUTCFullYear() + '-' + String(base.getUTCMonth() + 1).padStart(2, '0') + '-' + String(base.getUTCDate()).padStart(2, '0') + ' ' + String(hh).padStart(2, '0') + ':' + String(mi).padStart(2, '0') };
  }
  function lookupCity(name, CITY) {
    if (!name) return null;
    name = String(name).trim();
    if (CITY[name]) return CITY[name];
    var keys = Object.keys(CITY);
    for (var i = 0; i < keys.length; i++) if (name.indexOf(keys[i]) >= 0 || keys[i].indexOf(name) >= 0) return CITY[keys[i]];
    if (name.indexOf(',') >= 0) {
      var p = name.split(',');
      if (p.length === 2) {
        var la = parseFloat(p[0]), lo = parseFloat(p[1]);
        if (!isNaN(la) && !isNaN(lo) && la >= -90 && la <= 90 && lo >= -180 && lo <= 180) return [la, lo];
      }
    }
    return null;
  }

  /* ══════════ 格稀有度（1910–2101 逐日实测） ══════════
     单格：稀有系数 K = N / 出现次数（「平均每 K 天才出现一次」）
           子分 S = 100·ln(K)/ln(N)          —— N 天里只出现 1 次 ⇒ 100 分
     双格：名义叠加 K_nom = K_y × K_i        —— 独立假设下的值，仅作参照
           实测 K_real = N / 该组合真实出现天数
     为什么不用名义叠加直接打分：
       实测 12,152 种双格组合，log(K_nom) 与 log(K_real) 的相关只有
       Pearson 0.644 / Spearman 0.678，中位偏差 265% —— 阴格取自农历日期，
       与阳历日期强相关，独立性根本不成立（例 121121|1167：名义 145 万倍，
       实测 17,532 倍，差 84 倍）。故打分以实测为准。
     综合打分 = 0.25·S_y + 0.25·S_i + 0.5·S_real（双格权重加倍）。 */
  function rScore(K, N) { return 100 * Math.log(K) / Math.log(N); }

  function pairCount(yg, ig, J) {
    var k = yg + '|' + ig;
    if (J.map && Object.prototype.hasOwnProperty.call(J.map, k)) return J.map[k];
    return 1;   /* map 只存 >=2 次的组合；其余只要历史上出现过就是 1 次 */
  }

  function pairHist(J) {
    var h = J.hist || {}, tot = 0;
    Object.keys(h).forEach(function (k) { tot += h[k]; });
    return { h: h, tot: tot };
  }

  function pairPercentile(c, J) {
    var t = pairHist(J), less = 0;
    Object.keys(t.h).forEach(function (k) { if (+k < c) less += t.h[k]; });
    return t.tot ? (1 - less / t.tot) * 100 : 0;   /* 超过 xx% 的组合更稀有 */
  }

  function bandOf(score) {
    if (score >= 82) return { t: '极稀', c: 'lv2' };
    if (score >= 74) return { t: '稀有', c: 'lv1' };
    if (score >= 64) return { t: '少见', c: 'lv0' };
    if (score >= 52) return { t: '常见', c: 'lv0' };
    return { t: '高频', c: 'lv0' };
  }

  function rarity(yg, ig, F, J) {
    var N = F.days, cy = F.yang[yg] || 0, ci = F.yin[ig] || 0;
    if (!N || !cy || !ci) return null;
    var cj = pairCount(yg, ig, J);
    var Ky = N / cy, Ki = N / ci, Kr = N / cj;
    var Sy = rScore(Ky, N), Si = rScore(Ki, N), Sr = rScore(Kr, N);
    var score = 0.25 * Sy + 0.25 * Si + 0.5 * Sr;
    return {
      N: N, cy: cy, ci: ci, cj: cj,
      Ky: Ky, Ki: Ki, Knom: Ky * Ki, Kr: Kr,
      Sy: Sy, Si: Si, Sr: Sr, score: score,
      pct: pairPercentile(cj, J),
      band: bandOf(score),
      ratio: Kr / (Ky * Ki)      /* 实测 / 名义 */
    };
  }

  /* 出现次数分档（分布图用，全部由 hist 现算） */
  var PAIR_BUCKETS = [[1, 1, '1 次'], [2, 2, '2 次'], [3, 5, '3–5 次'],
                      [6, 20, '6–20 次'], [21, 100, '21–100 次'], [101, 1e9, '100 次以上']];
  function pairBuckets(J) {
    var t = pairHist(J), out = [];
    PAIR_BUCKETS.forEach(function (b) {
      var n = 0;
      Object.keys(t.h).forEach(function (k) {
        var c = +k;
        if (c >= b[0] && c <= b[1]) n += t.h[k];
      });
      out.push({ label: b[2], n: n, tot: t.tot });
    });
    return { rows: out, tot: t.tot };
  }

  root.MAGIC = {
    lunarInit: lunarInit, solar2lunar: solar2lunar,
    ds: ds, rds: rds, getUpgraded: getUpgraded, yangCalc: yangCalc, yinCalc: yinCalc,
    missingNum: missingNum, halfSup: halfSup, HALF_MAP: HALF_MAP,
    digitYinYang: digitYinYang, analyzeGridYinYang: analyzeGridYinYang,
    calcSoulDetail: calcSoulDetail, calcLifeCycle: calcLifeCycle, CYCLE_PARAMS: CYCLE_PARAMS,
    calc: calc, parseDate: parseDate,
    lookupSoulScore: lookupSoulScore, lookupSoulV5: lookupSoulV5,
    getCombo: getCombo, getSingle: getSingle, normZero: normZero, stripLeadingZeros: stripLeadingZeros,
    analyzeYun: analyzeYun, SHICHEN_LIST: SHICHEN_LIST,
    hourToShichen: hourToShichen, shichenRange: shichenRange,
    trueSolar: trueSolar, lookupCity: lookupCity,
    rarity: rarity, pairBuckets: pairBuckets, pairPercentile: pairPercentile,
    rScore: rScore, pairCount: pairCount,
    _L: L
  };
})(typeof window !== 'undefined' ? window : globalThis);
