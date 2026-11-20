# -*- coding: utf-8 -*-
"""给定生日，打开第 9 页，把稀有度卡片与检索结果的文字抓出来。"""
import json, os, subprocess, sys, tempfile

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HTML = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "慈海九宫格_即时解读.html"))

birth = sys.argv[1] if len(sys.argv) > 1 else "2012-12-21"
query = sys.argv[2] if len(sys.argv) > 2 else "121121 1167"
W = int(sys.argv[3]) if len(sys.argv) > 3 else 1300

PROBE = r"""
<script>
window.addEventListener('load', function(){ setTimeout(function(){
  var b=document.getElementById('fBirth');
  b.value='__BIRTH__';
  document.getElementById('btnRun').click();
  setTimeout(function(){
    var btns=document.querySelectorAll('nav#tabs button');
    if(btns[9]) btns[9].click();
    var q=document.getElementById('stSearch');
    q.value='__QUERY__';
    q.dispatchEvent(new Event('input',{bubbles:true}));
    setTimeout(function(){
      var t=function(id){var e=document.getElementById(id);return e?(e.innerText||'').replace(/\s+/g,' ').trim():'(缺)';};
      document.body.setAttribute('data-rar', JSON.stringify({rar:t('rar-body'), det:t('st-detail'), meta:t('stMeta')}));
    },350);
  },600);
},300);});
</script>
"""


def main():
    src = open(HTML, encoding="utf-8").read()
    probe = PROBE.replace("__BIRTH__", birth).replace("__QUERY__", query)
    tmp = os.path.join(tempfile.gettempdir(), "_rar.html")
    open(tmp, "w", encoding="utf-8").write(src.replace("</body>", probe + "</body>"))
    prof = tempfile.mkdtemp()
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + prof, "--window-size=%d,2400" % W,
           "--virtual-time-budget=20000", "--dump-dom",
           "file:///" + tmp.replace("\\", "/")]
    dom = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    i = dom.find('data-rar="')
    if i < 0:
        print("没拿到数据")
        return
    j = dom.index('"', i + len('data-rar="'))
    raw = dom[i + len('data-rar="'):j].replace("&quot;", '"').replace("&amp;", "&")
    d = json.loads(raw)
    print("生日 %s / 宽 %d" % (birth, W))
    print("  稀有度卡：", d["rar"][:600])
    print("  检索结果：", d["det"][:400])
    print("  统计抬头：", d["meta"][:220])


if __name__ == "__main__":
    main()
