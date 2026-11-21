/* ══════════════════════════════════════════════════════════════════════
   四柱八字 · 阴阳五行倾向（2026-11-21 师命：替换旧「数字→脏腑」判法）
   依据：
     · 排盘核心 = lunar-javascript（九龙道长 zydx.top 同款 Solar/Lunar/EightChar）
       交叉验证：一组虚构生日/钟点 → 癸亥 丁巳 癸卯 己未（与开源 bazi-tool 一致；
       按 SOUL C8 仅保留四柱结果作算法锚点，不记录真实生日）。
     · 五行量化 = 公开子平算法：天干 1.0、地支本气 1.0 + 藏干各 0.3；
       月令旺衰 旺×1.5 / 相×1.2 / 休×0.8 / 囚×0.5 / 死×0.2。
     · 身强身弱 = 得令（月令）+ 得地（通根）+ 得生（印星透干），三项计数。
     · 阴阳偏性 = 四柱天干地支阴阳个数统计（阳干支 / 阴干支）。
   仅作传统文化研究与参考，不替代医疗 / 法律 / 投资决策。
   ══════════════════════════════════════════════════════════════════════ */
(function (G) {
  'use strict';
  var LU = G.LunarUtil, WXG = LU.WU_XING_GAN, WXZ = LU.WU_XING_ZHI;
  var GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
  var ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
  var WUXING = ['木', '火', '土', '金', '水'];
  var YANG_GAN = { '甲': 1, '丙': 1, '戊': 1, '庚': 1, '壬': 1 };
  var YANG_ZHI = { '子': 1, '寅': 1, '辰': 1, '午': 1, '申': 1, '戌': 1 };
  /* 五行生克：生我者印、同我者比、我生者食伤、我克者财、克我者官杀 */
  var SHENG = { '木': '火', '火': '土', '土': '金', '金': '水', '水': '木' }; // 我生
  var KE = { '木': '土', '土': '水', '水': '火', '火': '金', '金': '木' };    // 我克
  function shengOf(x) { for (var k in SHENG) if (SHENG[k] === x) return k; return null; } // 生我者
  function keOf(x) { for (var k in KE) if (KE[k] === x) return k; return null; }          // 克我者

  /* 月令旺衰：以日主五行为核心，按四季定旺相休囚死。
     春(寅卯)木旺/火相/水休/金囚/土死；夏(巳午)火旺/土相/木休/水囚/金死；
     秋(申酉)金旺/水相/土休/火囚/木死；冬(亥子)水旺/木相/金休/土囚/火死；
     辰戌丑未月土旺/金相/火休/木囚/水死。 */
  var SEASON = {
    '寅': ['木', '火', '水', '金', '土'], '卯': ['木', '火', '水', '金', '土'],
    '巳': ['火', '土', '木', '水', '金'], '午': ['火', '土', '木', '水', '金'],
    '申': ['金', '水', '土', '火', '木'], '酉': ['金', '水', '土', '火', '木'],
    '亥': ['水', '木', '金', '土', '火'], '子': ['水', '木', '金', '土', '火'],
    '辰': ['土', '金', '火', '木', '水'], '戌': ['土', '金', '火', '木', '水'],
    '丑': ['土', '金', '火', '木', '水'], '未': ['土', '金', '火', '木', '水']
  };
  var WANG_COEF = { '旺': 1.5, '相': 1.2, '休': 0.8, '囚': 0.5, '死': 0.2 };
  var WANG_NAME = ['旺', '相', '休', '囚', '死'];

  function initScore() { return { '木': 0, '火': 0, '土': 0, '金': 0, '水': 0 }; }
  function addScore(score, wx, v) { if (wx in score) score[wx] += v; }

  /* 主入口：birth = 'YYYY/MM/DD' 或 'YYYY-MM-DD'，clock = 'HH:MM'（可空），
     shichen 仅用于无钟点时按时辰中气近似（子23/1、丑2、寅4...）。 */
  function analyze(birth, clock, gender, shichen) {
    var m = /^(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})$/.exec(String(birth || '').trim());
    if (!m) return null;
    var y = +m[1], mo = +m[2], d = +m[3], hh = 12, mi = 0, fromClock = false;
    if (clock && /^\d{1,2}:\d{2}$/.test(clock)) {
      var p = clock.split(':'); hh = +p[0]; mi = +p[1]; fromClock = true;
      if (isNaN(hh) || isNaN(mi) || hh < 0 || hh > 23 || mi < 0 || mi > 59) return null;
    } else if (shichen) {
      /* 无钟点：用该时辰代表小时（子时取 0 点） */
      var map = { '前子时': 23, '后子时': 0, '丑时': 2, '寅时': 4, '卯时': 6, '辰时': 8,
        '巳时': 10, '午时': 12, '未时': 14, '申时': 16, '酉时': 18, '戌时': 20, '亥时': 22 };
      if (shichen in map) { hh = map[shichen]; fromClock = true; }
    }
    if (!fromClock) return null;                       /* 没有任何时辰信息，不排时柱 */

    var solar = G.Solar.fromYmdHms(y, mo, d, hh, mi, 0);
    var lunar = solar.getLunar(), ec = lunar.getEightChar();
    var pillars = [
      { name: '年柱', gz: ec.getYear(),  gan: ec.getYearGan(),  zhi: ec.getYearZhi(),  hide: ec.getYearHideGan() },
      { name: '月柱', gz: ec.getMonth(), gan: ec.getMonthGan(), zhi: ec.getMonthZhi(), hide: ec.getMonthHideGan() },
      { name: '日柱', gz: ec.getDay(),   gan: ec.getDayGan(),   zhi: ec.getDayZhi(),   hide: ec.getDayHideGan() },
      { name: '时柱', gz: ec.getTime(),  gan: ec.getTimeGan(),  zhi: ec.getTimeZhi(),  hide: ec.getTimeHideGan() }
    ];
    var dayGan = ec.getDayGan(), dayWx = WXG[dayGan], monthZhi = ec.getMonthZhi();

    /* ---- 五行量化 ---- */
    var raw = initScore(), detail = { '木': [], '火': [], '土': [], '金': [], '水': [] };
    pillars.forEach(function (p, idx) {
      var gwx = WXG[p.gan];
      addScore(raw, gwx, 1.0);
      detail[gwx].push(p.gan + '(' + p.name.charAt(0) + '干)');
      var zwx = WXZ[p.zhi];
      addScore(raw, zwx, 1.0);
      detail[zwx].push(p.zhi + '(' + p.name.charAt(0) + '支本气)');
      p.hide.forEach(function (hg) {
        var hwx = WXG[hg];
        addScore(raw, hwx, 0.3);
        detail[hwx].push(hg + '(' + p.zhi + '藏)');
      });
    });

    /* 月令旺衰：对该五行整体加权（月令本气五行为旺） */
    var season = SEASON[monthZhi] || SEASON['寅'];
    var wangOf = {}; season.forEach(function (wx, i) { wangOf[wx] = WANG_NAME[i]; });
    var weighted = initScore(), wangApplied = [];
    WUXING.forEach(function (wx) {
      var w = WANG_COEF[wangOf[wx]] || 1;
      weighted[wx] = Math.round(raw[wx] * w * 100) / 100;
      if (raw[wx] > 0 && w !== 1) wangApplied.push(wx + wangOf[wx] + '×' + w);
    });
    var total = WUXING.reduce(function (s, wx) { return s + weighted[wx]; }, 0);
    var pct = {};
    WUXING.forEach(function (wx) { pct[wx] = total ? Math.round(weighted[wx] / total * 1000) / 10 : 0; });
    var ranked = WUXING.slice().sort(function (a, b) { return weighted[b] - weighted[a]; });
    var dominant = ranked[0], weakest = ranked[ranked.length - 1];

    /* ---- 日主强弱：得令 + 得地 + 得生 ---- */
    var reasons = [], strength = 0;
    var monthWx = WXZ[monthZhi];
    if (monthWx === dayWx) { strength++; reasons.push('得令：月令' + monthZhi + '(' + monthWx + ')与日主同气'); }
    else if (SHENG[monthWx] === dayWx || shengOf(dayWx) === monthWx) {
      /* 月令生日主（印）或月令为日主所生（食伤泄气，不算得令）；仅「生我」算得令生扶 */
      if (shengOf(dayWx) === monthWx) { strength++; reasons.push('得令生扶：月令' + monthZhi + '(' + monthWx + ')生日主' + dayWx); }
    }
    var roots = [];
    pillars.forEach(function (p) {
      if (WXZ[p.zhi] === dayWx) roots.push(p.zhi);
      p.hide.forEach(function (hg) { if (WXG[hg] === dayWx && roots.indexOf(p.zhi + '藏' + hg) < 0) roots.push(p.zhi + '藏' + hg); });
    });
    if (roots.length) { strength++; reasons.push('得地：' + roots.join('、') + ' 为日主通根'); }
    var yinStar = shengOf(dayWx);  // 生我者=印
    var touYin = pillars.filter(function (p) { return WXG[p.gan] === yinStar; }).map(function (p) { return p.gan; });
    if (touYin.length) { strength++; reasons.push('得生：天干' + touYin.join('、') + '(' + yinStar + ')为印星生身'); }
    var body;
    if (strength >= 3) body = '身强';
    else if (strength === 2) body = '偏强';
    else if (strength === 1) body = '偏弱';
    else body = '身弱';
    /* 喜用：身强喜克泄耗（官杀/食伤/财），身弱喜生扶（印/比劫） */
    var favor = (strength >= 2)
      ? [keOf(dayWx), SHENG[dayWx], KE[dayWx]].filter(Boolean)
      : [yinStar, dayWx].filter(Boolean);
    /* 忌神 = 喜用的反面：身强忌生扶（印/比劫），身弱忌克泄耗（官杀/食伤/财） */
    var avoid = (strength >= 2)
      ? [yinStar, dayWx].filter(Boolean)
      : [keOf(dayWx), SHENG[dayWx], KE[dayWx]].filter(Boolean);

    /* ---- 阴阳统计（四柱天干 + 地支）---- */
    var yang = 0, yin = 0, yangList = [], yinList = [];
    pillars.forEach(function (p) {
      [p.gan, p.zhi].forEach(function (c) {
        var isYang = (GAN.indexOf(c) >= 0 && YANG_GAN[c]) || (ZHI.indexOf(c) >= 0 && YANG_ZHI[c]);
        if (isYang) { yang++; yangList.push(c); } else { yin++; yinList.push(c); }
      });
    });
    var yyTrend = yang > yin ? '偏阳' : (yang < yin ? '偏阴' : '阴阳平衡');
    var dayGanYang = !!(YANG_GAN[dayGan]), dayYy = dayGanYang ? '阳日主' : '阴日主';

    return {
      ok: true, pillars: pillars, dayGan: dayGan, dayWx: dayWx, dayYy: dayYy,
      lunarDate: lunar.toString(), ganZhi: pillars.map(function (p) { return p.gz; }).join(' '),
      wangOf: wangOf, wangApplied: wangApplied,
      raw: raw, weighted: weighted, pct: pct, detail: detail,
      ranked: ranked, dominant: dominant, weakest: weakest,
      strength: strength, body: body, reasons: reasons, favor: favor, avoid: avoid,
      yang: yang, yin: yin, yangList: yangList, yinList: yinList, yyTrend: yyTrend,
      note: '排盘依据 lunar-javascript（九龙道长 zydx.top 同款）；五行量化含藏干与月令旺衰，身强身弱按得令/得地/得生三项计。仅供传统文化研究参考。'
    };
  }

  /* ---- 五行后天开运对照表（公开子平共识：颜色/数字/方位/饮食/养生/饰品/作息/行业）----
     来源交叉核对：dskfs.com、yi958.com、ordoslfy.com、g5u.cn 等，取各来源一致部分。
     仅作传统文化研究参考。 */
  var OPEN = {
    '木': { color: '青色、绿色', num: '3、8', dir: '正东、东南', taste: '酸、温性',
      food: '绿色蔬菜、动物肝胆、青梅、柠檬、豆类', organ: '肝、胆',
      jade: '木质手串、绿幽灵/翡翠', act: '晨间公园散步、庭院种植、拉伸',
      life: '居室多绿植、木制品，少戴金属', trade: '园林、木材、教育、出版、医药' },
    '火': { color: '红色、紫色、橙色', num: '2、7', dir: '正南、东南', taste: '苦、热性',
      food: '红色果蔬（草莓/番茄/车厘子）、动物的心与小肠、辣椒', organ: '心、小肠、血脉',
      jade: '红玛瑙、紫水晶', act: '晒太阳、下厨、写作创作',
      life: '居室温暖明亮，少熬夜护眼，控制情绪', trade: '艺术、餐饮、美容、营销、石化' },
    '土': { color: '黄色、棕色、卡其', num: '5、0', dir: '中央、本地、西南/东北', taste: '甘、中性',
      food: '黄色食物（小米/南瓜/山药）、动物脾胃、蛋白质', organ: '脾、胃、消化',
      jade: '玉石、黄水晶、陶瓷', act: '散步、站桩、规律作息',
      life: '居室宜近山/平原，黄色家居，多读经典', trade: '地产、农业、陶瓷、仓储、教育' },
    '金': { color: '白色、银色、金色', num: '4、9', dir: '正西、西北', taste: '辛、凉性',
      food: '白色食物（梨/百合/银耳/白萝卜）、动物大肠、润肺', organ: '肺、大肠、呼吸道',
      jade: '金银首饰、白金、金属饰品', act: '深呼吸、有氧运动',
      life: '居室可用大理石/瓷砖，随身带钱币，少食辛辣', trade: '金融、机械、珠宝、医疗、法律' },
    '水': { color: '黑色、蓝色、灰色', num: '1、6', dir: '正北、西北', taste: '咸、寒性',
      food: '黑色食物（黑木耳/黑豆/海带）、鱼、动物肾、滋阴补肾', organ: '肾、膀胱、泌尿',
      jade: '水晶、黑曜石、珍珠', act: '游泳、静坐冥想',
      life: '居室近水，多喝水，亥时（21-23点）前入睡', trade: '水利、物流、贸易、旅游、水产' }
  };
  /* ---- 二十四节气食养库（师命 2026-11-21：养生饮食须结合节气）----
     依据（单文件零外链，仅标注机构与篇名，不含 URL）：
       ① 国家中医药管理局主管《中国中医药报》/中国中医药网：清明、谷雨、白露、霜降、小雪专题；
       ② 新华网/央视网：中国中医科学院西苑医院、广安门医院专家节气养生解读；
       ③ 北京中医药大学东方医院《二十四节气食疗方》（2025 服贸会发布）；
       ④ 人民网健康时报《二十四节气养生表》。
     只取各家一致或权威单篇明示内容，作为传统文化研究参考，不替代专业医嘱。
     字段：n 节气 / wx 时令五行 / organ 重点脏腑 / pr 养生原则 / food 当令食材 /
           avoid 忌口 / recipe 代表食疗 */
  var JIEQI = {
    '立春': { wx: '木', organ: '肝、胆', pr: '助阳升发，增辛减酸，护阳春捂', food: '韭菜、葱、香菜、豆芽、春笋、山药、芡实、白扁豆', avoid: '酸收过度、生冷油腻', recipe: '芡实扁豆山药粥（健脾益气、化湿和胃）' },
    '雨水': { wx: '木', organ: '肝、脾', pr: '健脾祛湿，防倒春寒，少酸多甘', food: '山药、薏苡仁、小米、南瓜、韭菜、豆芽、蜂蜜', avoid: '辛辣燥热、卤制品、生冷', recipe: '山药薏米粥（健脾祛湿）' },
    '惊蛰': { wx: '木', organ: '肝、肺', pr: '疏肝润燥，清淡甘平微辛，助阳勿助火', food: '茵陈、梨（熟食）、百合、菠菜、荸荠、山药', avoid: '辛辣助火、过酸、生冷', recipe: '茵陈粥/冰糖炖梨（清湿热、润春燥）' },
    '春分': { wx: '木', organ: '肝、脾', pr: '调和阴阳，清热疏肝，勿偏寒偏热', food: '香椿、荠菜、春笋、菠菜、山药、蜂蜜、豆类', avoid: '大寒大热、过油腻', recipe: '香椿拌豆腐/荠菜煮鸡蛋（清热解毒、健胃理气）' },
    '清明': { wx: '木', organ: '肝、脾', pr: '平肝养阴、祛湿防风，慎发物', food: '银耳、薏仁、黄芪、山药、桑葚、杏仁、黄豆、燕麦、扁豆', avoid: '猪头肉/公鸡肉/鹅肉等发物、辛辣、海腥、过腻过酸煎炸', recipe: '银耳薏仁黄芪汤/青蒿蹄花汤（利水渗湿、清热滋补）' },
    '谷雨': { wx: '木', organ: '肝、脾', pr: '养肝清肝、健脾祛湿，为入夏打底', food: '菠菜、白扁豆、赤小豆、薏仁、山药、荷叶、芡实、冬瓜、陈皮、鲫鱼', avoid: '过度寒凉伤脾、暴饮暴食、对胃有刺激之物', recipe: '银耳怀山药排骨汤（健胃益气）' },
    '立夏': { wx: '火', organ: '心、脾', pr: '清补为主、兼顾祛湿，养心护脾', food: '乌梅、山楂、苦瓜、莲子、薏苡仁、赤小豆、茯苓、山药、绿叶菜', avoid: '油腻辛辣、冷饮冰品伤脾阳', recipe: '猪肝绿豆粥（养肝补血、利水消肿）' },
    '小满': { wx: '火', organ: '脾、胃', pr: '清热化湿、健脾和胃，南北有别', food: '白扁豆、赤小豆、薏苡仁、苦瓜、黄豆、冬瓜、鲫鱼、木棉花', avoid: '油腻、生冷、辛辣；脾胃虚寒者勿久食寒凉', recipe: '苦瓜黄豆排骨汤（清热益气、健脾和胃）' },
    '芒种': { wx: '火', organ: '脾、胃', pr: '防暑湿、护脾胃，宜清淡祛湿酸甘', food: '苦瓜、赤小豆、乌梅、薏米、山药、冬瓜、荷叶', avoid: '油腻、生冷、辛辣（三宜三忌）', recipe: '乌梅汤/薏米山药粥（生津祛湿）' },
    '夏至': { wx: '火', organ: '心、脾', pr: '顺时养阳、健脾化湿、滋养心阴宁心', food: '山药、茯苓、莲子、冬瓜、薏苡仁、百合、麦冬、银耳、乌梅、苦瓜、苦菊', avoid: '生冷寒凉、肥甘厚味、过咸过燥', recipe: '莲子茯苓糕/百合银耳羹（补益心脾、益气安神）' },
    '小暑': { wx: '火', organ: '心、脾', pr: '清热解暑、健脾化湿，勿贪凉伤阳', food: '绿豆、荷叶、莲子、冬瓜、薏苡仁、山药、生姜（空调房）', avoid: '冰品过度、油腻厚味', recipe: '荷叶粥/绿豆汤（清暑化湿）' },
    '大暑': { wx: '火', organ: '心、脾', pr: '暑湿热并重，化湿健脾、清心除烦', food: '苦瓜、冬瓜、西瓜、绿豆、荷叶、莲子心、淡竹叶、薏苡仁', avoid: '脾胃虚弱者勿长期寒凉、生冷油腻', recipe: '莲子茯苓糕（补益心脾、益气安神）' },
    '立秋': { wx: '金', organ: '肺、脾', pr: '润肺防燥、健脾祛湿，慎贴秋膘', food: '薏苡仁、冬瓜、豆芽、菠菜、胡萝卜、芹菜、雪梨、百合、山药', avoid: '辛辣燥热、肥甘厚腻；江南暑湿未退勿盲目进补', recipe: '薏苡仁冬瓜汤（健脾祛湿、润肺止渴）' },
    '处暑': { wx: '金', organ: '肺', pr: '滋阴润燥、收敛阳气，早睡早起', food: '百合、银耳、梨、莲子、山药、蜂蜜、乌梅、石榴', avoid: '辛辣、生冷、海鲜过敏者慎食', recipe: '莲子百合粥（润肺安神）' },
    '白露': { wx: '金', organ: '肺、肝', pr: '养阴润燥、省辛增酸、少凉多温', food: '黑芝麻、核桃、杏仁、蜂蜜、银耳、麦冬、沙参、百合、乌梅、山楂、龙眼肉、乌鸡、鸭肉', avoid: '辛辣发散、寒凉、燥热、肥甘厚腻', recipe: '百合银耳雪梨羹（润肺止咳、滋阴润燥）' },
    '秋分': { wx: '金', organ: '肺、胃', pr: '暖胃护胃、润肺安神，昼夜均调', food: '南瓜、小米、山药、银耳、百合、梨、柑橘、莲藕', avoid: '生冷瓜果过度、辛辣燥热', recipe: '小米南瓜粥/银耳百合羹（补中益气、滋阴润肺）' },
    '寒露': { wx: '金', organ: '肺、胃', pr: '防寒防燥、收敛阳气，饮食温润', food: '银耳、百合、山药、梨、蜂蜜水、淡茶、柿子（每日不超一个）', avoid: '生冷、辣椒/花椒/白酒等辛辣发散', recipe: '银耳百合山药羹（滋阴润燥）' },
    '霜降': { wx: '金', organ: '肺、脾', pr: '防寒润燥、淡补脾胃，补冬不如补霜降', food: '牛肉、羊肉、鸡肉、生姜、红枣、紫苏、山药、桂圆、枸杞、百合、银耳、梨、葡萄、莲藕、柑橘、石榴', avoid: '生冷、辛辣燥热、秋瓜过度、过早用肉桂等大热之品', recipe: '姜枣茶/山药羊肉汤（温补脾胃、滋阴润燥）' },
    '立冬': { wx: '水', organ: '肾', pr: '敛阴护阳、补肾藏精，冬补之始', food: '黑豆、黑芝麻、羊肉、核桃、栗子、山药、莲藕、黑米', avoid: '生冷、过燥大汗', recipe: '黑芝麻糊/当归生姜羊肉汤（温阳祛寒）' },
    '小雪': { wx: '水', organ: '脾、肾', pr: '温养为要：温而不燥、补而不滞，温中健脾兼温润', food: '生姜、葱、红枣、山药、莲子、羊肉、鲫鱼、桂圆、黑米/黑豆/黑芝麻、银耳、百合、雪梨', avoid: '冰淇淋/冰镇饮料/生冷海鲜、西瓜苦瓜等寒凉、盲目重油厚腻', recipe: '桂圆姜枣茶；山药红枣茯苓粥；银耳百合莲子羹' },
    '大雪': { wx: '水', organ: '肾、脾', pr: '藏阳固气、散寒祛湿、温补脾胃', food: '羊肉、牛肉、桂圆、核桃、栗子、山药、薏米、红枣、莲藕', avoid: '生冷寒凉；实热体质宜清淡防内火', recipe: '莲藕粥（健脾开胃、止泻固精）' },
    '冬至': { wx: '水', organ: '肾', pr: '冬至一阳生，温阳补肾、防寒保暖', food: '羊肉、饺子（驱寒活血）、黑芝麻、枸杞、核桃、山药', avoid: '生冷、剧烈运动大汗泄阳', recipe: '枸杞芝麻粥/当归生姜羊肉汤（温补肝肾）' },
    '小寒': { wx: '水', organ: '肾', pr: '防寒保暖，按气虚/阳虚/血虚分型温补', food: '黄芪牛肉汤（气虚）、干姜肉桂羊肉汤（阳虚）、鸡丝阿胶汤（血虚）、山药、栗子', avoid: '生冷、过度辛燥', recipe: '黄芪牛肉汤/干姜肉桂羊肉汤（驱寒取暖）' },
    '大寒': { wx: '水', organ: '肾、肝', pr: '防风寒、护肝，温补兼疏导，勿过补', food: '防风、葱白、生姜、大枣、羊肉、山药、粳米', avoid: '生冷、过度进补、熬夜', recipe: '防风粥（祛风解表、散寒止痛）' }
  };
  var JIEQI_SRC = '节气依据：国家中医药管理局主管《中国中医药报》/中国中医药网（清明/谷雨/白露/霜降/小雪专题）、' +
    '新华网与央视网（中国中医科学院西苑医院、广安门医院专家解读）、北京中医药大学东方医院二十四节气食疗方、' +
    '人民网健康时报《二十四节气养生表》。长期公益更新可查：中国中医药网「养生中国」专栏（节气养生/食疗药膳/每周药食/应地药膳）、' +
    '国家中医药管理局官网、中国公众健康网；命盘底色依据公开子平共识。资料策略：开发时联网查证公益网页，' +
    '若网页失效、不可达或查询失败，退回本页内嵌节气资料库（本表），确保离线与分享页仍给出完整建议。' +
    '仅供传统文化研究参考，不替代专业医嘱。';
  function pad2(n) { return n < 10 ? '0' + n : '' + n; }
  function jqName(key) {
    var map = { 'DONG_ZHI': '冬至', 'DA_HAN': '大寒', 'XIAO_HAN': '小寒', 'LI_CHUN': '立春',
      'DA_XUE': '大雪', 'YU_SHUI': '雨水', 'JING_ZHE': '惊蛰' };
    return map[key] || key;
  }
  /* 公历日期 → 当前所处节气（交节当日归新节气）。
     用 lunar-javascript 的节气表（天文算法，含交节时刻）按年月日比对，
     兼容跨年（查上年与当年两张表），失败返回 null。 */
  function jieqiOf(dateISO) {
    var m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(String(dateISO || '').trim());
    if (!m) return null;
    var y = +m[1], target = y + '-' + pad2(+m[2]) + '-' + pad2(+m[3]);
    var bestName = '', bestYmd = '';
    [y - 1, y].forEach(function (yy) {
      var table = G.Solar.fromYmd(yy, 6, 1).getLunar().getJieQiTable();
      for (var k in table) {
        var s = table[k];
        var ymd = s.getYear() + '-' + pad2(s.getMonth()) + '-' + pad2(s.getDay());
        if (ymd <= target && ymd > bestYmd) { bestYmd = ymd; bestName = jqName(k); }
      }
    });
    if (!JIEQI[bestName]) return null;
    return { name: bestName, ymd: bestYmd, info: JIEQI[bestName] };
  }
  /* 节气时令 × 命盘喜忌 × 九宫脏腑共振 的饮食合参。
     ⚠️ 硬约束：只用「五行/脏腑」作桥梁，绝不比对两套系统的数字。
     nine = { l1:[九宫一级共振数字], l2:[二级], digitOrgan:{数字→脏腑} } */
  function dietOf(jq, best, avoid, o, favor, bavoid, nine, bazi, region) {
    var info = jq.info, blend;
    if (info.wx === best) {
      blend = '天时与命盘同向（节气属' + info.wx + '、今日亦宜补' + best + '）：' +
        '以节气食材为底盘，按命盘口味略增' + o.taste + '之品即可。';
    } else if (info.wx === avoid) {
      blend = '天时属' + info.wx + '，而命盘今日宜避' + avoid + '：' +
        '顺节气但取清淡做法、减量，勿重补厚味。';
    } else {
      blend = '以节气时令为底盘（重点养' + info.organ + '），' +
        '再以命盘宜补' + best + '的' + o.taste + '之品作日常加减。';
    }
    if (best === '火' && /辛辣|燥热/.test(info.avoid)) {
      blend += ' 节气忌辛辣燥热，火行之品改用温和清补（莲子、百合、红色果蔬），勿以辣椒进补。';
    }
    if (best === '水' && /生冷|寒凉/.test(info.avoid)) {
      blend += ' 节气忌生冷寒凉，肾水之品宜煮熟温食（黑豆、黑芝麻、山药），勿食冰镇。';
    }
    /* 九宫：共振数字 → 脏腑 → 中医五行（与 6.4 同源映射） */
    nine = nine || {};
    var l1 = Array.isArray(nine.l1) ? nine.l1 : (nine.l1 ? String(nine.l1).split('') : []);
    var l2 = Array.isArray(nine.l2) ? nine.l2 : (nine.l2 ? String(nine.l2).split('') : []);
    var digitOrgan = nine.digitOrgan || {};
    var nineRows = [], seen = {}, nineWx = [];
    l1.concat(l2).forEach(function (d) {
      d = String(d);
      var wx = DIGIT_WX[d];
      if (!wx || seen[d]) return;
      seen[d] = 1;
      nineRows.push({ digit: d, organ: digitOrgan[d] || '', wx: wx });
      if (nineWx.indexOf(wx) < 0) nineWx.push(wx);
    });
    var focus = nineWx.slice(0, 2).map(function (w) {
      var f = OPEN[w] ? OPEN[w].food.split('、').slice(0, 3).join('、') : '';
      return w + '：' + f;
    });
    var nineText;
    if (!nineRows.length) {
      nineText = '九宫今日无缺格共振，饮食以节气时令与八字喜忌为准。';
    } else {
      nineText = '九宫今日共振 ' + nineRows.map(function (r) {
        return r.digit + (r.organ ? '（' + r.organ + '）' : '') + '属' + r.wx;
      }).join('、') + '；';
      var inBest = nineWx.filter(function (w) { return w === best; });
      var inSeason = nineWx.filter(function (w) { return w === info.wx; });
      var inAvoid = nineWx.filter(function (w) { return w === avoid; });
      if (inBest.length) nineText += inBest.join('、') + '与八字今日宜补同向，可优先取相应食材；';
      if (inSeason.length) nineText += '与节气同令（' + inSeason.join('、') + '），顺时食材可侧重该脏腑；';
      if (inAvoid.length) nineText += '与八字宜避相悖，相关脏腑只作温和观察、勿重补；';
      if (!inBest.length && !inSeason.length && !inAvoid.length) nineText += '与节气、八字无强交点，各按本系统提示分别调理；';
      nineText += '侧重食材 ' + focus.join('；') + '。';
    }
    var baseBlend = blend;
    return {
      name: jq.name, ymd: jq.ymd, wx: info.wx, organ: info.organ,
      principle: info.pr, food: info.food, avoid: info.avoid, recipe: info.recipe,
      constitution: o.taste + ' · ' + o.food,
      favor: (favor || []).slice(), bavoid: (bavoid || []).slice(),
      baseBlend: baseBlend,
      nineRows: nineRows, nineText: nineText, focus: focus,
      regional: regionText(region, jq.name, best),
      therapy: therapyOf(bazi, best).text,
      weekly: weeklyText(weeklyOf(jq.name, best)),
      blend: blend + ' ' + nineText,
      warning: '两套系统的数字含义不同：九宫数字是脏腑编号，八字数字是河图数理；本建议只以五行/脏腑为桥梁，不比对数字。',
      src: JIEQI_SRC
    };
  }
  /* ═══ 养生中国四栏目（资料源：中国中医药网「养生中国」/《中国中医药报》）═══
     节气养生 → 上方 JIEQI 表；此处补：应地药膳 / 食疗药膳 / 每周药食。
     应地药膳：按中国气候区给地域化食养，依据「应地药膳」系列（如重庆南川猪排品鲜果）
               及广东省中医院关于小满南北地域差异的论述。 */
  var REGIONS = {
    '东北': { climate: '严寒干燥、冬长夏短', pr: '温补藏阳、散寒护胃，忌生冷',
      dish: '当归生姜羊肉汤（温阳祛寒）；山药小米粥（健脾养肺）',
      cities: ['沈阳', '长春', '哈尔滨', '大连'] },
    '华北': { climate: '秋冬干冷、春夏多风', pr: '润燥兼温补，春捂防风',
      dish: '银耳百合雪梨羹（润燥）；姜枣茶（温中散寒）',
      cities: ['北京', '天津', '石家庄', '太原', '济南', '郑州', '青岛'] },
    '西北': { climate: '干寒少雨、昼夜温差大', pr: '温润并重，滋阴不腻',
      dish: '黑芝麻糊（补肾润燥）；莲藕粥（健脾开胃）',
      cities: ['呼和浩特', '西安', '兰州', '西宁', '银川', '乌鲁木齐', '拉萨'] },
    '江南': { climate: '梅雨潮湿、夏热冬湿冷', pr: '健脾祛湿、清淡甘平',
      dish: '芡实薏米粥（健脾祛湿）；薏苡仁冬瓜汤',
      cities: ['上海', '南京', '杭州', '合肥', '苏州', '南昌', '福州', '厦门', '台北'] },
    '华中': { climate: '湿热交错、夏季闷热', pr: '清热化湿、顾护脾胃',
      dish: '苦瓜黄豆排骨汤（清热益气）；赤小豆薏米水（祛湿）',
      cities: ['武汉', '长沙'] },
    '华南': { climate: '长夏湿热、地气蒸腾', pr: '清热化湿、健脾益气，少辛燥',
      dish: '五指毛桃煲汤（健脾祛湿）；苦瓜黄豆排骨汤（清热和胃）',
      cities: ['广州', '深圳', '南宁', '海口', '香港', '澳门'] },
    '西南': { climate: '湿重多雾、寒湿交织', pr: '散寒祛湿、温中健脾',
      dish: '猪排品鲜果（重庆南川，补中益气、健脾开胃、生津润肺）；山药羊肉汤',
      cities: ['重庆', '成都', '贵阳', '昆明'] }
  };
  var REGION_DEFAULT = { climate: '未指定地域', pr: '按节气时令与体质调理，因地制宜可再选城市',
    dish: '山药小米粥（健脾养肺）；银耳百合羹（滋阴润燥）', cities: [] };
  function regionOfCity(city) {
    city = String(city || '').replace(/[市区县省]/g, '').trim();
    if (!city) return '';
    for (var r in REGIONS) if (REGIONS[r].cities.indexOf(city) >= 0) return r;
    return '';
  }
  /* 经纬度 → 最近城市（城市库由页面内嵌 D.CITY 提供，纯本地计算，不联网） */
  function regionOfLatLon(lat, lon, cityTable) {
    cityTable = cityTable || {};
    var best = '', bd = 1e9;
    for (var c in cityTable) {
      var p = cityTable[c];
      if (!p || p.length < 2) continue;
      var d = Math.pow(p[0] - lat, 2) + Math.pow(p[1] - lon, 2);
      if (d < bd) { bd = d; best = c; }
    }
    return bd < 36 ? (regionOfCity(best) || best) : '';   /* 约 6° 以外视为不匹配 */
  }
  function regionText(region, jqName, best) {
    var r = REGIONS[region] || REGION_DEFAULT;
    return '【' + (REGIONS[region] ? region : '全国通用') + '】' + r.climate + '：' + r.pr +
      '。应地药膳：' + r.dish + '。与' + jqName + '合参：以本地气候为底盘，' +
      '叠加' + jqName + '当令食材与命盘宜补' + best + '之品。';
  }
  /* 食疗药膳：四型体质经典方（据《中国中医药报·从餐桌开始筑牢健康根基》） */
  var THERAPY = [
    { key: '气虚', wx: '土', text: '黄芪山药小米粥（黄芪10g、山药20g、小米50g）——补气升阳、健脾养胃，适合乏力易感冒。' },
    { key: '阴虚', wx: '水', text: '百合银耳雪梨汤（百合15g、银耳10g、雪梨1个）——滋阴润燥、清心安神，适合口干皮肤燥。' },
    { key: '痰湿', wx: '火', text: '薏苡仁赤小豆冬瓜汤（薏苡仁20g、赤小豆15g、冬瓜200g、陈皮5g）——利水祛湿，适合身重苔腻。' },
    { key: '肝郁', wx: '木', text: '解郁三花茶（玫瑰花、茉莉花、合欢花）——疏肝解郁，适合情绪郁结、胸闷叹息。' }
  ];
  function therapyOf(bazi, best) {
    var body = String((bazi && bazi.body) || '');
    if (/身弱/.test(body)) return (best === '金' || best === '土') ? THERAPY[0] : THERAPY[1];
    if (best === '木') return THERAPY[3];
    if (best === '土' || best === '火') return THERAPY[2];
    return THERAPY[1];
  }
  /* 每周药食：药食同源食材（据《每周药食》栏目，性味归经据《中国药典》2025版） */
  var WEEKLY = [
    { n: '紫苏', wx: '木', s: '辛温，归肺脾经', f: '解表散寒、行气和胃、解鱼蟹毒',
      r: '紫苏粥：粳米100g、紫苏叶15g、红糖适量', c: '气虚慎用，阴虚内热忌用' },
    { n: '小茴香', wx: '土', s: '辛温，归肝肾脾胃经', f: '散寒止痛、理气和胃',
      r: '茴香姜枣粥：小茴香6g、生姜6g、红枣15g、粳米150g', c: '热证及阴虚火旺者慎用' },
    { n: '益智仁', wx: '水', s: '辛温，归脾肾经', f: '温脾暖肾、固精缩尿',
      r: '益智仁粥：益智仁10g、大米50g、白糖适量', c: '阴虚火旺者忌用' },
    { n: '黄精', wx: '土', s: '甘平，归脾肺肾经', f: '补气养阴、健脾润肺益肾',
      r: '黄精粥/黄精元蹄：黄精配粳米或瘦肉慢炖', c: '脾虚湿滞、咳嗽痰多者慎用' },
    { n: '芡实', wx: '土', s: '甘涩平，归脾肾经', f: '益肾固精、健脾止泻、除湿止带',
      r: '芡实扁豆山药粥：芡实、白扁豆、山药、粳米同煮', c: '便秘、消化不良者不宜多食' },
    { n: '杏仁', wx: '金', s: '苦微温/甘平，归肺大肠经', f: '降气止咳平喘、润肠通便',
      r: '杏仁雪梨羹：杏仁、雪梨、冰糖炖煮', c: '苦杏仁有小毒，须炮制且不宜过量' },
    { n: '山茱萸', wx: '木', s: '酸涩微温，归肝肾经', f: '补益肝肾、收涩固脱',
      r: '山茱萸粥：山茱萸10g、粳米50g', c: '命门火炽、湿热者忌用' },
    { n: '五指毛桃', wx: '土', s: '甘平，归脾肺经', f: '健脾补肺、行气利湿（南方常用）',
      r: '五指毛桃煲汤：配瘦肉/排骨慢炖', c: '孕妇及实热证请咨询医师' },
    { n: '百合', wx: '金', s: '甘寒，归心肺经', f: '养阴润肺、清心安神',
      r: '百合银耳雪梨羹：润肺止咳、清心安神', c: '风寒咳嗽、脾胃虚寒者慎用' },
    { n: '生姜', wx: '火', s: '辛微温，归肺脾胃经', f: '解表散寒、温中止呕',
      r: '桂圆姜枣茶：桂圆5粒、红枣3枚、生姜3片煮10分钟', c: '阴虚内热、热盛者忌用' },
    { n: '黑芝麻', wx: '水', s: '甘平，归肝肾大肠经', f: '补肝肾、益精血、润肠燥',
      r: '枸杞芝麻粥：黑芝麻、枸杞、大米同煮', c: '脾虚便溏者不宜多食' },
    { n: '山药', wx: '土', s: '甘平，归脾肺肾经', f: '补脾养胃、生津益肺、补肾涩精',
      r: '山药小米粥：山药100g、小米50g', c: '湿盛中满、有实邪者慎用' }
  ];
  function weeklyOf(jqName, best) {
    var jq = JIEQI[jqName], wx = jq ? jq.wx : best;
    var hit = WEEKLY.filter(function (x) { return x.wx === best; });
    if (!hit.length) hit = WEEKLY.filter(function (x) { return x.wx === wx; });
    return hit[0] || WEEKLY[11];
  }
  function weeklyText(h) {
    return '【' + h.n + '】' + h.s + '；' + h.f + '。食疗：' + h.r + '。注意：' + h.c + '。';
  }
  /* 取某公历日期的日柱干支（用Solar，不含时辰） */
  function dayGanZhi(dateISO) {
    var m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(String(dateISO || '').trim());
    if (!m) return null;
    var s = G.Solar.fromYmd(+m[1], +m[2], +m[3]);
    var ec = s.getLunar().getEightChar();
    var gz = ec.getDay(), gan = ec.getDayGan(), zhi = ec.getDayZhi();
    return { gz: gz, gan: gan, zhi: zhi, wx: WXG[gan], zhiWx: WXZ[zhi] };
  }
  /* 今日衣食住行开运建议：本命喜用忌神 + 当日干支五行 综合。
     计分（让当日真正左右结论）：
       · 本命喜用各 +3、本命忌神各 −2（长期底色）；
       · 当日日干五行 +2、日支五行 +1.5（若在本命喜用内），落忌神则取负；
       · 当日五行若「生本命喜用」额外 +1（顺势助喜）。
     得分最高为「今日宜补」，最低（且为忌）为「今日宜避」。 */
  function dayAdvice(bazi, dateISO, nine, region) {
    if (!bazi || !bazi.ok) return null;
    var dg = dayGanZhi(dateISO);
    if (!dg) return null;
    var favor = bazi.favor || [], bavoid = bazi.avoid || [];
    var score = initScore();
    favor.forEach(function (wx) { if (wx in score) score[wx] += 3; });
    bavoid.forEach(function (wx) { if (wx in score) score[wx] -= 2; });
    /* 当日日干、日支五行——落喜用加分、落忌神减分 */
    function dayWxScore(wx, weight) {
      if (favor.indexOf(wx) >= 0) score[wx] += weight;
      else if (bavoid.indexOf(wx) >= 0) score[wx] -= weight;
      else score[wx] += 0.5;                       /* 中性五行小幅加，避免全 0 */
      /* 当日五行若生本命喜用，顺势再加 */
      favor.forEach(function (fw) { if (SHENG[wx] === fw) score[wx] += 1; });
    }
    dayWxScore(dg.wx, 2);
    if (dg.zhiWx !== dg.wx) dayWxScore(dg.zhiWx, 1.5);
    var ranked = WUXING.slice().sort(function (a, b) { return score[b] - score[a]; });
    var best = ranked[0], second = ranked[1];
    var avoid = ranked[ranked.length - 1];
    if (bavoid.indexOf(best) >= 0) {               /* 若最高分仍落忌神，降为次选 */
      var alt = ranked.find(function (w) { return bavoid.indexOf(w) < 0; });
      if (alt) { second = best; best = alt; }
    }
    var o = OPEN[best];
    var jq = jieqiOf(dateISO);
    return {
      ok: true, date: dateISO, dayGz: dg.gz, dayWx: dg.wx, dayZhiWx: dg.zhiWx,
      best: best, second: second, avoid: avoid, score: score, open: o,
      favor: favor, bavoid: bavoid, body: bazi.body,
      jieqi: jq ? { name: jq.name, ymd: jq.ymd, wx: jq.info.wx } : null,
      diet: jq ? dietOf(jq, best, avoid, o, favor, bavoid, nine, bazi, region) : null,
      note: '依据：本命四柱喜用（' + favor.join('、') + '）忌神（' + bavoid.join('、') + '，' + bazi.body +
        '）结合当日 ' + dg.gz + '（日干' + dg.wx + '、日支' + dg.zhiWx +
        '）综合；五行开运对照取公开子平共识，仅供传统文化研究参考，不替代专业建议。'
    };
  }

  /* ══════ 双系统五行共鸣（师命 2026-11-21：6.2 共振表 × 6.3 开运建议 关联）══════
     ⚠️ 硬约束：两套系统的「数字」功能不同，绝不直接比对数字！
       · 九宫数字 = 脏腑编号：1肺 2大肠 3心 4肝 5胆 6肾 7胃 8脾 9膀胱 0小肠
       · 八字开运数字 = 河图数理：1/6水 2/7火 3/8木 4/9金 5/0土（仅「吉利数字」建议）
       例如九宫「3」=心(火)，八字「3」=木 —— 直接比对必错。
     桥梁 = 五行/脏腑：九宫共振数字 → 脏腑 → 中医五行，再与八字宜补/宜避五行比对。
       九宫数字→五行依据中医脏腑配属，与 OPEN 表 organ 字段同源：
       肝胆=木、心小肠=火、脾胃=土、肺大肠=金、肾膀胱=水。 */
  var DIGIT_WX = {
    '1': '金', '2': '金', '3': '火', '0': '火',
    '4': '木', '5': '木', '6': '水', '9': '水',
    '7': '土', '8': '土'
  };
  /* l1/l2：6.2 共振表的一级/二级共振数字串；adv：6.3 的 dayAdvice 结果；
     digitOrgan：九宫数字→脏腑映射（ui.js 传 D.DIGIT_ORGAN） */
  function resonance(adv, l1, l2, digitOrgan) {
    if (!adv || !adv.ok) return null;
    /* l1/l2 兼容数组（analyzeYun 实际返回）与字符串两种形态 */
    if (!Array.isArray(l1)) l1 = l1 ? String(l1).split('') : [];
    if (!Array.isArray(l2)) l2 = l2 ? String(l2).split('') : [];
    digitOrgan = digitOrgan || {};
    var best = adv.best, avoid = adv.avoid;
    var favor = adv.favor || [], bavoid = adv.bavoid || [];
    var rows = [], seen = {};
    /* 一级共振优先，二级次之；同一数字可两级都有，分别列出 */
    function add(d, level) {
      var wx = DIGIT_WX[d];
      if (!wx) return;
      var k = d + '@' + level;
      if (seen[k]) return;
      seen[k] = 1;
      var rel, tone, desc;
      if (wx === best) {
        rel = 'sync'; tone = 'good';
        desc = '九宫共振脏腑属' + wx + '，八字今日亦宜补' + wx + ' —— 两套系统同向，重点强化。';
      } else if (wx === avoid) {
        rel = 'clash'; tone = 'warn';
        desc = '九宫共振脏腑属' + wx + '，八字今日却宜避' + wx + ' —— 信号相悖，养护宜温和、勿过补。';
      } else if (favor.indexOf(wx) >= 0) {
        rel = 'favor'; tone = 'mid';
        desc = '九宫共振脏腑属' + wx + '，为命盘长期喜用 —— 长期同向，日常可常养。';
      } else if (bavoid.indexOf(wx) >= 0) {
        rel = 'taboo'; tone = 'warn';
        desc = '九宫共振脏腑属' + wx + '，为命盘长期忌神 —— 今日共振仅作观察，不宜重补。';
      } else {
        rel = 'neutral'; tone = 'plain';
        desc = '九宫共振脏腑属' + wx + '，八字今日无明确喜忌 —— 各按本系统建议即可。';
      }
      rows.push({ digit: d, wx: wx, level: level, organ: digitOrgan[d] || '',
        rel: rel, tone: tone, desc: desc, open: OPEN[wx] });
    }
    var i;
    for (i = 0; i < l1.length; i++) add(String(l1[i]), 1);
    for (i = 0; i < l2.length; i++) add(String(l2[i]), 2);
    /* 排序：同频 > 相悖 > 喜用 > 忌神 > 中性；同级一级优先 */
    var rank = { sync: 0, clash: 1, favor: 2, taboo: 3, neutral: 4 };
    rows.sort(function (a, b) { return (rank[a.rel] - rank[b.rel]) || (a.level - b.level); });
    var nSync = rows.filter(function (x) { return x.rel === 'sync'; }).length;
    var nClash = rows.filter(function (x) { return x.rel === 'clash'; }).length;
    function wxList(rel) {
      var out = [];
      rows.filter(function (x) { return x.rel === rel; }).forEach(function (x) {
        if (out.indexOf(x.wx) < 0) out.push(x.wx);
      });
      return out.join('、');
    }
    var summary;
    if (!rows.length) {
      summary = '今日 6.2 无缺格共振，两套系统无五行交点；各按本系统建议执行即可。';
    } else if (nSync && !nClash) {
      summary = '两套系统在 ' + wxList('sync') + ' 上同频共振，可把 6.3 的颜色/饮食/养护 与 6.2 共振脏腑调理合一施行。';
    } else if (nClash && !nSync) {
      summary = '两套系统在 ' + wxList('clash') + ' 上信号相悖：九宫提示共振、八字建议回避，宜以八字宜补五行为主、共振脏腑温和观察。';
    } else if (nSync && nClash) {
      summary = '两套系统部分同频、部分相悖：' + wxList('sync') + ' 可强化，' + wxList('clash') + ' 宜回避，分而处之。';
    } else {
      summary = '今日两套系统各有指向、无强交点；按各自建议分别执行。';
    }
    return { ok: true, best: best, avoid: avoid, favor: favor, bavoid: bavoid,
      rows: rows, nSync: nSync, nClash: nClash, summary: summary };
  }

  G.BAZI = { analyze: analyze, dayGanZhi: dayGanZhi, dayAdvice: dayAdvice, resonance: resonance,
    jieqiOf: jieqiOf, dietOf: dietOf, JIEQI: JIEQI,
    REGIONS: REGIONS, regionOfCity: regionOfCity, regionOfLatLon: regionOfLatLon,
    DIGIT_WX: DIGIT_WX, WUXING: WUXING, SHENG: SHENG, KE: KE, OPEN: OPEN };
})(window);
