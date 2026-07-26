import re, os, hashlib
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "generated-images")

content = open(os.path.join(ROOT, "deities.js"), "r", encoding="utf-8").read()

# 抓所有 image:"generated-images/xxx" + 它前面的 code
pairs = re.findall(r'code:"(\d+)"[^}]*?image:"generated-images/([^"]+)"', content)

print(f"总引用对: {len(pairs)}")

restored_pairs = [(c, i) for c, i in pairs if "restored" in i]
normal_pairs = [(c, i) for c, i in pairs if "restored" not in i]
print(f"  普通版引用: {len(normal_pairs)}")
print(f"  restored版引用: {len(restored_pairs)}")

# 每个 restored code 的普通版是否存在
restored_codes = set(c for c, i in restored_pairs)
normal_codes = set(c for c, i in normal_pairs)

print(f"\nrestored 涉及的不同 code 数: {len(restored_codes)}")
print(f"其中有普通版存在的 code 数: {len(restored_codes & normal_codes)}")
print(f"只有 restored 没有普通版的 code 数: {len(restored_codes - normal_codes)}")

# 文件系统层面：restored 文件是否真实存在
restored_exist = 0
restored_missing = 0
for c, i in restored_pairs:
    fp = os.path.join(IMG_DIR, i)
    if os.path.exists(fp) and os.path.getsize(fp) > 5000:
        restored_exist += 1
    else:
        restored_missing += 1
print(f"\nrestored 文件在磁盘上 存在且有效={restored_exist}, 缺失/过小={restored_missing}")

# 普通版文件存在性（去重code）
norm_exist = 0
norm_missing = 0
for c in restored_codes:
    fp = os.path.join(IMG_DIR, f"code_{c}.jpg")
    if os.path.exists(fp) and os.path.getsize(fp) > 5000:
        norm_exist += 1
    else:
        norm_missing += 1
print(f"restored code 的普通版 code_XXX.jpg 存在={norm_exist}, 缺失={norm_missing}")

# MD5 重复检测（仅在 restored 文件中）
def md5(fp):
    h = hashlib.md5()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

md5map = defaultdict(list)
for c, i in restored_pairs:
    fp = os.path.join(IMG_DIR, i)
    if os.path.exists(fp) and os.path.getsize(fp) > 5000:
        md5map[md5(fp)].append((c, i))

dups = {k: v for k, v in md5map.items() if len(v) > 1}
total_dup_files = sum(len(v) for v in dups.values())
print(f"\nrestored 内部 MD5 重复组数: {len(dups)} (涉及文件 {total_dup_files} 张)")
for k, v in list(dups.items())[:5]:
    print(f"  组: {[c for c,_ in v]}")
