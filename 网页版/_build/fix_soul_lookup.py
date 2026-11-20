# -*- coding: utf-8 -*-
"""修灵魂库查表：前缀/前三位兜底不再给星级与名称，只作「疑似同族」提示。

起因（2026-10-27 实测 605 种真实阳格 / 70127 天）：
  SOUL_SCORE_DB 的 lookupSoulScore 照抄了 Python 的 startswith 兜底
      pref 28 种 + pre3 145 种 = 173 种 / 4946 天 = 7.05% 的天数被张冠李戴
      例：02167 / 02145 / 02134 / 02189 / 02178 / 02123 / 02112 → 全被判成 0219101
          1246(759天) → 12433101「新维度播种玉皇」★★★★☆
  SOUL_DB 的 lookupSoulV5 同病：pref 23 + pre3 136 = 159 种 / 3368 天 = 4.80%

改法：返回结构加 conf
  exact      原书精确命中      —— 唯一可直接当结论
  same-root  剥前导零后命中    —— 推定（先天/后天同源），UI 必须标注
  near       rec=null          —— 只回 near 供提示，不出星级/名称
  null       未收录

用法：python fix_soul_lookup.py [--dry]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'src')

# ────────────────────────── engine.js ──────────────────────────
ENG_NEW = '''  /** 查灵魂积分。三档置信度（2026-10-27 修：前缀兜底不再给结论）
   *   conf='exact'      原库精确命中 —— 唯一可当原书结论用的
   *   conf='same-root'  剥前导零后命中（先天形态 / 后天落形态同源，如 0213 ↔ 213），推定
   *   conf='near'       rec=null，只回 near 供「疑似同族」提示，不出星级与名称
   *   null              未收录
   * 起因：原实现照抄 Python 的 startswith 兜底，在 605 种真实阳格上把 7.05% 的天数
   * 张冠李戴（02167/02145/02134/02189 全被判成 0219101；1246 被判成 12433101）。 */
  function lookupSoulScore(grid, DB) {
    var g = String(grid);
    if (DB[g]) return { key: g, rec: DB[g], conf: 'exact' };
    var stripped = /^\\d+$/.test(g) ? String(parseInt(g, 10)) : g.replace(/^0+/, '');
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

'''

# ────────────────────── ui.js 主卡片（灵魂积分） ──────────────────────
UI1_NEW = '''    /* 灵魂积分（精确 / 剥零推定 / 未收录 三态，不再按前缀猜身份） */
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
'''

# ────────────────────── ui.js 稀有度页「库命中」 ──────────────────────
UI2_NEW = '''    /* 3. 库命中（有则报，无则说明为什么无；前缀相似不再当命中） */
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
'''

# ────────────────────── reports.js ──────────────────────
REP_OLD = "    if (sv) { soulN = sv.rec.n || ''; soulT = sv.rec.t || ''; }"
REP_NEW = "    if (sv && sv.rec) { soulN = sv.rec.n || ''; soulT = sv.rec.t || ''; }"


def patch(path, edits, dry):
    """edits: [(start_anchor, end_anchor_or_None, new_text, new_marker, mode)]
    mode='span' 用 start/end 切片替换 [start,end) ；mode='line' 精确替换锚点本身"""
    b = open(path, 'rb').read()
    s = b.decode('utf-8')
    orig = s
    for start, end, new, marker, mode in edits:
        if s.count(marker) > 0:
            print('  跳过（新标记已存在）：%r' % marker[:40])
            continue
        ns = s.count(start)
        assert ns == 1, '起始锚点出现 %d 次：%r' % (ns, start[:50])
        i = s.index(start)
        if mode == 'line':
            s = s[:i] + new + s[i + len(start):]
        else:
            ne = s.count(end)
            assert ne == 1, '结束锚点出现 %d 次：%r' % (ne, end[:50])
            j = s.index(end)
            assert j > i, '结束锚点位置异常'
            s = s[:i] + new + s[j:]
    nb = s.encode('utf-8')
    print('  %s：%d -> %d 字节（%+d）' % (os.path.basename(path), len(b), len(nb), len(nb) - len(b)))
    assert nb.count(b'\r') == 0, '出现 CR，行尾被破坏'
    if dry:
        print('  [dry] 未写盘')
        return
    with open(path, 'r+b') as f:
        f.seek(0)
        f.write(nb)
        f.truncate()


def main():
    dry = '--dry' in sys.argv
    print('=== 1/3 engine.js ===')
    patch(os.path.join(SRC, 'engine.js'), [
        ('  /** 查询工具 nine_palace_query.lookup_soul_score（精确 → 去零 → 前缀） */',
         '  /* ---------- 组合 / 单格解读 ---------- */',
         ENG_NEW, "conf: 'near'", 'span'),
    ], dry)

    print('=== 2/3 ui.js ===')
    patch(os.path.join(SRC, 'ui.js'), [
        ("    /* 灵魂积分 */",
         "    $('q-soul').innerHTML = soulHtml;",
         UI1_NEW, "conf === 'same-root'", 'span'),
        ("    /* 3. 库命中（有则报，无则说明为什么无） */",
         "    out += '</div>';\n    return out;\n  }",
         UI2_NEW, '不做前缀猜测', 'span'),
    ], dry)

    print('=== 3/3 reports.js ===')
    patch(os.path.join(SRC, 'reports.js'), [
        (REP_OLD, None, REP_NEW, 'if (sv && sv.rec) { soulN', 'line'),
    ], dry)


if __name__ == '__main__':
    main()
