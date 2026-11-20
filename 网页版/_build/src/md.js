/* ============================================================
 * 极简 Markdown 渲染器
 * 覆盖三份报告用到的语法：# ## ### / 表格 / 无序·有序列表 / 引用 / 分隔线 /
 * **粗体** / `行内代码` / :warning:
 * ============================================================ */
(function (root) {
  'use strict';

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function inline(s) {
    var t = esc(s);
    t = t.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    t = t.replace(/`([^`]+)`/g, '<code>$1</code>');
    t = t.replace(/:warning:/g, '⚠️');
    return t;
  }

  function splitRow(line) {
    var s = line.trim();
    if (s.charAt(0) === '|') s = s.slice(1);
    if (s.charAt(s.length - 1) === '|') s = s.slice(0, -1);
    return s.split('|').map(function (c) { return c.trim(); });
  }

  function isSep(line) {
    return /^\s*\|?[\s:\-|]+\|?\s*$/.test(line) && line.indexOf('-') >= 0;
  }

  function render(md) {
    var lines = String(md).split('\n');
    var out = [];
    var i = 0;
    var para = [];
    var listType = null;

    function flushPara() {
      if (para.length) { out.push('<p>' + para.map(inline).join('') + '</p>'); para = []; }
    }
    function closeList() {
      if (listType) { out.push('</' + listType + '>'); listType = null; }
    }
    function flushAll() { flushPara(); closeList(); }

    while (i < lines.length) {
      var ln = lines[i];

      /* 空行 */
      if (/^\s*$/.test(ln)) { flushAll(); i++; continue; }

      /* 分隔线 */
      if (/^\s*(-{3,}|\*{3,})\s*$/.test(ln)) { flushAll(); out.push('<hr>'); i++; continue; }

      /* 标题 */
      var mh = /^\s*(#{1,6})\s+(.*)$/.exec(ln);
      if (mh) {
        flushAll();
        var lv = Math.min(mh[1].length, 4);
        out.push('<h' + lv + '>' + inline(mh[2]) + '</h' + lv + '>');
        i++; continue;
      }

      /* 表格 */
      if (/^\s*\|/.test(ln) && i + 1 < lines.length && isSep(lines[i + 1])) {
        flushAll();
        var head = splitRow(ln);
        var j = i + 2, body = [];
        while (j < lines.length && /^\s*\|/.test(lines[j])) { body.push(splitRow(lines[j])); j++; }
        var html = '<div class="tw"><table><thead><tr>';
        head.forEach(function (c) { html += '<th>' + inline(c) + '</th>'; });
        html += '</tr></thead><tbody>';
        body.forEach(function (r) {
          html += '<tr>';
          for (var k = 0; k < head.length; k++) html += '<td>' + inline(r[k] == null ? '' : r[k]) + '</td>';
          html += '</tr>';
        });
        html += '</tbody></table></div>';
        out.push(html);
        i = j; continue;
      }

      /* 引用（连续 > 行合并；引用内空行 → 分段） */
      if (/^\s*>\s?/.test(ln)) {
        flushAll();
        var q = [];
        while (i < lines.length && /^\s*>\s?/.test(lines[i])) {
          q.push(lines[i].replace(/^\s*>\s?/, ''));
          i++;
        }
        var paras = [], cur = [];
        q.forEach(function (t) {
          if (/^\s*$/.test(t)) { if (cur.length) { paras.push(cur.join('')); cur = []; } }
          else cur.push(t);
        });
        if (cur.length) paras.push(cur.join(''));
        out.push('<blockquote>' + paras.map(function (p) { return '<p>' + inline(p) + '</p>'; }).join('') + '</blockquote>');
        continue;
      }

      /* 无序列表 */
      var mu = /^(\s*)-\s+(.*)$/.exec(ln);
      if (mu) {
        flushPara();
        if (listType !== 'ul') { closeList(); out.push('<ul>'); listType = 'ul'; }
        var nested = mu[1].length >= 2;
        out.push('<li' + (nested ? ' class="nested"' : '') + '>' + inline(mu[2]) + '</li>');
        i++; continue;
      }

      /* 有序列表 */
      var mo = /^(\s*)\d+\.\s+(.*)$/.exec(ln);
      if (mo) {
        flushPara();
        if (listType !== 'ol') { closeList(); out.push('<ol>'); listType = 'ol'; }
        out.push('<li>' + inline(mo[2]) + '</li>');
        i++; continue;
      }

      /* 普通段落 */
      closeList();
      para.push(ln.trim());
      i++;
    }
    flushAll();
    return out.join('\n');
  }

  root.MD = { render: render, esc: esc, inline: inline };
})(typeof window !== 'undefined' ? window : globalThis);
