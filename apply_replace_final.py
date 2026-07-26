"""
最终替换 - 暴力覆盖版
思路: 不管新旧, 全部替换成 individual 目录下对应code的最新文件
"""
import os
import re
import time
import shutil

INDIVIDUAL_DIR = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images\individual"
DEITIES_JS = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js"
BACKUP = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js.bak11_final"

NOW = time.time()
AGE_LIMIT = 3.0 * 3600

print("=" * 70)
print("最终图片替换 - 全覆盖版 vFinal")
print("=" * 70)

# ====== 扫描individual目录中的所有图片 ======
all_files = os.listdir(INDIVIDUAL_DIR)
jpg_files = [f for f in all_files if f.endswith('.jpg')]

# 按code分组
code_to_files = {}
for f in jpg_files:
    name = f[:-4]
    parts = name.split('_')
    if len(parts) >= 3:
        code = '_'.join(parts[1:-1])
    elif len(parts) == 2:
        code = parts[1]
    else:
        continue
    
    if code not in code_to_files:
        code_to_files[code] = []
    ts = int(parts[-1]) if parts[-1].isdigit() else 0
    code_to_files[code].append((f, ts))

# 每个code取最新的
code_to_newest = {}
for code, files in code_to_files.items():
    files.sort(key=lambda x: x[1], reverse=True)
    code_to_newest[code] = files[0][0]

print(f"\nindividual目录: {len(jpg_files)} 个jpg文件")
print(f"涵盖code数: {len(code_to_newest)}")

# ====== 备份 ======
shutil.copy2(DEITIES_JS, BACKUP)
print(f"备份: {BACKUP}")

# ====== 读deities.js逐行处理 ======
with open(DEITIES_JS, 'r', encoding='utf-8') as f:
    lines = f.readlines()

updated = 0

for i, line in enumerate(lines):
    # 匹配 {code:"XXXXX", ..., image:"...", ...}
    code_m = re.search(r'code:\s*"(\d+)"', line)
    if not code_m:
        continue
    
    code = code_m.group(1)
    if code not in code_to_newest:
        continue
    
    new_filename = code_to_newest[code]
    
    # 替换image字段的值
    img_m = re.search(r'(image:\s*")([^"]+)(")', line)
    if not img_m:
        continue
    
    # 构建新行: 替换image的值
    new_line = line[:img_m.start(2)] + new_filename + line[img_m.end(2):]
    
    if new_line != line:
        lines[i] = new_line
        updated += 1

# ====== 写回 ======
with open(DEITIES_JS, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"\n替换结果: {updated} 个条目已更新")

# ====== 验证 ======
with open(DEITIES_JS, 'r', encoding='utf-8') as f:
    content = f.read()

# 统计匹配率
matched = 0
for code, fn in code_to_newest.items():
    # 找code对应的image
    pattern = r'code:\s*"' + re.escape(code) + r'"[^}]*?image:\s*"([^"]+)"'
    m = re.search(pattern, content)
    if m:
        actual = m.group(1)
        if actual == 'generated-images/' + fn:
            matched += 1

print(f"验证: {matched}/{len(code_to_newest)} 个code正确映射")

if updated > 0:
    print(f"\ndeities.js 已更新完毕!")
    print(f"请刷新 game-roster.html 查看效果")

print("=" * 70)
