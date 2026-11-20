# -*- coding: utf-8 -*-
"""
按标签页逐块裁剪：点开指定标签 → 量出各关键块的真实矩形 → 高窗整页截图 → 按矩形裁剪 → 2x 放大。
用法：python crop_tabs.py <标签序号> [宽度]
输出：C:/tmp/_probe/crop/t<序号>_<宽度>_<块名>.png
说明：headless --screenshot 只截视口，所以窗口高度给足够大；超出视口的块会被截断并标注。
"""
import json, os, re, subprocess, sys, html as htmlmod
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "慈海九宫格_即时解读.html"))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TMP = r"C:\tmp\_probe"
OUTD = os.path.join(TMP, "crop")
SHOT_H = 3600

PROBE = r"""
<script>
(function(){
  var q = location.search.replace(/^\?/, '');
  var TAB = parseInt((q.match(/tab=(\d+)/)||[0,-1])[1], 10);
  window.addEventListener('load', function(){
    setTimeout(function(){
      try{
        var btns = document.querySelectorAll('#tabs button');
        if (TAB >= 0 && TAB < btns.length) btns[TAB].click();
        window.scrollTo(0, 0);
      }catch(e){}
      setTimeout(function(){
        var out = {tab: TAB, rects: [], vw: document.documentElement.clientWidth};
        var sec = document.getElementById('tab-' + TAB);
        if (sec) {
          out.secTop = Math.round(sec.getBoundingClientRect().top);
          out.secH = Math.round(sec.getBoundingClientRect().height);
          /* 取「最外层」的块：标题 / 卡片 / 提示 / 珠串 / SVG / 表格，跳过已被选中的后代的祖先 */
          var sel = sec.querySelectorAll('h2,h3,h4,.card,.note,.beads,.tl,table');
          var picked = [];
          for (var j = 0; j < sel.length; j++) {
            var skip = false;
            for (var k = 0; k < picked.length; k++) {
              if (picked[k].contains(sel[j])) { skip = true; break; }
            }
            if (!skip) picked.push(sel[j]);
          }
          for (var i = 0; i < picked.length; i++) {
            var r = picked[i].getBoundingClientRect();
            if (r.height < 4) continue;
            out.rects.push({
              i: i, tag: picked[i].tagName, cls: String(picked[i].className || ''),
              x: Math.round(r.left), y: Math.round(r.top),
              w: Math.round(r.width), h: Math.round(r.height),
              txt: (picked[i].innerText || '').replace(/\s+/g, ' ').slice(0, 60)
            });
          }
        }
        document.body.setAttribute('data-rects', JSON.stringify(out));
      }, 500);
    }, 450);
  });
})();
</script>
"""


def build_page():
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(OUTD, exist_ok=True)
    src = open(SRC, "rb").read().decode("utf-8")
    p = os.path.join(TMP, "crop.html")
    with open(p, "wb") as f:
        f.write(src.replace("</body>", PROBE + "\n</body>").encode("utf-8"))
    return p


def dump_rects(page, tab, w):
    prof = os.path.join(TMP, "cr_prof_%d_%d" % (tab, w))
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
           "--no-default-browser-check", "--hide-scrollbars",
           "--user-data-dir=" + prof, "--window-size=%d,%d" % (w, SHOT_H),
           "--virtual-time-budget=9000", "--dump-dom",
           "file:///" + page.replace("\\", "/") + "?tab=%d" % tab]
    r = subprocess.run(cmd, capture_output=True, timeout=180)
    dom = r.stdout.decode("utf-8", "replace")
    m = re.search(r'data-rects="(.*?)"\s*>', dom, re.S) or re.search(r'data-rects="(.*?)"', dom, re.S)
    if not m:
        return None
    return json.loads(htmlmod.unescape(m.group(1)))


def shot(page, tab, w, png):
    prof = os.path.join(TMP, "cr_shot_%d_%d" % (tab, w))
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
           "--no-default-browser-check", "--hide-scrollbars",
           "--user-data-dir=" + prof, "--window-size=%d,%d" % (w, SHOT_H),
           "--virtual-time-budget=9000", "--screenshot=" + png,
           "file:///" + page.replace("\\", "/") + "?tab=%d" % tab]
    subprocess.run(cmd, capture_output=True, timeout=180)


def main():
    tab = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    w = int(sys.argv[2]) if len(sys.argv) > 2 else 1300
    global SHOT_H
    if len(sys.argv) > 3:
        SHOT_H = int(sys.argv[3])
    page = build_page()
    info = dump_rects(page, tab, w)
    if info is None:
        print("FAIL 取不到矩形（tab=%d w=%d）" % (tab, w))
        return 1
    print("tab=%d  宽度=%d  视口=%d  节高=%s" % (tab, w, info["vw"], info.get("secH")))
    png = os.path.join(TMP, "shot_t%d_%d.png" % (tab, w))
    shot(page, tab, w, png)
    im = Image.open(png)
    print("截图 %dx%d" % im.size)
    made = []
    SEG = 620   # 单张裁剪最大高度；超高的块按 620px 切片，2x 后仍是 1240px，便于逐字读
    for r in info["rects"]:
        y0 = max(0, r["y"])
        limit = min(SHOT_H, im.size[1])
        if y0 >= limit - 8:
            print("  [跳过] i=%d %s .%s  在视口外 y=%d" % (r["i"], r["tag"], r["cls"], r["y"]))
            continue
        bot = min(y0 + r["h"], limit)
        trun = "" if y0 + r["h"] <= limit else "（截断，原高 %d）" % r["h"]
        segs = []
        yy = y0
        while yy < bot:
            segs.append((yy, min(yy + SEG, bot)))
            yy += SEG
        for si, (ya, yb) in enumerate(segs):
            box = (max(0, r["x"]), ya, min(im.size[0], r["x"] + r["w"]), yb)
            if box[2] - box[0] < 8 or box[3] - box[1] < 8:
                continue
            name = "t%d_%d_%02d_%d.png" % (tab, w, r["i"], si)
            p = os.path.join(OUTD, name)
            c = im.crop(box)
            c = c.resize((c.width * 2, c.height * 2), Image.LANCZOS)
            c.save(p)
            made.append(p)
        print("  i=%-2d %-6s .%-16s y=%-5d w=%-5d h=%-5d 切%d张 %s%s"
              % (r["i"], r["tag"], r["cls"][:16], r["y"], r["w"], r["h"], len(segs),
                 r["txt"][:44], trun))
    print("\n裁剪 %d 张 → %s" % (len(made), OUTD))
    return 0


if __name__ == "__main__":
    sys.exit(main())
