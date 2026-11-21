# -*- coding: utf-8 -*-
"""
构建单文件网页：慈海九宫格_即时解读.html
输入：src/*.js|css|html + lunar_table.json + data.json
输出：../慈海九宫格_即时解读.html（零外链、可直接双击打开、可拖进资料库）

用法：
  python build.py            # 构建
  python build.py --dry      # 只体检不写盘
"""
import json, os, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
OUT = os.path.abspath(os.path.join(HERE, "..", "慈海九宫格_即时解读.html"))
TITLE = "慈海九宫格 · 即时解读"


def read(p):
    with open(p, "rb") as f:
        return f.read().decode("utf-8")


def enc_json(obj):
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    # 防 </script> 提前闭合
    return s.replace("</", "<\\/")


def main():
    dry = "--dry" in sys.argv

    css = read(os.path.join(SRC, "style.css"))
    body = read(os.path.join(SRC, "body.html"))
    engine = read(os.path.join(SRC, "engine.js"))
    md = read(os.path.join(SRC, "md.js"))
    reports = read(os.path.join(SRC, "reports.js"))
    ui = read(os.path.join(SRC, "ui.js"))
    lunar_lib = read(os.path.join(SRC, "lunar.js"))   # lunar-javascript 排盘核心（Solar/Lunar/EightChar）
    bazi = read(os.path.join(SRC, "bazi.js"))         # 四柱八字阴阳五行倾向算法

    lunar = json.load(open(os.path.join(HERE, "lunar_table.json"), encoding="utf-8"))
    data = json.load(open(os.path.join(HERE, "data.json"), encoding="utf-8"))

    parts = []
    parts.append('<!DOCTYPE html>')
    parts.append('<html lang="zh-CN">')
    parts.append('<head>')
    parts.append('<meta charset="UTF-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    parts.append('<meta name="generator" content="慈海九宫格 build.py">')
    parts.append('<title>%s</title>' % TITLE)
    parts.append('<style>')
    parts.append(css)
    parts.append('</style>')
    parts.append('</head>')
    parts.append('<body>')
    parts.append(body)
    parts.append('<script>')
    parts.append('window.__LUNAR__=' + enc_json(lunar) + ';')
    parts.append('window.__DATA__=' + enc_json(data) + ';')
    parts.append('</script>')
    parts.append('<script>')
    parts.append(engine)
    parts.append('</script>')
    parts.append('<script>')
    parts.append(md)
    parts.append('</script>')
    parts.append('<script>')
    parts.append(reports)
    parts.append('</script>')
    parts.append('<script>')
    parts.append(lunar_lib)
    parts.append('</script>')
    parts.append('<script>')
    parts.append(bazi)
    parts.append('</script>')
    parts.append('<script>')
    parts.append(ui)
    parts.append('</script>')
    parts.append('</body>')
    parts.append('</html>')

    html = "\n".join(parts) + "\n"
    blob = html.encode("utf-8")

    print("来源体积：css %d · body %d · engine %d · md %d · reports %d · lunar %d · bazi %d · ui %d"
          % (len(css), len(body), len(engine), len(md), len(reports), len(lunar_lib), len(bazi), len(ui)))
    print("内嵌数据：lunar %d 项 / %d 字节 · data %d 字节"
          % (lunar["n"], len(enc_json(lunar)), len(enc_json(data))))
    print("输出：%s" % OUT)
    print("体积 %d 字节 · LF %d · CR %d · md5 %s"
          % (len(blob), blob.count(b"\n"), blob.count(b"\r"), hashlib.md5(blob).hexdigest()[:10]))

    # 体检
    checks = []
    checks.append(("无外部 http 链接", blob.count(b"http://") + blob.count(b"https://") == 0))
    checks.append(("无 <script src", b"<script src" not in blob))
    checks.append(("<style> 配对", blob.count(b"<style>") == blob.count(b"</style>")))
    checks.append(("<script> 配对", blob.count(b"<script>") == blob.count(b"</script>")))
    for name, okk in checks:
        print("  %s %s" % ("OK  " if okk else "FAIL", name))
    if not all(x[1] for x in checks):
        print("体检未通过，已中止")
        return 1

    if dry:
        print("[dry] 未写盘")
        return 0

    with open(OUT, "wb") as f:
        f.write(blob)
    print("已写盘")
    return 0


if __name__ == "__main__":
    sys.exit(main())
