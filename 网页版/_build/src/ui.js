/* ============================================================
 * 慈海九宫格 · 即时解读 — 页面逻辑
 * ============================================================ */
(function () {
  'use strict';

  var D = window.__DATA__;
  var M = window.MAGIC;
  var MD = window.MD;

  var TABS = [
    ['命盘概要', '0'], ['详细解读', '1'], ['跌落路径', '2'], ['命理报告', '3'],
    ['中医建议', '4'], ['食疗动功', '5'], ['时空行运', '6'], ['阴阳周期', '7'],
    ['灵魂图腾库', '8'], ['频率·稀有度', '9'], ['算法与校验', '10'],
    ['历史档案', '11']
  ];

  var SHICHEN_ALL = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时', '午时', '未时',
    '申时', '酉时', '戌时', '亥时', '前子时', '后子时'];
  var ROUTE_DESC = {
    'A': '路线 A：总数字和 ≥ 10，逐级数根落到主魂（最常见）',
    'B': '路线 B：总数字和 < 10，直接用年月日数根作基座',
    'MultiSoul': 'MultiSoul：总和 = 10 且有两个以上魄升魂，走多魂特例'
  };
  var TREND_CLS = { '偏阴': 'n', '偏阳': 'y', '平衡': '', '无': '' };

  var state = { f: null, res: null, md: {}, tab: 0, saveNext: false, suppressSave: false, histOk: true };

  function $(id) { return document.getElementById(id); }
  function esc(s) { return MD.esc(s == null ? '' : s); }
  function p2(n) { return String(n).padStart(2, '0'); }
  function todayISO() {
    var d = new Date();
    return d.getFullYear() + '-' + p2(d.getMonth() + 1) + '-' + p2(d.getDate());
  }
  function isoFromSlash(s) { return String(s).replace(/\//g, '-'); }
  function slashFromISO(s) { return String(s).replace(/-/g, '/'); }

  /* ══════════ 标签页 ══════════ */
  function buildTabs() {
    var nav = $('tabs');
    nav.innerHTML = TABS.map(function (t, i) {
      return '<button type="button" data-tab="' + i + '"' + (i === 0 ? ' class="on"' : '') +
        '><span class="no">' + t[1] + '</span>' + t[0] + '</button>';
    }).join('');
    nav.addEventListener('click', function (e) {
      var b = e.target.closest('button[data-tab]');
      if (!b) return;
      switchTab(+b.getAttribute('data-tab'));
    });
  }

  function switchTab(i) {
    state.tab = i;
    var btns = document.querySelectorAll('#tabs button');
    for (var k = 0; k < btns.length; k++) btns[k].classList.toggle('on', +btns[k].getAttribute('data-tab') === i);
    var secs = document.querySelectorAll('#views section.tab');
    for (var j = 0; j < secs.length; j++) secs[j].classList.toggle('on', secs[j].id === 'tab-' + i);
    if (i === 11) renderHist();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  /* ══════════ 表单 ══════════ */
  function fillCities() {
    var keys = Object.keys(D.CITY).sort();
    $('cityList').innerHTML = keys.map(function (k) { return '<option value="' + esc(k) + '">'; }).join('');
    var sel = $('fDayShichen');
    sel.innerHTML = SHICHEN_ALL.map(function (s) {
      return '<option value="' + s + '"' + (s === '巳时' ? ' selected' : '') + '>' + s + '</option>';
    }).join('');
  }

  function readForm() {
    return {
      name: ($('fName').value || '').trim(),
      birth: $('fBirth').value,
      shichen: $('fShichen').value,
      gender: $('fGender').value,
      clock: $('fClock').value,
      city: ($('fCity').value || '').trim(),
      rule: $('fRule').value
    };
  }

  /* ══════════ 历史档案 · 生辰参数数据表（localStorage） ══════════ */
  var HIST_KEY = 'cihai9_records_v1';
  var HIST_AUTO_KEY = 'cihai9_autosave_v1';
  var HIST_DEDUP_KEY = 'cihai9_dedup_mode_v2';   /* name（默认）| full；v1 旧键不继承 */
  var HIST_UNDO_KEY = 'cihai9_dedup_undo_v1';    /* 最近一次去重前的快照 */
  var HIST_MAX = 500;
  var HIST_FIELDS = ['name', 'birth', 'shichen', 'gender', 'clock', 'city', 'rule'];
  var HIST_IDS = {
    name: 'fName', birth: 'fBirth', shichen: 'fShichen', gender: 'fGender',
    clock: 'fClock', city: 'fCity', rule: 'fRule'
  };
  var RULE_TXT = { book: '原书', query: '查询工具', v5: '核心引擎 v5' };

  /* ══════════ 表头排序（2026-11-14） ══════════
     老师要求：点清单表头就能按「稀有度 / 灵魂积分 / 姓名首字母」排行。
     口径说明（写死在代码里，避免以后又靠字段名猜）：
       · 稀有度 = 第 9 页同一个 rarity() 打分（0–100，越高越稀），由该条的阳格×阴格现算，不落库；
       · 灵魂积分 = 灵魂积分库里那条记录的 ★ 个数（1–6，'★☆☆☆☆' 记 1 分），不是名称字符串；
         若该格在库里查不到（三态里的「未收录」），记为空值、排序时永远垫底，不冒充 0 分；
       · 姓名 / 出生地 = 中文按拼音排（Intl.Collator 'zh-Hans-CN'，Chrome 用的是 pinyin 排序规则），
         等价于「姓名首字母 A→Z」；取不到 Collator 时退回 localeCompare。
     方向：数值列第一次点降序（排行榜直觉：最高分在最上面），文字列第一次点升序；
           同一表头再点反向，第三次回默认「查询时间从新到旧」。排序状态存 localStorage。 */
  var HIST_SORT_KEY = 'cihai9_hist_sort_v1';
  var HIST_SORT_NUM = { ts: 1, rar: 1, soul: 1, hits: 1 };
  var HIST_SORT_TXT = {
    ts: '查询时间', name: '姓名（拼音）', birth: '阳历生日', shichen: '时辰', gender: '性别',
    clock: '出生钟点', city: '出生地', rule: '子时规则', yang: '阳格', yin: '阴格',
    yangQue: '阳缺', yinQue: '阴缺', type: '类型', soul: '灵魂积分', rar: '稀有度', hits: '次数'
  };
  var HIST_COLL = null;
  try { HIST_COLL = new Intl.Collator('zh-Hans-CN', { numeric: true, sensitivity: 'base' }); }
  catch (e) { HIST_COLL = null; }
  var histSort = { key: null, dir: -1 };   /* key=null 即默认：ts 倒序 */
  var RAR_CACHE = {};                       /* 阳格|阴格 → rarity 结果，同一组合不重算 */

  function histSortRead() {
    try {
      var o = JSON.parse(localStorage.getItem(HIST_SORT_KEY) || 'null');
      if (o && typeof o === 'object' && (o.key === null || HIST_SORT_TXT[o.key])) {
        histSort = { key: o.key || null, dir: o.dir === 1 ? 1 : -1 };
      }
    } catch (e) { }
  }
  function histSortSave() {
    try { localStorage.setItem(HIST_SORT_KEY, JSON.stringify(histSort)); } catch (e) { }
  }
  /* 行内稀有度：与第 9 页算的是同一个函数，保证「表里 87.3 分」和「详情页 87.3 分」一致 */
  function histRarity(s) {
    var yg = s && s.yang, ig = s && s.yin;
    if (!yg || !ig) return null;
    var k = yg + '|' + ig;
    if (Object.prototype.hasOwnProperty.call(RAR_CACHE, k)) return RAR_CACHE[k];
    var x = null;
    try { x = M.rarity(yg, ig, D.FREQ, D.JOINT); } catch (e) { x = null; }
    RAR_CACHE[k] = x;
    return x;
  }
  function histSoulStar(s) {
    var v = (s && s.soul) || '';
    var m = String(v).match(/★/g);
    return m ? m.length : null;            /* 未收录 → null（不冒充 0 分） */
  }
  function histVal(rec, key) {
    var f = rec.f || {}, s = rec.s || {};
    switch (key) {
      case 'ts': return String(rec.ts || '');
      case 'rar': var x = histRarity(s); return x ? x.score : null;
      case 'soul': return histSoulStar(s);
      case 'hits': return rec.hits || 1;
      case 'name': return f.name || '';
      case 'birth': return f.birth || '';
      case 'shichen': return f.shichen || '';
      case 'gender': return f.gender === 'female' ? '女' : '男';
      case 'clock': return f.clock || '';
      case 'city': return f.city || '';
      case 'rule': return RULE_TXT[f.rule] || f.rule || '';
      default: return s[key] || '';
    }
  }
  function histCmpText(a, b) {
    if (/^\d+$/.test(a) && /^\d+$/.test(b)) {          /* 纯数字按数值比，别让 '10' < '9' */
      var na = parseInt(a, 10), nb = parseInt(b, 10);
      if (na !== nb) return na - nb;
    }
    if (HIST_COLL) return HIST_COLL.compare(a, b);
    return a < b ? -1 : (a > b ? 1 : 0);
  }
  function histSortArr(a) {
    var key = histSort.key, dir = histSort.dir;
    var out = a.slice();
    if (!key) {   /* 默认：查询时间从新到旧（稳定排序，同秒保持原顺序） */
      return out.map(function (r, i) { return { r: r, i: i }; })
        .sort(function (x, y) {
          var c = String(y.r.ts || '').localeCompare(String(x.r.ts || ''));
          return c || (x.i - y.i);
        }).map(function (o) { return o.r; });
    }
    return out.map(function (r, i) { return { r: r, i: i, v: histVal(r, key) }; })
      .sort(function (x, y) {
        var na = (x.v === null || x.v === ''), nb = (y.v === null || y.v === '');
        if (na && nb) return x.i - y.i;
        if (na) return 1;                                /* 空值永远垫底，正反向都不翻上来 */
        if (nb) return -1;
        var c = (typeof x.v === 'number' && typeof y.v === 'number')
          ? (x.v - y.v) : histCmpText(String(x.v), String(y.v));
        return c ? c * dir : (x.i - y.i);
      }).map(function (o) { return o.r; });
  }
  function histPaintHead() {
    var tbl = $('histTable');
    if (!tbl || !tbl.tHead) return;
    var ths = tbl.tHead.querySelectorAll('th[data-sort]');
    [].forEach.call(ths, function (th) {
      var k = th.getAttribute('data-sort'), on = (histSort.key === k);
      th.classList.toggle('on', on);
      var ar = th.querySelector('.ar');
      if (!ar) { ar = document.createElement('span'); ar.className = 'ar'; th.appendChild(ar); }
      ar.textContent = on ? (histSort.dir < 0 ? '▼' : '▲') : '⇅';
      ar.setAttribute('aria-hidden', 'true');
    });
    var now = $('histSortNow');
    if (now) {
      now.textContent = histSort.key
        ? HIST_SORT_TXT[histSort.key] + (histSort.dir < 0 ? ' ↓（高→低）' : ' ↑（低→高）')
        : '查询时间 ↓（默认）';
    }
  }

  function histRead() {
    try {
      var raw = localStorage.getItem(HIST_KEY);
      if (!raw) return [];
      var a = JSON.parse(raw);
      if (!Array.isArray(a)) return [];
      var m = histMode();
      /* 旧数据里的 key 是旧口径（birth 格式 / 无字段前缀），一律按当前口径重算，
         否则同一人在导入后与自动保存后会被判成两条不同的记录。 */
      return a.filter(function (r) { return r && r.f && typeof r.f === 'object'; })
        .map(function (r) { r.key = histKey(r.f, m); return r; });
    } catch (e) { return []; }
  }
  function histWrite(a) {
    try { localStorage.setItem(HIST_KEY, JSON.stringify(a)); return true; }
    catch (e) { return false; }
  }
  function histAutoOn() {
    try { return localStorage.getItem(HIST_AUTO_KEY) !== '0'; }
    catch (e) { return true; }
  }
  /* 归一化：去空白（含全角）、生日统一 YYYY/MM/DD、字段带名前缀。
     师命 2026-11-14「重复名单 + 生辰信息就要去除」：**默认按【名单】去重**，同名只留最新一条
     —— 老师截图里 28 条正是同一批人反复试生日 / 时辰 / 性别留下的，7 项全等口径一条都合并不掉。
     另保留「名单 + 生辰信息」口径，供需要保留同一人不同命盘时切换。
     ⚠️ 口径键升到 v2：旧 v1 里存过 full 的浏览器刷新后一律回落到新默认 name，
     否则只改代码默认不生效（2026-11-14 实坑）。 */
  function normVal(v) {
    return String(v == null ? '' : v).replace(/[\s\u3000]/g, '');
  }
  function normBirth(v) {
    var s = normVal(v).replace(/[.\-\/]/g, '/');
    var m = /^(\d{4})\/(\d{1,2})\/(\d{1,2})$/.exec(s);
    return m ? (m[1] + '/' + ('0' + m[2]).slice(-2) + '/' + ('0' + m[3]).slice(-2)) : s;
  }
  function histMode() {
    try { return localStorage.getItem(HIST_DEDUP_KEY) === 'full' ? 'full' : 'name'; }
    catch (e) { return 'name'; }
  }
  function histSetMode(m) {
    try { localStorage.setItem(HIST_DEDUP_KEY, m === 'full' ? 'full' : 'name'); } catch (e) { }
  }
  function histKey(f, mode) {
    f = f || {};
    if (mode === 'name') return 'N:' + normVal(f.name);
    return 'F:' + HIST_FIELDS.map(function (k) {
      return k + '=' + (k === 'birth' ? normBirth(f[k]) : normVal(f[k]));
    }).join('\u0001');
  }
  /* 全表去重：按 ts 倒序保留最新一条，同组合并 hits。返回 {records, merged} */
  function histDedup(a, mode) {
    var seen = {}, out = [], merged = 0;
    a.sort(function (x, y) { return String(y.ts || '').localeCompare(String(x.ts || '')); });
    a.forEach(function (rec) {
      var k = histKey(rec.f || {}, mode);
      rec.key = k;
      if (seen[k]) { seen[k].hits = (seen[k].hits || 1) + (rec.hits || 1); merged++; return; }
      seen[k] = rec;
      out.push(rec);
    });
    return { records: out, merged: merged };
  }
  /* 自动去重：写盘前留一份可撤销快照，绝不静默丢数据 */
  function histAutoDedup(silent) {
    var a = histRead();
    if (a.length < 2) return 0;
    /* 快照必须在去重前深拷贝：histDedup 会原地排序并累加 hits */
    var snap = JSON.parse(JSON.stringify(a));
    var res = histDedup(a, histMode());
    if (!res.merged) return 0;
    try {
      localStorage.setItem(HIST_UNDO_KEY, JSON.stringify({
        at: new Date().toISOString(), mode: histMode(), records: snap
      }));
    } catch (e) { }
    state.histOk = histWrite(res.records);
    state.histMerged = res.merged;   /* 只报最近一次，避免切口径后显示累计值误导 */
    if (!silent && state.tab === 11) renderHist();
    return res.merged;
  }
  function histUndo() {
    var snap = null;
    try { snap = JSON.parse(localStorage.getItem(HIST_UNDO_KEY) || 'null'); } catch (e) { }
    if (!snap || !Array.isArray(snap.records)) { window.alert('没有可撤销的去重记录。'); return; }
    if (!window.confirm('恢复上次去重前的 ' + snap.records.length + ' 条记录？当前表会被替换。')) return;
    state.histOk = histWrite(snap.records);
    try { localStorage.removeItem(HIST_UNDO_KEY); } catch (e) { }
    histSetMode('full');           /* 撤销后临时切最保守口径，避免刷新又合并；要按名单再切回来 */
    state.histMerged = 0;
    renderHist();
  }
  function histSummary(r) {
    var soul = '';
    try {
      var sc = M.lookupSoulScore(r.yang, D.SOUL_SCORE_DB);
      if (sc && sc.rec) soul = (sc.rec.name || '') + (sc.rec.stars ? '（' + sc.rec.stars + '）' : '');
    } catch (e) { }
    return {
      yang: r.yang || '', yin: r.yin || '',
      yangQue: r.yangQue || '', yinQue: r.yinQue || '',
      type: r.type || '', half: r.half || '',
      soul: soul,
      trueSolar: state.ts ? (state.ts.iso + ' / ' + state.ts.shichen) : ''
    };
  }
  /* 用户完成一次解读后自动落盘；全表查同组合并（不再只比 a[0]），并顺带做一次全表去重 */
  function autoSave(f, r) {
    if (!histAutoOn() || state.suppressSave) return;
    var mode = histMode(), a = histRead();
    var key = histKey(f, mode), now = new Date().toISOString(), sum = histSummary(r);
    var idx = -1;
    for (var i = 0; i < a.length; i++) {
      if ((a[i].key || histKey(a[i].f || {}, mode)) === key) { idx = i; break; }
    }
    if (idx >= 0) {
      var rec = a.splice(idx, 1)[0];
      rec.ts = now; rec.hits = (rec.hits || 1) + 1; rec.s = sum; rec.key = key;
      a.unshift(rec);
    } else {
      a.unshift({
        id: 'r' + Date.now() + Math.random().toString(36).slice(2, 6),
        key: key, ts: now, hits: 1, f: f, s: sum, v: 1
      });
    }
    var res = histDedup(a, mode);
    if (res.records.length > HIST_MAX) { res.records.length = HIST_MAX; state.histTrimmed = true; }
    state.histOk = histWrite(res.records);
    if (state.tab === 11) renderHist();
  }

  function renderHist() {
    var a = histRead(), box = $('histBody'), mode = histMode();
    $('histCount').textContent = '共 ' + a.length + ' 条记录' +
      (a.length >= HIST_MAX ? '（已达上限 ' + HIST_MAX + '，最旧的会被淘汰）' : '');
    $('histAuto').checked = histAutoOn();
    $('histMode').value = mode;
    var undoSnap = null;
    try { undoSnap = JSON.parse(localStorage.getItem(HIST_UNDO_KEY) || 'null'); } catch (e) { }
    $('histUndo').disabled = !(undoSnap && Array.isArray(undoSnap.records));
    /* 两种口径各能剩多少，直接摆出来，老师不用猜 */
    var nFull = a.length ? histDedup(JSON.parse(JSON.stringify(a)), 'full').records.length : 0;
    var nName = a.length ? histDedup(JSON.parse(JSON.stringify(a)), 'name').records.length : 0;
    $('histStat').innerHTML = '当前口径 <b>' +
      (mode === 'name' ? '仅名单（同名留最新）' : '名单 + 生辰信息') +
      '</b>；口径预览：仅名单剩 <b>' + nName + '</b> 人，名单 + 生辰信息剩 <b>' + nFull + '</b> 条。' +
      ' 切换口径立即自动重跑，重复记录可撤销恢复。' +
      '<br><span style="color:#a8452a">为什么还有这么多条：</span>「名单 + 生辰信息」口径要求姓名与 7 项' +
      '生辰参数<b>全部相同</b>才算重复；同一人反复试生日 / 时辰 / 性别时每项都不同，' +
      '一条都不会合并 —— 要按人收敛请切「仅名单」（本页默认）。';
    var msg = '';
    if (state.histOk === false)
      msg = '<b style="color:#a8452a">本机存储写入失败</b>（隐私模式或空间满），请及时导出 JSON 备份。';
    else if (state.histTrimmed)
      msg = '记录已达 ' + HIST_MAX + ' 条上限，最旧的已自动淘汰，建议导出 JSON 留存。';
    if (state.histMerged)
      msg += (msg ? '<br>' : '') + '已自动合并 <b>' + state.histMerged + '</b> 条重复记录，' +
        '可点「撤销去重」恢复（恢复后临时切到「名单 + 生辰信息」，避免刷新又合并；' +
        '要按名单去重请切回「仅名单」）。';
    $('histHint').innerHTML = msg;
    /* 空态不设表格最小宽度，窄屏下提示文字才不会被推到滚动区外 */
    $('histTable').classList.toggle('is-empty', !a.length);
    histPaintHead();
    if (!a.length) {
      box.innerHTML = '<tr><td colspan="17"><div class="empty">暂无记录。填好生辰参数点「开始解读」，本表会自动保存。</div></td></tr>';
      return;
    }
    var rows = histSortArr(a);
    box.innerHTML = rows.map(function (rec, ri) {
      var f = rec.f || {}, s = rec.s || {};
      var ts = String(rec.ts || '').replace('T', ' ').slice(0, 19);
      /* 稀有度现算（口径与第 9 页同一个 rarity()）：查不到就直说，不填 0 分骗人 */
      var xr = histRarity(s);
      var rarCell = (s.yang && s.yin)
        ? (xr ? '<b>' + xr.score.toFixed(1) + '</b><span class="b">' + esc(xr.band.t) + '</span>'
              : '<span style="color:var(--ink3)">区间外</span>')
        : '—';
      var cls = (histSort.key === 'rar' && ri === 0 && xr) ? ' class="rank-top"' : '';
      /* 操作列放最左：17 列宽表在 1300 甚至 758 下横向滚动时，载入/删除始终可见 */
      return '<tr' + cls + '>' +
        '<td class="nowrap">' +
          '<button class="btn ghost sm" type="button" data-hist-load="' + esc(rec.id || '') + '">载入</button> ' +
          '<button class="btn ghost sm" type="button" data-hist-del="' + esc(rec.id || '') + '">删除</button>' +
        '</td>' +
        '<td class="nowrap">' + esc(ts) + '</td>' +
        '<td>' + esc(f.name || '—') + '</td>' +
        '<td>' + esc(f.birth || '') + '</td>' +
        '<td>' + esc(f.shichen || '') + '</td>' +
        '<td>' + esc(f.gender === 'female' ? '女' : '男') + '</td>' +
        '<td>' + esc(f.clock || '—') + '</td>' +
        '<td>' + esc(f.city || '—') + '</td>' +
        '<td>' + esc(RULE_TXT[f.rule] || f.rule || '') + '</td>' +
        '<td><code>' + esc(s.yang) + '</code></td>' +
        '<td><code>' + esc(s.yin) + '</code></td>' +
        '<td>' + esc(s.yangQue || '无') + '</td>' +
        '<td>' + esc(s.yinQue || '无') + '</td>' +
        '<td>' + esc(s.type || '—') + '</td>' +
        '<td>' + esc(s.soul || '—') + '</td>' +
        '<td class="hist-rar">' + rarCell + '</td>' +
        '<td>' + (rec.hits || 1) + '</td></tr>';
    }).join('');
  }

  /* 载入 = 把生辰参数调回表单并重新算出 11 页结果；不新增记录 */
  function histLoad(id) {
    var rec = histRead().filter(function (r) { return r.id === id; })[0];
    if (!rec) return;
    HIST_FIELDS.forEach(function (k) {
      var el = $(HIST_IDS[k]);
      if (!el) return;
      var v = rec.f[k] == null ? '' : rec.f[k];
      /* run() 把生日改成 1990/05/08，而 date input 只收 YYYY-MM-DD ⇒ 载入时转回 ISO */
      el.value = (k === 'birth') ? isoFromSlash(v) : v;
    });
    state.suppressSave = true;
    try { run(); } finally { state.suppressSave = false; }
    switchTab(0);
  }
  function histDel(id) {
    var a = histRead().filter(function (r) { return r.id !== id; });
    state.histOk = histWrite(a);
    renderHist();
  }
  function histClear() {
    if (!window.confirm('确定清空全部查询记录？此操作不可撤销，建议先导出 JSON 备份。')) return;
    state.histOk = histWrite([]);
    state.histTrimmed = false;
    renderHist();
  }
  function histDownload(text, mime, filename) {
    var blob = new Blob([text], { type: mime });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
  }
  function csvQ(v) { return '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"'; }
  function histCsv() {
    var a = histRead();
    var head = ['查询时间', '姓名', '阳历生日', '时辰', '性别', '出生钟点', '出生地', '子时规则',
      '阳格', '阴格', '阳缺', '阴缺', '类型', '半补', '灵魂', '灵魂★', '稀有度', '真太阳时', '次数'];
    var rows = [head.map(csvQ).join(',')];
    a.forEach(function (rec) {
      var f = rec.f || {}, s = rec.s || {}, xr = histRarity(s), st = histSoulStar(s);
      rows.push([
        rec.ts, f.name, f.birth, f.shichen, (f.gender === 'female' ? '女' : '男'),
        f.clock, f.city, (RULE_TXT[f.rule] || f.rule), s.yang, s.yin,
        s.yangQue, s.yinQue, s.type, s.half, s.soul,
        (st == null ? '' : st), (xr ? xr.score.toFixed(1) : ''),
        s.trueSolar, rec.hits || 1
      ].map(csvQ).join(','));
    });
    histDownload('\ufeff' + rows.join('\r\n') + '\r\n', 'text/csv;charset=utf-8',
      '慈海九宫格_查询记录_' + todayISO().replace(/-/g, '') + '.csv');
  }
  function histJson() {
    histDownload(JSON.stringify({ v: 1, app: '慈海九宫格 · 即时解读', exportedAt: new Date().toISOString(), records: histRead() }, null, 2),
      'application/json;charset=utf-8',
      '慈海九宫格_查询记录_' + todayISO().replace(/-/g, '') + '.json');
  }
  function histImport(file) {
    var fr = new FileReader();
    fr.onload = function () {
      try {
        var obj = JSON.parse(String(fr.result));
        var inc = Array.isArray(obj) ? obj : (obj && Array.isArray(obj.records) ? obj.records : null);
        if (!inc) throw new Error('文件里没有 records 数组');
        var mode = histMode(), a = histRead(), seen = {}, added = 0, dup = 0;
        a.forEach(function (r) { seen[histKey(r.f || {}, mode)] = 1; });
        inc.forEach(function (r) {
          if (!r || !r.f || typeof r.f !== 'object' || !r.f.birth) return;
          var k = histKey(r.f, mode);       /* 忽略文件里的旧 key，按当前口径重算 */
          if (seen[k]) { dup++; return; }
          seen[k] = 1;
          a.push({
            id: r.id || ('r' + Date.now() + Math.random().toString(36).slice(2, 6)),
            key: k, ts: r.ts || new Date().toISOString(), hits: r.hits || 1,
            f: r.f, s: r.s || {}, v: 1
          });
          added++;
        });
        var snap = JSON.parse(JSON.stringify(a));
        var res = histDedup(a, mode);
        if (res.merged) {
          try {
            localStorage.setItem(HIST_UNDO_KEY, JSON.stringify({
              at: new Date().toISOString(), mode: mode, records: snap
            }));
          } catch (e) { }
          state.histMerged = res.merged;
        }
        if (res.records.length > HIST_MAX) { res.records.length = HIST_MAX; state.histTrimmed = true; }
        state.histOk = histWrite(res.records);
        renderHist();
        window.alert('导入完成：新增 ' + added + ' 条，跳过重复 ' + (dup + res.merged) +
          ' 条，当前共 ' + res.records.length + ' 条。');
      } catch (e) {
        window.alert('导入失败：' + e.message);
      }
    };
    fr.readAsText(file, 'utf-8');
  }
  function bindHist() {
    $('histAuto').addEventListener('change', function () {
      try { localStorage.setItem(HIST_AUTO_KEY, this.checked ? '1' : '0'); } catch (e) { }
    });
    $('histCsv').addEventListener('click', histCsv);
    $('histJson').addEventListener('click', histJson);
    $('histImport').addEventListener('click', function () { $('histFile').click(); });
    $('histFile').addEventListener('change', function () {
      if (this.files && this.files[0]) histImport(this.files[0]);
      this.value = '';
    });
    $('histClear').addEventListener('click', histClear);
    $('histMode').addEventListener('change', function () {
      histSetMode(this.value);
      var n = histAutoDedup(true);
      renderHist();
      if (n) window.alert('已按新口径合并 ' + n + ' 条重复记录，可点「撤销去重」恢复。');
    });
    $('histDedup').addEventListener('click', function () {
      var n = histAutoDedup(true);
      renderHist();
      window.alert(n ? ('已合并 ' + n + ' 条重复记录，可点「撤销去重」恢复。') : '当前没有重复记录。');
    });
    $('histUndo').addEventListener('click', histUndo);
    /* 表头排序：数值列先降序（稀有度最高、灵魂★最多、次数最多在最上面），文字列先升序；
       同一列再点反向，第三次回默认。排序只改显示顺序，不动 localStorage 里的记录顺序。 */
    $('histTable').addEventListener('click', function (e) {
      var th = e.target.closest('th[data-sort]');
      if (th) {
        var k = th.getAttribute('data-sort'), start = HIST_SORT_NUM[k] ? -1 : 1;
        if (histSort.key !== k) histSort = { key: k, dir: start };
        else if (histSort.dir === start) histSort = { key: k, dir: -start };
        else histSort = { key: null, dir: -1 };
        histSortSave();
        renderHist();
        return;
      }
      var l = e.target.closest('[data-hist-load]');
      if (l) { histLoad(l.getAttribute('data-hist-load')); return; }
      var d = e.target.closest('[data-hist-del]');
      if (d) {
        if (window.confirm('删除这条查询记录？')) histDel(d.getAttribute('data-hist-del'));
      }
    });
    var rl = $('histSortReset');
    if (rl) rl.addEventListener('click', function (e) {
      e.preventDefault();
      histSort = { key: null, dir: -1 };
      histSortSave();
      renderHist();
    });
  }

  /* ══════════ 主流程 ══════════ */
  function run() {
    var f = readForm();
    var bd = M.parseDate(f.birth);
    if (!bd) {
      $('paramTail').innerHTML = '<span style="color:#a8452a">生日无效，请检查</span>';
      return;
    }
    f.birth = bd.y + '/' + p2(bd.m) + '/' + p2(bd.d);
    state.f = f;

    /* 真太阳时 */
    state.ts = null;
    if (f.clock && f.city) {
      var c = M.lookupCity(f.city, D.CITY);
      if (c) {
        var hm = f.clock.split(':');
        state.ts = M.trueSolar(bd.y, bd.m, bd.d, +hm[0], +hm[1], c[0], c[1], 8);
        state.ts.city = f.city;
        state.ts.lat = c[0]; state.ts.lon = c[1];
      }
    }

    var r = M.calc(f.birth, f.shichen, f.gender, f.rule);
    state.res = r;
    state.lunar = r.a.lunar;

    /* 三份报告 Markdown（只算一次，后续复制/下载直接取） */
    var opt = Object.assign({}, D, {
      name: f.name || '（未填姓名）', birth: f.birth, shichen: f.shichen,
      gender: f.gender, location: f.city || null, now: new Date(), targetDate: null,
      rule: f.rule
    });
    state.md.rp = M.REPORTS.comprehensive(opt);
    state.md.tm = M.REPORTS.ni(opt);
    state.md.sl = M.REPORTS.shiliao(opt);

    renderQ(); renderRd(); renderFp(); renderReports(); renderEx(); renderCy(); renderRarity(); renderAl();

    $('paramTail').innerHTML = '<span class="tag ok">已计算</span> ' +
      esc(f.birth) + ' ' + esc(f.shichen) + ' · ' + (f.gender === 'male' ? '男' : '女') +
      (state.ts ? ' · 真太阳时 ' + esc(state.ts.iso) + '（' + esc(state.ts.shichen) + '）' : '');
    if (state.saveNext) autoSave(Object.assign({}, f), r);
  }

  /* 用户主动查询才留痕；init() 的自动试算、载入历史重算都不写表 */
  function userRun() {
    state.saveNext = true;
    try { run(); } finally { state.saveNext = false; }
  }

  /* ══════════ 0 命盘概要 ══════════ */
  function beadRow(str, forceMiss) {
    var out = [];
    var s = String(str || '');
    for (var i = 0; i < s.length; i++) {
      var d = s[i];
      if (!/\d/.test(d)) continue;
      var yy = M.digitYinYang(d);
      var cls = forceMiss ? 'miss' : (yy.attr.charAt(0) === '阴' ? 'n' : (yy.attr.charAt(0) === '阳' ? 'y' : ''));
      out.push('<div class="bead ' + cls + '" title="' + esc(yy.attr) + '">' + d +
        '<small>' + esc(yy.organ) + '</small></div>');
    }
    return out.join('');
  }

  function organChain(str) {
    var out = [];
    var s = String(str || '');
    for (var i = 0; i < s.length; i++) {
      if (!/\d/.test(s[i])) continue;
      out.push(D.DIGIT_ORGAN[s[i]] || '?');
    }
    return out.join('·');
  }

  /* ── 九宫盘面（2026-11-20 加，同日改元宝风格）────────────────────────
     制法照元宝版：3×3 主宫 + 下方正中一格 0（整体像「甲」字）；底色按数字
     固定五行色（1/2 金白 · 3 火红 · 4/5 木绿 · 6/0 水紫 · 7/8/9 土黄），
     不看在不在格；数字统一蓝紫；角标四角分工。
     符号定义取自《卢先生社群答疑》第 274 条原文：
        「星星代表缺漏；方块代表主魂；圆圈代表魄；三角代表辅魂。」
        · 角标：■ 方块＝主魂（soulDetail.mainSoul，仅阳格）｜▲ 三角＝辅魂（auxSoul）｜
                 ○ 圆圈＝魄（阳格 r.a.po / 阴格 r.a.lunarPo）｜★ 星星＝缺漏（格与魄皆无）。
        · 重复几个符号＝该数字出现几次（辅魂 2911 的 1 出现 2 次 ⇒ 格1 画 ▲▲）。
        · 格中出现多次的，直接写在器官名后面 ×n，不占角标位。 */
  function plateCard(kind, label, grid, que, po, sd, who, whenTxt) {
    var cls = kind === 'yin' ? 'yin' : 'yang';
    var g = String(grid || ''), q = String(que || ''), pp = String(po || '');
    function cnt(str, d) {
      var n = 0;
      for (var i = 0; i < str.length; i++) if (str.charAt(i) === d) n++;
      return n;
    }
    var mainSoul = (who === 'yang' && sd) ? String(sd.mainSoul || '') : '';
    var auxSoul = (who === 'yang' && sd) ? String(sd.auxSoul || '') : '';
    /* 原版口径（《卢先生社群答疑》第 274 条）：星星=缺漏、方块=主魂、圆圈=魄、三角=辅魂。
       元宝图里符号是「重复几次画几个」（辅魂 2911 的 1 出现 2 次 ⇒ 格1 画 ▲▲），
       不是「符号+数字」，所以这里用 rep() 铺符号。 */
    function rep(ch, n) { var s = ''; for (var j = 0; j < n; j++) s += ch; return s; }
    var cells = '', d, k, hasG, isQ, nPo, nIn, mkA, mkM, mkP, mkS, na;
    /* 元宝原版是「竖向 123」：1/2/3 竖着排第一列，4/5/6 第二列，7/8/9 第三列。
       CSS Grid 按行填充，所以这里按列优先顺序吐格子 [1,4,7, 2,5,8, 3,6,9]。 */
    var order = [1, 4, 7, 2, 5, 8, 3, 6, 9], oi;
    for (oi = 0; oi < order.length; oi++) {
      d = order[oi]; k = String(d);
      hasG = g.indexOf(k) >= 0;
      isQ = q.indexOf(k) >= 0;
      nPo = cnt(pp, k);
      nIn = cnt(g, k);
      mkA = mkM = mkP = mkS = '';
      if (mainSoul && mainSoul.indexOf(k) >= 0) mkM = '■';
      if (auxSoul) { na = cnt(auxSoul, k); if (na) mkA = rep('▲', na); }
      if (nPo) mkP = rep('○', nPo);
      if (isQ) mkS = '★';
      cells += '<div class="pcell d' + k + '">' +
        '<div class="n">' + k + '</div>' +
        '<div class="o">' + esc(D.DIGIT_ORGAN[k] || '?') +
          (nIn > 1 ? ' <i>&times;' + nIn + '</i>' : '') + '</div>' +
        (mkA ? '<div class="mk mk-aux">' + mkA + '</div>' : '') +
        (mkM ? '<div class="mk mk-main">' + mkM + '</div>' : '') +
        (mkP ? '<div class="mk mk-po">' + mkP + '</div>' : '') +
        (mkS ? '<div class="mk mk-miss">' + mkS + '</div>' : '') +
        '</div>';
    }
    /* 0 入甲字格：九宫是 1–9，0 作第 10 格落在下方正中，不占九宫位 */
    var zIn = cnt(g, '0'), zPo = cnt(pp, '0'), zQ = q.indexOf('0') >= 0;
    var zA = auxSoul ? cnt(auxSoul, '0') : 0;
    var zM = (mainSoul && mainSoul.indexOf('0') >= 0) ? '■' : '';
    cells += '<div class="pcell d0">' +
      '<div class="n">0</div>' +
      '<div class="o">' + esc(D.DIGIT_ORGAN['0'] || '小肠') + '</div>' +
      (zA ? '<div class="mk mk-aux">' + rep('▲', zA) + '</div>' : '') +
      (zM ? '<div class="mk mk-main">' + zM + '</div>' : '') +
      (zPo ? '<div class="mk mk-po">' + rep('○', zPo) + '</div>' : '') +
      (zQ ? '<div class="mk mk-miss">★</div>' : '') +
      '</div>';
    var ztxt = zIn ? ('格中 ' + zIn + ' 次') : '不在格中';
    if (zPo) ztxt += ' · 魄中 ' + zPo + ' 次';
    if (!zIn && !zPo && zQ) ztxt += ' · 缺漏';
    return '<div class="plate ' + cls + '">' +
      '<div class="plate-hd"><span class="t">' + esc(label) + '</span>' +
        '<span class="g">' + esc(g || '—') + '</span>' +
        (whenTxt ? '<span class="when">' + esc(whenTxt) + '</span>' : '') + '</div>' +
      '<div class="pgrid">' + cells + '</div>' +
      '<div class="pfoot">0（' + esc(D.DIGIT_ORGAN['0'] || '小肠') + '）' + esc(ztxt) +
        '<br>■ 方块＝主魂　▲ 三角＝辅魂　○ 圆圈＝魄　★ 星星＝缺漏' +
        '（重复几个＝该数字出现几次）' +
        (who === 'yang' ? '' : '<br>阴格无主魂/辅魂口径，只标 ○ 与 ★') +
        '</div></div>';
  }

  function gridCard(kind, label, grid, que) {
    var cls = kind === 'yin' ? 'yin' : 'yang';
    return '' +
      '<div class="big ' + cls + '">' +
      '<div class="k">' + label + '</div>' +
      '<div class="v">' + esc(grid || '—') + '</div>' +
      '<div class="m">' + esc(organChain(grid) || '无') + '</div>' +
      '<div class="m" style="margin-top:6px">缺数 <b>' + esc(que || '无') + '</b>' +
      (que ? '（' + esc(que.split('').map(function (d) { return D.DIGIT_ORGAN[d] || '?'; }).join('、')) + '）' : '') +
      '</div></div>';
  }

  function renderQ() {
    var r = state.res, f = state.f;
    var isZ = r.isZishi;

    var lunarTxt = state.lunar
      ? '农历 ' + state.lunar.y + ' 年 ' + (state.lunar.leap ? '闰' : '') + state.lunar.m + ' 月 ' + state.lunar.d + ' 日'
      : '农历（超出 1900–2101 表范围）';
    $('q-caption').innerHTML = esc(f.birth) + ' · ' + esc(f.shichen) + ' · ' +
      (f.gender === 'male' ? '男' : '女') + ' · ' + esc(r.type) + ' · ' + esc(lunarTxt) +
      ' · 半补 <b>' + esc(r.half || '无') + '</b>' +
      (r.half ? '（' + esc(r.half.split('').map(function (d) { return D.DIGIT_ORGAN[d] || ''; }).join('、')) + '）' : '');

    var html = gridCard('yang', '阳格', r.yang, r.yangQue) + gridCard('yin', '阴格', r.yin, r.yinQue);
    $('q-duo').innerHTML = html;

    $('q-legend').innerHTML =
      '<span><i style="background:#fbeae4;border-color:#e0b7a6"></i>阳（腑）</span>' +
      '<span><i style="background:#e6f0f5;border-color:#b6cfdd"></i>阴（脏）</span>' +
      '<span><i style="background:#faf8f3;border-color:#c9c2b4;border-style:dashed"></i>缺数</span>';

    $('q-beads-yang').innerHTML = '<div style="font-size:12px;color:var(--ink3);margin-bottom:6px">阳格 ' + esc(r.yang) + '</div>' + beadRow(r.yang);
    $('q-beads-yin').innerHTML = '<div style="font-size:12px;color:var(--ink3);margin:10px 0 6px">阴格 ' + esc(r.yin) + '</div>' + beadRow(r.yin);

    $('q-missing').innerHTML =
      '<div style="font-size:12px;color:var(--ink3);margin:12px 0 6px">阳缺 ' + esc(r.yangQue || '无') + '</div>' +
      (r.yangQue ? beadRow(r.yangQue, true) : '<span class="tag">无缺</span>') +
      '<div style="font-size:12px;color:var(--ink3);margin:10px 0 6px">阴缺 ' + esc(r.yinQue || '无') + '</div>' +
      (r.yinQue ? beadRow(r.yinQue, true) : '<span class="tag">无缺</span>');

    var a = r.a, sd = a.soulDetail || {};
    /* 盘面：阳格魄用 r.a.po（yangCalc），阴格魄用 r.a.lunarPo（yinCalc，按农历日算）。
       子时（含"子时"泛指）出两副：当天格 + 调整格（按换日规则算的另一套）。 */
    if ($('q-plates')) {
      var b = r.b, bsd = b ? (b.soulDetail || {}) : {};
      var pHtml =
        plateCard('yang', '阳格九宫 · 当天', r.yang, r.yangQue, a.po, sd, 'yang', r.date) +
        plateCard('yin', '阴格九宫 · 当天', r.yin, r.yinQue, a.lunarPo, sd, 'yin', r.date);
      if (isZ) {
        pHtml += '<div class="plate-group">' +
          (r.isQian ? '前子时' : '后子时') + ' · 调整格 ' + esc(r.adjDate) +
          '（' + esc(ruleName(r.rule)) + '）</div>' +
          plateCard('yang', '阳格九宫 · 调整', r.yang1, r.yangQue1, b.po, bsd, 'yang', r.adjDate) +
          plateCard('yin', '阴格九宫 · 调整', r.yin1, r.yinQue1, b.lunarPo, bsd, 'yin', r.adjDate);
      }
      $('q-plates').innerHTML = pHtml;
    }
    $('q-struct').innerHTML =
      '<dl class="kv">' +
      '<dt>类型</dt><dd>' + esc(r.type) + '</dd>' +
      '<dt>半补</dt><dd>' + esc(r.half || '无（未填时辰或时辰无效）') + '</dd>' +
      '<dt>路线</dt><dd><span class="tag a">' + esc(a.route) + '</span> ' + esc(ROUTE_DESC[a.route] || '') + '</dd>' +
      '<dt>魄（' + (a.po ? a.po.length : 0) + ' 位）</dt><dd><code>' + esc((a.po || []).join('')) + '</code></dd>' +
      '<dt>升魂（UP）</dt><dd>' + (a.up && a.up.length ? '<code>' + esc(a.up.join('')) + '</code>' : '无') + '</dd>' +
      '<dt>主魂</dt><dd>' + esc(sd.mainSoul || '—') + '</dd>' +
      '<dt>辅魂</dt><dd>' + esc(sd.auxSoul || '无') + ' <span style="color:var(--ink3)">' + esc(sd.auxNote || '') + '</span></dd>' +
      '<dt>升级说明</dt><dd>' + esc(sd.upNote || '') + '</dd>' +
      '</dl>' +
      '<p class="sub" style="margin:10px 0 0">注：这里的「辅魂」按源码取 <code>阳格[:-1]</code>' +
      (sd.auxSoul ? '（' + esc(sd.auxSoul) + '）' : '') +
      '，而「升级说明」里的「升级为辅魂 N」指的是 <b>升魂</b>那批数字 —— 同名不同义，本站照源码原样呈现。</p>';

    /* 灵魂积分（精确 / 剥零推定 / 未收录 三态，不再按前缀猜身份） */
    var sc = M.lookupSoulScore(r.yang, D.SOUL_SCORE_DB);
    var sv = M.lookupSoulV5(r.yang, D.SOUL_DB);
    var soulHtml = '';
    if (sc && sc.rec) {
      var rec = sc.rec;
      soulHtml += '<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:baseline;margin-bottom:8px">' +
        '<span style="font-family:var(--mono);font-size:20px;color:var(--accent);font-weight:600">' + esc(sc.key) + '</span>' +
        '<span class="tag a">' + esc(rec.stars) + '</span>' +
        '<span style="font-size:16px;font-weight:600">' + esc(rec.name) + '</span>' +
        '</div>' +
        '<dl class="kv">' +
        '<dt>层级</dt><dd>' + esc(rec.level) + '</dd>' +
        '<dt>说明</dt><dd>' + esc(rec.desc || '—') + '</dd>' +
        (rec.path ? '<dt>跌落路径</dt><dd><code>' + esc(rec.path) + '</code></dd>' : '') +
        '</dl>';
      if (sc.conf === 'same-root') {
        soulHtml += '<p class="hint" style="margin-top:8px">注：阳格 <code>' + esc(r.yang) + '</code> 未被原库直接收录，' +
          '按「剥前导零」对应到 <code>' + esc(sc.key) + '</code>（先天形态 / 后天落形态同源）。' +
          '此条为<b>推定</b>，不是原书对 <code>' + esc(r.yang) + '</code> 的直接结论。</p>';
      }
    } else {
      soulHtml += '<div class="empty">灵魂积分库中无 <code>' + esc(r.yang) + '</code> 的收录条目' +
        '（82 条只覆盖 605 种阳格中的 71 种）。</div>';
      if (sc && sc.near) {
        soulHtml += '<p class="hint" style="margin-top:8px">键名相近的条目有 <code>' + esc(sc.near.key) + '</code>，' +
          '但那只是字符串前缀相同，<b>不是这个阳格的身份</b>，故此处不显示星级与名称。</p>';
      }
    }
    $('q-soul').innerHTML = soulHtml;

    /* 阴阳倾向 */
    function yyBlock(title, g, yy) {
      var cls = TREND_CLS[yy.trend] || '';
      return '<div class="big ' + cls + '" style="margin-bottom:10px">' +
        '<div class="k">' + title + ' · ' + esc(g) + '</div>' +
        '<div style="font-size:17px;font-weight:600;margin:4px 0">' + esc(yy.trend) +
        ' <span style="font-size:12.5px;font-weight:400;color:var(--ink3)">阴 ' + yy.yin + ' · 阳 ' + yy.yang + '</span></div>' +
        '<div class="m">阴数字：' + (yy.yinD.length ? esc(yy.yinD.join(' ')) : '无') + '</div>' +
        '<div class="m">阳数字：' + (yy.yangD.length ? esc(yy.yangD.join(' ')) : '无') + '</div>' +
        '</div>';
    }
    $('q-yy').innerHTML = yyBlock('阳格', r.yang, r.yyYang) + yyBlock('阴格', r.yin, r.yyYin);

    /* 子时双格 */
    var zc = $('q-zishi-card');
    if (isZ) {
      zc.style.display = '';
      $('q-zishi-note').innerHTML = esc(r.note) + ' · 调整日期 <b>' + esc(r.adjDate) + '</b>' +
        ' · 规则：' + ruleName(r.rule);
      $('q-zishi').innerHTML =
        '<div class="tw"><table><thead><tr><th>类型</th><th>阳格</th><th>阴格</th><th>阳缺</th><th>阴缺</th><th>半补</th></tr></thead><tbody>' +
        '<tr><td><b>当天格</b></td><td class="num">' + esc(r.yang) + '</td><td class="num">' + esc(r.yin) +
        '</td><td class="num">' + esc(r.yangQue) + '</td><td class="num">' + esc(r.yinQue) + '</td><td class="num">' + esc(r.half || '') + '</td></tr>' +
        '<tr><td><b>调整格</b></td><td class="num">' + esc(r.yang1) + '</td><td class="num">' + esc(r.yin1) +
        '</td><td class="num">' + esc(r.yangQue1) + '</td><td class="num">' + esc(r.yinQue1) + '</td><td class="num">' + esc(r.half1 || '') + '</td></tr>' +
        '</tbody></table></div>';
    } else {
      zc.style.display = 'none';
    }

    renderAcu(r);
  }

  /* ── 养生穴位（2026-11-20 加，照元宝版口径）───────────────────────────
     元宝版右栏两块：「先天灵穴·天赋气枢（扬长）」按主魂/辅魂取穴、
     「后天灵穴·补漏培元（补虚）」按缺数取穴，取穴一律为各经「原穴」。
     三张实拍图逐条反推验证：主魂 2→合谷、4→太冲、6→太溪；辅魂 842→太白/太冲/合谷；
     缺 3/5/7→神门/丘墟/冲阳；缺 6/7/8→太溪/冲阳/太白 —— 全部落在下表。
     慈海 10 个数字正好覆盖十经（缺心包/三焦），穴位一律取原穴，不自创配穴。 */
  var ACUPOINT = {
    '1': { mer: '手太阴肺经', zf: '脏', wx: '阴金', pt: '太渊', py: 'Tài Yuān',
           loc: '腕掌侧横纹桡侧，桡动脉搏动处。' },
    '2': { mer: '手阳明大肠经', zf: '腑', wx: '阳金', pt: '合谷', py: 'Hé Gǔ',
           loc: '手背第 1、2 掌骨间，第 2 掌骨桡侧中点处（虎口）。' },
    '3': { mer: '手少阴心经', zf: '脏', wx: '阴火', pt: '神门', py: 'Shén Mén',
           loc: '腕部，腕掌侧横纹尺侧端，尺侧腕屈肌腱桡侧凹陷中。' },
    '4': { mer: '足厥阴肝经', zf: '脏', wx: '阴木', pt: '太冲', py: 'Tài Chōng',
           loc: '足背，第 1、2 跖骨结合部前方凹陷中，触及动脉搏动处。' },
    '5': { mer: '足少阳胆经', zf: '腑', wx: '阳木', pt: '丘墟', py: 'Qiū Xū',
           loc: '足外踝前下方，趾长伸肌腱外侧凹陷中。' },
    '6': { mer: '足少阴肾经', zf: '脏', wx: '阴水', pt: '太溪', py: 'Tài Xī',
           loc: '踝区，内踝尖与跟腱之间的凹陷中。' },
    '7': { mer: '足阳明胃经', zf: '腑', wx: '阳土', pt: '冲阳', py: 'Chōng Yáng',
           loc: '足背最高处，拇长伸肌腱与趾长伸肌腱之间，足背动脉搏动处。' },
    '8': { mer: '足太阴脾经', zf: '脏', wx: '阴土', pt: '太白', py: 'Tài Bái',
           loc: '跖区，第 1 跖趾关节后下方凹陷处，赤白肉际。' },
    '9': { mer: '足太阳膀胱经', zf: '腑', wx: '阳水', pt: '京骨', py: 'Jīng Gǔ',
           loc: '跖区，第 5 跖骨粗隆前下方，赤白肉际处。' },
    '0': { mer: '手太阳小肠经', zf: '腑', wx: '阳火', pt: '腕骨', py: 'Wàn Gǔ',
           loc: '腕区，第 5 掌骨底与三角骨之间的赤白肉际凹陷中。' }
  };

  function acuCard(d, role, tail) {
    var a = ACUPOINT[d];
    if (!a) return '';
    return '<div class="acu">' +
      '<div class="acu-hd"><b class="acu-pt">' + esc(a.pt) + '穴</b>' +
        '<span class="acu-py">' + esc(a.py) + '</span>' +
        '<span class="acu-tag">' + esc(role) + '</span></div>' +
      '<div class="acu-mer">' + esc(a.mer) + ' · ' + esc(a.zf) + ' · ' + esc(a.wx) +
        '　←　数字 <b>' + esc(d) + '</b> ' + esc(D.DIGIT_ORGAN[d] || '') + '</div>' +
      '<div class="acu-loc">' + esc(a.loc) + '</div>' +
      (tail ? '<div class="acu-note">' + tail + '</div>' : '') +
      '</div>';
  }

  function renderAcu(r) {
    var el = $('q-acu');
    if (!el) return;

    /* 元宝口径：取穴依据是「当前这副盘的数字串」—— 末位为主、其余为辅、缺数为补漏。
       三张实拍图验证：阳格 29112 → 主 2（合谷）/ 辅 2911（京骨、太渊）；
       阴格 404 → 主 4（太冲）/ 辅 40（腕骨）；阳格 8426 → 主 6（太溪）/ 辅 842（太白、太冲、合谷）。
       慈海两副盘并列，所以阳/阴各出一套，不替老师二选一。 */
    function oneSet(plabel, grid, que, isYin) {
      var g = String(grid || ''), q = String(que || '');
      var main = g.length ? g.charAt(g.length - 1) : '';
      var aux = g.length > 1 ? g.slice(0, -1) : '';
      var used = {}, i, d, html = '';
      var mains = [], auxs = [];
      if (ACUPOINT[main]) mains.push(main);
      for (i = 0; i < aux.length; i++) {
        d = aux.charAt(i);
        if (ACUPOINT[d] && !used[d] && mains.indexOf(d) < 0) { used[d] = 1; auxs.push(d); }
      }
      mains.forEach(function (x) { used[x] = 1; });

      html += '<div class="acu-sec"><div class="acu-sec-t">' + esc(plabel) +
        ' · 先天灵穴 · 天赋气枢' +
        '<span class="acu-sec-n">主 ' + esc(main || '—') +
        (aux ? ' ＋ 辅 ' + esc(aux) : '') +
        (isYin ? '（阴格按末位为主取穴）' : '') + '</span></div>';
      if (!main || !ACUPOINT[main]) {
        html += '<p class="sub">' + esc(plabel) + '无可用数字，先天灵穴跳过。</p>';
      } else {
        mains.forEach(function (x) { html += acuCard(x, '主灵穴', ''); });
        if (auxs.length) {
          html += '<div class="acu-sub">辅灵穴配置（协同调动元气）：</div>';
          auxs.forEach(function (x) { html += acuCard(x, '辅灵穴', ''); });
        } else {
          html += '<div class="acu-sub">辅灵穴：无（辅位为空或与主灵穴重复）</div>';
        }
      }
      html += '</div>';

      html += '<div class="acu-sec"><div class="acu-sec-n-sub">' + esc(plabel) +
        ' · 后天灵穴 · 补漏培元　缺数 ' + esc(q || '无') + '</div>';
      if (!q) {
        html += '<p class="sub">' + esc(plabel) + '无缺数，无需补漏。</p>';
      } else {
        for (i = 0; i < q.length; i++) {
          d = q.charAt(i);
          if (ACUPOINT[d]) html += acuCard(d, '补缺 ' + d, '');
        }
      }
      html += '</div>';
      return html;
    }

    el.innerHTML =
      oneSet('阳格', r.yang, r.yangQue, false) +
      oneSet('阴格', r.yin, r.yinQue, true);
  }

  /* ══════════ 1 详细解读 ══════════ */
  function featList(arr, label) {
    if (!arr || !arr.length) return '';
    return '<div style="margin-top:8px"><b style="font-size:12.5px;color:var(--ink2)">' + label + '</b><ul style="margin:4px 0 0;padding-left:20px;font-size:13.5px">' +
      arr.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul></div>';
  }

  function renderRd() {
    var r = state.res;
    var pairs = r.isZishi
      ? [{ tag: '当天格', yg: r.yang, ig: r.yin, yq: r.yangQue, iq: r.yinQue },
         { tag: '调整格', yg: r.yang1, ig: r.yin1, yq: r.yangQue1, iq: r.yinQue1 }]
      : [{ tag: '', yg: r.yang, ig: r.yin, yq: r.yangQue, iq: r.yinQue }];

    var html = pairs.map(function (p) {
      var cb = M.getCombo(p.yg, p.ig, D.COMBO);
      var out = '<div style="margin-bottom:22px' + (p.tag ? ';padding-top:6px;border-top:1px dashed var(--line)' : '') + '">';
      out += '<div style="font-family:var(--serif);font-size:17px;font-weight:700;margin:0 0 4px">' +
        (p.tag ? '【' + esc(p.tag) + '】' : '') + '阳格 ' + esc(p.yg) + ' × 阴格 ' + esc(p.ig) + '</div>';

      if (cb) {
        var rec = cb.rec;
        if (rec.is_pure) {
          var pe = rec.pure_energy || {};
          out += '<div class="note" style="margin-top:10px"><b>★ ' + esc(rec.combo_name) + '　阴阳同格（纯格）</b><br>' + esc(pe['定义'] || '') + '</div>';
          out += featList(pe['优势'], '优势（能量纯粹性）');
          out += featList(pe['课题'], '核心课题');
          if (pe['修行路径']) out += '<p style="margin-top:10px"><b>修行路径：</b>' + esc(pe['修行路径']) + '</p>';
          if (pe['缺数建议']) out += '<p><b>缺数建议：</b>' + esc(pe['缺数建议']) + '</p>';
          if (rec.summary) out += summaryBlock(rec.summary);
        } else {
          out += '<div style="margin:8px 0"><span class="tag a">' + esc(rec.combo_name) + '</span>' +
            (rec.aliases && rec.aliases.length ? ' <span style="font-size:12.5px;color:var(--ink3)">别称：' + esc(rec.aliases.join(' / ')) + '</span>' : '') + '</div>';
          out += '<div class="grid2" style="margin-top:10px">';
          out += gridInfoCard('阳格', rec.yang_grid, p.yg, 'yang');
          out += gridInfoCard('阴格', rec.yin_grid, p.ig, 'yin');
          out += '</div>';
          if (rec.relationship_dynamics && rec.relationship_dynamics.length) {
            out += '<div class="card" style="margin-top:14px"><h3 style="font-size:14px">关系动态</h3>' +
              featList(rec.relationship_dynamics, '') + '</div>';
          }
          if (rec.combined_path) {
            out += '<p style="margin-top:10px;font-size:13px;color:var(--ink2)">合并路径：' +
              (rec.combined_path['yang'] ? '<code>' + esc(rec.combined_path['yang']) + '</code> ' : '') +
              (rec.combined_path['yin'] ? '<code>' + esc(rec.combined_path['yin']) + '</code>' : '') + '</p>';
          }
          if (rec.summary) out += summaryBlock(rec.summary);
        }
      } else {
        out += '<div class="note blue" style="margin-top:10px">该组合在 <code>COMBO_INTERPRETATIONS</code> 中无专门条目，以下回退为单格解读。</div>';
        out += '<div class="grid2" style="margin-top:10px">';
        out += singleCard('阳格', p.yg, D.SINGLE);
        out += (String(p.ig) !== String(p.yg)) ? singleCard('阴格', p.ig, D.SINGLE) : '';
        out += '</div>';
        if (String(p.ig) === String(p.yg)) {
          var same = M.getSingle(p.yg, D.SINGLE);
          out += '<div class="note" style="margin-top:12px"><b>★ 阴阳同格</b><br>阳格与阴格完全相同（均为 ' +
            esc(same ? same.rec.name : p.yg) + '）。能量高度聚焦，课题高度集中，在各层面反复遇到同一类核心问题。' +
            (same && same.rec['课题'] ? '<br>核心课题：' + esc(same.rec['课题'].join(' / ')) : '') +
            (same && same.rec['修行提示'] ? '<br>修行提示：' + esc(same.rec['修行提示']) : '') + '</div>';
        }
      }
      out += '</div>';
      out += extensionBlock(p);
      return out;
    }).join('');

    $('rd-body').innerHTML = html || '<div class="empty">无解读</div>';
  }

  function gridInfoCard(kind, info, fallbackNum, cls) {
    if (!info) return singleCard(kind, fallbackNum, D.SINGLE);
    var h = '<div class="big ' + cls + '">' +
      '<div class="k">' + kind + ' · ' + esc(info.number || fallbackNum) + '</div>' +
      '<div style="font-size:15px;font-weight:600;margin:4px 0">' + esc(info.identity || '') + '</div>';
    if (info.quote) h += '<div class="m" style="font-style:italic;color:var(--ink3)">「' + esc(info.quote) + '」</div>';
    h += '</div>';
    h += featList(info.features, '特征');
    if (info.earth_role) h += '<p style="font-size:13px"><b>地球角色：</b>' + esc(info.earth_role) + '</p>';
    if (info.wealth_warning) h += '<div class="note warn" style="margin-top:8px">⚠️ ' + esc(info.wealth_warning) + '</div>';
    if (info.path) h += '<p style="font-size:13px"><b>跌落路径：</b><code>' + esc(info.path) + '</code></p>';
    if (info['修行_key']) h += '<p style="font-size:13px"><b>修行要点：</b>' + esc(info['修行_key']) + '</p>';
    return h;
  }

  function singleCard(kind, num, SINGLE) {
    var s = M.getSingle(num, SINGLE);
    if (!s) {
      return '<div class="big"><div class="k">' + kind + ' · ' + esc(num) + '</div>' +
        '<div class="m" style="margin-top:6px">单格库无匹配条目。</div></div>';
    }
    var rec = s.rec;
    return '<div class="big"><div class="k">' + kind + ' · ' + esc(s.key) + '</div>' +
      '<div style="font-size:15px;font-weight:600;margin:4px 0">' + esc(rec.name) + '</div>' +
      '<div class="m">' + esc(rec.level || '') + '</div>' +
      '<div class="m" style="margin-top:6px">' + esc(rec.core || '') + '</div></div>' +
      (rec['课题'] && rec['课题'].length ? featList(rec['课题'], '课题') : '') +
      (rec['修行提示'] ? '<p style="font-size:13px;margin-top:8px"><b>修行提示：</b>' + esc(rec['修行提示']) + '</p>' : '');
  }

  function summaryBlock(sm) {
    var rows = '';
    ['人生剧本', '核心课题', '天赋潜力', '特别注意', '修行总纲'].forEach(function (k) {
      if (sm[k]) rows += '<dt>' + k + '</dt><dd>' + esc(sm[k]) + '</dd>';
    });
    return '<div class="card" style="margin-top:14px;background:#fbf8f2"><h3 style="font-size:14px">综合总结</h3>' +
      '<dl class="kv">' + rows + '</dl></div>';
  }

  /** 延伸参考：灵魂积分 / 天赋使命 / 跌落路径命中 / 单格库条目 */
  /* 任何日期都拿得出的逐位对照：库没收录时，这一块就是主体内容 */
  function digitCells(yg, ig, yq, iq) {
    var rows = '';
    function cnt(str, k) {
      var n = 0;
      for (var i = 0; i < str.length; i++) if (str.charAt(i) === k) n++;
      return n;
    }
    for (var d = 0; d <= 9; d++) {
      var k = String(d);
      var cy = cnt(yg, k), ci = cnt(ig, k);
      var isYin = !!D.DIGIT_YIN[k];
      rows += '<tr><td class="num"><b>' + k + '</b></td>' +
        '<td>' + esc(D.DIGIT_ORGAN[k] || '') + '</td>' +
        '<td><span class="tag ' + (isYin ? 'n' : 'y') + '">' + (isYin ? '阴（脏）' : '阳（腑）') + '</span></td>' +
        '<td>' + (cy ? '<b>' + cy + '</b> 次' : (yq.indexOf(k) >= 0 ? '<span class="miss">缺</span>' : '<span class="carried">魄</span>')) + '</td>' +
        '<td>' + (ci ? '<b>' + ci + '</b> 次' : (iq.indexOf(k) >= 0 ? '<span class="miss">缺</span>' : '<span class="carried">魄</span>')) + '</td>' +
        '<td style="font-size:12.5px">' + esc(D.QUE_FIX[k] || '') + '</td></tr>';
    }
    return rows;
  }

  function queList(que) {
    if (!que) return '<span style="color:var(--ink3)">无缺数</span>';
    var arr = String(que).split('');
    return '<ul style="margin:4px 0 0;padding-left:20px;font-size:13px">' + arr.map(function (k) {
      return '<li><b>' + k + '</b>（' + esc(D.DIGIT_ORGAN[k] || '') + '）：' + esc(D.QUE_FIX[k] || '') + '</li>';
    }).join('') + '</ul>';
  }

  function extensionBlock(p) {
    var yg = p.yg, ig = p.ig, yq = p.yq || '', iq = p.iq || '';

    /* 1. 逐位对照（永远有内容） */
    var out = '<div class="card" style="margin-top:14px">' +
      '<h3 style="font-size:13.5px">逐位对照 · 0–9 全覆盖</h3>' +
      '<p class="sub">阳格 <code>' + esc(yg) + '</code>（' + yg.length + ' 位）／ 阴格 <code>' + esc(ig) + '</code>（' + ig.length + ' 位）。' +
      '同一个数字出现几次就记几次。<span class="miss">缺</span>＝格里没有、同侧魄里也没有（与「缺数」口径一致）；' +
      '<span class="carried">魄</span>＝格里没有，但该数字已由同侧魄承载，故不记为缺。</p>' +
      '<div class="tw"><table><thead><tr><th>数字</th><th>脏腑</th><th>阴阳</th><th>阳格</th><th>阴格</th><th>缺格修正</th></tr></thead>' +
      '<tbody>' + digitCells(String(yg), String(ig), String(yq), String(iq)) + '</tbody></table></div></div>';

    /* 2. 缺数专项 */
    out += '<div class="card" style="margin-top:14px"><h3 style="font-size:13.5px">缺数专项 · 该补什么</h3>' +
      '<p class="sub">缺数＝格里没有、魄里也没有的数字。条数越多，说明能量越集中、需要外部补给的面向越多。</p>' +
      '<div class="grid2"><div><b style="font-size:13px">阳缺 ' + (yq || '无') + '</b>' + queList(yq) + '</div>' +
      '<div><b style="font-size:13px">阴缺 ' + (iq || '无') + '</b>' + queList(iq) + '</div></div></div>';

    /* 3. 库命中（有则报，无则说明为什么无；前缀相似不再当命中） */
    var sc = M.lookupSoulScore(yg, D.SOUL_SCORE_DB);
    var sv = M.lookupSoulV5(yg, D.SOUL_DB);
    var hits = [];
    Object.keys(D.FALL_STRUCT).forEach(function (k) {
      var pp = D.FALL_STRUCT[k];
      var seq = String(pp.full_sequence || '').split('→').map(function (x) { return x.trim(); });
      if (seq.indexOf(String(yg)) >= 0 || seq.indexOf(String(ig)) >= 0) hits.push(pp.title);
    });
    var s1 = M.getSingle(yg, D.SINGLE), s2 = M.getSingle(ig, D.SINGLE);

    out += '<div class="card" style="margin-top:14px"><h3 style="font-size:13.5px">库命中情况</h3><dl class="kv">';
    out += '<dt>阳格灵魂积分</dt><dd>' +
      (sc && sc.rec
        ? esc(sc.key + '　' + sc.rec.stars + '　' + sc.rec.name + '（' + sc.rec.level + '）') +
          (sc.conf === 'same-root' ? ' <span class="tag a">剥零推定</span>' : '')
        : '<span style="color:var(--ink3)">SOUL_SCORE_DB 82 条中无 ' + esc(yg) + '（未收录，不做前缀猜测）</span>') +
      '</dd>';
    if (sv && sv.rec && (sv.rec.t || sv.rec.m)) {
      out += '<dt>天赋 / 使命</dt><dd>' + esc([sv.rec.t, sv.rec.m].filter(Boolean).join(' · ')) + '</dd>';
    }
    out += '<dt>跌落路径</dt><dd>' + (hits.length ? esc(hits.join('；')) + ' <span class="tag a">见「跌落路径」页</span>'
      : '<span style="color:var(--ink3)">阳格与阴格都不在五条主线中</span>') + '</dd>';
    out += '<dt>谱系归属</dt><dd>阳格 ' + esc(String(yg)) + '：' + gridLineBrief(yg) +
      '<br>阴格 ' + esc(String(ig)) + '：' + gridLineBrief(ig) +
      ' <span class="ln-src">（主魂线 × 跌落叙事线，见「跌落路径」页 2.3）</span></dd>';
    out += '<dt>单格库</dt><dd>阳格 ' + (s1 ? esc(s1.rec.name) : '<span style="color:var(--ink3)">无</span>') +
      '；阴格 ' + (s2 && String(ig) !== String(yg) ? esc(s2.rec.name) : '<span style="color:var(--ink3)">同上</span>') + '</dd>';
    out += '</dl>';

    if (!(sc && sc.rec) && !(sv && sv.rec) && !hits.length && !s1 && !s2) {
      out += '<div class="note" style="margin-top:12px">这个格不属于「82 条灵魂积分 / 67 条灵魂库 / 5 条跌落主线 / 31 条单格库」里任何一条 —— ' +
        '四个库收录的都是历史上重点研究过的少数配置，绝大多数日期都落在库外。此时以上「逐位对照」与「缺数专项」才是可靠解读依据，' +
        '下面的命理报告、中医建议、食疗动功三份全文仍按完整算法生成，不受库是否收录影响。</div>';
      if (sc && sc.near) {
        out += '<div class="note warn" style="margin-top:8px">键名前缀相似的有 <code>' + esc(sc.near.key) + '</code>，' +
          '但仅凭前缀相同就套用它的星级会张冠李戴，故不显示。</div>';
      }
    }
    out += '</div>';
    return out;
  }


  /* ══════════ 2 谱系归属：主魂线 × 跌落叙事线（2026-11-15 新增） ══════════ */
  function GL() { return D.GRID_LINES || {}; }
  function arr(x) { return Object.prototype.toString.call(x) === '[object Array]' ? x : []; }
  function trim(s) { return String(s == null ? '' : s).trim(); }

  /** 任意数字格 → 双轴归属。查不到一手定性也不空手：按末位主魂自动归线。 */
  function gridLine(code) {
    var c = String(code == null ? '' : code).replace(/[^0-9]/g, '');
    if (!c) return null;
    var G = GL(), soul = c.charAt(c.length - 1), sl = null;
    arr(G.soul_lines).forEach(function (x) { if (String(x.id) === soul) sl = x; });

    var falls = [];
    Object.keys(D.FALL_STRUCT || {}).forEach(function (k) {
      var p = D.FALL_STRUCT[k];
      var seq = String(p.full_sequence || '').split('→').map(trim).filter(Boolean);
      var i = seq.indexOf(c);
      if (i >= 0) falls.push({ key: k, title: p.title, idx: i + 1, n: seq.length, seq: seq });
      else if (p.stages && p.stages[c]) falls.push({ key: k, title: p.title, idx: null, n: seq.length, seq: seq });
    });

    var fam = (G.family && G.family.tang) || null, tang = null, variant = null, fruit = fam && fam.fruit;
    if (fam) {
      arr(fam.stages).forEach(function (s, i) {
        if (String(s.code) === c) tang = { idx: i + 1, n: arr(fam.stages).length, name: s.name, stage: s.stage, src: s.src };
      });
      arr(fam.variants).forEach(function (v) { if (String(v.code) === c) variant = v; });
    }
    var libs = [];
    if (D.WEAPON && D.WEAPON[c]) libs.push({ k: '法器库', v: D.WEAPON[c][0] });
    if (D.SINGLE && D.SINGLE[c]) libs.push({ k: '单格库', v: D.SINGLE[c].name || '' });
    if (D.FREQ && D.FREQ.yang && (D.FREQ.yang[c] || D.FREQ.yin[c]))
      libs.push({ k: '频次库', v: '阳 ' + (D.FREQ.yang[c] || 0) + ' / 阴 ' + (D.FREQ.yin[c] || 0) });
    return {
      code: c, soul: soul, soulLine: sl, exact: (G.grid_map || {})[c] || null,
      falls: falls, tang: tang, variant: variant, fruit: fruit, fam: fam,
      isFruit: !!fruit && c === String(fruit), libs: libs
    };
  }

  /** 归属查询结果的 HTML（2.3 与延伸参考共用） */
  function gridLineHtml(code) {
    var g = gridLine(code);
    if (!g) return '<div class="note">请输入纯数字格，例如 <code>415</code> / <code>145</code> / <code>28101</code>。</div>';
    var h = '<div class="ln-res">';
    h += '<div class="ln-head"><b class="ln-code">' + esc(g.code) + '</b> ';
    if (g.isFruit) h += '<span class="tag a">果位 · 回修终点</span> ';
    if (g.exact) h += '<span class="tag ' + (g.exact.level === '一手' ? 'ok' : '') + '">' + esc(g.exact.level) + '定性</span>';
    else h += '<span class="tag">按主魂归纳</span>';
    h += '</div>';
    if (g.exact) h += '<p class="ln-name">' + esc(g.exact.name) +
      '<br><span class="ln-src">来源：' + esc(g.exact.src) + '</span></p>';
    else h += '<p class="ln-name">一手库未收录该格的专名；以下按主魂线归纳，属推定层级。</p>';

    h += '<dl class="kv">';
    h += '<dt>轴 A · 主魂线</dt><dd><b>主魂 ' + esc(g.soul) + '</b> · ' +
      (g.soulLine ? esc(g.soulLine.organ) + ' · ' + esc(g.soulLine.totem) +
        ' <span class="ln-src">' + esc(g.soulLine.yy) + '；' + esc(g.soulLine.gift) + '</span>'
        : '<span class="ln-src">分型表未列此主魂</span>') + '</dd>';
    if (g.soulLine) {
      h += '<dt>该线主要格</dt><dd>2000 前 <code>' + esc(arr(g.soulLine.pre).join(' / ')) +
        '</code>；2000 后 <code>' + esc(arr(g.soulLine.post).join(' / ')) + '</code></dd>';
    }
    if (g.tang) h += '<dt>唐僧谱系</dt><dd>第 ' + g.tang.idx + ' / ' + g.tang.n + ' 阶：<b>' +
      esc(g.tang.name) + '</b> —— ' + esc(g.tang.stage) + '</dd>';
    if (g.variant) h += '<dt>谱系变体</dt><dd>' + esc(g.variant.name) +
      '<span class="ln-src">（加辅魂变体，不是新的跌落阶段）</span></dd>';
    h += '<dt>轴 B · 跌落叙事线</dt><dd>';
    if (g.falls.length) {
      h += g.falls.map(function (f) {
        return '<div>' + esc(f.title) + (f.idx ? ' · 第 <b>' + f.idx + '</b> / ' + f.n + ' 阶' : ' · 阶段表内') +
          '<br><span class="ln-src"><code>' + esc(f.seq.join(' → ')) + '</code></span></div>';
      }).join('');
    } else {
      h += '<b class="ln-no">不在任何一条跌落序列里</b>' +
        (g.isFruit ? '：415 是 145 逆向回溯修成后的显化，不是跌落的一环。' : '。');
    }
    h += '</dd>';
    if (g.fam && g.isFruit) {
      h += '<dt>往回修（原路返回）</dt><dd><div class="beads">' +
        arr(g.fam.reverse).map(function (c) { return '<span class="tag" style="font-family:var(--mono)">' + esc(c) + '</span>'; })
          .join('<span class="ln-ar">→</span>') +
        '</div><span class="ln-src">唐僧这一支修成后显化为 <b>415 果位</b>；项目 FALL_STRUCT 的终点写作 28101，两者是不同轴的终点。</span></dd>';
    }
    if (g.libs.length) h += '<dt>本地库命中</dt><dd>' + g.libs.map(function (l) {
      return esc(l.k) + '：' + esc(l.v);
    }).join('；') + '</dd>';
    h += '</dl></div>';
    return h;
  }

  /** 2.3：主魂线总表 + 任意格查询 */
  function gridLinesHtml() {
    var G = GL(), h = '';
    h += '<div class="card"><h3><span class="n">2.3</span>数字格谱系归属 · 主魂线 × 跌落叙事线</h3>' +
      '<p class="sub">回答「415 等等数字格属于哪条线」：<b>两条轴要分开看</b>。' +
      '轴 A 是主魂谱系线（按主魂 1–9 / 0 分型），轴 B 是跌落叙事线（五条跌落路径 + 唐僧谱系）。' +
      '415 属主魂 5 线、是唐僧谱系的<b>果位</b>，<b>不在任何跌落序列里</b>。</p>';

    h += '<div class="ln-q"><label for="lnInput">查一个格属于哪条线</label>' +
      '<input id="lnInput" type="search" value="415" placeholder="如 415 / 145 / 325 / 347 / 28101" autocomplete="off">' +
      '<button class="btn ghost sm" id="lnGo" type="button">查询</button>' +
      '<span class="ln-chips">' + ['415', '145', '235', '325', '347', '268', '28101', '37101', '336'].map(function (c) {
        return '<button class="btn ghost sm" type="button" data-gl="' + c + '">' + c + '</button>';
      }).join('') + '</span></div>';
    h += '<div id="lnResult">' + gridLineHtml('415') + '</div>';

    h += '<h4 style="margin:20px 0 6px;font-size:14px">轴 A · 十条主魂谱系线（一手「九宫格分型」表）</h4>' +
      '<p class="sub">可验算的归纳：每行所有格的<b>末位数字都等于该行主魂</b>，' +
      '因此任意数字格都能自动归线。表中格名按一手原样保留。</p>';
    h += '<div class="tw"><table><thead><tr><th>主魂</th><th>脏腑 / 阴阳</th><th>图腾</th>' +
      '<th>天赋与课程</th><th>2000 前主要格</th><th>2000 后主要格</th><th>与跌落线的交集</th></tr></thead><tbody>';
    arr(G.soul_lines).forEach(function (x) {
      var all = arr(x.pre).concat(arr(x.post)).filter(function (c) { return /^\d+$/.test(c); });
      var rel = [];
      all.forEach(function (c) {
        Object.keys(D.FALL_STRUCT || {}).forEach(function (k) {
          var seq = String(D.FALL_STRUCT[k].full_sequence || '').split('→').map(trim);
          if (seq.indexOf(c) >= 0 && rel.indexOf(D.FALL_STRUCT[k].title) < 0) rel.push(D.FALL_STRUCT[k].title);
        });
      });
      h += '<tr><td class="num"><b>' + esc(x.id) + '</b></td><td>' + esc(x.organ) + '<br><span class="ln-src">' + esc(x.yy) + '</span></td>' +
        '<td>' + esc(x.totem) + '</td><td style="font-size:12.5px">' + esc(x.gift) + '</td>' +
        '<td><code>' + esc(arr(x.pre).join(' / ')) + '</code>' + (x.preNote ? '<br><span class="ln-src">' + esc(x.preNote) + '</span>' : '') + '</td>' +
        '<td><code>' + esc(arr(x.post).join(' / ')) + '</code>' + (x.postNote ? '<br><span class="ln-src">' + esc(x.postNote) + '</span>' : '') + '</td>' +
        '<td style="font-size:12.5px">' + (rel.length ? esc(rel.join('；')) : '<span class="ln-src">—</span>') + '</td></tr>';
    });
    h += '</tbody></table></div>';
    h += '<div class="note">「末位数字＝主魂」是<b>由一手分型表逐行归纳</b>的可验算规则，不是卢先生原话直述；' +
      '「跌落主线」也是项目 FALL_DOC 的整理用语。9 / 0 行一手表写作 <code>1910、2810、3710</code>，' +
      '疑为 19101 等截断，此处<b>原样保留、不擅自改写</b>。</div>';
    h += '</div>';
    return h;
  }

  /** 2.4：415 果位与往回修（双轴路径图 + 长文） */
  function gridFruitHtml() {
    var G = GL(), fam = (G.family && G.family.tang) || {}, h = '';
    var fs = (D.FALL_STRUCT && D.FALL_STRUCT['28101_line']) || {};
    var down = String(fs.full_sequence || '').split('→').map(trim).filter(Boolean);
    var up = arr(fam.reverse);
    h += '<div class="card"><h3><span class="n">2.4</span>415 果位与「往回修」 · 两条方向相反的线</h3>' +
      '<p class="sub">师问「415 这个格是怎么往回修」——按正典应答：' +
      '<b>从 145 一路往回修，唐僧谱系修成之后才显化为 415</b>；415 是果位，不是需要修的起点。</p>';

    h += '<div class="ln-path"><div class="ln-path-t">轴 B · 跌落（顺流向下，二清 28101 主线）</div>' +
      '<div class="beads">' + down.map(function (c, i) {
        var st = (fs.stages || {})[c] || {};
        return '<span class="tag' + (arr(fam.fall_tail).indexOf(c) >= 0 ? ' n' : '') + '" style="font-family:var(--mono)" title="' +
          esc(st.name || '') + '">' + esc(c) + '</span>';
      }).join('<span class="ln-ar">→</span>') + '</div>' +
      '<div class="ln-src">原话（《九宫解译历史人物》第 8 节）：「28101 跌落是 1268 刑天……在跌落是 145 襁褓中的唐僧」；' +
      '末三格 <code>325 → 235 → 145</code> 同时是唐僧谱系的三阶。</div></div>';

    h += '<div class="ln-path"><div class="ln-path-t">轴 B · 往回修（原路返回／倒着转回来）</div>' +
      '<div class="beads">' + up.map(function (c) {
        return '<span class="tag" style="font-family:var(--mono)">' + esc(c) + '</span>';
      }).join('<span class="ln-ar">→</span>') + '</div>' +
      '<div class="ln-src">一手：「你原路返回 37101，你就成了玉皇大帝」「跌落的灵魂，他要返回原来的宗」' +
      '「我们要知道我们跌落的过程……那我们就把它倒过来说」「用呼吸把它倒着转回来」。</div></div>';

    h += '<div class="ln-path ln-fruit"><div class="ln-path-t">轴 A · 唐僧谱系四阶段（主魂 5 线）→ 415 果位</div>' +
      '<div class="ln-stages">' + arr(fam.stages).map(function (s, i) {
        var isFruit = String(s.code) === String(fam.fruit);
        return '<div class="ln-stage' + (isFruit ? ' is-fruit' : '') + '">' +
          '<div class="ln-stage-c">' + esc(s.code) + '</div>' +
          '<div class="ln-stage-n">' + esc(s.name) + '</div>' +
          '<div class="ln-stage-s">' + esc(s.stage) + '</div></div>';
      }).join('<span class="ln-ar">→</span>') + '</div>' +
      '<div class="note">前三格是跌落线上的位置，<b>415 不是跌落的一环</b>：' +
      '它与 145 数字集合同为 {1,4,5}、主魂同为 5，只差辅魂顺序 14 / 41。' +
      '一手资料只给「襁褓 ↔ 果位」的定性，<b>未解释数字机理</b>（A7 记账不编）。</div></div>';

    if (G.doc) h += '<div class="md" id="lnDoc" style="margin-top:18px;padding-top:14px;border-top:1px solid var(--line)">' + MD.render(G.doc) + '</div>';
    h += '<p class="sub" style="margin-top:14px">取证：IMA「卢先生经典语录资料包」（《九宫格相关内容汇总》-5 表、' +
      '《2.九宫解译历史人物》第 1 / 5 / 8 节、《关于九宫格》九宫格分型表）＋' +
      'IMA「卢先生视频转文字的语录」（《疗愈师3班2阶10.22上午（二）》）；本地 data.json 的 FALL_STRUCT / SINGLE / WEAPON / FREQ。</p>';
    h += '</div>';
    return h;
  }

  /** 延伸参考里的一行简版归属 */
  function gridLineBrief(code) {
    var g = gridLine(code);
    if (!g) return '—';
    var t = '主魂 ' + g.soul + ' · ' + (g.soulLine ? esc(g.soulLine.totem) : '未列');
    if (g.isFruit) t += ' <span class="tag a">415 果位 · 回修终点（非跌落态）</span>';
    else if (g.tang) t += ' · 唐僧谱系第 ' + g.tang.idx + ' 阶「' + esc(g.tang.name) + '」';
    else if (g.falls.length) t += ' · ' + esc(g.falls[0].title) + (g.falls[0].idx ? ' 第 ' + g.falls[0].idx + ' 阶' : '');
    else t += ' · 不在跌落序列';
    return t;
  }

  /* ══════════ 2 跌落路径 ══════════ */
  function renderFp() {
    var r = state.res;
    var mine = {};
    mine[r.yang] = 1; mine[r.yin] = 1;
    if (r.isZishi) { mine[r.yang1] = 1; mine[r.yin1] = 1; }

    var keys = Object.keys(D.FALL_STRUCT);
    var html = '<div class="card"><h3><span class="n">2.1</span>五条跌落主线</h3>' +
      '<p class="sub">取自 <code>grid_interpretations.py</code> 的 <code>FALL_PATHS</code>。若某个格属于你，会高亮标出。</p>';

    keys.forEach(function (k) {
      var p = D.FALL_STRUCT[k];
      var seq = String(p.full_sequence || '').split('→').map(function (x) { return x.trim(); }).filter(Boolean);
      var hit = seq.filter(function (c) { return mine[c]; });
      html += '<div style="margin:18px 0 0;padding-top:14px;border-top:1px solid var(--line)">';
      html += '<div style="font-size:15.5px;font-weight:700">' + esc(p.title) +
        (hit.length ? ' <span class="tag a">命中你的格：' + esc(hit.join('、')) + '</span>' : '') + '</div>';
      if (p.subtitle) html += '<div style="font-size:12.5px;color:var(--ink3)">' + esc(p.subtitle) + '</div>';
      html += '<div class="beads" style="margin:10px 0">' + seq.map(function (c) {
        return '<span class="tag ' + (mine[c] ? 'a' : '') + '" style="font-family:var(--mono)">' + esc(c) + '</span>';
      }).join('<span style="color:var(--ink3);align-self:center">→</span>') + '</div>';

      var stages = p.stages || {};
      var order = seq.filter(function (c) { return stages[c]; });
      Object.keys(stages).forEach(function (c) { if (order.indexOf(c) < 0) order.push(c); });
      if (order.length) {
        html += '<div class="tw"><table><thead><tr><th>格</th><th>名称</th><th>身份</th><th>说明</th></tr></thead><tbody>';
        order.forEach(function (c) {
          var st = stages[c] || {};
          html += '<tr><td class="num">' + esc(c) + '</td><td>' + esc(st.name || '') + '</td>' +
            '<td>' + esc(st.identity || '') + '</td><td>' + esc(st.desc || '') +
            (st.note ? '<br><span style="color:var(--warn)">' + esc(st.note) + '</span>' : '') + '</td></tr>';
        });
        html += '</tbody></table></div>';
      }
      if (p['修行目标']) html += '<p style="font-size:13.5px"><b>修行目标：</b>' + esc(p['修行目标']) + '</p>';
      if (k === '28101_line') html += '<div class="note">本线末三格 <code>325 → 235 → 145</code> 同时是' +
        '<b>主魂 5 唐僧谱系</b>的三阶；该谱系修成后显化为 <b>415 果位</b>（修成果位的唐僧）。' +
        '<b>415 不在这条跌落序列里</b>，它是往回修的终点，详见 <b>2.3 / 2.4</b>。</div>';
      html += '</div>';
    });
    html += '</div>';

    html += '<div class="card"><h3><span class="n">2.2</span>四清总纲与解读长文</h3>' +
      '<p class="sub">取自 <code>lu_fall_paths.py</code>，共 ' + Object.keys(D.FALL_DOC).length + ' 篇。</p>';
    Object.keys(D.FALL_DOC).forEach(function (k) {
      html += '<div class="md" style="margin-top:16px;padding-top:14px;border-top:1px solid var(--line)">' +
        MD.render(D.FALL_DOC[k]) + '</div>';
    });
    html += '</div>';

    /* 2.3 / 2.4：数字格谱系归属（2026-11-15 新增） */
    html += gridLinesHtml() + gridFruitHtml();
    $('fp-body').innerHTML = html;

    /* IIFE 页面禁用内联 onchange；renderFp 每次重建 DOM 后重绑 */
    var qi = $('lnInput'), qr = $('lnResult');
    function doLineQuery(v) { if (qr) qr.innerHTML = gridLineHtml(v); }
    if (qi) {
      qi.addEventListener('input', function () { doLineQuery(this.value); });
      qi.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); doLineQuery(this.value); } });
    }
    if ($('lnGo')) $('lnGo').addEventListener('click', function () { if (qi) doLineQuery(qi.value); });
    var host = $('fp-body');
    if (host) host.addEventListener('click', function (e) {
      var b = e.target && e.target.closest ? e.target.closest('[data-gl]') : null;
      if (!b) return;
      if (qi) qi.value = b.getAttribute('data-gl');
      doLineQuery(b.getAttribute('data-gl'));
    });
  }

  /* ══════════ 3/4/5 三份报告 ══════════ */
  function renderReports() {
    $('rp-body').innerHTML = MD.render(state.md.rp);
    $('tm-body').innerHTML = MD.render(state.md.tm);
    $('sl-body').innerHTML = MD.render(state.md.sl);
    $('rp-count').textContent = state.md.rp.length + ' 字符';
    $('tm-count').textContent = state.md.tm.length + ' 字符';
    $('sl-count').textContent = state.md.sl.length + ' 字符';
  }

  /* ══════════ 6 时空行运 ══════════ */
  function renderEx() {
    var f = state.f, r = state.res;
    var day = $('fDay').value || todayISO();
    var sc = $('fDayShichen').value || '巳时';
    var dr = M.calc(slashFromISO(day), sc, f.gender, f.rule);

    var byq = r.yangQue, biq = r.yinQue;
    if (r.isZishi) {
      byq = Array.from(new Set((r.yangQue + r.yangQue1).split(''))).sort().join('');
      biq = Array.from(new Set((r.yinQue + r.yinQue1).split(''))).sort().join('');
    }
    var y = M.analyzeYun(dr, byq, biq);

    var html = '<div class="card">';
    html += '<h3><span class="n">6.1</span>当日天时</h3>';
    html += '<p class="sub">' + esc(day) + ' ' + esc(sc) + ' · ' + esc(dr.type) + '</p>';
    html += '<div class="duo">' + gridCard('yang', '天时阳格', dr.yang, dr.yangQue) +
      gridCard('yin', '天时阴格', dr.yin, dr.yinQue) + '</div>';
    html += '</div>';

    html += '<div class="card"><h3><span class="n">6.2</span>共振表</h3>' +
      '<p class="sub">一级＝同类缺（天时阳缺∩命盘阳缺 或 阴缺∩阴缺）；二级＝交叉缺。同一数字可同时是一级与二级（原引擎两个集合独立计算）。</p>';
    html += '<div class="tw"><table><thead><tr><th>数字</th><th>脏腑</th><th>天时</th><th>命盘</th><th>共振</th></tr></thead><tbody>';
    for (var i = 0; i <= 9; i++) {
      var d = String(i);
      var tz = (dr.yangQue.indexOf(d) >= 0 ? '阳缺 ' : '') + (dr.yinQue.indexOf(d) >= 0 ? '阴缺' : '');
      if (!tz) tz = '正常';
      var inB = (byq.indexOf(d) >= 0 || biq.indexOf(d) >= 0);
      var lv = y.l1.indexOf(d) >= 0 ? '<span class="tag lv1">🔴 一级</span>'
        : (y.l2.indexOf(d) >= 0 ? '<span class="tag lv2">🟡 二级</span>' : '<span class="tag lv0">⚪ 潜伏</span>');
      html += '<tr><td class="num"><b>' + d + '</b></td><td>' + esc(D.DIGIT_ORGAN[d] || '') + '</td>' +
        '<td>' + esc(tz) + '</td><td>' + (inB ? '命盘缺' : '正常') + '</td><td>' + lv + '</td></tr>';
    }
    html += '</tbody></table></div>';

    if (y.l1.length) {
      html += '<div class="note warn" style="margin-top:14px"><b>🔴 一级共振（需重点关注）</b><br>' +
        y.l1.map(function (d) { return d + ' ' + (D.DIGIT_ORGAN[d] || '') + '：' + (D.QUE_FIX[d] || ''); }).join('<br>') + '</div>';
    }
    var l2u = y.l2.filter(function (d) { return y.l1.indexOf(d) < 0; });
    if (l2u.length) {
      html += '<div class="note" style="margin-top:10px"><b>🟡 二级共振（需留意）</b><br>' +
        l2u.map(function (d) { return d + ' ' + (D.DIGIT_ORGAN[d] || '') + '：' + (D.QUE_FIX[d] || ''); }).join('<br>') + '</div>';
    }
    if (!y.l1.length && !l2u.length) {
      html += '<div class="note blue" style="margin-top:14px">今日与本命无缺格共振，各脏腑经络相对平稳；仍宜按命盘固有缺格做日常养护。</div>';
    }
    html += '</div>';

    $('ex-body').innerHTML = html;
  }

  /* ══════════ 7 阴阳周期 ══════════ */
  function renderCy() {
    var r = state.res, f = state.f;
    var lc = r.life;
    if (!lc) { $('cy-body').innerHTML = '<div class="empty">未指定性别，无法推算周期</div>'; return; }

    var maxAge = 90, W = 1120, H = 176, padL = 30, padR = 14;
    var bw = W - padL - padR;
    function X(a) { return padL + (Math.min(a, maxAge) / maxAge) * bw; }

    var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" style="min-width:640px;display:block">';
    svg += '<rect x="0" y="0" width="' + W + '" height="' + H + '" fill="#fdfcf9"/>';

    /* 刻度（末端刻度直接带单位，避免单独画「岁」压在 90 上） */
    for (var a = 0; a <= maxAge; a += 10) {
      svg += '<line x1="' + X(a) + '" y1="52" x2="' + X(a) + '" y2="102" stroke="#e5dfd4" stroke-width="1"/>';
      if (a === maxAge) {
        svg += '<text x="' + X(a) + '" y="120" font-size="11" fill="#8b8478" text-anchor="end" font-family="monospace">' + a + ' 岁</text>';
      } else {
        svg += '<text x="' + X(a) + '" y="120" font-size="11" fill="#8b8478" text-anchor="middle" font-family="monospace">' + a + '</text>';
      }
    }

    /* 阶段条 */
    var y0 = 62, bh = 26;
    lc.cycles.forEach(function (c) {
      if (c.start >= maxAge) return;
      var e = Math.min(c.end, maxAge);
      var x1 = X(c.start), x2 = X(e), w = Math.max(1.5, x2 - x1);
      var fill = c.type === '阳格' ? '#f0d6bb' : (c.type === '阴格' ? '#cfe0ea' : '#e9e3d7');
      var stroke = c.type === '阳格' ? '#b8814a' : (c.type === '阴格' ? '#5885a0' : '#b3a894');
      svg += '<rect x="' + x1.toFixed(1) + '" y="' + y0 + '" width="' + w.toFixed(1) + '" height="' + bh +
        '" fill="' + fill + '" stroke="' + stroke + '" stroke-width="1"/>';
      if (w > 30) {
        svg += '<text x="' + (x1 + w / 2).toFixed(1) + '" y="' + (y0 + 17) +
          '" font-size="10.5" fill="#5c564d" text-anchor="middle">' + esc(c.phase) + '</text>';
      }
    });

    /* 当前年龄线 */
    svg += '<line x1="' + X(lc.age) + '" y1="46" x2="' + X(lc.age) + '" y2="104" stroke="#9c5f2b" stroke-width="2" stroke-dasharray="4 3"/>';
    svg += '<circle cx="' + X(lc.age) + '" cy="46" r="4" fill="#9c5f2b"/>';
    svg += '<text x="' + X(lc.age) + '" y="38" font-size="12" fill="#9c5f2b" text-anchor="middle" font-weight="bold">' + lc.age + ' 岁</text>';

    /* 图例 */
    svg += '<rect x="' + padL + '" y="140" width="12" height="12" fill="#f0d6bb" stroke="#b8814a"/>';
    svg += '<text x="' + (padL + 18) + '" y="150" font-size="11.5" fill="#5c564d">阳格</text>';
    svg += '<rect x="' + (padL + 66) + '" y="140" width="12" height="12" fill="#cfe0ea" stroke="#5885a0"/>';
    svg += '<text x="' + (padL + 84) + '" y="150" font-size="11.5" fill="#5c564d">阴格</text>';
    svg += '<rect x="' + (padL + 132) + '" y="140" width="12" height="12" fill="#e9e3d7" stroke="#b3a894"/>';
    svg += '<text x="' + (padL + 150) + '" y="150" font-size="11.5" fill="#5c564d">换魂（2.3 年）</text>';
    svg += '<text x="' + (W - padR) + '" y="150" font-size="11.5" fill="#8b8478" text-anchor="end">' +
      esc(lc.params.desc) + '</text>';
    svg += '</svg>';

    var inTrans = lc.type === '换魂';
    var html = '<div class="note ' + (inTrans ? 'warn' : 'blue') + '">' +
      '<b>当前阶段：' + esc(lc.phase) + '（' + esc(lc.type) + '）</b>　' +
      lc.start.toFixed(1) + ' – ' + lc.end.toFixed(1) + ' 岁　' +
      '下次换魂：' + esc(lc.nextPhase) + '（' + lc.nextAge.toFixed(1) + ' 岁，距今 ' + lc.toNext.toFixed(1) + ' 年）' +
      (inTrans ? '<br>⚠️ 正处于换魂期，身体能量重组，需特别养护。' : '') +
      '</div>';
    html += '<div class="tl">' + svg + '</div>';

    html += '<div class="tw" style="margin-top:14px"><table><thead><tr><th>阶段</th><th>起</th><th>止</th><th>类型</th></tr></thead><tbody>';
    lc.cycles.slice(0, 16).forEach(function (c) {
      var cur = (c.phase === lc.phase && c.start === lc.start);
      html += '<tr' + (cur ? ' style="background:#fdf6ea"' : '') + '><td>' + (cur ? '▶ ' : '') + esc(c.phase) +
        '</td><td class="num">' + c.start.toFixed(1) + '</td><td class="num">' + c.end.toFixed(1) +
        '</td><td>' + esc(c.type) + '</td></tr>';
    });
    html += '</tbody></table></div>';
    html += '<p class="hint" style="margin-top:10px">注：原引擎把每轮末尾的换魂编号为「换魂 k+2」、下一轮开头的换魂也编号为「换魂 k+2」，' +
      '故表中会出现同名换魂（阶段区间不同）。此处按原样呈现，未改名。</p>';

    $('cy-body').innerHTML = html;
  }

  /* ══════════ 8 灵魂库 / 法器 ══════════ */
  function buildDbRows() {
    var keys = {};
    Object.keys(D.SOUL_SCORE_DB).forEach(function (k) { keys[k] = 1; });
    Object.keys(D.SOUL_DB).forEach(function (k) { keys[k] = 1; });
    var list = Object.keys(keys).sort(function (a, b) {
      if (a.length !== b.length) return a.length - b.length;
      return a < b ? -1 : 1;
    });
    return list.map(function (k) {
      var sc = D.SOUL_SCORE_DB[k] || null;
      var sv = D.SOUL_DB[k] || null;
      return {
        code: k, sc: sc, sv: sv,
        text: [k, sc ? sc.name : '', sc ? sc.level : '', sc ? sc.desc : '',
          sv ? sv.n : '', sv ? sv.t : '', sv ? sv.m : '', sv ? sv.n2 : ''].join(' ').toLowerCase()
      };
    });
  }
  var DB_ROWS = null;

  function renderDb(q) {
    if (!DB_ROWS) DB_ROWS = buildDbRows();
    q = (q || '').trim().toLowerCase();
    var rows = q ? DB_ROWS.filter(function (r) { return r.text.indexOf(q) >= 0; }) : DB_ROWS;
    $('dbCount').textContent = '共 ' + DB_ROWS.length + ' 条' + (q ? '，命中 ' + rows.length : '');
    $('db-body').innerHTML = rows.slice(0, 200).map(function (r) {
      var name = r.sc ? r.sc.name : (r.sv ? r.sv.n : '—');
      var stars = r.sc ? r.sc.stars : '';
      var lv = r.sc ? r.sc.level : '';
      var extra = [];
      if (r.sv && r.sv.t) extra.push('天赋：' + r.sv.t);
      if (r.sv && r.sv.m) extra.push('使命：' + r.sv.m);
      return '<div class="rowitem"><span class="code">' + esc(r.code) + '</span>' +
        '<span class="nm">' + esc(name) + (lv ? '<em>' + esc(lv) + '</em>' : '') +
        (extra.length ? '<em>' + esc(extra.join(' · ')) + '</em>' : '') + '</span>' +
        '<span class="rt">' + esc(stars) + '</span></div>';
    }).join('') || '<div class="empty">无匹配</div>';
  }

  function renderWp(q) {
    q = (q || '').trim().toLowerCase();
    var keys = Object.keys(D.WEAPON);
    var rows = keys.filter(function (k) {
      if (!q) return true;
      var v = D.WEAPON[k];
      return (k + ' ' + v[0] + ' ' + v[1]).toLowerCase().indexOf(q) >= 0;
    });
    $('wpCount').textContent = '共 ' + keys.length + ' 条' + (q ? '，命中 ' + rows.length : '');
    $('wp-body').innerHTML = rows.map(function (k) {
      var v = D.WEAPON[k];
      return '<tr><td class="num">' + esc(k) + '</td><td>' + esc(v[0]) + '</td><td>' + esc(v[1]) + '</td></tr>';
    }).join('');
  }

  /* ══════════ 9 频率统计 ══════════ */
  /* ══════════ 9 频率与稀有度 ══════════ */
  function fmtPct(p, d) { return (p * 100).toFixed(d === undefined ? 3 : d) + '%'; }
  function fmtK(K) { return K >= 1000 ? Math.round(K).toLocaleString() : K.toFixed(K < 10 ? 1 : 0); }
  /* 双格组合总数 = map 里只存了 >=2 次的那部分 + 只出现 1 次的那部分 */
  function jTotal() { return Object.keys(D.JOINT.map).length + D.JOINT.single; }

  function renderSt() {
    var F = D.FREQ;
    /* 四张图共用一把标尺：以全场最高次数为满格，最稀的自然只剩一丝 */
    var gmax = 1;
    [F.yang, F.yin].forEach(function (o) {
      Object.keys(o).forEach(function (k) { if (o[k] > gmax) gmax = o[k]; });
    });

    function bars(obj, el, asc) {
      var arr = Object.keys(obj).map(function (k) { return [k, obj[k]]; })
        .sort(function (a, b) { return asc ? a[1] - b[1] : b[1] - a[1]; })
        .slice(0, 15);
      $(el).innerHTML = arr.map(function (it) {
        var w = Math.max(2, it[1] / gmax * 100);
        return '<div class="bar"><span class="c">' + esc(it[0]) + '</span>' +
          '<span class="t"><i style="width:' + w.toFixed(2) + '%"></i></span>' +
          '<span class="n">' + it[1].toLocaleString() + '</span></div>';
      }).join('');
    }
    bars(F.yang, 'st-yang', false); bars(F.yin, 'st-yin', false);

    /* 只出现 1 次的格：直接全列出来，比「最稀有 15 种」更有信息量 */
    function chips(obj, cls, name) {
      var arr = Object.keys(obj).filter(function (k) { return obj[k] === 1; }).sort();
      return '<div style="margin-bottom:8px"><span class="tag ' + cls + '">' + name + ' ' + arr.length +
        ' 种</span> <span class="chipline">' + arr.map(function (k) {
          return '<span class="chip">' + esc(k) + '</span>';
        }).join('') + '</span></div>';
    }
    $('st-single').innerHTML = chips(F.yang, 'a', '阳格') + chips(F.yin, 'n', '阴格') +
      '<p class="sub" style="margin:6px 0 0">这些格在 70,127 天里只轮到 1 次 ⟹ 稀有系数 K = 70,127、单格稀有分 100。' +
      '阳格与阴格两个清单高度重合（39 种里有 38 种同名）—— 阴格就是把同一套算法套在农历日期上，值域同源，' +
      '所以「极稀」落在同一批数字组合上。</p>';

    $('stMeta').innerHTML = '按日遍历 <b>' + F.start + ' … ' + F.end + '</b> 共 <b>' +
      F.days.toLocaleString() + '</b> 天，每天各记一次：阳格 <b>' + Object.keys(F.yang).length +
      '</b> 种、阴格 <b>' + Object.keys(F.yin).length + '</b> 种、双格组合 <b>' +
      jTotal().toLocaleString() + '</b> 种（其中只出现 1 次的 ' +
      D.JOINT.single.toLocaleString() + ' 种）。两张图条形共用同一标尺。';

    /* 分布图 */
    var b = M.pairBuckets(D.JOINT);
    var bmax = Math.max.apply(null, b.rows.map(function (x) { return x.n; }));
    $('st-buckets').innerHTML = b.rows.map(function (x) {
      return '<div class="bar"><span class="c">' + x.label + '</span>' +
        '<span class="t"><i style="width:' + Math.max(2, x.n / bmax * 100).toFixed(2) + '%"></i></span>' +
        '<span class="n">' + x.n.toLocaleString() + ' 种 · ' +
        (x.n / b.tot * 100).toFixed(1) + '%</span></div>';
    }).join('');

    renderRarity();
  }

  function ruleName(k) {
    if (k === 'v5') return '核心引擎 v5（两个分支都与原书相反）';
    if (k === 'query') return '查询工具原样（后子时不换日）';
    return '原书口径（前子时 +1 / 后子时 −1）';
  }

  /* 分位描述：两端各给一句话，避免出现「0.0% 比它更常见」这种别扭说法 */
  function pctLine(x) {
    if (x.pct >= 99.95) return '稀有度分位 <b>100%</b>（并列最稀）—— 没有任何一种双格组合比它出现得更少。';
    if (x.pct <= 0.05) return '稀有度分位 <b>0%</b> —— 它属于全库最常见的那一档。';
    return '稀有度分位 <b>' + x.pct.toFixed(1) + '%</b>（分位越高越稀）—— 全部 ' +
      jTotal().toLocaleString() + ' 种双格组合里，有 ' + (100 - x.pct).toFixed(1) +
      '% 比它更常见，' + x.pct.toFixed(1) + '% 比它更稀有。';
  }

  /* 9.1 当前生日的格稀有度 */
  function renderRarity() {
    var box = $('rar-body'), r = state.res;
    if (!r) { box.innerHTML = ''; return; }
    var yr = parseInt(String(state.f.birth).slice(0, 4), 10);
    var F = D.FREQ;
    if (!(yr >= 1910 && yr <= 2101)) {
      box.innerHTML = '<p class="hint">统计区间为 ' + F.start + ' … ' + F.end +
        '，这个生日在区间外，无法给出稀有度（频率库不覆盖）。</p>';
      return;
    }
    var x = M.rarity(r.yang, r.yin, F, D.JOINT);
    if (!x) {
      box.innerHTML = '<p class="hint">阳格 <code>' + esc(r.yang) + '</code> / 阴格 <code>' +
        esc(r.yin) + '</code> 不在频率库中，无法计算。</p>';
      return;
    }

    function row(name, tag, code, cnt, p, K, S, w) {
      return '<tr><td>' + name + '<span class="wt">' + w + '</span></td>' +
        '<td class="num">' + (tag ? '<span class="tag ' + tag + '">' + esc(code) + '</span>' : esc(code)) + '</td>' +
        '<td class="num">' + cnt.toLocaleString() + '</td>' +
        '<td class="num">' + fmtPct(p) + '</td>' +
        '<td class="num">' + fmtK(K) + '</td>' +
        '<td class="num"><b>' + S.toFixed(1) + '</b></td></tr>';
    }

    var html = '<div class="rarhead">' +
      '<div class="rarscore"><b>' + x.score.toFixed(1) + '</b><span>稀有度打分 / 100</span></div>' +
      '<div class="rartxt">' +
      '<span class="tag ' + x.band.c + '">' + x.band.t + '</span> ' +
      '<span class="tag a">阳格 ' + esc(r.yang) + '</span> ' +
      '<span class="tag n">阴格 ' + esc(r.yin) + '</span>' +
      '<p style="margin:8px 0 0">在 ' + F.start + ' … ' + F.end + ' 的 <b>' + F.days.toLocaleString() +
      '</b> 天里，这一组「' + esc(r.yang) + ' × ' + esc(r.yin) + '」只出现 <b>' +
      x.cj.toLocaleString() + '</b> 天（' + fmtPct(x.cj / x.N, 4) + '）；稀有系数 <b>K = ' +
      fmtK(x.Kr) + '</b>，即平均每 ' + fmtK(x.Kr) + ' 天才轮到一次。</p>' +
      '<p style="margin:6px 0 0;color:var(--ink3);font-size:13px">' + pctLine(x) + '</p>' +
      '</div></div>';

    html += '<div class="tw" style="margin-top:16px"><table><thead><tr>' +
      '<th>层（权重）</th><th>格</th><th>出现次数</th><th>占本侧</th><th>稀有系数 K（天/次）</th><th>子分</th>' +
      '</tr></thead><tbody>' +
      row('阳格', 'a', r.yang, x.cy, x.cy / x.N, x.Ky, x.Sy, '25%') +
      row('阴格', 'n', r.yin, x.ci, x.ci / x.N, x.Ki, x.Si, '25%') +
      row('双格实测', '', r.yang + ' × ' + r.yin, x.cj, x.cj / x.N, x.Kr, x.Sr, '50%') +
      '<tr class="sumrow"><td>综合</td><td class="num">—</td><td class="num">—</td>' +
      '<td class="num">—</td><td class="num">—</td><td class="num"><b>' + x.score.toFixed(1) + '</b></td></tr>' +
      '</tbody></table></div>';

    /* 名义叠加 vs 实测 */
    html += '<div class="note" style="margin-top:14px">' +
      '<b>稀有系数叠加</b>：阳格 K = ' + fmtK(x.Ky) + '，阴格 K = ' + fmtK(x.Ki) +
      '，两者相乘得名义叠加 <b>K = ' + fmtK(x.Knom) + '</b>（若两边独立，本该平均每 ' +
      fmtK(x.Knom) + ' 天才出现一次）。<br>' +
      '但实测只有 <b>' + fmtK(x.Kr) + '</b>，实测 / 名义 = <b>' + (x.ratio * 100).toFixed(1) +
      '% </b>。原因是阴格取自<b>农历</b>日期、阳格取自<b>阳历</b>日期，二者强相关，独立性不成立 ——' +
      '全库 12,152 种组合上 log(名义) 与 log(实测) 的 Spearman 只有 0.68。所以打分以<b>实测 K</b> 为准，' +
      '名义叠加只作参照。</div>';

    html += '<div class="note blue" style="margin-top:10px">' +
      '<b>打分公式</b>：子分 S = 100 · ln(K) / ln(70,127)，K = 天/次。<br>' +
      '综合 = 0.25 · S阳 + 0.25 · S阴 + 0.50 · S双格实测。<br>' +
      '含义：某格在 70,127 天里只出现 1 次 ⟹ K = 70,127 ⟹ S = 100 分（最稀）；天天都是同一格 ⟹ S = 0。' +
      '双格权重加倍，因为最终落到你身上的是这一对组合。</div>';

    if (r.isZishi) {
      var x2 = M.rarity(r.yang1, r.yin1, F, D.JOINT);
      if (x2) {
        html += '<div class="note warn" style="margin-top:10px">' +
          '子时还有一组<b>调整格</b>：阳格 ' + esc(r.yang1) + ' × 阴格 ' + esc(r.yin1) +
          '，全区间出现 <b>' + x2.cj.toLocaleString() + '</b> 天，稀有度打分 <b>' +
          x2.score.toFixed(1) + '</b>（' + x2.band.t + '）。上面算的是「当天格」。' +
          (x2.cj < x.cj ? '调整格反而更稀有。' : '') + '</div>';
      }
    }
    box.innerHTML = html;
  }

  function stSearch(q) {
    q = (q || '').trim();
    if (!q) {
      $('st-detail').innerHTML = '<p class="hint">输入一个或多个格（空格分隔）查看其在 ' + D.FREQ.start +
        ' … ' + D.FREQ.end + ' 区间内的出现次数与稀有度。输入两个格时，按「阳格 阴格」给出双格稀有度。</p>';
      return;
    }
    var codes = q.split(/[\s,，]+/).filter(Boolean);
    var N = D.FREQ.days;
    var html = '<div class="tw"><table><thead><tr><th>格</th><th>作阳格</th><th>作阴格</th>' +
      '<th>稀有系数 K</th><th>单格稀有分</th><th>灵魂库</th></tr></thead><tbody>';
    codes.forEach(function (c) {
      var y = D.FREQ.yang[c] || 0, n = D.FREQ.yin[c] || 0;
      var sc = D.SOUL_SCORE_DB[c];
      var best = Math.max(y ? N / y : 0, n ? N / n : 0);
      html += '<tr><td class="num">' + esc(c) + '</td>' +
        '<td class="num">' + (y ? y.toLocaleString() + '（' + fmtPct(y / N, 3) + '）' : '—') + '</td>' +
        '<td class="num">' + (n ? n.toLocaleString() + '（' + fmtPct(n / N, 3) + '）' : '—') + '</td>' +
        '<td class="num">' + (best ? fmtK(best) : '—') + '</td>' +
        '<td class="num">' + (best ? M.rScore(best, N).toFixed(1) : '—') + '</td>' +
        '<td>' + (sc ? esc(sc.stars + ' ' + sc.name) : '<span style="color:var(--ink3)">—</span>') + '</td></tr>';
    });
    html += '</tbody></table></div>';

    if (codes.length >= 2) {
      var yg = codes[0], ig = codes[1];
      var x = (D.FREQ.yang[yg] && D.FREQ.yin[ig]) ? M.rarity(yg, ig, D.FREQ, D.JOINT) : null;
      if (x) {
        html += '<div class="note" style="margin-top:12px"><b>双格稀有度：' + esc(yg) + ' × ' + esc(ig) + '</b><br>' +
          '全区间出现 <b>' + x.cj.toLocaleString() + '</b> 天 · 稀有系数 K = <b>' + fmtK(x.Kr) +
          '</b> · 名义叠加 K = ' + fmtK(x.Knom) + ' · 打分 <b>' + x.score.toFixed(1) +
          '</b>（<span class="tag ' + x.band.c + '">' + x.band.t + '</span>）· 分位 ' + x.pct.toFixed(1) + '%</div>';
      } else {
        html += '<div class="note warn" style="margin-top:12px">这两个格单独存在，但这一对组合在 ' +
          D.FREQ.start + ' … ' + D.FREQ.end + ' 里没出现过，无法给出双格稀有度。</div>';
      }
    }
    $('st-detail').innerHTML = html;
  }

  /* ══════════ 10 算法与校验 ══════════ */
  function renderAl() {
    var r = state.res, f = state.f, a = r.a;

    var digits = a.po.join(' ');
    var tot = a.po.reduce(function (x, y) { return x + y; }, 0);

    /* 「成串」直接取引擎实际拼出的 parts（不在此处重算，避免两套实现打架） */
    function stepA4() {
      if (a.route === 'MultiSoul') {
        return '总和 = 10 且两个以上魄升魂 ⟹ 走 <b>MultiSoul</b> 特例（九位公式成串），末位落数根 ' + a.main + '。';
      }
      if (a.route === 'B') return '合计 ' + tot + ' < 10 ⟹ 末位直接落合计本身 <b>' + a.main + '</b>，不再取数根。';
      return '合计 ' + tot + ' 取数根 ⟹ 末位落 <b>' + a.main + '</b>；合计本身 <b>' + tot + '</b> 整块作为「中间值」参与成串。';
    }
    function stepA5() {
      var parts = a.parts || [], extra = a.extra || [];
      var cnt = {};
      parts.join('').split('').forEach(function (c) { cnt[c] = (cnt[c] || 0) + 1; });
      var cntTxt = Object.keys(cnt).map(function (k) { return k + '×' + cnt[k]; }).join('、');
      if (a.route === 'MultiSoul') {
        return '按 MultiSoul 九位公式（辅魂₁ 辅魂₂ 年数根 月数根 日十位 数根 辅魂₁ 合计首位 日个位）成串 ⟹ ' +
          '<b>' + esc(parts.join('')) + '</b> ⟹ 阳格 <b>' + esc(r.yang) + '</b>。';
      }
      return '辅魂 ' + (a.up.length ? a.up.join('') : '无') + ' + ' +
        (a.route === 'B' ? '年月日数根 + 合计' : '中间值 + 末位数根') + ' ⟹ ' +
        parts.join(' | ') + ' = <b>' + esc(parts.join('')) + '</b>；再数一遍：' + cntTxt +
        (extra.length
          ? ' ⟹ ' + extra.join('') + ' 已凑满 3 个，追加 ⟹ 阳格 <b>' + esc(r.yang) + '</b>。'
          : ' ⟹ 无数字凑满 3 个，不追加 ⟹ 阳格 <b>' + esc(r.yang) + '</b>。');
    }

    var html = '<p>以 <code>' + esc(f.birth) + '</code> 为例，把年月日拆成单个数字：</p>' +
      '<div class="note blue"><b>魄（拆数）</b>：' + esc(digits) + '　合计 <b>' + tot + '</b></div>' +
      '<dl class="kv">' +
      '<dt>① 拆数</dt><dd>年 4 位 + 月 2 位 + 日 2 位，得魄 ' + a.po.length + ' 位（见上）。</dd>' +
      '<dt>② 升魂</dt><dd>同一数字出现 ≥3 次即每 3 个升为辅魂：' +
      (a.up.length ? '<code>' + esc(a.up.join('')) + '</code>' : '本例无') + '。</dd>' +
      '<dt>③ 判路线</dt><dd>合计 ' + tot + (tot < 10 ? ' < 10 ⟹ <b>路线 B</b>（直接用数根作基座）' : ' ≥ 10 ⟹ <b>路线 A</b>（逐级数根落主魂）') + '。</dd>' +
      '<dt>④ 数根</dt><dd>' + stepA4() + '</dd>' +
      '<dt>⑤ 成串</dt><dd>' + stepA5() + '</dd>' +
      '<dt>⑥ 阴格</dt><dd>把公历换成农历后，用<b>同一套</b>阳格算法再算一遍 ⟹ 阴格 <b>' + esc(r.yin) + '</b>' +
      (state.lunar ? '（对应农历 ' + state.lunar.y + '-' + state.lunar.m + '-' + state.lunar.d + '）' : '') + '。</dd>' +
      '<dt>⑦ 缺数</dt><dd>0–9 中未出现者。阳缺 = 阳格 ∪ 魄 之外的数字；阴缺 = 阴格 ∪ 农历魄 之外的数字。</dd>' +
      '<dt>⑧ 半补</dt><dd>按时辰五行取补数：金 1·2、木 4·5、水 0·6、火 3、土 7·8·9。本例 ' +
      esc(f.shichen) + ' ⟹ <b>' + esc(r.half || '无') + '</b>。</dd>' +
      '</dl>' +
      '<div class="note" style="margin-top:12px"><b>两个「主魂」不是一回事</b>：<br>' +
      '本页第 ④ 步说的「末位数根」指 <code>rds(合计)</code>，是算法落下去的最后一个数；<br>' +
      '而「灵魂详情」里的<b>主魂</b>在源码中是 <code>yang[-1]</code>（阳格<b>最后一位</b>），<b>辅魂</b>是 <code>yang[:-1]</code>（前面所有位）。' +
      '有追加位时（第 ⑤ 步凑满 3 个追加）末位会是追加的那个数字，两者就不再相等 —— 这是源侧命名遗留，本页照原样呈现。' +
      '本例：末位数根 <b>' + esc(String(a.main)) + '</b>，阳格末位（主魂）<b>' + esc(a.soulDetail.mainSoul) + '</b>。</div>';
    $('al-body').innerHTML = html;

    $('al-verify').innerHTML =
      '<div class="grid3">' +
      '<div class="big"><div class="k">农历表</div><div style="font-size:20px;font-weight:600">73,779 天</div>' +
      '<div class="m">1900-01-01 – 2101-12-31，与 <code>lunarcalendar</code> 逐日比对零差异</div></div>' +
      '<div class="big"><div class="k">引擎字段比对</div><div style="font-size:20px;font-weight:600">12,608 项</div>' +
      '<div class="m">705 组样本 × 阳格/阴格/缺数/半补/魄/路线/周期，0 失败</div></div>' +
      '<div class="big"><div class="k">三份报告</div><div style="font-size:20px;font-weight:600">21 / 21</div>' +
      '<div class="m">7 组输入 × 3 份报告，与 Python 写出的 .md 逐字节一致</div></div>' +
      '</div>' +
      '<p class="hint" style="margin-top:12px">校验在构建期完成（node 侧比对 Python 黄金样本），页面本身不含任何硬编码结果。' +
      '另：频率库按日复算 70,127 天、比对 1,351 项（阳格 605 种 + 阴格 606 种逐格、双格组合 12,152 种直方图），0 失败。</p>';

    $('al-issues').innerHTML =
      '<div class="note warn"><b>① 闰月的「1」前缀从未生效</b><br>' +
      '<code>nine_palace_core_v5.py</code> 用 <code>leap = lunarcalendar.month &lt; 0</code> 判断闰月，' +
      '但该库的 <code>month</code> 恒为正、闰月另由 <code>isleap</code> 标记，故这个判据永远为假，' +
      '「闰月阴格前加 1」是死代码。本页与之一致（不额外加 1），否则所有历史结果都会变。</div>' +
      '<div class="note warn"><b>② 子时换日：两个实现各错一半，已按原书定为「前子时 +1 / 后子时 −1」</b><br>' +
      '核心引擎 v5 取 <code>前子时 = 日期−1</code>、<code>后子时 = 日期+1</code>；' +
      '查询工具 <code>adjust_date_for_zishi</code> 取 <code>前子时 = 日期+1</code>。同一份 <code>前子时</code> 输入，' +
      '两者给出的调整格是<b>相邻的两天</b>。<br>' +
      '<b>《九宫解译历史人物》第一章第 6 节「子时的人」原文</b>：「如果是前子时的师兄，他想要计算出后子时的那套系统，' +
      '他就需要在自己的出生日期上面，去额外的加一天，比如说你是，阳历 1990 年 5 月 8 号，前子时出生的师兄……' +
      '后子时就是 1990 年 5 月 9 号」「如果你是后子时出生的，那么想要去计算出前子时的格，就在出生日期上面去减一天」。<br>' +
      '<b>《九宫格相关内容汇总》一、算法</b>：「子时有两套系统：第二套前子时加一天计算，后子时减一天计算。」<br>' +
      '<b>《道医九宫格说明书》二、特殊场景规则</b>：「前子时（23:00-0:00）：日期加 1 天计算（如 6 月 1 日 23:30 → 按 6 月 2 日计算）」。<br>' +
      '三份资料一致 ⟹ <b>前子时 +1 天、后子时 −1 天才是正确</b>。据此对照两个实现：<br>' +
      '· <b>核心引擎 v5</b>：前 −1、后 +1 ⟹ <b>两个分支都反</b>；<br>' +
      '· <b>查询工具</b>：前 +1、后 <b>不换日</b> ⟹ 只对了前子时；后子时的两套格退化成同一套，等于少了一整套魂；<br>' +
      '⟹ 所以不是「二选一」，而是<b>两者各错一半</b>。本页新增 <b>原书口径</b>（前 +1 / 后 −1）并设为默认，' +
      '三份报告随之同步；v5 与 query 仍可切换，仅供复现历史输出。</div>' +
      '<div class="note warn"><b>③ v3.9 报告的「来源」字段顺序随机</b><br>' +
      '<code>src_str = \'+\'.join(set(yq_src))</code> 用的是 <code>set</code>，Python 字符串哈希随机化会让' +
      '同一输入每次运行顺序不同（已实测四次四种顺序）。本页固定为 当天 → 调整 → 当天阴 → 调整阴。</div>' +
      '<div class="note warn"><b>④ 「阴阳格期」判据与取值不匹配</b><br>' +
      '报告里判断 <code>trend == "阳"</code> / <code>"阴"</code>，而 <code>analyze_grid_yin_yang</code> 只会返回' +
      '<code>偏阴 / 偏阳 / 平衡</code>，于是永远落到 else 分支、印出「当前处于阴格期」——即便实际是偏阳。' +
      '本页保留原输出以便与 .md 对齐，真实倾向以上方「阴阳倾向」卡片为准。</div>' +
      '<div class="note warn"><b>⑤ 随仓库的 grid_frequency_data.json 分母不统一</b><br>' +
      '文件里 <code>yang_counter</code> 合计 435,004、<code>yin_counter</code> 合计 69,762，比值 6.24；' +
      '而生成脚本 <code>batch_grid_count.py</code> 是每天各 +1，两个合计本应相等。' +
      '实测阴格那侧正好是 1910-01-01…2100-12-31 的 69,762 天；阳格那侧约跨 1200 年' +
      '（1400–2600 区间 438,656 天 / 784 种，1300–2700 得 804 种，与它的 798 种吻合），' +
      '且文件内没有 <code>total_days</code> / <code>date_range</code> 字段可供核对。' +
      '分母不统一就无法换算概率，因此本页第 9 页的频率与稀有度<b>全部改用重算值</b>' +
      '（1910-01-01…2101-12-31，70,127 天，每天各记一次）。</div>' +
      '<div class="note warn"><b>⑥ 灵魂积分的前缀兜底会张冠李戴（本条本页未照抄）</b><br>' +
      '<code>nine_palace_query.lookup_soul_score</code> 的第三、四级保底只按字符串前缀给星级：' +
      '凡以 <code>021</code> 开头的格都被认成 <code>0219101</code>「一清/西王母变体」，' +
      '<code>1246</code>（759 天）被认成 <code>12433101</code>「新维度播种玉皇」★★★★☆。' +
      '按全区间 605 种阳格统计，这样错配的有 <b>173 种、4,946 天，占 7.05%</b>；' +
      '另有 11 条键名本身不是合法阳格（其中 <code>-02167</code> 带负号永远匹配不上）。' +
      '本页因此把前缀匹配降级为「仅提示、不出星级」，只保留精确命中与剥前导零' +
      '（后者明确标 <b>剥零推定</b>），<code>SOUL_DB</code> 同样只用精确匹配。' +
      '灵魂星级是档案位阶、不是数字的函数——这一条已用分组检验证伪（最强特征组合也只有 47.9% 组内一致）。</div>';
  }

  /* ── 命盘长图导出（2026-11-20 加）────────────────────────────────────
     为什么要自己画 SVG：本页是【零外链单文件】（build.py 体检会拦「外链协议前缀」和「外部脚本引用」），
     引不进 html-to-image / dom-to-image 那类库。所以走「手写 SVG → Image → canvas → PNG」，
     全程零依赖，且矢量重绘天然比截图清晰（这里按 2× 输出）。
     只导出"命盘"这一块，不做整页长图：整页含 12 个标签页，导出来没人看。 */
  function svgEsc(v) {
    return String(v == null ? '' : v).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function plateSVG(r, f) {
    var W = 700, M = 36, CW = W - M * 2;      /* 内容宽 628 */
    var CELL = 200, GAP = 14;                  /* 3×200 + 2×14 = 628 */
    var FF = 'Microsoft YaHei,PingFang SC,Noto Sans SC,sans-serif';
    var SER = 'Songti SC,SimSun,serif';
    var INK = '#1e1b17', INK2 = '#5c564d', INK3 = '#8b8478', LINE = '#e5dfd4',
        LINE2 = '#d5cdbe', ACC = '#9c5f2b', PAPER = '#fbfaf6';
    /* 元宝风格：数字固定五行底色，不看在不在格 */
    var NUM_C = { '1': '#ffffff', '2': '#ffffff', '3': '#f6a8a2', '4': '#d5efda',
      '5': '#d5efda', '6': '#ded8f7', '7': '#fde9b5', '8': '#fde9b5', '9': '#fde9b5', '0': '#ded8f7' };
    var NUM_B = { '1': '#ded9d0', '2': '#ded9d0', '3': '#e9908a', '4': '#b6dfbf',
      '5': '#b6dfbf', '6': '#c6bdf0', '7': '#efd791', '8': '#efd791', '9': '#efd791', '0': '#c6bdf0' };
    var BLUE = '#6b5ce7', M_MAIN = '#3f36a8', M_PO = '#e04b43', M_MISS = '#7a7a7a';
    var o = [];
    function T(x, y, str, size, color, anchor, weight, ff) {
      o.push('<text x="' + x + '" y="' + y + '" font-size="' + size + '" fill="' + color +
        '" font-family="' + (ff || FF) + '"' +
        (anchor ? ' text-anchor="' + anchor + '"' : '') +
        (weight ? ' font-weight="' + weight + '"' : '') + '>' + str + '</text>');
    }
    function R(x, y, w, h, fill, stroke, dash, rx) {
      o.push('<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="' +
        (rx == null ? 10 : rx) + '" fill="' + fill + '" stroke="' + stroke + '"' +
        (dash ? ' stroke-dasharray="5 4"' : '') + '/>');
    }
    /* 原版角标是「重复几个画几个」，不是「符号+数字」 */
    function repS(ch, n) { var s = ''; for (var j = 0; j < n; j++) s += ch; return s; }

    /* ---- 头部 ---- */
    var y = 52;
    T(M, y, '慈海九宫格 · 命盘', 30, INK, null, '700', SER);
    y += 30;
    var gtxt = (f.gender === 'male' ? '男' : '女');
    T(M, y, svgEsc(f.birth) + '　' + svgEsc(f.shichen || '未填时辰') + '　' + gtxt +
      '　' + svgEsc(r.type || ''), 15.5, INK2);
    y += 22;
    var lunarTxt = r.a && r.a.lunar
      ? ('农历 ' + r.a.lunar.y + ' 年 ' + (r.a.lunar.leap ? '闰' : '') + r.a.lunar.m + ' 月 ' + r.a.lunar.d + ' 日')
      : '农历 —';
    T(M, y, svgEsc(lunarTxt) + '　·　半补 ' + svgEsc(r.half || '无') +
      (r.half ? '（' + svgEsc(r.half.split('').map(function (d) { return D.DIGIT_ORGAN[d] || ''; }).join('、')) + '）' : ''),
      13, INK3);
    y += 26;
    o.push('<line x1="' + M + '" y1="' + y + '" x2="' + (W - M) + '" y2="' + y +
      '" stroke="' + LINE + '"/>');
    y += 18;

    /* ---- 两副盘：竖向排，长图适合手机看 ---- */
    var po = (r.a && r.a.po) || '', lnPo = (r.a && r.a.lunarPo) || '';
    var sd = (r.a && r.a.soulDetail) || {};

    function onePlate(label, grid, que, pps, who, whenTxt) {
      var g = String(grid || ''), q = String(que || ''), pp = String(pps || '');
      var top = y;
      /* 卡高：标题 30 + 3×CELL + 2×GAP + 0格(CELL) + gap 14 + 注 34 + padding 36 */
      var cardH = 30 + 3 * CELL + 2 * GAP + 14 + CELL + 34 + 36;
      R(M, top, CW, cardH, '#ffffff', LINE, false, 12);
      var ix = M + 18, iy = top + 18;
      T(ix, iy + 16, label, 17.5, BLUE, null, '700', SER);
      T(ix + 160, iy + 16, svgEsc(g || '—'), 15, INK3, null, null, 'Consolas,monospace');
      if (whenTxt) T(M + CW - 18, iy + 16, svgEsc(whenTxt), 12, INK3, 'end');
      iy += 30;
      function cell(d, x0, y0, side) {
        var k = String(d);
        var isQ = q.indexOf(k) >= 0;
        var nIn = 0, nPo = 0, na = 0;
        for (var t1 = 0; t1 < g.length; t1++) if (g.charAt(t1) === k) nIn++;
        for (var t2 = 0; t2 < pp.length; t2++) if (pp.charAt(t2) === k) nPo++;
        R(x0, y0, CELL, CELL, NUM_C[k], NUM_B[k], false, 10);
        var cx = x0 + CELL / 2;
        T(cx, y0 + CELL * 0.55, k, 46, BLUE, 'middle', '700', 'Consolas,monospace');
        o.push('<text x="' + cx + '" y="' + (y0 + CELL * 0.75) + '" font-size="16" fill="' +
          INK2 + '" font-family="' + FF + '" text-anchor="middle">' +
          svgEsc(D.DIGIT_ORGAN[k] || '?') +
          (nIn > 1 ? '<tspan fill="' + M_PO + '" dx="3">×' + nIn + '</tspan>' : '') + '</text>');
        /* 角标四角分工：左上 ▲辅魂 · 右上 ■主魂 · 左下 ○魄 · 右下 ★缺 */
        if (who === 'yang' && sd.mainSoul && String(sd.mainSoul).indexOf(k) >= 0)
          T(x0 + CELL - 9, y0 + 20, '■', 15, M_MAIN, 'end', '700', 'Consolas,monospace');
        if (who === 'yang' && sd.auxSoul) {
          for (var t3 = 0; t3 < String(sd.auxSoul).length; t3++)
            if (String(sd.auxSoul).charAt(t3) === k) na++;
          if (na) T(x0 + 9, y0 + 20, repS('▲', na), 14, BLUE, null, '700', 'Consolas,monospace');
        }
        if (nPo) T(x0 + 9, y0 + CELL - 10, repS('○', nPo), 15, M_PO, null, '700', 'Consolas,monospace');
        if (isQ) T(x0 + CELL - 9, y0 + CELL - 10, '★', 15, M_MISS, 'end', '700', 'Consolas,monospace');
      }
      /* 竖向 123：列号 = floor((d-1)/3)，行号 = (d-1)%3 ⇒ 1/2/3 竖排第一列 */
      var d, x0, y0;
      for (d = 1; d <= 9; d++) {
        x0 = ix + Math.floor((d - 1) / 3) * (CELL + GAP);
        y0 = iy + ((d - 1) % 3) * (CELL + GAP);
        cell(d, x0, y0);
      }
      /* 甲字形：0 作第 10 格，落在下方正中 */
      var z0x = ix + (CELL + GAP), z0y = iy + 3 * CELL + 2 * GAP + 14;
      cell(0, z0x, z0y);
      var zIn = 0, zPo = 0;
      for (var z1 = 0; z1 < g.length; z1++) if (g.charAt(z1) === '0') zIn++;
      for (var z2 = 0; z2 < pp.length; z2++) if (pp.charAt(z2) === '0') zPo++;
      var zt = zIn ? ('格中 ' + zIn + ' 次') : '不在格中';
      if (zPo) zt += ' · 魄中 ' + zPo + ' 次';
      if (!zIn && !zPo && q.indexOf('0') >= 0) zt += ' · 缺漏';
      T(ix, z0y + CELL + 22, '0（' + (D.DIGIT_ORGAN['0'] || '小肠') + '）' + zt +
        '　·　■ 主魂　▲ 辅魂　○ 魄　★ 缺漏（重复几个＝出现几次）' +
        (who === 'yang' ? '' : '　·　阴格无主魂/辅魂口径'), 12, INK3);
      y = top + cardH + 24;
    }

    onePlate('阳格九宫 · 当天', r.yang, r.yangQue, po, 'yang', r.date);
    onePlate('阴格九宫 · 当天', r.yin, r.yinQue, lnPo, 'yin', r.date);
    if (r.isZishi && r.b) {
      var bp = (r.b && r.b.po) || '', blp = (r.b && r.b.lunarPo) || '';
      var bsd = (r.b && r.b.soulDetail) || {};
      var savedSd = sd; sd = bsd;   /* onePlate 内部读外层 sd */
      T(M, y - 12, '—— ' + (r.isQian ? '前子时' : '后子时') + ' · 调整格 ' + svgEsc(r.adjDate) +
        '（' + svgEsc(ruleName(r.rule)) + '）——', 14, BLUE);
      y += 12;
      onePlate('阳格九宫 · 调整', r.yang1, r.yangQue1, bp, 'yang', r.adjDate);
      onePlate('阴格九宫 · 调整', r.yin1, r.yinQue1, blp, 'yin', r.adjDate);
      sd = savedSd;
    }

    /* ---- 底部来源 ---- */
    T(M, y + 6, '盘位竖排：1/2/3 第一列、4/5/6 第二列、7/8/9 第三列，0 作第十格落下方正中（甲字形）；',
      12, INK3);
    T(M, y + 24, '不看在不在格；角标 ▲辅魂 ■主魂 ○魄 ★缺数。慈海只定义「数字→脏腑」，未定义卦位方位，故不标卦名。',
      12, INK3);
    T(M, y + 42, '慈海九宫格 · 即时解读　·　核心引擎 nine_palace_core_v5  ·  本图由页面当场计算生成',
      12, INK3);
    var H = Math.ceil(y + 60);

    return '<?xml version="1.0" encoding="UTF-8"?>' +
      /* xmlns 必须拆开写：build.py 体检要求全文不含外链协议前缀（本页零外链） */
      '<svg xmlns="' + 'http' + '://www.w3.org/2000/svg' + '" width="' + W + '" height="' + H +
      '" viewBox="0 0 ' + W + ' ' + H + '">' +
      '<rect width="' + W + '" height="' + H + '" fill="' + PAPER + '"/>' +
      o.join('') + '</svg>';
  }

  function exportPlatePNG() {
    if (!state.res || !state.f) {
      window.alert('先点「开始解读」出结果，再导出。');
      return;
    }
    var svg = plateSVG(state.res, state.f);
    var img = new Image();
    img.onload = function () {
      var S = 2;                                   /* 2× 高清 */
      var cv = document.createElement('canvas');
      cv.width = Math.round(img.width * S);
      cv.height = Math.round(img.height * S);
      var g = cv.getContext('2d');
      g.fillStyle = '#fbfaf6';
      g.fillRect(0, 0, cv.width, cv.height);
      g.drawImage(img, 0, 0, cv.width, cv.height);
      var nm = '慈海九宫格_' + String(state.f.birth).replace(/[\/\\]/g, '-') +
        '_' + (state.f.shichen || '') + '_' + (state.f.gender === 'male' ? '男' : '女') + '.png';
      var a = document.createElement('a');
      a.download = nm;
      a.href = cv.toDataURL('image/png');
      a.click();
    };
    img.onerror = function () { window.alert('SVG 转 PNG 失败：请换 Chrome / Edge 打开本页再试。'); };
    /* 用 encodeURIComponent 而不是 btoa —— 图里有中文，btoa 会抛 InvalidCharacterError */
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
  }

  /* ══════════ 交互绑定 ══════════ */
  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.top = '-9999px';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch (e) { }
    document.body.removeChild(ta);
  }

  function bind() {
    $('btnRun').addEventListener('click', userRun);
    $('btnExportPlate').addEventListener('click', exportPlatePNG);
    $('btnDemo').addEventListener('click', function () {
      $('fName').value = '小李';
      $('fBirth').value = '2012-12-21';
      $('fShichen').value = '巳时';
      $('fGender').value = 'male';
      $('fClock').value = '';
      $('fCity').value = '';
      $('fRule').value = 'book';
      run();
    });

    ['fName', 'fBirth', 'fShichen', 'fGender', 'fClock', 'fCity', 'fRule'].forEach(function (id) {
      $(id).addEventListener('change', userRun);
    });
    $('fBirth').addEventListener('keydown', function (e) { if (e.key === 'Enter') userRun(); });
    bindHist();

    $('btnDay').addEventListener('click', renderEx);
    $('fDay').addEventListener('change', renderEx);
    $('fDayShichen').addEventListener('change', renderEx);

    $('dbSearch').addEventListener('input', function () { renderDb(this.value); });
    $('wpSearch').addEventListener('input', function () { renderWp(this.value); });
    $('stSearch').addEventListener('input', function () { stSearch(this.value); });

    document.addEventListener('click', function (e) {
      var c = e.target.closest('[data-copy]');
      if (c) {
        var key = c.getAttribute('data-copy').replace('-md', '');
        var txt = state.md[key] || '';
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(txt).then(function () { flash(c, '已复制'); }, function () { fallbackCopy(txt); flash(c, '已复制'); });
        } else { fallbackCopy(txt); flash(c, '已复制'); }
        return;
      }
      var d = e.target.closest('[data-dl]');
      if (d) {
        var k2 = d.getAttribute('data-dl').replace('-md', '');
        var nm = { rp: '综合命理报告', tm: '倪海厦中医建议', sl: '食疗动功方案' }[k2] || k2;
        var nm2 = (state.f && state.f.name) || '命盘';
        var blob = new Blob([state.md[k2] || ''], { type: 'text/markdown;charset=utf-8' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = nm2 + nm + '_' + (state.f ? state.f.birth.replace(/\//g, '') : '') + '.md';
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
      }
    });

    function flash(el, msg) {
      var old = el.textContent;
      el.textContent = msg;
      setTimeout(function () { el.textContent = old; }, 1200);
    }
  }

  /* ══════════ 启动 ══════════ */
  function init() {
    M.lunarInit(window.__LUNAR__);
    histSortRead();          /* 排序偏好要在第一次 renderHist 之前读回来 */
    buildTabs();
    fillCities();
    $('fDay').value = todayISO();
    $('fDay').setAttribute('max', '2101-12-31');
    bind();
    renderDb('');
    renderWp('');
    renderSt();
    stSearch('');
    run();
    histAutoDedup(true);      /* 开机自动清掉历史遗留的重复名单（默认按名单） */
    renderHist();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
