"""
终极替换 v13 - 最简单可靠的方式: 逐行处理
deities.js 格式:
  {code:"XXX",name:"XXX",role:"...",image:"generated-images/xxx.jpg",node:13,races:[]},
"""
import os
import re
import shutil

INDIVIDUAL_DIR = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images\individual"
DEITIES_JS = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js"
BACKUP = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js.bak13"

print("=" * 70)
print("终极替换 v13 - 逐行精确匹配")
print("=" * 70)

# ====== 1. 扫描individual ======
all_files = os.listdir(INDIVIDUAL_DIR)
jpg_files = [f for f in all_files if f.endswith('.jpg')]

# code -> 文件名 (按时间戳排序, 取最新)
code_map = {}  # code -> (filename, timestamp)
for f in jpg_files:
    name = f[:-4]
    parts = name.split('_')
    if len(parts) >= 3:
        code = '_'.join(parts[1:-1])
    elif len(parts) == 2:
        code = parts[1]
    else:
        continue

    try:
        ts = int(parts[-1])
    except:
        ts = 0

    if code not in code_map or ts > code_map[code][1]:
        code_map[code] = (f, ts)

print(f"individual: {len(jpg_files)} files, {len(code_map)} codes")

# ====== 2. 备份 ======
shutil.copy2(DEITIES_JS, BACKUP)
print(f"备份: {BACKUP}")

# ====== 3. 逐行读取 ======
with open(DEITIES_JS, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# ====== 4. 替换 ======
# 格式: {code:"12345",name:"12345",role:"...",image:"generated-images/code_12345_TIMESTAMP.jpg",...}
# 匹配code和image

updated = 0
skipped_no_new_img = 0

for i, line in enumerate(lines):
    # 查找 code:"XXXXX"
    code_match = re.search(r'code:\s*"(\d+)"', line)
    if not code_match:
        continue

    found_code = code_match.group(1)

    # 找image:"..."
    img_match = re.search(r'image:\s*"([^"]*)"', line)
    if not img_match:
        continue

    old_image = img_match.group(1)

    # 这个code是否有新版图片
    if found_code not in code_map:
        continue

    new_filename = code_map[found_code][0]

    # 替换
    # image:"old" -> image:"new"
    line = line[:img_match.start(1)] + new_filename + line[img_match.end(1):]

    updated += 1

# ====== 5. 写回 ======
with open(DEITIES_JS, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"\n✅ 替换完成: {updated} 个条目")

# ====== 6. 验证 ======
with open(DEITIES_JS, 'r', encoding='utf-8') as f:
    content = f.read()

# 对每个code检查
correct = 0
wrong = 0
missing = 0
for code, (fn, _) in sorted(code_map.items()):
    # 找code的行
    pattern = r'code:\s*"' + re.escape(code) + r'"[^}]*image:\s*"([^"]*)"'
    m = re.search(pattern, content)
    if m:
        actual = m.group(1)
        if fn == actual:
            correct += 1
        else:
            wrong += 1
            if wrong <= 3:
                print(f"  ❌ MISMATCH code={code}")
                print(f"     expected: {fn}")
                print(f"     got:      {actual}")
    else:
        missing += 1

print(f"\n验证结果:")
print(f"  ✅ 正确: {correct}/{len(code_map)}")
print(f"  ❌ 错误: {wrong}")
print(f"  ❓ 缺失: {missing}")
print("=" * 70)
