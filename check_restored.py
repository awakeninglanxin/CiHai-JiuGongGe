import re
from collections import Counter

content = open('deities.js', 'r', encoding='utf-8').read()
images = re.findall(r'image:"generated-images/([^"]+)"', content)
print(f"deities.js 总 image 引用: {len(images)}")

# 分类
normal = [i for i in images if '_v1restored' not in i and 'restored' not in i]
restored = [i for i in images if '_v1restored' in i or 'restored' in i]
print(f"  普通 code_*.jpg: {len(normal)}")
print(f"  restored 版: {len(restored)}")

# 检查 restored 引用里有多少是 MD5 重复的
import os, hashlib
restored_groups = {}
for img in restored:
    fp = os.path.join('generated-images', img)
    if os.path.isfile(fp):
        with open(fp, 'rb') as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        restored_groups.setdefault(md5, []).append(img)

dup_restored = {k: v for k, v in restored_groups.items() if len(v) > 1}
print(f"\nrestored 文件中 MD5 重复的组数: {len(dup_restored)}")
total_dup_files = sum(len(v) for v in dup_restored.values())
print(f"涉及重复文件数: {total_dup_files}")

if dup_restored:
    print("\n重复组明细 (前10):")
    for md5, files in list(dup_restored.items())[:10]:
        codes = [f.replace('code_','').replace('_v1restored.jpg','').replace('.jpg','') for f in files]
        print(f"  {len(files)}张同图: {codes}")
