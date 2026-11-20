# -*- coding: utf-8 -*-
"""按卢先生原书口径纠正子时换日规则。

结论（三份资料一致）：
  前子时 → 日期 +1 天；后子时 → 日期 −1 天
  《九宫解译历史人物》第一章第 6 节「子时的人」
  《九宫格相关内容汇总》一、算法
  《道医九宫格说明书》二、特殊场景规则

核心引擎 v5 的两个分支方向都反了（前→−1、后→+1），
与它对齐的 .md 报告必须保留该口径，因此 v5 仍可切换，但不再是默认。
"""
import sys

DRY = '--dry' in sys.argv
edits = []          # (path, old, new, note)

# ══════════ 1. engine.js：缺省口径改为 query，注释写明依据 ══════════
edits.append((
    'src/engine.js',
    "   * @param {string} zishiRule 'v5'（前子时→前一天，核心引擎）| 'query'（前子时→后一天，查询工具）",
    "   * @param {string} zishiRule 'query'（前子时→+1 天，与卢先生原书一致）\n"
    "   *                            | 'v5'（前子时→−1 天，核心引擎，仅供对齐历史 .md）\n"
    "   *   依据《九宫解译历史人物》1-6「子时的人」：前子时加一天算另一套、后子时减一天算另一套。",
    'engine 注释'))

edits.append((
    'src/engine.js',
    "    var rule = zishiRule || 'v5';",
    "    /* 缺省用与原书一致的口径。'v5' 是反向的，只有三个 .md 报告生成器为了\n"
    "       与 完整综合命理报告v3.9.py 逐字节一致才显式传它。 */\n"
    "    var rule = zishiRule || 'query';",
    'engine 缺省值'))

# ══════════ 2. reports.js：把 rule 透传进 7 个 M.calc ══════════
# 2a. comprehensive
edits.append((
    'src/reports.js',
    "    var targetDate = o.targetDate || ds2(now);\n\n    var r = M.calc(birth, birthTime, gender);",
    "    var targetDate = o.targetDate || ds2(now);\n"
    "    var RULE = o.rule || 'query';   /* 缺省与原书一致；校验脚本显式传 'v5' 复现 Python 基线 */\n\n"
    "    var r = M.calc(birth, birthTime, gender, RULE);",
    'reports comprehensive 主格'))

edits.append((
    'src/reports.js',
    "var dayR = M.calc(targetDate, nowShichen, gender);",
    "var dayR = M.calc(targetDate, nowShichen, gender, RULE);",
    'reports comprehensive 行运'))

# 2b. ni
edits.append((
    'src/reports.js',
    "    var genderText = g === 'male' ? '男' : '女';\n\n    var r = M.calc(birth, birthTime, g);",
    "    var genderText = g === 'male' ? '男' : '女';\n"
    "    var RULE = o.rule || 'query';\n\n"
    "    var r = M.calc(birth, birthTime, g, RULE);",
    'reports ni 主格'))

edits.append((
    'src/reports.js',
    "var rNow = M.calc(ds2(now), nowShichen, g);",
    "var rNow = M.calc(ds2(now), nowShichen, g, RULE);",
    'reports ni 今日'))

# 2c. shiliao
edits.append((
    'src/reports.js',
    "    var nowRange = M.shichenRange(nowShichen);\n\n    var jgg = M.calc(birth, shichen, gender);",
    "    var nowRange = M.shichenRange(nowShichen);\n"
    "    var RULE = o.rule || 'query';\n\n"
    "    var jgg = M.calc(birth, shichen, gender, RULE);",
    'reports shiliao 主格'))

edits.append((
    'src/reports.js',
    "    var dayAllR = M.calc(todayStr, shichen, gender);\n    var dayNowR = M.calc(todayStr, nowShichen, gender);",
    "    var dayAllR = M.calc(todayStr, shichen, gender, RULE);\n"
    "    var dayNowR = M.calc(todayStr, nowShichen, gender, RULE);",
    'reports shiliao 今日两只'))

# ══════════ 3. body.html：选项换序 + 标注 ══════════
edits.append((
    'src/body.html',
    '          <option value="v5" selected>核心引擎 v5：前子时→前一天</option>\n'
    '          <option value="query">查询工具：前子时→后一天</option>',
    '          <option value="query" selected>查询工具：前子时→后一天（符合原书）</option>\n'
    '          <option value="v5">核心引擎 v5：前子时→前一天（与原书相反）</option>',
    'body 下拉选项'))

# ══════════ 4. ui.js ══════════
# 4a. 示例按钮重置
edits.append((
    'src/ui.js',
    "      $('fRule').value = 'v5';",
    "      $('fRule').value = 'query';",
    'ui 示例重置'))

# 4b. 子时卡片上的规则名
edits.append((
    'src/ui.js',
    "        ' · 规则：' + (r.rule === 'v5' ? '核心引擎 v5' : '查询工具');",
    "        ' · 规则：' + (r.rule === 'v5' ? '核心引擎 v5（与原书相反）' : '查询工具（符合原书）');",
    'ui 子时规则名'))

# 4c. 报告透传 rule
edits.append((
    'src/ui.js',
    "      gender: f.gender, location: f.city || null, now: new Date(), targetDate: null\n    });",
    "      gender: f.gender, location: f.city || null, now: new Date(), targetDate: null,\n"
    "      rule: f.rule\n    });",
    'ui 报告透传 rule'))

# 4d. 10.3 第 ② 条改写为定论
old2 = ("      '<div class=\"note warn\"><b>② 子时换日，两套实现互相矛盾</b><br>' +\n"
        "      '核心引擎 v5 是「前子时 → 前一天」，查询工具 <code>adjust_date_for_zishi</code> 是「前子时 → 后一天」。' +\n"
        "      '同一份 <code>前子时</code> 输入，两者给出的调整格是<b>相邻的两天</b>。本页做成可选项，默认跟 v5（三份报告都用它）。</div>' +")
new2 = ("      '<div class=\"note warn\"><b>② 子时换日：两套实现方向相反，已按原书定为「前子时→后一天」</b><br>' +\n"
        "      '核心引擎 v5 取 <code>前子时 = 日期−1</code>、<code>后子时 = 日期+1</code>；' +\n"
        "      '查询工具 <code>adjust_date_for_zishi</code> 取 <code>前子时 = 日期+1</code>。同一份 <code>前子时</code> 输入，' +\n"
        "      '两者给出的调整格是<b>相邻的两天</b>。<br>' +\n"
        "      '<b>《九宫解译历史人物》第一章第 6 节「子时的人」原文</b>：「如果是前子时的师兄，他想要计算出后子时的那套系统，' +\n"
        "      '他就需要在自己的出生日期上面，去额外的加一天，比如说你是，阳历 1990 年 5 月 8 号，前子时出生的师兄……' +\n"
        "      '后子时就是 1990 年 5 月 9 号」「如果你是后子时出生的，那么想要去计算出前子时的格，就在出生日期上面去减一天」。<br>' +\n"
        "      '<b>《九宫格相关内容汇总》一、算法</b>：「子时有两套系统：第二套前子时加一天计算，后子时减一天计算。」<br>' +\n"
        "      '<b>《道医九宫格说明书》二、特殊场景规则</b>：「前子时（23:00-0:00）：日期加 1 天计算（如 6 月 1 日 23:30 → 按 6 月 2 日计算）」。<br>' +\n"
        "      '三份资料一致 ⟹ <b>前子时 +1 天、后子时 −1 天为正确，v5 两个分支都反了</b>。' +\n"
        "      '本页因此默认改用查询工具口径，三份报告也随之同步；v5 口径仍可切换，仅供复现历史 <code>.md</code>。</div>' +")
edits.append(('src/ui.js', old2, new2, 'ui 10.3 第②条'))

# ══════════ 5. verify_reports.js：显式声明用 v5 复现 Python 基线 ══════════
edits.append((
    'verify_reports.js',
    "    location: c.location, now: NOW, targetDate: '2026/10/27'",
    "    location: c.location, now: NOW, targetDate: '2026/10/27',\n"
    "    /* 显式传 v5：Python 侧的 完整综合命理报告v3.9.py 走 core_v5 口径，\n"
    "       这里要复现的就是那份历史基线，不是本页的新默认值。 */\n"
    "    rule: 'v5'",
    'verify_reports 显式 v5'))

# ══════════ 执行（带幂等闸门） ══════════
by_file = {}
for path, old, new, note in edits:
    by_file.setdefault(path, []).append((old, new, note))

fails = []
for path, items in by_file.items():
    s = open(path, 'rb').read().decode('utf-8')
    orig = s
    for old, new, note in items:
        n = s.count(old)
        already = s.count(new) > 0 and n == 0
        if n == 1:
            s = s.replace(old, new)
            print('  [改] %-18s %s' % (path, note))
        elif already:
            print('  [跳] %-18s %s（已是目标态）' % (path, note))
        else:
            fails.append('%s / %s：锚点出现 %d 次' % (path, note, n))
            print('  [!!] %-18s %s：锚点出现 %d 次' % (path, note, n))
    if s != orig and not DRY:
        open(path, 'wb').write(s.encode('utf-8'))
    if s != orig:
        print('  → %s 体积 %d → %d' % (path, len(orig), len(s)))

if fails:
    print('\n有 %d 处失败，未写盘的按未改处理：' % len(fails))
    for f in fails:
        print('   -', f)
    sys.exit(1)
print('\n全部锚点通过' + ('（dry，未写盘）' if DRY else '，已写盘'))
