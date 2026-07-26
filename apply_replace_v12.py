"""
最终完整替换脚本 v12 - 把所有individual图片(新旧混合)替换进deities.js
"""
import os
import re
import time
import shutil

INDIVIDUAL_DIR = r"D:\AAA我的文件\慈海九宫格_整合版\generated-images\individual"
DEITIES_JS = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js"
BACKUP = r"D:\AAA我的文件\慈海九宫格_整合版\deities.js.bak12"

print("=" * 70)
print("终极图片替换 v12 - 全覆盖")
print("=" * 70)

# ====== 扫描individual目录(所有时间戳的图片都算) ======
all_files = os.listdir(INDIVIDUAL_DIR)
jpg_files = [f for f in all_files if f.endswith('.jpg')]
print(f"\nindividual目录: {len(jpg_files)} 个jpg文件")

# 按code分组, 取最新的
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
    
    ts_str = parts[-1]
    try:
        ts = int(ts_str)
    except ValueError:
        ts = 0
    
    if code not in code_to_files:
        code_to_files[code] = []
    code_to_files[code].append((f, ts))

code_to_newest = {}
for code, files in code_to_files.items():
    files.sort(key=lambda x: x[1], reverse=True)
    code_to_newest[code] = files[0][0]

print(f"涵盖code数: {len(code_to_newest)}")

# ====== 备份 ======
shutil.copy2(DEITIES_JS, BACKUP)
print(f"备份: {BACKUP}")

# ====== 读deities.js ======
with open(DEITIES_JS, 'r', encoding='utf-8') as f:
    content = f.read()

# ====== 按code逐个替换 ======
updated = 0
for code, new_filename in sorted(code_to_newest.items()):
    # 精确匹配: code:"XXX" 后面跟随的image字段
    # 格式: {code:"123",name:"123",role:"...",image:"old.jpg",...}
    pattern = r'(\{code:"' + re.escape(code) + r'")[^}]*?image:\s*")([^"]+)(")'
    m = re.search(pattern, content)
    if m:
        old_img = m.group(2)
        # 替换
        new_img = m.group(1) + new_filename + m.group(3)
        content = content.replace(old_img + '">', new_img + '>') if old_img + '">' in content else content
        # 上面不对, 用正则直接替换
        new_content = re.sub(pattern, r'\1' + new_filename + r'\3', content)
        if new_content != content:
            updated += 1

# 重新用简单方法:
content2 = open(DEITIES_JS, 'r', encoding='utf-8').read()
updated2 = 0
for code, new_filename in sorted(code_to_newest.items()):
    # 精确: 找到这一行的code:"XXX"和对应的image:"xxx"
    pattern = r'(\{code:"' + re.escape(code) + r'"[^}]*image:\s*")([^"]+)(")'
    m = re.search(pattern, content2)
    if m:
        old_val = m.group(2)
        if new_filename not in old_val:
            content2 = re.sub(pattern, r'\g<1>' + new_filename + r'\3', content2)
            updated2 += 1

print(f"\n替换结果: {updated2} 个条目已更新")

# ====== 写回 ======
with open(DEITIES_JS, 'w', encoding='utf-8') as f:
    f.write(content2)

# ====== 验证 ======
verified = 0
for code, fn in code_to_newest.items():
    pattern = r'code:"' + re.escape(code) + r'"[^}]*image:\s*"([^"]+)"'
    m = re.search(pattern, content2)
    if m:
        if fn in m.group(1):
            verified += 1
        else:
            # 显示不匹配的前几个
            if verified < 5:
                print(f"  MISMATCH code={code}: expected={fn}, got={m.group(1)}")

print(f"验证: {verified}/{len(code_to_newest)} 个code正确映射")

print("=" * 70)
