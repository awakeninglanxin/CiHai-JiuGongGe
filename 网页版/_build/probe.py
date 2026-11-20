# -*- coding: utf-8 -*-
"""
真机验收：headless Chrome 载入构建产物，注入探针，检查
  ① 未捕获异常  ② 各标签页是否渲染出内容  ③ 横向溢出（真越界 vs 滚动容器内）
  ④ 关键渲染值  ⑤ 截图
做法：把探针脚本追加进页面副本，--dump-dom 取回 data-probe 属性，无需 CDP。
"""
import json, os, re, subprocess, sys, html as htmlmod

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "慈海九宫格_即时解读.html"))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TMP = r"C:\tmp\_probe"
WIDTHS = [1300, 1000, 758]

PROBE = r"""
<script>
(function(){
  var errs=[];
  window.addEventListener('error', function(e){ errs.push(String(e.message)+' @L'+e.lineno); });
  window.addEventListener('unhandledrejection', function(e){ errs.push('promise:'+e.reason); });
  function inScroller(el){
    var p=el.parentElement;
    while(p){ var s=getComputedStyle(p);
      if(/auto|scroll/.test(s.overflowX)) return true;
      p=p.parentElement; }
    return false;
  }
  var out={errs:errs,tabs:[],overflow:{},values:{}};
  window.addEventListener('load', function(){
    setTimeout(function(){
      try{
        var btns=document.querySelectorAll('#tabs button');
        for(var i=0;i<btns.length;i++){
          btns[i].click();
          var sec=document.getElementById('tab-'+i);
          out.tabs.push({i:i,len:sec?sec.innerHTML.length:0});
        }
        btns[0].click();
      }catch(e){ errs.push('probe-tabs:'+e.message); }
      try{
        var cw=document.documentElement.clientWidth;
        out.overflow.cw=cw;
        out.overflow.bodySW=document.body.scrollWidth;
        out.overflow.docSW=document.documentElement.scrollWidth;
        var bad=[], inS=0, all=document.querySelectorAll('*');
        for(var k=0;k<all.length;k++){
          var r=all[k].getBoundingClientRect();
          if(r.width===0&&r.height===0) continue;
          if(r.right>cw+1.5){
            if(inScroller(all[k])) inS++;
            else bad.push(all[k].tagName+'.'+String(all[k].className||'').slice(0,40));
          }
        }
        out.overflow.bad=bad.length; out.overflow.inScroll=inS;
        out.overflow.sample=bad.slice(0,10);
      }catch(e){ errs.push('probe-ovf:'+e.message); }
      try{
        function t(id){ var e=document.getElementById(id); return e?e.innerText.replace(/\s+/g,' ').trim():''; }
        out.values={
          tail:t('paramTail'),
          duo:t('q-duo').slice(0,200),
          soul:t('q-soul').slice(0,180),
          struct:t('q-struct').slice(0,200),
          rdLen:(document.getElementById('rd-body')||{innerHTML:''}).innerHTML.length,
          fpLen:(document.getElementById('fp-body')||{innerHTML:''}).innerHTML.length,
          rpLen:(document.getElementById('rp-body')||{innerHTML:''}).innerHTML.length,
          tmLn:(document.getElementById('tm-body')||{innerHTML:''}).innerHTML.length,
          slLen:(document.getElementById('sl-body')||{innerHTML:''}).innerHTML.length,
          exLen:(document.getElementById('ex-body')||{innerHTML:''}).innerHTML.length,
          cyLen:(document.getElementById('cy-body')||{innerHTML:''}).innerHTML.length,
          alLen:(document.getElementById('al-body')||{innerHTML:''}).innerHTML.length,
          dbRows:document.querySelectorAll('#db-body .rowitem').length,
          wpRows:document.querySelectorAll('#wp-body tr').length,
          bars:document.querySelectorAll('#st-yang .bar').length,
          svg:document.querySelectorAll('#cy-body svg').length,
          tables:document.querySelectorAll('#views table').length
        };
      }catch(e){ errs.push('probe-val:'+e.message); }
      document.body.setAttribute('data-probe', JSON.stringify(out));
    }, 400);
  });
})();
</script>
"""


def build_probe_html():
    os.makedirs(TMP, exist_ok=True)
    src = open(SRC, "rb").read().decode("utf-8")
    assert "</body>" in src
    probe = src.replace("</body>", PROBE + "\n</body>")
    p = os.path.join(TMP, "probe.html")
    with open(p, "wb") as f:
        f.write(probe.encode("utf-8"))
    return p


def run_chrome(page, w):
    prof = os.path.join(TMP, "prof_%d" % w)
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
           "--no-default-browser-check", "--hide-scrollbars",
           "--user-data-dir=" + prof,
           "--window-size=%d,1000" % w,
           "--virtual-time-budget=9000",
           "--dump-dom", "file:///" + page.replace("\\", "/")]
    r = subprocess.run(cmd, capture_output=True, timeout=180)
    dom = r.stdout.decode("utf-8", "replace")
    m = re.search(r'data-probe="(.*?)"\s*>', dom, re.S)
    if not m:
        m = re.search(r'data-probe="(.*?)"', dom, re.S)
    if not m:
        return None, dom
    raw = htmlmod.unescape(m.group(1))
    return json.loads(raw), dom


def shot(page, w, out_png, height=2600):
    prof = os.path.join(TMP, "shot_%d" % w)
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
           "--no-default-browser-check", "--hide-scrollbars",
           "--user-data-dir=" + prof,
           "--window-size=%d,%d" % (w, height),
           "--virtual-time-budget=9000",
           "--screenshot=" + out_png,
           "file:///" + page.replace("\\", "/")]
    subprocess.run(cmd, capture_output=True, timeout=180)


def main():
    page = build_probe_html()
    print("探针页：%s（%d 字节）" % (page, os.path.getsize(page)))
    allok = True
    for w in WIDTHS:
        data, dom = run_chrome(page, w)
        print("\n================ 宽度 %d ================" % w)
        if data is None:
            print("  FAIL 未取到探针数据，DOM 长度 %d" % len(dom))
            allok = False
            continue
        errs = data.get("errs", [])
        print("  未捕获异常：%d %s" % (len(errs), errs[:5] if errs else ""))
        if errs:
            allok = False
        tabs = data.get("tabs", [])
        empty = [t for t in tabs if t["len"] < 40]
        print("  标签页：%d 个，内容为空的：%s" % (len(tabs), [(t["i"], t["len"]) for t in empty] or "无"))
        if empty:
            allok = False
        o = data.get("overflow", {})
        same = (o.get("bodySW") == o.get("cw") and o.get("docSW") == o.get("cw"))
        print("  溢出：cw=%s bodySW=%s docSW=%s  一致=%s  ★真越界=%s  滚动容器内=%s"
              % (o.get("cw"), o.get("bodySW"), o.get("docSW"), same, o.get("bad"), o.get("inScroll")))
        if o.get("bad"):
            print("     越界样例：", o.get("sample"))
        if not same or o.get("bad"):
            allok = False
        v = data.get("values", {})
        print("  渲染长度：rd=%s fp=%s rp=%s tm=%s sl=%s ex=%s cy=%s al=%s"
              % (v.get("rdLen"), v.get("fpLen"), v.get("rpLen"), v.get("tmLn"),
                 v.get("slLen"), v.get("exLen"), v.get("cyLen"), v.get("alLen")))
        print("  控件：db行=%s 法器行=%s 统计条=%s SVG=%s 表格=%s"
              % (v.get("dbRows"), v.get("wpRows"), v.get("bars"), v.get("svg"), v.get("tables")))
        print("  参数栏：%s" % v.get("tail"))
        print("  阳/阴格：%s" % v.get("duo"))
        print("  灵魂：%s" % v.get("soul"))
        if v.get("dbRows", 0) < 80 or v.get("bars", 0) != 15 or v.get("svg", 0) < 1:
            print("  FAIL 控件数量异常")
            allok = False

    png = os.path.join(TMP, "shot_1300.png")
    shot(page, 1300, png)
    if os.path.exists(png):
        print("\n截图：%s（%d 字节）" % (png, os.path.getsize(png)))

    print("\n============ 结论：%s ============" % ("全部通过" if allok else "存在问题"))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
