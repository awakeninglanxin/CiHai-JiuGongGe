# -*- coding: utf-8 -*-
"""交互分支实测：改表单 → 点运行 → 抓关键文本 + 异常 + 溢出。用法：python probe_case.py <json文件|内联json>"""
import json, os, re, subprocess, sys, html as htmlmod

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "慈海九宫格_即时解读.html"))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TMP = r"C:\tmp\_probe"

PROBE = r"""
<script>
(function(){
  var CASE = __CASE__;
  var errs=[];
  window.addEventListener('error', function(e){ errs.push(String(e.message)+' @L'+e.lineno); });
  window.addEventListener('unhandledrejection', function(e){ errs.push('promise:'+e.reason); });
  function set(id,v){ var e=document.getElementById(id); if(!e) return '缺控件'+id;
    e.value=v; e.dispatchEvent(new Event('change',{bubbles:true}));
    e.dispatchEvent(new Event('input',{bubbles:true})); return null; }
  function t(id){ var e=document.getElementById(id); return e?e.innerText.replace(/\s+/g,' ').trim():''; }
  window.addEventListener('load', function(){
    setTimeout(function(){
      var out={errs:errs, missing:[]};
      ['fBirth','fShichen','fGender','fClock','fCity','fRule'].forEach(function(id){
        if(!document.getElementById(id)) out.missing.push(id);
      });
      Object.keys(CASE).forEach(function(id){ var m=set(id, CASE[id]); if(m) out.missing.push(m); });
      try { document.getElementById('btnRun').click(); } catch(e){ errs.push('click:'+e.message); }
      setTimeout(function(){
        out.tail=t('paramTail');
        out.hint=t('paramHint');
        out.duo=t('q-duo').slice(0,300);
        out.struct=t('q-struct').slice(0,300);
        out.ts=(document.getElementById('q-ts')||{innerText:''}).innerText.replace(/\s+/g,' ').slice(0,300);
        out.soul=t('q-soul').slice(0,160);
        out.life=(document.getElementById('cy-pick')||{innerText:''}).innerText.replace(/\s+/g,' ').slice(0,220);
        out.alLen=(document.getElementById('al-body')||{innerHTML:''}).innerHTML.length;
        out.tabs=[].map.call(document.querySelectorAll('#tabs button'), function(b){return b.textContent;});
        var cw=document.documentElement.clientWidth;
        var bad=0, all=document.querySelectorAll('*');
        for(var i=0;i<all.length;i++){ var r=all[i].getBoundingClientRect();
          if(r.width===0&&r.height===0) continue;
          if(r.right>cw+1.5){
            var p=all[i].parentElement, inS=false;
            while(p){ if(/auto|scroll/.test(getComputedStyle(p).overflowX)){inS=true;break;} p=p.parentElement; }
            if(!inS) bad++;
          } }
        out.bad=bad; out.cw=cw;
        document.body.setAttribute('data-case', JSON.stringify(out));
      }, 500);
    }, 400);
  });
})();
</script>
"""


def main():
    spec = sys.argv[1] if len(sys.argv) > 1 else '{}'
    if os.path.exists(spec):
        spec = open(spec, encoding='utf-8').read()
    os.makedirs(TMP, exist_ok=True)
    src = open(SRC, "rb").read().decode("utf-8")
    page = os.path.join(TMP, "case.html")
    with open(page, "wb") as f:
        f.write(src.replace("</body>", PROBE.replace("__CASE__", spec) + "\n</body>").encode("utf-8"))
    for w in (1300, 758):
        prof = os.path.join(TMP, "cs_%d" % w)
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
               "--no-default-browser-check", "--hide-scrollbars",
               "--user-data-dir=" + prof, "--window-size=%d,1400" % w,
               "--virtual-time-budget=9000", "--dump-dom",
               "file:///" + page.replace("\\", "/")]
        r = subprocess.run(cmd, capture_output=True, timeout=180)
        dom = r.stdout.decode("utf-8", "replace")
        m = re.search(r'data-case="(.*?)"\s*>', dom, re.S) or re.search(r'data-case="(.*?)"', dom, re.S)
        print("=" * 20, "宽度", w, "=" * 20)
        if not m:
            print("  FAIL 取不到数据，DOM 长度", len(dom))
            continue
        d = json.loads(htmlmod.unescape(m.group(1)))
        print("  异常：", d["errs"] or "无")
        print("  缺控件：", d["missing"] or "无")
        print("  溢出：cw=%s 真越界=%s" % (d["cw"], d["bad"]))
        for k in ("tail", "hint", "struct", "ts", "soul", "life"):
            print("  %-7s %s" % (k + "：", d.get(k, "")))


if __name__ == "__main__":
    main()
