import os, hashlib, re
from collections import defaultdict

IMG_DIR = "generated-images"
h2f = defaultdict(list)
for fn in os.listdir(IMG_DIR):
    if not fn.startswith("code_") or not fn.lower().endswith(".jpg"):
        continue
    fp = os.path.join(IMG_DIR, fn)
    if os.path.isfile(fp):
        with open(fp, "rb") as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        m = re.match(r"code_(.+)\.jpg", fn)
        if m:
            h2f[md5].append(m.group(1))

dup = {k: v for k, v in h2f.items() if len(v) > 1}
print(f"code_*.jpg 文件总数: {sum(len(v) for v in h2f.values())}")
print(f"MD5 重复的组数: {len(dup)}")
if dup:
    for md5, codes in list(dup.items())[:10]:
        print(f"  重复组({len(codes)}张): {codes[:10]}")
else:
    print("✅ 所有 code 图片 MD5 唯一，无视觉重复！")
