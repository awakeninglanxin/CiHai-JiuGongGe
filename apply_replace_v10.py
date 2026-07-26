"""
慈海九宫格 - 图片路径替换脚本 v10 (最终版)
格式: {code:"XXX",image:"generated-images/code_XXX_timestamp.jpg"}
"""
import os
import re
import time
import shutil
from pathlib import Path

INDIVIDUAL_DIR = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images\individual"
DEITIES_JS = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js"
BACKUP_DEITIES = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js.bak10"

NOW = time.time()
AGE_LIMIT_HOURS = 2.0
AGE_LIMIT_SECS = AGE_LIMIT_HOURS * 3600

print("=" * 70)
print("慈海九宫格 - 图片路径替换脚本 v10 (最终版)")
print("=" * 70)

# ====== 第1步: 扫描individual目录 ======
all_files = os.listdir(INDIVIDUAL_DIR)
jpg_files = [f for f in all_files if f.endswith('.jpg')]
print(f"\n扫描 individual 目录: {len(jpg_files)} 个jpg文件")

# 提取每个code的最新文件（2小时内），以及旧文件列表
code_to_latest = {}  # code -> filename
old_files = []

for f in jpg_files:
    # code_XXX_TIMESTAMP.jpg
    name = f[:-4]  # without .jpg
    parts = name.split('_')
    # 至少 code_ + CODE + TIMESTAMP
    if len(parts) >= 3:
        code = '_'.join(parts[1:-1])
        ts_str = parts[-1]
        try:
            ts = int(ts_str)
        except ValueError:
            continue
    elif len(parts) == 2:
        code = parts[1]
        ts = 0
    else:
        continue

    filepath = os.path.join(INDIVIDUAL_DIR, f)
    age_secs = NOW - os.path.getmtime(filepath)

    if age_secs <= AGE_LIMIT_SECS:
        # 新文件，保留最新的
        if code not in code_to_latest or ts > code_to_latest[code][1]:
            code_to_latest[code] = (f, ts)
    else:
        old_files.append(f)

print(f"  2小时内新生成的code: {len(code_to_latest)}")
print(f"  需要删除的旧文件: {len(old_files)}")

# ====== 第2步: 删除旧文件 ======
print(f"\n删除旧文件...")
for f in old_files:
    fp = os.path.join(INDIVIDUAL_DIR, f)
    try:
        os.remove(fp)
    except:
        pass
print(f"  已删除 {len(old_files)} 个旧文件")
remaining = len(os.listdir(INDIVIDUAL_DIR))
print(f"  目录剩余: {remaining} 个文件")

# ====== 第3步: 备份 + 读取 deities.js ======
shutil.copy2(DEITIES_JS, BACKUP_DEITIES)
print(f"\n备份 deities.js -> {BACKUP_DEITIES}")

with open(DEITIES_JS, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"deities.js 大小: {len(content)} 字符")

# ====== 第4步: 正则替换 ======
# 格式: {code:"XXX",...,image:"generated-images/OLD_FILENAME",...}
# 替换: {code:"XXX",...,image:"generated-images/NEW_FILENAME",...}

updated = 0
skipped = 0

for code, (new_filename, ts) in code_to_latest.items():
    # 构造正则: 匹配 code:"XXX" 和 image:"..."在同一行/同一个对象内
    # 由于整个条目在一行，我们用灵活匹配
    escaped_code = re.escape(code)
    # {code:"XXX"...image:"generated-images/OLD"...}
    pat_str = r'(\{code:"' + escaped_code + r'"[^}]*?image:\s*")generated-images/[^"]+(")'
    pattern = re.compile(pat_str)
    
    replacement = r'\1' + new_filename + r'\2'
    
    # 尝试替换
    new_content = pattern.sub(replacement, content)
    count = len(pattern.findall(content))
    
    if new_content != content:
        content = new_content
        updated += 1
    else:
        skipped += 1

print(f"\n替换结果:")
print(f"  成功替换: {updated} 个条目")
print(f"  未匹配: {skipped} 个")

# ====== 第5步: 写入 ======
with open(DEITIES_JS, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"\n已写入 deities.js")

# ====== 验证 ======
# 随机抽查几个
print(f"\n抽查验证:")
sample_codes = list(code_to_latest.keys())[:5]
for code in sample_codes:
    new_fn = code_to_latest[code][0]
    # 查找这个code在文件中的image值
    m = re.search(rf'{code}[^}}]*?image:\s*"([^"]+)"', content)
    if m:
        current_img = m.group(1)
        status = "✓" if new_fn in current_img else "✗"
        print(f"  {status} code={code} -> {current_img}")
    else:
        print(f"  ? code={code} 未找到匹配")

print(f"\n{'=' * 70}")
print(f"完成! 更新 {updated} 个条目的图片路径")
print(f"剩余 individual 图片数: {len(os.listdir(INDIVIDUAL_DIR))}")
print(f"{'=' * 70}")
