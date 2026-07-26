import re, os, hashlib
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "generated-images")
JS = os.path.join(ROOT, "deities.js")

content = open(JS, "r", encoding="utf-8").read()
pairs = re.findall(r'code:"(\d+)"[^}]*?image:"generated-images/([^"]+)"', content)
print(f"总引用对: {len(pairs)}")

def md5(fp):
    h = hashlib.md5()
    try:
        with open(fp, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

# md5 -> list of (code, imgfile)
md5map = defaultdict(list)
missing = []
for code, img in pairs:
    fp = os.path.join(IMG_DIR, img)
    if not os.path.exists(fp) or os.path.getsize(fp) <= 5000:
        missing.append((code, img))
        continue
    m = md5(fp)
    md5map[m].append((code, img))

print(f"缺失/过小文件: {len(missing)}")
print(f"有效图片 MD5 组总数: {len(md5map)}")

# 视觉重复组：同 MD5 且涉及 >1 个不同 code
dup_groups = []
for m, items in md5map.items():
    codes = set(c for c, _ in items)
    if len(codes) > 1:
        dup_groups.append((m, items))

dup_groups.sort(key=lambda x: -len(x[1]))
total_involved = set()
for m, items in dup_groups:
    for c, _ in items:
        total_involved.add(c)

print(f"\n=== 视觉重复组(不同code同图): {len(dup_groups)} 组, 涉及 {len(total_involved)} 个不同 code ===")
for m, items in dup_groups[:30]:
    codes = [c for c, _ in items]
    print(f"  MD5={m[:8]}  codes=[{','.join(codes)}]  ({len(items)}个文件)")
