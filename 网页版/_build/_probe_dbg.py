# -*- coding: utf-8 -*-
"""真机探针：灵魂库三态（exact / same-root / near）在页面上的实际显示。

断言（这是本次修复的核心，必须逐条实测，不能只看引擎层）：
  near       · #q-soul 不得出现任何 ★（不再给星级）
             · 必须出现「未收录」与「不是这个阳格的身份」
  same-root  · 必须出现「推定」
             · 必须指向剥零后的 key（0213 → 213）
  exact      · 必须出现星级与名称
  稀有度页   · near 格必须显示「未收录，不做前缀猜测」，且整块不含 ★
"""
import json, os, subprocess, sys, tempfile, html as H

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, '..', '慈海九宫格_即时解读.html')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

CASES = [
    ('1980-01-14', 'near',      '1246'),
    ('2001-09-22', 'near',      '02167'),
    ('1980-01-02', 'same-root', '0213'),
    ('2000-01-09', 'exact',     '0123'),
    ('1980-02-19', 'exact',     '303'),
]

PROBE = r"""
<script>
window.addEventListener('load', function(){
  var CASES = __CASES__;
  var out = { rows: [] };
  var idx = 0;
  function step() {
    if (idx >= CASES.length) {
      /* 稀有度页：用 near 格验一次 */
      try {
        var tab = document.querySelector('[data-tab="9"]') || document.getElementById('tabbtn-9');
        if (tab) tab.click();
        var box = document.getElementById('stSearch');
        box.value = '1246';
        box.dispatchEvent(new Event('input', { bubbles: true }));
        setTimeout(function () {
          var e = document.getElementById('st-detail');
          var tx = e ? (e.textContent || '').replace(/\s+/g, ' ') : '';
          out.rar_has_star = tx.indexOf('★') >= 0;
          out.rar_has_note = tx.indexOf('不做前缀猜测') >= 0;
          out.rar_has_12433101 = tx.indexOf('12433101') >= 0;
          out.rar_tail = tx.slice(-160);
          document.body.setAttribute('data-soul', JSON.stringify(out));
        }, 400);
      } catch (e2) {
        out.rar_err = e2.message;
        document.body.setAttribute('data-soul', JSON.stringify(out));
      }
      return;
    }
    var c = CASES[idx];
    document.getElementById('fBirth').value = c[0];
    document.getElementById('fShichen').value = '午时';
    document.getElementById('fGender').value = 'male';
    document.getElementById('btnRun').click();
    setTimeout(function () {
      var e = document.getElementById('q-soul');
      var tx = e ? (e.textContent || '').replace(/\s+/g, ' ') : '(缺 q-soul)';
      out.rows.push({
        date: c[0], want: c[1], grid: c[2],
        stars: (tx.match(/★/g) || []).length,
        has_uncol: tx.indexOf('未收录') >= 0,
        has_identity: tx.indexOf('不是这个阳格的身份') >= 0,
        has_tui: tx.indexOf('推定') >= 0,
        has_213: tx.indexOf('213') >= 0,
        near_key: (tx.match(/条目有\s*(\w+)/) || [])[1] || '',
        text: tx.slice(0, 240)
      });
      idx++;
      step();
    }, 420);
  }
  step();
});
</script>
"""


def run(w):
    src = open(PAGE, 'rb').read().decode('utf-8')
    probe = PROBE.replace('__CASES__', json.dumps(CASES, ensure_ascii=False))
    patched = src.replace('</body>', probe + '</body>')
    fd, tmp = tempfile.mkstemp(suffix='.html', dir=os.environ.get('TEMP', None))
    os.close(fd)
    with open(tmp, 'wb') as f:
        f.write(patched.encode('utf-8'))
    dom = subprocess.run(
        [CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
         '--virtual-time-budget=25000', '--window-size=%d,1400' % w,
         '--dump-dom', 'file:///' + tmp.replace('\\', '/')],
        capture_output=True, timeout=240
    ).stdout.decode('utf-8', 'replace')
    try:
        os.unlink(tmp)
    except OSError:
        pass
    i = dom.find('data-soul=')
    if i < 0:
        return None
    j = dom.find('"', dom.find('=', i))
    k = dom.find('"', j + 1)
    return json.loads(H.unescape(dom[j + 1:k]))


ok = fail = 0


def t(name, cond, extra=''):
    global ok, fail
    if cond:
        ok += 1
    else:
        fail += 1
        print('  FAIL ' + name + ('  ' + extra if extra else ''))


for w in (1300, 1000, 758):
    d = run(w)
    print('=' * 22, '宽度', w, '=' * 22)
    if not d:
        print('  探针没回传')
        fail += 1
        continue
    if len(d.get('rows', [])) != len(CASES):
        print('  只跑完 %d/%d 条' % (len(d.get('rows', [])), len(CASES)))
    for r in d.get('rows', []):
        print('  %-11s %-9s %-7s ★×%d 未收录=%s 非身份=%s 推定=%s' %
              (r['date'], r['want'], r['grid'], r['stars'],
               r['has_uncol'], r['has_identity'], r['has_tui']))
        print('      文案：'+r['text'])
        if r['want'] == 'near':
            t('near 不给星级 %s' % r['grid'], r['stars'] == 0, '★×%d' % r['stars'])
            t('near 显示未收录 %s' % r['grid'], r['has_uncol'])
            t('near 明说不是身份 %s' % r['grid'], r['has_identity'])
            t('near 不出现推定字样 %s' % r['grid'], not r['has_tui'])
        elif r['want'] == 'same-root':
            t('same-root 标注推定 %s' % r['grid'], r['has_tui'])
            t('same-root 有星级 %s' % r['grid'], r['stars'] >= 1, '★×%d' % r['stars'])
            t('same-root 指向 213 %s' % r['grid'], r['has_213'])
        elif r['want'] == 'exact':
            t('exact 有星级 %s' % r['grid'], r['stars'] >= 1, '★×%d' % r['stars'])
            t('exact 不显示未收录 %s' % r['grid'], not r['has_uncol'])
    if 'rar_err' in d:
        print('  稀有度页异常：', d['rar_err'])
        fail += 1
    else:
        print('  稀有度页尾：'+str(d.get('rar_tail',''))[:200])
        print('  稀有度页：1246 含★=%s  含「不做前缀猜测」=%s  含 12433101=%s'
              % (d.get('rar_has_star'), d.get('rar_has_note'), d.get('rar_has_12433101')))
        t('稀有度页 near 不含★', d.get('rar_has_star') is False)
        t('稀有度页 near 有说明', d.get('rar_has_note') is True)
        t('稀有度页 near 不出现 12433101', d.get('rar_has_12433101') is False)

print('\n灵魂三态探针：OK %d / FAIL %d' % (ok, fail))
sys.exit(1 if fail else 0)
