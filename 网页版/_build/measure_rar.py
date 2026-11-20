# -*- coding: utf-8 -*-
"""量 9.1 卡片里各元素的矩形与 scrollWidth/clientWidth，判断文字是否真的被裁。"""
import json, os, subprocess, sys, tempfile
from PIL import Image

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HTML = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "慈海九宫格_即时解读.html"))
OUT = r"C:\tmp\_probe"
os.makedirs(OUT, exist_ok=True)

W = int(sys.argv[1]) if len(sys.argv) > 1 else 758
H = int(sys.argv[2]) if len(sys.argv) > 2 else 3000

PROBE = r"""
<script>
window.addEventListener('load', function(){
 setTimeout(function(){
  var btns = document.querySelectorAll('nav#tabs button');
  if (btns[9]) btns[9].click();
  setTimeout(function(){
  function r(el){var b=el.getBoundingClientRect();return {x:Math.round(b.left),y:Math.round(b.top),
    w:Math.round(b.width),h:Math.round(b.height),r:Math.round(b.right)};}
  function rec(sel){
    var el=document.querySelector(sel); if(!el) return {sel:sel,missing:true};
    var o=r(el); o.sel=sel; o.sw=el.scrollWidth; o.cw=el.clientWidth;
    o.overflow=el.scrollWidth-el.clientWidth; return o;
  }
  var out=[];
  ['.rarhead','.rartxt','.rartxt p','#rar-body','#tab-9 .card','.rarscore',
   '#st-buckets .bar .n','.freq2'].forEach(function(s){out.push(rec(s));});
  document.body.setAttribute('data-measure', JSON.stringify(out));
  }, 400);
 }, 300);
});
</script>
"""


def main():
    src = open(HTML, encoding="utf-8").read()
    tmp = os.path.join(tempfile.gettempdir(), "_measure.html")
    open(tmp, "w", encoding="utf-8").write(src.replace("</body>", PROBE + "</body>"))
    prof = tempfile.mkdtemp()
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + prof, "--window-size=%d,%d" % (W, H),
           "--virtual-time-budget=12000", "--dump-dom", "file:///" + tmp.replace("\\", "/")]
    dom = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    i = dom.find('data-measure="')
    if i < 0:
        print("没拿到测量数据")
        return
    j = dom.index('"', i + len('data-measure="'))
    raw = dom[i + len('data-measure="'):j].replace("&quot;", '"').replace("&amp;", "&")
    rows = json.loads(raw)
    print("视口宽 %d" % W)
    for x in rows:
        if x.get("missing"):
            print("  [缺] %s" % x["sel"]); continue
        print("  %-16s x=%-4d w=%-4d right=%-4d  scrollW=%-4d clientW=%-4d 溢出=%d"
              % (x["sel"], x["x"], x["w"], x["r"], x["sw"], x["cw"], x["overflow"]))
    json.dump(rows, open(os.path.join(OUT, "measure_%d.json" % W), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
