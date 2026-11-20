# -*- coding: utf-8 -*-
"""第二轮：加入「原书口径」(book) 作为默认。

第一轮只把默认从 v5 换成 query，但校验暴露了更深的问题：
  · 核心引擎 v5：前子时 −1、后子时 +1        ⟹ 两个分支都反
  · 查询工具   ：前子时 +1、后子时 正好不换日  ⟹ 只对了前子时，后子时退化（两套格变成同一套）
  · 原书要求   ：前子时 +1、后子时 −1        ⟹ 两套格必然不同

原书依据：
  《九宫解译历史人物》1-6「子时的人」——前子时「在出生日期上面去额外的加一天」，
      后子时「在出生日期上面去减一天」
  《九宫格相关内容汇总》一、算法——「第二套前子时加一天计算，后子时减一天计算」

故新增 book 口径为默认；v5 / query 仍可切换，仅供复现历史输出。
"""
import sys

DRY = '--dry' in sys.argv
edits = []

# ══════════ engine.js ══════════
edits.append((
    'src/engine.js',
    "   * @param {string} zishiRule 'query'（前子时→+1 天，与卢先生原书一致）\n"
    "   *                            | 'v5'（前子时→−1 天，核心引擎，仅供对齐历史 .md）\n"
    "   *   依据《九宫解译历史人物》1-6「子时的人」：前子时加一天算另一套、后子时减一天算另一套。",
    "   * @param {string} zishiRule\n"
    "   *   'book'  前子时 +1 天 / 后子时 −1 天 —— 与卢先生原书一致（本页默认）\n"
    "   *   'v5'    前子时 −1 天 / 后子时 +1 天 —— 核心引擎 v5，两个分支都反，仅供对齐历史 .md\n"
    "   *   'query' 前子时 +1 天 / 后子时  0 天 —— 查询工具原样，后子时不换日（两套格退化相同）\n"
    "   *   依据《九宫解译历史人物》1-6「子时的人」：前子时加一天算另一套、后子时减一天算另一套。",
    'engine 注释'))

edits.append((
    'src/engine.js',
    "    /* 缺省用与原书一致的口径。'v5' 是反向的，只有三个 .md 报告生成器为了\n"
    "       与 完整综合命理报告v3.9.py 逐字节一致才显式传它。 */\n"
    "    var rule = zishiRule || 'query';",
    "    /* 缺省用原书口径。'v5' 两个分支都反，只有三个 .md 报告生成器为了与\n"
    "       完整综合命理报告v3.9.py 逐字节一致才显式传它。 */\n"
    "    var rule = zishiRule || 'book';",
    'engine 缺省值'))

edits.append((
    'src/engine.js',
    "      var adj = addDays(dt, rule === 'v5' ? (isQian ? -1 : 1) : (isQian ? 1 : 0));",
    "      /* 三套口径的位移表，见上方注释。'book' 是唯一让两套格必然不同的那个。 */\n"
    "      var shift = rule === 'v5' ? (isQian ? -1 : 1)\n"
    "                : rule === 'query' ? (isQian ? 1 : 0)\n"
    "                : (isQian ? 1 : -1);\n"
    "      var adj = addDays(dt, shift);",
    'engine 位移公式'))

edits.append((
    'src/engine.js',
    "      if (rule === 'v5') {\n"
    "        res.note = isQian ? '前子时实际属于前一天(' + adjStr + ')' : '后子时属于后一天(' + adjStr + ')';\n"
    "      } else {\n"
    "        res.note = isQian ? '前子时：实际属于下一天(' + adjStr + ')' : '后子时：属于当天(' + adjStr + ')';\n"
    "      }",
    "      if (rule === 'v5') {\n"
    "        res.note = isQian ? '前子时实际属于前一天(' + adjStr + ')' : '后子时属于后一天(' + adjStr + ')';\n"
    "      } else if (rule === 'query') {\n"
    "        res.note = isQian ? '前子时：另一套取后一天(' + adjStr + ')' : '后子时：查询工具不换日，与当天格相同';\n"
    "      } else {\n"
    "        res.note = isQian ? '前子时：另一套取后一天(' + adjStr + ')' : '后子时：另一套取前一天(' + adjStr + ')';\n"
    "      }",
    'engine 文案'))

# ══════════ reports.js：缺省同步为 book ══════════
# #1 是 comprehensive 里带注释的那行（唯一）；后两处 ni / shiliao 是同一句裸行（共 2 次）
edits.append(('src/reports.js',
    "    var RULE = o.rule || 'query';   /* 缺省与原书一致；校验脚本显式传 'v5' 复现 Python 基线 */",
    "    var RULE = o.rule || 'book';   /* 缺省与原书一致；校验脚本显式传 'v5' 复现 Python 基线 */",
    'reports 缺省 book（comprehensive）'))
edits.append(('src/reports.js',
    "    var RULE = o.rule || 'query';\n",
    "    var RULE = o.rule || 'book';\n",
    'reports 缺省 book（ni+shiliao）', 2))

# ══════════ body.html：三选项，book 默认 ══════════
edits.append((
    'src/body.html',
    '          <option value="query" selected>查询工具：前子时→后一天（符合原书）</option>\n'
    '          <option value="v5">核心引擎 v5：前子时→前一天（与原书相反）</option>',
    '          <option value="book" selected>原书口径：前子时→后一天 / 后子时→前一天</option>\n'
    '          <option value="query">查询工具原样：前子时→后一天 / 后子时不换日</option>\n'
    '          <option value="v5">核心引擎 v5：前子时→前一天 / 后子时→后一天</option>',
    'body 三选项'))

# ══════════ ui.js ══════════
edits.append((
    'src/ui.js',
    "      $('fRule').value = 'query';",
    "      $('fRule').value = 'book';",
    'ui 示例重置'))

edits.append((
    'src/ui.js',
    "        ' · 规则：' + (r.rule === 'v5' ? '核心引擎 v5（与原书相反）' : '查询工具（符合原书）');",
    "        ' · 规则：' + ruleName(r.rule);",
    'ui 规则名调用'))

edits.append((
    'src/ui.js',
    "  /* 分位描述：两端各给一句话",
    "  function ruleName(k) {\n"
    "    if (k === 'v5') return '核心引擎 v5（两个分支都与原书相反）';\n"
    "    if (k === 'query') return '查询工具原样（后子时不换日）';\n"
    "    return '原书口径（前子时 +1 / 后子时 −1）';\n"
    "  }\n\n"
    "  /* 分位描述：两端各给一句话",
    'ui 新增 ruleName'))

# ══════════ verify_zishi.js：改写为三口径全测 ══════════
old_v = open('verify_zishi.js', 'rb').read().decode('utf-8')
new_v = old_v
# ① 原书例改成 book
new_v = new_v.replace("const pdfCase = M.calc('1990/05/08', '前子时', 'male', 'query');",
                      "const pdfCase = M.calc('1990/05/08', '前子时', 'male', 'book');")
# ② 方向律：改成三种口径各自的位移表
new_v = new_v.replace("""let nDir = 0;
for (let off = 0; off < 400; off++) {
  const d = new Date(1990, 0, 1 + off);
  const cur = slash(d);
  [['前子时', +1], ['后子时', -1]].forEach(function (pair) {
    const sc = pair[0], sign = pair[1];
    const adj = new Date(d.getFullYear(), d.getMonth(), d.getDate() + sign);
    const r = M.calc(cur, sc, 'male', 'query');
    const direct = M.calc(slash(adj), '巳时', 'male', 'query');
    check('方向律 ' + cur + ' ' + sc,
      r.yang1 === direct.yang && r.yin1 === direct.yin,
      '调整格 ' + r.yang1 + '/' + r.yin1 + ' ≠ ' + slash(adj) + ' 的 ' + direct.yang + '/' + direct.yin);
    nDir++;
  });
}""",
"""let nDir = 0;
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
}""")
# ③ 删掉原来单独的 ③ v5 段（已并入 ② 的 SHIFT 表）
import re
new_v = re.sub(r"/\* ── ③ v5 必须正好相反.*?nV5\+\+;\n  \}\);\n\}\n", "", new_v, flags=re.S)
new_v = new_v.replace("console.log('方向律对拍 ' + nDir + ' 组 · v5 对照 ' + nV5 + ' 组');",
                      "console.log('三口径位移对拍 ' + nDir + ' 组');")
# ④ 缺省口径断言改 book
new_v = new_v.replace("check('缺省口径', dflt.rule === 'query', '缺省 rule 应为 query，实际 ' + dflt.rule);",
                      "check('缺省口径', dflt.rule === 'book', '缺省 rule 应为 book，实际 ' + dflt.rule);")
# ⑤ 报告断言改成 book vs v5
new_v = new_v.replace("""  const mdQ = c[1](Object.assign({}, base, { rule: 'query' }));
  const mdV = c[1](Object.assign({}, base, { rule: 'v5' }));
  check('报告 ' + c[0] + ' query 含 09336', mdQ.indexOf('09336') >= 0,
    '这一份在 query 口径下没出现 09336 ⟹ rule 没透传进去');
  check('报告 ' + c[0] + ' query 不含 0314', mdQ.indexOf('0314') < 0,
    '出现了 v5 的 0314 ⟹ rule 混用');""",
"""  const mdQ = c[1](Object.assign({}, base, { rule: 'book' }));
  const mdV = c[1](Object.assign({}, base, { rule: 'v5' }));
  check('报告 ' + c[0] + ' book 含 09336', mdQ.indexOf('09336') >= 0,
    '这一份在 book 口径下没出现 09336 ⟹ rule 没透传进去');
  check('报告 ' + c[0] + ' book 不含 0314', mdQ.indexOf('0314') < 0,
    '出现了 v5 的 0314 ⟹ rule 混用');""")
new_v = new_v.replace("const b = M.calc('2012/12/21', '巳时', 'male', 'v5');",
                      "const b = M.calc('2012/12/21', '巳时', 'male', 'v5');")
edits.append(('verify_zishi.js', old_v, new_v, 'verify_zishi 改三口径'))

# ══════════ 执行 ══════════
by_file = {}
for e in edits:
    path, old, new, note = e[0], e[1], e[2], e[3]
    expect = e[4] if len(e) > 4 else 1
    by_file.setdefault(path, []).append((old, new, note, expect))

fails = []
for path, items in by_file.items():
    s = open(path, 'rb').read().decode('utf-8')
    orig = s
    for old, new, note, expect in items:
        n = s.count(old)
        if n == expect:
            s = s.replace(old, new)
            print('  [改] %-18s %s' % (path, note))
        elif s.count(new) > 0 and n == 0:
            print('  [跳] %-18s %s（已是目标态）' % (path, note))
        else:
            fails.append('%s / %s：锚点 %d 次' % (path, note, n))
            print('  [!!] %-18s %s：锚点 %d 次' % (path, note, n))
    if s != orig and not DRY:
        open(path, 'wb').write(s.encode('utf-8'))
    if s != orig:
        print('  → %s %d → %d' % (path, len(orig), len(s)))

if fails:
    print('\n有 %d 处失败：' % len(fails))
    for f in fails:
        print('   -', f)
    sys.exit(1)
print('\n全部通过' + ('（dry）' if DRY else '，已写盘'))
