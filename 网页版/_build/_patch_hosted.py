# -*- coding: utf-8 -*-
"""把本地构建版的内嵌脚本同步到资料库下载的基线文件，完整保留 pnid 标记。
静态 HTML/CSS 未改动，只替换 7 个 <script> 块的内容；平台注入的 inject.js 原样保留。"""
import re, sys

BASE = sys.argv[1] + r'\慈海九宫格_即时解读.html' if len(sys.argv) > 1 else r'E:\Temp\workbuddy-page-edit-k_z6ei6m\慈海九宫格_即时解读.html'
LOCAL = r'D:\AAA我的文件\慈海九宫格_整合版\网页版\慈海九宫格_即时解读.html'

base = open(BASE, encoding='utf-8').read()
local = open(LOCAL, encoding='utf-8').read()
pat = re.compile(r'(<script\b[^>]*>)([\s\S]*?)(</script>)')
bms = list(pat.finditer(base))
lms = list(pat.finditer(local))
bs = [m for m in bms if 'src=' not in m.group(1).lower()]
assert len(bs) == len(lms), (len(bs), len(lms))

out, last, k = [], 0, 0
for m in bms:
    out.append(base[last:m.start()])
    if 'src=' in m.group(1).lower():
        out.append(m.group(0))
    else:
        out.append(m.group(1) + lms[k].group(2) + m.group(3))
        k += 1
    last = m.end()
out.append(base[last:])
blob = ''.join(out)
open(BASE, 'w', encoding='utf-8').write(blob)
print('已替换 %d 个脚本块；pnid 属性数 %d → %d；体积 %d'
      % (k, base.count('data-page-node-id'), blob.count('data-page-node-id'), len(blob.encode('utf-8'))))
