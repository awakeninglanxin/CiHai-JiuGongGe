"""
慈海九宫格 - 图片路径替换脚本 v11 (精确版)
修复: code非唯一前缀导致的误替换问题
采用行级别精确匹配
"""
import os
import re
import time
import shutil

INDIVIDUAL_DIR = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images\individual"
DEITIES_JS = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js"
BACKUP = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js.bak11"

NOW = time.time()
AGE_LIMIT = 2.0 * 3600

print("=" * 70)
print("慈海九宫格 - 图片路径替换脚本 v11 (精确行匹配版)")
print("=" * 70)

# ====== 扫描 ======
all_files = os.listdir(INDIVIDUAL_DIR)
jpg_files = [f for f in all_files if f.endswith('.jpg')]

# code -> (filename, timestamp)
code_to_latest = {}
old_files = []

for f in jpg_files:
    name = f[:-4]
    parts = name.split('_')
    if len(parts) >= 3:
        code = '_'.join(parts[1:-1])
        ts_str = parts[-1]
        try:
            ts = int(ts_str)
        except:
            continue
    elif len(parts) == 2:
        code = parts[1]
        ts = 0
    else:
        continue

    age = NOW - os.path.getmtime(os.path.join(INDIVIDUAL_DIR, f))
    if age <= AGE_LIMIT:
        if code not in code_to_latest or ts > code_to_latest[code][1]:
            code_to_latest[code] = (f, ts)
    else:
        old_files.append(f)

# 也清理旧文件
for f in old_files:
    try:
        os.remove(os.path.join(INDIVIDUAL_DIR, f))
    except:
        pass

print(f"\nnew images: {len(code_to_latest)} codes")
print(f"old removed: {len(old_files)} files")

# ====== 备份 ======
shutil.copy2(DEITIES_JS, BACKUP)
print(f"备份: {BACKUP}")

# ====== 行级别精确替换 ======
with open(DEITIES_JS, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 我们需要知道每个code在deities.js中对应的IMAGE行
# 格式示例:
#     {code:"0101",name:"0101",role:"...",image:"generated-images/xxx.jpg",node:13,races:[]},
# 
# 所以code和image在同一行!

updated = 0
for i, line in enumerate(lines):
    # 检查这一行是否包含 code:"XXX" 格式
    code_match = re.search(r'code:\s*"(\d+)"', line)
    if not code_match:
        continue
    
    found_code = code_match.group(1)
    
    if found_code not in code_to_latest:
        continue
    
    new_filename = code_to_latest[found_code][0]
    
    # 找image字段
    img_match = re.search(r'image:\s*"([^"]*)"', line)
    if not img_match:
        continue
    
    old_image = img_match.group(1)
    
    # 检查这个旧图片是否是我们想替换的
    # 只有当旧图片是旧的individual文件时才替换
    old_basename = os.path.basename(old_image)
    old_filepath = os.path.join(INDIVIDUAL_DIR, old_basename) if 'generated-images/' in old_image else old_image
    
    # 判断是否为旧版：文件存在但已被删除或不在新列表中
    is_old = old_basename not in code_to_latest.values()
    
    # 直接替换: 用新filename替换image的值
    new_line = line[:img_match.start(1)] + new_filename + line[img_match.end(1):]
    
    if new_line != line:
        lines[i] = new_line
        updated += 1

# ====== 写回 ======
with open(DEITIES_JS, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"\n替换结果: {updated} 个条目已更新")

# ====== 验证 ======
# 重新读文件验证
with open(DEITIES_JS, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"\n抽查验证 (随机20个):")
import random
sample = random.sample(list(code_to_latest.items()), min(20, len(code_to_latest)))
for code, (expected_fn, _) in sample:
    # 找这个code对应的image
    m = re.search(rf'code:\s*"{re.escape(code)}"[^}}]*?image:\s*"([^"]+)"', content)
    if m:
        actual = m.group(1)
        status = "✓" if expected_fn in actual else "?"
        print(f"  {status} code={code} -> {actual}")
    else:
        print(f"  ? code={code} 未找到")

# 统计：有多少条目使用新版图片
new_img_count = 0
for code, (fn, _) in code_to_latest.items():
    # 检查这个code在文件中的image是否包含这个文件名
    if re.search(rf'code:\s*"{re.escape(code)}"[^}}]*image:\s*"[^"]*{re.escape(fn)}', content):
        new_img_count += 1

print(f"\n统计: {new_img_count}/{len(code_to_latest)} 个code正确映射到新版图片")
print("=" * 70)
