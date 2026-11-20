# -*- coding: utf-8 -*-
"""实测页面上「前子时」这条路径：
   · 子时卡片的规则名与调整日期是否对
   · 卡片里两套格是不是 0325/28101 与 09336/29112
   · 三份报告里出现的是不是 09336（而不是 v5 的 0314）
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, '..', '慈海九宫格_即时解读.html')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

RULE = sys.argv[1] if len(sys.argv) > 1 else 'book'

PROBE = r"""
<script>
window.addEventListener('load', function(){
  setTimeout(function(){
    var out = {};
    try {
      document.getElementById('fBirth').value  = '1990-05-08';
      document.getElementById('fShichen').value = '前子时';
      document.getElementById('fGender').value  = 'male';
      document.getElementById('fRule').value    = '__RULE__';
      document.getElementById('btnRun').click();
      setTimeout(function(){
        function t(id){ var e=document.getElementById(id); return e? (e.innerText||'').replace(/\s+/g,' ').trim() : '(缺'+id+')'; }
        out.note = t('q-zishi-note');
        out.card = t('q-zishi');
        out.shown = document.getElementById('q-zishi-card').style.display;
        out.rule = document.getElementById('fRule').value;
        /* 报告：直接取三块 .md 容器的 textContent（tab 隐藏时 innerText 取不到） */
        var rep = ['rp-body','tm-body','sl-body'].map(function(id){
          var e = document.getElementById(id);
          return e ? (e.textContent || '') : '';
        });
        out.rep_len = rep.map(function(x){ return x.length; });
        out.rep_09336 = rep.map(function(x){ return x.indexOf('09336') >= 0; });
        out.rep_0314  = rep.map(function(x){ return x.indexOf('0314')  >= 0; });
        out.has09336 = out.rep_09336.every(Boolean);
        out.has0314  = out.rep_0314.some(Boolean);
        out.tail = t('paramTail');
        document.body.setAttribute('data-zishi', JSON.stringify(out));
      }, 500);
    } catch(e) {
      out.err = e.message;
      document.body.setAttribute('data-zishi', JSON.stringify(out));
    }
  }, 300);
});
</script>
"""


def run(w):
    html = open(PAGE, 'rb').read().decode('utf-8')
    probe = PROBE.replace('__RULE__', RULE)
    patched = html.replace('</body>', probe + '</body>')
    fd, tmp = tempfile.mkstemp(suffix='.html', dir=os.environ.get('TEMP', None))
    os.close(fd)
    with open(tmp, 'wb') as f:
        f.write(patched.encode('utf-8'))
    dom = subprocess.run(
        [CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
         '--virtual-time-budget=12000', '--window-size=%d,1400' % w,
         '--dump-dom', 'file:///' + tmp.replace('\\', '/')],
        capture_output=True, timeout=180
    ).stdout.decode('utf-8', 'replace')
    os.unlink(tmp)
    i = dom.find('data-zishi=')
    if i < 0:
        return None
    j = dom.find('"', dom.find('=', i))
    k = dom.find('"', j + 1)
    raw = dom[j + 1:k]
    import html as H
    return json.loads(H.unescape(raw))


for w in (1300, 758):
    d = run(w)
    print('=' * 20, '宽度', w, '规则', RULE, '=' * 20)
    if not d:
        print('  探针没回传')
        continue
    if d.get('err'):
        print('  异常：', d['err'])
        continue
    print('  卡片显示：', d['shown'], '| 下拉值：', d['rule'])
    print('  规则行：', d['note'])
    print('  两套格：', d['card'])
    print('  三份报告字符数   ：', d['rep_len'])
    print('  三份都含 09336   ：', d['has09336'], '（逐份', d['rep_09336'], '）')
    print('  任一份含 0314    ：', d['has0314'], '（逐份', d['rep_0314'], '）')
